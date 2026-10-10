"""Build a derived evaluator baseline from a pinned image and bound head probe.

No agent workspace approval: oracle removal and history sanitization are later
steps. Does not install packages or change the parent image.
"""
import argparse
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record, load_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resolution', type=Path, required=True)
    parser.add_argument('--probe', type=Path, required=True)
    parser.add_argument('--context', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    inputs = {str(p): file_record(p) for p in (args.resolution, args.probe, Path(__file__),
              ROOT/'zenithsync/source_base.py', ROOT/'zenithsync/source_snapshot.py')}
    resolution = load_json(args.resolution)
    probe = load_json(args.probe)
    image = resolution['registry']['pinned_image']
    if re.fullmatch(r'[a-z0-9_./-]+@sha256:[0-9a-f]{64}', image) is None:
        raise ValueError('Pinned parent registry image required')
    if (probe['input'] != inputs[str(args.resolution)] or probe['image'] != image
            or probe['returncode'] != 0 or probe['cleanup_returncode'] != 0
            or probe['observations']['head']['returncode'] != 0):
        raise ValueError('Successful bound source probe required')
    config = {'expected_head': probe['observations']['head']['stdout'],
              'target_base': resolution['task']['base_commit']}
    if any(not isinstance(v, str) or re.fullmatch('[0-9a-f]{40}', v) is None for v in config.values()):
        raise ValueError('Full checkout identities required')
    args.context.mkdir(parents=True, exist_ok=False)
    args.output.mkdir(parents=True, exist_ok=False)
    package = args.context/'zenithsync';package.mkdir()
    (package/'__init__.py').write_text('')
    for name in ('source_base.py', 'source_snapshot.py'):
        shutil.copyfile(ROOT/'zenithsync'/name, package/name)
    (args.context/'config.json').write_bytes(canonical_json(config))
    (args.context/'build.py').write_text(
        'import json\nfrom pathlib import Path\n'
        'from zenithsync.source_base import normalize_base\n'
        'config=json.loads(Path("/tmp/zenithsync-base/config.json").read_text())\n'
        'result=normalize_base("/testbed", **config)\n'
        'Path("/opt/zenithsync").mkdir(parents=True,exist_ok=True)\n'
        'Path("/opt/zenithsync/base-normalization.json").write_text(json.dumps(result,sort_keys=True))\n')
    (args.context/'Dockerfile').write_text(
        'FROM '+image+'\nUSER root\nCOPY . /tmp/zenithsync-base/\n'
        'RUN PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 /tmp/zenithsync-base/build.py && '
        'rm -r /tmp/zenithsync-base\nWORKDIR /testbed\n')
    context_inputs = {str(p.relative_to(args.context)): file_record(p)
                      for p in args.context.rglob('*') if p.is_file()}
    receipt = {'inputs': inputs, 'context': context_inputs, 'parent_image': image,
               'config': config, 'training_approved': False, 'agent_workspace_approved': False,
               'status': 'building'}
    try:
        with (args.output/'build.log').open('w') as log:
            subprocess.run(['docker','build','--network','none','--pull=false',
                '--platform','linux/amd64','--progress','plain','--iidfile',
                str(args.output/'image-id.txt'),str(args.context)],
                stdout=log,stderr=subprocess.STDOUT,check=True,timeout=600)
        image_id = (args.output/'image-id.txt').read_text().strip()
        if re.fullmatch('sha256:[0-9a-f]{64}', image_id) is None:
            raise ValueError('Invalid derived image identity')
        if (any(file_record(Path(p)) != value for p, value in inputs.items())
                or context_inputs != {str(p.relative_to(args.context)):file_record(p)
                    for p in args.context.rglob('*') if p.is_file()}):
            raise ValueError('Baseline build input drift')
        derived = dict(resolution)
        derived['registry'] = {'pinned_image': image_id, 'runtime_verified': False}
        derived['baseline_derivation'] = {'parent_resolution': inputs[str(args.resolution)],
                                         'parent_image': image, 'config': config}
        (args.output/'resolution.json').write_bytes(canonical_json(derived))
        receipt.update(status='built_controls_pending', image_id=image_id,
                       resolution=file_record(args.output/'resolution.json'))
    finally:
        (args.output/'receipt.json').write_bytes(canonical_json(receipt))
    print({'image': image_id, 'status': receipt['status']})


if __name__ == '__main__':
    main()
