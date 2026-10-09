"""Reduced random Gemma4: adapter coverage, causal loss, and optimizer resume.

Uses synthetic token IDs, not a training corpus or the downloaded checkpoint.
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
    if version('transformers') != '5.13.1' or version('peft') != '0.21.2':
        raise ValueError('Pinned architecture and adapter versions required')
    import torch
    from transformers import Gemma4TextConfig, Gemma4ForCausalLM
    from peft import LoraConfig, PeftModel, get_peft_model

    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(7181)
    config = Gemma4TextConfig(vocab_size=64, hidden_size=64, intermediate_size=128,
        num_hidden_layers=2, num_attention_heads=4, num_key_value_heads=2,
        num_global_key_value_heads=2, head_dim=16, global_head_dim=16,
        hidden_size_per_layer_input=0, attention_k_eq_v=True,
        layer_types=['sliding_attention', 'full_attention'], sliding_window=8,
        max_position_embeddings=32, attention_dropout=0.0, use_cache=False)
    config._attn_implementation = 'eager'
    initial = Gemma4ForCausalLM(config)
    base_state = copy.deepcopy(initial.state_dict())
    targets = ['q_proj', 'k_proj', 'v_proj', 'o_proj', 'gate_proj', 'up_proj', 'down_proj']
    shapes = {name: tuple(module.weight.shape) for name, module in initial.named_modules()
              if name.split('.')[-1] in targets}
    if len(shapes) != 13 or any('layers.1.self_attn.v_proj' in name for name in shapes):
        raise ValueError('Unexpected shared-key/value projection layout')
    model = get_peft_model(initial, LoraConfig(r=4, lora_alpha=8, lora_dropout=0,
                                              target_modules=targets, bias='none'))
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})

    def trainable(current):
        return [(name, parameter) for name, parameter in current.named_parameters() if parameter.requires_grad]

    expected = sum(4 * (rows + cols) for rows, cols in shapes.values())
    if sum(p.numel() for _, p in trainable(model)) != expected:
        raise ValueError('Adapter parameter count disagrees with projection dimensions')
    attached = {name.removeprefix('base_model.model.') for name, module in model.named_modules()
                if hasattr(module, 'lora_A')}
    if attached != shapes.keys():
        raise ValueError('Adapter coverage differs from intended projections')
    tokens = torch.tensor([[2, 7, 8, 9, 10, 1], [2, 11, 12, 1, 0, 0]])
    attention = tokens.ne(0).long()
    labels = tokens.clone()
    labels[:, :3] = -100
    labels[attention == 0] = -100
    selected = labels[:, 1:] != -100
    if selected.sum().item() != 4:
        raise ValueError('Synthetic loss-mask fixture changed')

    def step(current, optimizer):
        current.train()
        optimizer.zero_grad(set_to_none=True)
        result = current(input_ids=tokens, attention_mask=attention, labels=labels)
        result.logits.retain_grad()
        logits = result.logits[:, :-1, :].float()[selected]
        desired = labels[:, 1:][selected]
        independent = (torch.logsumexp(logits, dim=-1)
                       - logits.gather(1, desired[:, None]).squeeze(1)).mean()
        torch.testing.assert_close(result.loss, independent, rtol=1e-6, atol=1e-6)
        if not torch.isfinite(result.loss):
            raise ValueError('Nonfinite masked loss')
        result.loss.backward()
        with torch.no_grad():
            expected_gradient = torch.zeros_like(result.logits)
            active_gradient = logits.softmax(dim=-1)
            active_gradient[torch.arange(desired.numel()), desired] -= 1
            expected_gradient[:, :-1, :][selected] = active_gradient / desired.numel()
            torch.testing.assert_close(result.logits.grad, expected_gradient, rtol=1e-5, atol=1e-7)
            ignored = torch.ones_like(labels, dtype=torch.bool)
            ignored[:, :-1] = ~selected
            if torch.count_nonzero(result.logits.grad[ignored]):
                raise ValueError('Masked or final-position logits received loss gradients')
        for name, parameter in trainable(current):
            if parameter.grad is None or not torch.isfinite(parameter.grad).all():
                raise ValueError('Missing or nonfinite adapter gradient: ' + name)
        if not any(torch.count_nonzero(p.grad) for _, p in trainable(current)):
            raise ValueError('No adapter learning signal')
        optimizer.step()
        return result.loss.item()

    optimizer = torch.optim.AdamW([p for _, p in trainable(model)], lr=0.001, weight_decay=0)
    first_loss = step(model, optimizer)
    args.output.mkdir(parents=True, exist_ok=False)
    adapter = args.output / 'adapter-step-1'
    model.save_pretrained(adapter, safe_serialization=True)
    torch.save({'optimizer': optimizer.state_dict(), 'names': [n for n, _ in trainable(model)],
                'completed_steps': 1}, args.output / 'optimizer-step-1.pt')
    second_loss = step(model, optimizer)

    fresh = Gemma4ForCausalLM(copy.deepcopy(config))
    fresh.load_state_dict(base_state)
    resumed = PeftModel.from_pretrained(fresh, adapter, is_trainable=True)
    resumed.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
    checkpoint = torch.load(args.output / 'optimizer-step-1.pt', weights_only=True, map_location='cpu')
    if checkpoint['names'] != [name for name, _ in trainable(resumed)] or checkpoint['completed_steps'] != 1:
        raise ValueError('Optimizer parameter mapping changed')
    resumed_optimizer = torch.optim.AdamW([p for _, p in trainable(resumed)], lr=0.001, weight_decay=0)
    resumed_optimizer.load_state_dict(checkpoint['optimizer'])
    resumed_loss = step(resumed, resumed_optimizer)
    if second_loss != resumed_loss:
        raise ValueError('Resumed loss differs from uninterrupted run')
    for (name, left), (other_name, right) in zip(trainable(model), trainable(resumed), strict=True):
        if name != other_name:
            raise ValueError('Adapter mapping changed')
        torch.testing.assert_close(left, right, rtol=0, atol=0)
    original_optimizer = optimizer.state_dict()
    restored_optimizer = resumed_optimizer.state_dict()
    if original_optimizer['param_groups'] != restored_optimizer['param_groups']:
        raise ValueError('Optimizer parameter groups differ after resume')
    if original_optimizer['state'].keys() != restored_optimizer['state'].keys():
        raise ValueError('Optimizer state identities differ after resume')
    for identity, values in original_optimizer['state'].items():
        restored_values = restored_optimizer['state'][identity]
        if values.keys() != restored_values.keys():
            raise ValueError('Optimizer state fields differ after resume')
        for key, value in values.items():
            torch.testing.assert_close(value, restored_values[key], rtol=0, atol=0)
    for current in [model, resumed]:
        for name, parameter in current.base_model.model.named_parameters():
            if '.lora_' in name:
                continue
            original_name = name.replace('.base_layer.', '.')
            if parameter.requires_grad or parameter.grad is not None:
                raise ValueError('Base was not frozen: ' + name)
            torch.testing.assert_close(parameter, base_state[original_name], rtol=0, atol=0)
    (args.output / 'receipt.json').write_bytes(canonical_json({
        'schema_version': 1, 'status': 'reduced_gemma_cpu_checks_passed',
        'versions': {n: version(n) for n in ['torch', 'transformers', 'peft']},
        'config': config.to_dict(), 'projection_shapes': shapes, 'trainable_parameters': expected,
        'supervised_next_tokens': selected.sum().item(), 'first_loss': first_loss,
        'second_loss': second_loss, 'resumed_loss': resumed_loss,
        'resume_parameter_comparison': 'bitwise_equal', 'verifier': file_record(Path(__file__)),
        'resume_optimizer_comparison': 'bitwise_equal', 'masked_logit_gradients': 'exactly_zero',
        'scope': 'Random reduced text-only Gemma4 CPU FP32; no checkpoint/CUDA/BF16/native-chat-mask qualification'}))
    print('Reduced Gemma: adapter coverage, masked loss, frozen base and optimizer resume passed')


if __name__ == '__main__':
    main()
