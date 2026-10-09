import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock

from scripts.intake_public_trajectory_source import download_file


class PublicSourceDownloadTests(unittest.TestCase):
    def session(self, chunks):
        session = MagicMock()
        response = session.get.return_value.__enter__.return_value
        response.iter_content.return_value = chunks
        return session

    def test_git_blob_identity(self):
        content = b'public card\n'
        row = {'size': len(content), 'blobId': hashlib.sha1(b'blob 12\0' + content).hexdigest()}
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'README.md'
            result = download_file(self.session([content[:4], content[4:]]), 'https://example.test', target, row, 100)
            self.assertEqual(result['sha256'], hashlib.sha256(content).hexdigest())
            self.assertEqual(target.read_bytes(), content)

    def test_lfs_identity(self):
        content = b'abc'
        row = {'size': 3, 'lfs': {'size': 3, 'sha256': hashlib.sha256(content).hexdigest()}}
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'data.parquet'
            download_file(self.session([content]), 'https://example.test', target, row, 3)
            self.assertEqual(target.read_bytes(), content)

    def test_size_budget_rejected_before_network(self):
        session = self.session([])
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, 'limit'):
                download_file(session, 'https://example.test', Path(directory) / 'file', {'size': 4}, 3)
        session.get.assert_not_called()

    def test_corrupt_short_and_oversized_downloads_not_promoted(self):
        row = {'size': 3, 'lfs': {'size': 3, 'sha256': hashlib.sha256(b'abc').hexdigest()}}
        for content in [b'abd', b'ab', b'abcd']:
            with tempfile.TemporaryDirectory() as directory:
                target = Path(directory) / 'file'
                with self.assertRaises(ValueError):
                    download_file(self.session([content]), 'https://example.test', target, row, 3)
                self.assertFalse(target.exists())
