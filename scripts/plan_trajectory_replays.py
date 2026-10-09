"""Prioritize replay candidates using pinned source counts, never training admission."""
import argparse
from collections import Counter,defaultdict
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from zenithsync.artifacts import canonical_json,file_record
from zenithsync.trajectory_import import convert_swe_hero_history


def action_budget(messages):
    counts=Counter();unsupported=Counter()
    for m in messages:
        for call in m.get('tool_calls',[]):
            f=call['function'];name=f['name'];a=f['arguments'];counts[name]+=1
            if name=='execute_bash':
                if a.get('is_input'):unsupported['interactive_shell']+=1
                if not a.get('command'):unsupported['empty_shell_command']+=1
            if name=='str_replace_editor' and a.get('command') not in ('view','create','str_replace'):
                unsupported['unqualified_editor_action']+=1
    return {'source_tool_counts':dict(sorted(counts.items())),
            'estimated_native_charged_calls':counts['execute_bash']+counts['str_replace_editor'],
            'known_adapter_flags':dict(sorted(unsupported.items()))}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    source=ROOT/'artifacts/data/quarantine/swe-hero-001/data/train-00000-of-00014.parquet'
    intake_path=ROOT/'evidence/data/swe-hero-intake-001/receipt.json'
    intake=json.loads(intake_path.read_text());identity=file_record(source)
    if intake['downloaded']['data/train-00000-of-00014.parquet']!=identity:
        raise ValueError('Teacher source identity mismatch')
    census_path=ROOT/'evidence/data/context-census-001/receipt.json'
    census=json.loads(census_path.read_text())
    length_path=census_path.parent/'lengths.jsonl'
    if census['shard']!=identity or census['records']!=file_record(length_path):
        raise ValueError('Context census provenance mismatch')
    lengths={}
    for line in length_path.read_text().splitlines():
        row=json.loads(line)
        if row['trajectory_id'] in lengths:raise ValueError('Duplicate context record')
        lengths[row['trajectory_id']]=row
    import pyarrow.parquet as pq
    records=[];seen=set()
    for batch in pq.ParquetFile(source).iter_batches(batch_size=16,
            columns=['repo','instance_id','trajectory_id','trajectory']):
        for row in batch.to_pylist():
            tid=row['trajectory_id']
            if tid in seen or tid not in lengths or lengths[tid]['repo']!=row['repo']:
                raise ValueError('Ambiguous context-to-trajectory join')
            seen.add(tid)
            budget=action_budget(convert_swe_hero_history(row['trajectory'])['messages'])
            n=lengths[tid]['input_tokens']
            records.append({'repo':row['repo'],'instance_id':row['instance_id'],'trajectory_id':tid,
                **budget,'source_context_tokens':n,
                'within_40_estimated_calls':budget['estimated_native_charged_calls']<=40,
                'within_32768_source_tokens':n<=32768,
                'selection_rank':hashlib.sha256((intake['revision']+'\0'+tid).encode()).hexdigest(),
                'training_approved':False})
    if seen!=set(lengths) or file_record(source)!=identity:
        raise ValueError('Incomplete or unstable source census')
    groups=defaultdict(list)
    for row in records:groups[row['repo']].append(row)
    summaries={};selected=[]
    for repo,rows in sorted(groups.items()):
        budget=[r for r in rows if r['within_40_estimated_calls'] and not r['known_adapter_flags']]
        joint=[r for r in budget if r['within_32768_source_tokens']]
        summaries[repo]={'histories':len(rows),'within_40_estimated_calls':sum(r['within_40_estimated_calls'] for r in rows),
            'within_40_without_known_adapter_flags':len(budget),'joint_source_budget_and_context':len(joint)}
        # Context is not a hard rejection: the native replay can have a different
        # length (source prompt, tool serialization and reasoning all differ).
        pool=joint or budget
        if pool:
            choice=min(pool,key=lambda r:(r['selection_rank'],r['trajectory_id']))
            selected.append({**choice,'pool':'joint_source_fit' if joint else 'budget_fit_context_unqualified'})
    joined_path=ROOT/'evidence/data/source-task-join-002/joined.jsonl'
    joined_identity=file_record(joined_path)
    joined={}
    for line in joined_path.read_text().splitlines():
        task=json.loads(line)
        if task['trajectory_id'] in joined:raise ValueError('Duplicate joined trajectory')
        joined[task['trajectory_id']]=task
    selected_tasks=[]
    for row in selected:
        task=joined[row['trajectory_id']]
        if task['instance_id']!=row['instance_id'] or task['repo']!=row['repo']:
            raise ValueError('Selection source-task linkage mismatch')
        selected_tasks.append(task)
    if file_record(joined_path)!=joined_identity:raise ValueError('Join changed during selection')
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'selected-joined.jsonl').write_bytes(b''.join(canonical_json(t) for t in selected_tasks))
    (args.output/'records.jsonl').write_bytes(b''.join(canonical_json(r) for r in records))
    (args.output/'selected.json').write_bytes(canonical_json(selected))
    report={'shard':identity,'intake':file_record(intake_path),'census':file_record(census_path),
        'joined_source':joined_identity,'repositories':summaries,'rows':len(records),'script':file_record(Path(__file__)),
        'selection_rule':'Per repository: prefer joint source-budget/context fit, then minimum SHA256(revision+NUL+trajectory_id); fallback to call-budget fit.',
        'training_approved':False,
        'limitations':['Counts assume one native charged call per shell/editor action; runtime may differ.',
            'Source context omits tool schemas and generation reserve and is not native replay context.',
            'Known flags are incomplete semantic-adaptation diagnostics.',
            'Selection prioritizes cost and coverage; not a representative performance sample.',
            'Longer teacher traces are not automatically invalid SFT data; deployment-budget policy remains open.']}
    (args.output/'report.json').write_bytes(canonical_json(report))
    print(json.dumps(summaries,indent=2))


if __name__=='__main__':main()
