"""Source snapshots for context recovery; checksums are integrity, not authenticity."""
import argparse
import hashlib
import json
from pathlib import Path
import stat
import tempfile

MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_EXCERPT_BYTES = 8192


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(',', ':')).encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_regular(path, limit):
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
        raise ValueError('Expected a bounded regular file, without symlinks')
    with path.open('rb') as stream:
        data = stream.read(limit + 1)
    after = path.lstat()
    signature = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    if signature(before) != signature(after) or len(data) != before.st_size:
        raise ValueError('File changed while reading')
    return data


def source(root, relative):
    path = Path(relative)
    if path.is_absolute() or not path.parts or any(p in ('.', '..', '.git') for p in path.parts):
        raise ValueError('Expected a repository-relative source path outside .git')
    target = root / path
    if any(p.is_symlink() for p in [target, *target.parents] if p != root and root in p.parents):
        raise ValueError('Symlink paths are not supported')
    if not target.resolve().is_relative_to(root):
        raise ValueError('Source escapes workspace')
    return target


def snapshot(root, relative, start, end, temp_root=None):
    if type(start) is not int or type(end) is not int or not 1 <= start <= end or end - start >= 100:
        raise ValueError('Choose 1 to 100 lines using positive inclusive line numbers')
    data = read_regular(source(root, relative), MAX_FILE_BYTES)
    lines = data.decode('utf-8').splitlines(keepends=True)
    if end > len(lines):
        raise ValueError('Requested line range is outside the file')
    excerpt = ''.join(lines[start - 1:end])
    if len(excerpt.encode('utf-8')) > MAX_EXCERPT_BYTES:
        raise ValueError('Excerpt exceeds byte cap; choose fewer lines')
    record = {'schema_version': 1, 'workspace': str(root), 'path': relative,
              'file_sha256': digest(data), 'start_line': start, 'end_line': end,
              'excerpt': excerpt}
    payload = encoded(record)
    directory = Path(tempfile.mkdtemp(prefix='zenithsync-observation-', dir=temp_root))
    handle = directory / (digest(payload) + '.json')
    with handle.open('xb') as stream:
        stream.write(payload)
    handle.chmod(0o600)
    return {'status': 'recorded', 'handle': str(handle), 'record': record}


def recall(root, handle):
    path = Path(handle)
    if not path.is_absolute():
        raise ValueError('Expected an absolute observation handle')
    payload = read_regular(path, 64 * 1024)
    if path.name != digest(payload) + '.json':
        raise ValueError('Observation checksum mismatch')
    record = json.loads(payload)
    if not isinstance(record, dict) or set(record) != {
        'schema_version', 'workspace', 'path', 'file_sha256', 'start_line', 'end_line', 'excerpt'
    } or record['schema_version'] != 1 or record['workspace'] != str(root):
        raise ValueError('Observation schema or workspace mismatch')
    data = read_regular(source(root, record['path']), MAX_FILE_BYTES)
    current_hash = digest(data)
    if current_hash != record['file_sha256']:
        return {'status': 'stale', 'path': record['path'], 'recorded_sha256': record['file_sha256'],
                'current_sha256': current_hash, 'action': 'Read current source and create a new snapshot'}
    start, end = record['start_line'], record['end_line']
    if type(start) is not int or type(end) is not int or not 1 <= start <= end or end - start >= 100:
        raise ValueError('Invalid stored line range')
    lines = data.decode('utf-8').splitlines(keepends=True)
    if end > len(lines) or ''.join(lines[start - 1:end]) != record['excerpt']:
        raise ValueError('Stored excerpt does not match source')
    return {'status': 'current_source_match', 'record': record,
            'scope': 'Source bytes match; this does not validate any interpretation or test outcome'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, default=Path('/workspace'))
    sub = parser.add_subparsers(dest='operation', required=True)
    put = sub.add_parser('snapshot')
    put.add_argument('--path', required=True)
    put.add_argument('--start', type=int, required=True)
    put.add_argument('--end', type=int, required=True)
    get = sub.add_parser('recall')
    get.add_argument('--handle', required=True)
    args = parser.parse_args()
    root = args.workspace.resolve(strict=True)
    if not root.is_dir():
        raise ValueError('Workspace must be a directory')
    result = snapshot(root, args.path, args.start, args.end) if args.operation == 'snapshot' else recall(root, args.handle)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
