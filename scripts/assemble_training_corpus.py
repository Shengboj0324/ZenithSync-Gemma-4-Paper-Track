"""Stage explicit token candidates into a portable quarantine corpus; never approve training."""
import argparse
import hashlib
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from zenithsync.artifacts import canonical_json,file_record,load_json
from zenithsync.training_corpus import GATES,SCHEMA_VERSION,load_corpus


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--selection',type=Path,required=True)
    p.add_argument('--directory',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--max-bytes',type=int,required=True)
    args=p.parse_args()
    selection_identity=file_record(args.selection)
    rows=load_json(args.selection)
    if not isinstance(rows,list) or not rows:raise ValueError('Nonempty explicit selection required')
    args.directory.mkdir(parents=True,exist_ok=False)
    args.output.mkdir(parents=True,exist_ok=False)
    records=[];assets=None;bound={};total=0
    for row in rows:
        keys={'example_id','task_id','repository_group','leakage_group','split','candidate_directory'}
        if not isinstance(row,dict) or set(row)!=keys:raise ValueError('Invalid selection row')
        directory=(ROOT/row['candidate_directory']).resolve(strict=True)
        if not directory.is_relative_to(ROOT):raise ValueError('Candidate directory outside workspace')
        key=hashlib.sha256(row['example_id'].encode()).hexdigest()
        destination=args.directory/'examples'/key
        destination.mkdir(parents=True,exist_ok=False)
        refs={}
        for label,name in [('tokens','tokens.json'),('audit','report.json')]:
            source=directory/name;identity=file_record(source);total+=identity['size_bytes']
            if total>args.max_bytes:raise ValueError('Explicit corpus byte budget exceeded')
            target=destination/name;shutil.copyfile(source,target)
            if file_record(target)!=identity:raise ValueError('Copy identity mismatch')
            bound[str(source)]=identity
            refs[label]={'path':target.relative_to(args.directory).as_posix(),'identity':identity}
        audit=load_json(destination/'report.json')
        if assets is None:assets=audit['assets']
        elif assets!=audit['assets']:raise ValueError('Tokenizer assets differ across selection')
        records.append({**{k:row[k] for k in keys-{'candidate_directory'}},**refs})
    manifest={'schema_version':SCHEMA_VERSION,'status':'quarantine','tokenizer_assets':assets,
              'max_length':32768,'examples':records,'admission':{gate:None for gate in GATES}}
    path=args.directory/'corpus.json';path.write_bytes(canonical_json(manifest))
    identity=file_record(path)
    validated=load_corpus(args.directory,path,expected_manifest_sha256=identity['sha256'],
                          max_total_bytes=args.max_bytes)
    if file_record(args.selection)!=selection_identity or any(file_record(Path(p))!=v for p,v in bound.items()):
        raise ValueError('Source inputs changed during assembly')
    receipt={'summary':validated['summary'],'manifest':identity,'selection':selection_identity,
             'sources':bound,'script':file_record(Path(__file__)),'training_approved':False}
    (args.output/'receipt.json').write_bytes(canonical_json(receipt))
    print(validated['summary'])


if __name__=='__main__':main()
