"""Exercise source-observation skill via released executor in an owned offline container."""
import argparse
import asyncio
from importlib.metadata import version
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record, inventory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    expected = {'google-adk': '1.36.1', 'adk-submission': '0.2.13',
                'swegemma': '0.2.10', 'adk-eval-core': '0.1.0'}
    if any(version(name) != value for name, value in expected.items()):
        raise ValueError('Pinned runtime required')
    from adk_submission import ModelRegistry, compile_submission
    from google.adk.skills import load_skill_from_dir
    from google.adk.tools.skill_toolset import _SkillScriptCodeExecutor
    from swegemma.config import build_submission_limits
    from swegemma.context import SwegemmaContext
    from swegemma.sandbox import AdkSandboxCodeExecutor, ContainerConfig, ContainerManager
    os.environ.setdefault('DOCKER_HOST', subprocess.check_output(
        ['docker', 'context', 'inspect', '--format', '{{.Endpoints.docker.Host}}'],
        text=True, timeout=15).strip())
    image = 'sha256:14d857d591be7d1a7efc83ff1dcc87f83c96c764895b0986a45db0d8af5a8a46'
    manager = ContainerManager(ContainerConfig(image=image, reuse_containers=False))
    if manager.client.images.get(image).id != image:
        raise ValueError('Pinned local image required; no image download authorized by this probe')
    args.output.mkdir(parents=True, exist_ok=False)
    cid = None
    records = []
    candidate = ROOT/'candidates/p1-observation-memory'
    def retain():
        (args.output/'operations.json').write_bytes(canonical_json(records))
    try:
        cid = manager.start()
        container = manager.client.containers.get(cid)
        config = container.attrs['HostConfig']
        if config['NetworkMode'] != 'none' or config['Memory'] != 4 * 1024**3 or config['CpuQuota'] != 200000:
            raise AssertionError('Expected offline 4 GiB / 2 CPU container')
        if container.attrs['Mounts']:
            raise AssertionError('Probe container must not mount host paths')
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'module.py'
            path.write_text('value = "α"\nreturn_value = value\n')
            manager.copy_to(cid, path, '/workspace/module.py')
        initialized = manager.exec(cid, 'git init -q && git add module.py && git -c user.name=Fixture -c user.email=fixture@example.invalid commit -qm baseline && git tag _swegemma_baseline')
        if initialized.exit_code != 0:
            raise AssertionError(initialized.stderr)
        ctx = SwegemmaContext(docker_manager=manager, container_id=cid,
            task_id='synthetic-observation-test', repo='synthetic/observation',
            max_tool_calls=40, max_time_minutes=3, max_exec_seconds=20,
            graph_dir='/nonexistent-fixture', embeddings_dir='/nonexistent-fixture')
        ctx.start_agent_session()
        executor = AdkSandboxCodeExecutor(sandbox=ctx.sandbox, timeout_seconds=20,
                                         budget_check_fn=ctx.check_budget)
        tools = ctx.create_tools()
        models = ModelRegistry()
        model = 'gemma-4-31b-it-qat-w4a16-ct'
        models.register(model, model)
        limits, generation = build_submission_limits()
        agent = compile_submission(candidate, tool_registry=tools, model_registry=models,
            code_executor=executor, limits=limits, generation_constraints=generation)
        skill = load_skill_from_dir(candidate/'skills/source-observations')
        helper = _SkillScriptCodeExecutor(executor, 20)
        def invoke(arguments):
            result = asyncio.run(helper.execute_script_async(None, skill,
                'scripts/observe.py', arguments))
            records.append({'arguments': arguments, 'result': result})
            retain()
            if result.get('status') != 'success':
                raise AssertionError('Skill execution failed; see retained operation')
            return json.loads(result['stdout'])
        captured = invoke(['snapshot', '--path', 'module.py', '--start', '1', '--end', '1'])
        if not captured['handle'].startswith('/tmp/'):
            raise AssertionError('Observation must be stored outside workspace')
        recalled = invoke(['recall', '--handle', captured['handle']])
        if recalled['status'] != 'current_source_match' or recalled['record']['excerpt'] != 'value = "α"\n':
            raise AssertionError('Exact source recovery failed')
        clean = manager.exec(cid, 'git status --porcelain --untracked-files=all')
        if clean.exit_code != 0 or clean.stdout.strip():
            raise AssertionError('Memory or executor artifacts leaked into repository')
        changed = tools['write_file'](filepath='module.py', content='value = "α"\nreturn_value = None\n')
        if changed['status'] != 'ok':
            raise AssertionError('Actual workspace edit failed')
        stale = invoke(['recall', '--handle', captured['handle']])
        if stale['status'] != 'stale' or 'record' in stale:
            raise AssertionError('Stale source accepted')
        submitted = tools['submit_patch']()
        if submitted['status'] != 'ok':
            raise AssertionError('Official patch extraction failed')
        patch = ctx.submitted_patch
        if patch.count('diff --git ') != 1 or 'diff --git a/module.py b/module.py' not in patch:
            raise AssertionError('Unexpected patch file set')
        if '.adk_exec_' in patch or 'zenithsync-observation' in patch:
            raise AssertionError('Memory infrastructure leaked into patch')
        (args.output/'candidate.patch').write_text(patch)
        receipt = {'schema_version': 1, 'status': 'offline_sandbox_observation_recovery_passed',
            'versions': expected, 'image': image, 'agent_name': agent.name,
            'network_mode': config['NetworkMode'], 'host_mounts': [],
            'checks': ['real bound tools and candidate compiler', 'actual ADK script materialization and executor',
                       'exact UTF-8 recall in separate sandbox processes', 'no workspace artifacts before edit',
                       'stale source invalidated', 'official submit_patch contains only intended source edit'],
            'scope': 'Owned synthetic Docker sandbox; deterministic script calls, no model selection, '
                     'compaction handle retention, repair performance, subprocess backend or hidden-grader qualification',
            'probe': file_record(Path(__file__)), 'operations': file_record(args.output/'operations.json'),
            'patch': file_record(args.output/'candidate.patch')}
        (args.output/'candidate-manifest.json').write_bytes(canonical_json(inventory(candidate,
            kind='candidate', source='Experimental source-observation recovery', revision='untrained-001')))
        (args.output/'receipt.json').write_bytes(canonical_json(receipt))
    except Exception as exc:
        (args.output/'failure.json').write_bytes(canonical_json({'type': type(exc).__name__, 'message': str(exc)}))
        raise
    finally:
        if cid is not None:
            manager.stop(cid)
            remains = manager.client.containers.list(all=True, filters={'id': cid})
            (args.output/'cleanup.json').write_bytes(canonical_json({'created_container': cid, 'removed': not remains}))
            if remains:
                raise RuntimeError('Owned probe container remains after cleanup')
    print('Actual offline sandbox recovery, staleness and patch-exclusion checks passed')


if __name__ == '__main__':
    main()
