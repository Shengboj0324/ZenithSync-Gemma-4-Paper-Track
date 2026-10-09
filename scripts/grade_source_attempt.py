"""Independently grade a saved source-runner patch in a fresh offline evaluator."""

import argparse
from importlib.metadata import version
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.compare_source_snapshot import run_image
from zenithsync.artifacts import canonical_json, file_record, load_json, verify
from zenithsync.source_evaluator import compare_publisher_expectations

PROBE = r'''
import hashlib, json, pathlib, subprocess, sys
pathlib.Path('/audit').mkdir()
patch = pathlib.Path('/tmp/submitted.patch').read_bytes()
if hashlib.sha256(patch).hexdigest() != PATCH_SHA:
    raise RuntimeError('Staged patch identity mismatch')
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd='/testbed', text=True).strip()
if head != BASE:
    raise RuntimeError('Evaluator base identity mismatch')
if patch.strip():
    subprocess.run(['git', 'apply', '--check', '/tmp/submitted.patch'], cwd='/testbed', check=True, timeout=30)
    subprocess.run(['git', 'apply', '/tmp/submitted.patch'], cwd='/testbed', check=True, timeout=30)
origin = subprocess.run(['/testbed/.venv/bin/python', '-c',
    'import pyramid; print(pyramid.__file__)'], capture_output=True, text=True, timeout=30)
if origin.returncode != 0 or origin.stdout.strip() != '/testbed/pyramid/__init__.py':
    raise RuntimeError('Candidate must import from task source')
test = subprocess.run(['/testbed/.venv/bin/python', '-m', 'pytest', '-q',
    '-p', 'no:cacheprovider', '/r2e_tests', '--junitxml=/audit/junit.xml'],
    cwd='/testbed', timeout=240)
pathlib.Path('/audit/runtime.json').write_text(json.dumps({'pytest_exit': test.returncode,
    'head': head, 'patch_sha256': PATCH_SHA, 'source_import': origin.stdout.strip()}))
sys.exit(test.returncode)
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--attempt', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if version('swegemma') != '0.2.10':
        raise ValueError('Pinned patch protection required')
    manifest = load_json(args.manifest)
    verify(args.package, manifest)
    attempt = load_json(args.attempt / 'receipt.json')
    if attempt['package_manifest'] != file_record(args.manifest):
        raise ValueError('Attempt belongs to a different package manifest')
    if attempt['agent_task'] != file_record(args.package / 'agent/task.json'):
        raise ValueError('Attempt task identity mismatch')
    if attempt.get('patch_submitted') is not True:
        raise ValueError('No submitted patch to grade')
    patch_path = args.attempt / 'agent.patch'
    identity = file_record(patch_path)
    if identity != attempt['patch'] or identity['size_bytes'] > 2 * 1024**2:
        raise ValueError('Patch identity mismatch or excessive size')
    patch = patch_path.read_text(encoding='utf-8')
    from swegemma.harness.verification import strip_protected_files_from_patch
    if strip_protected_files_from_patch(patch).strip() != patch.strip():
        raise ValueError('Submitted patch includes protected paths')
    task = load_json(args.package / 'evaluator/task.json')
    if task['repo'] != 'Pylons/pyramid' or task['test_path'] != '/r2e_tests':
        raise ValueError('Evaluator supports only the qualified Pyramid profile')
    if re.fullmatch('[0-9a-f]{40}', task['base_commit']) is None:
        raise ValueError('Invalid evaluator base')
    args.output.mkdir(parents=True, exist_ok=False)
    receipt = {'schema_version': 1, 'status': 'grading_started', 'patch': identity,
        'attempt': file_record(args.attempt / 'receipt.json'), 'attempt_status': attempt['status'],
        'package_manifest': file_record(args.manifest), 'fixture': attempt.get('fixture'),
        'training_approved': False, 'model_quality_evidence': False,
        'script': file_record(Path(__file__)), 'container_runner': file_record(ROOT / 'scripts/compare_source_snapshot.py')}
    try:
        probe = 'BASE = ' + repr(task['base_commit']) + '\nPATCH_SHA = ' + repr(identity['sha256']) + '\n' + PROBE
        result = run_image(task['image'], args.output / 'evaluator', probe=probe,
                           generated_grading_tests=True, patch_path=patch_path)
        if result['cleanup_returncode'] != 0 or result['state']['OOMKilled'] or result['returncode'] not in (0, 1):
            raise ValueError('Evaluator execution or cleanup failed')
        runtime = load_json(args.output / 'evaluator/runtime.json')
        if runtime['head'] != task['base_commit'] or runtime['patch_sha256'] != identity['sha256']:
            raise ValueError('Evaluator runtime identity mismatch')
        score = compare_publisher_expectations(args.output / 'evaluator/junit.xml',
                                               load_json(args.package / 'evaluator/expected.json'))
        if file_record(patch_path) != identity:
            raise ValueError('Patch changed during grading')
        verify(args.package, manifest)
        receipt.update(status='graded_against_source_expectations', score=score,
                       pytest_exit=result['returncode'], evaluator_receipt=file_record(args.output / 'evaluator/receipt.json'))
    except Exception as error:
        receipt.update(status='grading_failed', error_type=type(error).__name__, error=str(error))
        raise
    finally:
        (args.output / 'receipt.json').write_bytes(canonical_json(receipt))
    print({'status': receipt['status'], 'matches': score['all_cases_match_publisher_expectations'],
           'mismatches': len(score['disagreements']), 'fixture': receipt['fixture']})


if __name__ == '__main__':
    main()
