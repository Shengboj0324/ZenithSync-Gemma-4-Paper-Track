"""Capture bounded tracked source and selected dependency notices for review."""
import argparse
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.compare_source_snapshot import run_image
from zenithsync.artifacts import canonical_json,file_record,load_json

PROBE=r'''
import hashlib,json,pathlib,subprocess
out=pathlib.Path('/audit');out.mkdir()
root=pathlib.Path('/testbed')
snapshot=json.loads(pathlib.Path('/opt/zenithsync/source-snapshot.json').read_text())
def git(*args):
    return subprocess.check_output(['git','-C',str(root),*args],timeout=30).decode().strip()
if git('rev-parse','HEAD')!=snapshot['snapshot_commit'] or git('rev-parse','HEAD^{tree}')!=snapshot['source_tree']:
    raise ValueError('Snapshot identity mismatch')
if git('status','--porcelain','--untracked-files=no'):
    raise ValueError('Tracked modifications')
records=[];total=0
for name in subprocess.check_output(['git','-C',str(root),'ls-files','-z']).decode().split('\0'):
    if not name:continue
    source=root/name
    if source.is_symlink() or not source.resolve().is_relative_to(root):
        raise ValueError('Unsupported source path')
    content=source.read_bytes();total+=len(content)
    if total>2*1024**2:raise ValueError('Source capture exceeds 2 MiB')
    dest=out/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(content)
    records.append({'path':name,'size_bytes':len(content),'sha256':hashlib.sha256(content).hexdigest()})
(out/'source-manifest.json').write_text(json.dumps({'snapshot':snapshot,'files':records}))
code=r"""
import hashlib,json,pathlib,sys
try:
    import importlib.metadata as md
except ImportError:
    import importlib_metadata as md
runtime_root=pathlib.Path(sys.prefix).resolve(strict=True)
out=pathlib.Path('/audit/dependencies');out.mkdir()
records=[]
for name in json.loads(sys.argv[1]):
    d=md.distribution(name);files=[];total=0
    for f in d.files or []:
        if not any(word in str(f).lower() for word in ('license','copying','copyright','notice')):
            continue
        path=pathlib.Path(d.locate_file(f))
        if not path.is_file():continue
        resolved=path.resolve(strict=True)
        if path.is_symlink() or (resolved!=runtime_root and runtime_root not in resolved.parents):
            raise ValueError('Dependency notice outside runtime')
        raw=path.read_bytes();total+=len(raw)
        if total>2*1024**2:raise ValueError('Dependency notices exceed 2 MiB')
        dest=out/name/str(len(files));dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
        files.append({'source':str(f),'saved':str(dest.relative_to(out)),
                      'size_bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
    if not files and not json.loads(sys.argv[2]):
        raise ValueError('No preserved notice for '+name)
    records.append({'distribution':name,'name':d.metadata['Name'],'version':d.version,
                    'license_field':d.metadata.get('License'),'files':files,
                    'notice_status':'captured' if files else 'missing'})
(out/'manifest.json').write_text(json.dumps(records))
"""
subprocess.run([PYTHON,'-c',code,json.dumps(DISTRIBUTIONS),json.dumps(ALLOW_MISSING)],check=True,timeout=60)
'''


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--image',required=True)
    p.add_argument('--distribution',action='append',required=True)
    p.add_argument('--python',choices=['/opt/conda/envs/testbed/bin/python',
                                     '/opt/miniconda3/envs/testbed/bin/python'],
                   default='/opt/conda/envs/testbed/bin/python')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--allow-missing-notices',action='store_true',
                   help='Inventory explicit missing notices for investigation; never rights approval')
    args=p.parse_args()
    if len(set(args.distribution))!=len(args.distribution) or any(
            re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*',n) is None for n in args.distribution):
        raise ValueError('Unique simple distribution names required')
    r=run_image(args.image,args.output,probe='DISTRIBUTIONS='+repr(args.distribution)+'\nPYTHON='+repr(args.python)+'\nALLOW_MISSING='+repr(args.allow_missing_notices)+'\n'+PROBE)
    if r['returncode'] or r['cleanup_returncode']:
        raise ValueError('Material capture failed; inspect retained logs')
    missing=[row['distribution'] for row in load_json(args.output/'dependencies/manifest.json') if not row['files']]
    report={'source_manifest':file_record(args.output/'source-manifest.json'),
            'dependency_manifest':file_record(args.output/'dependencies/manifest.json'),
            'script':file_record(Path(__file__)),'python':args.python,'training_approved':False,
            'missing_notices':missing,'all_selected_notices_present':not missing,
            'scope':'Selected material capture for review, not exhaustive dependency or rights clearance.'}
    (args.output/'report.json').write_bytes(canonical_json(report))
    print(report)


if __name__=='__main__':main()
