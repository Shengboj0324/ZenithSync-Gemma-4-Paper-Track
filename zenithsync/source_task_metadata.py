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


def select_source_metadata(rows, *, reserved_repositories, source_dataset):
    """Select one declared source; reject contradictory exclusion metadata.

    This is an exact-name exclusion gate, not fork or semantic clearance.
    Rows remain quarantined and no trajectory bodies are accessed here.
    """
    if not isinstance(source_dataset, str) or not source_dataset.strip():
        raise ValueError('Explicit source dataset required')
    reserved = {name.casefold() for name in reserved_repositories}
    selected = []
    seen = set()
    excluded_reserved = 0
    unsupported_source = 0
    for row in rows:
        for field in ('repo', 'instance_id', 'trajectory_id', 'dataset'):
            if not isinstance(row.get(field), str) or not row[field].strip():
                raise ValueError('Invalid census identity field')
        if row['trajectory_id'] in seen:
            raise ValueError('Duplicate census trajectory ID')
        seen.add(row['trajectory_id'])
        overlaps = row['repo'].casefold() in reserved
        flag = row.get('reserved_repository_exact_match')
        if type(flag) is not bool or flag != overlaps:
            raise ValueError('Reserved-repository exclusion flag mismatch')
        if overlaps:
            excluded_reserved += 1
        elif row['dataset'] != source_dataset:
            unsupported_source += 1
        else:
            selected.append(row)
    return selected, {'input_rows': len(seen), 'selected_source_rows': len(selected),
                      'excluded_reserved_rows': excluded_reserved,
                      'other_source_rows_not_joined': unsupported_source}


def select_r2e_metadata(rows, *, reserved_repositories):
    """Compatibility entrypoint for the R2E task join."""
    selected, counts = select_source_metadata(rows, reserved_repositories=reserved_repositories,
                                             source_dataset='R2E-Gym/R2E-Gym-Subset')
    counts['selected_r2e_rows'] = counts.pop('selected_source_rows')
    return selected, counts


def project_swebench_task_identity(row):
    """Allowlist SWE-rebench task metadata; never export issue bodies or patches."""
    repo = row['repo']
    if not isinstance(repo, str) or re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo) is None:
        raise ValueError('Expected owner/repository')
    if any(part in ('.', '..') for part in repo.split('/')):
        raise ValueError('Invalid repository segment')
    instance = row['instance_id']
    if not isinstance(instance, str) or re.fullmatch(re.escape(repo.replace('/', '__')) + r'-[0-9]+', instance) is None:
        raise ValueError('Instance ID does not match repository and PR number')
    images = []
    for name in ('docker_image', 'image_name'):
        image = row[name]
        if image is not None and (not isinstance(image, str)
                or re.fullmatch(r'[a-z0-9_./:-]+', image) is None):
            raise ValueError('Invalid declared image reference')
        if image is not None:
            images.append(image)
    if len(set(images)) > 1:
        raise ValueError('Conflicting declared images')
    license_name = row['license_name']
    if license_name is not None and not isinstance(license_name, str):
        raise ValueError('Invalid publisher license declaration type')
    if license_name is not None and not license_name.strip():
        license_name = None
    return {'repo': repo, 'instance_id': instance, 'base_commit': _commit(row['base_commit']),
            'environment_setup_commit': _commit(row['environment_setup_commit']),
            'source_image_reference': images[0] if images else None,
            'publisher_license_declaration': license_name,
            'environment_verified': False, 'training_approved': False}
