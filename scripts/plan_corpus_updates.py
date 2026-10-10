"""Plan whole-example updates from a verified corpus without starting training."""
import argparse
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from zenithsync.artifacts import canonical_json,file_record
from zenithsync.training_corpus import IndexedCorpus
from zenithsync.training_schedule import make_schedule,iter_updates


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--corpus',type=Path,required=True)
    p.add_argument('--manifest-sha256',required=True)
    p.add_argument('--max-bytes',type=int,required=True)
    p.add_argument('--max-example-bytes',type=int,default=16*1024**2)
    for name in ['seed','target-supervised-tokens','max-epochs','max-update-supervised-tokens']:
        p.add_argument('--'+name,type=int,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    corpus=IndexedCorpus(args.corpus,args.corpus/'corpus.json',expected_manifest_sha256=args.manifest_sha256,
                         max_total_bytes=args.max_bytes,max_example_bytes=args.max_example_bytes,
                         purpose='inspection')
    records=[{key:r[key] for key in ['example_id','input_tokens','supervised_tokens']}
             for r in corpus.metadata() if r['split']=='train']
    plan=make_schedule(records,corpus_content_sha256=corpus.summary['content_sha256'],seed=args.seed,
                       target_supervised_tokens=args.target_supervised_tokens,max_epochs=args.max_epochs,
                       max_update_supervised_tokens=args.max_update_supervised_tokens)
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'schedule.json').write_bytes(canonical_json(plan))
    last=None
    with (args.output/'updates.jsonl').open('wb') as out:
        for update in iter_updates(plan):out.write(canonical_json(update));last=update
    report={'corpus':corpus.summary,'schedule':file_record(args.output/'schedule.json'),
            'updates':file_record(args.output/'updates.jsonl'),'terminal_cursor':last['next_cursor'],
            'target_overshoot':last['next_cursor']['consumed_supervised_tokens']-args.target_supervised_tokens,
            'training_started':False,'sources':{name:file_record(ROOT/name) for name in
                ['zenithsync/training_schedule.py','zenithsync/training_corpus.py','scripts/plan_corpus_updates.py']},
            'scope':'Explicit exposure schedule only; no data admission, new data, GPU fit or optimizer steps.'}
    (args.output/'report.json').write_bytes(canonical_json(report))
    print(report['terminal_cursor'])


if __name__=='__main__':main()
