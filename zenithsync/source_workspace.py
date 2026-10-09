"""Prepare a qualified source snapshot for native /workspace tool semantics."""

import re
import shlex


def prepare_source_workspace(manager, container_id, *, snapshot_commit, source_tree):
    """Move one fresh /testbed snapshot into /workspace, then tag its baseline.

    The caller owns this disposable container and must destroy it on failure.
    Only the qualified installer leftover is removed. Unknown untracked files,
    mismatched source identities, and nonempty workspaces cause rejection.
    The /testbed compatibility alias preserves existing dependency paths.
    """
    if any(not isinstance(value, str) or re.fullmatch('[0-9a-f]{40}', value) is None
           for value in (snapshot_commit, source_tree)):
        raise ValueError('Expected exact snapshot commit and source tree identities')
    commands = [
        'test -d /testbed/.git',
        'test ! -L /testbed',
        'test ! -L /testbed/.git',
        'test ! -L /workspace',
        'test "$(git -C /testbed rev-parse HEAD)" = ' + shlex.quote(snapshot_commit),
        'test "$(git -C /testbed rev-parse HEAD^{tree})" = ' + shlex.quote(source_tree),
        'test "$(git -C /testbed rev-list --all --count)" = 1',
        'test -z "$(git -C /testbed remote)"',
        'git -C /testbed diff --quiet HEAD --',
        'test "$(git -C /testbed ls-files --others --exclude-standard)" = install.sh',
        'rmdir /workspace',
        'mv /testbed /workspace',
        'ln -s /workspace /testbed',
        'cd /workspace',
        'rm /workspace/install.sh',
        'git tag _swegemma_baseline',
        'test -z "$(git status --porcelain --untracked-files=all)"',
        'test "$(git rev-parse HEAD^{tree})" = ' + shlex.quote(source_tree),
    ]
    result = manager.exec(container_id, ' && '.join(commands), timeout=30)
    if result.exit_code != 0:
        raise ValueError('Source workspace preparation rejected: ' + result.stderr)
    return {'snapshot_commit': snapshot_commit, 'source_tree': source_tree,
            'workspace': '/workspace', 'dependency_alias': '/testbed',
            'removed_untracked_files': ['install.sh'], 'tracked_source_preserved': True}
