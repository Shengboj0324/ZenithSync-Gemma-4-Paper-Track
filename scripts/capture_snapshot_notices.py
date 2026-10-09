"""Preserve tracked license/notice files from an already-qualified source snapshot."""
import argparse
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.compare_source_snapshot import run_image

PROBE=r'''
import hashlib,json,pathlib,re,subprocess
root=pathlib.Path('/testbed');out=pathlib.Path('/audit');out.mkdir()
names=subprocess.check_output(['git','ls-files','-z'],cwd=root).decode().split('\0')
records=[];total=0
for name in names:
    if not name or not re.match(r'^(licen[cs]e|copying|copyright|notice)([._-]|$)',pathlib.PurePosixPath(name).name,re.I):
        continue
    source=root/name
    if source.is_symlink() or not source.resolve().is_relative_to(root):raise RuntimeError('Unsafe notice path')
    size=source.stat().st_size;total+=size
    if size>2*1024**2 or total>5*1024**2:raise RuntimeError('Notice size limit exceeded')
    content=source.read_bytes()
    dest=out/'notices'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(content)
    records.append({'path':name,'size_bytes':len(content),'sha256':hashlib.sha256(content).hexdigest()})
if not records:raise RuntimeError('No tracked license/notice found')
(out/'runtime.json').write_text(json.dumps({'files':records,'snapshot':json.loads(pathlib.Path('/opt/zenithsync/source-snapshot.json').read_text()),
    'scope':'Tracked files with license/notice basenames; not exhaustive embedded or dependency license audit'}))
'''


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--image',required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    r=run_image(args.image,args.output,probe=PROBE)
    if r['returncode']!=0 or r['cleanup_returncode']!=0:raise RuntimeError('Notice export or cleanup failed')
    print({'status':'captured','image':args.image})


if __name__=='__main__':main()
