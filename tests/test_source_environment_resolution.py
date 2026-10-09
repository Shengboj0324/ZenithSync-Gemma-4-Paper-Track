import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.resolve_source_environments import image_identity, parent_identity, verify_digest, dockerhub_tag_identity


def digest(raw):
    return 'sha256:' + hashlib.sha256(raw).hexdigest()


class SourceEnvironmentResolutionTests(unittest.TestCase):
    def test_first_parent_and_missing_parent(self):
        task = {'solution_commit': 'b' * 40, 'base_ref': 'b' * 40 + '^'}
        response = {'sha': 'b' * 40, 'parents': [{'sha': 'a' * 40}, {'sha': 'c' * 40}]}
        self.assertEqual(parent_identity(task, response)['base_commit'], 'a' * 40)
        for altered in [dict(response, sha='d' * 40), dict(response, parents=[])]:
            with self.assertRaises(ValueError):
                parent_identity(task, altered)

    def test_digest_rejects_modified_bytes(self):
        self.assertEqual(verify_digest(b'original', digest(b'original')), digest(b'original'))
        with self.assertRaises(ValueError):
            verify_digest(b'changed', digest(b'original'))

    def test_registry_config_and_layer_identity(self):
        for architecture in ['amd64', 'arm64']:
            with self.subTest(architecture=architecture), tempfile.TemporaryDirectory() as tmp:
                config = json.dumps({'os': 'linux', 'architecture': architecture}).encode()
                manifest = json.dumps({'schemaVersion': 2,
                    'config': {'digest': digest(config), 'size': len(config)},
                    'layers': [{'digest': digest(b'layer'), 'size': 5}]}).encode()
                responses = [(b'{"token":"test-only-secret"}', {}),
                             (manifest, {'Docker-Content-Digest': digest(manifest)}), (config, {})]
                with patch('scripts.resolve_source_environments.fetch', side_effect=responses):
                    if architecture == 'arm64':
                        with self.assertRaises(ValueError):
                            image_identity(None, 'publisher/repo:' + 'b' * 40, Path(tmp))
                    else:
                        result = image_identity(None, 'publisher/repo:' + 'b' * 40, Path(tmp))
                        self.assertEqual(result['compressed_layer_bytes'], 5)
                        self.assertEqual(result['image_digest'], digest(manifest))
                        self.assertNotIn('secret', json.dumps(result))
                        self.assertFalse(result['runtime_verified'])


    def test_explicit_latest_tag_resolves_to_digest(self):
        config = json.dumps({'os': 'linux', 'architecture': 'amd64'}).encode()
        manifest = json.dumps({'schemaVersion': 2,
            'config': {'digest': digest(config), 'size': len(config)}, 'layers': []}).encode()
        responses = [(b'{"token":"fixture-token"}', {}),
                     (manifest, {'Docker-Content-Digest': digest(manifest)}), (config, {})]
        with tempfile.TemporaryDirectory() as tmp, patch(
                'scripts.resolve_source_environments.fetch', side_effect=responses):
            result = dockerhub_tag_identity(None, 'publisher/repo:latest', Path(tmp))
            self.assertEqual(result['pinned_image'], 'publisher/repo@' + digest(manifest))
            self.assertFalse(result['runtime_verified'])

    def test_ambiguous_tags_and_r2e_latest_reject_before_network(self):
        with patch('scripts.resolve_source_environments.fetch') as fetch:
            for tag in ['publisher/repo', 'https://example.com/repo:tag',
                        'publisher/repo:tag;command', 'publisher/repo:']:
                with self.subTest(tag=tag), self.assertRaises(ValueError):
                    dockerhub_tag_identity(None, tag, Path('unused'))
            with self.assertRaises(ValueError):
                image_identity(None, 'publisher/repo:latest', Path('unused'))
            fetch.assert_not_called()


if __name__ == '__main__':
    unittest.main()
