"""Verify an immutable source snapshot through the pinned native tool context.

This does not execute an LLM or establish repair performance. No evaluator assets
are supplied to the agent container. Requires the image already present locally.
"""
import argparse
from importlib.metadata import version
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record
from zenithsync.container_cleanup import cleanup_owned_container
from zenithsync.source_workspace import prepare_source_workspace


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', required=True)
    parser.add_argument('--module', required=True)
    parser.add_argument('--solution', required=True)
    parser.add_argument('--src-layout', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if re.fullmatch('sha256:[0-9a-f]{64}', args.image) is None:
        raise ValueError('Immutable local image ID required')
    if re.fullmatch('[a-z][a-z0-9_]*', args.module) is None:
        raise ValueError('Simple top-level module required')
    if re.fullmatch('[0-9a-f]{40}', args.solution) is None:
        raise ValueError('Full solution commit required')
    for name, pinned in {'swegemma':'0.2.10','adk-submission':'0.2.13',
                         'google-adk':'1.36.1','adk-eval-core':'0.1.0'}.items():
        if version(name) != pinned:
            raise ValueError('Pinned native runtime required')
    from swegemma.context import SwegemmaContext
    from swegemma.sandbox import ContainerConfig, ContainerManager
    os.environ.setdefault('DOCKER_HOST', subprocess.check_output(
        ['docker','context','inspect','--format','{{.Endpoints.docker.Host}}'],text=True,timeout=15).strip())
    manager = ContainerManager(ContainerConfig(image=args.image,reuse_containers=False))
    manager.client.images.get(args.image)
    args.output.mkdir(parents=True,exist_ok=False)
    receipt = {'image':args.image,'script':file_record(Path(__file__)),
               'adapter':file_record(ROOT/'zenithsync/source_workspace.py'),
               'agent_evaluated':False,'training_approved':False,'status':'incomplete'}
    cid = None
    try:
        cid = manager.start()
        receipt['container'] = cid
        attrs = manager.client.containers.get(cid).attrs
        if attrs['HostConfig']['NetworkMode'] != 'none' or attrs['Mounts']:
            raise ValueError('Offline unmounted container required')
        raw = manager.exec(cid,'cat /opt/zenithsync/source-snapshot.json',timeout=30)
        if raw.exit_code != 0:
            raise ValueError('Missing sanitizer receipt')
        provenance = json.loads(raw.stdout)
        (args.output/'snapshot.json').write_bytes(canonical_json(provenance))
        receipt['workspace'] = prepare_source_workspace(manager,cid,
            snapshot_commit=provenance['snapshot_commit'],source_tree=provenance['source_tree'])
        absence = manager.exec(cid,'test ! -e /r2e_tests && test ! -e /workspace/run_tests.sh '
            '&& ! git -C /workspace cat-file -e '+args.solution+'^{commit}',timeout=30)
        if absence.exit_code != 0:
            raise ValueError('Known evaluator oracle remains accessible')
        receipt['known_oracles_absent'] = True
        ctx = SwegemmaContext(docker_manager=manager,container_id=cid,
            task_id='offline-workspace-probe',repo='fixture/source',max_tool_calls=10,
            max_time_minutes=2,max_exec_seconds=30,
            graph_dir='/nonexistent-fixture',embeddings_dir='/nonexistent-fixture')
        ctx.start_agent_session()
        tools = ctx.create_tools()
        module = args.module
        package = ('src/' if args.src_layout else '') + module
        receipt['source_package'] = package
        result = tools['run_command'](command='.venv/bin/python -c "import pathlib,'+module+
            '; print(pathlib.Path('+module+'.__file__).resolve())"')
        receipt['native_import'] = result
        if result['status'] != 'ok' or result['stdout'].strip() != f'/workspace/{package}/__init__.py':
            raise ValueError('Native import resolves outside source workspace')
        read = tools['read_file'](filepath=f'{package}/__init__.py')
        receipt['native_read_status'] = read['status']
        if read['status'] != 'ok' or read['is_truncated']:
            raise ValueError('Native source read failed')
        submitted = tools['submit_patch']()
        if submitted['status'] != 'ok' or ctx.submitted_patch.strip():
            raise ValueError('Untouched source exported a nonempty patch')
        receipt['empty_patch_verified'] = True
        receipt['status'] = 'passed'
    finally:
        if cid is not None:
            receipt['cleanup'] = cleanup_owned_container(manager,cid)
        (args.output/'receipt.json').write_bytes(canonical_json(receipt))
    if receipt['cleanup']['removed'] is not True:
        raise RuntimeError('Container cleanup unverified')
    print({'status':receipt['status'],'cleanup':receipt['cleanup']})


if __name__ == '__main__':
    main()
