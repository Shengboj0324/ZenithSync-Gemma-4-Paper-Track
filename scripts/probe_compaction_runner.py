"""Offline ADK runner integration: synthetic token usage, tool loop, real compaction."""

import argparse
import asyncio
from importlib.metadata import version
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record
from zenithsync.harness_context import competition_context_configs


async def scenario(name, usage, enabled):
    from google.adk.agents import LlmAgent
    from google.adk.apps import App
    from google.adk.models.base_llm import BaseLlm
    from google.adk.models.llm_response import LlmResponse
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types
    requests, executed = [], []
    main_calls = 0

    def observe(index: int) -> dict:
        """Return a synthetic observation for the specified test index."""
        executed.append(index)
        return {'observation': f'OBSERVATION_SENTINEL_{index}'}

    class RecordingModel(BaseLlm):
        async def generate_content_async(self, llm_request, stream=False):
            nonlocal main_calls
            snapshot = llm_request.model_dump(mode='json', exclude_none=True)
            first_text = llm_request.contents[0].parts[0].text or ''
            is_summary = first_text.startswith('The following is a conversation history')
            requests.append({'kind': 'summary' if is_summary else 'agent', 'request': snapshot})
            if is_summary:
                content = types.Content(role='model', parts=[types.Part(text='OFFLINE_SYNTHETIC_SUMMARY')])
            else:
                main_calls += 1
                if main_calls > 7:
                    raise AssertionError('Unexpected extra agent call')
                if main_calls <= 6:
                    content = types.Content(role='model', parts=[types.Part(function_call=types.FunctionCall(
                        name='observe', args={'index': main_calls}, id=f'call_{main_calls}'))])
                else:
                    content = types.Content(role='model', parts=[types.Part(text='OFFLINE_LOOP_COMPLETE')])
            yield LlmResponse(content=content, usage_metadata=types.GenerateContentResponseUsageMetadata(
                prompt_token_count=usage, candidates_token_count=1, total_token_count=usage + 1))

    agent = LlmAgent(name='repair', model=RecordingModel(model='offline-fixture'), tools=[observe])
    configs = competition_context_configs() if enabled else {}
    app = App(name='context_probe', root_agent=agent, **configs)
    service = InMemorySessionService()
    await service.create_session(app_name=app.name, user_id='fixture', session_id=name)
    runner = Runner(app=app, session_service=service)
    events = []
    async for event in runner.run_async(user_id='fixture', session_id=name,
        new_message=types.Content(role='user', parts=[types.Part(text='SYNTHETIC_TASK_SENTINEL')])):
        events.append(event.model_dump(mode='json', exclude_none=True))
    session = await service.get_session(app_name=app.name, user_id='fixture', session_id=name)
    if executed != list(range(1, 7)) or main_calls != 7:
        raise AssertionError('Expected six actual local tool executions and seven agent requests')
    raw_events = [e for e in session.events if not e.actions.compaction]
    if len({e.invocation_id for e in raw_events}) != 1:
        raise AssertionError('Fixture must use one invocation')
    response_ids = [r.id for e in raw_events for r in e.get_function_responses()]
    if response_ids != [f'call_{i}' for i in range(1, 7)]:
        raise AssertionError('Original tool response events must remain stored')
    visibility = []
    for request in requests:
        payload = canonical_json(request['request']).decode()
        visibility.append({'kind': request['kind'], 'observation_indices': [i for i in range(1, 7)
            if f'OBSERVATION_SENTINEL_{i}' in payload], 'summary_visible': 'OFFLINE_SYNTHETIC_SUMMARY' in payload})
    return {'name': name, 'synthetic_prompt_usage': usage, 'compaction_enabled': enabled,
            'requests': requests, 'visibility': visibility, 'executed_tools': executed,
            'raw_invocations': 1, 'stored_tool_response_ids': response_ids,
            'yielded_events': events, 'session_events': [e.model_dump(mode='json', exclude_none=True) for e in session.events]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if version('google-adk') != '1.36.1':
        raise ValueError('Pinned ADK required')
    import google.adk
    package = Path(google.adk.__file__).parent
    wheel = ROOT/'artifacts/official/wheelhouse/google_adk-1.36.1-py3-none-any.whl'
    if file_record(wheel)['sha256'] != '1a2f6868c509e3151fb0de3575a7d18b45c338be86f420924dad74e7193631a0':
        raise ValueError('Unqualified wheel')
    sources = {}
    with zipfile.ZipFile(wheel) as archive:
        for relative in ('runners.py', 'apps/compaction.py', 'apps/llm_event_summarizer.py',
                         'flows/llm_flows/compaction.py', 'flows/llm_flows/contents.py'):
            path = package/relative
            if path.read_bytes() != archive.read('google/adk/' + relative):
                raise ValueError('Installed runner source differs from pinned wheel')
            sources[relative] = file_record(path)
    args.output.mkdir(parents=True, exist_ok=False)
    cases = []
    for name, usage, enabled in [('below_threshold', 14335, True),
                                  ('at_threshold', 14336, True), ('disabled_control', 14336, False)]:
        result = asyncio.run(scenario(name, usage, enabled))
        (args.output/(name + '.json')).write_bytes(canonical_json(result))
        summaries = sum(r['kind'] == 'summary' for r in result['requests'])
        if (name == 'at_threshold') != (summaries > 0):
            raise AssertionError('Unexpected threshold behavior')
        agents = [r for r in result['visibility'] if r['kind'] == 'agent']
        if agents[1]['observation_indices'] != [1]:
            raise AssertionError('Initial tool result did not reach agent')
        final_has_first = 1 in agents[-1]['observation_indices']
        if final_has_first == (name == 'at_threshold'):
            raise AssertionError('Unexpected retained observation visibility')
        case = {'name': name, 'summary_requests': summaries, 'agent_requests': len(agents),
                'first_observation_visible_in_final_request': final_has_first,
                'visibility': result['visibility'], 'evidence': file_record(args.output/(name + '.json'))}
        cases.append(case)
        print(case['name'], case['summary_requests'], case['first_observation_visible_in_final_request'], flush=True)
    (args.output/'receipt.json').write_bytes(canonical_json({'schema_version': 1,
        'status': 'offline_runner_threshold_and_observation_loss_reproduced', 'cases': cases,
        'installed_sources': sources, 'probe': file_record(Path(__file__)),
        'config_helper': file_record(ROOT/'zenithsync/harness_context.py'),
        'scope': 'Real pinned ADK runner and local tools; synthetic model outputs and usage metadata. '
                 'No actual token measurement, GPU inference, generated summary quality, training data, '
                 'SWE-gemma end-to-end execution or hidden-grader parity.'}))


if __name__ == '__main__':
    main()
