"""Verify pinned task shards and join identities without exporting oracle content."""

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record
from zenithsync.source_task_metadata import match_trajectory, project_r2e_task


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    import pyarrow.parquet as pq
    revision = '2e8108ff942f24fcb5686badfaf7f9a8808566d5'
    columns = ['repo_name', 'commit_hash', 'docker_image', 'parsed_commit_content',
               'execution_result_content', 'problem_statement']
    tasks = {}
    inputs = []
    for shard in range(8):
        directory = ROOT / f'artifacts/data/quarantine/r2e-gym-shard-{shard:03d}'
        receipt_path = ROOT / f'evidence/data/r2e-gym-shard-{shard:03d}/receipt.json'
        receipt = json.loads(receipt_path.read_text())
        if receipt['dataset'] != 'R2E-Gym/R2E-Gym-Subset' or receipt['revision'] != revision:
            raise ValueError('Source task revision mismatch')
        relative = f'data/train-{shard:05d}-of-00008.parquet'
        path = directory / relative
        identity = file_record(path)
        if identity != receipt['downloaded'][relative]:
            raise ValueError('Task shard identity mismatch')
        inputs.append({'path': str(path.relative_to(ROOT)), **identity})
        for batch in pq.ParquetFile(path).iter_batches(batch_size=16, columns=columns):
            for row in batch.to_pylist():
                task = project_r2e_task(row)
                key = (task['source_repo_name'], task['solution_commit'])
                if key in tasks:
                    raise ValueError('Duplicate source task identity')
                tasks[key] = task
        if file_record(path) != identity:
            raise ValueError('Source task shard changed during audit')
    source = ROOT / 'artifacts/data/quarantine/swe-hero-001/data/train-00000-of-00014.parquet'
    receipt = json.loads((ROOT / 'evidence/data/swe-hero-intake-001/receipt.json').read_text())
    identity = file_record(source)
    if identity != receipt['downloaded']['data/train-00000-of-00014.parquet']:
        raise ValueError('Trajectory shard identity mismatch')
    inputs.append({'path': str(source.relative_to(ROOT)), **identity})
    joined = []
    unmatched = []
    seen = set()
    for batch in pq.ParquetFile(source).iter_batches(batch_size=128, columns=['repo', 'instance_id', 'trajectory_id']):
        for row in batch.to_pylist():
            if row['trajectory_id'] in seen:
                raise ValueError('Duplicate trajectory identity')
            seen.add(row['trajectory_id'])
            suffix = row['instance_id'].rsplit('-', 1)[-1]
            task = tasks.get((row['repo'].split('/')[-1], suffix))
            if task is None or not match_trajectory(task, repo=row['repo'], instance_id=row['instance_id']):
                unmatched.append(row)
            else:
                joined.append({**row, **task})
    if file_record(source) != identity:
        raise ValueError('Trajectory shard changed during audit')
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'joined.jsonl').write_bytes(b''.join(canonical_json(row) for row in joined))
    (args.output / 'unmatched.json').write_bytes(canonical_json(unmatched))
    report = {
        'schema_version': 1, 'task_revision': revision, 'inputs': inputs,
        'task_count': len(tasks), 'trajectory_count': len(seen),
        'joined_count': len(joined), 'unmatched_count': len(unmatched),
        'unresolved_base_refs': sum(row['base_commit'] is None for row in joined),
        'joined_repositories': dict(sorted(Counter(row['repo'] for row in joined).items())),
        'join_scope': 'Exact instance identity plus repository basename; publisher ownership not independently verified',
        'environment_verified': False, 'training_approved': False,
        'script': file_record(Path(__file__)),
        'projection': file_record(ROOT / 'zenithsync/source_task_metadata.py'),
    }
    (args.output / 'report.json').write_bytes(canonical_json(report))
    print({key: report[key] for key in ('task_count', 'trajectory_count', 'joined_count', 'unmatched_count')})


if __name__ == '__main__':
    main()
