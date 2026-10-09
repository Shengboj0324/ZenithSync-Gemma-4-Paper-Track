"""Bounded-copy state fingerprints for quiescent, single-process training.

These fingerprints detect byte changes; they do not establish numerical quality.
Call only between completed model operations, with no concurrent state writers.
"""

import hashlib


def fingerprint_state(model, *, excluded_names=(), chunk_bytes=8 * 1024 * 1024):
    """Hash parameters and persistent buffers without cloning entire tensors.

    Exclusions are exact state-dict names, never substring rules. Noncontiguous,
    sparse, quantized and meta tensors are rejected instead of silently creating
    potentially model-sized copies. CPU transfer is synchronous. At most one
    chunk is transferred at a time; Python conversion adds another chunk copy.
    Device placement is deliberately absent from the identity, allowing reload
    comparison across devices. Shape and dtype remain part of that identity.
    """
    import torch

    if type(chunk_bytes) is not int or chunk_bytes <= 0:
        raise ValueError('chunk_bytes must be a positive integer')
    exclusions = tuple(excluded_names)
    if any(not isinstance(name, str) for name in exclusions):
        raise ValueError('Excluded state names must be strings')
    if len(set(exclusions)) != len(exclusions):
        raise ValueError('Duplicate excluded state name')
    state = model.state_dict()
    if not state or set(exclusions) - state.keys():
        raise ValueError('Empty state or unknown excluded state name')
    selected = sorted(state.keys() - set(exclusions))
    if not selected:
        raise ValueError('Cannot exclude the entire model state')
    result = {}
    for name in selected:
        tensor = state[name]
        if (not isinstance(tensor, torch.Tensor) or tensor.is_meta
                or tensor.layout != torch.strided or tensor.is_quantized
                or not tensor.is_contiguous() or tensor.is_conj() or tensor.is_neg()):
            raise ValueError('Unsupported state representation: ' + name)
        # Flatten before reinterpreting bytes: scalar tensors otherwise fail.
        raw = tensor.detach().reshape(-1).view(torch.uint8)
        digest = hashlib.sha256()
        for start in range(0, raw.numel(), chunk_bytes):
            digest.update(raw[start:start + chunk_bytes].cpu().numpy().tobytes())
        result[name] = {'shape': list(tensor.shape), 'dtype': str(tensor.dtype),
                        'bytes': raw.numel(), 'sha256': digest.hexdigest()}
    return result


def require_identical_state(before, after):
    """Reject missing/added tensors, metadata drift, and any content change."""
    if not before or not after:
        raise ValueError('Nonempty state fingerprints required')
    missing = sorted(before.keys() - after.keys())
    added = sorted(after.keys() - before.keys())
    changed = sorted(name for name in before.keys() & after.keys()
                     if before[name] != after[name])
    if missing or added or changed:
        raise ValueError(f'State changed: missing={missing}, added={added}, changed={changed}')
