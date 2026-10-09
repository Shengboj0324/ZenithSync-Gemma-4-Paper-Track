"""Check every quantized text projection against the pinned Gemma4 config."""

import argparse
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from zenithsync.artifacts import canonical_json, file_record, load_json, verify
from zenithsync.model_intake import inspect_safetensors
from zenithsync.quantized_layout import expected_projections, validate_projection


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model-dir', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    sources = ['scripts/verify_quantized_layout.py', 'zenithsync/quantized_layout.py',
               'zenithsync/model_intake.py', 'zenithsync/artifacts.py', 'zenithsync/contracts.py']
    identities = {name: file_record(ROOT / name) for name in sources}
    manifest_identity = file_record(args.manifest)
    manifest = load_json(args.manifest)
    verify(args.model_dir, manifest)
    config = load_json(args.model_dir / 'config.json')
    expected = expected_projections(config)
    checkpoint = args.model_dir / 'model.safetensors'
    structure = inspect_safetensors(checkpoint)
    with checkpoint.open('rb') as stream:
        prefix = stream.read(8)
        size = struct.unpack('<Q', prefix)[0]
        if size != structure['header_size_bytes']:
            raise ValueError('header size changed')
        header = json.loads(stream.read(size))
        for suffix in ('.weight_shape', '.weight_packed', '.weight_scale'):
            actual = {name.removesuffix(suffix) for name in header if name.endswith(suffix)}
            if actual != set(expected):
                raise ValueError(f'missing or unexpected projection tensors: {suffix}')
        for name, shape in expected.items():
            descriptor = header[name + '.weight_shape']
            if descriptor['dtype'] != 'I64' or descriptor['shape'] != [2]:
                raise ValueError(f'invalid original shape descriptor: {name}')
            stream.seek(8 + size + descriptor['data_offsets'][0])
            original = struct.unpack('<qq', stream.read(16))
            validate_projection(name, original, header[name + '.weight_packed'],
                                header[name + '.weight_scale'], shape)
    # Rehash the complete package after reads; inputs must be quiescent throughout.
    verify(args.model_dir, manifest)
    if identities != {name: file_record(ROOT / name) for name in sources}:
        raise ValueError('validation sources changed')
    if manifest_identity != file_record(args.manifest):
        raise ValueError('manifest changed')
    receipt = {'schema_version': 1, 'status': 'quantized_text_layout_passed',
               'sources': identities, 'manifest': manifest_identity,
               'quantized_projections_checked': len(expected),
               'projections': expected,
               'limitations': ['Owned quiescent input directory required',
                               'No unquantized vision/embedding/norm architecture check',
                               'No packed-value dequantization or GPU execution']}
    (args.output / 'receipt.json').write_bytes(canonical_json(receipt))
    print('Quantized text layout passed:', len(expected), 'projections')


if __name__ == '__main__':
    main()
