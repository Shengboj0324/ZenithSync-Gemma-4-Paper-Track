"""Inspect a pinned source image in a read-only, networkless local container.

No agent, reference patch, or source-generated test is executed. This measures
base identity and oracle reachability, not task correctness or replay fidelity.
"""

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record

PROBE = r'''
import json, os, subprocess, sys
from pathlib import Path
solution, expected_base = sys.argv[1:]
def git(*args):
    p = subprocess.run(['git', '-c', 'safe.directory=/testbed', *args],
                       cwd='/testbed', capture_output=True, text=True, timeout=20)
    return {'returncode': p.returncode, 'stdout': p.stdout.strip(), 'stderr': p.stderr.strip()}
head = git('rev-parse', 'HEAD')
parent = git('rev-parse', solution + '^')
solution_object = git('cat-file', '-e', solution + '^{commit}')
paths = ['/r2e_tests', '/testbed/r2e_tests', '/testbed/expected_test_output.json',
         '/testbed/parsed_commit.json', '/testbed/run_tests.sh', '/testbed/.git']
print(json.dumps({'uid': os.getuid(), 'head': head, 'parent': parent,
    'base_matches': head['returncode'] == 0 and head['stdout'] == expected_base,
    'parent_matches': parent['returncode'] == 0 and parent['stdout'] == expected_base,
    'solution_object_accessible': solution_object['returncode'] == 0,
    'paths': [{'path': p, 'exists': Path(p).exists(), 'readable': os.access(p, os.R_OK),
               'searchable': os.access(p, os.X_OK)} for p in paths]}))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resolution', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source = json.loads(args.resolution.read_text())
    image = source['registry']['pinned_image']
    base = source['git']['base_commit']
    solution = source['instance_id'].rsplit('-', 1)[-1]
    if re.fullmatch(r'[a-z0-9_-]+/[a-z0-9_.-]+@sha256:[0-9a-f]{64}', image) is None:
        raise ValueError('Expected pinned Docker Hub digest')
    if any(re.fullmatch('[0-9a-f]{40}', value) is None for value in (base, solution)):
        raise ValueError('Expected exact commit identities')
    args.output.mkdir(parents=True, exist_ok=False)
    name = 'zenithsync-source-probe-' + uuid.uuid4().hex
    command = ['docker', 'run', '--pull', 'never', '--name', name, '--platform', 'linux/amd64',
        '--network', 'none', '--read-only', '--cap-drop', 'ALL', '--security-opt',
        'no-new-privileges', '--pids-limit', '64', '--memory', '1g', '--cpus', '1',
        '--entrypoint', '/usr/bin/python3', image, '-c', PROBE, solution, base]
    receipt = {'schema_version': 1, 'image': image, 'container': name,
               'input': file_record(args.resolution), 'script': file_record(Path(__file__)),
               'agent_executed': False, 'tests_executed': False, 'training_approved': False}
    try:
        run = subprocess.run(command, capture_output=True, text=True, timeout=90)
        (args.output / 'stdout.txt').write_text(run.stdout)
        (args.output / 'stderr.txt').write_text(run.stderr)
        receipt['returncode'] = run.returncode
        if run.returncode == 0:
            receipt['observations'] = json.loads(run.stdout)
        else:
            raise RuntimeError('Source image inspection failed; inspect retained output')
    finally:
        cleanup = subprocess.run(['docker', 'rm', '-f', name], capture_output=True, text=True, timeout=30)
        receipt['cleanup_returncode'] = cleanup.returncode
        receipt['cleanup_stdout'] = cleanup.stdout.strip()
        (args.output / 'receipt.json').write_bytes(canonical_json(receipt))
    print({'base_matches': receipt['observations']['base_matches'],
           'solution_object_accessible': receipt['observations']['solution_object_accessible'],
           'cleanup_returncode': receipt['cleanup_returncode']})


if __name__ == '__main__':
    main()
