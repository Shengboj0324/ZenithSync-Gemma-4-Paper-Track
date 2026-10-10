"""CPU stochastic resume checks; no GPU equivalence is inferred."""
import copy
import importlib.util
import io
import random
import unittest


@unittest.skipUnless(importlib.util.find_spec('torch') and importlib.util.find_spec('numpy'),
                     'Torch and NumPy runtime required')
class TrainingRngTests(unittest.TestCase):
    def setUp(self):
        from zenithsync.training_rng import capture_rng_state, restore_rng_state
        saved = capture_rng_state()
        self.addCleanup(restore_rng_state, saved)

    def test_roundtrip_weights_only_serialization(self):
        import numpy as np
        import torch
        from zenithsync.training_rng import capture_rng_state, restore_rng_state
        random.seed(12); np.random.seed(13); torch.manual_seed(14)
        saved = capture_rng_state()
        expected = (random.random(), np.random.random(4), torch.rand(4))
        buffer = io.BytesIO(); torch.save(saved, buffer); buffer.seek(0)
        restored = torch.load(buffer, weights_only=True)
        restore_rng_state(restored)
        self.assertEqual(random.random(), expected[0])
        np.testing.assert_array_equal(np.random.random(4), expected[1])
        self.assertTrue(torch.equal(torch.rand(4), expected[2]))

    def test_invalid_rng_does_not_partially_restore_globals(self):
        import numpy as np
        import torch
        from zenithsync.training_rng import capture_rng_state, restore_rng_state
        saved = capture_rng_state()
        invalid = copy.deepcopy(saved)
        invalid['torch_cpu'] = torch.zeros(3, dtype=torch.uint8)
        with self.assertRaises((ValueError, RuntimeError)):
            restore_rng_state(invalid)
        actual = (random.random(), np.random.random(4), torch.rand(4))
        restore_rng_state(saved)
        self.assertEqual(random.random(), actual[0])
        np.testing.assert_array_equal(np.random.random(4), actual[1])
        self.assertTrue(torch.equal(torch.rand(4), actual[2]))
        invalid = copy.deepcopy(saved)
        invalid['runtime']['torch_version'] = 'changed'
        with self.assertRaisesRegex(ValueError, 'runtime'):
            restore_rng_state(invalid)

    def test_dropout_optimizer_and_cursor_resume_exactly(self):
        import numpy as np
        import torch
        from tests.test_corpus_optimization import CorpusOptimizationTests
        from zenithsync.training_rng import capture_rng_state, restore_rng_state
        from zenithsync.optimizer_checkpoint import capture_adamw_checkpoint, restore_adamw_checkpoint
        from zenithsync.training_schedule import make_schedule, iter_updates
        from zenithsync.corpus_optimization import token_weighted_step
        helper = CorpusOptimizationTests()

        def model():
            result = helper.setup_model()
            result.embedding = torch.nn.Sequential(result.embedding, torch.nn.Dropout(0.4))
            return result

        random.seed(71); np.random.seed(72)
        uninterrupted = model()
        optimizer = torch.optim.AdamW(uninterrupted.parameters(), lr=0.01, foreach=False)
        examples = helper.examples()
        schedule = make_schedule(
            [{'example_id':str(i), 'input_tokens':len(row['input_ids']),
              'supervised_tokens':sum(x != -100 for x in row['labels'][1:])}
             for i, row in enumerate(examples)], corpus_content_sha256='a'*64,
            seed=17, target_supervised_tokens=12, max_epochs=3, max_update_supervised_tokens=3)

        def step(target, opt, update):
            # Consume all three global generators as a realistic stochastic
            # preprocessing + dropout path, identically in both branches.
            random.random(); np.random.random()
            return token_weighted_step(target, opt, helper.batches(
                [[examples[int(row['example_id'])]] for row in update['examples']]))

        losses = []
        for update in iter_updates(schedule):
            losses.append(step(uninterrupted, optimizer, update)['token_mean_loss'])
            if update['step'] == 2:
                checkpoint = copy.deepcopy({
                    'model': uninterrupted.state_dict(),
                    'optimizer': capture_adamw_checkpoint(optimizer,
                        list(uninterrupted.named_parameters()), completed_steps=2),
                    'cursor': update['next_cursor'], 'rng': capture_rng_state()})
        resumed = model()
        resumed.load_state_dict(checkpoint['model'])
        resumed_optimizer = torch.optim.AdamW(resumed.parameters(), lr=0.01, foreach=False)
        restore_adamw_checkpoint(resumed_optimizer, list(resumed.named_parameters()), checkpoint['optimizer'])
        restore_rng_state(checkpoint['rng'])
        resumed_losses = [step(resumed, resumed_optimizer, update)['token_mean_loss']
                          for update in iter_updates(schedule, resume=checkpoint['cursor'])]
        self.assertEqual(resumed_losses, losses[2:])
        for a, b in zip(uninterrupted.parameters(), resumed.parameters(), strict=True):
            self.assertTrue(torch.equal(a, b))
        for a, b in zip(optimizer.state.values(), resumed_optimizer.state.values(), strict=True):
            for key in a:
                self.assertTrue(torch.equal(a[key], b[key]))


if __name__ == '__main__':
    unittest.main()
