"""Controlled runner + Docker recovery integration; scripted model, not learned performance."""
import argparse
import asyncio
from importlib.metadata import version
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record
from zenithsync.harness_context import competition_context_configs

HANDLE = re.compile(r'/tmp/zenithsync-observation-[A-Za-z0-9_\-]+/[0-9a-f]{64}\.json')


async def run_case(manager, retain_handle, output):
    from adk_submission import ModelRegistry, compile_submission
    from google.adk.apps import App
    from google.adk.models.base_llm import BaseLlm
    from google.adk.models.llm_response import LlmResponse
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types
    from swegemma.config import build_submission_limits
    from swegemma.context import SwegemmaContext
    from swegemma.sandbox import AdkSandboxCodeExecutor
    cid = manager.start()
    requests, events = [], []
    source_text = 'value = "' + uuid.uuid4().hex + '"\n'
    main_calls = 0
    recalled_payload = None
    try:
        container = manager.client.containers.get(cid)
        host = container.attrs['HostConfig']
        if host['NetworkMode'] != 'none' or container.attrs['Mounts']:
            raise AssertionError('Expected offline container without host mounts')
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp)/'module.py'
            file.write_text(source_text)
            manager.copy_to(cid, file, '/workspace/module.py')
        initialized = manager.exec(cid, 'git init -q && git add module.py && git -c user.name=Fixture -c user.email=fixture@example.invalid commit -qm baseline')
        if initialized.exit_code:
            raise AssertionError(initialized.stderr)
        ctx = SwegemmaContext(docker_manager=manager, container_id=cid,
            task_id='synthetic-recovery', repo='synthetic/recovery', max_tool_calls=40,
            max_time_minutes=3, max_exec_seconds=20, graph_dir='/missing', embeddings_dir='/missing')
        ctx.start_agent_session()
        class ScriptedModel(BaseLlm):
            async def generate_content_async(self, request, stream=False):
                nonlocal main_calls, recalled_payload
                snapshot = request.model_dump(mode='json', exclude_none=True)
                first = request.contents[0].parts[0].text or ''
                is_summary = first.startswith('The following is a conversation history')
                requests.append({'kind': 'summary' if is_summary else 'agent', 'request': snapshot})
                if is_summary:
                    handles = sorted(set(HANDLE.findall(first))) if retain_handle else []
                    parts = [types.Part(text='SYNTHETIC_SUMMARY ' + ' '.join(handles))]
                else:
                    main_calls += 1
                    if main_calls > 10:
                        raise AssertionError('Unexpected loop')
                    args = None
                    if main_calls == 1:
                        args = {'skill_name': 'source-observations', 'file_path': 'scripts/observe.py',
                                'args': ['snapshot', '--path', 'module.py', '--start', '1', '--end', '1']}
                        tool = 'run_skill_script'
                        parts = []
                    elif main_calls <= 8:
                        tool = 'run_command'
                        args = {'command': 'printf distraction'}
                        parts = []
                        if main_calls == 2:
                            # Echo only a handle actually present in this request, never a saved oracle.
                            handles = HANDLE.findall(canonical_json(snapshot).decode())
                            if not handles:
                                raise AssertionError('Snapshot handle missing from tool response')
                            parts = [types.Part(text='Saved source handle: ' + handles[-1])]
                    elif main_calls == 9:
                        serialized = canonical_json(snapshot).decode()
                        if source_text.strip() in serialized or uuid_value in serialized:
                            raise AssertionError('Original source observation has not left active context')
                        handles = HANDLE.findall(serialized)
                        parts = []
                        if handles:
                            tool = 'run_skill_script'
                            args = {'skill_name': 'source-observations', 'file_path': 'scripts/observe.py',
                                    'args': ['recall', '--handle', handles[-1]]}
                        else:
                            parts = [types.Part(text='SYNTHETIC_STOP_MISSING_HANDLE')]
                    else:
                        for content in request.contents:
                            for part in content.parts or []:
                                response = part.function_response
                                if response and response.name == 'run_skill_script':
                                    value = response.response
                                    if value.get('stdout'):
                                        parsed = json.loads(value['stdout'])
                                        if parsed.get('status') == 'current_source_match':
                                            recalled_payload = parsed
                        parts = [types.Part(text='SYNTHETIC_RECOVERY_CHECK_COMPLETE')]
                    if args is not None:
                        parts.append(types.Part(function_call=types.FunctionCall(
                            name=tool, args=args, id=f'call_{main_calls}')))
                yield LlmResponse(content=types.Content(role='model', parts=parts),
                    usage_metadata=types.GenerateContentResponseUsageMetadata(
                        prompt_token_count=14336, candidates_token_count=1, total_token_count=14337))
        uuid_value = source_text.split('"')[1]
        models = ModelRegistry()
        models.register('gemma-4-31b-it-qat-w4a16-ct', ScriptedModel(model='offline-fixture'))
        executor = AdkSandboxCodeExecutor(sandbox=ctx.sandbox, timeout_seconds=20, budget_check_fn=ctx.check_budget)
        limits, generation = build_submission_limits()
        agent = compile_submission(ROOT/'candidates/p1-observation-memory', tool_registry=ctx.create_tools(),
            model_registry=models, code_executor=executor, limits=limits, generation_constraints=generation)
        app = App(name='recovery_probe', root_agent=agent, **competition_context_configs())
        service = InMemorySessionService()
        await service.create_session(app_name=app.name, user_id='fixture', session_id='fixture')
        runner = Runner(app=app, session_service=service)
        async for event in runner.run_async(user_id='fixture', session_id='fixture',
            new_message=types.Content(role='user', parts=[types.Part(text='Offline recovery fixture')])):
            ctx.handle_adk_event(event, agent_name=agent.name)
            events.append(event.model_dump(mode='json', exclude_none=True))
        recovered = recalled_payload is not None and recalled_payload['record']['excerpt'] == source_text
        if recovered != retain_handle:
            raise AssertionError('Unexpected controlled recovery outcome')
        clean = manager.exec(cid, 'git status --porcelain --untracked-files=all')
        if clean.exit_code or clean.stdout.strip():
            raise AssertionError('Memory operations changed repository')
        skill_calls = sum(call['name'] == 'run_skill_script' for event in events
            for part in event.get('content', {}).get('parts', [])
            if (call := part.get('function_call')))
        result = {'retain_handle_in_synthetic_summary': retain_handle, 'recovered_exact_source': recovered,
                  'agent_requests': main_calls, 'summary_requests': sum(r['kind'] == 'summary' for r in requests),
                  'skill_calls': skill_calls, 'harness_tool_calls_used': ctx.tool_calls_used,
                  'requests': requests, 'events': events}
        if ctx.tool_calls_used != 7 + skill_calls:
            raise AssertionError('Unexpected accounting for seven shell calls plus skill executions')
        return result
    finally:
        output.write_bytes(canonical_json({'requests': requests, 'events': events}))
        manager.stop(cid)
        if manager.client.containers.list(all=True, filters={'id': cid}):
            raise RuntimeError('Owned container remains')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    expected = {'google-adk': '1.36.1', 'adk-submission': '0.2.13', 'swegemma': '0.2.10', 'adk-eval-core': '0.1.0'}
    if any(version(name) != value for name, value in expected.items()):
        raise ValueError('Pinned runtime required')
    from swegemma.sandbox import ContainerConfig, ContainerManager
    os.environ.setdefault('DOCKER_HOST', subprocess.check_output(
        ['docker', 'context', 'inspect', '--format', '{{.Endpoints.docker.Host}}'], text=True, timeout=15).strip())
    image = 'sha256:14d857d591be7d1a7efc83ff1dcc87f83c96c764895b0986a45db0d8af5a8a46'
    manager = ContainerManager(ContainerConfig(image=image, reuse_containers=False))
    if manager.client.images.get(image).id != image:
        raise ValueError('Pinned local image required')
    args.output.mkdir(parents=True, exist_ok=False)
    cases = []
    for retain in (True, False):
        name = 'retained' if retain else 'dropped'
        result = asyncio.run(run_case(manager, retain, args.output/(name + '-trace.json')))
        (args.output/(name + '.json')).write_bytes(canonical_json(result))
        cases.append({k: v for k, v in result.items() if k not in ('requests', 'events')})
        print(cases[-1], flush=True)
    (args.output/'receipt.json').write_bytes(canonical_json({'schema_version': 1,
        'status': 'controlled_compaction_recovery_and_cost_accounting_passed', 'versions': expected,
        'cases': cases, 'owned_containers_removed': True, 'image': image,
        'probe': file_record(Path(__file__)),
        'scope': 'Actual compiled candidate, ADK runner, compaction and Docker executor. Scripted model '
                 'and summaries, synthetic usage counters. Not learned model performance, natural summary '
                 'retention probability, real token cost or training data.'}))


if __name__ == '__main__':
    main()
