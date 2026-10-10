"""Qualify selected V2 Python base/reference controls in offline containers."""
import argparse
import base64
from pathlib import Path
import re
import sys
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record, load_json
from zenithsync.pytest_controls import compare_candidate, compare_controls, validate_supplemental_passes
from scripts.compare_source_snapshot import run_image
from scripts.qualify_swe_rebench_evaluator import PROBE, PLUGIN
from zenithsync.session_resource_bundle import session_resource_payload


def validate_v2_profile(profile):
    required = {'root', 'python', 'module', 'expected_origin', 'test_targets'}
    optional = {'layout', 'supplemental_pass_to_pass', 'pytest_root', 'session_resources',
                'publisher_nodes_only'}
    if not isinstance(profile, dict) or not required <= set(profile) or set(profile) - required - optional:
        raise ValueError('Exact reviewed profile required')
    if 'supplemental_pass_to_pass' in profile:
        validate_supplemental_passes(profile['supplemental_pass_to_pass'])
    if 'publisher_nodes_only' in profile and profile['publisher_nodes_only'] is not True:
        raise ValueError('Publisher node selection must be explicitly true')
    if 'session_resources' in profile:
        value = profile['session_resources']
        if (not isinstance(value, dict) or set(value) != {'receipt', 'max_bytes'}
                or type(value['max_bytes']) is not int or value['max_bytes'] <= 0):
            raise ValueError('Explicit resource receipt and byte budget required')
        identity = value['receipt']
        if (not isinstance(identity, dict) or set(identity) != {'sha256', 'size_bytes'}
                or not isinstance(identity['sha256'], str)
                or re.fullmatch('[0-9a-f]{64}', identity['sha256']) is None
                or type(identity['size_bytes']) is not int or identity['size_bytes'] <= 0):
            raise ValueError('Exact resource receipt identity required')
    root, module, python = profile['root'], profile['module'], profile['python']
    if not isinstance(root, str) or re.fullmatch(r'/[A-Za-z0-9_-]+', root) is None:
        raise ValueError('Simple absolute repository root required')
    if 'pytest_root' in profile and profile['pytest_root'] != root:
        raise ValueError('Explicit pytest root must equal the task repository root')
    if not isinstance(module, str) or re.fullmatch(r'[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*', module) is None:
        raise ValueError('Invalid module name')
    if (not isinstance(python, str) or re.fullmatch(r'/[A-Za-z0-9_./-]+', python) is None
            or any(part in ('.', '..', '') for part in python.split('/')[1:])):
        raise ValueError('Explicit absolute interpreter path required')
    layout = profile.get('layout', 'src')
    if layout not in ('src', 'flat'):
        raise ValueError('Explicit src or flat package layout required')
    prefix = '/src/' if layout == 'src' else '/'
    if profile['expected_origin'] != root + prefix + module.replace('.', '/') + '/__init__.py':
        raise ValueError('Package origin must match the reviewed repository layout')
    targets = profile['test_targets']
    if (not isinstance(targets, list) or not targets
            or any(not isinstance(target, str) or re.fullmatch(r'[A-Za-z0-9_/-]+\.py', target) is None
                   or any(part in ('', '.', '..') for part in target.split('/')) for target in targets)
            or len(set(targets)) != len(targets)):
        raise ValueError('Explicit relative Python test files required')
    return profile


def validate_source_allowance(paths, *, package_root='src'):
    """Require an explicit source-only allowance before starting a container."""
    if (not isinstance(package_root, str)
            or re.fullmatch(r'[A-Za-z_]\w*', package_root) is None
            or package_root in ('tests', 'test')):
        raise ValueError('Explicit source package root required')
    if not isinstance(paths, list) or not paths:
        raise ValueError('Nonempty source allowance required')
    for path in paths:
        if (not isinstance(path, str) or not path.startswith(package_root + '/')
                or not path.endswith('.py')
                or re.fullmatch(r'[A-Za-z0-9_./-]+', path) is None
                or any(part in ('', '.', '..', '.git') for part in path.split('/'))):
            raise ValueError('Explicit relative package Python source allowance required')
    if len(set(paths)) != len(paths):
        raise ValueError('Duplicate source allowance')
    return paths


def publisher_test_targets(task, reviewed_files):
    """Select publisher nodes, widening truncated parameters to their function.

    Log-derived parameter labels may be truncated at whitespace. Execute the
    full function in that case; compare_controls must still enforce exact
    publisher-group coverage and valid phases for every collected case.
    """
    if any(not isinstance(task.get(key), list) for key in ('FAIL_TO_PASS', 'PASS_TO_PASS')):
        raise ValueError('Publisher expectation lists required')
    nodes = task['FAIL_TO_PASS'] + task['PASS_TO_PASS']
    if (not nodes or any(not isinstance(node, str) or not any(
            node.startswith(name + '::') and len(node) > len(name) + 2 for name in reviewed_files)
            for node in nodes) or len(set(nodes)) != len(nodes)):
        raise ValueError('Publisher nodes must be unique and within reviewed test files')
    targets = [node.split('[', 1)[0] if '[' in node and not node.endswith(']')
               else node for node in nodes]
    # Whole-function selection already includes explicitly named parameters.
    functions = {target for target in targets if '[' not in target}
    return list(dict.fromkeys(target for target in targets
                              if '[' not in target or target.split('[', 1)[0] not in functions))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', type=Path, required=True)
    parser.add_argument('--task-receipt', type=Path, required=True)
    parser.add_argument('--resolution', type=Path, required=True)
    parser.add_argument('--profile', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--snapshot', type=Path,
                        help='Independently verified sanitized image, with bound source base')
    parser.add_argument('--candidate-replay', type=Path,
                        help='Native replay directory containing receipt and submitted patch')
    parser.add_argument('--allowed-source-path', action='append', default=[])
    parser.add_argument('--session-resources', type=Path)
    args = parser.parse_args()
    paths = [args.task, args.task_receipt, args.resolution, args.profile, Path(__file__),
             ROOT / 'scripts/compare_source_snapshot.py',
             ROOT / 'scripts/qualify_swe_rebench_evaluator.py',
             ROOT / 'zenithsync/pytest_controls.py', ROOT / 'evidence/p1/task-index-001/receipt.json']
    identities = {str(path): file_record(path) for path in paths}
    task = load_json(args.task)
    receipt = load_json(args.task_receipt)
    resolution = load_json(args.resolution)
    profile = validate_v2_profile(load_json(args.profile))
    resource_bindings = None
    resource_payload = ''
    resource_adapter = ''
    if bool(args.session_resources) != ('session_resources' in profile):
        raise ValueError('Session resources require a matching reviewed profile')
    if args.session_resources:
        raw, resource_bindings = session_resource_payload(args.session_resources,
            max_bytes=profile['session_resources']['max_bytes'])
        if resource_bindings['files']['receipt.json'] != profile['session_resources']['receipt']:
            raise ValueError('Resource receipt differs from reviewed profile')
        extra_paths = [args.session_resources / name for name in resource_bindings['files']]
        extra_paths += [ROOT / 'zenithsync/session_resource_bundle.py',
                        ROOT / 'zenithsync/session_resource_replay.py']
        for path in extra_paths:
            identities[str(path)] = file_record(path)
        for name, identity in resource_bindings['files'].items():
            key = str(args.session_resources / name)
            if identities[key] != identity:
                raise ValueError('Resource changed after payload construction')
        paths.extend(extra_paths)
        resource_payload = base64.b64encode(zlib.compress(raw)).decode('ascii')
        resource_adapter = (ROOT / 'zenithsync/session_resource_replay.py').read_text()
    if bool(args.candidate_replay) != bool(args.allowed_source_path):
        raise ValueError('Candidate replay and reviewed source allowance required together')
    if args.candidate_replay and args.snapshot is None:
        raise ValueError('Candidate grading requires a verified sanitized snapshot')
    if args.candidate_replay:
        package_root = (profile['module'].split('.')[0]
                        if profile.get('layout', 'src') == 'flat' else 'src')
        validate_source_allowance(args.allowed_source_path, package_root=package_root)
    if identities[str(args.task)] != receipt['task']:
        raise ValueError('Task content differs from extraction receipt')
    if any(task[key] != resolution['task'][key] for key in
           ('repo', 'instance_id', 'base_commit', 'image_name')):
        raise ValueError('Task and pinned runtime metadata differ')
    reserved = {name.casefold() for name in load_json(ROOT / 'evidence/p1/task-index-001/receipt.json')['repo_counts']}
    if task['repo'].casefold() in reserved:
        raise ValueError('Reserved task excluded from qualification')
    root = profile['root']
    targets = list(profile['test_targets'])
    if profile.get('publisher_nodes_only'):
        targets = publisher_test_targets(task, targets)
    if 'pytest_root' in profile:
        targets.insert(0, '--rootdir=' + profile['pytest_root'])
    if re.fullmatch('[0-9a-f]{40}', task['base_commit']) is None:
        raise ValueError('Full task base commit required')
    image = resolution['registry']['pinned_image']
    base, tree = task['base_commit'], ''
    if args.snapshot is not None:
        snapshot_paths = [args.snapshot / name for name in
                          ('snapshot.json', 'verification.json', 'receipt.json', 'input-bindings.json')]
        for path in snapshot_paths:
            identities[str(path)] = file_record(path)
        paths.extend(snapshot_paths)
        snapshot = load_json(snapshot_paths[0])
        verification = load_json(snapshot_paths[1])
        execution = load_json(snapshot_paths[2])
        for name, identity in load_json(snapshot_paths[3]).items():
            if file_record(Path(name)) != identity:
                raise ValueError('Snapshot verification input drift')
        if (snapshot['base_commit'] != base or snapshot['exact_tree_preserved'] is not True
                or verification['tracked_manifest_matches'] is not True
                or verification['reachable_commits'] != 1
                or base not in verification['old_commits_inaccessible']
                or any(execution[key] != 0 for key in ('returncode', 'cleanup_returncode', 'copy_returncode'))
                or execution['state']['OOMKilled']):
            raise ValueError('Unqualified snapshot')
        image, base, tree = execution['image_id'], snapshot['snapshot_commit'], snapshot['source_tree']
    candidate_body = None
    if args.candidate_replay:
        replay_paths = [args.candidate_replay / name for name in ('receipt.json', 'submitted.patch')]
        paths.extend(replay_paths)
        for path in replay_paths:
            identities[str(path)] = file_record(path)
        replay = load_json(replay_paths[0])
        if resource_bindings is not None:
            resources = replay.get('session_resources', {})
            if (resources.get('bundle') != resource_bindings
                    or resources.get('adapter') != identities[str(ROOT / 'zenithsync/session_resource_replay.py')]):
                raise ValueError('Candidate replay resource environment differs from grader')
        elif replay.get('session_resources') is not None:
            raise ValueError('Resource-backed replay needs a resource-backed grader')
        if (replay['status'] != 'replayed_not_graded'
                or replay['patch'] != identities[str(replay_paths[1])]
                or replay['image'] != image
                or replay['snapshot'] != identities[str(args.snapshot / 'receipt.json')]
                or replay['workspace']['snapshot_commit'] != base
                or replay['workspace']['source_tree'] != tree
                or replay['cleanup']['removed'] is not True
                or any(replay['task'][key] != task[key] for key in
                       ('repo', 'instance_id', 'base_commit'))):
            raise ValueError('Native replay does not bind to this task and snapshot')
        candidate_body = replay_paths[1].read_bytes()
        if not 0 < len(candidate_body) <= 2 * 1024 * 1024:
            raise ValueError('Candidate patch must be nonempty and bounded')
    args.output.mkdir(parents=True, exist_ok=False)
    controls = {}
    # Replace only the fixed audited template before adding any task payload.
    # This changes evaluator working-directory literals, never task/patch bytes.
    template = PROBE.replace('/testbed', root)
    for role in (('base', 'reference', 'candidate') if candidate_body is not None
                 else ('base', 'reference')):
        patches = {'tests': base64.b64encode(task['test_patch'].encode()).decode()}
        if role == 'reference':
            patches['reference'] = base64.b64encode(task['patch'].encode()).decode()
        if role == 'candidate':
            patches['candidate'] = base64.b64encode(candidate_body).decode()
        settings = {'BASE': base, 'TREE': tree, 'ROLE': role,
            'PYTHON': profile['python'], 'MODULE': profile['module'],
            'EXPECTED_ORIGIN': profile['expected_origin'],
            'ALLOWED_PATHS': args.allowed_source_path,
            'TEST_TARGETS': targets, 'PATCHES': patches, 'PLUGIN': PLUGIN,
            'RESOURCE_PAYLOAD': '', 'RESOURCE_ADAPTER': ''}
        settings.update(SESSION_RESOURCE_PAYLOAD=resource_payload, SESSION_RESOURCE_ADAPTER=resource_adapter)
        probe = ''.join(f'{key}={value!r}\n' for key, value in settings.items()) + template
        result = run_image(image, args.output / role, probe=probe,
                           generated_grading_tests=True, entrypoint=profile['python'])
        runtime = load_json(args.output / role / 'runtime.json')
        if (any(result[key] != 0 for key in ('returncode', 'copy_returncode', 'cleanup_returncode'))
                or result['state']['OOMKilled'] or 'error' in runtime
                or runtime.get('tracked_diff_unchanged_by_tests') is not True):
            raise ValueError('Control runtime invalid; inspect retained evidence')
        controls[role] = result
    expectations = {'FAIL_TO_PASS': task['FAIL_TO_PASS'], 'PASS_TO_PASS': task['PASS_TO_PASS'],
                    'FAIL_TO_FAIL': [], 'PASS_TO_FAIL': []}
    comparison = compare_controls(load_json(args.output / 'base/outcomes.json'),
                                  load_json(args.output / 'reference/outcomes.json'), expectations,
                                  supplemental_pass_to_pass=profile.get('supplemental_pass_to_pass'))
    candidate_comparison = (compare_candidate(load_json(args.output / 'reference/outcomes.json'),
                            load_json(args.output / 'candidate/outcomes.json'))
                            if candidate_body is not None else None)
    if any(file_record(path) != identities[str(path)] for path in paths):
        raise ValueError('Qualification inputs changed')
    report = {'inputs': identities,
        'controls': controls, 'comparison': comparison, 'training_approved': False,
        'candidate_comparison': candidate_comparison,
        'allowed_source_paths': args.allowed_source_path,
        'sanitized_snapshot': args.snapshot is not None,
        'scope': 'V2 paired evaluator controls and optional native candidate grade; not model performance.'}
    if profile.get('supplemental_pass_to_pass'):
        report['supplemental_profile'] = str(args.profile)
    if resource_bindings is not None:
        report['session_resources'] = resource_bindings
        report['resource_profile'] = str(args.profile)
        report['scope'] += ' Current captured-response transport is explicit; historical equivalence and rights remain unproven.'
    (args.output / 'report.json').write_bytes(canonical_json(report))
    print({'controls': comparison, 'candidate': candidate_comparison})


if __name__ == '__main__':
    main()
