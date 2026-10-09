"""Project source task identities without exporting reference fixes or tests.

These records describe publisher metadata, not verified runnable environments.
Image tags remain untrusted mutable references until resolved and inspected.
"""

import hashlib
import json
import re


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate metadata JSON key')
        result[key] = value
    return result


def _commit(value):
    if not isinstance(value, str) or re.fullmatch('[0-9a-f]{40}', value) is None:
        raise ValueError('Expected full lowercase Git commit identity')
    return value


def project_r2e_task(row):
    """Return an allowlisted record; never return diffs, test code or prompts."""
    parsed = json.loads(row['parsed_commit_content'], object_pairs_hook=_object)
    execution = json.loads(row['execution_result_content'], object_pairs_hook=_object)
    if not isinstance(parsed, dict) or not isinstance(execution, dict):
        raise ValueError('Expected metadata JSON objects')
    solution = _commit(parsed['new_commit_hash'])
    base = parsed['old_commit_hash']
    # Publisher stores first-parent expressions, not necessarily resolved hashes.
    if base != solution + '^':
        _commit(base)
    if base == solution:
        raise ValueError('Base and solution commits must differ')
    if _commit(row['commit_hash']) != solution or _commit(execution['new_commit_hash']) != solution:
        raise ValueError('Conflicting solution commit identities')
    repo = row['repo_name']
    if not isinstance(repo, str) or re.fullmatch('[A-Za-z0-9_.-]+', repo) is None:
        raise ValueError('Invalid source repository name')
    if execution['repo_name'] != repo:
        raise ValueError('Conflicting repository names')
    image = row['docker_image']
    if not isinstance(image, str) or re.fullmatch(r'[a-z0-9_./-]+:' + solution, image) is None:
        raise ValueError('Image must carry the declared solution commit tag')
    problem = row['problem_statement']
    if not isinstance(problem, str) or not problem.strip():
        raise ValueError('Missing problem statement')
    return {
        'source_repo_name': repo,
        'base_ref': base,
        'base_commit': base if len(base) == 40 else None,
        'solution_commit': solution,
        'source_image_tag': image,
        'problem_statement_sha256': hashlib.sha256(problem.encode('utf-8')).hexdigest(),
        'environment_verified': False,
        'training_approved': False,
    }


def match_trajectory(task, *, repo, instance_id):
    """Match exact owner/repo plus solution suffix; basename is not ownership proof."""
    if not isinstance(repo, str) or re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo) is None:
        raise ValueError('Expected owner/repository')
    expected = repo.replace('/', '__') + '-' + task['solution_commit']
    return repo.split('/')[1] == task['source_repo_name'] and instance_id == expected
