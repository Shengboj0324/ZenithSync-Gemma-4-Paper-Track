"""Synthetic BF16 Gemma W4 checkpoint -> Transformers -> PEFT qualification.

Exercises released loader code on a reduced random text model, not the 31B model.
"""

import argparse
import copy
from importlib.metadata import version
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record, inventory
from zenithsync.training_state import fingerprint_state, require_identical_state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    required = {'transformers': '5.13.1', 'compressed-tensors': '0.15.0.1', 'peft': '0.21.2'}
    if any(version(name) != value for name, value in required.items()):
        raise ValueError('Pinned loader dependencies required')
    import torch
    from transformers import Gemma4TextConfig, Gemma4ForCausalLM, CompressedTensorsConfig
    from compressed_tensors.quantization import (
        QuantizationConfig, QuantizationScheme, QuantizationArgs, apply_quantization_config)
    from compressed_tensors.compressors import ModelCompressor
    from peft import LoraConfig, PeftModel, get_peft_model

    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(7301)
    config = Gemma4TextConfig(vocab_size=64, hidden_size=64, intermediate_size=128,
        num_hidden_layers=2, num_attention_heads=4, num_key_value_heads=2,
        num_global_key_value_heads=2, head_dim=16, global_head_dim=16,
        hidden_size_per_layer_input=0, attention_k_eq_v=True,
        layer_types=['sliding_attention', 'full_attention'], max_position_embeddings=32,
        sliding_window=8, use_cache=False, attention_dropout=0.0)
    config._attn_implementation = 'eager'
    original = Gemma4ForCausalLM(config).to(torch.bfloat16)
    quantization = QuantizationConfig(config_groups={'group_0': QuantizationScheme(
        targets=['Linear'], weights=QuantizationArgs(num_bits=4, type='int', symmetric=True,
        strategy='group', group_size=32))}, ignore=['lm_head'], format='pack-quantized',
        quantization_status='frozen')
    apply_quantization_config(original, quantization)
    with torch.no_grad():
        for module in original.modules():
            if hasattr(module, 'weight_scale'):
                # Synthetic calibration only; not a calibration recipe for Gemma weights.
                scale = module.weight.reshape(module.weight.shape[0], -1, 32).abs().amax(-1)
                module.weight_scale.copy_(scale.clamp_min(1e-6) / 7)
                if hasattr(module, 'weight_zero_point'):
                    module.weight_zero_point.zero_()
    compressor = ModelCompressor(quantization_config=quantization, force_compression_format='pack-quantized')
    compressor.compress_model(original)
    packed_count = sum('weight_packed' in name for name, _ in original.named_parameters())
    if packed_count != 13:
        raise ValueError('Unexpected packed projection coverage')
    args.output.mkdir(parents=True, exist_ok=False)
    checkpoint = args.output / 'base'
    original.save_pretrained(checkpoint)
    compressor.update_config(str(checkpoint))
    compressor.decompress_model(original)
    expected_state = copy.deepcopy(original.state_dict())

    def load_base():
        return Gemma4ForCausalLM.from_pretrained(checkpoint, local_files_only=True,
            quantization_config=CompressedTensorsConfig(run_compressed=False),
            dtype=torch.bfloat16, attn_implementation='eager')

    loaded = load_base()
    if any('weight_packed' in name for name, _ in loaded.named_parameters()):
        raise ValueError('Packed weights remain after explicit decompression')
    if loaded.state_dict().keys() != expected_state.keys():
        raise ValueError('Loaded state identities differ')
    for name, value in loaded.state_dict().items():
        torch.testing.assert_close(value, expected_state[name], rtol=0, atol=0)
    model = get_peft_model(loaded, LoraConfig(r=4, lora_alpha=8, lora_dropout=0,
        target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj', 'gate_proj', 'up_proj', 'down_proj'], bias='none'))
    parameters = [p for p in model.parameters() if p.requires_grad]
    if len(parameters) != 26 or sum(p.numel() for p in parameters) != 7808:
        raise ValueError('Unexpected adapter coverage')
    adapter_names = [name for name, parameter in model.named_parameters() if parameter.requires_grad]
    frozen_before = fingerprint_state(model, excluded_names=adapter_names)
    optimizer = torch.optim.AdamW(parameters, lr=0.005, weight_decay=0)
    ids = torch.tensor([[2, 3, 4, 5, 1]])
    labels = ids.clone()
    labels[:, :2] = -100
    loss = model(input_ids=ids, labels=labels).loss
    loss.backward()
    if not torch.isfinite(loss) or any(p.grad is None or not torch.isfinite(p.grad).all() for p in parameters):
        raise ValueError('Invalid adapter gradients')
    if not any(torch.count_nonzero(p.grad) for p in parameters):
        raise ValueError('No adapter learning signal')
    optimizer.step()
    require_identical_state(frozen_before, fingerprint_state(model, excluded_names=adapter_names))
    for name, parameter in model.base_model.model.named_parameters():
        if '.lora_' not in name:
            if parameter.requires_grad or parameter.grad is not None:
                raise ValueError('Base parameter was not frozen')
            torch.testing.assert_close(parameter, expected_state[name.replace('.base_layer.', '.')], rtol=0, atol=0)
    model.eval()
    with torch.no_grad():
        logits = model(ids).logits
        with model.disable_adapter():
            disabled = model(ids).logits
    if torch.equal(logits, disabled):
        raise ValueError('Adapter has no observable output effect')
    adapter = args.output / 'adapter'
    model.save_pretrained(adapter, safe_serialization=True)
    restored = PeftModel.from_pretrained(load_base(), adapter).eval()
    with torch.no_grad():
        restored_logits = restored(ids).logits
    torch.testing.assert_close(logits, restored_logits, rtol=0, atol=0)
    (args.output / 'receipt.json').write_bytes(canonical_json({
        'schema_version': 1, 'status': 'reduced_bf16_compressed_loader_adapter_checks_passed',
        'versions': {name: version(name) for name in [*required, 'torch']},
        'packed_projections': packed_count, 'trainable_parameters': sum(p.numel() for p in parameters),
        'loaded_weight_comparison': 'bitwise_equal', 'loss': loss.item(),
        'frozen_state_fingerprints': frozen_before,
        'state_verifier': file_record(ROOT / 'zenithsync/training_state.py'),
        'adapter_effect_max_abs': (logits-disabled).abs().max().item(),
        'reload_max_abs_error': (logits-restored_logits).abs().max().item(),
        'checkpoint_manifest': inventory(checkpoint, kind='fixture', source='random reduced Gemma', revision='001'),
        'verifier': file_record(Path(__file__)),
        'scope': 'BF16 CPU reduced text model; no full checkpoint, multimodal wrapper, CUDA or vLLM adapter qualification'}))
    print('BF16 compressed Gemma loader, frozen-base adapter update and adapter reload passed')


if __name__ == '__main__':
    main()
