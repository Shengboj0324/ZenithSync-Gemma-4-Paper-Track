"""Strict paired-control checks retaining full pytest parameter identities.

Publisher whitespace-truncated names are matched as groups. Every member must
agree with the expected transition; last-write-wins collapse is never used.
"""


def call_outcomes(document):
    collected = document['collected']
    if (not isinstance(collected, list) or not collected
            or any(not isinstance(node, str) or not node.strip() for node in collected)
            or len(set(collected)) != len(collected)):
        raise ValueError('Collected identities must be nonempty and unique')
    if document['collection_errors']:
        raise ValueError('Collection errors invalidate controls')
    phases = {}
    for report in document['reports']:
        node, phase, outcome = report['nodeid'], report['when'], report['outcome']
        if node not in collected or phase not in ('setup', 'call', 'teardown'):
            raise ValueError('Unexpected test report')
        key = (node, phase)
        if key in phases:
            raise ValueError('Duplicate test phase')
        if outcome not in ('passed', 'failed'):
            raise ValueError('Skipped or unknown outcomes invalidate controls')
        phases[key] = outcome
    result = {}
    for node in collected:
        if any((node, phase) not in phases for phase in ('setup', 'call', 'teardown')):
            raise ValueError('Missing test phase')
        if phases[node, 'setup'] != 'passed' or phases[node, 'teardown'] != 'passed':
            raise ValueError('Setup or teardown failure invalidates controls')
        result[node] = phases[node, 'call']
    expected_exit = int('failed' in result.values())
    if type(document['exitstatus']) is not int or document['exitstatus'] != expected_exit:
        raise ValueError('Exit status contradicts outcomes')
    return result


def validate_supplemental_passes(nodes):
    """Require individually declared full test identities, never inferred coverage."""
    if (not isinstance(nodes, list)
            or any(not isinstance(node, str) or not node or node.split() != [node]
                   for node in nodes)
            or len(set(nodes)) != len(nodes)):
        raise ValueError('Unique explicit supplemental test identities required')
    return nodes


def compare_controls(base, reference, expectations, *, supplemental_pass_to_pass=None):
    """Require exact coverage and each publisher group's complete transition."""
    transitions = {'FAIL_TO_PASS': ('failed', 'passed'),
                   'PASS_TO_PASS': ('passed', 'passed'),
                   'FAIL_TO_FAIL': ('failed', 'failed'),
                   'PASS_TO_FAIL': ('passed', 'failed')}
    if set(expectations) != set(transitions):
        raise ValueError('Unexpected expectation categories')
    expected = {}
    for category, keys in expectations.items():
        if not isinstance(keys, list):
            raise ValueError('Expectation category must be a list')
        for key in keys:
            if not isinstance(key, str) or not key or key.split() != [key] or key in expected:
                raise ValueError('Invalid or duplicated publisher identity')
            expected[key] = transitions[category]
    before, after = call_outcomes(base), call_outcomes(reference)
    if set(before) != set(after):
        raise ValueError('Control coverage differs')
    groups = {}
    for node in before:
        groups.setdefault(node.split()[0], []).append(node)
    supplemental = validate_supplemental_passes(
        [] if supplemental_pass_to_pass is None else supplemental_pass_to_pass)
    for node in supplemental:
        if node in expected or groups.get(node) != [node]:
            raise ValueError('Supplemental test must be a distinct exact collected identity')
        if before[node] != 'passed' or after[node] != 'passed':
            raise ValueError('Supplemental regression test must pass both controls')
    if set(groups) != set(expected) | set(supplemental):
        raise ValueError('Publisher expectation coverage differs')
    for key, nodes in groups.items():
        if key in supplemental:
            continue
        if any((before[node], after[node]) != expected[key] for node in nodes):
            raise ValueError('Full test outcome contradicts publisher transition: ' + key)
    result = {'full_test_count': len(before), 'publisher_key_count': len(expected),
            'collision_groups': {key: sorted(nodes) for key, nodes in groups.items() if len(nodes) > 1},
            'base_passed': sum(value == 'passed' for value in before.values()),
            'reference_passed': sum(value == 'passed' for value in after.values()),
            'all_transitions_match': True, 'training_approved': False}
    if supplemental:
        result['supplemental_pass_to_pass'] = sorted(supplemental)
    return result


def compare_candidate(reference, candidate):
    """Compare complete valid call outcomes; infrastructure errors are not scores."""
    expected, actual = call_outcomes(reference), call_outcomes(candidate)
    if set(expected) != set(actual):
        raise ValueError('Candidate test coverage differs from qualified reference')
    differences = [{'nodeid': node, 'expected': expected[node], 'actual': actual[node]}
                   for node in sorted(expected) if expected[node] != actual[node]]
    return {'case_count': len(expected), 'disagreements': differences,
            'all_cases_match_reference': not differences, 'training_approved': False}
