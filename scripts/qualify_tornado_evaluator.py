"""Run isolated Tornado base/reference controls through its publisher runner."""
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

# Runs inside the disposable evaluator using its installed interpreter.
CHILD = r'''
import json, pathlib, runpy, unittest, xml.etree.ElementTree as ET
namespace = runpy.run_path('/r2e_tests/tornado_unittest_runner.py')
suite = unittest.TestLoader().discover('.', pattern='test_*.py')
result = namespace['PytestLikeRunner'](verbosity=0).run(suite)
records = []
root = ET.Element('testsuite')
seen = set()
for identity, status, info in result.results:
    parts = identity.split('::')
    if len(parts) != 3 or identity in seen:
        raise RuntimeError('Unrepresentable or duplicate publisher test identity')
    seen.add(identity)
    case = ET.SubElement(root, 'testcase', classname=parts[0]+'.'+parts[1], name=parts[2])
    if status != 'passed':
        tag = {'failed': 'failure', 'error': 'error', 'skipped': 'skipped'}[status]
        ET.SubElement(case, tag)
    records.append({'identity': identity, 'status': status})
if len(records) != result.testsRun or not records:
    raise RuntimeError('Publisher runner omitted test outcomes')
root.set('tests', str(len(records)))
ET.ElementTree(root).write('/audit/junit.xml', encoding='utf-8', xml_declaration=True)
pathlib.Path('/audit/outcomes.json').write_text(json.dumps(records))
raise SystemExit(not result.wasSuccessful())
'''

PROBE = r'''
import hashlib, json, pathlib, subprocess, sys
pathlib.Path('/audit').mkdir()
git = lambda *args: subprocess.check_output(['git', *args], cwd='/testbed', text=True).strip()
if git('rev-parse', SOLUTION+'^') != BASE:
    raise RuntimeError('Source parent identity mismatch')
subprocess.run(['git','checkout','--detach',COMMIT], cwd='/testbed', check=True, timeout=30)
if git('rev-parse','HEAD') != COMMIT:
    raise RuntimeError('Source checkout mismatch')
pathlib.Path('/testbed/r2e_tests').symlink_to('/r2e_tests', target_is_directory=True)
origin = subprocess.check_output(['/testbed/.venv/bin/python','-c',
    'import tornado; print(tornado.__file__)'], cwd='/testbed', text=True, timeout=30).strip()
if origin != '/testbed/tornado/__init__.py':
    raise RuntimeError('Wrong source import')
runner = pathlib.Path('/r2e_tests/tornado_unittest_runner.py').read_bytes()
test = subprocess.run(['/testbed/.venv/bin/python','-W','ignore','-c',CHILD],
                      cwd='/testbed', timeout=240)
diff = subprocess.run(['git','diff','--exit-code','HEAD','--'],cwd='/testbed',capture_output=True,timeout=30)
pathlib.Path('/audit/runtime.json').write_text(json.dumps({
    'head':git('rev-parse','HEAD'), 'test_exit':test.returncode,
    'source_import':origin, 'tracked_source_unchanged':diff.returncode==0,
    'publisher_runner_sha256':hashlib.sha256(runner).hexdigest()}))
raise SystemExit(test.returncode if diff.returncode==0 else 99)
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resolution', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source = json.loads(args.resolution.read_text())
    if source['repo'] != 'tornadoweb/tornado':
        raise ValueError('Tornado profile required')
    base = source['git']['base_commit']
    solution = source['instance_id'].rsplit('-',1)[-1]
    if any(re.fullmatch('[0-9a-f]{40}', x) is None for x in (base, solution)):
        raise ValueError('Invalid source identities')
    args.output.mkdir(parents=True, exist_ok=False)
    for role, commit in [('base',base),('reference',solution)]:
        probe = '\n'.join(f'{k} = {v!r}' for k,v in {
            'BASE':base,'SOLUTION':solution,'COMMIT':commit,'CHILD':CHILD}.items())+'\n'+PROBE
        result = run_image(source['registry']['pinned_image'],args.output/role,
                           probe=probe,generated_grading_tests=True)
        runtime = json.loads((args.output/role/'runtime.json').read_text())
        if (result['returncode'] not in (0,1) or result['cleanup_returncode'] != 0
                or result['state']['OOMKilled'] or not runtime['tracked_source_unchanged']):
            raise RuntimeError('Evaluator execution or cleanup failed')
        print({'role':role,'test_exit':result['returncode']},flush=True)
    comparison = compare_junit(args.output/'base/junit.xml',args.output/'reference/junit.xml')
    comparison.update({'input':file_record(args.resolution),'script':file_record(Path(__file__)),
                       'runner':file_record(ROOT/'scripts/compare_source_snapshot.py'),
                       'training_approved':False,'agent_evaluated':False})
    (args.output/'comparison.json').write_bytes(canonical_json(comparison))
    print({k:comparison[k] for k in ('case_count','baseline_counts','candidate_counts')})


if __name__ == '__main__':
    main()
