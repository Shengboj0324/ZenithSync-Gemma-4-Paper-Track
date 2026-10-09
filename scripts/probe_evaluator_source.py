"""Exercise the official evaluator with a synthetic source-origin assertion.

Uses the reserved Requests snapshot, an empty agent patch, and an explicitly
synthetic evaluator test. Does not read or apply a benchmark reference patch.
"""

import argparse
import asyncio
from importlib.metadata import version
import os
from pathlib import Path
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
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--dependencies', type=Path, required=True)
    parser.add_argument('--dependency-manifest', type=Path, required=True)
    parser.add_argument('--backend', choices=['docker', 'subprocess'], default='docker')
    parser.add_argument('--image')
    parser.add_argument('--source-path-control', action='store_true',
                        help='Diagnostic only: prepend checkout source paths for pytest')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.backend == 'docker' and not args.image:
        parser.error('--image is required for Docker')
    if args.backend == 'subprocess' and args.image:
        parser.error('--image does not apply to the subprocess backend')
    args.output.mkdir(parents=True, exist_ok=False)
    verify(args.bundle, load_json(args.manifest))
    verify(args.dependencies, load_json(args.dependency_manifest))
    if version('swegemma') != '0.2.10':
        raise ValueError('this audit requires swegemma 0.2.10')
    if args.backend == 'docker':
        os.environ.setdefault('DOCKER_HOST', subprocess.check_output(
            ['docker', 'context', 'inspect', '--format', '{{.Endpoints.docker.Host}}'],
            text=True, timeout=15).strip())
    os.environ['KAGGLE_SANDBOX_DIR'] = str(ROOT / 'artifacts/official/gemma-4-developer-agent/sandbox')
    from adk_submission import ModelRegistry
    from swegemma.config import EvalConfig
    from swegemma.models import Task
    from swegemma.sandbox import ContainerConfig, ContainerManager, SubprocessManager
    from swegemma.harness.verification import verify_task
    import swegemma.harness.verification as implementation

    # The bundle exposes only the allowed agent-input projection.
    task_input = load_json(args.bundle / 'tasks.jsonl')
    if task_input['repo'] != 'psf/requests':
        raise ValueError('source probe only qualifies the reserved Requests snapshot')
    source = ('from pathlib import Path\n\n'
              'def test_workspace_source_origin():\n'
              '    import requests\n'
              '    origin = Path(requests.__file__).resolve()\n'
              '    expected = Path(__file__).resolve().parents[1] / "src" / "requests"\n'
              '    assert origin.is_relative_to(expected), str(origin)\n')
    test_path = 'tests/test_zenith_source_probe.py'
    patch = (f'diff --git a/{test_path} b/{test_path}\nnew file mode 100644\n'
             f'--- /dev/null\n+++ b/{test_path}\n@@ -0,0 +1,{len(source.splitlines())} @@\n'
             + ''.join('+' + line + '\n' for line in source.splitlines()))
    (args.output / 'synthetic-test.patch').write_text(patch)
    task = Task(instance_id='zenith_source_origin_probe', repo=task_input['repo'],
                base_commit=task_input['base_commit'], problem_statement='Synthetic source-origin audit',
                test_patch=patch)
    config = EvalConfig(tasks_path=args.bundle / 'tasks.jsonl', snapshots_dir=args.bundle / 'snapshots',
                        results_dir=args.output, models=ModelRegistry(),
                        submission_dir=ROOT / 'artifacts/official/gemma-4-developer-agent/sample_submission',
                        wheels_dir=args.dependencies / 'wheels', sandbox=args.backend)
    image_id = None
    if args.backend == 'docker':
        manager = ContainerManager(ContainerConfig(image=args.image, reuse_containers=False))
        image_id = manager.client.images.get(args.image).id
        manager.config.image = image_id
    else:
        manager = SubprocessManager()
    if args.source_path_control:
        original_exec = manager.exec

        def source_control_exec(sandbox_id, command, **kwargs):
            if ' -m pytest ' in command:
                command = command.replace(
                    'PYTHONSAFEPATH=1',
                    'PYTHONPATH=/workspace/src:/workspace PYTHONSAFEPATH=1', 1)
            return original_exec(sandbox_id, command, **kwargs)

        manager.exec = source_control_exec
    identities = {'verifier': file_record(Path(__file__)),
                  'official_verification': file_record(Path(implementation.__file__))}
    result = asyncio.run(verify_task(manager, config, task,
        args.bundle / 'snapshots' / (task_input['instance_id'] + '.tgz'),
        agent_patch='', start_time=time.perf_counter()))
    (args.output / 'result.json').write_text(result.model_dump_json(indent=2) + '\n')
    (args.output / 'test-output.log').write_text(result.test_output)
    verify(args.bundle, load_json(args.manifest))
    verify(args.dependencies, load_json(args.dependency_manifest))
    if identities != {'verifier': file_record(Path(__file__)),
                      'official_verification': file_record(Path(implementation.__file__))}:
        raise ValueError('audit implementation changed')
    (args.output / 'receipt.json').write_bytes(canonical_json({
        'schema_version': 1, 'status': 'official_evaluator_source_probe_recorded',
        'image': image_id, 'backend': args.backend, 'sources': identities, 'swegemma_version': version('swegemma'),
        'host_python': sys.version,
        'source_path_control': args.source_path_control,
        'test_exit_code': result.test_exit_code, 'resolved': result.resolved,
        'result': file_record(args.output / 'result.json'),
        'scope': 'Synthetic origin assertion through real verify_task; no benchmark repair claim'}))
    print('Official evaluator probe recorded:', result.resolved, result.test_exit_code)


if __name__ == '__main__':
    main()
