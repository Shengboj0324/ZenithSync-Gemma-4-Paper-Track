"""Synthetic wheelhouse fixtures exercise provenance and metadata boundaries."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


class ServingWheelsTests(unittest.TestCase):
    def verify(self, *, vendored=False, duplicate=False, wrong_hash=False,
               wrong_metadata=False, extra=False):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wheels = root / 'wheels'
            wheels.mkdir()
            path = wheels / 'fixture-1.0-py3-none-any.whl'
            with zipfile.ZipFile(path, 'w') as wheel:
                name = 'other' if wrong_metadata else 'fixture'
                wheel.writestr('fixture-1.0.dist-info/METADATA', f'Name: {name}\nVersion: 1.0\n')
                if vendored:
                    wheel.writestr('fixture/_vendor/vendor-2.dist-info/METADATA', 'Name: vendor\nVersion: 2\n')
                if duplicate:
                    wheel.writestr('other-1.0.dist-info/METADATA', 'Name: other\nVersion: 1.0\n')
            sha = hashlib.sha256(path.read_bytes()).hexdigest()
            report = root / 'report.json'
            report.write_text(json.dumps({'install': [{'metadata': {'name': 'fixture', 'version': '1.0'},
                'download_info': {'url': path.as_uri(), 'archive_info': {
                    'hashes': {'sha256': '0' * 64 if wrong_hash else sha}}}}]}))
            if extra:
                (wheels / 'unexpected.txt').write_text('synthetic unaccounted file')
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/verify_serving_wheels.py'),
                '--directory', str(wheels), '--report', str(report), '--output', str(root / 'output')],
                capture_output=True, text=True, timeout=30)
            return result, (root / 'output/receipt.json').exists()

    def test_vendored_metadata_is_not_top_level_identity(self):
        result, receipt = self.verify(vendored=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(receipt)

    def test_invalid_bundles_never_emit_acceptance_receipt(self):
        for flag in ['duplicate', 'wrong_hash', 'wrong_metadata', 'extra']:
            with self.subTest(flag=flag):
                result, receipt = self.verify(**{flag: True})
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(receipt)


if __name__ == '__main__':
    unittest.main()
