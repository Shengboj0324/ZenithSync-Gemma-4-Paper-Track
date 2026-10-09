"""Independently grade saved teacher patches with qualified repository profiles."""
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.compare_source_snapshot import run_image
from scripts.qualify_tornado_evaluator import CHILD as TORNADO_CHILD
from zenithsync.artifacts import canonical_json,file_record
from zenithsync.source_evaluator import compare_publisher_expectations

PROBE=r'''
import hashlib,json,pathlib,subprocess
pathlib.Path('/audit').mkdir()
patch=pathlib.Path('/tmp/submitted.patch').read_bytes()
if hashlib.sha256(patch).hexdigest()!=PATCH_SHA:raise RuntimeError('Patch checksum mismatch')
git=lambda *args:subprocess.check_output(['git',*args],cwd='/testbed').strip()
if git('rev-parse','HEAD').decode()!=BASE:raise RuntimeError('Wrong source base')
subprocess.run(['git','apply','--check','/tmp/submitted.patch'],cwd='/testbed',check=True,timeout=30)
subprocess.run(['git','apply','/tmp/submitted.patch'],cwd='/testbed',check=True,timeout=30)
before=git('diff','--binary','HEAD','--')
pathlib.Path('/testbed/r2e_tests').symlink_to('/r2e_tests',target_is_directory=True)
origin=subprocess.check_output(['/testbed/.venv/bin/python','-c',
    'import importlib; print(importlib.import_module('+repr(MODULE)+').__file__)'],cwd='/testbed',text=True,timeout=30).strip()
if origin!=IMPORT_PATH:raise RuntimeError('Wrong source import')
r=subprocess.run(['/testbed/.venv/bin/python','-W','ignore','-c',CHILD],cwd='/testbed',timeout=240)
if before!=git('diff','--binary','HEAD','--'):raise RuntimeError('Tests modified tracked patch')
pathlib.Path('/audit/runtime.json').write_text(json.dumps({'base':BASE,'patch_sha256':PATCH_SHA,
    'test_exit':r.returncode,'source_import':origin,'tracked_patch_unchanged':True}))
raise SystemExit(r.returncode)
'''


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--attempt',type=Path,required=True)
    p.add_argument('--src-layout',action='store_true')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--resolution',type=Path,default=ROOT/'evidence/data/source-environment-resolution-001/07/result.json')
    p.add_argument('--expectations',type=Path,default=ROOT/'evidence/data/tornado-expectations-002')
    args=p.parse_args()
    attempt=json.loads((args.attempt/'receipt.json').read_text())
    patch=args.attempt/'submitted.patch';identity=file_record(patch)
    if (attempt['status']!='replayed_not_graded' or attempt['patch']!=identity
            or attempt['cleanup']['removed'] is not True or identity['size_bytes']>2*1024**2):
        raise ValueError('Unqualified replay receipt')
    resolution=args.resolution
    source=json.loads(resolution.read_text())
    expected_path=args.expectations/'publisher-expected.json'
    expected=json.loads(expected_path.read_text())
    control=json.loads((expected_path.parent/'report.json').read_text())
    if (source['repo'] not in ('tornadoweb/tornado','Pylons/pyramid') or source['instance_id']!=attempt['instance_id']
            or control['resolution']!=file_record(resolution)
            or not control['reference']['all_cases_match_publisher_expectations']
            or control['base']['all_cases_match_publisher_expectations']):
        raise ValueError('Evaluator controls not qualified')
    # Re-read the pinned source row rather than trusting an editable expectation
    # export alone. The solution commit stays evaluator-side.
    import pyarrow.parquet as pq
    from zenithsync.source_task_metadata import _object
    shard=control['source']['shard']
    relative=f'data/train-{shard:05d}-of-00008.parquet'
    shard_path=ROOT/f'artifacts/data/quarantine/r2e-gym-shard-{shard:03d}'/relative
    identity_before=file_record(shard_path)
    intake=json.loads((ROOT/f'evidence/data/r2e-gym-shard-{shard:03d}/receipt.json').read_text())
    if identity_before!=control['source']['identity'] or identity_before!=intake['downloaded'][relative]:
        raise ValueError('Source expectations shard mismatch')
    row=pq.read_table(shard_path,columns=['repo_name','commit_hash','expected_output_json']).slice(control['source']['row_index'],1).to_pylist()[0]
    if (row['repo_name']!=source['repo'].split('/')[-1] or source['instance_id']!=source['repo'].replace('/','__')+'-'+row['commit_hash']
            or json.loads(row['expected_output_json'],object_pairs_hook=_object)!=expected
            or file_record(shard_path)!=identity_before):
        raise ValueError('Expected outcomes or source identity differ from pinned row')
    module=source['repo'].split('/')[-1]
    if module=='tornado' and args.src_layout:raise ValueError('Unqualified Tornado source layout')
    child=TORNADO_CHILD if module=='tornado' else (
        "import subprocess; raise SystemExit(subprocess.call(['/testbed/.venv/bin/python',"
        "'-m','pytest','-q','-p','no:cacheprovider','/r2e_tests','--junitxml=/audit/junit.xml']))")
    import_path='/testbed/'+('src/' if args.src_layout else '')+module+'/__init__.py'
    args.output.mkdir(parents=True,exist_ok=False)
    probe='\n'.join(f'{k}={v!r}' for k,v in {'BASE':source['git']['base_commit'],
        'PATCH_SHA':identity['sha256'],'CHILD':child,'MODULE':module,'IMPORT_PATH':import_path}.items())+'\n'+PROBE
    receipt=run_image(source['registry']['pinned_image'],args.output/'evaluator',
        probe=probe,generated_grading_tests=True,patch_path=patch)
    if receipt['cleanup_returncode']!=0 or receipt['state']['OOMKilled'] or receipt['returncode'] not in (0,1):
        raise RuntimeError('Evaluator runtime or cleanup failed')
    runtime=json.loads((args.output/'evaluator/runtime.json').read_text())
    if not runtime['tracked_patch_unchanged']:raise RuntimeError('Patch changed during test')
    result=compare_publisher_expectations(args.output/'evaluator/junit.xml',expected)
    report={'grading':result,'patch':identity,'attempt':file_record(args.attempt/'receipt.json'),
        'expected':file_record(expected_path),'controls':file_record(expected_path.parent/'report.json'),
        'script':file_record(Path(__file__)),
        'runner':file_record(ROOT/'scripts/qualify_tornado_evaluator.py'),
        'training_approved':False,'new_model_evaluated':False,
        'scope':'One teacher patch replay, adapted native tools; not original-observation equivalence'}
    (args.output/'report.json').write_bytes(canonical_json(report))
    print({'cases':result['case_count'],'matches':result['all_cases_match_publisher_expectations'],
           'disagreements':len(result['disagreements'])})


if __name__=='__main__':main()
