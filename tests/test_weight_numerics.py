"""Numerical scanner acceptance/rejection checks on explicitly synthetic files."""

import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(importlib.util.find_spec('numpy'), 'numerical scanner requires NumPy')
class WeightNumericsTests(unittest.TestCase):
    def scan(self, values, corrupt_hash=False):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            header = json.dumps({'test.weight_scale': {
                'dtype': 'BF16', 'shape': [len(values)],
                'data_offsets': [0, 2 * len(values)]}}).encode()
            payload = struct.pack('<Q', len(header)) + header + struct.pack('<' + 'H' * len(values), *values)
            checkpoint = root / 'model.safetensors'
            checkpoint.write_bytes(payload)
            manifest = root / 'manifest.json'
            manifest.write_text(json.dumps({'files': [{'path': checkpoint.name,
                'size_bytes': len(payload), 'sha256': '0' * 64 if corrupt_hash else hashlib.sha256(payload).hexdigest()}]}))
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/verify_weight_numerics.py'),
                '--checkpoint', str(checkpoint), '--manifest', str(manifest),
                '--output', str(root / 'output')], capture_output=True, text=True, timeout=30)
            receipt = root / 'output/receipt.json'
            return result, json.loads(receipt.read_text()) if receipt.exists() else None

    def test_finite_positive_including_smallest_subnormal(self):
        result, receipt = self.scan([1, 0x3F80, 0x7F7F])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(receipt['bf16_values_checked'], 3)
        self.assertEqual(receipt['predicate_encodings_checked'], 65536)

    def test_nan_and_infinities_fail(self):
        result, receipt = self.scan([0x7F80, 0xFF80, 0x7FC1])
        self.assertEqual(result.returncode, 1)
        self.assertEqual(receipt['tensors'][0]['nonfinite'], 3)

    def test_signed_zero_and_negative_scale_fail(self):
        result, receipt = self.scan([0, 0x8000, 0xBF80])
        self.assertEqual(result.returncode, 1)
        self.assertEqual(receipt['tensors'][0]['nonfinite'], 0)
        self.assertEqual(receipt['tensors'][0]['nonpositive_or_nonfinite_scales'], 3)

    def test_manifest_mismatch_cannot_emit_passing_receipt(self):
        result, receipt = self.scan([0x3F80], corrupt_hash=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIsNone(receipt)


if __name__ == '__main__':
    unittest.main()
