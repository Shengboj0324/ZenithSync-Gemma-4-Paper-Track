"""Verify the exact complete wheel set selected by a retained pip report.

No wheel code is executed. Produces a manifest for the existing R2 transport.
"""

import argparse
from email.parser import BytesParser
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from zenithsync.artifacts import canonical_json, file_record, inventory


def normalized(name):
    return re.sub('[-_.]+', '-', name).lower()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    source_paths = [Path(__file__).resolve(), ROOT / 'zenithsync/artifacts.py',
                    ROOT / 'zenithsync/contracts.py']
    sources = {str(p.relative_to(ROOT)): file_record(p) for p in source_paths}
    report_identity = file_record(args.report)
    report = json.loads(args.report.read_bytes())
    expected = {}
    distributions = set()
    for package in report['install']:
        metadata = package['metadata']
        name = normalized(metadata['name'])
        download = package['download_info']
        filename = unquote(urlsplit(download['url']).path.rsplit('/', 1)[-1])
        if (not filename.endswith('.whl') or '/' in filename or '\\' in filename
                or filename in expected or name in distributions):
            raise ValueError('invalid or duplicate wheel identity')
        sha = download['archive_info']['hashes']['sha256']
        if not re.fullmatch('[0-9a-f]{64}', sha):
            raise ValueError('invalid expected SHA-256')
        expected[filename] = (name, metadata['version'], sha)
        distributions.add(name)
    if not expected:
        raise ValueError('empty resolver report')
    manifest = inventory(args.directory, kind='harness',
                         source='exact serving runtime wheels from pip resolver report',
                         revision=report_identity['sha256'])
    if {row['path'] for row in manifest['files']} != set(expected):
        raise ValueError('wheelhouse is incomplete or contains unaccounted files')
    for row in manifest['files']:
        name, version, sha = expected[row['path']]
        if row['sha256'] != sha:
            raise ValueError(f'wheel hash mismatch: {row["path"]}')
        with zipfile.ZipFile(args.directory / row['path']) as wheel:
            members = [m for m in wheel.infolist()
                       if m.filename.count('/') == 1 and m.filename.endswith('.dist-info/METADATA')]
            if len(members) != 1 or members[0].file_size > 16 * 1024 * 1024:
                raise ValueError(f'missing, ambiguous or oversized wheel metadata: {row["path"]}')
            metadata = BytesParser().parsebytes(wheel.read(members[0]))
            if (len(metadata.get_all('Name', [])) != 1 or len(metadata.get_all('Version', [])) != 1
                    or normalized(metadata['Name']) != name or metadata['Version'] != version):
                raise ValueError('wheel metadata differs from resolver report')
    if report_identity != file_record(args.report):
        raise ValueError('resolver report changed during verification')
    if sources != {str(p.relative_to(ROOT)): file_record(p) for p in source_paths}:
        raise ValueError('verifier sources changed')
    (args.output / 'manifest.json').write_bytes(canonical_json(manifest))
    receipt = {'schema_version': 1, 'status': 'serving_wheelhouse_verified',
               'report': report_identity, 'sources': sources, 'wheel_count': len(expected),
               'total_bytes': sum(row['size_bytes'] for row in manifest['files']),
               'manifest': file_record(args.output / 'manifest.json'),
               'limitations': ['Requires quiescent owned input directory',
                               'No installation, import or GPU compatibility claim']}
    (args.output / 'receipt.json').write_bytes(canonical_json(receipt))
    print('Verified', len(expected), 'exact serving wheels')


if __name__ == '__main__':
    main()
