"""Exact-shape LoRA attachment for the full Gemma corpus worker."""
import re


def attach_training_adapter(base, target_shapes):
    import torch
    from peft import LoraConfig, get_peft_model
    if not target_shapes:
        raise ValueError('Nonempty exact target shapes required')
    modules = dict(base.named_modules())
    for name, shape in target_shapes.items():
        module = modules.get(name)
        if not isinstance(module, torch.nn.Linear) or list(module.weight.shape) != list(shape):
            raise ValueError('Unexpected projection: ' + name)
    model = get_peft_model(base, LoraConfig(
        r=4, lora_alpha=8, lora_dropout=0.0, bias='none',
        target_modules='(?:' + '|'.join(re.escape(name) for name in sorted(target_shapes)) + ')'))
    parameters = [(name, value) for name, value in model.named_parameters() if value.requires_grad]
    expected = {f'base_model.model.{name}.lora_{side}.default.weight'
                for name in target_shapes for side in ('A', 'B')}
    if {name for name, _ in parameters} != expected:
        raise ValueError('Unexpected trainable adapter coverage')
    if sum(value.numel() for _, value in parameters) != 4 * sum(a+b for a, b in target_shapes.values()):
        raise ValueError('Adapter parameter count differs from projection accounting')
    model.config.use_cache = False
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
    model.train()
    return model
