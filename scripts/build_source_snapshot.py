"""Build an exact-tree source snapshot from an already-local pinned task image."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from zenithsync.artifacts import canonical_json,file_record

ORACLES=['/r2e_tests','/testbed/r2e_tests','/testbed/run_tests.sh',
         '/testbed/expected_test_output.json','/testbed/execution_result.json',
         '/testbed/parsed_commit.json','/testbed/syn_issue.json',
         '/testbed/modified_files.json','/testbed/modified_entities.json']
BUILDER='''import json
from pathlib import Path
from source_snapshot import sanitize
c=json.loads(Path('/tmp/config.json').read_text())
repo=c.pop('repo_root','/testbed')
normalization=c.pop('normalization',None)
if normalization is not None:
    from zenithsync.source_base import normalize_base
    normalize_base(repo,**normalization)
r=sanitize(repo,**c)
Path('/opt/zenithsync').mkdir(parents=True,exist_ok=True)
Path('/opt/zenithsync/source-snapshot.json').write_text(json.dumps(r,sort_keys=True))
print(json.dumps(r,sort_keys=True))
'''


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--resolution',type=Path,required=True)
    p.add_argument('--context',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--repo-root',default='/testbed')
    p.add_argument('--python',default='/usr/bin/python3')
    p.add_argument('--solution-already-absent',action='store_true',
                   help='Require local solution absence; explicitly does not verify ancestry')
    p.add_argument('--base-probe',type=Path,
                   help='Bound successful image probe for explicit base normalization')
    args=p.parse_args()
    if re.fullmatch(r'/[A-Za-z0-9_-]+',args.repo_root) is None:
        raise ValueError('Simple absolute source root required')
    if (re.fullmatch(r'/[A-Za-z0-9_./-]+',args.python) is None
            or any(part in ('','.','..') for part in args.python.split('/')[1:])):
        raise ValueError('Explicit absolute interpreter path required')
    source=json.loads(args.resolution.read_text())
    image=source['registry']['pinned_image']
    if 'task' in source:
        base=source['task']['base_commit']
        solution=source['solution_commit']
        oracles=ORACLES+['/issue.md','/testbed/issue.md','/.env']
        relation='ancestor'
    else:
        base=source['git']['base_commit']
        solution=source['instance_id'].rsplit('-',1)[-1]
        oracles=ORACLES
        relation='first_parent'
    if re.fullmatch(r'[a-z0-9_./-]+@sha256:[0-9a-f]{64}',image) is None:
        raise ValueError('Pinned registry image required')
    if any(re.fullmatch('[0-9a-f]{40}',x) is None for x in (base,solution)):
        raise ValueError('Full commit identities required')
    if args.solution_already_absent:
        relation='already_absent'
    if args.repo_root != '/testbed':
        oracles=list(dict.fromkeys(oracles+[path.replace('/testbed/',args.repo_root+'/')
                                           for path in oracles if path.startswith('/testbed/')]))
    config={'expected_base':base,'solution':solution,'oracle_paths':oracles,
            'solution_relation':relation,'repo_root':args.repo_root}
    probe_identity=None
    if args.base_probe is not None:
        probe_identity=file_record(args.base_probe)
        probe=json.loads(args.base_probe.read_text())
        if (probe['image']!=image or probe['returncode']!=0 or probe['cleanup_returncode']!=0
                or probe['observations']['head']['returncode']!=0):
            raise ValueError('Successful probe of the same pinned image required')
        head=probe['observations']['head']['stdout']
        if not isinstance(head,str) or re.fullmatch('[0-9a-f]{40}',head) is None:
            raise ValueError('Full observed image HEAD required')
        config['normalization']={'expected_head':head,'target_base':base}
    subprocess.run(['docker','image','inspect',image],check=True,capture_output=True,timeout=30)
    if args.context.exists() or args.output.exists():raise FileExistsError('Fresh build paths required')
    args.context.mkdir(parents=True);args.output.mkdir(parents=True)
    shutil.copyfile(ROOT/'zenithsync/source_snapshot.py',args.context/'source_snapshot.py')
    (args.context/'config.json').write_bytes(canonical_json(config))
    extra_copy=''
    extra_cleanup=''
    if args.base_probe is not None:
        shutil.copyfile(ROOT/'zenithsync/source_base.py',args.context/'source_base.py')
        extra_copy='COPY source_base.py source_snapshot.py /tmp/zenithsync/\n'
        extra_cleanup=' && rm -r /tmp/zenithsync'
    (args.context/'build_snapshot.py').write_text(BUILDER)
    (args.context/'Dockerfile').write_text('FROM '+image+'\nUSER root\n'+extra_copy+
        'COPY source_snapshot.py config.json build_snapshot.py /tmp/\n'
        'RUN PYTHONDONTWRITEBYTECODE=1 '+args.python+' /tmp/build_snapshot.py && '
        'rm /tmp/source_snapshot.py /tmp/config.json /tmp/build_snapshot.py'+extra_cleanup+'\nWORKDIR '+args.repo_root+'\n')
    inputs={p.name:file_record(p) for p in args.context.iterdir()}
    receipt={'resolution':file_record(args.resolution),'inputs':inputs,'script':file_record(Path(__file__)),
             'training_approved':False,'status':'building','python':args.python,'repo_root':args.repo_root}
    if args.base_probe is not None:
        receipt['base_probe']={'path':str(args.base_probe),'identity':probe_identity}
    try:
        with (args.output/'build.log').open('w') as log:
            subprocess.run(['docker','build','--network','none','--pull=false','--platform','linux/amd64',
                '--progress','plain','--iidfile',str(args.output/'image-id.txt'),str(args.context)],
                stdout=log,stderr=subprocess.STDOUT,check=True,timeout=600)
        if inputs!={p.name:file_record(p) for p in args.context.iterdir()}:
            raise ValueError('Build inputs changed')
        if args.base_probe is not None and file_record(args.base_probe)!=probe_identity:
            raise ValueError('Base probe changed during build')
        image_id=(args.output/'image-id.txt').read_text().strip()
        if re.fullmatch('sha256:[0-9a-f]{64}',image_id) is None:raise ValueError('Invalid image identity')
        receipt.update(status='built_runtime_probe_pending',image=image_id)
    except Exception as error:
        receipt.update(status='failed',error_type=type(error).__name__)
        raise
    finally:
        (args.output/'receipt.json').write_bytes(canonical_json(receipt))
    print({'status':receipt['status'],'image':image_id})


if __name__=='__main__':main()
