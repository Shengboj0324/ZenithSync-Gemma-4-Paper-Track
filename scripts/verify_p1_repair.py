"""Grade the reserved development task separately from agent execution.

The optional source-path correction is a labeled local diagnostic, not official
environment parity. Source selection is measured immediately before pytest.
"""

import argparse
import asyncio
from importlib.metadata import version
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('LITELLM_LOCAL_MODEL_COST_MAP', 'True')
os.environ.setdefault('OTEL_SDK_DISABLED', 'true')
from zenithsync.artifacts import canonical_json, file_record, load_json, verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--patch', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--source-path-override', action='store_true')
    parser.add_argument('--in-process-source-check', action='store_true',
                        help='Local diagnostic: fail if pytest loads Requests outside the checkout')
    parser.add_argument('--image', default='sha256:14d857d591be7d1a7efc83ff1dcc87f83c96c764895b0986a45db0d8af5a8a46')
    args = parser.parse_args()
    if not re.fullmatch(r'sha256:[0-9a-f]{64}', args.image):
        raise ValueError('An immutable local image ID is required')
    if version('swegemma') != '0.2.10':
        raise ValueError('Pinned evaluator required')
    oracle = ROOT/'artifacts/official/p1-evaluator-input'
    verify(oracle, load_json(ROOT/'evidence/p1/evaluator-intake-001/manifest.json'))
    task_data = load_json(oracle/'task.json')
    if set(task_data) != {'instance_id','repo','base_commit','problem_statement','test_patch'}:
        raise ValueError('Unexpected evaluator fields')
    if task_data['repo'] != 'psf/requests':
        raise ValueError('This source-origin probe is specific to Requests')
    bundle = ROOT/'artifacts/official/restored-pilot-p1-001'
    dependencies = ROOT/'artifacts/official/restored-dependencies-p1-001'
    verify(bundle, load_json(ROOT/'evidence/p1/pilot-bundle-001/manifest.json'))
    verify(dependencies, load_json(ROOT/'evidence/p1/wheels-001/manifest.json'))
    patch_text = args.patch.read_text() if args.patch else ''
    patch_identity = file_record(args.patch) if args.patch else None
    args.output.mkdir(parents=True, exist_ok=False)
    os.environ.setdefault('DOCKER_HOST', subprocess.check_output(
        ['docker','context','inspect','--format','{{.Endpoints.docker.Host}}'], text=True, timeout=15).strip())
    os.environ['KAGGLE_SANDBOX_DIR'] = str(ROOT/'artifacts/official/gemma-4-developer-agent/sandbox')
    from adk_submission import ModelRegistry
    from swegemma.config import EvalConfig
    from swegemma.models import Task
    from swegemma.sandbox import ContainerConfig, ContainerManager
    from swegemma.harness.verification import verify_task
    image = args.image
    environment = {'TEST_TMPDIR': '/tmp'}
    if args.source_path_override:
        environment['PYTHONPATH'] = '/workspace/src:/workspace'
    if args.in_process_source_check:
        environment.update(ZENITH_SOURCE_REPORT='/tmp/zenithsync-source.jsonl',
                           ZENITH_SOURCE_MODULES='["requests","requests.utils"]',
                           ZENITH_SOURCE_ROOT='/workspace')
    manager = ContainerManager(ContainerConfig(image=image, environment=environment, reuse_containers=False))
    if manager.client.images.get(image).id != image:
        raise ValueError('Unexpected local image')
    original_exec = manager.exec
    origins = []
    def audited_exec(container_id, command, *, timeout=None):
        report_path = None
        if ' -m pytest ' in command:
            if args.in_process_source_check:
                site = original_exec(container_id,
                    "python3 -s -c 'import sysconfig; print(sysconfig.get_path(\"purelib\"))'", timeout=30)
                site_path = site.stdout.strip()
                if site.exit_code or not re.fullmatch(r'/usr/local/lib/python3\.[0-9]+/site-packages', site_path):
                    raise RuntimeError('Unexpected evaluator plugin install location')
                manager.copy_to(container_id, ROOT/'scripts/evaluator_source_plugin.py',
                                site_path+'/zenithsync_source_probe.py')
                command = command.replace(' -m pytest ', ' -m pytest -p zenithsync_source_probe ', 1)
            observed = original_exec(container_id,
                "PYTHONSAFEPATH=1 python3 -s -c 'import requests,requests.utils,json; "
                "print(json.dumps({\"package\":requests.__file__,\"utils\":requests.utils.__file__}))'", timeout=30)
            if observed.exit_code:
                raise RuntimeError('Evaluator source-origin measurement failed')
            origins.append(json.loads(observed.stdout))
            report = re.search(r'--junitxml=(/tmp/_swegemma_junit_[0-9a-f]+\.xml)\b', command)
            if not report:
                raise RuntimeError('Official verifier JUnit path not found')
            report_path = report.group(1)
        result = original_exec(container_id, command, timeout=timeout)
        if report_path:
            if args.in_process_source_check:
                provenance = original_exec(container_id, 'cat /tmp/zenithsync-source.jsonl', timeout=30)
                if provenance.exit_code:
                    raise RuntimeError('In-process source report missing')
                (args.output/'source-in-process.jsonl').write_text(provenance.stdout)
            # Preserve per-case outcomes even when the official overall result fails.
            # The allowlisted path above is generated by the trusted verifier.
            xml = original_exec(container_id, 'cat ' + report_path, timeout=30)
            (args.output/'junit-capture.json').write_bytes(canonical_json({'exit_code':xml.exit_code}))
            if xml.exit_code == 0:
                (args.output/'junit.xml').write_text(xml.stdout)
        return result
    manager.exec = audited_exec
    config = EvalConfig(tasks_path=oracle/'task.json', snapshots_dir=bundle/'snapshots',
        results_dir=args.output, submission_dir=ROOT/'candidates/p1-base', models=ModelRegistry(),
        wheels_dir=dependencies/'wheels', timeout_seconds=120)
    result = asyncio.run(verify_task(manager, config, Task(**task_data),
        bundle/'snapshots'/(task_data['instance_id']+'.tgz'), agent_patch=patch_text,
        start_time=time.perf_counter()))
    (args.output/'result.json').write_text(result.model_dump_json(indent=2)+'\n')
    (args.output/'test-output.log').write_text(result.test_output)
    if args.patch and patch_identity != file_record(args.patch):
        raise ValueError('Agent patch changed during evaluation')
    (args.output/'receipt.json').write_bytes(canonical_json({
        'schema_version':1, 'status':'evaluation_recorded', 'source_override':args.source_path_override,
        'image':image,
        'in_process_source_check':args.in_process_source_check,
        'agent_patch':patch_identity, 'source_origins':origins, 'reported_resolved':result.resolved,
        'test_exit_code':result.test_exit_code, 'verifier':file_record(Path(__file__)),
        'result':file_record(args.output/'result.json'),
        'scope':'Official test patch in fresh sandbox; inspect source origin before interpreting outcome'}))
    print('Evaluation recorded:', result.resolved, 'source override:', args.source_path_override)


if __name__ == '__main__':
    main()
