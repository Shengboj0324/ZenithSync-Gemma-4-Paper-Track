"""Bounded external-task rollout using native tools; dry-run unless --execute.

This source-image runner uses ADK directly, not the official snapshot installer.
It records an attempt only. Independent grading and training admission follow.
"""

import argparse
import asyncio
from datetime import datetime, timezone
from importlib.metadata import version
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('LITELLM_LOCAL_MODEL_COST_MAP', 'True')
os.environ.setdefault('OTEL_SDK_DISABLED', 'true')
from zenithsync.artifacts import canonical_json, file_record, load_json, verify
from zenithsync.harness_context import competition_context_configs
from zenithsync.source_workspace import prepare_source_workspace
from zenithsync.task_intake import AGENT_FIELDS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--execute', action='store_true')
    mode.add_argument('--fixture', choices=['success', 'submit-then-fail', 'timeout', 'turn-limit'])
    parser.add_argument('--session', type=Path)
    parser.add_argument('--port', type=int, default=18000)
    args = parser.parse_args()
    versions = {'swegemma': '0.2.10', 'adk-submission': '0.2.13',
                'google-adk': '1.36.1', 'adk-eval-core': '0.1.0'}
    if any(version(k) != v for k, v in versions.items()):
        raise ValueError('Pinned SDK and harness required')
    if not 1024 <= args.port <= 65535:
        raise ValueError('Invalid loopback port')
    manifest = load_json(args.manifest)
    verify(args.package, manifest)
    task_data = load_json(args.package / 'agent/task.json')
    if set(task_data) != set(AGENT_FIELDS):
        raise ValueError('Agent task must contain only allowlisted fields')
    workspace = load_json(args.package / 'workspace.json')
    if workspace['adapter'] != file_record(ROOT / 'zenithsync/source_workspace.py'):
        raise ValueError('Workspace adapter changed; requalify package')
    candidate = ROOT / 'candidates/p1-base'
    candidate_manifest = load_json(ROOT / 'evidence/p1/base-agent-001/manifest.json')
    verify(candidate, candidate_manifest)
    deadline = None
    if args.execute:
        if args.session is None:
            raise ValueError('Explicit approved session record required for model execution')
        deadline = datetime.fromisoformat(load_json(args.session)['validation_deadline_utc'])
        if deadline.tzinfo is None or (deadline - datetime.now(timezone.utc)).total_seconds() < 1200:
            raise ValueError('Insufficient approved session time')
    import yaml
    from adk_submission import ModelRegistry
    from adk_submission.yaml_loader import load_yaml
    from swegemma.config import EvalConfig
    from swegemma.models import Task
    from swegemma.harness.agent_runner import build_agent_prompt
    budget = yaml.safe_load((candidate / 'eval_config.yaml').read_text())['evaluation']
    if budget != {'timeout_seconds': 120, 'max_tool_calls': 40, 'max_time_minutes': 10, 'max_turns': 40}:
        raise ValueError('Candidate budgets require requalification')
    task = Task(**task_data)
    dry_models = ModelRegistry()
    alias = 'gemma-4-31b-it-qat-w4a16-ct'
    dry_models.register(alias, alias)
    config = EvalConfig(tasks_path=args.package / 'agent/task.json', results_dir=args.output,
                       snapshots_dir=args.package / 'agent', models=dry_models,
                       image=workspace['image'], submission_dir=candidate,
                       **competition_context_configs(), **budget)
    prompt = build_agent_prompt(task=task, config=config, workspace_tree='',
                               enable_sandbox_testing=True,
                               declared_tools=set(load_yaml(candidate / 'agent.yaml', root_dir=candidate)['tools']))
    args.output.mkdir(parents=True, exist_ok=False)
    plan = {'schema_version': 1, 'status': 'prepared_not_executed', 'versions': versions,
            'agent_task': file_record(args.package / 'agent/task.json'),
            'package_manifest': file_record(args.manifest), 'workspace': workspace,
            'budgets': budget, 'script': file_record(Path(__file__)),
            'endpoint': f'http://127.0.0.1:{args.port}/v1',
            'runner_mode': 'Single ADK invocation; no official outer-loop nudges or retry plugins',
            'execution_path_qualified': False,
            'fixture': args.fixture, 'training_approved': False,
            'scope': 'One external development task; evaluator files excluded from model input'}
    (args.output / 'prompt.txt').write_text(prompt)
    (args.output / 'plan.json').write_bytes(canonical_json(plan))
    if not args.execute and not args.fixture:
        print('Task prompt and bounded rollout plan verified; no container or model started')
        return
    from adk_submission import compile_submission
    from google.adk.apps import App
    from google.adk.runners import Runner
    from google.adk.agents.run_config import RunConfig
    from google.adk.sessions import InMemorySessionService
    from google.genai import types
    from swegemma.config import build_submission_limits
    from swegemma.context import SwegemmaContext
    from swegemma.models.registry import setup_gemma_model_registry
    from swegemma.sandbox import AdkSandboxCodeExecutor, ContainerConfig, ContainerManager
    os.environ.setdefault('DOCKER_HOST', subprocess.check_output(
        ['docker', 'context', 'inspect', '--format', '{{.Endpoints.docker.Host}}'], text=True, timeout=15).strip())
    manager = ContainerManager(ContainerConfig(image=workspace['image'], reuse_containers=False))
    manager.client.images.get(workspace['image'])
    cid = None
    ctx = None
    async def attempt():
        if args.fixture:
            from zenithsync.source_runner_fixture import SourceRunnerFixture
            fixture = SourceRunnerFixture(model='explicit-offline-fixture', scenario=args.fixture)
            fixture.retain_to(args.output / 'fixture-requests.json')
            models = ModelRegistry()
            models.register(alias, fixture)
            plan['fixture_implementation'] = file_record(ROOT / 'zenithsync/source_runner_fixture.py')
        else:
            models = setup_gemma_model_registry(api_base=plan['endpoint'], api_key='EMPTY',
                num_retries=0, served_model=alias)
        executor = AdkSandboxCodeExecutor(sandbox=ctx.sandbox, timeout_seconds=120,
                                         budget_check_fn=ctx.check_budget)
        limits, generation = build_submission_limits()
        agent = compile_submission(candidate, tool_registry=ctx.create_tools(), model_registry=models,
                                   code_executor=executor, limits=limits, generation_constraints=generation)
        service = InMemorySessionService()
        app = App(name='source_development', root_agent=agent, **competition_context_configs())
        runner = Runner(app=app, session_service=service)
        session = await service.create_session(app_name=app.name, user_id='development',
                                              state={'problem_description': task.problem_statement})
        remaining = (1.0 if args.fixture == 'timeout' else 600) if args.fixture else (
            deadline - datetime.now(timezone.utc)).total_seconds() - 30
        plan['effective_timeout_seconds'] = min(600, remaining)
        if remaining <= 0:
            raise ValueError('No execution time remains after cleanup reserve')
        ctx.start_agent_session()
        async with asyncio.timeout(min(600, remaining)):
            with (args.output / 'events.jsonl').open('wb') as stream:
                async for event in runner.run_async(user_id='development', session_id=session.id,
                        new_message=types.Content(role='user', parts=[types.Part(text=prompt)]),
                        run_config=RunConfig(max_llm_calls=40)):
                    ctx.handle_adk_event(event, agent_name=agent.name)
                    stream.write(canonical_json(event.model_dump(mode='json')))
                    stream.flush()
        return ctx.submitted_patch or ''
    try:
        cid = manager.start()
        attrs = manager.client.containers.get(cid).attrs
        if attrs['Mounts'] or attrs['HostConfig']['NetworkMode'] != 'none':
            raise ValueError('Agent container isolation settings differ')
        prepare_source_workspace(manager, cid, snapshot_commit=workspace['snapshot_commit'], source_tree=workspace['source_tree'])
        ctx = SwegemmaContext(docker_manager=manager, container_id=cid, task=task,
            repo=task.repo, graph_dir='/unavailable-source-graphs', embeddings_dir='/unavailable-source-embeddings',
            budget=config.budget, harness=config.harness)
        patch = asyncio.run(attempt())
        (args.output / 'agent.patch').write_text(patch)
        plan.update(status='attempt_recorded_not_graded', patch_submitted=ctx.patch_submitted,
                    patch=file_record(args.output / 'agent.patch'))
    except Exception as error:
        if ctx is not None:
            (args.output / 'agent.patch').write_text(ctx.submitted_patch or '')
        plan.update(status='attempt_failed_not_graded', error_type=type(error).__name__, error=str(error))
        raise
    finally:
        if ctx is not None:
            plan.update(patch_submitted=ctx.patch_submitted, tool_calls=ctx.tool_calls_used,
                        llm_calls=ctx.llm_calls_used)
        if (args.output / 'agent.patch').exists():
            plan['patch'] = file_record(args.output / 'agent.patch')
        if cid is not None:
            manager.stop(cid)
            plan['container_removed'] = not manager.client.containers.list(all=True, filters={'id': cid})
        (args.output / 'receipt.json').write_bytes(canonical_json(plan))
        if plan.get('container_removed') is False:
            raise RuntimeError('Owned source-task container remains after cleanup')
    verify(args.package, manifest)
    verify(candidate, candidate_manifest)


if __name__ == '__main__':
    main()
