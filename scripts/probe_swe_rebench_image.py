"""Inspect one already-pulled SWE-rebench image without executing task tests."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record, load_json

PROBE = r'''
import json,os,subprocess,sys
from pathlib import Path
base=sys.argv[1]
def git(*args):
    result=subprocess.run(['git','-c','safe.directory=/testbed',*args],cwd='/testbed',
                          capture_output=True,text=True,timeout=20)
    return {'returncode':result.returncode,'stdout':result.stdout.strip(),'stderr':result.stderr.strip()}
head=git('rev-parse','HEAD')
status=git('status','--porcelain','--untracked-files=no')
refs=git('for-each-ref','--format=%(refname)')
commits=git('rev-list','--all','--count')
paths=['/testbed/.git','/testbed/patch.diff','/testbed/test.patch','/patch.diff','/test.patch',
       '/eval.sh','/root/setup_repo.sh','/root/setup_env.sh']
python_paths=['/opt/miniconda3/envs/testbed/bin/python','/opt/conda/envs/testbed/bin/python']
print(json.dumps({'head':head,'base_matches':head['returncode']==0 and head['stdout']==base,
                  'tracked_status':status,'refs':refs,'reachable_commit_count':commits,
                  'selected_paths':{path:Path(path).exists() for path in paths},
                  'candidate_environment_python_paths':{path:Path(path).exists() for path in python_paths},
                  'root_names':sorted(os.listdir('/'))[:100],
                  'scope':'Selected paths and Git state only; not exhaustive oracle or image security audit.'}))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resolution', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    resolution = load_json(args.resolution)
    image = resolution['registry']['pinned_image']
    base = resolution['task']['base_commit']
    if re.fullmatch(r'[a-z0-9_-]+/[a-z0-9_.-]+@sha256:[0-9a-f]{64}', image) is None:
        raise ValueError('Expected immutable Docker Hub image digest')
    if re.fullmatch('[0-9a-f]{40}', base) is None:
        raise ValueError('Expected exact source base commit')
    args.output.mkdir(parents=True, exist_ok=False)
    name = 'zenithsync-rebench-probe-' + uuid.uuid4().hex
    command = ['docker', 'run', '--pull', 'never', '--name', name, '--platform', 'linux/amd64',
        '--network', 'none', '--read-only', '--cap-drop', 'ALL', '--security-opt',
        'no-new-privileges', '--pids-limit', '64', '--memory', '1g', '--cpus', '1',
        '--entrypoint', '/usr/bin/python3', image, '-B', '-c', PROBE, base]
    receipt = {'input': file_record(args.resolution), 'script': file_record(Path(__file__)),
               'image': image, 'container': name, 'tests_executed': False, 'training_approved': False}
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=120)
        (args.output / 'stdout.txt').write_text(result.stdout)
        (args.output / 'stderr.txt').write_text(result.stderr)
        receipt['returncode'] = result.returncode
        if result.returncode != 0:
            raise RuntimeError('Image probe failed; retained output requires inspection')
        receipt['observations'] = json.loads(result.stdout)
    finally:
        cleanup = subprocess.run(['docker', 'rm', '-f', name], capture_output=True, text=True, timeout=30)
        receipt['cleanup_returncode'] = cleanup.returncode
        (args.output / 'receipt.json').write_bytes(canonical_json(receipt))
    if cleanup.returncode != 0:
        raise RuntimeError('Probe container cleanup unconfirmed')
    print({'base_matches': receipt['observations']['base_matches'],
           'reachable_commit_count': receipt['observations']['reachable_commit_count'],
           'cleanup_returncode': cleanup.returncode})


if __name__ == '__main__':
    main()
