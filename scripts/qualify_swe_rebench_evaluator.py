"""Run bounded base/reference controls for the inspected Biolink task, offline.

This is a task-specific qualification probe, not a general SWE-rebench harness.
No agent runs and evaluator patches are confined to disposable containers.
"""
import argparse
import base64
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record, load_json
from scripts.compare_source_snapshot import run_image

PLUGIN = r'''
import json
from pathlib import Path
items=[];reports=[];collection_errors=[]
def pytest_collection_finish(session):
    items.extend(item.nodeid for item in session.items)
def pytest_collectreport(report):
    if report.failed:
        collection_errors.append({'nodeid':report.nodeid,'error':str(report.longrepr)[:4000]})
def pytest_runtest_logreport(report):
    reports.append({'nodeid':report.nodeid,'when':report.when,'outcome':report.outcome})
def pytest_sessionfinish(session,exitstatus):
    Path('/audit/outcomes.json').write_text(json.dumps({'collected':items,'reports':reports,
        'collection_errors':collection_errors,'exitstatus':int(exitstatus)}))
'''

PROBE = r'''
import base64,hashlib,json,os,pathlib,subprocess
out=pathlib.Path('/audit');out.mkdir()
result={'role':ROLE,'tests_started':False}
def git(*args):
    return subprocess.run(['git','-c','safe.directory=/testbed',*args],cwd='/testbed',
                          capture_output=True,check=True,timeout=30).stdout
try:
    if git('rev-parse','HEAD').decode().strip()!=BASE:
        raise RuntimeError('Wrong checkout base')
    for name in (['reference'] if ROLE=='reference' else [])+['tests']:
        patch=pathlib.Path('/tmp/'+name+'.patch');patch.write_bytes(base64.b64decode(PATCHES[name]))
        git('apply','--check',str(patch));git('apply',str(patch))
    python='/opt/conda/envs/testbed/bin/python'
    origin=subprocess.run([python,'-c','import bmt; print(bmt.__file__)'],cwd='/testbed',
                          capture_output=True,text=True,timeout=30)
    result['import']={'returncode':origin.returncode,'stdout':origin.stdout.strip(),'stderr':origin.stderr}
    if origin.returncode or origin.stdout.strip()!='/testbed/bmt/__init__.py':
        raise RuntimeError('Module does not import from task checkout')
    (out/'audit_plugin.py').write_text(PLUGIN)
    env={**os.environ,'PYTHONPATH':'/audit','PYTHONDONTWRITEBYTECODE':'1'}
    before=hashlib.sha256(git('diff','--binary','HEAD','--')).hexdigest()
    result['tests_started']=True
    with (out/'pytest.log').open('w') as log:
        test=subprocess.run([python,'-m','pytest','--no-header','-rA','--tb=line','--color=no',
            '-p','no:cacheprovider','-W','ignore::DeprecationWarning','-p','audit_plugin',
            '--junitxml=/audit/junit.xml','tests/unit/test_toolkit.py'],cwd='/testbed',env=env,
            stdout=log,stderr=subprocess.STDOUT,timeout=240)
    result['pytest_exit']=test.returncode
    result['tracked_diff_unchanged_by_tests']=hashlib.sha256(git('diff','--binary','HEAD','--')).hexdigest()==before
except Exception as error:
    result['error_type']=type(error).__name__
    result['error']=str(error)[:2000]
finally:
    (out/'runtime.json').write_text(json.dumps(result))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    resolution_path = ROOT / 'evidence/data/swe-rebench-image-resolution-001/006/result.json'
    resolution = load_json(resolution_path)
    if resolution['task']['instance_id'] != 'biolink__biolink-model-toolkit-172':
        raise ValueError('This qualification probe supports only inspected task 172')
    source = ROOT / 'evidence/data/swe-rebench-evaluator-input-001'
    receipt = load_json(source / 'receipt.json')
    if receipt['task'] != resolution['task']:
        raise ValueError('Evaluator input task identity mismatch')
    for name, identity in receipt['files'].items():
        if file_record(source / name) != identity:
            raise ValueError('Evaluator input drift')
    patches = {name: base64.b64encode((source / filename).read_bytes()).decode()
               for name, filename in [('reference', 'reference.patch'), ('tests', 'tests.patch')]}
    args.output.mkdir(parents=True, exist_ok=False)
    results = {}
    for role in ('base', 'reference'):
        probe = ('BASE='+repr(resolution['task']['base_commit'])+'\nROLE='+repr(role)
                 +'\nPATCHES='+repr(patches)+'\nPLUGIN='+repr(PLUGIN)+'\n'+PROBE)
        result = run_image(resolution['registry']['pinned_image'], args.output / role,
                           probe=probe, generated_grading_tests=True)
        runtime = load_json(args.output / role / 'runtime.json')
        results[role] = {'container_returncode': result['returncode'],
                         'cleanup_returncode': result['cleanup_returncode'], 'runtime': runtime}
        print({'role':role, **runtime}, flush=True)
    (args.output / 'report.json').write_bytes(canonical_json({'controls':results,
        'input_receipt':file_record(source / 'receipt.json'), 'resolution':file_record(resolution_path),
        'script':file_record(Path(__file__)), 'scope':'Raw control observations; expectation comparison not yet performed.',
        'training_approved':False,'agent_executed':False}))


if __name__ == '__main__':
    main()
