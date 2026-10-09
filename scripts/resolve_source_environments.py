"""Resolve a fixed per-repository sample without pulling or executing images.

Anonymous read-only requests establish registry digests and GitHub-reported
parent identities. They do not verify image working trees or runtime isolation.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record

MEDIA = ', '.join([
    'application/vnd.oci.image.index.v1+json',
    'application/vnd.docker.distribution.manifest.list.v2+json',
    'application/vnd.oci.image.manifest.v1+json',
    'application/vnd.docker.distribution.manifest.v2+json',
])


def fetch(session, url, *, headers=None, params=None):
    with session.get(url, headers=headers, params=params, stream=True, timeout=(15, 45)) as response:
        response.raise_for_status()
        body = bytearray()
        for chunk in response.iter_content(65536):
            body.extend(chunk)
            if len(body) > 2 * 1024**2:
                raise ValueError('Metadata response exceeds 2 MiB')
        return bytes(body), response.headers


def verify_digest(body, expected):
    actual = 'sha256:' + hashlib.sha256(body).hexdigest()
    if not isinstance(expected, str) or re.fullmatch(r'sha256:[0-9a-f]{64}', expected) is None:
        raise ValueError('Invalid expected SHA-256 digest')
    if actual != expected:
        raise ValueError('Registry metadata digest mismatch')
    return actual


def parent_identity(task, response):
    solution = task['solution_commit']
    if response['sha'] != solution or task['base_ref'] != solution + '^':
        raise ValueError('Commit identity or supported parent expression mismatch')
    parents = response['parents']
    if not parents:
        raise ValueError('Solution commit has no parent')
    parent = parents[0]['sha']
    if not isinstance(parent, str) or re.fullmatch('[0-9a-f]{40}', parent) is None or parent == solution:
        raise ValueError('Invalid first-parent identity')
    return {'base_commit': parent, 'parent_count': len(parents),
            'scope': 'GitHub API first-parent assertion; local Git object verification pending'}


def image_identity(session, tag, directory):
    if re.fullmatch(r'[a-z0-9_-]+/[a-z0-9_.-]+:[0-9a-f]{40}', tag) is None:
        raise ValueError('Expected Docker Hub repository and full commit tag')
    repository, reference = tag.split(':')
    raw, _ = fetch(session, 'https://auth.docker.io/token', params={
        'service': 'registry.docker.io', 'scope': f'repository:{repository}:pull'})
    token = json.loads(raw)['token']
    headers = {'Authorization': 'Bearer ' + token, 'Accept': MEDIA}
    base = f'https://registry-1.docker.io/v2/{repository}'
    raw, returned = fetch(session, base + '/manifests/' + reference, headers=headers)
    tag_digest = verify_digest(raw, returned.get('Docker-Content-Digest'))
    (directory / 'tag-manifest.json').write_bytes(raw)
    manifest = json.loads(raw)
    digest = tag_digest
    if 'manifests' in manifest:
        matches = [item for item in manifest['manifests']
                   if item.get('platform', {}).get('os') == 'linux'
                   and item.get('platform', {}).get('architecture') == 'amd64'
                   and item.get('platform', {}).get('variant') in (None, '')]
        if len(matches) != 1:
            raise ValueError('Expected one unambiguous Linux amd64 image')
        descriptor = matches[0]
        raw, _ = fetch(session, base + '/manifests/' + descriptor['digest'], headers=headers)
        digest = verify_digest(raw, descriptor['digest'])
        if len(raw) != descriptor['size']:
            raise ValueError('Image manifest size mismatch')
        manifest = json.loads(raw)
    if manifest.get('schemaVersion') != 2 or 'layers' not in manifest:
        raise ValueError('Unsupported image manifest')
    (directory / 'image-manifest.json').write_bytes(raw)
    config = manifest['config']
    raw, _ = fetch(session, base + '/blobs/' + config['digest'], headers=headers)
    verify_digest(raw, config['digest'])
    if len(raw) != config['size']:
        raise ValueError('Image config size mismatch')
    (directory / 'image-config.json').write_bytes(raw)
    obj = json.loads(raw)
    if obj.get('os') != 'linux' or obj.get('architecture') != 'amd64':
        raise ValueError('Image config platform is not Linux amd64')
    layers = manifest['layers']
    for layer in layers:
        if type(layer['size']) is not int or layer['size'] < 0:
            raise ValueError('Invalid layer size')
        if re.fullmatch(r'sha256:[0-9a-f]{64}', layer['digest']) is None:
            raise ValueError('Invalid layer digest')
    return {'tag_digest': tag_digest, 'image_digest': digest,
            'pinned_image': repository + '@' + digest, 'platform': 'linux/amd64',
            'compressed_layer_bytes': sum(layer['size'] for layer in layers),
            'layer_count': len(layers), 'image_config': file_record(directory / 'image-config.json'),
            'layers_downloaded': False, 'runtime_verified': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--joined', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    identity = file_record(args.joined)
    selected = {}
    for line in args.joined.read_text().splitlines():
        if line.strip():
            task = json.loads(line)
            selected.setdefault(task['repo'], task)
    if not selected or len(selected) > 16:
        raise ValueError('Expected 1–16 source repositories')
    args.output.mkdir(parents=True, exist_ok=False)
    import requests
    session = requests.Session()
    results = []
    for index, (repo, task) in enumerate(sorted(selected.items())):
        directory = args.output / f'{index:02d}'
        directory.mkdir()
        result = {'repo': repo, 'instance_id': task['instance_id'], 'training_approved': False}
        for stage in ('git', 'registry'):
            try:
                if stage == 'git':
                    if re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo) is None:
                        raise ValueError('Invalid repository identity')
                    if re.fullmatch('[0-9a-f]{40}', task['solution_commit']) is None:
                        raise ValueError('Invalid solution commit')
                    url = f'https://api.github.com/repos/{repo}/git/commits/{task["solution_commit"]}'
                    raw, _ = fetch(session, url, headers={'Accept': 'application/vnd.github+json'})
                    # Persist identity projection only, excluding messages/signatures.
                    result[stage] = {**parent_identity(task, json.loads(raw)), 'url': url,
                                     'response_sha256': hashlib.sha256(raw).hexdigest()}
                else:
                    result[stage] = image_identity(session, task['source_image_tag'], directory)
            except (requests.RequestException, ValueError, KeyError, TypeError) as error:
                # Never persist token-bearing request objects or headers.
                status = getattr(getattr(error, 'response', None), 'status_code', None)
                result[stage] = {'error_type': type(error).__name__, 'http_status': status}
        results.append(result)
        (directory / 'result.json').write_bytes(canonical_json(result))
        print({'repo': repo, 'git_ok': 'error_type' not in result['git'],
               'registry_ok': 'error_type' not in result['registry']}, flush=True)
    if file_record(args.joined) != identity:
        raise ValueError('Input changed during resolution')
    (args.output / 'report.json').write_bytes(canonical_json({
        'schema_version': 1, 'retrieved_at': datetime.now(timezone.utc).isoformat(),
        'selection': 'First trajectory per repository in input order; no replacement on failure',
        'input': identity, 'script': file_record(Path(__file__)), 'results': results,
        'environment_verified': False, 'training_approved': False,
    }))


if __name__ == '__main__':
    main()
