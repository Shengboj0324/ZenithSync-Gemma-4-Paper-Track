"""Native tools -> sanitized workspace -> patch -> separate source evaluator.

The edit is a random comment used only as a transport fixture, not a repair or
agent attempt. Reference solutions and generated tests never enter the agent
container. A compiler check does not invoke an LLM.
"""

import argparse
from importlib.metadata import version
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record
from zenithsync.evaluation import compare_junit
from zenithsync.source_evaluator import compare_publisher_expectations
from zenithsync.source_workspace import prepare_source_workspace


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    expected = {'google-adk': '1.36.1', 'adk-submission': '0.2.13',
                'swegemma': '0.2.10', 'adk-eval-core': '0.1.0'}
    if any(version(name) != value for name, value in expected.items()):
        raise ValueError('Pinned runtime required')
    from adk_submission import ModelRegistry, compile_submission
    from swegemma.config import build_submission_limits
    from swegemma.context import SwegemmaContext
    from swegemma.sandbox import AdkSandboxCodeExecutor, ContainerConfig, ContainerManager
    os.environ.setdefault('DOCKER_HOST', subprocess.check_output(
        ['docker', 'context', 'inspect', '--format', '{{.Endpoints.docker.Host}}'],
        text=True, timeout=15).strip())
    snapshot = 'sha256:397c5e0c8991ee3d2ab594052f66e9fd2cf2d9df45a67fd1a6445e00caf6fea1'
    resolution_path = ROOT / 'evidence/data/source-environment-resolution-001/00/result.json'
    source = json.loads(resolution_path.read_text())
    agent_manager = ContainerManager(ContainerConfig(image=snapshot, reuse_containers=False))
    evaluator_manager = ContainerManager(ContainerConfig(image=source['registry']['pinned_image'],
                                         working_dir='/testbed', reuse_containers=False))
    # Require both images already local. This probe never downloads new images.
    agent_manager.client.images.get(snapshot)
    evaluator_manager.client.images.get(source['registry']['pinned_image'])
    args.output.mkdir(parents=True, exist_ok=False)
    owned = []
    records = []
    def record(label, result):
        records.append({'label': label, 'result': result})
        (args.output / 'operations.json').write_bytes(canonical_json(records))
        return result
    try:
        cid = agent_manager.start()
        owned.append((agent_manager, cid))
        for manager, container in owned:
            attrs = manager.client.containers.get(container).attrs
            if attrs['HostConfig']['NetworkMode'] != 'none' or attrs['Mounts']:
                raise ValueError('Expected offline container without host mounts')
        snapshot_receipt = ROOT / 'evidence/data/source-snapshot-build-001/receipt.json'
        provenance = json.loads(snapshot_receipt.read_text())
        record('workspace_setup', prepare_source_workspace(agent_manager, cid,
            snapshot_commit=provenance['snapshot_commit'], source_tree=provenance['source_tree']))
        ctx = SwegemmaContext(docker_manager=agent_manager, container_id=cid,
            task_id=source['instance_id'], repo=source['repo'], max_tool_calls=20,
            max_time_minutes=5, max_exec_seconds=30,
            graph_dir='/nonexistent-fixture', embeddings_dir='/nonexistent-fixture')
        ctx.start_agent_session()
        executor = AdkSandboxCodeExecutor(sandbox=ctx.sandbox, timeout_seconds=30,
                                         budget_check_fn=ctx.check_budget)
        tools = ctx.create_tools()
        models = ModelRegistry()
        model = 'gemma-4-31b-it-qat-w4a16-ct'
        models.register(model, model)
        limits, generation = build_submission_limits()
        agent = compile_submission(ROOT / 'candidates/p1-base', tool_registry=tools,
            model_registry=models, code_executor=executor, limits=limits,
            generation_constraints=generation)
        imported = record('native_dependency_import', tools['run_command'](command=
            '.venv/bin/python -c "import pathlib,pyramid; '
            'print(pathlib.Path(pyramid.__file__).resolve())"'))
        if imported['status'] != 'ok' or imported['stdout'].strip() != '/workspace/pyramid/__init__.py':
            raise ValueError('Relocated runtime does not import from agent workspace')
        empty = record('empty_patch', tools['submit_patch']())
        if empty['status'] != 'ok' or ctx.submitted_patch.strip():
            raise ValueError('Untouched workspace exports a nonempty patch')
        read = record('read_source', tools['read_file'](filepath='pyramid/__init__.py'))
        if read['status'] != 'ok' or read['is_truncated']:
            raise ValueError('Native read must return complete fixture source')
        content = read['content']
        anchor = next((line for line in content.splitlines() if line and content.count(line) == 1), None)
        if anchor is None:
            raise ValueError('No unique source anchor for transport fixture')
        marker = '# transport-only fixture ' + uuid.uuid4().hex
        changed = record('edit_source', tools['edit_file'](filepath='pyramid/__init__.py',
            old_string=anchor, new_string=marker + '\n' + anchor))
        if changed['status'] != 'ok':
            raise ValueError('Native edit failed')
        submitted = record('submit_patch', tools['submit_patch']())
        patch = ctx.submitted_patch
        if submitted['status'] != 'ok' or patch.count('diff --git ') != 1 or marker not in patch:
            raise ValueError('Patch does not contain exactly the transport fixture')
        if not patch.startswith('diff --git a/pyramid/__init__.py b/pyramid/__init__.py\n'):
            raise ValueError('Unexpected patch path')
        patch_path = args.output / 'transport.patch'
        patch_path.write_text(patch)
        agent_manager.copy_from(cid, '/workspace/pyramid/__init__.py', args.output / 'agent-source.py')
        absence = agent_manager.exec(cid,
            'test ! -e /r2e_tests && ! git cat-file -e '
            + source['instance_id'].rsplit('-', 1)[-1] + '^{commit}')
        record('known_oracles_absent', {'exit': absence.exit_code})
        if absence.exit_code != 0:
            raise ValueError('Known oracle accessible to agent container')
        eid = evaluator_manager.start()
        owned.append((evaluator_manager, eid))
        attrs = evaluator_manager.client.containers.get(eid).attrs
        if attrs['HostConfig']['NetworkMode'] != 'none' or attrs['Mounts']:
            raise ValueError('Evaluator must be separate and offline without host mounts')
        head = evaluator_manager.exec(eid, 'git rev-parse HEAD')
        if head.exit_code != 0 or head.stdout.strip() != source['git']['base_commit']:
            raise ValueError('Evaluator starting revision mismatch')
        evaluator_manager.copy_to(eid, patch_path, '/tmp/transport.patch')
        applied = evaluator_manager.exec(eid, 'git apply --check /tmp/transport.patch && git apply /tmp/transport.patch')
        record('apply_patch', {'exit': applied.exit_code, 'stderr': applied.stderr})
        if applied.exit_code != 0:
            raise ValueError('Native patch cannot apply to evaluator base')
        staged = evaluator_manager.exec(eid, 'cp /testbed/pyramid/__init__.py /tmp/evaluator-source.py')
        if staged.exit_code != 0:
            raise ValueError('Evaluator source comparison export failed')
        evaluator_manager.copy_from(eid, '/tmp/evaluator-source.py', args.output / 'evaluator-source.py')
        if file_record(args.output / 'agent-source.py') != file_record(args.output / 'evaluator-source.py'):
            raise ValueError('Transferred patch produced different evaluator bytes')
        tested = evaluator_manager.exec(eid,
            '.venv/bin/python -m pytest -q -p no:cacheprovider /r2e_tests --junitxml=/tmp/junit.xml', timeout=240)
        (args.output / 'tests.stdout').write_text(tested.stdout)
        (args.output / 'tests.stderr').write_text(tested.stderr)
        evaluator_manager.copy_from(eid, '/tmp/junit.xml', args.output / 'junit.xml')
        paired = compare_junit(ROOT / 'evidence/data/source-evaluator-controls-001/base/junit.xml',
                               args.output / 'junit.xml')
        if paired['changed_cases']:
            raise ValueError('Comment transport fixture changed evaluator outcomes')
        expected_path = ROOT / 'evidence/data/source-expectations-001/publisher-expected.json'
        score = compare_publisher_expectations(args.output / 'junit.xml', json.loads(expected_path.read_text()))
        receipt = {'schema_version': 1, 'status': 'native_patch_transport_verified',
            'versions': expected, 'agent_name': agent.name, 'tool_calls': ctx.tool_calls_used,
            'model_invoked': False, 'training_approved': False, 'patch': file_record(patch_path),
            'resolution': file_record(resolution_path), 'expected': file_record(expected_path),
            'snapshot_image': snapshot, 'evaluator_image': source['registry']['pinned_image'],
            'comparison': paired, 'score': score, 'pytest_exit': tested.exit_code,
            'probe': file_record(Path(__file__)),
            'workspace_adapter': file_record(ROOT / 'zenithsync/source_workspace.py'),
            'snapshot_provenance': file_record(snapshot_receipt),
            'scope': 'Random comment transport through native tools; no repair capability or trajectory qualification'}
        (args.output / 'receipt.json').write_bytes(canonical_json(receipt))
    except Exception as error:
        (args.output / 'failure.json').write_bytes(canonical_json({'type': type(error).__name__, 'message': str(error)}))
        raise
    finally:
        cleanup = []
        for manager, container in reversed(owned):
            manager.stop(container)
            cleanup.append({'id': container, 'removed': not manager.client.containers.list(all=True, filters={'id': container})})
        (args.output / 'cleanup.json').write_bytes(canonical_json(cleanup))
        if not all(item['removed'] for item in cleanup):
            raise RuntimeError('Owned transport container remains')
    print('Native patch transport and unchanged evaluator outcomes verified')


if __name__ == '__main__':
    main()
