"""Construct a diagnostic native history from one fully captured Tornado replay."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from zenithsync.artifacts import canonical_json,file_record
from zenithsync.replay_history import native_replay_history
from zenithsync.source_task import project_source_issue


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--attempt',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--controls',type=Path,default=ROOT/'evidence/data/tornado-expectations-002/report.json')
    p.add_argument('--snapshot',type=Path,default=ROOT/'evidence/data/tornado-workspace-probe-001/snapshot.json')
    args=p.parse_args()
    attempt=json.loads((args.attempt/'receipt.json').read_text())
    if attempt['status']!='replayed_not_graded' or attempt['cleanup']['removed'] is not True:
        raise ValueError('Completed and cleaned-up replay required')
    control_path=args.controls
    control=json.loads(control_path.read_text())
    shard=control['source']['shard'];relative=f'data/train-{shard:05d}-of-00008.parquet'
    path=ROOT/f'artifacts/data/quarantine/r2e-gym-shard-{shard:03d}'/relative
    intake=json.loads((ROOT/f'evidence/data/r2e-gym-shard-{shard:03d}/receipt.json').read_text())
    identity=file_record(path)
    if identity!=control['source']['identity'] or identity!=intake['downloaded'][relative]:
        raise ValueError('Source shard identity mismatch')
    import pyarrow.parquet as pq
    row=pq.read_table(path,columns=['repo_name','commit_hash','problem_statement']).slice(control['source']['row_index'],1).to_pylist()[0]
    repo=attempt.get('profile',{}).get('repo','tornadoweb/tornado')
    if repo not in ('tornadoweb/tornado','Pylons/pyramid'):
        raise ValueError('Unqualified issue projection repository')
    if row['repo_name']!=repo.split('/')[-1] or attempt['instance_id']!=repo.replace('/','__')+'-'+row['commit_hash']:
        raise ValueError('Issue/replay task mismatch')
    snapshot=json.loads(args.snapshot.read_text())
    if attempt.get('profile') and snapshot['base_commit']!=attempt['profile']['base_commit']:
        raise ValueError('Replay/snapshot base mismatch')
    task=project_source_issue(problem_statement=row['problem_statement'],repo=repo,
        source_instance_id=attempt['instance_id'],source_revision=intake['revision'],
        snapshot_commit=snapshot['snapshot_commit'])
    protocol_path=ROOT/'evidence/data/source-http-client-001/success/http-fixture/exchanges.json'
    protocol=json.loads(protocol_path.read_text())[0]['request']
    tools=protocol['tools'];allowed={x['function']['name'] for x in tools}
    if allowed!=set(attempt['available_tools']):raise ValueError('Native schema tool set mismatch')
    events=json.loads((args.attempt/'events.json').read_text())
    history=native_replay_history(events,system=protocol['messages'][0]['content'],
        problem=task['problem_statement'],allowed_tools=allowed)
    if file_record(path)!=identity:raise ValueError('Source changed during projection')
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'history.json').write_bytes(canonical_json(history['messages']))
    (args.output/'tools.json').write_bytes(canonical_json(tools))
    (args.output/'mapping.json').write_bytes(canonical_json(history['mapping']))
    (args.output/'receipt.json').write_bytes(canonical_json({
        'attempt':file_record(args.attempt/'receipt.json'),'events':file_record(args.attempt/'events.json'),
        'protocol_snapshot':file_record(protocol_path),'source_shard':identity,
        'history':file_record(args.output/'history.json'),'tools':file_record(args.output/'tools.json'),
        'exchanges':len(history['mapping']),'training_approved':False,
        'scope':history['scope'],'script':file_record(Path(__file__)),
        'projection':file_record(ROOT/'zenithsync/replay_history.py'),
        'limitations':['Initial prompt reconstructed after replay, not a teacher conditioning claim.',
                       'Action-only supervision omits original teacher reasoning.',
                       'Schema reused from pinned client fixture; same tool-name set checked.',
                       'Budget and context admission remain separate.']}))
    print({'messages':len(history['messages']),'exchanges':len(history['mapping'])})


if __name__=='__main__':main()
