"""Single-device token-mean update over separately attended microbatches.

The model must return mean causal loss over labels[..., 1:] != -100, with no
auxiliary loss. This contract is tested separately for each model backend.
No distributed reduction, AMP scaler, clipping or learning-rate schedule here.
"""
import math


def _target_count(batch, device):
    import torch
    if not isinstance(batch,dict) or set(batch)!={'input_ids','labels','attention_mask'}:
        raise ValueError('Exact causal batch fields required')
    if any(not isinstance(t,torch.Tensor) or t.dtype!=torch.long or t.device!=device for t in batch.values()):
        raise ValueError('Integer batch tensors must use model device')
    ids,labels,mask=batch['input_ids'],batch['labels'],batch['attention_mask']
    if ids.ndim!=2 or ids.shape!=labels.shape or ids.shape!=mask.shape or ids.shape[0]<1 or ids.shape[1]<2:
        raise ValueError('Invalid causal batch shape')
    if ((ids<0).any() or not ((mask==0)|(mask==1)).all() or (mask[:,0]!=1).any()
            or (mask[:,1:]>mask[:,:-1]).any() or (labels[:,0]!=-100).any()
            or not ((labels==-100)|(labels==ids)).all() or (labels[mask==0]!=-100).any()):
        raise ValueError('Invalid right padding or labels')
    per_row=(labels[:,1:]!=-100).sum(dim=1)
    if (per_row==0).any():raise ValueError('Every sequence needs a next-token target')
    return int(per_row.sum().item())


def token_weighted_step(model, optimizer, microbatches):
    import torch
    if torch.distributed.is_available() and torch.distributed.is_initialized():
        raise ValueError('Global distributed token normalization is not implemented')
    if not model.training or not isinstance(microbatches,list) or not microbatches:
        raise ValueError('Training model and nonempty microbatch list required')
    parameters=[p for p in model.parameters() if p.requires_grad]
    owned=[p for group in optimizer.param_groups for p in group['params']]
    if (not parameters or len(owned)!=len(parameters) or len({id(p) for p in owned})!=len(owned)
            or {id(p) for p in owned}!={id(p) for p in parameters}):
        raise ValueError('Optimizer must own exactly the trainable parameters')
    devices={p.device for p in model.parameters()}
    if len(devices)!=1:raise ValueError('Single-device model required')
    device=next(iter(devices));counts=[]
    counts = [_target_count(batch, device) for batch in microbatches]
    return streamed_token_weighted_step(model, optimizer, iter(microbatches),
                                        expected_supervised_tokens=sum(counts))


def streamed_token_weighted_step(model, optimizer, microbatches, *, expected_supervised_tokens):
    """Accumulate one microbatch at a time; step only after exact count agreement.

    On any failure discard mutable model/RNG state and restore a checkpoint.
    No optimizer step occurs for invalid data, but forwards can mutate buffers.
    """
    import torch
    if type(expected_supervised_tokens) is not int or expected_supervised_tokens <= 0:
        raise ValueError("Positive expected supervised-token count required")
    if torch.distributed.is_available() and torch.distributed.is_initialized():
        raise ValueError("Global distributed token normalization is not implemented")
    if not model.training:
        raise ValueError("Training model required")
    parameters = [p for p in model.parameters() if p.requires_grad]
    owned = [p for group in optimizer.param_groups for p in group["params"]]
    if (not parameters or len(owned) != len(parameters)
            or len({id(p) for p in owned}) != len(owned)
            or {id(p) for p in owned} != {id(p) for p in parameters}):
        raise ValueError("Optimizer must own exactly the trainable parameters")
    devices = {p.device for p in model.parameters()}
    if len(devices) != 1:
        raise ValueError("Single-device model required")
    device = next(iter(devices))
    counts = []
    if any(p.grad is not None for p in model.parameters() if not p.requires_grad):
        raise ValueError('Frozen parameter has a gradient')
    total=expected_supervised_tokens;losses=[];consumed=0
    optimizer.zero_grad(set_to_none=True)
    try:
        for batch in microbatches:
            count = _target_count(batch, device)
            consumed += count
            if consumed > total:
                raise ValueError("Stream exceeds declared supervised-token count")
            counts.append(count)
            loss=model(**batch).loss
            if not isinstance(loss,torch.Tensor) or loss.ndim!=0 or not torch.isfinite(loss).item():
                raise ValueError('Nonfinite or nonscalar causal mean loss')
            losses.append(float(loss.detach().double().item())*(count/total))
            (loss*(count/total)).backward()
            del loss, batch
        if consumed != total:
            raise ValueError("Stream differs from declared supervised-token count")
        if any(p.grad is None or not torch.isfinite(p.grad).all().item() for p in parameters):
            raise ValueError('Missing or nonfinite trainable gradient')
        if any(p.grad is not None for p in model.parameters() if not p.requires_grad):
            raise ValueError('Frozen parameter acquired a gradient')
        optimizer.step()
        if any(not torch.isfinite(p).all().item() for p in parameters):
            raise ValueError('Nonfinite parameters after optimizer update; discard mutable state')
    except BaseException:
        optimizer.zero_grad(set_to_none=True)
        # An optimizer may have partially mutated state before failing. The caller
        # must discard it and restore the last complete checkpoint, never retry it.
        raise
    return {'supervised_tokens':total,'microbatch_supervised_tokens':counts,
            'token_mean_loss':math.fsum(losses),'microbatches':len(counts)}
