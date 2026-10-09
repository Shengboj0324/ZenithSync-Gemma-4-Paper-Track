"""Census pinned publisher grading contracts; do not infer executable correctness."""

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record
from zenithsync.source_task_metadata import _object, _commit

REVISION = '2e8108ff942f24fcb5686badfaf7f9a8808566d5'
ALLOWED = frozenset({'PASSED', 'FAILED', 'ERROR', 'SKIPPED'})


def summarize_contract(raw):
    """Report invalid contracts without copying evaluator test identities."""
    try:
        expected = json.loads(raw, object_pairs_hook=_object)
    except (ValueError, TypeError):
        return {'valid': False, 'reason': 'invalid_or_duplicate_json'}
    if not isinstance(expected, dict) or not expected:
        return {'valid': False, 'reason': 'empty_or_non_mapping'}
    if any(not isinstance(k, str) or not k.strip() or not isinstance(v, str)
           or v not in ALLOWED for k, v in expected.items()):
        return {'valid': False, 'reason': 'unsupported_identity_or_status'}
    counts = Counter(expected.values())
    return {'valid': True, 'publisher_key_count': len(expected),
            'status_counts': dict(sorted(counts.items())),
            'all_passed_contract': counts['PASSED'] == len(expected),
            'has_passed_expectation': counts['PASSED'] > 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    import pyarrow.parquet as pq
    records, inputs, seen = [], [], set()
    for shard in range(8):
        relative = f'data/train-{shard:05d}-of-00008.parquet'
        path = ROOT / f'artifacts/data/quarantine/r2e-gym-shard-{shard:03d}' / relative
        receipt_path = ROOT / f'evidence/data/r2e-gym-shard-{shard:03d}/receipt.json'
        receipt = json.loads(receipt_path.read_text())
        identity = file_record(path)
        if (receipt['dataset'] != 'R2E-Gym/R2E-Gym-Subset'
                or receipt['revision'] != REVISION
                or receipt['downloaded'][relative] != identity):
            raise ValueError('Pinned input provenance mismatch')
        inputs.append({'path': str(path.relative_to(ROOT)), **identity,
                       'receipt': file_record(receipt_path)})
        row_index = 0
        for batch in pq.ParquetFile(path).iter_batches(batch_size=128,
                columns=['repo_name', 'commit_hash', 'expected_output_json']):
            for row in batch.to_pylist():
                repo, commit = row['repo_name'], _commit(row['commit_hash'])
                if not isinstance(repo, str) or not repo.strip():
                    raise ValueError('Missing repository identity')
                key = (repo, commit)
                if key in seen:
                    raise ValueError('Duplicate task identity')
                seen.add(key)
                records.append({'repo': repo, 'solution_commit': commit,
                                'shard': shard, 'row_index': row_index,
                                **summarize_contract(row['expected_output_json'])})
                row_index += 1
        if file_record(path) != identity:
            raise ValueError('Input changed during census')
    groups = defaultdict(list)
    for record in records:
        groups[record['repo']].append(record)
    summaries = {}
    for repo, rows in sorted(groups.items()):
        valid = [row for row in rows if row['valid']]
        counts = Counter()
        for row in valid:
            counts.update(row['status_counts'])
        summaries[repo] = {
            'tasks': len(rows), 'valid_contracts': len(valid),
            'invalid_reasons': dict(Counter(row['reason'] for row in rows if not row['valid'])),
            'all_passed_contracts': sum(row['all_passed_contract'] for row in valid),
            'no_passed_expectation': sum(not row['has_passed_expectation'] for row in valid),
            'publisher_key_occurrences': sum(row['publisher_key_count'] for row in valid),
            'status_occurrences': dict(sorted(counts.items())),
        }
    args.output.mkdir(parents=True, exist_ok=False)
    records_path = args.output / 'contracts.jsonl'
    records_path.write_bytes(b''.join(canonical_json(row) for row in records))
    report = {'schema_version': 1, 'revision': REVISION, 'inputs': inputs,
              'task_count': len(records), 'repositories': summaries,
              'records': file_record(records_path), 'script': file_record(Path(__file__)),
              'training_approved': False, 'runtime_validated': False,
              'limitations': ['Publisher keys can collapse multiple runtime test cases.',
                              'Counts are occurrences across tasks, not unique tests.',
                              'Expected failures are contract states, not successful tests.',
                              'Metadata validity does not establish base/reference separation.']}
    (args.output / 'report.json').write_bytes(canonical_json(report))
    print(json.dumps({'task_count': len(records), 'repositories': summaries}, indent=2))


if __name__ == '__main__':
    main()
