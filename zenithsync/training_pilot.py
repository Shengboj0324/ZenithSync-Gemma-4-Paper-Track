"""One-update qualification engine; not a corpus trainer or performance claim."""

import gc
import json
import math
import re
import time

from zenithsync.training_state import fingerprint_state, require_identical_state
from zenithsync.optimizer_checkpoint import capture_adamw_checkpoint


def _stage(name):
    print(json.dumps({'training_stage': name, 'monotonic_seconds': time.monotonic()}), flush=True)


def _adapter_names(model):
    names = [name for name, value in model.named_parameters() if value.requires_grad]
    if not names or any('.lora_A.default.weight' not in name
                        and '.lora_B.default.weight' not in name for name in names):
        raise ValueError('Only default LoRA A/B weights may be trainable')
    return names


def _adapter_fingerprint(model, names):
    return fingerprint_state(model, excluded_names=set(model.state_dict()) - set(names))


def _updated_adapter(load_base, batch, target_shapes, rank, alpha, learning_rate, output):
    # Function scope ensures graphs, optimizer references and parameter aliases
    # are released before the caller constructs the second full base model.
    import torch
    from peft import LoraConfig, get_peft_model

    _stage('initial_base_load_started')
    base = load_base()
    _stage('initial_base_loaded')
    modules = dict(base.named_modules())
    for name, shape in target_shapes.items():
        module = modules.get(name)
        if not isinstance(module, torch.nn.Linear) or list(module.weight.shape) != list(shape):
            raise ValueError('Target is absent or has unexpected shape: ' + name)
    _stage('adapter_attachment_started')
    model = get_peft_model(base, LoraConfig(
        r=rank, lora_alpha=alpha, lora_dropout=0.0, bias='none',
        target_modules='(?:' + '|'.join(re.escape(name) for name in sorted(target_shapes)) + ')'))
    names = _adapter_names(model)
    _stage('adapter_attachment_finished')
    expected_names = {f'base_model.model.{name}.lora_{side}.default.weight'
                      for name in target_shapes for side in ['A', 'B']}
    if set(names) != expected_names:
        raise ValueError('PEFT attached adapters to unexpected modules')
    parameters = [value for value in model.parameters() if value.requires_grad]
    count = sum(value.numel() for value in parameters)
    if count != rank * sum(rows + cols for rows, cols in target_shapes.values()):
        raise ValueError('Adapter parameter count violates rank/shape accounting')
    model.config.use_cache = False
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
    model.train()
    _stage('initial_state_hash_started')
    frozen_before = fingerprint_state(model, excluded_names=names)
    adapter_before = _adapter_fingerprint(model, names)
    _stage('initial_state_hash_finished')
    optimizer = torch.optim.AdamW(parameters, lr=learning_rate, weight_decay=0,
                                 foreach=False, fused=False)
    optimizer.zero_grad(set_to_none=True)
    _stage('forward_started')
    loss = model(**batch).loss
    if loss.ndim or not torch.isfinite(loss):
        raise ValueError('Training loss is not a finite scalar')
    loss.backward()
    _stage('backward_finished')
    if any(value.grad is None or not torch.isfinite(value.grad).all() for value in parameters):
        raise ValueError('Missing or nonfinite adapter gradient')
    if not any(torch.count_nonzero(value.grad).item() for value in parameters):
        raise ValueError('All adapter gradients are zero')
    optimizer.step()
    _stage('optimizer_step_finished')
    optimizer_checkpoint = capture_adamw_checkpoint(optimizer,
        [(name, value) for name, value in model.named_parameters() if value.requires_grad],
        completed_steps=1)
    if any(not torch.isfinite(value).all() for value in parameters):
        raise ValueError('Nonfinite updated adapter parameter')
    for name, value in model.named_parameters():
        if name not in names and (value.requires_grad or value.grad is not None):
            raise ValueError('Base parameter is not frozen: ' + name)
    require_identical_state(frozen_before, fingerprint_state(model, excluded_names=names))
    _stage('updated_frozen_state_verified')
    adapter_after = _adapter_fingerprint(model, names)
    if adapter_after == adapter_before:
        raise ValueError('Optimizer did not change the adapter')
    model.eval()
    inputs = {key: value for key, value in batch.items() if key != 'labels'}
    with torch.no_grad():
        logits = model(**inputs).logits.float().cpu()
        with model.disable_adapter():
            disabled = model(**inputs).logits.float().cpu()
    if not torch.isfinite(logits).all() or not torch.isfinite(disabled).all():
        raise ValueError('Nonfinite qualification logits')
    effect = (logits - disabled).abs().max().item()
    if effect == 0:
        raise ValueError('Updated adapter has no observable output effect')
    model.save_pretrained(output / 'adapter', safe_serialization=True)
    torch.save(optimizer_checkpoint, output / 'optimizer.pt')
    _stage('adapter_and_optimizer_saved')
    return logits, {'loss': loss.item(), 'trainable_parameters': count,
                    'adapter_effect_max_abs': effect, 'adapter_state': adapter_after,
                    'frozen_state': frozen_before}


def qualify_adapter(*, load_base, batch, target_shapes, output, rank=4, alpha=8,
                    learning_rate=1e-4, reload_atol=0.0, reload_rtol=0.0):
    """Require a fresh independently loaded base on each load_base invocation.

    The caller owns checkpoint identity, device admission, native masking,
    deadline supervision and durable storage. Batch must already be validated.
    Output must not exist. Failures preserve partial files without a receipt.
    Reload tolerances must be declared before execution, never adjusted to fit.
    """
    import torch
    from peft import PeftModel
    from zenithsync.artifacts import canonical_json, inventory

    if type(rank) is not int or rank <= 0 or not target_shapes:
        raise ValueError('Positive rank and nonempty exact target shapes required')
    for name, value in [('alpha', alpha), ('learning_rate', learning_rate),
                        ('reload_atol', reload_atol), ('reload_rtol', reload_rtol)]:
        if isinstance(value, bool) or not math.isfinite(value) or value < 0:
            raise ValueError('Invalid numeric configuration: ' + name)
    if alpha == 0 or learning_rate == 0:
        raise ValueError('Positive alpha and learning rate required')
    output.mkdir(parents=True, exist_ok=False)
    logits, result = _updated_adapter(load_base, batch, target_shapes, rank, alpha,
                                     learning_rate, output)
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    _stage('fresh_base_and_adapter_load_started')
    restored = PeftModel.from_pretrained(load_base(), output / 'adapter', is_trainable=True)
    _stage('fresh_base_and_adapter_loaded')
    restored.eval()
    names = _adapter_names(restored)
    require_identical_state(result['adapter_state'], _adapter_fingerprint(restored, names))
    require_identical_state(result['frozen_state'], fingerprint_state(restored, excluded_names=names))
    _stage('reloaded_state_verified')
    with torch.no_grad():
        actual = restored(**{key: value for key, value in batch.items() if key != 'labels'}).logits.float().cpu()
    torch.testing.assert_close(actual, logits, atol=reload_atol, rtol=reload_rtol)
    _stage('reloaded_outputs_verified')
    result.update({'schema_version': 1, 'status': 'one_update_and_reload_passed',
                   'reload_max_abs_error': (actual - logits).abs().max().item(),
                   'reload_atol': reload_atol, 'reload_rtol': reload_rtol,
                   'scope': 'Caller-selected model and fixture only; no corpus or quality qualification',
                   'artifacts': inventory(output, kind='fixture', source='adapter qualification', revision='001')})
    (output / 'receipt.json').write_bytes(canonical_json(result))
    return result
