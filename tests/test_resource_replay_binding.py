import copy
import hashlib
from pathlib import Path
import unittest

from tests import test_session_resource_bundle as bundle_tests
from zenithsync.artifacts import file_record
from zenithsync.resource_replay_binding import verify_resource_replay_binding
from zenithsync.session_resource_bundle import DIRECTORY, STARTUP


class ResourceReplayBindingTests(unittest.TestCase):
    write = bundle_tests.SessionResourceBundleTests.write

    def setUp(self):
        bundle_tests.SessionResourceBundleTests.setUp(self)
        binding = bundle_tests.SessionResourceBundleTests.load(self)[1]
        root = Path(__file__).resolve().parents[1]
        sources = {name: file_record(root/name) for name in (
            'zenithsync/session_resource_bundle.py', 'zenithsync/session_resource_replay.py')}
        self.profile = {'session_resources': {'receipt': file_record(self.root/'receipt.json'),
                                              'max_bytes': 100}}
        self.attempt = {'injected_support_modules': True, 'sources': sources,
            'environment': {'PYTHONPATH': DIRECTORY},
            'session_resources': {'bundle': binding,
                'adapter': sources['zenithsync/session_resource_replay.py'], 'directory': DIRECTORY,
                'startup_sha256': hashlib.sha256(STARTUP.encode()).hexdigest()}}

    def test_exact_binding_is_explicitly_not_admission(self):
        proof, files = verify_resource_replay_binding(self.attempt, self.profile, self.root)
        self.assertFalse(proof['training_approved'])
        self.assertEqual(proof['staging'], self.attempt['session_resources'])
        self.assertIn(str(self.root/'page.html'), files)
        self.assertTrue(any(name.endswith('/resource_replay_binding.py') for name in files))

    def test_missing_bundle_cannot_bypass_injection_gate(self):
        with self.assertRaises(ValueError):
            verify_resource_replay_binding(self.attempt, self.profile)
        self.assertEqual(verify_resource_replay_binding({'injected_support_modules': False}, {}),
                         (None, {}))

    def test_configuration_and_producer_drift_rejected(self):
        for field in ('injection', 'startup', 'directory', 'environment', 'adapter', 'producer', 'bundle'):
            attempt = copy.deepcopy(self.attempt)
            if field == 'injection':
                attempt['injected_support_modules'] = False
            elif field == 'environment':
                attempt['environment']['PYTHONPATH'] = '/unreviewed'
            elif field == 'producer':
                attempt['sources']['zenithsync/session_resource_bundle.py']['sha256'] = '0'*64
            elif field == 'bundle':
                attempt['session_resources']['bundle']['response_bytes'] += 1
            elif field == 'adapter':
                attempt['session_resources']['adapter'] = {}
            else:
                key = 'startup_sha256' if field == 'startup' else 'directory'
                attempt['session_resources'][key] = 'incorrect'
            with self.subTest(field=field), self.assertRaises(ValueError):
                verify_resource_replay_binding(attempt, self.profile, self.root)

    def test_profile_and_body_drift_rejected(self):
        profile = copy.deepcopy(self.profile)
        profile['session_resources']['receipt']['sha256'] = '0'*64
        with self.assertRaises(ValueError):
            verify_resource_replay_binding(self.attempt, profile, self.root)
        (self.root/'page.html').write_bytes(b'changed')
        with self.assertRaises(ValueError):
            verify_resource_replay_binding(self.attempt, self.profile, self.root)


if __name__ == '__main__':
    unittest.main()
