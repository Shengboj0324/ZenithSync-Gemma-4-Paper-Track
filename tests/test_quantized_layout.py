import unittest

from zenithsync.quantized_layout import expected_projections, validate_projection


def fixture():
    return {'model_type': 'gemma4', 'text_config': {
        'enable_moe_block': False, 'num_kv_shared_layers': 0,
        'hidden_size_per_layer_input': 0, 'attention_bias': False,
        'hidden_size': 32, 'intermediate_size': 64, 'num_hidden_layers': 2,
        'num_attention_heads': 4, 'num_key_value_heads': 2,
        'num_global_key_value_heads': 1, 'head_dim': 8, 'global_head_dim': 16,
        'attention_k_eq_v': True, 'layer_types': ['sliding_attention', 'full_attention']},
        'quantization_config': {'quant_method': 'compressed-tensors',
            'format': 'pack-quantized', 'quantization_status': 'compressed',
            'config_groups': {'group_0': {'targets': ['Linear'],
                'input_activations': None, 'output_activations': None,
                'weights': {'num_bits': 4, 'group_size': 32, 'symmetric': True,
                            'strategy': 'group', 'type': 'int', 'dynamic': False}}}}}


class QuantizedLayoutTests(unittest.TestCase):
    def test_distinct_sliding_and_global_attention_dimensions(self):
        result = expected_projections(fixture())
        self.assertEqual(len(result), 13)
        root = 'model.language_model.layers.'
        self.assertEqual(result[root + '0.self_attn.v_proj'], (16, 32))
        self.assertNotIn(root + '1.self_attn.v_proj', result)
        self.assertEqual(result[root + '1.self_attn.q_proj'], (64, 32))
        self.assertEqual(result[root + '1.self_attn.k_proj'], (16, 32))
        self.assertEqual(result[root + '1.self_attn.o_proj'], (32, 64))
        self.assertEqual(result[root + '0.mlp.down_proj'], (32, 64))

    def test_separate_value_projection_when_configured(self):
        config = fixture()
        config['text_config']['attention_k_eq_v'] = False
        result = expected_projections(config)
        self.assertEqual(result['model.language_model.layers.1.self_attn.v_proj'], (32, 32))
        self.assertEqual(len(result), 14)

    def test_unsupported_features_and_invalid_dimensions_fail(self):
        for key, value in [('enable_moe_block', True), ('num_kv_shared_layers', 1),
                           ('hidden_size', True), ('head_dim', 0),
                           ('num_key_value_heads', 3), ('layer_types', ['full_attention'])]:
            with self.subTest(key=key):
                config = fixture()
                config['text_config'][key] = value
                with self.assertRaises(ValueError):
                    expected_projections(config)

    def test_packing_rounds_up_and_rejects_corruption(self):
        packed = {'dtype': 'I32', 'shape': [2, 5]}
        scale = {'dtype': 'BF16', 'shape': [2, 2]}
        validate_projection('fixture', [2, 33], packed, scale, (2, 33))
        for original, actual_packed, actual_scale in [
                ([33, 2], packed, scale),
                ([2, 33], {'dtype': 'I32', 'shape': [2, 4]}, scale),
                ([2, 33], packed, {'dtype': 'BF16', 'shape': [2, 1]}),
                ([2, 33], {'dtype': 'BF16', 'shape': [2, 5]}, scale)]:
            with self.subTest(original=original, packed=actual_packed, scale=actual_scale):
                with self.assertRaises(ValueError):
                    validate_projection('fixture', original, actual_packed, actual_scale, (2, 33))


if __name__ == '__main__':
    unittest.main()
