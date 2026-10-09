"""Join SWE-Hero metadata to a pinned SWE-rebench task table without oracle columns."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record, load_json
from zenithsync.source_task_metadata import project_swebench_task_identity, select_source_metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--split', choices=['filtered', 'test'], default='filtered')
    args = parser.parse_args()
    import pyarrow.parquet as pq
    source_specs = [('swe-rebench-filtered-001', 'data/filtered-00000-of-00001.parquet')]
    if args.split == 'test':
        source_specs = [(f'swe-rebench-test-{i:03d}', f'data/test-{i:05d}-of-00002.parquet') for i in range(2)]
    inputs = []
    for directory, relative in source_specs:
        source = ROOT / 'artifacts/data/quarantine' / directory / relative
        intake_path = ROOT / 'evidence/data' / directory / 'receipt.json'
        intake = load_json(intake_path)
        if intake['dataset'] != 'nebius/SWE-rebench' or intake['revision'] != '89cdfbab4ab1bd8f5a658bb212d1b63624f4f881':
            raise ValueError('Unexpected task dataset revision')
        identity = file_record(source)
        if identity != intake['downloaded'][relative]:
            raise ValueError('Task shard identity mismatch')
        inputs.append({'path': str(source.relative_to(ROOT)), 'identity': identity,
                       'intake_path': str(intake_path.relative_to(ROOT)), 'intake': file_record(intake_path)})
    census_dir = ROOT / 'evidence/data/swe-hero-corpus-001/census'
    census_path = census_dir / 'report.json'
    census = load_json(census_path)
    index = census_dir / 'index.jsonl'
    official = ROOT / 'evidence/p1/task-index-001/receipt.json'
    if file_record(index) != census['index'] or file_record(official) != census['official_index']:
        raise ValueError('Census or official index identity mismatch')
    reserved = load_json(official)['repo_counts']
    with index.open() as stream:
        traces, selection = select_source_metadata((json.loads(line) for line in stream),
            reserved_repositories=reserved, source_dataset='nebius/SWE-rebench')
    if selection['input_rows'] != census['rows']:
        raise ValueError('Census row count mismatch')
    columns = ['instance_id', 'repo', 'base_commit', 'environment_setup_commit',
               'docker_image', 'image_name', 'license_name']
    tasks = {}
    for source_record in inputs:
        source = ROOT / source_record['path']
        row_index = 0
        for batch in pq.ParquetFile(source).iter_batches(batch_size=256, columns=columns):
            for row in batch.to_pylist():
                task = project_swebench_task_identity(row)
                key = (task['repo'], task['instance_id'])
                if key in tasks:
                    raise ValueError('Duplicate task identity')
                tasks[key] = {**task, 'source_task_shard_sha256': source_record['identity']['sha256'],
                              'source_task_row': row_index}
                row_index += 1
        if file_record(source) != source_record['identity']:
            raise ValueError('Task shard changed during projection')
        source_record['rows'] = row_index
    joined, unmatched = [], []
    for row in traces:
        task = tasks.get((row['repo'], row['instance_id']))
        if task is None:
            unmatched.append(row)
        else:
            joined.append({**row, **task})
    if file_record(index) != census['index']:
        raise ValueError('Input changed during join')
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'joined.jsonl').write_bytes(b''.join(canonical_json(row) for row in joined))
    (args.output / 'unmatched.json').write_bytes(canonical_json(unmatched))
    report = {'schema_version': 1, 'source_task_count': len(tasks), 'corpus_selection': selection,
        'joined_trajectories': len(joined), 'unmatched_trajectories': len(unmatched),
        'unique_joined_tasks': len({(row['repo'], row['instance_id']) for row in joined}),
        'unique_joined_repositories': len({row['repo'] for row in joined}),
        'joined_missing_image_rows': sum(row['source_image_reference'] is None for row in joined),
        'license_declarations': dict(Counter(row['publisher_license_declaration'] or '<missing>' for row in joined)),
        'joined_missing_license_rows': sum(row['publisher_license_declaration'] is None for row in joined),
        'source_split': args.split, 'task_shards': inputs, 'census': file_record(census_path),
        'read_task_columns': columns, 'oracle_columns_read': False,
        'joined': file_record(args.output / 'joined.jsonl'),
        'source_image_digests_resolved': False, 'environment_verified': False, 'training_approved': False,
        'script': file_record(Path(__file__)), 'projection': file_record(ROOT / 'zenithsync/source_task_metadata.py'),
        'scope': 'Exact repo and instance identity join. Publisher image strings are not executable-environment qualification.'}
    (args.output / 'report.json').write_bytes(canonical_json(report))
    print({key: report[key] for key in ('source_task_count', 'joined_trajectories',
          'unmatched_trajectories', 'unique_joined_tasks', 'unique_joined_repositories', 'joined_missing_image_rows')})


if __name__ == '__main__':
    main()
