"""Metadata-only audit: never reads trajectory bodies or model patches."""

import argparse
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record, load_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--shard', type=Path, required=True)
    parser.add_argument('--intake', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    intake = load_json(args.intake)
    identity = file_record(args.shard)
    if identity not in intake['downloaded'].values():
        raise ValueError('Shard identity absent from pinned intake receipt')
    import pyarrow.parquet as pq
    parquet = pq.ParquetFile(args.shard)
    if intake['dataset'] == 'nvidia/Open-SWE-Traces':
        required = {'instance_id', 'repo', 'license', 'language', 'trajectory_id',
                    'messages', 'tools', 'resolved', 'metadata', 'hf_dataset_name'}
        history_column, origin_column = 'messages', 'hf_dataset_name'
        extra_columns = ['language', 'resolved']
    else:
        required = {'instance_id', 'repo', 'license', 'trajectory_id', 'trajectory', 'model_patch', 'dataset'}
        history_column, origin_column = 'trajectory', 'dataset'
        extra_columns = []
    if set(parquet.schema_arrow.names) != required:
        raise ValueError('Publisher schema drift')
    text_columns = ['repo', 'license', 'instance_id', 'trajectory_id', origin_column]
    columns = text_columns + extra_columns
    repositories, licenses, issues, traces, origins = (Counter() for _ in range(5))
    languages, outcomes = Counter(), Counter()
    total = 0
    for batch in parquet.iter_batches(batch_size=1024, columns=columns):
        for row in batch.to_pylist():
            if any(not isinstance(row[key], str) or not row[key].strip() for key in text_columns):
                raise ValueError('Missing or invalid source metadata')
            if extra_columns:
                if (not isinstance(row['language'], str) or not row['language'].strip()
                        or type(row['resolved']) is not int or row['resolved'] not in (-1, 0, 1)):
                    raise ValueError('Invalid language or publisher outcome')
                languages[row['language']] += 1
                outcomes[str(row['resolved'])] += 1
            repositories[row['repo']] += 1
            licenses[row['license']] += 1
            issues[(row['repo'], row['instance_id'])] += 1
            traces[row['trajectory_id']] += 1
            origins[row[origin_column]] += 1
            total += 1
    if not total or total != parquet.metadata.num_rows:
        raise ValueError('Metadata row count mismatch')
    official = load_json(ROOT / 'evidence/p1/task-index-001/receipt.json')
    reserved = {name.casefold() for name in official['repo_counts']}
    overlapping = {name: count for name, count in repositories.items() if name.casefold() in reserved}
    fields = parquet.schema_arrow.field(history_column).type.value_type
    message_fields = [field.name for field in fields]
    concentration = sum(count**2 for count in repositories.values()) / total**2
    result = {'schema_version': 1, 'status': 'metadata_audited_not_training_approved',
        'dataset': intake['dataset'], 'revision': intake['revision'], 'shard': identity,
        'read_columns': columns, 'trajectory_or_patch_bodies_read': False,
        'rows': total, 'unique_repositories': len(repositories), 'unique_repository_issue_pairs': len(issues),
        'unique_trajectory_ids': len(traces), 'duplicate_trajectory_ids': sum(v-1 for v in traces.values()),
        'repository_rows': dict(repositories), 'license_rows': dict(licenses), 'source_rows': dict(origins),
        'language_rows': dict(languages), 'publisher_outcome_rows': dict(outcomes),
        'outcome_scope': 'Publisher labels only: 1 resolved, 0 unresolved, -1 unknown; not independent verification',
        'repository_hhi': concentration, 'inverse_repository_concentration': 1 / concentration,
        'concentration_scope': 'Row-mass diversity only; not an effective independent statistical sample size',
        'official_repository_overlap_rows': overlapping,
        'overlap_scope': 'Case-insensitive exact repository IDs only; no fork, semantic or broader benchmark audit',
        'message_schema_fields': message_fields, 'explicit_tool_call_id_field': 'tool_call_id' in message_fields,
        'training_approval': False, 'replay_verified': False,
        'selection': 'Explicit input shard; not a random or representative sample',
        'source': file_record(args.intake), 'official_index_receipt': file_record(ROOT / 'evidence/p1/task-index-001/receipt.json'),
        'verifier': file_record(Path(__file__))}
    if file_record(args.shard) != identity:
        raise ValueError('Shard changed during metadata audit')
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'receipt.json').write_bytes(canonical_json(result))
    (args.output / 'schema.txt').write_text(str(parquet.schema_arrow))
    print({key: result[key] for key in ['rows', 'unique_repositories', 'unique_repository_issue_pairs',
        'license_rows', 'official_repository_overlap_rows', 'explicit_tool_call_id_field']})


if __name__ == '__main__':
    main()
