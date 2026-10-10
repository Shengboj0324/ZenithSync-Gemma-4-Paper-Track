import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


@unittest.skipUnless(importlib.util.find_spec('torch'), 'Torch runtime required')
class TrainingSessionTests(unittest.TestCase):
    def setUp(self):
        from tests.test_corpus_training import CorpusTrainingTests
        from zenithsync.training_rng import capture_rng_state, restore_rng_state
        from zenithsync.training_schedule import make_schedule
        self.addCleanup(restore_rng_state, capture_rng_state())
        self.fixture = CorpusTrainingTests()
        self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
        self.corpus = self.fixture.corpus
        summary = self.corpus.summary
        self.schedule = make_schedule(
            [{key: row[key] for key in ('example_id','input_tokens','supervised_tokens')}
             for row in self.corpus.metadata()], corpus_content_sha256=summary['content_sha256'],
            seed=19, target_supervised_tokens=3, max_epochs=3, max_update_supervised_tokens=1)
        self.bindings = {'base_manifest_sha256':'b'*64,
                         'corpus_manifest_sha256':summary['manifest']['sha256'],
                         'corpus_content_sha256':summary['content_sha256'],
                         'schedule_sha256':self.schedule['schedule_sha256'],
                         'worker_config_sha256':'c'*64}
        directory = tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup)
        self.root = Path(directory.name).resolve()

    def model(self):
        import torch
        from tests.test_corpus_optimization import CorpusOptimizationTests
        model = CorpusOptimizationTests().setup_model()
        for p in model.embedding.parameters():p.requires_grad_(False)
        model.embedding = torch.nn.Sequential(model.embedding, torch.nn.Dropout(0.3))
        return model, torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],
                                        lr=0.01, foreach=False)

    def run_session(self, name, model, optimizer, **overrides):
        from zenithsync.training_session import run_training_session
        from zenithsync.adapter_checkpoint import frozen_state
        options = dict(corpus=self.corpus, schedule=self.schedule, bindings=self.bindings,
                       expected_frozen=frozen_state(model), output=self.root/name,
                       max_updates=10, max_seconds=60, max_sequence_tokens=8,
                       max_checkpoint_bytes=100000, max_session_checkpoint_bytes=1000000)
        options.update(overrides)
        return run_training_session(model, optimizer, **options)

    def test_complete_and_interrupted_resumed_sessions_match(self):
        import torch
        full, full_opt = self.model()
        complete = self.run_session('full', full, full_opt)
        self.assertEqual(complete['status'], 'schedule_complete')
        from zenithsync.session_report import validate_session_report
        from zenithsync.training_schedule import initial_cursor
        from zenithsync.checkpoint_storage import load_checkpoint
        verified = validate_session_report(complete,schedule=self.schedule,
            start_cursor=initial_cursor(self.schedule),bindings=self.bindings,
            checkpoint_root=self.root/'full',max_updates=10,max_seconds=60,
            max_checkpoint_bytes=100000,max_session_checkpoint_bytes=1000000,
            load_payload=lambda path,identity:load_checkpoint(path,expected_identity=identity,max_bytes=100000))
        self.assertEqual(verified['verified_updates'],3)
        split, split_opt = self.model()
        first = self.run_session('first', split, split_opt, max_updates=1)
        self.assertEqual(first['status'], 'update_budget')
        restored, restored_opt = self.model()
        last = first['checkpoints'][-1]
        resumed = self.run_session('resumed', restored, restored_opt,
                                   resume={'path':last['path'],'identity':last['identity']})
        self.assertEqual(resumed['status'], 'schedule_complete')
        self.assertEqual(resumed['cursor'], complete['cursor'])
        self.assertEqual([row['metrics'] for row in resumed['checkpoints']],
                         [row['metrics'] for row in complete['checkpoints'][1:]])
        for name, value in full.state_dict().items():
            self.assertTrue(torch.equal(value, restored.state_dict()[name]))

    def test_checkpoint_failure_preserves_prior_file(self):
        from zenithsync.checkpoint_storage import save_checkpoint, load_checkpoint
        from zenithsync.artifacts import file_record
        model, optimizer = self.model()
        calls = 0
        def fail_second(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:raise OSError('injected disk failure')
            return save_checkpoint(*args, **kwargs)
        with patch('zenithsync.training_session.save_checkpoint', side_effect=fail_second):
            with self.assertRaisesRegex(OSError, 'injected'):
                self.run_session('failed', model, optimizer)
        files = list((self.root/'failed').iterdir())
        self.assertEqual(len(files), 1)
        payload = load_checkpoint(files[0], expected_identity=file_record(files[0]), max_bytes=100000)
        self.assertEqual(payload['cursor']['completed_updates'], 1)

    def test_bad_bindings_and_capacity_rejected_before_training(self):
        import torch
        model, optimizer = self.model()
        before = copy.deepcopy(model.state_dict())
        invalid = {**self.bindings, 'corpus_manifest_sha256':'f'*64}
        for name, options in [('identity', {'bindings':invalid}),
                              ('capacity', {'max_sequence_tokens':2})]:
            with self.assertRaises(ValueError):self.run_session(name, model, optimizer, **options)
            self.assertFalse((self.root/name).exists())
        self.assertFalse(optimizer.state)
        for name, value in before.items():self.assertTrue(torch.equal(value, model.state_dict()[name]))

    def test_disk_reservation_stops_before_second_update(self):
        model, optimizer = self.model()
        result = self.run_session('limited', model, optimizer, max_session_checkpoint_bytes=100000)
        self.assertEqual(result['status'], 'checkpoint_budget')
        self.assertEqual(result['cursor']['completed_updates'], 1)

    def test_elapsed_budget_prevents_first_update(self):
        model, optimizer = self.model()
        with patch('zenithsync.training_session.time.monotonic', side_effect=[0, 61, 61]):
            result = self.run_session('expired', model, optimizer)
        self.assertEqual(result['status'], 'wall_budget')
        self.assertEqual(result['cursor']['completed_updates'], 0)
        self.assertFalse(result['checkpoints'])
        self.assertFalse(optimizer.state)


if __name__ == '__main__':unittest.main()
