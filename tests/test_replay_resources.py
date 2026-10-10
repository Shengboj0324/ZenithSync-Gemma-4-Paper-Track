import io
from pathlib import Path
import tarfile
import tempfile
from types import SimpleNamespace
import unittest

from zenithsync.artifacts import canonical_json, file_record
from zenithsync.replay_resources import stage_resources


class ReplayResourceTests(unittest.TestCase):
    def test_stages_only_allowlisted_resource_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'schema.yaml').write_bytes(b'version: 1\n')
            (root/'adapter.py').write_text('# transport adapter\n')
            (root/'receipt.json').write_bytes(canonical_json({'files': {'schema.yaml': {
                'identity':file_record(root/'schema.yaml'), 'original_url':'https://example.invalid/schema'}}}))
            uploads = []
            container = SimpleNamespace(put_archive=lambda path, body: uploads.append((path, body)) or True)
            manager = SimpleNamespace(exec=lambda *a, **k: SimpleNamespace(exit_code=0),
                client=SimpleNamespace(containers=SimpleNamespace(get=lambda cid: container)))
            result = stage_resources(manager, 'owned', root, root/'adapter.py')
            self.assertEqual(result['response_count'], 1)
            with tarfile.open(fileobj=io.BytesIO(uploads[0][1])) as archive:
                self.assertEqual(set(archive.getnames()),
                                 {'resources.json','offline_resources.py','sitecustomize.py'})
                self.assertTrue(all(member.mode == 0o444 for member in archive.getmembers()))
            (root/'schema.yaml').write_bytes(b'changed')
            with self.assertRaises(ValueError):
                stage_resources(manager, 'owned', root, root/'adapter.py')
            self.assertEqual(len(uploads), 1)
