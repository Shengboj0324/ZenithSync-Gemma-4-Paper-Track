"""Compare original repository tests before/after snapshot sanitization locally."""

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record
from zenithsync.evaluation import compare_junit

PROBE = r'''
import json, pathlib, subprocess, sys
pathlib.Path('/audit').mkdir()
origin = subprocess.run(['/testbed/.venv/bin/python', '-c',
    'import pyramid; print(pyramid.__file__)'], capture_output=True, text=True, timeout=30)
if origin.returncode != 0 or origin.stdout.strip() != '/testbed/pyramid/__init__.py':
    raise RuntimeError('Pyramid must import from the task source')
test = subprocess.run(['/testbed/.venv/bin/python', '-m', 'pytest', '-q',
    '-p', 'no:cacheprovider', '/testbed/pyramid/tests', '--junitxml=/audit/junit.xml'],
    cwd='/testbed', timeout=240)
diff = subprocess.run(['git', 'diff', '--exit-code', 'HEAD', '--'], cwd='/testbed',
                      capture_output=True, timeout=30)
result = {'pytest_exit': test.returncode, 'source_import': origin.stdout.strip(),
          'tracked_source_unchanged': diff.returncode == 0}
pathlib.Path('/audit/runtime.json').write_text(json.dumps(result))
sys.exit(test.returncode if diff.returncode == 0 else 99)
'''


def run_image(image, output, *, probe=PROBE, generated_grading_tests=False, patch_path=None):
    # Require a content identity, never a mutable local tag.
    if re.fullmatch(r'(?:[a-z0-9_./-]+@)?sha256:[0-9a-f]{64}', image) is None:
        raise ValueError('Expected an image digest or local image ID')
    output.mkdir(parents=True, exist_ok=False)
    name = 'zenithsync-source-tests-' + uuid.uuid4().hex
    create = ['docker', 'create', '--pull', 'never', '--name', name,
              '--platform', 'linux/amd64', '--network', 'none', '--cap-drop', 'ALL',
              '--security-opt', 'no-new-privileges', '--pids-limit', '128',
              '--memory', '2g', '--cpus', '2', '--entrypoint', '/usr/bin/python3', image,
              '/tmp/zenithsync-qualification-probe.py']
    subprocess.run(create, capture_output=True, check=True, timeout=30)
    receipt = {'image': image, 'container': name, 'agent_executed': False,
               'generated_grading_tests_executed': generated_grading_tests}
    try:
        # Stage source as a file: Linux limits a single argv entry to 128 KiB.
        # Resource-backed probes may exceed that even after payload compression.
        with tempfile.TemporaryDirectory(prefix='zenithsync-probe-') as staging:
            source = Path(staging) / 'probe.py'
            source.write_text(probe)
            receipt['probe_source'] = file_record(source)
            subprocess.run(['docker', 'cp', str(source),
                            name + ':/tmp/zenithsync-qualification-probe.py'],
                           capture_output=True, check=True, timeout=30)
        if patch_path is not None:
            receipt['staged_patch'] = file_record(patch_path)
            subprocess.run(['docker', 'cp', str(patch_path.resolve()), name + ':/tmp/submitted.patch'],
                           capture_output=True, check=True, timeout=30)
        with (output / 'stdout.log').open('w') as stdout, (output / 'stderr.log').open('w') as stderr:
            run = subprocess.run(['docker', 'start', '-a', name], stdout=stdout, stderr=stderr, timeout=330)
        receipt['returncode'] = run.returncode
        inspect = subprocess.run(['docker', 'inspect', name], capture_output=True, check=True, timeout=30)
        state = json.loads(inspect.stdout)[0]
        receipt['image_id'] = state['Image']
        receipt['state'] = {k: state['State'][k] for k in ['Status', 'ExitCode', 'OOMKilled', 'Error']}
        copy = subprocess.run(['docker', 'cp', name + ':/audit/.', str(output)], capture_output=True, timeout=30)
        receipt['copy_returncode'] = copy.returncode
        if copy.returncode != 0:
            raise RuntimeError('Test evidence export failed')
    finally:
        cleanup = subprocess.run(['docker', 'rm', '-f', name], capture_output=True, timeout=30)
        receipt['cleanup_returncode'] = cleanup.returncode
        (output / 'receipt.json').write_bytes(canonical_json(receipt))
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original', required=True)
    parser.add_argument('--snapshot', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    for name, image in [('original', args.original), ('snapshot', args.snapshot)]:
        result = run_image(image, args.output / name)
        print({'image_role': name, 'test_exit': result['returncode'],
               'cleanup_returncode': result['cleanup_returncode']}, flush=True)
    paired = compare_junit(args.output / 'original/junit.xml', args.output / 'snapshot/junit.xml')
    paired['script'] = file_record(Path(__file__))
    (args.output / 'comparison.json').write_bytes(canonical_json(paired))
    print({k: paired[k] for k in ['case_count', 'baseline_counts', 'candidate_counts']})


if __name__ == '__main__':
    main()
