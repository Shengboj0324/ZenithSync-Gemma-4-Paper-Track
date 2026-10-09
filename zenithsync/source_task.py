"""Agent-visible source task projection, separate from evaluator metadata."""

import hashlib
import re

from zenithsync.task_intake import AGENT_FIELDS


def project_source_issue(*, problem_statement, repo, source_instance_id,
                         source_revision, snapshot_commit):
    if not isinstance(problem_statement, str) or not problem_statement.strip():
        raise ValueError('Nonempty source issue required')
    if len(problem_statement.encode('utf-8')) > 1024 * 1024:
        raise ValueError('Issue exceeds bounded projection size')
    if re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo) is None:
        raise ValueError('Invalid repository identity')
    for commit in (source_revision, snapshot_commit):
        if not isinstance(commit, str) or re.fullmatch('[0-9a-f]{40}', commit) is None:
            raise ValueError('Full source and snapshot identities required')
    if not isinstance(source_instance_id, str) or not source_instance_id:
        raise ValueError('Source task identity required')
    text = problem_statement.strip()
    if '[ISSUE]' in text or '[/ISSUE]' in text:
        if (text.count('[ISSUE]') != 1 or text.count('[/ISSUE]') != 1
                or not text.startswith('[ISSUE]') or not text.endswith('[/ISSUE]')):
            raise ValueError('Ambiguous issue wrapper; do not discard surrounding content')
        text = text[len('[ISSUE]'):-len('[/ISSUE]')].strip()
    if not text:
        raise ValueError('Empty issue after wrapper removal')
    # The source ID includes a solution commit. Keep that mapping evaluator-only.
    opaque = hashlib.sha256((source_revision + '\0' + source_instance_id).encode()).hexdigest()
    task = {'instance_id': 'r2e_' + opaque, 'repo': repo,
            'base_commit': snapshot_commit, 'problem_statement': text}
    if set(task) != set(AGENT_FIELDS):
        raise AssertionError('Agent task allowlist changed')
    return task
