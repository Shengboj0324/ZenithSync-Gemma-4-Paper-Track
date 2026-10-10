"""Adapter-only resume contract over an independently verified frozen base.

Assumes a quiescent single-process model with immutable persistent frozen state.
Nonpersistent buffers must be deterministically reconstructed by the worker.
"""
from copy import deepcopy

from .contracts import digest
from .optimizer_checkpoint import capture_adamw_checkpoint, validate_adamw_restore, restore_adamw_checkpoint
from .training_rng import capture_rng_state, validate_rng_state, restore_rng_state
from .training_schedule import iter_updates
from .training_state import fingerprint_state, require_identical_state

BINDINGS = {'base_manifest_sha256', 'corpus_manifest_sha256', 'corpus_content_sha256',
            'schedule_sha256', 'worker_config_sha256'}


def validate_checkpoint_bindings(bindings, schedule):
    if not isinstance(bindings, dict) or set(bindings) != BINDINGS:
        raise ValueError('Exact checkpoint bindings required')
    for value in bindings.values():
        digest(value)
    if (bindings['schedule_sha256'] != schedule['schedule_sha256']
            or bindings['corpus_content_sha256'] != schedule['corpus_content_sha256']):
        raise ValueError('Checkpoint bindings disagree with schedule')


def _cursor(schedule, cursor):
    # Advancing this iterator validates the entire consumed prefix, even at the
    # terminal boundary. It does not execute or advance a training operation.
    next(iter_updates(schedule, resume=cursor), None)
    if cursor['completed_updates'] <= 0:
        raise ValueError('Checkpoint requires a completed optimizer update')


def _parameters(model):
    if not model.training:
        raise ValueError('Training-mode model required')
    rows = [(name, parameter) for name, parameter in model.named_parameters(remove_duplicate=False)
            if parameter.requires_grad]
    if not rows or len({id(parameter) for _, parameter in rows}) != len(rows):
        raise ValueError('Unique nonempty trainable parameters required; aliases unsupported')
    state = model.state_dict()
    if any(name not in state for name, _ in rows) or len(state) <= len(rows):
        raise ValueError('Adapter checkpoint requires separate persistent frozen state')
    return rows


def frozen_state(model):
    return fingerprint_state(model, excluded_names=[name for name, _ in _parameters(model)])


def _cpu_copy(value):
    import torch
    if isinstance(value, torch.Tensor):
        return value.detach().to(device='cpu', copy=True)
    if isinstance(value, dict):
        return {key: _cpu_copy(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_cpu_copy(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_cpu_copy(item) for item in value)
    return deepcopy(value)


def capture_adapter_checkpoint(model, optimizer, *, bindings, schedule, cursor, expected_frozen):
    import torch
    validate_checkpoint_bindings(bindings, schedule)
    _cursor(schedule, cursor)
    rows = _parameters(model)
    require_identical_state(expected_frozen, frozen_state(model))
    if any(not torch.isfinite(parameter).all().item() for _, parameter in rows):
        raise ValueError('Nonfinite adapter parameter')
    optimizer_state = capture_adamw_checkpoint(
        optimizer, rows, completed_steps=cursor['completed_updates'])
    return {'schema_version': 1, 'bindings': deepcopy(bindings),
            'module_modes': {name: module.training for name, module in model.named_modules()},
            'cursor': deepcopy(cursor), 'frozen_state': deepcopy(expected_frozen),
            'adapter': {name: _cpu_copy(parameter) for name, parameter in rows},
            'optimizer': _cpu_copy(optimizer_state), 'rng': capture_rng_state()}


def restore_adapter_checkpoint(model, optimizer, payload, *, bindings, schedule, expected_frozen):
    """Reject incompatible checkpoints before mutation; discard state on apply failure.

    The caller must independently verify base/corpus/config artifacts and load a
    hash-bound payload. Hash strings alone do not authenticate those artifacts.
    """
    import torch
    fields = {'schema_version', 'bindings', 'module_modes', 'cursor', 'frozen_state', 'adapter', 'optimizer', 'rng'}
    if (not isinstance(payload, dict) or set(payload) != fields
            or type(payload['schema_version']) is not int or payload['schema_version'] != 1):
        raise ValueError('Invalid adapter checkpoint schema')
    validate_checkpoint_bindings(bindings, schedule)
    if payload['bindings'] != bindings:
        raise ValueError('Checkpoint artifact bindings differ')
    modes = {name: module.training for name, module in model.named_modules()}
    if (not isinstance(payload['module_modes'], dict)
            or any(type(value) is not bool for value in payload['module_modes'].values())
            or payload['module_modes'] != modes):
        raise ValueError('Model module training modes differ')
    _cursor(schedule, payload['cursor'])
    rows = _parameters(model)
    require_identical_state(expected_frozen, payload['frozen_state'])
    require_identical_state(expected_frozen, frozen_state(model))
    if not isinstance(payload['adapter'], dict) or set(payload['adapter']) != {name for name, _ in rows}:
        raise ValueError('Adapter parameter names differ')
    for name, parameter in rows:
        value = payload['adapter'][name]
        if (not isinstance(value, torch.Tensor) or value.device.type != 'cpu'
                or value.layout != torch.strided or value.shape != parameter.shape
                or value.dtype != parameter.dtype or not torch.isfinite(value).all().item()):
            raise ValueError('Adapter tensor differs: ' + name)
    if payload['optimizer'].get('completed_steps') != payload['cursor']['completed_updates']:
        raise ValueError('Optimizer and data cursor step counts differ')
    validate_adamw_restore(optimizer, rows, payload['optimizer'])
    validate_rng_state(payload['rng'])
    # From here failures may have partially changed state (for example CUDA OOM).
    # The worker must abandon this model/optimizer instance rather than retry it.
    with torch.no_grad():
        for name, parameter in rows:
            parameter.copy_(payload['adapter'][name])
    restore_adamw_checkpoint(optimizer, rows, payload['optimizer'])
    restore_rng_state(payload['rng'])
    return deepcopy(payload['cursor'])
