"""Run bounded base/reference controls for the inspected Biolink task, offline.

This is a task-specific qualification probe, not a general SWE-rebench harness.
No agent runs and evaluator patches are confined to disposable containers.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import sys
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record, load_json
from scripts.compare_source_snapshot import run_image

PLUGIN = r'''
import json
from pathlib import Path
items=[];reports=[];collection_errors=[]
resource_events=[]
def pytest_configure(config):
    session_cache=Path('/audit/session_resources.json')
    if session_cache.exists():
        import base64
        from session_resource_replay import install_session_resource_replay
        data=json.loads(session_cache.read_text())
        install_session_resource_replay({url:dict(record,body=base64.b64decode(record['body'],validate=True))
            for url,record in data.items()},resource_events)
    cache=Path('/audit/resources.json')
    if cache.exists():
        import base64
        from offline_resources import install_resource_replay
        resources=json.loads(cache.read_text())
        install_resource_replay({url:(base64.b64decode(value['body']),value['sha256'])
            for url,value in resources.items()},resource_events)
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
    Path('/audit/resource-events.json').write_text(json.dumps(resource_events))
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
    if TREE and git('rev-parse','HEAD^{tree}').decode().strip()!=TREE:
        raise RuntimeError('Wrong checkout tree')
    if git('status','--porcelain','--untracked-files=no').strip():
        raise RuntimeError('Checkout has tracked changes before evaluation')
    for name in ([ROLE] if ROLE in ('reference','candidate') else [])+['tests']:
        patch=pathlib.Path('/tmp/'+name+'.patch');patch.write_bytes(base64.b64decode(PATCHES[name]))
        if patch.stat().st_size:
            options=['--index'] if name=='candidate' else []
            git('apply',*options,'--check',str(patch));git('apply',*options,str(patch))
        if name=='candidate':
            changed=git('diff','--name-only','HEAD','--').decode().splitlines()
            if any(path not in ALLOWED_PATHS for path in changed):
                raise RuntimeError('Candidate changes outside task-specific source allowance')
    python=PYTHON
    origin=subprocess.run([python,'-c','import importlib; print(importlib.import_module('+repr(MODULE)+').__file__)'],cwd='/testbed',
                          capture_output=True,text=True,timeout=30)
    result['import']={'returncode':origin.returncode,'stdout':origin.stdout.strip(),'stderr':origin.stderr}
    if origin.returncode or origin.stdout.strip()!=EXPECTED_ORIGIN:
        raise RuntimeError('Module does not import from task checkout')
    (out/'audit_plugin.py').write_text(PLUGIN)
    if globals().get('SESSION_RESOURCE_PAYLOAD'):
        import zlib
        (out/'session_resources.json').write_bytes(zlib.decompress(base64.b64decode(SESSION_RESOURCE_PAYLOAD)))
        (out/'session_resource_replay.py').write_text(SESSION_RESOURCE_ADAPTER)
    if RESOURCE_PAYLOAD:
        import zlib
        (out/'resources.json').write_bytes(zlib.decompress(base64.b64decode(RESOURCE_PAYLOAD)))
        (out/'offline_resources.py').write_text(RESOURCE_ADAPTER)
    env={**os.environ,'PYTHONPATH':'/audit','PYTHONDONTWRITEBYTECODE':'1'}
    before=hashlib.sha256(git('diff','--binary','HEAD','--')).hexdigest()
    result['tests_started']=True
    with (out/'pytest.log').open('w') as log:
        test=subprocess.run([python,'-m','pytest','--no-header','-rA','--tb=line','--color=no',
            '-p','no:cacheprovider','-W','ignore::DeprecationWarning','-p','audit_plugin',
            '--junitxml=/audit/junit.xml',*TEST_TARGETS],cwd='/testbed',env=env,
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
    parser.add_argument('--offline-resources', type=Path,
                        help='Explicit hashed resource bundle; changes evaluator transport only')
    parser.add_argument('--snapshot', action='store_true',
                        help='Evaluate the previously verified task-172 sanitized snapshot')
    parser.add_argument('--candidate-patch', type=Path,
                        help='Grade this task-172 patch alone; empty patch is a negative control')
    args = parser.parse_args()
    resolution_path = ROOT / 'evidence/data/swe-rebench-image-resolution-001/006/result.json'
    resolution = load_json(resolution_path)
    if resolution['task']['instance_id'] != 'biolink__biolink-model-toolkit-172':
        raise ValueError('This qualification probe supports only inspected task 172')
    image = resolution['registry']['pinned_image']
    base = resolution['task']['base_commit']
    tree = ''
    snapshot_inputs = None
    if args.snapshot:
        directory = ROOT / 'evidence/data/swe-rebench-snapshot-verify-001'
        snapshot = load_json(directory / 'snapshot.json')
        container = load_json(directory / 'receipt.json')
        if snapshot['base_commit'] != base or not snapshot['exact_tree_preserved']:
            raise ValueError('Snapshot source identity mismatch')
        image = container['image_id']
        base = snapshot['snapshot_commit']
        tree = snapshot['source_tree']
        snapshot_inputs = {name:file_record(directory / name)
                           for name in ('snapshot.json', 'receipt.json', 'verification.json')}
    source = ROOT / 'evidence/data/swe-rebench-evaluator-input-001'
    receipt = load_json(source / 'receipt.json')
    if receipt['task'] != resolution['task']:
        raise ValueError('Evaluator input task identity mismatch')
    for name, identity in receipt['files'].items():
        if file_record(source / name) != identity:
            raise ValueError('Evaluator input drift')
    patches = {name: base64.b64encode((source / filename).read_bytes()).decode()
               for name, filename in [('reference', 'reference.patch'), ('tests', 'tests.patch')]}
    candidate_identity = None
    if args.candidate_patch:
        body = args.candidate_patch.read_bytes()
        if len(body) > 2 * 1024**2:
            raise ValueError('Candidate patch exceeds 2 MiB')
        candidate_identity = {'size_bytes':len(body), 'sha256':hashlib.sha256(body).hexdigest()}
        # The candidate run receives no reference patch payload.
        patches = {'tests':patches['tests'], 'candidate':base64.b64encode(body).decode()}
    resource_payload = ''
    resource_receipt = None
    adapter_path = ROOT / 'zenithsync/offline_resources.py'
    if args.offline_resources:
        resource_receipt = file_record(args.offline_resources / 'receipt.json')
        metadata = load_json(args.offline_resources / 'receipt.json')
        resources = {}
        for name, record in metadata['files'].items():
            if Path(name).name != name:
                raise ValueError('Resource filename must be a basename')
            path = args.offline_resources / name
            body = path.read_bytes()
            identity = {'size_bytes':len(body), 'sha256':hashlib.sha256(body).hexdigest()}
            if identity != record['identity']:
                raise ValueError('Resource hash mismatch')
            url = record['original_url']
            if url in resources:
                raise ValueError('Duplicate resource URL')
            resources[url] = {'body':base64.b64encode(body).decode(), 'sha256':identity['sha256']}
        resource_payload = base64.b64encode(zlib.compress(canonical_json(resources))).decode()
    args.output.mkdir(parents=True, exist_ok=False)
    results = {}
    for role in (('candidate',) if args.candidate_patch else ('base', 'reference')):
        probe = ('BASE='+repr(base)+'\nTREE='+repr(tree)+'\nROLE='+repr(role)
                 +'\nPYTHON="/opt/conda/envs/testbed/bin/python"\nMODULE="bmt"'
                 +'\nEXPECTED_ORIGIN="/testbed/bmt/__init__.py"'
                 +'\nALLOWED_PATHS=["bmt/toolkit.py"]\nTEST_TARGETS=["tests/unit/test_toolkit.py"]'
                 +'\nPATCHES='+repr(patches)+'\nPLUGIN='+repr(PLUGIN)
                 +'\nRESOURCE_PAYLOAD='+repr(resource_payload)
                 +'\nRESOURCE_ADAPTER='+repr(adapter_path.read_text())+'\n'+PROBE)
        result = run_image(image, args.output / role,
                           probe=probe, generated_grading_tests=True)
        runtime = load_json(args.output / role / 'runtime.json')
        results[role] = {'container_returncode': result['returncode'],
                         'cleanup_returncode': result['cleanup_returncode'], 'runtime': runtime}
        print({'role':role, **runtime}, flush=True)
    (args.output / 'report.json').write_bytes(canonical_json({'controls':results,
        'input_receipt':file_record(source / 'receipt.json'), 'resolution':file_record(resolution_path),
        'resource_receipt':resource_receipt, 'resource_adapter':file_record(adapter_path),
        'snapshot_inputs':snapshot_inputs, 'image':image, 'expected_head':base,
        'candidate_patch':candidate_identity,
        'script':file_record(Path(__file__)), 'scope':'Raw control observations; expectation comparison not yet performed.',
        'training_approved':False,'agent_executed':False}))


if __name__ == '__main__':
    main()
