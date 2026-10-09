"""Failure-path tests using actual reduced Gemma and PEFT operations."""

import os
from pathlib import Path
import tempfile
import unittest

from zenithsync.training_pilot import qualify_adapter


@unittest.skipUnless(os.environ.get('ZENITHSYNC_TEST_TORCH') == '1',
                     'Requires explicitly selected Torch environment')
class PilotFailureTests(unittest.TestCase):
    def setUp(self):
        import torch
        from transformers import Gemma4TextConfig, Gemma4ForCausalLM
        torch.set_num_threads(1)
        config = Gemma4TextConfig(vocab_size=16, hidden_size=16, intermediate_size=32,
            num_hidden_layers=2, num_attention_heads=2, num_key_value_heads=1,
            num_global_key_value_heads=1, head_dim=8, global_head_dim=8,
            hidden_size_per_layer_input=0, attention_k_eq_v=True,
            layer_types=['sliding_attention', 'full_attention'], max_position_embeddings=16,
            sliding_window=8, use_cache=False, attention_dropout=0.0)
        config._attn_implementation = 'eager'
        def load():
            torch.manual_seed(91)
            return Gemma4ForCausalLM(config)
        self.load = load
        self.torch = torch
        self.batch = {'input_ids': torch.tensor([[2, 3, 4]]),
                      'labels': torch.tensor([[-100, 3, 4]])}
        self.shapes = {'model.layers.0.self_attn.q_proj': [16, 16]}
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.output = Path(self.directory.name) / 'run'

    def run_pilot(self, **overrides):
        options = dict(load_base=self.load, batch=self.batch, target_shapes=self.shapes,
                       output=self.output, learning_rate=0.005)
        options.update(overrides)
        return qualify_adapter(**options)

    def test_wrong_target_rejected_without_receipt(self):
        with self.assertRaisesRegex(ValueError, 'Target is absent'):
            self.run_pilot(target_shapes={'model.layers.0.self_attn.q_proj': [17, 16]})
        self.assertFalse((self.output / 'receipt.json').exists())

    def test_no_supervised_targets_rejected_without_receipt(self):
        self.batch['labels'].fill_(-100)
        with self.assertRaisesRegex(ValueError, 'finite scalar'):
            self.run_pilot()
        self.assertFalse((self.output / 'receipt.json').exists())

    def test_changed_reload_base_rejected_without_receipt(self):
        calls = 0
        def changed_loader():
            nonlocal calls
            model = self.load()
            calls += 1
            if calls == 2:
                with self.torch.no_grad():
                    model.model.embed_tokens.weight[1, 0].add_(1)
            return model
        with self.assertRaisesRegex(ValueError, 'State changed'):
            self.run_pilot(load_base=changed_loader)
        self.assertEqual(calls, 2)
        self.assertFalse((self.output / 'receipt.json').exists())

    def test_existing_output_never_overwritten(self):
        self.output.mkdir()
        sentinel = self.output / 'keep.txt'
        sentinel.write_text('preserve')
        with self.assertRaises(FileExistsError):
            self.run_pilot()
        self.assertEqual(sentinel.read_text(), 'preserve')


if __name__ == '__main__':
    unittest.main()
