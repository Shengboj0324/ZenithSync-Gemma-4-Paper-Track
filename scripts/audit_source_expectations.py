"""Recover pinned publisher expectations and compare all control-test identities."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record
from zenithsync.source_evaluator import compare_publisher_expectations
from zenithsync.source_task_metadata import _object


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resolution', type=Path, required=True)
    parser.add_argument('--controls', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source = json.loads(args.resolution.read_text())
    solution = source['instance_id'].rsplit('-', 1)[-1]
    import pyarrow.parquet as pq
    matches = []
    for shard in range(8):
        relative = f'data/train-{shard:05d}-of-00008.parquet'
        path = ROOT / f'artifacts/data/quarantine/r2e-gym-shard-{shard:03d}' / relative
        receipt = json.loads((ROOT / f'evidence/data/r2e-gym-shard-{shard:03d}/receipt.json').read_text())
        identity = file_record(path)
        if (receipt['dataset'] != 'R2E-Gym/R2E-Gym-Subset'
                or receipt['revision'] != '2e8108ff942f24fcb5686badfaf7f9a8808566d5'
                or identity != receipt['downloaded'][relative]):
            raise ValueError('Source task shard provenance mismatch')
        row_index = 0
        for batch in pq.ParquetFile(path).iter_batches(batch_size=128,
                columns=['repo_name', 'commit_hash', 'expected_output_json']):
            for row in batch.to_pylist():
                if row['commit_hash'] == solution and row['repo_name'] == source['repo'].split('/')[-1]:
                    expected = json.loads(row['expected_output_json'], object_pairs_hook=_object)
                    matches.append((expected, {'shard': shard, 'row_index': row_index, 'identity': identity}))
                row_index += 1
        if file_record(path) != identity:
            raise ValueError('Source task shard changed during read')
    if len(matches) != 1:
        raise ValueError('Expected exactly one matching source task')
    expected, provenance = matches[0]
    report = {'schema_version': 1, 'source': provenance, 'resolution': file_record(args.resolution),
              'script': file_record(Path(__file__)),
              'implementation': file_record(ROOT / 'zenithsync/source_evaluator.py'),
              'agent_evaluated': False, 'training_approved': False}
    for role, commit in [('base', source['git']['base_commit']), ('reference', solution)]:
        runtime_path = args.controls / role / 'runtime.json'
        runtime = json.loads(runtime_path.read_text())
        if runtime['head'] != commit or runtime['tracked_source_unchanged'] is not True:
            raise ValueError('Control source revision or integrity mismatch')
        junit = args.controls / role / 'junit.xml'
        report[role] = {**compare_publisher_expectations(junit, expected),
                        'junit': file_record(junit), 'runtime': file_record(runtime_path)}
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'publisher-expected.json').write_bytes(canonical_json(expected))
    (args.output / 'report.json').write_bytes(canonical_json(report))
    print({role: report[role]['all_cases_match_publisher_expectations'] for role in ('base', 'reference')})


if __name__ == '__main__':
    main()
