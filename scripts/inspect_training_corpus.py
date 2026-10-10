"""Validate a restored corpus without importing Torch or starting training."""
import argparse
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from zenithsync.artifacts import canonical_json,file_record
from zenithsync.training_corpus import load_corpus


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--directory',type=Path,required=True)
    p.add_argument('--manifest-sha256',required=True)
    p.add_argument('--max-bytes',type=int,required=True)
    p.add_argument('--max-examples',type=int,default=100000)
    p.add_argument('--purpose',choices=['inspection','training'],default='inspection')
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    r=load_corpus(args.directory,args.directory/'corpus.json',
                  expected_manifest_sha256=args.manifest_sha256,purpose=args.purpose,
                  max_total_bytes=args.max_bytes,max_examples=args.max_examples)
    args.output.mkdir(parents=True,exist_ok=False)
    report={'summary':r['summary'],'loader':file_record(ROOT/'zenithsync/training_corpus.py'),
            'script':file_record(Path(__file__)),'gpu_used':False,
            'scope':'Local byte integrity, audit lineage, token/label accounting and declared split gates; not model execution or evidence authenticity.'}
    (args.output/'report.json').write_bytes(canonical_json(report))
    print(r['summary'])


if __name__=='__main__':main()
