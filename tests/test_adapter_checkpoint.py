import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest


@unittest.skipUnless(importlib.util.find_spec('torch'), 'Torch runtime required')
class AdapterCheckpointTests(unittest.TestCase):
    def setUp(self):
        import torch
        from tests.test_corpus_optimization import CorpusOptimizationTests
        from zenithsync.training_rng import capture_rng_state, restore_rng_state
        from zenithsync.training_schedule import make_schedule, iter_updates
        from zenithsync.adapter_checkpoint import frozen_state, capture_adapter_checkpoint
        self.addCleanup(restore_rng_state, capture_rng_state())
        self.helper = CorpusOptimizationTests()
        self.examples = self.helper.examples()
        self.schedule = make_schedule(
            [{'example_id': str(i), 'input_tokens': len(row['input_ids']),
              'supervised_tokens': sum(v != -100 for v in row['labels'][1:])}
             for i, row in enumerate(self.examples)], corpus_content_sha256='a'*64,
            seed=17, target_supervised_tokens=8, max_epochs=2, max_update_supervised_tokens=3)
        self.updates = list(iter_updates(self.schedule))
        self.bindings = {'base_manifest_sha256':'b'*64, 'corpus_manifest_sha256':'c'*64,
                         'corpus_content_sha256':'a'*64,
                         'schedule_sha256':self.schedule['schedule_sha256'],
                         'worker_config_sha256':'d'*64}
        self.model, self.optimizer = self.model_and_optimizer()
        self.frozen = frozen_state(self.model)
        self.step(self.model, self.optimizer, self.updates[0])
        self.payload = capture_adapter_checkpoint(self.model, self.optimizer,
            bindings=self.bindings, schedule=self.schedule,
            cursor=self.updates[0]['next_cursor'], expected_frozen=self.frozen)

    def model_and_optimizer(self):
        import torch
        model = self.helper.setup_model()
        for parameter in model.embedding.parameters():
            parameter.requires_grad_(False)
        model.embedding = torch.nn.Sequential(model.embedding, torch.nn.Dropout(0.3))
        optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],
                                      lr=0.01, foreach=False)
        return model, optimizer

    def step(self, model, optimizer, update):
        from zenithsync.corpus_optimization import token_weighted_step
        return token_weighted_step(model, optimizer, self.helper.batches(
            [[self.examples[int(row['example_id'])]] for row in update['examples']]))

    def test_disk_roundtrip_resumes_adapter_optimizer_rng_and_cursor(self):
        import torch
        from zenithsync.adapter_checkpoint import restore_adapter_checkpoint
        from zenithsync.checkpoint_storage import save_checkpoint, load_checkpoint
        from zenithsync.training_schedule import iter_updates
        expected_losses = [self.step(self.model, self.optimizer, row) for row in self.updates[1:]]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory).resolve()/'adapter.pt'
            identity = save_checkpoint(path, self.payload, max_bytes=1000000)
            loaded = load_checkpoint(path, expected_identity=identity, max_bytes=1000000)
        model, optimizer = self.model_and_optimizer()
        cursor = restore_adapter_checkpoint(model, optimizer, loaded, bindings=self.bindings,
                                            schedule=self.schedule, expected_frozen=self.frozen)
        actual_losses = [self.step(model, optimizer, row)
                         for row in iter_updates(self.schedule, resume=cursor)]
        self.assertEqual(actual_losses, expected_losses)
        for name, value in self.model.state_dict().items():
            self.assertTrue(torch.equal(value, model.state_dict()[name]))
        for left, right in zip(self.optimizer.state.values(), optimizer.state.values(), strict=True):
            for key in left:
                self.assertTrue(torch.equal(left[key], right[key]))
        self.assertNotIn('embedding.0.weight', loaded['adapter'])

    def test_invalid_bindings_state_and_cursor_rejected_before_mutation(self):
        import torch
        from zenithsync.adapter_checkpoint import restore_adapter_checkpoint
        mutations = [
            lambda p: p['bindings'].update(worker_config_sha256='e'*64),
            lambda p: p['module_modes'].update({'embedding.1': False}),
            lambda p: p['cursor'].update(consumed_supervised_tokens=999),
            lambda p: p['optimizer'].update(completed_steps=2),
            lambda p: p['optimizer']['optimizer_state']['param_groups'][0].update(lr=0.7),
            lambda p: p['rng'].update(torch_cpu=torch.zeros(3, dtype=torch.uint8)),
            lambda p: next(iter(p['adapter'].values())).fill_(float('nan')),
        ]
        for mutate in mutations:
            payload = copy.deepcopy(self.payload);mutate(payload)
            model, optimizer = self.model_and_optimizer()
            before = copy.deepcopy(model.state_dict())
            with self.assertRaises((ValueError, RuntimeError)):
                restore_adapter_checkpoint(model, optimizer, payload, bindings=self.bindings,
                                           schedule=self.schedule, expected_frozen=self.frozen)
            for name, value in before.items():
                self.assertTrue(torch.equal(value, model.state_dict()[name]))
            self.assertFalse(optimizer.state)

    def test_changed_frozen_base_rejected_and_capture_is_independent(self):
        import torch
        from zenithsync.adapter_checkpoint import restore_adapter_checkpoint
        model, optimizer = self.model_and_optimizer()
        with torch.no_grad():
            model.embedding[0].weight[0, 0].add_(1)
        with self.assertRaisesRegex(ValueError, 'State changed'):
            restore_adapter_checkpoint(model, optimizer, self.payload, bindings=self.bindings,
                                       schedule=self.schedule, expected_frozen=self.frozen)
        snapshot = copy.deepcopy(self.payload['adapter'])
        self.step(self.model, self.optimizer, self.updates[1])
        for name, value in snapshot.items():
            self.assertTrue(torch.equal(value, self.payload['adapter'][name]))


if __name__ == '__main__':
    unittest.main()
