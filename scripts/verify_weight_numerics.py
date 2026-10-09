"""Scan every BF16 value and hash every checkpoint byte without a GPU.

Requires NumPy. Finite weights do not prove inference or training correctness.
The caller must keep the checkpoint and validation sources quiescent.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from zenithsync.artifacts import canonical_json, file_record, load_json
from zenithsync.model_intake import inspect_safetensors


def predicates(words):
    """BF16 has one sign bit, eight exponent bits and seven fraction bits."""
    finite = (words & 0x7F80) != 0x7F80
    positive_finite = finite & ((words & 0x8000) == 0) & ((words & 0x7FFF) != 0)
    return finite, positive_finite


def verify_predicates():
    """Exhaust all encodings against independent IEEE float32 decoding."""
    words = np.arange(65536, dtype=np.uint16)
    finite, positive = predicates(words)
    for word in range(65536):
        value = struct.unpack('<f', struct.pack('<I', word << 16))[0]
        expected = math.isfinite(value)
        if bool(finite[word]) != expected or bool(positive[word]) != (expected and value > 0):
            raise ValueError(f'BF16 predicate disagreement at encoding {word}')


def signature(value):
    return (value.st_dev, value.st_ino, value.st_size,
            value.st_mtime_ns, value.st_ctime_ns)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    sources = [Path(__file__).resolve(), ROOT / 'zenithsync/model_intake.py',
               ROOT / 'zenithsync/artifacts.py', ROOT / 'zenithsync/contracts.py']
    identities = {str(p.relative_to(ROOT)): file_record(p) for p in sources}
    manifest_identity = file_record(args.manifest)
    manifest = load_json(args.manifest)
    matches = [r for r in manifest['files'] if r['path'] == args.checkpoint.name]
    if len(matches) != 1:
        raise ValueError('checkpoint must have exactly one manifest entry')
    expected = matches[0]
    verify_predicates()
    before = args.checkpoint.lstat()
    structure = inspect_safetensors(args.checkpoint)
    digest = hashlib.sha256()
    records = []
    with args.checkpoint.open('rb') as stream:
        if signature(before) != signature(os.fstat(stream.fileno())):
            raise ValueError('checkpoint changed before scan')
        prefix = stream.read(8)
        raw = stream.read(structure['header_size_bytes'])
        if hashlib.sha256(raw).hexdigest() != structure['header_sha256']:
            raise ValueError('header changed after structural validation')
        digest.update(prefix)
        digest.update(raw)
        header = json.loads(raw)
        header.pop('__metadata__', None)
        for name, tensor in sorted(header.items(), key=lambda pair: (*pair[1]['data_offsets'], pair[0])):
            start, end = tensor['data_offsets']
            if stream.tell() != 8 + len(raw) + start:
                raise ValueError('noncontiguous scan')
            if tensor['dtype'] not in {'BF16', 'I32', 'I64'}:
                raise ValueError('unqualified dtype for this numerical scanner')
            remaining = end - start
            nonfinite = invalid_scale = count = 0
            while remaining:
                chunk = stream.read(min(32 * 1024 * 1024, remaining))
                if not chunk:
                    raise ValueError('truncated checkpoint')
                digest.update(chunk)
                remaining -= len(chunk)
                if tensor['dtype'] == 'BF16':
                    words = np.frombuffer(chunk, dtype='<u2')
                    finite, positive = predicates(words)
                    count += len(words)
                    nonfinite += int(np.count_nonzero(~finite))
                    if name.endswith('.weight_scale'):
                        invalid_scale += int(np.count_nonzero(~positive))
            records.append({'name': name, 'dtype': tensor['dtype'],
                            'bf16_values': count, 'nonfinite': nonfinite,
                            'nonpositive_or_nonfinite_scales': invalid_scale})
        if stream.read(1) or signature(before) != signature(os.fstat(stream.fileno())):
            raise ValueError('checkpoint changed or contains unscanned bytes')
    if signature(before) != signature(args.checkpoint.lstat()):
        raise ValueError('checkpoint replaced during scan')
    if digest.hexdigest() != expected['sha256'] or before.st_size != expected['size_bytes']:
        raise ValueError('checkpoint does not match trusted local manifest')
    if identities != {str(p.relative_to(ROOT)): file_record(p) for p in sources}:
        raise ValueError('validation sources changed')
    if manifest_identity != file_record(args.manifest):
        raise ValueError('manifest changed')
    failed = any(r['nonfinite'] or r['nonpositive_or_nonfinite_scales'] for r in records)
    receipt = {'schema_version': 1, 'timestamp_utc': datetime.now(timezone.utc).isoformat(),
               'status': 'numerical_scan_failed' if failed else 'numerical_scan_passed',
               'sources': identities, 'manifest': manifest_identity,
               'checkpoint_sha256': digest.hexdigest(), 'numpy_version': np.__version__,
               'predicate_encodings_checked': 65536,
               'bf16_values_checked': sum(r['bf16_values'] for r in records),
               'scale_tensors_checked': sum(r['name'].endswith('.weight_scale') for r in records),
               'tensors': records,
               'limitations': ['No dequantization or architecture correspondence check',
                               'No inference, GPU loading or training execution',
                               'Local manifest does not authenticate publisher bytes']}
    (args.output / 'receipt.json').write_bytes(canonical_json(receipt))
    print(receipt['status'], receipt['bf16_values_checked'], 'BF16 values checked', flush=True)
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
