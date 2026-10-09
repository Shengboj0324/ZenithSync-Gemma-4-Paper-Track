"""Inventory pinned trajectory metadata across shards without reading task bodies.

Repeated issue trajectories are counted separately from independent issues.
Publisher license labels are declarations, not source-level rights clearance.
"""
import argparse
from collections import Counter, defaultdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record, load_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources', type=Path, required=True,
                        help='JSON list of shard and intake paths relative to repository root')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    sources = load_json(args.sources)
    if not isinstance(sources, list) or not sources:
        raise ValueError('Nonempty explicit source list required')
    import pyarrow.parquet as pq
    columns = ['repo', 'instance_id', 'trajectory_id', 'license', 'dataset']
    official_path = ROOT / 'evidence/p1/task-index-001/receipt.json'
    reserved = {name.casefold() for name in load_json(official_path)['repo_counts']}
    repos, origins, traces, issues, overlap = (Counter() for _ in range(5))
    repo_licenses = defaultdict(Counter)
    seen_shards = set()
    inputs = []
    args.output.mkdir(parents=True, exist_ok=False)
    index_path = args.output / 'index.jsonl'
    with index_path.open('xb') as stream:
        for source in sources:
            if not isinstance(source, dict) or set(source) != {'shard', 'intake'}:
                raise ValueError('Expected explicit shard and intake paths')
            path, receipt_path = (ROOT / source[key] for key in ('shard', 'intake'))
            receipt = load_json(receipt_path)
            if (receipt['dataset'] != 'nvidia/SWE-Hero-openhands-trajectories'
                    or receipt['revision'] != '150bc119e52c647216fce285fd801f16b6fd745b'):
                raise ValueError('Unexpected source dataset/revision')
            identity = file_record(path)
            if identity not in receipt['downloaded'].values() or identity['sha256'] in seen_shards:
                raise ValueError('Unverified or repeated shard')
            seen_shards.add(identity['sha256'])
            parquet = pq.ParquetFile(path)
            row_index = 0
            for batch in parquet.iter_batches(batch_size=512, columns=columns):
                for row in batch.to_pylist():
                    if any(not isinstance(row[key], str) or not row[key].strip() for key in columns):
                        raise ValueError('Invalid metadata field')
                    repo = row['repo'].casefold()
                    repos[repo] += 1
                    origins[row['dataset']] += 1
                    traces[row['trajectory_id']] += 1
                    issues[(repo, row['instance_id'])] += 1
                    repo_licenses[repo][row['license']] += 1
                    if repo in reserved:
                        overlap[repo] += 1
                    stream.write(canonical_json({**row, 'shard_sha256': identity['sha256'],
                        'row_index': row_index, 'reserved_repository_exact_match': repo in reserved}))
                    row_index += 1
            if row_index != parquet.metadata.num_rows or file_record(path) != identity:
                raise ValueError('Incomplete read or source mutation')
            inputs.append({**source, 'identity': identity, 'intake_identity': file_record(receipt_path),
                           'rows': row_index})
            print({'shards_read': len(inputs), 'rows_read': sum(repos.values())}, flush=True)
    total = sum(repos.values())
    if not total:
        raise ValueError('Empty corpus')
    report = {'schema_version': 1, 'inputs': inputs, 'rows': total,
        'unique_repositories': len(repos), 'repository_rows': dict(sorted(repos.items())),
        'unique_repository_issue_pairs': len(issues), 'unique_trajectory_ids': len(traces),
        'duplicate_trajectory_id_rows': sum(n - 1 for n in traces.values()),
        'extra_trajectories_for_repeated_issues': sum(n - 1 for n in issues.values()),
        'trajectories_per_issue_histogram': dict(sorted(Counter(issues.values()).items())),
        'source_rows': dict(origins), 'publisher_license_labels_by_repository': dict(repo_licenses),
        'reserved_repository_exact_match_rows': dict(overlap),
        'index': file_record(index_path), 'official_index': file_record(official_path),
        'sources_specification': file_record(args.sources), 'script': file_record(Path(__file__)),
        'training_approved': False, 'trajectory_or_patch_bodies_read': False,
        'limitations': ['Repository comparison is case-insensitive exact name only, not fork or semantic isolation.',
                       'Repeated trajectories of one issue are not independent evaluation samples.',
                       'Publisher license labels do not replace source notices.',
                       'No token, quality, replay, rights or training admission is established.']}
    (args.output / 'report.json').write_bytes(canonical_json(report))
    print({key: report[key] for key in ('rows', 'unique_repositories',
          'unique_repository_issue_pairs', 'unique_trajectory_ids', 'duplicate_trajectory_id_rows',
          'reserved_repository_exact_match_rows')})


if __name__ == '__main__':
    main()
