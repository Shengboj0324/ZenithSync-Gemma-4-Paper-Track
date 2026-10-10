"""Validate token normalization against reduced Gemma, without model downloads."""

import copy
import os
import unittest


@unittest.skipUnless(os.environ.get('ZENITHSYNC_TEST_TORCH') == '1',
                     'Requires explicitly selected Torch/Transformers environment')
class GemmaCorpusTests(unittest.TestCase):
    def test_microbatch_loss_gradients_and_update_match_padded_batch(self):
        import torch
        from transformers import Gemma4TextConfig, Gemma4ForCausalLM
        from zenithsync.corpus_optimization import token_weighted_step
        from zenithsync.training_batch import collate_training_examples

        torch.set_num_threads(1)
        torch.manual_seed(91)
        config = Gemma4TextConfig(
            vocab_size=16, hidden_size=16, intermediate_size=32,
            num_hidden_layers=2, num_attention_heads=2, num_key_value_heads=1,
            num_global_key_value_heads=1, head_dim=8, global_head_dim=8,
            hidden_size_per_layer_input=0, attention_k_eq_v=True,
            layer_types=['sliding_attention', 'full_attention'],
            max_position_embeddings=16, sliding_window=8,
            use_cache=False, attention_dropout=0.0)
        config._attn_implementation = 'eager'
        full = Gemma4ForCausalLM(config).double().train()
        split = copy.deepcopy(full)
        examples = [
            {'input_ids': [2, 3, 4, 5, 6], 'labels': [-100, 3, 4, 5, 6]},
            {'input_ids': [2, 7, 8], 'labels': [-100, -100, 8]},
        ]

        def batch(rows):
            values = collate_training_examples(
                rows, pad_token_id=0, vocab_size=16, max_length=16)['batch']
            return {key: torch.tensor(value, dtype=torch.long)
                    for key, value in values.items()}

        # Independently compute the objective from logits. Gemma's loss uses
        # float32 logits internally even when the reduced model is float64.
        combined = batch(examples)
        with torch.no_grad():
            output = full(**combined)
            expected = torch.nn.functional.cross_entropy(
                output.logits[:, :-1].float().reshape(-1, 16),
                combined['labels'][:, 1:].reshape(-1), ignore_index=-100)
            torch.testing.assert_close(output.loss, expected, rtol=1e-6, atol=1e-7)

        optimizers = [torch.optim.AdamW(model.parameters(), lr=0.001, foreach=False)
                      for model in (full, split)]
        first = token_weighted_step(full, optimizers[0], [combined])
        second = token_weighted_step(split, optimizers[1], [batch([row]) for row in examples])
        self.assertEqual(second['microbatch_supervised_tokens'], [4, 1])
        self.assertAlmostEqual(first['token_mean_loss'], second['token_mean_loss'], places=6)
        for left, right in zip(full.parameters(), split.parameters(), strict=True):
            torch.testing.assert_close(left.grad, right.grad, rtol=2e-5, atol=2e-7)
            torch.testing.assert_close(left, right, rtol=2e-5, atol=2e-7)
        for left, right in zip(optimizers[0].state.values(), optimizers[1].state.values(), strict=True):
            for key in left:
                torch.testing.assert_close(left[key], right[key], rtol=2e-5, atol=2e-7)


if __name__ == '__main__':
    unittest.main()
