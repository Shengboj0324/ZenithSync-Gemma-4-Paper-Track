"""Adversarial contract checks for the explicit Session response adapter."""
import hashlib
import importlib.util
import unittest
from unittest.mock import patch

from zenithsync.session_resource_replay import install_session_resource_replay


@unittest.skipUnless(importlib.util.find_spec('requests'), 'requests is required')
class SessionResourceReplayTests(unittest.TestCase):
    def setUp(self):
        self.url = 'https://example.invalid/page?lang=en'
        self.body = b'<html>captured</html>\x00\xff'
        self.record = {'body': self.body, 'sha256': hashlib.sha256(self.body).hexdigest(),
                       'content_type': 'text/html; charset=utf-8'}
        self.events = []

    def install(self):
        self.addCleanup(install_session_resource_replay({self.url: self.record}, self.events))

    def test_body_metadata_and_iteration_without_network(self):
        import requests
        self.install()
        with patch('socket.socket', side_effect=AssertionError('Network forbidden')):
            session = requests.Session()
            session.trust_env = False
            with session:
                response = session.get(self.url, timeout=(2, 3))
        self.assertEqual(response.content, self.body)
        self.assertEqual(b''.join(response.iter_content(3)), self.body)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], self.record['content_type'])
        self.assertEqual(response.url, self.url)
        self.assertTrue(self.events[-1]['allowed'])
        self.assertFalse(self.events[-1]['live_transport_executed'])

    def test_unknown_url_method_body_and_headers_rejected(self):
        import requests
        self.install()
        cases = [('GET', self.url + '&extra=1', {}), ('POST', self.url, {}),
                 ('GET', self.url, {'data': b'x'})]
        cases.extend(('GET', self.url, {'headers': {key: 'x'}}) for key in
                     ['Authorization', 'Cookie', 'Range', 'If-None-Match'])
        for method, url, options in cases:
            with self.subTest(method=method, options=options):
                request = requests.Request(method, url, **options).prepare()
                with self.assertRaises(ValueError):
                    requests.Session().send(request)
        self.assertEqual(len(self.events), len(cases))
        self.assertFalse(any(e['allowed'] for e in self.events))

    def test_unsupported_transport_and_hooks_rejected(self):
        import requests
        self.install()
        request = requests.Request('GET', self.url).prepare()
        for options in ({'stream': True}, {'verify': False}, {'cert': 'file'},
                        {'proxies': {'https': 'http://proxy.invalid'}}, {'unknown': 1},
                        {'timeout': float('nan')}, {'timeout': 0}, {'timeout': True},
                        {'timeout': (1,)}, {'timeout': (1, -2)}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                requests.Session().send(request, **options)
        request.register_hook('response', lambda response: response)
        with self.assertRaises(ValueError):
            requests.Session().send(request)

    def test_invalid_record_never_partially_installs(self):
        import requests
        original = requests.sessions.Session.send
        for record in ({**self.record, 'sha256': '0' * 64},
                       {**self.record, 'content_type': 'text/html\r\nInjected: yes'},
                       {**self.record, 'status': 200}):
            with self.assertRaises(ValueError):
                install_session_resource_replay({self.url: self.record,
                                                self.url + '&second=1': record}, [])
            self.assertIs(requests.sessions.Session.send, original)

    def test_rejects_nonpublic_or_ambiguous_url(self):
        for url in ('http://example.invalid', 'https://user:pass@example.invalid',
                    'https://example.invalid/#fragment', 'https://example.invalid/a b'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                install_session_resource_replay({url: self.record}, [])

    def test_validated_snapshot_cannot_be_changed_by_caller(self):
        import requests
        self.install()
        self.record['body'] = b'replaced'
        response = requests.Session().send(requests.Request('GET', self.url).prepare())
        self.assertEqual(response.content, self.body)

    def test_restore(self):
        import requests
        original = requests.sessions.Session.send
        restore = install_session_resource_replay({self.url: self.record}, [])
        restore()
        self.assertIs(requests.sessions.Session.send, original)


if __name__ == '__main__':
    unittest.main()
