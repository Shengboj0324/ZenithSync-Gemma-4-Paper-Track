"""Audit the original full-GPU one-step AdamW export without inventing names."""

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record, load_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--qualification', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    receipt = load_json(args.qualification / 'receipt.json')
    expected = next(row for row in receipt['artifacts']['files'] if row['path'] == 'optimizer.pt')
    identity = file_record(args.qualification / 'optimizer.pt')
    if identity != {key: expected[key] for key in ['size_bytes', 'sha256']}:
        raise ValueError('Optimizer file differs from qualification receipt')
    import torch
    torch.set_num_threads(1)
    state = torch.load(args.qualification / 'optimizer.pt', map_location='cpu', weights_only=True)
    if set(state) != {'state', 'param_groups'} or len(state['param_groups']) != 1:
        raise ValueError('Expected original single-group optimizer export')
    group = state['param_groups'][0]
    identifiers = group['params']
    if len(set(identifiers)) != len(identifiers) or set(identifiers) != set(state['state']):
        raise ValueError('Optimizer state coverage mismatch')
    beta1, beta2 = group['betas']
    if not (0 <= beta1 < 1 and 0 <= beta2 < 1) or group['amsgrad']:
        raise ValueError('Unsupported AdamW configuration')
    coefficient = (1 - beta2) / (1 - beta1)**2
    elements = 0
    nonzero_first_moments = 0
    largest_residual = 0.0
    for values in state['state'].values():
        if set(values) != {'step', 'exp_avg', 'exp_avg_sq'} or values['step'].item() != 1:
            raise ValueError('Expected complete first-step AdamW state')
        first, second = values['exp_avg'], values['exp_avg_sq']
        if first.shape != second.shape or first.dtype != second.dtype:
            raise ValueError('Moment shape or dtype disagreement')
        if not torch.isfinite(first).all() or not torch.isfinite(second).all() or (second < 0).any():
            raise ValueError('Invalid optimizer moments')
        # At step one, m=(1-beta1)g and v=(1-beta2)g^2. Eliminate g
        # and compare in FP64 with a declared numerical tolerance in stored dtype.
        predicted = first.double().square() * coefficient
        observed = second.double()
        residual = (observed - predicted).abs()
        limits = torch.finfo(first.dtype)
        tolerance = 8 * limits.eps * (observed.abs() + predicted.abs()) + 8 * limits.tiny
        if (residual > tolerance).any():
            raise ValueError('First-step Adam moment relation fails rounding tolerance')
        largest_residual = max(largest_residual, residual.max().item())
        nonzero_first_moments += int(torch.count_nonzero(first).item())
        elements += first.numel()
    if elements != receipt['trainable_parameters']:
        raise ValueError('Optimizer moment element count differs from adapter count')
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'receipt.json').write_bytes(canonical_json({
        'schema_version': 1, 'status': 'original_optimizer_numerical_audit_passed',
        'optimizer_file': identity, 'parameter_tensors': len(identifiers),
        'parameter_elements': elements, 'nonzero_first_moment_elements': nonzero_first_moments,
        'largest_first_step_relation_absolute_residual': largest_residual,
        'rounding_tolerance': '8*eps*(abs(observed)+abs(predicted)) + 8*tiny in stored dtype',
        'parameter_names_present': 'param_names' in group,
        'verifier': file_record(Path(__file__)),
        'scope': 'Numeric moments/counters only; no parameter-name binding, resume or coding-quality claim'}))
    print('Original optimizer moments and first-step relation passed; parameter-name binding remains absent')


if __name__ == '__main__':
    main()
