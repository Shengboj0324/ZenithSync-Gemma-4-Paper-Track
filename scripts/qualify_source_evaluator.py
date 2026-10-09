"""Test a source evaluator against known base and reference solution controls.

Reference code is confined to separate evaluator containers. Neither control
is an agent attempt, a training example, or evidence of learned performance.
"""

import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.compare_source_snapshot import run_image
from zenithsync.artifacts import canonical_json, file_record
from zenithsync.evaluation import compare_junit

PROBE = r'''
import json, os, pathlib, subprocess, sys
pathlib.Path('/audit').mkdir()
subprocess.run(['git', 'checkout', '--detach', COMMIT], cwd='/testbed', check=True, timeout=30)
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd='/testbed', text=True).strip()
if head != COMMIT:
    raise RuntimeError('Evaluator source identity mismatch')
origin = subprocess.run(['/testbed/.venv/bin/python', '-c',
    'import pyramid; print(pyramid.__file__)'], capture_output=True, text=True, timeout=30)
if origin.returncode != 0 or origin.stdout.strip() != '/testbed/pyramid/__init__.py':
    raise RuntimeError('Pyramid must import from evaluator task source')
test = subprocess.run(['/testbed/.venv/bin/python', '-m', 'pytest', '-q',
    '-p', 'no:cacheprovider', '/r2e_tests', '--junitxml=/audit/junit.xml'],
    cwd='/testbed', timeout=240)
diff = subprocess.run(['git', 'diff', '--exit-code', 'HEAD', '--'], cwd='/testbed',
                      capture_output=True, timeout=30)
result = {'pytest_exit': test.returncode, 'head': head, 'source_import': origin.stdout.strip(),
          'tracked_source_unchanged': diff.returncode == 0}
pathlib.Path('/audit/runtime.json').write_text(json.dumps(result))
sys.exit(test.returncode if diff.returncode == 0 else 99)
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resolution', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source = json.loads(args.resolution.read_text())
    if source['repo'] != 'Pylons/pyramid':
        raise ValueError('This first evaluator qualification supports Pyramid only')
    base = source['git']['base_commit']
    solution = source['instance_id'].rsplit('-', 1)[-1]
    if any(re.fullmatch('[0-9a-f]{40}', value) is None for value in (base, solution)):
        raise ValueError('Invalid commit identities')
    args.output.mkdir(parents=True, exist_ok=False)
    for role, commit in [('base', base), ('reference', solution)]:
        probe = 'COMMIT = ' + repr(commit) + '\n' + PROBE
        result = run_image(source['registry']['pinned_image'], args.output / role,
                           probe=probe, generated_grading_tests=True)
        print({'control': role, 'exit': result['returncode']}, flush=True)
    comparison = compare_junit(args.output / 'base/junit.xml', args.output / 'reference/junit.xml')
    comparison.update({'scope': 'Reference controls only; no agent or training admission',
                       'input': file_record(args.resolution), 'script': file_record(Path(__file__)),
                       'container_runner': file_record(ROOT / 'scripts/compare_source_snapshot.py')})
    (args.output / 'comparison.json').write_bytes(canonical_json(comparison))
    print({k: comparison[k] for k in ['case_count', 'baseline_counts', 'candidate_counts']})


if __name__ == '__main__':
    main()
