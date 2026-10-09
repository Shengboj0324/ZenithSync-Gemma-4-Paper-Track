"""Build a reproducible deployment ZIP from an explicit, reviewed file map.

No discovery of credentials, model weights or evaluator data is performed.
The allowlist is a review boundary, not a general-purpose secret detector.
"""

import argparse
from pathlib import Path
import shutil
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record, inventory, load_json, relative_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--file-map', type=Path, required=True)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    map_identity = file_record(args.file_map)
    mapping = load_json(args.file_map)
    if not isinstance(mapping, dict) or not mapping:
        raise ValueError('file map must be a nonempty destination-to-source object')
    records = []
    seen = set()
    sources = {}
    for destination, source in sorted(mapping.items()):
        destination, source = relative_path(destination), relative_path(source)
        if destination.casefold() in seen:
            raise ValueError('case-colliding bundle destination')
        seen.add(destination.casefold())
        path = ROOT / source
        if path.suffix not in {'.py', '.json', '.txt', '.md', '.whl', '.lock', '.yaml', '.yml'}:
            raise ValueError('unsupported deployment source type')
        if any(part.startswith('.') for part in Path(source).parts):
            raise ValueError('hidden source paths are forbidden')
        if any(parent.is_symlink() for parent in [path, *path.parents]):
            raise ValueError('symlink source paths are forbidden')
        record = file_record(path)
        sources[source] = record
        records.append({'path': destination, **record})
    args.directory.mkdir(parents=True, exist_ok=False)
    args.output.mkdir(parents=True, exist_ok=False)
    for destination, source in sorted(mapping.items()):
        target = args.directory / destination
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / source, target)
    manifest = inventory(args.directory, kind='harness', source='curated P1 deployment bundle',
                         revision=map_identity['sha256'])
    if manifest['files'] != records:
        raise ValueError('staged bytes differ from allowlisted sources')
    if sources != {name: file_record(ROOT / name) for name in sources}:
        raise ValueError('source files changed during packaging')
    if map_identity != file_record(args.file_map):
        raise ValueError('file map changed')
    archive_path = args.output / 'deployment.zip'
    with zipfile.ZipFile(archive_path, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for row in records:
            info = zipfile.ZipInfo(row['path'], date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, (args.directory / row['path']).read_bytes())
    with zipfile.ZipFile(archive_path) as archive:
        import hashlib
        if archive.namelist() != [row['path'] for row in records]:
            raise ValueError('archive member set changed')
        for row in records:
            data = archive.read(row['path'])
            if len(data) != row['size_bytes'] or hashlib.sha256(data).hexdigest() != row['sha256']:
                raise ValueError('archive member integrity mismatch')
    (args.output / 'manifest.json').write_bytes(canonical_json(manifest))
    (args.output / 'receipt.json').write_bytes(canonical_json({
        'schema_version': 1, 'status': 'deployment_bundle_built_and_archive_verified',
        'file_map': map_identity, 'builder': file_record(Path(__file__)),
        'file_count': len(records), 'total_bytes': sum(r['size_bytes'] for r in records),
        'archive': file_record(archive_path), 'manifest': file_record(args.output / 'manifest.json'),
        'limitations': ['Not a Kaggle submission archive', 'No GPU or training execution',
                        'File allowlist requires review; not an automatic secret scanner']}))
    print('Verified deployment bundle:', len(records), 'files')


if __name__ == '__main__':
    main()
