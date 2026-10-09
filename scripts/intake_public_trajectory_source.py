"""Pin public dataset metadata and optionally one bounded, quarantined shard.

Acquisition is not training approval. No examples, patches or tool outputs are
executed, and publisher success labels are not treated as replay verification.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record, inventory, relative_path


def download_file(session, url, destination, row, maximum_bytes):
    size = row['size']
    if type(size) is not int or not 0 <= size <= maximum_bytes:
        raise ValueError('Source file exceeds explicit download limit')
    lfs = row.get('lfs')
    if lfs is not None:
        expected = lfs['sha256']
        if lfs['size'] != size or not re.fullmatch('[0-9a-f]{64}', expected):
            raise ValueError('Invalid LFS identity')
        digest = hashlib.sha256()
    else:
        expected = row['blobId']
        if not re.fullmatch('[0-9a-f]{40}', expected):
            raise ValueError('Invalid Git blob identity')
        digest = hashlib.sha1(b'blob ' + str(size).encode('ascii') + b'\0')
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + '.partial')
    total = 0
    with session.get(url, stream=True, timeout=(15, 60)) as response:
        response.raise_for_status()
        with temporary.open('xb') as stream:
            for chunk in response.iter_content(1024 * 1024):
                total += len(chunk)
                if total > size:
                    raise ValueError('Download exceeds pinned size')
                digest.update(chunk)
                stream.write(chunk)
    if total != size or digest.hexdigest() != expected:
        raise ValueError('Downloaded bytes differ from pinned publisher identity')
    if destination.exists():
        raise ValueError('Refusing to overwrite an existing source file')
    temporary.rename(destination)
    return file_record(destination)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', required=True)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--shard-path')
    parser.add_argument('--max-shard-bytes', type=int, default=0)
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', args.dataset):
        raise ValueError('Expected owner/dataset identifier')
    if args.max_shard_bytes < 0:
        raise ValueError('Negative shard byte limit')
    import requests
    session = requests.Session()
    endpoint = 'https://huggingface.co/api/datasets/' + args.dataset
    with session.get(endpoint, params={'blobs': 'true'}, stream=True, timeout=(15, 30)) as response:
        response.raise_for_status()
        raw = bytearray()
        for chunk in response.iter_content(65536):
            raw.extend(chunk)
            if len(raw) > 2 * 1024**2:
                raise ValueError('Dataset metadata exceeds bounded intake size')
    metadata = json.loads(raw)
    revision = metadata['sha']
    if metadata['id'] != args.dataset or not re.fullmatch('[0-9a-f]{40}', revision):
        raise ValueError('Dataset identity or commit invalid')
    files = {}
    for row in metadata['siblings']:
        name = relative_path(row['rfilename'])
        if name in files:
            raise ValueError('Duplicate publisher file path')
        files[name] = row
    selected = [name for name in ['README.md', 'LICENSE', 'LICENSE.md', 'LICENSE.txt'] if name in files]
    if 'README.md' not in selected:
        raise ValueError('Dataset card required for quarantine intake')
    if args.shard_path:
        relative_path(args.shard_path)
        if args.shard_path not in files or not args.shard_path.endswith('.parquet'):
            raise ValueError('Requested Parquet shard is absent')
        if not files[args.shard_path].get('lfs'):
            raise ValueError('Shard requires publisher SHA-256 identity')
        selected.append(args.shard_path)
    args.directory.mkdir(parents=True, exist_ok=False)
    args.output.mkdir(parents=True, exist_ok=False)
    (args.directory / 'publisher-metadata.json').write_bytes(canonical_json(metadata))
    downloaded = {}
    for name in selected:
        url = f'https://huggingface.co/datasets/{args.dataset}/resolve/{revision}/{quote(name, safe="/")}'
        downloaded[name] = download_file(session, url, args.directory / name, files[name],
            args.max_shard_bytes if name == args.shard_path else 1024**2)
    receipt = {'schema_version': 1, 'status': 'quarantined_not_training_approved',
        'dataset': args.dataset, 'revision': revision, 'retrieved_at': datetime.now(timezone.utc).isoformat(),
        'downloaded': downloaded, 'publisher_file_count': len(files),
        'training_approval': False, 'replay_verified': False,
        'open_gates': ['competition-use terms', 'repository and teacher rights',
                       'reserved-task and repository overlap', 'tool semantics',
                       'privacy/secret filtering', 'native conversion', 'replay and quality'],
        'script': file_record(Path(__file__))}
    (args.output / 'receipt.json').write_bytes(canonical_json(receipt))
    manifest = inventory(args.directory, kind='fixture', source=args.dataset, revision=revision)
    (args.output / 'manifest.json').write_bytes(canonical_json(manifest))
    print({'dataset': args.dataset, 'revision': revision, 'downloaded_files': len(downloaded),
           'downloaded_bytes': sum(row['size_bytes'] for row in downloaded.values()),
           'status': receipt['status']})


if __name__ == '__main__':
    main()
