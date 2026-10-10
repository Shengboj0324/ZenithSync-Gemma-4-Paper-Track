"""Replay a hash-reviewed mini source trace, with explicit native cleanup."""
import argparse
from importlib.metadata import version
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record, load_json
from zenithsync.container_cleanup import cleanup_owned_container
from zenithsync.source_workspace import prepare_source_workspace
from zenithsync.conversation import normalize_history
from zenithsync.submission_reconciliation import scratch_cleanup_command
from zenithsync.session_resource_bundle import (
    DIRECTORY as SESSION_RESOURCE_DIRECTORY, load_session_resource_bundle, stage_session_resources)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--profile', type=Path, required=True)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--session-resources', type=Path,
                        help='Explicitly profile-bound current-response bundle; admission still requires resource review')
    args = parser.parse_args()
    profile = load_json(args.profile)
    candidate_identity = file_record(args.candidate)
    required_profile = {'candidate', 'scratch_paths', 'terminal_command', 'source_root', 'python'}
    expected_profile = required_profile | ({'session_resources'} if args.session_resources else set())
    if set(profile) != expected_profile:
        raise ValueError('Exact reviewed source replay profile required')
    resource_bindings = None
    if args.session_resources:
        resource_review = profile['session_resources']
        if not isinstance(resource_review, dict) or set(resource_review) != {'receipt', 'max_bytes'}:
            raise ValueError('Exact reviewed resource identity and budget required')
        _, resource_bindings = load_session_resource_bundle(
            args.session_resources, max_bytes=resource_review['max_bytes'])
        if resource_bindings['files']['receipt.json'] != resource_review['receipt']:
            raise ValueError('Resource bundle differs from reviewed profile')
    if candidate_identity != profile['candidate']:
        raise ValueError('Source candidate differs from reviewed bytes')
    candidate = load_json(args.candidate)
    task = candidate['task_metadata']
    official = load_json(ROOT / 'evidence/p1/task-index-001/receipt.json')
    if task['repo'].casefold() in {name.casefold() for name in official['repo_counts']}:
        raise ValueError('Reserved repository excluded')
    messages = normalize_history(candidate['messages'], allowed_tools={'bash'}, allow_pending=True)
    commands = []
    for index, message in enumerate(messages):
        for call in message.get('tool_calls', []):
            arguments = call['function']['arguments']
            if set(arguments) != {'command'} or not isinstance(arguments['command'], str):
                raise ValueError('Unreviewed source call arguments')
            commands.append({'source_index': index, 'command': arguments['command']})
    if not commands or commands[-1]['command'] != profile['terminal_command']:
        raise ValueError('Source terminal differs from reviewed profile')
    if profile['terminal_command'] not in (
            'echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && cat patch.txt',
            'echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && cat /testbed/patch.txt'):
        raise ValueError('Unsupported source patch-export protocol')
    if len(commands) > 40:
        raise ValueError('Source replay exceeds qualification call ceiling')
    snapshot = load_json(args.snapshot / 'snapshot.json')
    verification = load_json(args.snapshot / 'verification.json')
    run = load_json(args.snapshot / 'receipt.json')
    for name, identity in load_json(args.snapshot / 'input-bindings.json').items():
        if file_record(Path(name)) != identity:
            raise ValueError('Snapshot verification input drift')
    if (snapshot['base_commit'] != task['base_commit'] or not snapshot['exact_tree_preserved']
            or verification['tracked_manifest_matches'] is not True
            or verification['reachable_commits'] != 1
            or any(run[key] != 0 for key in ('returncode', 'copy_returncode', 'cleanup_returncode'))):
        raise ValueError('Unqualified source snapshot')
    for package, expected in {'swegemma': '0.2.10', 'adk-submission': '0.2.13',
                              'google-adk': '1.36.1', 'adk-eval-core': '0.1.0'}.items():
        if version(package) != expected:
            raise ValueError('Pinned native runtime required')
    from swegemma.context import SwegemmaContext
    from swegemma.sandbox import ContainerConfig, ContainerManager
    os.environ.setdefault('DOCKER_HOST', subprocess.check_output(
        ['docker', 'context', 'inspect', '--format', '{{.Endpoints.docker.Host}}'],
        text=True, timeout=15).strip())
    environment = {'PYTHONDONTWRITEBYTECODE': '1', 'TEST_TMPDIR': '/tmp',
        'PIP_CACHE_DIR': '/opt/zenithsync/runtime-cache/pip',
        'PYTHONPYCACHEPREFIX': '/opt/zenithsync/runtime-cache/pycache',
        'XDG_CACHE_HOME': '/opt/zenithsync/runtime-cache'}
    if resource_bindings is not None:
        environment['PYTHONPATH'] = SESSION_RESOURCE_DIRECTORY
    manager = ContainerManager(ContainerConfig(image=run['image_id'], reuse_containers=False,
                                               environment=environment))
    sources = {name: file_record(ROOT / name) for name in (
        'scripts/replay_mini_source.py', 'zenithsync/source_workspace.py',
        'zenithsync/session_resource_bundle.py', 'zenithsync/session_resource_replay.py',
        'zenithsync/submission_reconciliation.py', 'zenithsync/artifacts.py', 'zenithsync/contracts.py')}
    args.output.mkdir(parents=True, exist_ok=False)
    receipt = {'status': 'incomplete', 'candidate': candidate_identity,
        'profile': file_record(args.profile), 'snapshot': file_record(args.snapshot / 'receipt.json'),
        'image': run['image_id'], 'task': task, 'sources': sources, 'training_approved': False,
        'source_observations_reused': False, 'model_executed': False,
        'standalone_cleanup': True, 'injected_support_modules': False,
        'adaptation': 'Source terminal replaced by adapter-authored cleanup and native submit_patch; source commands otherwise unchanged',
        'environment': environment}
    cid = None
    events = []
    try:
        cid = manager.start()
        container = manager.client.containers.get(cid)
        if container.attrs['HostConfig']['NetworkMode'] != 'none' or container.attrs['Mounts']:
            raise ValueError('Offline unmounted container required')
        if resource_bindings is not None:
            staged = stage_session_resources(manager, cid, args.session_resources,
                ROOT / 'zenithsync/session_resource_replay.py', max_bytes=resource_review['max_bytes'])
            if staged['bundle'] != resource_bindings:
                raise ValueError('Resource bundle changed before staging')
            receipt['session_resources'] = staged
            receipt['injected_support_modules'] = True
        receipt['workspace'] = prepare_source_workspace(manager, cid,
            snapshot_commit=snapshot['snapshot_commit'], source_tree=snapshot['source_tree'],
            installer_leftover=False, source_root=profile['source_root'], preserve_workspace_cache=True)
        ctx = SwegemmaContext(docker_manager=manager, container_id=cid,
            task_id=candidate['source_metadata']['trajectory_id'], repo=task['repo'],
            max_tool_calls=40, max_time_minutes=10, max_exec_seconds=30,
            graph_dir='/nonexistent-fixture', embeddings_dir='/nonexistent-fixture')
        ctx.start_agent_session()
        tools = ctx.create_tools()

        def invoke(name, arguments, *, source_index=None, adapter_authored=False):
            result = tools[name](**arguments)
            events.append({'source_index': source_index, 'adapter_authored': adapter_authored,
                           'name': name, 'arguments': arguments, 'result': result})
            (args.output / 'events.json').write_bytes(canonical_json(events))
            print({'event': len(events), 'tool': name, 'status': result['status']}, flush=True)
            return result

        for row in commands[:-1]:
            invoke('run_command', {'command': row['command']}, source_index=row['source_index'])
        exported = manager.exec(cid, 'cat /workspace/patch.txt', timeout=10)
        if exported.exit_code or not exported.stdout or len(exported.stdout.encode()) > 2 * 1024**2:
            raise ValueError('Missing or invalid intended patch export')
        (args.output / 'intended.patch').write_text(exported.stdout)
        command = scratch_cleanup_command(python=profile['python'],
            scratch_paths=profile['scratch_paths'])
        result = invoke('run_command', {'command': command}, adapter_authored=True)
        if result['status'] != 'ok':
            raise ValueError('Explicit scratch cleanup failed')
        result = invoke('submit_patch', {}, adapter_authored=True)
        if result['status'] != 'ok' or ctx.submitted_patch != exported.stdout:
            raise ValueError('Native submission differs from source intended patch')
        (args.output / 'submitted.patch').write_text(ctx.submitted_patch)
        receipt.update(status='replayed_not_graded', tool_calls=ctx.tool_calls,
            patch=file_record(args.output / 'submitted.patch'), intended_patch=file_record(args.output / 'intended.patch'),
            native_submission_equals_source_export=True)
        if file_record(args.candidate) != candidate_identity or any(
                file_record(ROOT / name) != identity for name, identity in sources.items()):
            raise ValueError('Replay source changed during execution')
    except Exception as error:
        receipt.update(status='failed', error_type=type(error).__name__)
        raise
    finally:
        if cid is not None:
            receipt['cleanup'] = cleanup_owned_container(manager, cid)
        (args.output / 'receipt.json').write_bytes(canonical_json(receipt))
    if receipt['cleanup']['removed'] is not True:
        raise ValueError('Container cleanup unconfirmed')


if __name__ == '__main__':
    main()
