"""Dimension contracts for dense Gemma4 W4/group-32 text projections.

Scope deliberately excludes MoE, per-layer inputs, biases and shared KV layers.
These checks do not execute compressed-tensors unpacking or model inference.
"""


def expected_projections(config: dict) -> dict[str, tuple[int, int]]:
    if config.get('model_type') != 'gemma4':
        raise ValueError('expected Gemma4 configuration')
    text = config['text_config']
    for key, expected in [('enable_moe_block', False), ('num_kv_shared_layers', 0),
                          ('hidden_size_per_layer_input', 0), ('attention_bias', False)]:
        if type(text.get(key)) is not type(expected) or text[key] != expected:
            raise ValueError(f'unsupported text configuration: {key}')
    dims = ['hidden_size', 'intermediate_size', 'num_hidden_layers',
            'num_attention_heads', 'num_key_value_heads', 'num_global_key_value_heads',
            'head_dim', 'global_head_dim']
    for key in dims:
        if type(text.get(key)) is not int or text[key] <= 0:
            raise ValueError(f'invalid positive dimension: {key}')
    if type(text.get('attention_k_eq_v')) is not bool:
        raise ValueError('attention_k_eq_v must be boolean')
    layers = text['layer_types']
    if not isinstance(layers, list) or len(layers) != text['num_hidden_layers']:
        raise ValueError('layer_types length must equal num_hidden_layers')
    if any(kind not in ('sliding_attention', 'full_attention') for kind in layers):
        raise ValueError('unsupported attention layer type')
    quant = config['quantization_config']
    if (quant.get('quant_method'), quant.get('format'), quant.get('quantization_status')) != (
            'compressed-tensors', 'pack-quantized', 'compressed'):
        raise ValueError('unsupported quantization representation')
    if set(quant['config_groups']) != {'group_0'}:
        raise ValueError('expected one quantization group')
    group = quant['config_groups']['group_0']
    if group.get('targets') != ['Linear'] or group.get('input_activations') is not None or group.get('output_activations') is not None:
        raise ValueError('unsupported quantization targets or activation quantization')
    weights = group['weights']
    for key, expected in [('num_bits', 4), ('group_size', 32), ('symmetric', True),
                          ('strategy', 'group'), ('type', 'int'), ('dynamic', False)]:
        if type(weights.get(key)) is not type(expected) or weights[key] != expected:
            raise ValueError(f'unsupported quantization parameter: {key}')
    hidden, intermediate = text['hidden_size'], text['intermediate_size']
    result = {}
    for index, kind in enumerate(layers):
        prefix = f'model.language_model.layers.{index}'
        result[f'{prefix}.mlp.gate_proj'] = (intermediate, hidden)
        result[f'{prefix}.mlp.up_proj'] = (intermediate, hidden)
        result[f'{prefix}.mlp.down_proj'] = (hidden, intermediate)
        full = kind == 'full_attention'
        head = text['global_head_dim'] if full else text['head_dim']
        shared_value = full and text['attention_k_eq_v']
        kv_heads = text['num_global_key_value_heads'] if shared_value else text['num_key_value_heads']
        if text['num_attention_heads'] % kv_heads:
            raise ValueError('query heads must be divisible by KV heads')
        query = text['num_attention_heads'] * head
        result[f'{prefix}.self_attn.q_proj'] = (query, hidden)
        result[f'{prefix}.self_attn.k_proj'] = (kv_heads * head, hidden)
        result[f'{prefix}.self_attn.o_proj'] = (hidden, query)
        if not shared_value:
            result[f'{prefix}.self_attn.v_proj'] = (kv_heads * head, hidden)
    return result


def validate_projection(name, original_shape, packed, scale, expected):
    if tuple(original_shape) != expected:
        raise ValueError(f'original shape disagrees with configuration: {name}')
    rows, columns = expected
    if packed['dtype'] != 'I32' or packed['shape'] != [rows, (columns + 7) // 8]:
        raise ValueError(f'invalid W4 packed shape: {name}')
    if scale['dtype'] != 'BF16' or scale['shape'] != [rows, (columns + 31) // 32]:
        raise ValueError(f'invalid group-32 scale shape: {name}')
