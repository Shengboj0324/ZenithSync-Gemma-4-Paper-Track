import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


def resume_fixture(source, identity, destination):
    """Fresh-process consumer for a synthetic dropout checkpoint."""
    import torch
    from zenithsync.checkpoint_storage import load_checkpoint, save_checkpoint
    from zenithsync.training_rng import restore_rng_state
    from zenithsync.optimizer_checkpoint import restore_adamw_checkpoint
    from tests.test_corpus_optimization import CorpusOptimizationTests
    from zenithsync.corpus_optimization import token_weighted_step
    fixture = CorpusOptimizationTests()
    model = fixture.setup_model()
    model.embedding = torch.nn.Sequential(model.embedding, torch.nn.Dropout(0.4))
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.01, foreach=False)
    saved = load_checkpoint(Path(source), expected_identity=identity, max_bytes=1000000)
    model.load_state_dict(saved['model'])
    restore_adamw_checkpoint(optimizer, list(model.named_parameters()), saved['optimizer'])
    restore_rng_state(saved['rng'])
    result = token_weighted_step(model, optimizer, fixture.batches([fixture.examples()]))
    return save_checkpoint(Path(destination), {'model': model.state_dict(),
        'optimizer': optimizer.state_dict(), 'result': result}, max_bytes=1000000)


@unittest.skipUnless(importlib.util.find_spec('torch'), 'Torch runtime required')
class CheckpointStorageTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name).resolve()

    def test_budget_and_serialization_failure_never_publish(self):
        import torch
        from zenithsync.checkpoint_storage import save_checkpoint
        target = self.root/'checkpoint.pt'
        with self.assertRaises((ValueError, RuntimeError)):
            save_checkpoint(target, {'large': torch.zeros(10000)}, max_bytes=100)
        self.assertFalse(target.exists())
        self.assertEqual(list(self.root.iterdir()), [])
        with patch('torch.save', side_effect=RuntimeError('interrupted serialization')):
            with self.assertRaisesRegex(RuntimeError, 'interrupted'):
                save_checkpoint(target, {}, max_bytes=10000)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_no_overwrite_tamper_and_incomplete_file_rejection(self):
        import torch
        from zenithsync.checkpoint_storage import save_checkpoint, load_checkpoint
        target = self.root/'checkpoint.pt'
        identity = save_checkpoint(target, {'value': torch.arange(10)}, max_bytes=10000)
        original = target.read_bytes()
        with self.assertRaises(FileExistsError):
            save_checkpoint(target, {}, max_bytes=10000)
        self.assertEqual(target.read_bytes(), original)
        tampered = bytearray(original);tampered[-1] ^= 1;target.write_bytes(tampered)
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            load_checkpoint(target, expected_identity=identity, max_bytes=10000)
        target.write_bytes(original[:100])
        with self.assertRaisesRegex(ValueError, 'size mismatch'):
            load_checkpoint(target, expected_identity=identity, max_bytes=10000)

    def test_fresh_process_dropout_resume(self):
        import torch
        from zenithsync.checkpoint_storage import save_checkpoint, load_checkpoint
        from zenithsync.training_rng import capture_rng_state, restore_rng_state
        from zenithsync.optimizer_checkpoint import capture_adamw_checkpoint
        from tests.test_corpus_optimization import CorpusOptimizationTests
        from zenithsync.corpus_optimization import token_weighted_step
        initial_rng = capture_rng_state();self.addCleanup(restore_rng_state, initial_rng)
        fixture = CorpusOptimizationTests()
        model = fixture.setup_model()
        model.embedding = torch.nn.Sequential(model.embedding, torch.nn.Dropout(0.4))
        optimizer = torch.optim.AdamW(model.parameters(), lr=0.01, foreach=False)
        token_weighted_step(model, optimizer, fixture.batches([fixture.examples()]))
        source = self.root/'saved.pt'
        identity = save_checkpoint(source, {
            'model': model.state_dict(),
            'optimizer': capture_adamw_checkpoint(optimizer, list(model.named_parameters()), completed_steps=1),
            'rng': capture_rng_state()}, max_bytes=1000000)
        expected_result = token_weighted_step(model, optimizer, fixture.batches([fixture.examples()]))
        expected_model = copy.deepcopy(model.state_dict())
        destination = self.root/'resumed.pt'
        code = ('import json,sys;from tests.test_checkpoint_storage import resume_fixture;'
                'print(json.dumps(resume_fixture(sys.argv[1],json.loads(sys.argv[2]),sys.argv[3])))')
        result = subprocess.run([sys.executable, '-B', '-c', code, str(source),
                                 json.dumps(identity), str(destination)],
                                cwd=Path(__file__).resolve().parents[1],
                                env={**os.environ, 'PYTHONDONTWRITEBYTECODE':'1'},
                                capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)
        resumed = load_checkpoint(destination, expected_identity=json.loads(result.stdout), max_bytes=1000000)
        self.assertEqual(resumed['result'], expected_result)
        for name, value in expected_model.items():
            self.assertTrue(torch.equal(value, resumed['model'][name]))
        for key, state in optimizer.state_dict()['state'].items():
            for name, value in state.items():
                self.assertTrue(torch.equal(value, resumed['optimizer']['state'][key][name]))

    def test_nonregular_files_and_symlinks_are_rejected(self):
        from zenithsync.checkpoint_storage import load_checkpoint
        identity = {'sha256': 'a'*64, 'size_bytes': 1}
        fifo = self.root/'pipe'
        os.mkfifo(fifo)
        with self.assertRaisesRegex(ValueError, 'type or size'):
            load_checkpoint(fifo, expected_identity=identity, max_bytes=100)
        link = self.root/'link'
        link.symlink_to(fifo)
        with self.assertRaises(OSError):
            load_checkpoint(link, expected_identity=identity, max_bytes=100)


if __name__ == '__main__':
    unittest.main()
