"""Transport replay must preserve bytes and reject unrecorded requests."""

import hashlib
import importlib.util
import ssl
import unittest
import urllib.request

from zenithsync.offline_resources import install_resource_replay


@unittest.skipUnless(importlib.util.find_spec('requests'), 'requests is required')
class ResourceReplayTests(unittest.TestCase):
    def setUp(self):
        self.url = 'https://example.invalid/schema.yaml'
        self.body = b'version: 4.2.1\n'
        self.digest = hashlib.sha256(self.body).hexdigest()
        self.events = []

    def install(self):
        restore = install_resource_replay(
            {self.url: (self.body, self.digest)}, self.events)
        self.addCleanup(restore)

    def test_exact_body_and_metadata_for_both_clients(self):
        import requests
        self.install()
        with urllib.request.urlopen(self.url) as response:
            self.assertEqual(response.read(), self.body)
            self.assertEqual(response.getcode(), 200)
            self.assertEqual(response.geturl(), self.url)
        response = requests.get(self.url, timeout=1)
        self.assertEqual(response.content, self.body)
        self.assertEqual(response.text, self.body.decode())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(self.events), 2)
        self.assertTrue(all(event['allowed'] for event in self.events))

    def test_missing_url_and_query_variants_fail_closed(self):
        import requests
        self.install()
        for fetch in (requests.get, urllib.request.urlopen):
            with self.assertRaises(RuntimeError):
                fetch(self.url + '?different=1')
        self.assertEqual(len(self.events), 2)
        self.assertFalse(any(event['allowed'] for event in self.events))

    def test_options_and_post_are_not_silently_ignored(self):
        import requests
        self.install()
        with self.assertRaises(ValueError):
            requests.get(self.url, params={'a': 1})
        with self.assertRaises(ValueError):
            urllib.request.urlopen(urllib.request.Request(self.url, data=b'payload'))

    def test_invalid_hash_does_not_install_partial_adapter(self):
        import requests
        original_get, original_open = requests.get, urllib.request.urlopen
        with self.assertRaises(ValueError):
            install_resource_replay({self.url: (self.body, '0' * 64)}, [])
        self.assertIs(requests.get, original_get)
        self.assertIs(urllib.request.urlopen, original_open)

    def test_restore(self):
        import requests
        original_get, original_open = requests.get, urllib.request.urlopen
        restore = install_resource_replay({self.url: (self.body, self.digest)}, [])
        restore()
        self.assertIs(requests.get, original_get)
        self.assertIs(urllib.request.urlopen, original_open)

    def test_tls_context_bypass_is_explicit(self):
        self.install()
        with urllib.request.urlopen(self.url, context=ssl.create_default_context()) as response:
            self.assertEqual(response.read(), self.body)
        self.assertTrue(self.events[-1]['tls_context_bypassed'])
        with self.assertRaises(ValueError):
            urllib.request.urlopen(self.url, context='invalid')
