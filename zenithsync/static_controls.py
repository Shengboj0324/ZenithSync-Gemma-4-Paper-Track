"""Compare bounded mypy text diagnostics without conflating existing and new errors.

This supports the explicit noncolored, error-code-bearing mypy output profile
used by our offline evaluator. Unknown output or inconsistent exit status rejects.
It does not infer runtime correctness or approve a training example.
"""
from collections import Counter
import re


ERROR = re.compile(r'([^:\n]+):[0-9]+(?::[0-9]+)?: error: (.+)  \[([a-z][a-z0-9-]*)\]')
NOTE = re.compile(r'[^:\n]+:[0-9]+(?::[0-9]+)?: note: .+')
FAILURE = re.compile(r'Found ([0-9]+) errors? in [0-9]+ files? \(checked [0-9]+ source files?\)')
SUCCESS = re.compile(r'Success: no issues found in [0-9]+ source files?')


def mypy_diagnostics(stdout, returncode):
    """Retain error multiplicity and identity, excluding unstable line numbers."""
    if (not isinstance(stdout, str) or len(stdout.encode()) > 2 * 1024**2
            or '\x1b' in stdout or type(returncode) is not int or returncode not in (0, 1)):
        raise ValueError('Bounded normal mypy execution required')
    errors = Counter()
    summaries = []
    for line in stdout.splitlines():
        if not line.strip():
            continue
        match = ERROR.fullmatch(line)
        if match:
            path, message, code = match.groups()
            errors[(path, code, message)] += 1
        elif NOTE.fullmatch(line):
            continue
        elif (match := FAILURE.fullmatch(line)):
            summaries.append(int(match.group(1)))
        elif SUCCESS.fullmatch(line):
            summaries.append(0)
        else:
            raise ValueError('Unsupported mypy output; inspect raw evidence')
    count = sum(errors.values())
    if summaries != [count] or returncode != int(count > 0):
        raise ValueError('Mypy summary, diagnostics and exit status disagree')
    return errors


def compare_mypy_controls(base, reference, candidate):
    """Report new diagnostics against both controls; line movement is not novelty."""
    controls = {name: mypy_diagnostics(result['stdout'], result['returncode'])
                for name, result in (('base', base), ('reference', reference), ('candidate', candidate))}

    def rows(counter):
        return [{'path': path, 'code': code, 'message': message, 'count': count}
                for (path, code, message), count in sorted(counter.items())]

    new_vs_base = controls['candidate'] - controls['base']
    new_vs_reference = controls['candidate'] - controls['reference']
    return {'counts': {name: sum(errors.values()) for name, errors in controls.items()},
        'introduced_vs_base': rows(new_vs_base),
        'introduced_vs_reference': rows(new_vs_reference),
        'removed_vs_base': rows(controls['base'] - controls['candidate']),
        'candidate_has_no_new_diagnostics': not new_vs_base and not new_vs_reference,
        'training_approved': False,
        'scope': 'Exact path/code/message multiset comparison; locations and notes excluded. '
                 'Requires separately qualified identical checker and dependency environment.'}
