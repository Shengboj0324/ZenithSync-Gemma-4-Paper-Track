"""Audit supply ceilings and select a reproducible repository review batch."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from zenithsync.artifacts import canonical_json,file_record,load_json
from zenithsync.qualification_sampling import stratified_repository_batch
from zenithsync.training_corpus import IndexedCorpus


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exclusions',type=Path,required=True)
    parser.add_argument('--corpus',type=Path,required=True)
    parser.add_argument('--manifest-sha256',required=True)
    parser.add_argument('--screen',type=Path,required=True)
    parser.add_argument('--census',type=Path,required=True)
    parser.add_argument('--evaluation-metadata',type=Path,required=True)
    parser.add_argument('--seed',type=int,default=7401)
    parser.add_argument('--per-stratum',type=int,default=8)
    parser.add_argument('--previous-batch',type=Path,action='append',default=[],
                        help='Exclude repository names from a previous batch; repeatable')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    screen=args.screen
    corpus=args.corpus
    census=args.census
    paths=[screen/'report.json',screen/'ranked.jsonl',corpus/'corpus.json',
           census/'report.json',census/'index.jsonl',args.exclusions,
           args.evaluation_metadata,Path(__file__),
           ROOT/'zenithsync/qualification_sampling.py',*args.previous_batch]
    inputs={str(p):file_record(p) for p in paths}
    if file_record(screen/'ranked.jsonl')!=load_json(screen/'report.json')['records']:
        raise ValueError('Screen record mismatch')
    if file_record(census/'index.jsonl')!=load_json(census/'report.json')['index']:
        raise ValueError('Census mismatch')
    rows=[json.loads(line) for line in (screen/'ranked.jsonl').open()]
    if len(rows)!=load_json(screen/'report.json')['rows']:raise ValueError('Screen count mismatch')
    raw=[json.loads(line) for line in (census/'index.jsonl').open()]
    metadata={r['trajectory_id']:r for r in raw}
    if len(metadata)!=len(raw):raise ValueError('Duplicate census trace')
    reserved=set(load_json(args.evaluation_metadata)['repo_counts'])
    reserved={r.casefold() for r in reserved}
    for row in rows:
        source=metadata[row['trajectory_id']]
        if (any(row[k]!=source[k] for k in ('repo','instance_id'))
                or row['source']['sha256']!=source['shard_sha256']
                or source['reserved_repository_exact_match'] or row['repo'].casefold() in reserved):
            raise ValueError('Screen/census mismatch or reserved repository')
    excluded=load_json(args.exclusions)
    if not isinstance(excluded,list) or any(not isinstance(r,str) or not r.strip() for r in excluded):
        raise ValueError('Exclusions must be a list of nonempty repository names')
    verified=IndexedCorpus(corpus,corpus/'corpus.json',expected_manifest_sha256=args.manifest_sha256,purpose='inspection')
    current_repositories={r['repository_group'] for r in load_json(corpus/'corpus.json')['examples']}
    previous_repositories=set()
    for path in args.previous_batch:
        previous=load_json(path)
        if not isinstance(previous,list) or any(
                not isinstance(row,dict) or not isinstance(row.get('repo'),str)
                or not row['repo'].strip() for row in previous):
            raise ValueError('Previous batch must contain repository records')
        previous_repositories.update(row['repo'] for row in previous)
    effective_exclusions=sorted(set(excluded)|current_repositories|reserved|previous_repositories)
    batch=stratified_repository_batch(rows,excluded_repositories=effective_exclusions,seed=args.seed,per_stratum=args.per_stratum)
    trace_count=len(rows);task_count=len({r['instance_id'] for r in rows})
    # N <= 32768 - 8192; next-token loss has at most N-1 supervised targets.
    maximum_targets_per_example=32768-8192-1
    report={'schema_version':1,'inputs':inputs,'raw_traces':len(raw),
            'screened_traces':trace_count,'screened_tasks':task_count,
            'screened_repositories':len({r['repo'].casefold() for r in rows}),
            'current_corpus':verified.summary,'training_approved':False,
            'per_candidate_target':50000000,'candidate_count':3,
            'conditional_single_pass_ceiling':{
                'maximum_targets_per_example':maximum_targets_per_example,
                'all_screened_traces':trace_count*maximum_targets_per_example,
                'one_trace_per_task':task_count*maximum_targets_per_example,
                'assumptions':'Current screened cohort only; complete examples, 32768 total context, 8192 output reserve, causal labels excluding first token. Optimistic ceiling before prompt/tool masks and all quality/admission failures.'},
            'effective_exclusions':effective_exclusions,
            'batch_design':{'seed':args.seed,'repositories':len(batch),'strata':4,'per_stratum':args.per_stratum,
                'scope':'Shortest source-proxy trace per unreviewed repository, hash-ranked within four repository cost rank strata. Purposive cohort; not an unbiased agent benchmark, no success-rate extrapolation. Source proxy is not native length or target count.'},
            'campaign_note':'Three 50M-token candidates mean 150M processed target tokens. Candidates may reuse the same training corpus; repeated exposure is not unique data or independent evidence.'}
    if any(file_record(Path(p))!=identity for p,identity in inputs.items()):raise ValueError('Input drift')
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'batch.json').write_bytes(canonical_json(batch))
    report['batch']=file_record(args.output/'batch.json')
    (args.output/'report.json').write_bytes(canonical_json(report))
    print({k:report[k] for k in ['raw_traces','screened_traces','screened_tasks','screened_repositories','conditional_single_pass_ceiling']})

if __name__=='__main__':main()
