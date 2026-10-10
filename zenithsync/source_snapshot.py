"""Create a fresh Git history while preserving an exact base tree.

Run only in a disposable build container or an explicitly owned test fixture.
This removes known oracle paths; it does not certify arbitrary image contents.
"""

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess


def is_relative_to(path, parent):
    """Path-component containment compatible with Python 3.7 task images."""
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def git(repo, *args, data=None, check=True):
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    env.update({'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull,
                'GIT_AUTHOR_NAME': 'ZenithSync snapshot', 'GIT_AUTHOR_EMAIL': 'snapshot@invalid',
                'GIT_COMMITTER_NAME': 'ZenithSync snapshot', 'GIT_COMMITTER_EMAIL': 'snapshot@invalid',
                'GIT_AUTHOR_DATE': '2000-01-01T00:00:00+00:00',
                'GIT_COMMITTER_DATE': '2000-01-01T00:00:00+00:00'})
    return subprocess.run(['git', '-c', 'safe.directory=' + str(repo), *args],
                          cwd=repo, input=data, capture_output=True, check=check,
                          env=env, timeout=60)


def tracked_snapshot(repo):
    result = []
    for entry in git(repo, 'ls-files', '--stage', '-z').stdout.split(b'\0'):
        if not entry:
            continue
        info, name = entry.split(b'\t', 1)
        mode, blob, stage = info.decode('ascii').split()
        relative = name.decode('utf-8')
        pure = PurePosixPath(relative)
        if pure.is_absolute() or any(part in ('.', '..', '.git') for part in pure.parts):
            raise ValueError('Unsafe tracked path')
        if stage != '0' or mode not in ('100644', '100755', '120000'):
            raise ValueError('Unmerged entries and submodules are unsupported')
        path = repo / relative
        if path.is_symlink():
            resolved = path.resolve(strict=True)
            if mode != '120000' or not is_relative_to(resolved, repo) or '.git' in resolved.relative_to(repo).parts:
                raise ValueError('Tracked symlink escapes source tree or targets Git metadata')
            content = os.readlink(path).encode('utf-8')
        else:
            if mode == '120000' or not path.is_file() or not is_relative_to(path.resolve(), repo):
                raise ValueError('Tracked file type or path mismatch')
            executable = bool(path.stat().st_mode & 0o111)
            if executable != (mode == '100755'):
                raise ValueError('Tracked executable mode mismatch')
            content = path.read_bytes()
        # The snapshot contract uses SHA-1 Git object identities (40 hex digits).
        # Hash the unfiltered Git blob encoding directly, avoiding one process
        # per file. Symlink content is its link text, as in Git's index.
        if re.fullmatch('[0-9a-f]{40}', blob) is None:
            raise ValueError('Expected SHA-1 Git blob identity')
        header = b'blob ' + str(len(content)).encode('ascii') + b'\0'
        digest = hashlib.sha1(header)
        digest.update(content)
        actual = digest.hexdigest()
        if actual != blob:
            raise ValueError('Working file differs from tracked Git blob')
        result.append({'path': relative, 'mode': mode, 'blob': blob,
                       'sha256': hashlib.sha256(content).hexdigest(), 'size_bytes': len(content)})
    if not result:
        raise ValueError('Empty source snapshot')
    return result


def sanitize(repo, *, expected_base, solution, oracle_paths, solution_relation='first_parent'):
    """Sanitize an owned disposable filesystem; discard it on any failure.

    Preflight checks precede deletion. Post-mutation integrity failures cannot
    roll back removed history and must never be treated as successful output.
    """
    repo = Path(repo).resolve(strict=True)
    if any(re.fullmatch('[0-9a-f]{40}', value) is None for value in (expected_base, solution)):
        raise ValueError('Expected full Git commit identities')
    if solution_relation not in ('first_parent', 'ancestor', 'already_absent') or expected_base == solution:
        raise ValueError('Invalid solution relationship or identical base/solution')
    metadata = repo / '.git'
    if metadata.is_symlink() or not metadata.is_dir():
        raise ValueError('Expected ordinary local .git directory')
    if git(repo, 'rev-parse', '--absolute-git-dir').stdout.strip().decode() != str(metadata):
        raise ValueError('Unexpected Git metadata location')
    if git(repo, 'rev-parse', 'HEAD').stdout.strip().decode() != expected_base:
        raise ValueError('Wrong source base commit')
    if solution_relation == 'first_parent':
        if git(repo, 'rev-parse', solution + '^').stdout.strip().decode() != expected_base:
            raise ValueError('Solution first parent differs from declared base')
    elif solution_relation == 'already_absent':
        absent = git(repo, 'rev-parse', '--verify', '--quiet', solution + '^{commit}', check=False)
        if absent.returncode != 1 or absent.stdout or absent.stderr:
            raise ValueError('Solution must be verifiably absent before sanitization')
    elif git(repo, 'merge-base', '--is-ancestor', expected_base, solution, check=False).returncode != 0:
        raise ValueError('Declared base is not an ancestor of solution')
    tree = git(repo, 'rev-parse', 'HEAD^{tree}').stdout.strip().decode()
    if git(repo, 'diff', '--quiet', 'HEAD', '--', check=False).returncode != 0:
        raise ValueError('Source tree has tracked modifications')
    before = tracked_snapshot(repo)
    paths = [Path(path).absolute() for path in oracle_paths]
    tracked = [repo / row['path'] for row in before]
    tracked += [path.resolve(strict=True) for path in tracked if path.is_symlink()]
    for path in paths:
        if '..' in path.parts:
            raise ValueError('Parent traversal in oracle path')
        if path == repo or path == metadata or is_relative_to(repo, path):
            raise ValueError('Oracle removal would remove repository or metadata')
        if any(file == path or is_relative_to(file, path) for file in tracked):
            raise ValueError('Oracle path overlaps preserved tracked source')
        if path.parent.resolve() != path.parent:
            raise ValueError('Oracle path has symlinked parent')
    removed = []
    for path in paths:
        if path.is_symlink() or path.is_file():
            path.unlink()
            removed.append(str(path))
        elif path.exists():
            if not path.is_dir():
                raise ValueError('Unsupported oracle path type')
            shutil.rmtree(path)
            removed.append(str(path))
    shutil.rmtree(metadata)
    git(repo, '-c', 'init.templateDir=', 'init', '--initial-branch=main')
    index = bytearray()
    for row in before:
        path = repo / row['path']
        content = os.readlink(path).encode('utf-8') if row['mode'] == '120000' else path.read_bytes()
        blob = git(repo, 'hash-object', '-w', '--stdin', data=content).stdout.strip().decode()
        if blob != row['blob']:
            raise ValueError('Source changed while rebuilding Git objects')
        index.extend(f"{row['mode']} {blob}\t{row['path']}".encode('utf-8') + b'\0')
    git(repo, 'update-index', '-z', '--index-info', data=bytes(index))
    rebuilt_tree = git(repo, 'write-tree').stdout.strip().decode()
    if rebuilt_tree != tree:
        raise ValueError('Rebuilt tree differs from original base tree')
    commit = git(repo, 'commit-tree', rebuilt_tree, data=b'Sanitized agent baseline\n').stdout.strip().decode()
    git(repo, 'update-ref', 'refs/heads/main', commit)
    after = tracked_snapshot(repo)
    if before != after:
        raise ValueError('Source bytes or modes changed during sanitization')
    if git(repo, 'cat-file', '-e', solution + '^{commit}', check=False).returncode == 0:
        raise ValueError('Solution commit remains accessible')
    if git(repo, 'rev-list', '--all', '--count').stdout.strip() != b'1':
        raise ValueError('Snapshot must have exactly one reachable commit')
    if any(path.exists() or path.is_symlink() for path in paths):
        raise ValueError('Known oracle path remains accessible')
    return {'schema_version': 1, 'base_commit': expected_base, 'source_tree': tree,
            'snapshot_commit': commit, 'solution_relation': solution_relation,
            'solution_ancestry_verified': solution_relation != 'already_absent', 'tracked_files': len(before),
            'tracked_bytes': sum(row['size_bytes'] for row in before),
            'tracked_manifest_sha256': hashlib.sha256(json.dumps(before, sort_keys=True).encode()).hexdigest(),
            'exact_tree_preserved': True, 'known_oracles_removed': removed,
            'solution_commit_accessible': False, 'training_approved': False,
            'scope': 'Exact tracked tree and declared oracle paths only; broader image audit pending'}
