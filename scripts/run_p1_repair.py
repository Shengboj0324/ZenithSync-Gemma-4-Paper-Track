"""Run one development attempt through official tools, without evaluator answers.

Default mode only validates inputs and configuration. --execute invokes Gemma.
An attempt receipt is never a claim that the issue was solved.
"""

import argparse
import asyncio
from contextlib import nullcontext
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
from zenithsync.task_intake import AGENT_FIELDS
from zenithsync.harness_context import competition_context_configs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--dependencies', type=Path, required=True)
    parser.add_argument('--session', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--port', type=int, default=18000)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--candidate', choices=['base', 'observation-memory'], default='base')
    parser.add_argument('--capture-http', action='store_true',
                        help='Retain full development requests and raw generated token IDs')
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        raise ValueError('Invalid loopback port')
    if version('swegemma') != '0.2.10' or version('adk-submission') != '0.2.13':
        raise ValueError('Pinned harness and SDK required')
    candidate = ROOT/('candidates/p1-' + args.candidate)
    candidate_manifest = ROOT/('evidence/p1/base-agent-001/manifest.json' if args.candidate == 'base'
                              else 'evidence/p1/observation-skill-001/candidate-manifest.json')
    manifests = [(args.bundle, ROOT/'evidence/p1/pilot-bundle-001/manifest.json'),
                 (args.dependencies, ROOT/'evidence/p1/wheels-001/manifest.json'),
                 (candidate, candidate_manifest)]
    for directory, manifest in manifests:
        verify(directory, load_json(manifest))
    task_input = load_json(args.bundle/'tasks.jsonl')
    if set(task_input) != set(AGENT_FIELDS):
        raise ValueError('Only the four agent-visible task fields are permitted')
    session = load_json(args.session)
    deadline = datetime.fromisoformat(session['validation_deadline_utc'])
    if deadline.tzinfo is None:
        raise ValueError('Timezone-aware session deadline required')
    remaining = (deadline-datetime.now(timezone.utc)).total_seconds()
    if args.execute and remaining < 1200:
        raise ValueError('Insufficient approved session time for setup and bounded attempt')
    import yaml
    from swegemma.config import EvalConfig
    from swegemma.models import Task
    from swegemma.models.registry import setup_gemma_model_registry
    from swegemma.sandbox import ContainerConfig, ContainerManager
    from swegemma.harness.agent_runner import run_agent_sandbox

    budget = yaml.safe_load((candidate/'eval_config.yaml').read_text())['evaluation']
    expected = {'timeout_seconds': 120, 'max_tool_calls': 40, 'max_time_minutes': 10, 'max_turns': 40}
    if budget != expected:
        raise ValueError('P1 candidate budgets changed; requalify before executing')
    alias = 'gemma-4-31b-it-qat-w4a16-ct'
    endpoint = f'http://127.0.0.1:{args.port}/v1'
    models = setup_gemma_model_registry(api_base=endpoint, api_key='EMPTY',
                                       num_retries=0, served_model=alias)
    image = 'sha256:14d857d591be7d1a7efc83ff1dcc87f83c96c764895b0986a45db0d8af5a8a46'
    context_configs = competition_context_configs()
    config = EvalConfig(tasks_path=args.bundle/'tasks.jsonl', snapshots_dir=args.bundle/'snapshots',
        results_dir=args.output, submission_dir=candidate, models=models, image=image,
        wheels_dir=args.dependencies/'wheels', graph_dir=str(args.bundle/'graphs'),
        embeddings_dir=str(args.bundle/'embeddings'), display_mode='quiet',
        **context_configs, **budget)
    task = Task(**task_input)
    args.output.mkdir(parents=True, exist_ok=False)
    source = file_record(Path(__file__))
    record = {'schema_version': 1, 'status': 'configuration_prepared_not_executed',
              'task_id': task.instance_id, 'endpoint': endpoint, 'model': alias,
              'candidate': args.candidate, 'session_deadline_utc': deadline.isoformat(),
              'budgets': budget, 'image': image, 'source': source,
              'context_configs': {name: value.model_dump(mode='json')
                                  for name, value in context_configs.items()},
              'context_config_source': file_record(ROOT/'zenithsync/harness_context.py'),
              'manifests': {str(p.relative_to(ROOT)): file_record(p) for _, p in manifests},
              'scope': 'One development attempt; no reference patch or grading oracle supplied'}
    (args.output/'plan.json').write_bytes(canonical_json(record))
    if not args.execute:
        print('Official configuration prepared; no model request or sandbox started.')
        return
    os.environ.setdefault('DOCKER_HOST', subprocess.check_output(
        ['docker', 'context', 'inspect', '--format', '{{.Endpoints.docker.Host}}'],
        text=True, timeout=15).strip())
    os.environ['KAGGLE_SANDBOX_DIR'] = str(ROOT/'artifacts/official/gemma-4-developer-agent/sandbox')
    manager = ContainerManager(ContainerConfig(image=image, reuse_containers=False))
    # The literal image ID must already exist locally; never pull an unpinned image here.
    if manager.client.images.get(image).id != image:
        raise ValueError('Unexpected task sandbox image')
    started = datetime.now(timezone.utc).isoformat()
    async def attempt():
        execution_remaining = (deadline-datetime.now(timezone.utc)).total_seconds() - 30
        if execution_remaining <= 0:
            raise ValueError('Session deadline leaves no cleanup reserve')
        async with asyncio.timeout(min(1200, execution_remaining)):
            return await run_agent_sandbox(manager, config, task,
                args.bundle/'snapshots'/(task.instance_id+'.tgz'))
    from zenithsync.inference_capture import capture_inference
    capture = capture_inference(args.output/'http', args.port) if args.capture_http else nullcontext(endpoint)
    with capture as captured_endpoint:
        if args.capture_http:
            config.models = setup_gemma_model_registry(api_base=captured_endpoint, api_key='EMPTY',
                                                      num_retries=0, served_model=alias)
        patch, error, trace = asyncio.run(attempt())
    (args.output/'agent.patch').write_text(patch)
    trace.save(args.output/'trace.json')
    for directory, manifest in manifests:
        verify(directory, load_json(manifest))
    if source != file_record(Path(__file__)):
        raise ValueError('Driver changed during execution')
    if record['context_config_source'] != file_record(ROOT/'zenithsync/harness_context.py'):
        raise ValueError('Context settings changed during execution')
    record.update(status='attempt_recorded_not_graded', started_utc=started,
                  finished_utc=datetime.now(timezone.utc).isoformat(), agent_error=error,
                  patch=file_record(args.output/'agent.patch'), trace=file_record(args.output/'trace.json'))
    record['http_capture'] = args.capture_http
    (args.output/'receipt.json').write_bytes(canonical_json(record))
    print('Actual agent attempt retained; independent grading remains required.')


if __name__ == '__main__':
    main()
