"""Plan explicit scratch cleanup only when tracked repair bytes already agree.

This module never deletes files, stages changes, executes a source command, or
approves a training example. The caller must expose any subsequent cleanup as
an adapter-authored native action and reverify the submitted patch afterward.
"""

from pathlib import Path, PurePosixPath
import re
import subprocess
import inspect
import shlex

from .artifacts import file_record


def scratch_cleanup_command(*, python, scratch_paths, repository='/workspace'):
    """Render an explicit standalone action using the same inspected planner.

    The generated command needs only Python's standard library and Git. It
    reads the source-exported patch and native baseline at execution time, and
    never carries a reference solution or depends on an injected support module.
    Calling this renderer performs no filesystem mutation.
    """
    if (not isinstance(python, str) or not python.startswith('/')
            or any(part in ('', '.', '..') for part in python.split('/')[1:])):
        raise ValueError('Explicit absolute interpreter required')
    if not isinstance(repository, str) or not repository.startswith('/'):
        raise ValueError('Absolute repository path required')
    if (not isinstance(scratch_paths, list) or not scratch_paths
            or any(not isinstance(path, str) for path in scratch_paths)):
        raise ValueError('Explicit scratch path list required')
    code = (
        'from pathlib import Path, PurePosixPath\n'
        'import hashlib, json, os, re, stat, subprocess\n'
        + inspect.getsource(file_record) + '\n'
        + inspect.getsource(plan_scratch_cleanup) + '\n'
        + f'root = Path({repository!r})\n'
        + "base = subprocess.check_output(['git', 'rev-parse', '_swegemma_baseline^{commit}'], cwd=root, text=True).strip()\n"
        + "intended = (root / 'patch.txt').read_bytes()\n"
        + f'plan = plan_scratch_cleanup(root, baseline=base, intended_patch=intended, scratch_paths={scratch_paths!r})\n'
        + "if any(file_record(root / name) != identity for name, identity in plan['scratch_files'].items()):\n"
        + "    raise ValueError('Scratch file changed before cleanup')\n"
        + "for name in plan['scratch_files']:\n    (root / name).unlink()\n"
        + "actual = subprocess.check_output(['git', '-c', 'core.fsmonitor=false', '-c', 'core.hooksPath=/dev/null', 'diff', '--binary', '--no-ext-diff', '--no-textconv', '--src-prefix=a/', '--dst-prefix=b/', base, '--'], cwd=root)\n"
        + "if actual != intended:\n    raise ValueError('Cleanup changed intended patch')\n"
        + "print(json.dumps({'cleanup_performed': True, 'scratch_paths': sorted(plan['scratch_files']), 'patch_sha256': hashlib.sha256(actual).hexdigest()}))\n")
    return shlex.join([python, '-B', '-c', code])


def plan_scratch_cleanup(repository, *, baseline, intended_patch, scratch_paths):
    """Check the bounded tracked-repair/untracked-scratch submission profile.

    Exact diff-byte equality is intentional. New source files, staged changes,
    unknown scratch files, ignored files selected for deletion, and symlink
    cleanup are outside this profile and reject rather than being guessed.
    """
    repository = Path(repository).resolve(strict=True)
    if not isinstance(baseline, str) or re.fullmatch('[0-9a-f]{40}', baseline) is None:
        raise ValueError('Full baseline commit required')
    if not isinstance(intended_patch, bytes) or not intended_patch or len(intended_patch) > 2 * 1024**2:
        raise ValueError('Bounded nonempty intended patch bytes required')
    if not isinstance(scratch_paths, list) or not scratch_paths:
        raise ValueError('Explicit nonempty scratch path list required')
    checked = []
    for name in scratch_paths:
        if not isinstance(name, str) or not name or '\x00' in name:
            raise ValueError('Invalid scratch path')
        path = PurePosixPath(name)
        if (path.is_absolute() or str(path) != name
                or any(part in ('.', '..', '.git') for part in path.parts)):
            raise ValueError('Unsafe scratch path')
        checked.append(name)
    if len(set(checked)) != len(checked):
        raise ValueError('Duplicate scratch path')

    def git(*arguments):
        result = subprocess.run(['git', '-c', 'core.fsmonitor=false', '-c',
            'core.hooksPath=/dev/null', '-C', str(repository), *arguments],
            capture_output=True, timeout=30, check=False)
        if result.returncode:
            raise ValueError('Git submission inspection failed')
        return result.stdout

    if Path(git('rev-parse', '--show-toplevel').decode().strip()).resolve() != repository:
        raise ValueError('Expected repository root')
    if git('rev-parse', 'HEAD').decode().strip() != baseline:
        raise ValueError('Repository baseline mismatch')
    if git('diff', '--cached', '--binary', '--no-ext-diff', '--no-textconv', baseline, '--'):
        raise ValueError('Staged changes outside reconciliation profile')
    tracked_patch = git('diff', '--binary', '--no-ext-diff', '--no-textconv',
                        '--src-prefix=a/', '--dst-prefix=b/', baseline, '--')
    if tracked_patch != intended_patch:
        raise ValueError('Tracked repair differs from intended patch')
    untracked = git('ls-files', '--others', '--exclude-standard', '-z').split(b'\x00')
    names = {name.decode('utf-8') for name in untracked if name}
    if names != set(checked):
        raise ValueError('Untracked files differ from reviewed scratch inventory')
    files = {}
    for name in sorted(checked):
        path = repository
        for part in PurePosixPath(name).parts:
            path = path / part
            if path.is_symlink():
                raise ValueError('Symlink scratch cleanup is unsupported')
        if not path.is_file():
            raise ValueError('Scratch file outside repository or not regular')
        try:
            path.resolve().relative_to(repository)
        except ValueError:
            raise ValueError('Scratch file outside repository or not regular')
        files[name] = file_record(path)
    return {'baseline': baseline, 'scratch_files': files,
            'tracked_patch_equals_intended': True, 'cleanup_performed': False,
            'training_approved': False,
            'scope': 'Point-in-time plan only. Recheck identities before explicit native cleanup '
                     'and require post-cleanup native submission byte equality.'}
