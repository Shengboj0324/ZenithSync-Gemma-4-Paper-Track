"""Grade a task-172 patch using the qualified offline sanitized evaluator.

This explicitly scoped entry point does not establish trajectory provenance,
training admission, or a general SWE-rebench grading capability.
"""

import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record, load_json
from zenithsync.pytest_controls import compare_candidate, compare_controls


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--patch', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--attempt', type=Path, help='Bind grading to a completed native replay receipt')
    args = parser.parse_args()
    controls = ROOT / 'evidence/data/swe-rebench-snapshot-controls-001'
    comparison = ROOT / 'evidence/data/swe-rebench-control-comparison-001/comparison.json'
    expectations = ROOT / 'evidence/data/swe-rebench-evaluator-input-001/expectations.json'
    qualification = load_json(comparison)
    for role in ('base', 'reference'):
        for name, identity in qualification['inputs']['snapshot/' + role].items():
            if file_record(controls / role / name) != identity:
                raise ValueError('Qualified control input drift')
    if file_record(expectations) != qualification['inputs']['expectations']:
        raise ValueError('Publisher expectations changed')
    base = load_json(controls / 'base/outcomes.json')
    reference = load_json(controls / 'reference/outcomes.json')
    compare_controls(base, reference, load_json(expectations))
    identities = {'patch': file_record(args.patch), 'qualification': file_record(comparison),
                  'runner': file_record(ROOT / 'scripts/qualify_swe_rebench_evaluator.py'),
                  'comparator': file_record(ROOT / 'zenithsync/pytest_controls.py')}
    attempt_identity = None
    if args.attempt:
        replay = load_json(args.attempt / 'receipt.json')
        if (replay['instance_id'] != 'biolink__biolink-model-toolkit-172'
                or replay['status'] != 'replayed_not_graded' or replay['cleanup']['removed'] is not True
                or replay['patch'] != identities['patch']
                or file_record(args.attempt / 'submitted.patch') != identities['patch']):
            raise ValueError('Replay/patch linkage invalid')
        attempt_identity = file_record(args.attempt / 'receipt.json')
    args.output.mkdir(parents=True, exist_ok=False)
    subprocess.run([sys.executable, str(ROOT / 'scripts/qualify_swe_rebench_evaluator.py'),
                    '--snapshot', '--candidate-patch', str(args.patch.resolve()),
                    '--offline-resources', str(ROOT / 'evidence/data/swe-rebench-biolink-resources-001'),
                    '--output', str(args.output.resolve() / 'run')], check=True, timeout=400)
    run = args.output / 'run'
    metadata = load_json(run / 'report.json')
    original_metadata = load_json(controls / 'report.json')
    for key in ('image', 'expected_head', 'resource_receipt', 'resource_adapter', 'input_receipt'):
        if metadata[key] != original_metadata[key]:
            raise ValueError('Candidate evaluator differs from qualified environment: ' + key)
    if metadata['candidate_patch'] != identities['patch'] or file_record(args.patch) != identities['patch']:
        raise ValueError('Candidate patch identity changed')
    runtime = load_json(run / 'candidate/runtime.json')
    receipt = load_json(run / 'candidate/receipt.json')
    if (any(receipt[key] != 0 for key in ('returncode', 'copy_returncode', 'cleanup_returncode'))
            or receipt['state']['OOMKilled'] or 'error' in runtime
            or runtime.get('tracked_diff_unchanged_by_tests') is not True):
        raise ValueError('Evaluator runtime or cleanup invalid')
    result = compare_candidate(reference, load_json(run / 'candidate/outcomes.json'))
    for label, path in (('runner', ROOT / 'scripts/qualify_swe_rebench_evaluator.py'),
                        ('comparator', ROOT / 'zenithsync/pytest_controls.py'),
                        ('qualification', comparison)):
        if file_record(path) != identities[label]:
            raise ValueError('Grading implementation or qualification changed during execution')
    if args.attempt and file_record(args.attempt / 'receipt.json') != attempt_identity:
        raise ValueError('Replay receipt changed during grading')
    report = {'grading': result, 'inputs': identities, 'attempt': attempt_identity,
              'backend': 'swe_rebench_full_nodeid_reference',
              'outcomes': file_record(run / 'candidate/outcomes.json'),
              'script': file_record(Path(__file__)), 'training_approved': False,
              'model_executed': False, 'task': 'biolink__biolink-model-toolkit-172'}
    (args.output / 'report.json').write_bytes(canonical_json(report))
    print({'cases': result['case_count'], 'matches': result['all_cases_match_reference'],
           'disagreements': len(result['disagreements'])})


if __name__ == '__main__':
    main()
