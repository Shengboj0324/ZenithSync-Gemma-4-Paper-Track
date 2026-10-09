import hashlib
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from zenithsync.artifacts import file_record


class ArtifactFileRecordTests(unittest.TestCase):
    def test_stable_bytes_have_expected_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'fixture.bin'
            path.write_bytes(b'content')
            self.assertEqual(file_record(path), {'size_bytes': 7,
                'sha256': hashlib.sha256(b'content').hexdigest()})

    def test_metadata_only_change_remains_rejected_with_diagnostic(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'fixture.bin'
            path.write_bytes(b'content')
            before = path.stat()
            fields = ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns')
            after = SimpleNamespace(**{name: getattr(before, name) for name in fields})
            after.st_ctime_ns += 1
            with patch('zenithsync.artifacts.os.fstat', side_effect=[before, after]):
                with self.assertRaisesRegex(ValueError, 'st_ctime_ns'):
                    file_record(path)


if __name__ == '__main__':
    unittest.main()
