"""Probe the pinned ADK summary input with synthetic events, without an LLM call."""

import argparse
import asyncio
import inspect
from importlib.metadata import version
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record
from zenithsync.harness_context import competition_context_configs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    versions = {name: version(name) for name in ('google-adk', 'adk-submission', 'swegemma')}
    if versions != {'google-adk': '1.36.1', 'adk-submission': '0.2.13', 'swegemma': '0.2.10'}:
        raise ValueError('Pinned ADK, compiler and harness required')
    configs = competition_context_configs()
    from google.adk.apps.llm_event_summarizer import LlmEventSummarizer
    from google.adk.events.event import Event
    from google.adk.models.base_llm import BaseLlm
    from google.adk.models.llm_response import LlmResponse
    from google.genai import types
    from swegemma.config import EvalConfig
    from adk_submission.registry import ModelRegistry

    required = dict(tasks_path=Path('unused-tasks'), snapshots_dir=Path('unused-snapshots'),
                    results_dir=Path('unused-results'), submission_dir=Path('unused-submission'),
                    models=ModelRegistry())
    baseline = EvalConfig(**required)
    configured = EvalConfig(**required, **configs)
    if baseline.events_compaction_config is not None or baseline.context_cache_config is not None:
        raise AssertionError('Released harness defaults changed')
    if any(getattr(configured, name) != value for name, value in configs.items()):
        raise AssertionError('Harness configuration lost context settings')

    wheel = ROOT/'artifacts/official/wheelhouse/google_adk-1.36.1-py3-none-any.whl'
    if file_record(wheel)['sha256'] != '1a2f6868c509e3151fb0de3575a7d18b45c338be86f420924dad74e7193631a0':
        raise ValueError('ADK wheel differs from runtime lock')
    module = Path(inspect.getfile(LlmEventSummarizer))
    with zipfile.ZipFile(wheel) as archive:
        if module.read_bytes() != archive.read('google/adk/apps/llm_event_summarizer.py'):
            raise ValueError('Installed summarizer differs from pinned wheel')
    requests = []

    class RecordingModel(BaseLlm):
        async def generate_content_async(self, llm_request, stream=False):
            requests.append(llm_request)
            yield LlmResponse(content=types.Content(role='model', parts=[
                types.Part(text='SYNTHETIC_TEST_SUMMARY_NOT_MODEL_GENERATED')]))

    events = [
        Event(author='user', timestamp=1.0, content=types.Content(role='user', parts=[
            types.Part(text='TASK_TEXT_SENTINEL')])),
        Event(author='repair', timestamp=2.0, content=types.Content(role='model', parts=[
            types.Part(text='ASSISTANT_TEXT_SENTINEL'),
            types.Part(function_call=types.FunctionCall(name='read_file',
                args={'path': 'CALL_ARGUMENT_SENTINEL'}, id='call_1'))])),
        Event(author='repair', timestamp=3.0, content=types.Content(role='user', parts=[
            types.Part(function_response=types.FunctionResponse(name='read_file',
                response={'content': 'TOOL_RESULT_SENTINEL'}, id='call_1'))])),
    ]
    summarizer = LlmEventSummarizer(llm=RecordingModel(model='offline-recording-fixture'))
    summary = asyncio.run(summarizer.maybe_summarize_events(events=events))
    if len(requests) != 1 or summary is None:
        raise AssertionError('Expected exactly one synthetic summarizer request')
    prompt = requests[0].contents[0].parts[0].text
    checks = {marker: marker in prompt for marker in (
        'TASK_TEXT_SENTINEL', 'ASSISTANT_TEXT_SENTINEL',
        'CALL_ARGUMENT_SENTINEL', 'TOOL_RESULT_SENTINEL')}
    if checks != {'TASK_TEXT_SENTINEL': True, 'ASSISTANT_TEXT_SENTINEL': True,
                  'CALL_ARGUMENT_SENTINEL': False, 'TOOL_RESULT_SENTINEL': False}:
        raise AssertionError('Pinned behavior changed; inspect before updating expectations')
    compaction = summary.actions.compaction
    if (compaction.start_timestamp, compaction.end_timestamp) != (1.0, 3.0):
        raise AssertionError('Unexpected compacted interval')
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output/'summary-input.txt').write_text(prompt, encoding='utf-8')
    receipt = {'schema_version': 1, 'status': 'structured_tool_omission_reproduced',
        'versions': versions,
        'marker_present_in_summary_input': checks,
        'compacted_timestamp_interval': [1.0, 3.0],
        'harness_defaults_have_compaction_and_cache_disabled': True,
        'explicit_harness_config_preserved': True,
        'configs': {name: value.model_dump(mode='json') for name, value in configs.items()},
        'pinned_wheel': file_record(wheel), 'installed_summarizer': file_record(module),
        'summary_input': file_record(args.output/'summary-input.txt'),
        'sources': {name: file_record(ROOT/name) for name in (
            'scripts/probe_harness_compaction.py', 'scripts/run_p1_repair.py',
            'zenithsync/harness_context.py',
            'artifacts/official/gemma-4-developer-agent/HARNESS_README.md')},
        'scope': 'Synthetic event formatting and recorded offline model request only; '
                 'not live summary quality, trigger timing, runner event deletion, '
                 'hidden-grader behavior, or repair success. No GPU or network model call.'}
    (args.output/'receipt.json').write_bytes(canonical_json(receipt))
    print(receipt['status'], checks)


if __name__ == '__main__':
    main()
