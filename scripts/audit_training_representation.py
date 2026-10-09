"""Account for checkpoint-derived dense storage and hypothetical LoRA states.

Static accounting only: excludes activations, workspaces, allocator overhead,
retained quantization metadata, and transient decompression buffers. It cannot
prove that a training workload fits or that an adapter loader works.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record, load_json
from zenithsync.model_intake import inspect_safetensors
from zenithsync.quantized_layout import expected_projections, validate_projection


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    config = load_json(args.model / 'config.json')
    manifest = load_json(ROOT / 'evidence/p1/model-intake-001/model-manifest.json')
    config_identity = next(row for row in manifest['files'] if row['path'] == 'config.json')
    if file_record(args.model / 'config.json') != {k: config_identity[k] for k in ['sha256', 'size_bytes']}:
        raise ValueError('Configuration differs from qualified model')
    weights = args.model / 'model.safetensors'
    inspection = inspect_safetensors(weights)
    prior = load_json(ROOT / 'evidence/p1/storage-001/receipt.json')['inspection']
    if inspection != prior:
        raise ValueError('Checkpoint structure differs from qualified intake')
    with weights.open('rb') as stream:
        length = int.from_bytes(stream.read(8), 'little')
        raw = stream.read(length)
        if hashlib.sha256(raw).hexdigest() != inspection['header_sha256']:
            raise ValueError('Header changed during audit')
        tensors = json.loads(raw)
        tensors.pop('__metadata__', None)
        projections = expected_projections(config)
        excluded = set()
        for name, shape in projections.items():
            descriptor = tensors[name + '.weight_shape']
            if descriptor['dtype'] != 'I64' or descriptor['shape'] != [2]:
                raise ValueError('Invalid stored original shape')
            stream.seek(8 + length + descriptor['data_offsets'][0])
            original = stream.read(16)
            stored_shape = [int.from_bytes(original[i:i+8], 'little', signed=True) for i in [0, 8]]
            validate_projection(name, stored_shape, tensors[name + '.weight_packed'],
                                tensors[name + '.weight_scale'], shape)
            excluded.update(name + suffix for suffix in ['.weight_shape', '.weight_packed', '.weight_scale'])
    remaining = {name: row for name, row in tensors.items() if name not in excluded}
    if any(row['dtype'] != 'BF16' for row in remaining.values()):
        raise ValueError('Unexpected unquantized dtype')
    dense_elements = sum(rows * cols for rows, cols in projections.values())
    other_elements = sum(math.prod(row['shape']) for row in remaining.values())
    groups = {'all_text_projections': projections,
              'attention_only': {n: s for n, s in projections.items() if '.self_attn.' in n}}
    adapters = {}
    for label, selected in groups.items():
        adapters[label] = {}
        for rank in [8, 16, 32, 64]:
            count = sum(rank * (rows + cols) for rows, cols in selected.values())
            adapters[label][str(rank)] = {
                'parameters': count,
                'fp32_parameters_gradients_adam_moments_bytes': count * 16,
                'bf16_parameters_gradients_fp32_moments_bytes': count * 12,
            }
    sources = {}
    for wheel, member in [
        ('transformers-5.13.1-py3-none-any.whl', 'transformers/quantizers/quantizer_compressed_tensors.py'),
        ('compressed_tensors-0.15.0.1-py3-none-any.whl', 'compressed_tensors/compressors/model_compressors/model_compressor.py'),
    ]:
        path = ROOT / 'artifacts/official/p1-serving-wheels' / wheel
        with ZipFile(path) as archive:
            source = archive.read(member)
        sources[member] = {'wheel': file_record(path), 'source_sha256': hashlib.sha256(source).hexdigest()}
    if inspect_safetensors(weights) != inspection:
        raise ValueError('Checkpoint structure changed during audit')
    result = {'schema_version': 1, 'status': 'static_accounting_only',
              'header_sha256': inspection['header_sha256'], 'source_identities': sources,
              'quantized_projection_count': len(projections),
              'dense_projection_elements': dense_elements, 'other_bf16_elements': other_elements,
              'dense_bf16_weight_bytes': 2 * (dense_elements + other_elements),
              'adapters': adapters,
              'assumptions': ['LoRA A is rank by input; B is output by rank; no biases or DoRA',
                              'All listed targets exist; actual PEFT attachment is untested',
                              'Adam memory excludes optional master copies and implementation temporaries'],
              'limitations': ['No training or GPU execution', 'No peak memory or fit guarantee',
                              'Header and original shapes checked; full weight payload not rehashed in this audit'],
              'verifier': file_record(Path(__file__))}
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'receipt.json').write_bytes(canonical_json(result))
    print('Dense BF16 weights:', result['dense_bf16_weight_bytes'], 'bytes')


if __name__ == '__main__':
    main()
