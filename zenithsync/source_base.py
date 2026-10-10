"""Normalize an owned disposable checkout; retain history for later sanitization."""
from pathlib import Path
import re

from .source_snapshot import git, tracked_snapshot


def normalize_base(repo, *, expected_head, target_base):
    """Require the observed head and clean files before a non-forced checkout.

    This is not an agent-safe snapshot. On any failure discard the disposable
    container; untracked files and solution history deliberately remain unaudited.
    """
    repo = Path(repo).resolve(strict=True)
    for value in (expected_head, target_base):
        if not isinstance(value, str) or re.fullmatch('[0-9a-f]{40}', value) is None:
            raise ValueError('Full commit identities required')
    metadata = repo/'.git'
    if metadata.is_symlink() or not metadata.is_dir():
        raise ValueError('Ordinary Git directory required')
    if git(repo, 'rev-parse', '--absolute-git-dir').stdout.strip().decode() != str(metadata):
        raise ValueError('Unexpected Git metadata location')
    if git(repo, 'rev-parse', 'HEAD').stdout.strip().decode() != expected_head:
        raise ValueError('Unexpected initial checkout')
    if git(repo, 'status', '--porcelain', '--untracked-files=no').stdout.strip():
        raise ValueError('Tracked changes before normalization')
    before = tracked_snapshot(repo)
    tree = git(repo, 'rev-parse', target_base+'^{tree}').stdout.strip().decode()
    # Local hooks must not run during the controlled checkout. No force/reset
    # or clean is used: an obstructing untracked path causes checkout to fail.
    git(repo, '-c', 'core.hooksPath=/dev/null', 'checkout', '--detach', target_base)
    if (git(repo, 'rev-parse', 'HEAD').stdout.strip().decode() != target_base
            or git(repo, 'rev-parse', 'HEAD^{tree}').stdout.strip().decode() != tree
            or git(repo, 'status', '--porcelain', '--untracked-files=no').stdout.strip()):
        raise ValueError('Base checkout verification failed')
    after = tracked_snapshot(repo)
    return {'previous_head': expected_head, 'base_commit': target_base,
            'source_tree': tree, 'before': before, 'after': after,
            'agent_workspace_approved': False,
            'scope': 'Exact tracked base files only; history and untracked/oracle files remain'}
