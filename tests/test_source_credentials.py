import json
import unittest
from zenithsync.source_credentials import scan_text
from scripts.replay_source_teacher import preflight


class SourceCredentialTests(unittest.TestCase):
    def test_authorization_literals_have_locations_but_no_values(self):
        token = 'fakeCredentialValueForTesting12345'
        for prefix in ['"Authorization": "', "'authorization': '", 'Authorization: Bearer ',
                       'Proxy-Authorization: Basic ', 'authorization = ']:
            text = 'Unicode: λ\n' + prefix + token
            findings = scan_text(text)
            self.assertEqual(len(findings), 1)
            self.assertEqual(text[findings[0]['start']:findings[0]['end']], token)
            self.assertEqual(findings[0]['line'], 2)
            self.assertNotIn(token, json.dumps(findings))

    def test_known_token_and_key_indicators(self):
        samples = ['AKIA' + 'A' * 16, 'ghp_' + 'x' * 30,
                   'github_pat_' + 'x' * 30, '-----BEGIN OPENSSH PRIVATE KEY-----']
        for sample in samples:
            with self.subTest(sample_type=sample[:4]):
                self.assertEqual(len(scan_text(sample)), 1)

    def test_short_placeholders_and_unlabelled_text_are_not_flagged(self):
        self.assertEqual(scan_text('Authorization: Bearer EMPTY'), [])
        self.assertEqual(scan_text('a' * 80), [])
        self.assertEqual(scan_text('Authorization: ${TOKEN}'), [])

    def test_type_and_deterministic_order(self):
        with self.assertRaises(TypeError):
            scan_text(None)
        text = 'ghp_' + 'z' * 30 + '\n' + 'AKIA' + 'B' * 16
        rows = scan_text(text)
        self.assertEqual([r['line'] for r in rows], [1, 2])
        self.assertEqual(rows, scan_text(text))

    def test_replay_rejects_prompt_observation_and_action_before_adaptation(self):
        token = 'fakeCredentialValueForTesting12345'
        cases = [
            [{'role': 'user', 'content': 'Authorization: ' + token}],
            [{'role': 'tool', 'content': {'headers': {'Authorization': token}}}],
            [{'tool_calls': [{'function': {'name': 'execute_bash', 'arguments':
                {'command': 'Authorization: ' + token}}}]}],
        ]
        for messages in cases:
            original = json.dumps(messages)
            with self.assertRaisesRegex(ValueError, '^Source credential indicator requires review before replay$') as caught:
                preflight(messages)
            self.assertNotIn(token, str(caught.exception))
            self.assertEqual(json.dumps(messages), original)

    def test_clean_replay_keeps_existing_action(self):
        messages = [{'tool_calls': [{'function': {'name': 'execute_bash',
                     'arguments': {'command': 'python --version'}}}]}]
        self.assertEqual(preflight(messages)[0]['command'], 'python --version')


if __name__ == '__main__':
    unittest.main()
