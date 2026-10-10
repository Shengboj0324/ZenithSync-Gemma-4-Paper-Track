"""Response identity, provenance linkage, coverage and byte-bound checks."""
import base64
import io
from pathlib import Path
import tarfile
import tempfile
from types import SimpleNamespace
import unittest

from zenithsync.artifacts import canonical_json, file_record
from zenithsync.session_resource_bundle import load_session_resource_bundle, stage_session_resources


class SessionResourceBundleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.url = 'https://example.invalid/page?lang=en'
        self.body = b'<html>captured</html>'
        (self.root/'page.html').write_bytes(self.body)
        self.identity = file_record(self.root/'page.html')
        self.capture = {'responses': [{'requested_url': self.url, 'final_url': self.url,
            'status': 200, 'content_type': 'text/html', 'retrieved_at': '2026-10-10T00:00:00Z',
            'identity': self.identity}]}
        self.receipt = {'schema_version': 1, 'capture_receipt': None,
            'responses': [{'file': 'page.html', 'url': self.url, 'content_type': 'text/html',
                           'identity': self.identity}], 'training_approved': False}
        self.write()

    def write(self):
        (self.root/'capture-receipt.json').write_bytes(canonical_json(self.capture))
        self.receipt['capture_receipt'] = file_record(self.root/'capture-receipt.json')
        (self.root/'receipt.json').write_bytes(canonical_json(self.receipt))

    def load(self, budget=100):
        return load_session_resource_bundle(self.root, max_bytes=budget)

    def test_complete_capture_matches_bytes_and_bindings(self):
        resources, bindings = self.load(len(self.body))
        self.assertEqual(base64.b64decode(resources[self.url]['body']), self.body)
        self.assertEqual(bindings['response_bytes'], len(self.body))
        self.assertEqual(bindings['response_count'], 1)
        self.assertFalse(bindings['training_approved'])

    def test_body_and_capture_drift_rejected(self):
        (self.root/'page.html').write_bytes(b'changed')
        with self.assertRaises(ValueError):
            self.load()
        (self.root/'page.html').write_bytes(self.body)
        (self.root/'capture-receipt.json').write_text('{}')
        with self.assertRaises(ValueError):
            self.load()

    def test_budget_and_invalid_limits_rejected(self):
        for limit in (len(self.body)-1, 0, True, -1, 1.5):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                self.load(limit)

    def test_duplicate_and_missing_capture_rejected(self):
        self.receipt['responses'].append(dict(self.receipt['responses'][0]))
        self.write()
        with self.assertRaises(ValueError):
            self.load()
        self.capture['responses'].append(dict(self.capture['responses'][0]))
        self.write()
        with self.assertRaises(ValueError):
            self.load()

    def test_redirect_and_failed_status_rejected(self):
        for key, value in [('status', 403), ('final_url', 'https://other.invalid/')]:
            original = self.capture['responses'][0][key]
            self.capture['responses'][0][key] = value
            self.write()
            with self.assertRaises(ValueError):
                self.load()
            self.capture['responses'][0][key] = original

    def test_traversal_symlink_and_metadata_mismatch_rejected(self):
        for name in ('../page.html', '/page.html', 'a\\page.html', 'receipt.json'):
            self.receipt['responses'][0]['file'] = name
            self.write()
            with self.assertRaises(ValueError):
                self.load()
        self.receipt['responses'][0]['file'] = 'link.html'
        (self.root/'link.html').symlink_to(self.root/'page.html')
        self.write()
        with self.assertRaises(ValueError):
            self.load()
        self.receipt['responses'][0]['file'] = 'page.html'
        self.receipt['responses'][0]['content_type'] = 'application/json'
        self.write()
        with self.assertRaises(ValueError):
            self.load()

    def test_staging_contains_only_resources_and_support_code(self):
        adapter = Path(__file__).resolve().parents[1]/'zenithsync/session_resource_replay.py'
        uploads = []
        commands = []
        container = SimpleNamespace(put_archive=lambda path, data: uploads.append((path, data)) or True)
        def execute(*args, **kwargs):
            commands.append(args)
            return SimpleNamespace(exit_code=0)
        manager = SimpleNamespace(exec=execute, client=SimpleNamespace(
            containers=SimpleNamespace(get=lambda cid: container)))
        staged = stage_session_resources(manager, 'owned', self.root, adapter, max_bytes=100)
        self.assertEqual(staged['bundle']['response_count'], 1)
        with tarfile.open(fileobj=io.BytesIO(uploads[0][1])) as archive:
            self.assertEqual(set(archive.getnames()),
                             {'resources.json', 'session_resource_replay.py', 'sitecustomize.py'})
            self.assertTrue(all(m.mode == 0o444 for m in archive.getmembers()))
        (self.root/'page.html').write_bytes(b'corrupt')
        with self.assertRaises(ValueError):
            stage_session_resources(manager, 'owned', self.root, adapter, max_bytes=100)
        self.assertEqual(len(uploads), 1)
        self.assertEqual(len(commands), 1)


if __name__ == '__main__':
    unittest.main()
