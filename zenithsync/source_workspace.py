"""Prepare a qualified source snapshot for native /workspace tool semantics."""

import re
import shlex


def prepare_source_workspace(manager, container_id, *, snapshot_commit, source_tree,
                             installer_leftover=True, source_root='/testbed',
                             preserve_workspace_cache=False):
    """Move one qualified source root into /workspace, then tag its baseline.

    The caller owns this disposable container and must destroy it on failure.
    Only the qualified installer leftover is removed. Unknown untracked files,
    mismatched source identities, and unexpected workspace files reject.
    An explicitly allowed .cache directory moves outside the source tree.
    Source-root and /testbed aliases preserve existing dependency paths.
    """
    if any(not isinstance(value, str) or re.fullmatch('[0-9a-f]{40}', value) is None
           for value in (snapshot_commit, source_tree)):
        raise ValueError('Expected exact snapshot commit and source tree identities')
    if (not isinstance(source_root, str) or re.fullmatch(r'/[A-Za-z0-9_-]+', source_root) is None
            or source_root == '/workspace' or type(preserve_workspace_cache) is not bool
            or type(installer_leftover) is not bool):
        raise ValueError('Explicit simple source root and cache policy required')
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
        'test "$(git -C /testbed ls-files --others --exclude-standard)" = '
        + shlex.quote('install.sh' if installer_leftover else ''),
        'rmdir /workspace',
        'mv /testbed /workspace',
        'ln -s /workspace /testbed',
        'cd /workspace',
        'rm /workspace/install.sh' if installer_leftover else 'true',
        'git tag _swegemma_baseline',
        'test -z "$(git status --porcelain --untracked-files=all)"',
        'test "$(git rev-parse HEAD^{tree})" = ' + shlex.quote(source_tree),
    ]
    if source_root != '/testbed':
        commands = [command.replace('/testbed', source_root) for command in commands]
        commands[:0] = ['test ! -e /testbed', 'test ! -L /testbed']
        commands.append('ln -s /workspace /testbed')
    if preserve_workspace_cache:
        index = commands.index('rmdir /workspace')
        commands[index:index] = [
            'test -d /workspace/.cache', 'test ! -L /workspace/.cache',
            'test "$(find /workspace -mindepth 1 -maxdepth 1 -printf \'%f\\n\')" = .cache',
            'test ! -e /opt/zenithsync/runtime-cache', 'test ! -L /opt/zenithsync/runtime-cache',
            'mv /workspace/.cache /opt/zenithsync/runtime-cache',
        ]
    result = manager.exec(container_id, ' && '.join(commands), timeout=30)
    if result.exit_code != 0:
        raise ValueError('Source workspace preparation rejected: ' + result.stderr)
    return {'snapshot_commit': snapshot_commit, 'source_tree': source_tree,
            'workspace': '/workspace', 'dependency_alias': source_root,
            'testbed_alias': '/testbed',
            'preserved_workspace_cache': '/opt/zenithsync/runtime-cache' if preserve_workspace_cache else None,
            'removed_untracked_files': ['install.sh'] if installer_leftover else [],
            'tracked_source_preserved': True}
