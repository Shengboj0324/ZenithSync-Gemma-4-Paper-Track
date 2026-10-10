"""Independently verify an exact-tree snapshot in a disposable offline container."""
import argparse
import base64
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record, load_json
from scripts.compare_source_snapshot import run_image

PROBE = r'''
import base64,hashlib,json,pathlib,subprocess,sys
out=pathlib.Path('/audit');out.mkdir()
module=pathlib.Path('/tmp/source_snapshot.py');module.write_bytes(base64.b64decode(MODULE))
sys.path.insert(0,'/tmp')
from source_snapshot import git,tracked_snapshot
repo=pathlib.Path(REPO_ROOT)
snapshot=json.loads(pathlib.Path('/opt/zenithsync/source-snapshot.json').read_text())
if snapshot['base_commit']!=BASE:
    raise ValueError('Wrong snapshot source base')
if git(repo,'rev-parse','HEAD').stdout.decode().strip()!=snapshot['snapshot_commit']:
    raise ValueError('Wrong snapshot HEAD')
if git(repo,'rev-parse','HEAD^{tree}').stdout.decode().strip()!=snapshot['source_tree']:
    raise ValueError('Wrong snapshot tree')
if git(repo,'rev-list','--all','--count').stdout.strip()!=b'1':
    raise ValueError('Unexpected reachable history')
if git(repo,'rev-list','--parents','-n','1','HEAD').stdout.split()!=[snapshot['snapshot_commit'].encode()]:
    raise ValueError('Snapshot is not parentless')
if git(repo,'remote').stdout.strip() or git(repo,'status','--porcelain','--untracked-files=no').stdout.strip():
    raise ValueError('Remotes or tracked changes remain')
for commit in OLD_COMMITS:
    if git(repo,'cat-file','-e',commit+'^{commit}',check=False).returncode==0:
        raise ValueError('Old commit remains accessible')
for path in ORACLES:
    p=pathlib.Path(path)
    if p.exists() or p.is_symlink():
        raise ValueError('Known oracle remains accessible')
tracked=tracked_snapshot(repo)
digest=hashlib.sha256(json.dumps(tracked,sort_keys=True).encode()).hexdigest()
if digest!=snapshot['tracked_manifest_sha256'] or len(tracked)!=snapshot['tracked_files']:
    raise ValueError('Tracked manifest mismatch')
if sum(row['size_bytes'] for row in tracked)!=snapshot['tracked_bytes']:
    raise ValueError('Tracked byte count mismatch')
(out/'snapshot.json').write_text(json.dumps(snapshot))
(out/'verification.json').write_text(json.dumps({'tracked_manifest_matches':True,
    'reachable_commits':1,'old_commits_inaccessible':OLD_COMMITS,'known_oracles_absent':ORACLES,
    'tracked_files':len(tracked),'training_approved':False,
    'scope':'Mounted filesystem only; inherited Docker layer bytes not audited.'}))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--context', type=Path, required=True)
    parser.add_argument('--resolution', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    build = load_json(args.build / 'receipt.json')
    if build['status'] != 'built_runtime_probe_pending' or file_record(args.resolution) != build['resolution']:
        raise ValueError('Completed build with matching resolution required')
    for name, identity in build['inputs'].items():
        if Path(name).name != name or file_record(args.context / name) != identity:
            raise ValueError('Build context drift')
    config = load_json(args.context / 'config.json')
    source = load_json(args.resolution)
    old = [config['expected_base'], config['solution']]
    normalization = config.get('normalization')
    if normalization and normalization['expected_head'] not in old:
        old.append(normalization['expected_head'])
    for key in ('head', 'merge'):
        commit = source.get('pull_request', {}).get(key)
        if commit and commit not in old:
            old.append(commit)
    module = ROOT / 'zenithsync/source_snapshot.py'
    inputs = {str(p):file_record(p) for p in [module, args.build/'receipt.json', args.resolution,
                                            args.context/'config.json', Path(__file__)]}
    settings = {'MODULE':base64.b64encode(module.read_bytes()).decode(),
                'BASE':config['expected_base'],'OLD_COMMITS':old,'ORACLES':config['oracle_paths'],
                'REPO_ROOT':config.get('repo_root','/testbed')}
    probe = ''.join(f'{key}={value!r}\n' for key,value in settings.items()) + PROBE
    result = run_image(build['image'], args.output, probe=probe,
                       entrypoint=build.get('python','/usr/bin/python3'))
    if result['returncode'] or result['cleanup_returncode']:
        raise ValueError('Snapshot verification or cleanup failed')
    verification = load_json(args.output / 'verification.json')
    if any(file_record(Path(path))!=identity for path,identity in inputs.items()):
        raise ValueError('Verification input drift')
    (args.output/'input-bindings.json').write_bytes(canonical_json(inputs))
    print(verification)


if __name__ == '__main__':
    main()
