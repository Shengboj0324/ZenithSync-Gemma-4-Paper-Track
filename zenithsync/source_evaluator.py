"""Compare source expectations without dropping colliding test identities."""

from collections import defaultdict
from pathlib import Path
import xml.etree.ElementTree as ET

from zenithsync.evaluation import junit_outcomes


def compare_publisher_expectations(junit: Path, expected: dict) -> dict:
    """Require every fully qualified case to satisfy its publisher group.

    The publisher uses Class.method identities, which may collide across modules.
    We retain all cases and require all members to agree with the expected state;
    no last-write-wins dictionary collapse is used to assign acceptance.
    """
    allowed = {'PASSED', 'FAILED', 'ERROR', 'SKIPPED'}
    if not isinstance(expected, dict) or not expected:
        raise ValueError('Expected a nonempty publisher status mapping')
    if any(not isinstance(k, str) or not k or not isinstance(v, str) or v not in allowed
           for k, v in expected.items()):
        raise ValueError('Unsupported publisher expectation')
    outcomes = junit_outcomes(junit)
    groups = defaultdict(list)
    for case in ET.parse(junit).getroot().iter('testcase'):
        classname, name = case.get('classname'), case.get('name')
        identity = classname + '::' + name
        publisher_key = classname.rsplit('.', 1)[-1] + '.' + name
        groups[publisher_key].append(identity)
    missing = sorted(expected.keys() - groups.keys())
    unexpected = sorted(groups.keys() - expected.keys())
    disagreements = []
    for key in sorted(groups.keys() & expected.keys()):
        for identity in sorted(groups[key]):
            observed = outcomes[identity].upper()
            if observed != expected[key]:
                disagreements.append({'test': identity, 'publisher_key': key,
                                      'expected': expected[key], 'observed': observed})
    return {'case_count': len(outcomes), 'publisher_key_count': len(expected),
            'observed_group_count': len(groups), 'missing_groups': missing,
            'unexpected_groups': unexpected, 'disagreements': disagreements,
            'collisions': {k: sorted(v) for k, v in sorted(groups.items()) if len(v) > 1},
            'all_cases_match_publisher_expectations': not (missing or unexpected or disagreements),
            'scope': 'Strict all-members comparison of Class.method groups; not exact publisher parser parity'}
