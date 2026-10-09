"""Synthetic W4/group32 codec and PEFT gradient/reload qualification on CPU.

This does not load Gemma, qualify CUDA, or supply any model-training examples.
"""

import argparse
import copy
from importlib.metadata import version
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    required = {'transformers': '5.13.1', 'compressed-tensors': '0.15.0.1', 'peft': '0.21.2'}
    if any(version(name) != expected for name, expected in required.items()):
        raise ValueError('Unexpected dependency version')
    import torch
    from torch import nn
    from compressed_tensors.compressors.pack_quantized import PackedQuantizationCompressor
    from compressed_tensors.quantization import QuantizationArgs, QuantizationScheme
    from peft import LoraConfig, PeftModel, get_peft_model

    torch.set_num_threads(1)
    torch.manual_seed(7103)
    args.output.mkdir(parents=True, exist_ok=False)
    scheme = QuantizationScheme(targets=['Linear'], weights=QuantizationArgs(
        num_bits=4, type='int', symmetric=True, strategy='group', group_size=32))
    integers = torch.arange(8 * 64).reshape(8, 64) % 16 - 8
    weight = integers.to(torch.bfloat16) / 8
    scale = torch.full((8, 2), 0.125, dtype=torch.bfloat16)
    packed = PackedQuantizationCompressor.compress({'weight': weight, 'weight_scale': scale}, scheme)
    if packed['weight_packed'].dtype != torch.int32 or packed['weight_packed'].shape != (8, 8):
        raise ValueError('Packed representation differs from W4 contract')
    unpacked = PackedQuantizationCompressor.decompress(packed, scheme)['weight']
    torch.testing.assert_close(unpacked, weight, rtol=0, atol=0)

    class Toy(nn.Module):
        def __init__(self):
            super().__init__()
            self.proj = nn.Linear(64, 8, bias=False, dtype=torch.float64)
            with torch.no_grad():
                self.proj.weight.copy_(unpacked)

        def forward(self, x):
            return self.proj(x)

    base = Toy()
    frozen = copy.deepcopy(base.state_dict())
    model = get_peft_model(base, LoraConfig(r=4, lora_alpha=8, lora_dropout=0,
                                           target_modules=['proj'], bias='none'))
    layer = model.base_model.model.proj
    a, b = layer.lora_A.default.weight, layer.lora_B.default.weight
    parameters = [p for p in model.parameters() if p.requires_grad]
    if sum(p.numel() for p in parameters) != 4 * (64 + 8):
        raise ValueError('Unexpected adapter parameter count')
    if layer.base_layer.weight.requires_grad:
        raise ValueError('Base weight must be frozen')
    x = torch.randn(3, 64, dtype=torch.float64)
    target = torch.randn(3, 8, dtype=torch.float64)
    optimizer = torch.optim.AdamW(parameters, lr=0.005, weight_decay=0)
    errors = []
    for step in range(2):
        optimizer.zero_grad(set_to_none=True)
        y = model(x)
        loss = (y - target).square().mean()
        loss.backward()
        with torch.no_grad():
            dy = 2 * (y - target) / y.numel()
            expected_b = 2 * dy.T @ (x @ a.T)
            expected_a = 2 * (dy @ b).T @ x
            torch.testing.assert_close(a.grad, expected_a, rtol=1e-10, atol=1e-10)
            torch.testing.assert_close(b.grad, expected_b, rtol=1e-10, atol=1e-10)
            if not torch.isfinite(loss) or not all(torch.isfinite(p.grad).all() for p in parameters):
                raise ValueError('Nonfinite loss or gradient')
            if not torch.count_nonzero(b.grad) or (step and not torch.count_nonzero(a.grad)):
                raise ValueError('Expected adapter learning signal absent')
            errors.append({'step': step, 'loss': loss.item(),
                           'a_gradient_max_error': (a.grad - expected_a).abs().max().item(),
                           'b_gradient_max_error': (b.grad - expected_b).abs().max().item()})
        optimizer.step()
    torch.testing.assert_close(layer.base_layer.weight, frozen['proj.weight'], rtol=0, atol=0)
    if layer.base_layer.weight.grad is not None:
        raise ValueError('Frozen base unexpectedly has a gradient')
    model.eval()
    with torch.no_grad():
        trained = model(x)
        with model.disable_adapter():
            disabled = model(x)
        if torch.equal(trained, disabled):
            raise ValueError('Trained adapter has no measured output effect')
    adapter_dir = args.output / 'adapter'
    model.save_pretrained(adapter_dir, safe_serialization=True)
    restored = PeftModel.from_pretrained(Toy(), adapter_dir).eval()
    with torch.no_grad():
        reloaded = restored(x)
    torch.testing.assert_close(trained, reloaded, rtol=0, atol=0)
    (args.output / 'receipt.json').write_bytes(canonical_json({
        'schema_version': 1, 'status': 'synthetic_cpu_adapter_checks_passed',
        'versions': {name: version(name) for name in [*required, 'torch']},
        'trainable_parameters': sum(p.numel() for p in parameters), 'gradient_checks': errors,
        'adapter_effect_max_abs': (trained - disabled).abs().max().item(),
        'reload_max_abs_error': (trained - reloaded).abs().max().item(),
        'verifier': file_record(Path(__file__)),
        'scope': 'Synthetic exact-grid W4 codec and FP64 PEFT gradients; no Gemma/CUDA/optimizer-resume qualification'}))
    print('CPU codec, analytical gradients, frozen base, adapter effect and reload passed')


if __name__ == '__main__':
    main()
