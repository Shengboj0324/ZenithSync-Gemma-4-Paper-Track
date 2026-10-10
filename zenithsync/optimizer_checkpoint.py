"""Identity-checked single-group AdamW checkpoint contract.

Scope: dense, non-AMSGrad AdamW with a state entry for every trainable tensor.
RNG, data-cursor and scheduler recovery are separate resume requirements.
"""


def _metadata(named_parameters):
    rows = list(named_parameters)
    names = [name for name, _ in rows]
    if not rows or any(not isinstance(name, str) or not name for name in names):
        raise ValueError('Nonempty named parameters required')
    if len(set(names)) != len(names) or len({id(value) for _, value in rows}) != len(rows):
        raise ValueError('Duplicate optimizer parameter identity')
    if any(not value.requires_grad for _, value in rows):
        raise ValueError('Optimizer parameters must be trainable')
    return rows, [{'name': name, 'shape': list(value.shape), 'dtype': str(value.dtype)}
                  for name, value in rows]


def validate_adamw_checkpoint(payload, named_parameters):
    import torch

    rows, metadata = _metadata(named_parameters)
    if (payload.get('schema_version') != 1 or payload.get('optimizer_class') != 'AdamW'
            or payload.get('parameters') != metadata):
        raise ValueError('Optimizer parameter names, order, shapes or dtypes differ')
    steps = payload.get('completed_steps')
    if type(steps) is not int or steps <= 0:
        raise ValueError('Positive completed optimizer step count required')
    state = payload['optimizer_state']
    groups = state['param_groups']
    if len(groups) != 1 or groups[0].get('amsgrad') is not False:
        raise ValueError('Exactly one non-AMSGrad AdamW group required')
    identities = groups[0]['params']
    if (len(identities) != len(rows) or any(type(identity) is not int or identity < 0 for identity in identities)
            or len(set(identities)) != len(identities) or set(state['state']) != set(identities)):
        raise ValueError('Optimizer state coverage or identities differ')
    moment_elements = 0
    for identity, (name, parameter) in zip(identities, rows, strict=True):
        item = state['state'][identity]
        if set(item) != {'step', 'exp_avg', 'exp_avg_sq'}:
            raise ValueError('Unexpected AdamW state fields: ' + name)
        step = item['step']
        if (not isinstance(step, torch.Tensor) or step.numel() != 1
                or not torch.isfinite(step).all() or step.item() != steps):
            raise ValueError('Optimizer step counter differs: ' + name)
        for key in ['exp_avg', 'exp_avg_sq']:
            value = item[key]
            if (not isinstance(value, torch.Tensor) or value.layout != torch.strided
                    or value.shape != parameter.shape or value.dtype != parameter.dtype
                    or not torch.isfinite(value).all()):
                raise ValueError('Invalid optimizer moment: ' + name + '/' + key)
            moment_elements += value.numel()
        if (item['exp_avg_sq'] < 0).any():
            raise ValueError('Negative second moment: ' + name)
    return {'parameters': len(rows), 'moment_elements': moment_elements, 'completed_steps': steps}


def capture_adamw_checkpoint(optimizer, named_parameters, *, completed_steps):
    import torch

    rows, metadata = _metadata(named_parameters)
    if type(optimizer) is not torch.optim.AdamW or len(optimizer.param_groups) != 1:
        raise ValueError('Single-group torch AdamW required')
    owned = optimizer.param_groups[0]['params']
    if len(owned) != len(rows) or any(left is not right for left, (_, right) in zip(owned, rows, strict=True)):
        raise ValueError('Optimizer owns different parameters or ordering')
    payload = {'schema_version': 1, 'optimizer_class': 'AdamW',
               'parameters': metadata, 'completed_steps': completed_steps,
               'optimizer_state': optimizer.state_dict()}
    validate_adamw_checkpoint(payload, rows)
    return payload


def validate_adamw_restore(optimizer, named_parameters, payload):
    """Reject identity or hyperparameter drift before mutating the optimizer."""
    import torch

    rows, _ = _metadata(named_parameters)
    validate_adamw_checkpoint(payload, rows)
    if type(optimizer) is not torch.optim.AdamW or len(optimizer.param_groups) != 1:
        raise ValueError('Single-group torch AdamW required')
    owned = optimizer.param_groups[0]['params']
    if len(owned) != len(rows) or any(left is not right for left, (_, right) in zip(owned, rows, strict=True)):
        raise ValueError('Resume optimizer owns different parameters')
    current = {key: value for key, value in optimizer.state_dict()['param_groups'][0].items() if key != 'params'}
    saved = {key: value for key, value in payload['optimizer_state']['param_groups'][0].items() if key != 'params'}
    if current != saved:
        raise ValueError('Resume optimizer hyperparameters differ')


def restore_adamw_checkpoint(optimizer, named_parameters, payload):
    validate_adamw_restore(optimizer, named_parameters, payload)
    optimizer.load_state_dict(payload['optimizer_state'])
