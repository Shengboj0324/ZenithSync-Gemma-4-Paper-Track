"""Run base/reference controls using an explicit reviewed execution profile."""
import argparse
import base64
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record, load_json
from scripts.compare_source_snapshot import run_image
from scripts.qualify_swe_rebench_evaluator import PLUGIN, PROBE


def validate_profile(profile):
    required = {'instance_id', 'python', 'module', 'expected_origin', 'test_targets'}
    if not isinstance(profile, dict) or set(profile) != required:
        raise ValueError('Exact execution profile fields required')
    if (not isinstance(profile['instance_id'], str) or not profile['instance_id']
            or not isinstance(profile['module'], str)
            or re.fullmatch(r'[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*', profile['module']) is None):
        raise ValueError('Invalid task or import module')
    for key, prefix in [('python', '/opt/'), ('expected_origin', '/testbed/')]:
        value = profile[key]
        if (not isinstance(value, str) or not value.startswith(prefix)
                or '..' in Path(value).parts or '\x00' in value):
            raise ValueError('Invalid executable or source origin')
    targets = profile['test_targets']
    if (not isinstance(targets, list) or not targets
            or any(not isinstance(t, str) or not t or t.startswith(('-', '/'))
                   or '..' in Path(t.split('::')[0]).parts or '\x00' in t for t in targets)):
        raise ValueError('Nonempty relative test targets required')
    if len(targets) != len(set(targets)):
        raise ValueError('Duplicate test target')
    return profile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resolution', type=Path, required=True)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--profile', type=Path, required=True)
    parser.add_argument('--snapshot', type=Path, help='Independent verified snapshot directory')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    bound = {str(p): file_record(p) for p in
             [args.resolution, args.inputs / 'receipt.json', args.profile, Path(__file__),
              ROOT / 'scripts/qualify_swe_rebench_evaluator.py',
              ROOT / 'scripts/compare_source_snapshot.py']}
    resolution = load_json(args.resolution)
    inputs = load_json(args.inputs / 'receipt.json')
    profile = validate_profile(load_json(args.profile))
    if (inputs['task'] != resolution['task']
            or inputs['resolution'] != bound[str(args.resolution)]
            or profile['instance_id'] != inputs['task']['instance_id']):
        raise ValueError('Profile, source and image task identity mismatch')
    for name, identity in inputs['files'].items():
        if Path(name).name != name or file_record(args.inputs / name) != identity:
            raise ValueError('Evaluator input hash mismatch')
        bound[str(args.inputs / name)] = identity
    patches = {role: base64.b64encode((args.inputs / name).read_bytes()).decode()
               for role, name in [('reference', 'reference.patch'), ('tests', 'tests.patch')]}
    image = resolution['registry']['pinned_image']
    base, tree = inputs['task']['base_commit'], ''
    if args.snapshot:
        for name in ['snapshot.json', 'verification.json', 'receipt.json', 'input-bindings.json']:
            path = args.snapshot / name
            bound[str(path)] = file_record(path)
        snapshot = load_json(args.snapshot / 'snapshot.json')
        verified = load_json(args.snapshot / 'verification.json')
        container = load_json(args.snapshot / 'receipt.json')
        if (snapshot['base_commit'] != base or snapshot['exact_tree_preserved'] is not True
                or verified['tracked_manifest_matches'] is not True
                or verified['reachable_commits'] != 1
                or base not in verified['old_commits_inaccessible']
                or container['returncode'] != 0 or container['cleanup_returncode'] != 0):
            raise ValueError('Snapshot provenance or runtime verification failed')
        image, base, tree = container['image_id'], snapshot['snapshot_commit'], snapshot['source_tree']
    args.output.mkdir(parents=True, exist_ok=False)
    controls = {}
    for role in ('base', 'reference'):
        payload = {key: value for key, value in patches.items() if key == 'tests' or role == 'reference'}
        settings = {'BASE': base, 'TREE': tree, 'ROLE': role,
                    'PYTHON': profile['python'], 'MODULE': profile['module'],
                    'EXPECTED_ORIGIN': profile['expected_origin'], 'ALLOWED_PATHS': [],
                    'TEST_TARGETS': profile['test_targets'], 'PATCHES': payload,
                    'PLUGIN': PLUGIN, 'RESOURCE_PAYLOAD': '', 'RESOURCE_ADAPTER': ''}
        probe = ''.join(f'{key}={value!r}\n' for key, value in settings.items()) + PROBE
        result = run_image(image, args.output / role,
                           probe=probe, generated_grading_tests=True)
        controls[role] = {'container': result, 'runtime': load_json(args.output / role / 'runtime.json')}
        print({'role': role, 'runtime': controls[role]['runtime']}, flush=True)
    if any(file_record(Path(path)) != identity for path, identity in bound.items()):
        raise ValueError('Evaluator inputs changed during execution')
    (args.output / 'report.json').write_bytes(canonical_json({
        'controls': controls, 'inputs': bound, 'training_approved': False,
        'scope': 'Raw controls; full-node-ID outcome comparison still required.'}))


if __name__ == '__main__':
    main()
