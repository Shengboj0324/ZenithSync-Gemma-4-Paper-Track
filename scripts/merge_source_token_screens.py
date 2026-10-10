"""Merge complete hash-bound source token screens into a cost-ranked cohort."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.screen_source_token_cost import read_rows
from zenithsync.artifacts import canonical_json, file_record, load_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--screen', type=Path, action='append', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    cohort_path = ROOT/'evidence/data/swe-rebench-budget-cohort-001/joined.jsonl'
    cohort_report = ROOT/'evidence/data/swe-rebench-budget-cohort-001/report.json'
    cohort_identity = file_record(cohort_path)
    if cohort_identity != load_json(cohort_report)['joined']:
        raise ValueError('Cohort changed')
    expected = {}
    for row in read_rows(cohort_path):
        if row['trajectory_id'] in expected:
            raise ValueError('Duplicate cohort trajectory')
        expected[row['trajectory_id']] = row
    inputs = {str(cohort_path): cohort_identity,
              str(cohort_report): file_record(cohort_report),
              str(Path(__file__)): file_record(Path(__file__))}
    rows = {}
    directories = set()
    for directory in args.screen:
        resolved = directory.resolve(strict=True)
        if resolved in directories:
            raise ValueError('Repeated screening directory')
        directories.add(resolved)
        report_path = directory/'report.json'
        records_path = directory/'ranked.jsonl'
        inputs[str(report_path)] = file_record(report_path)
        report = load_json(report_path)
        if (report['status'] != 'source_cost_screen_complete'
                or report['training_approved'] is not False
                or report['native_context_measured'] is not False
                or file_record(records_path) != report['records']):
            raise ValueError('Invalid screening report')
        inputs[str(records_path)] = report['records']
        for path, identity in report['bindings'].items():
            if path in inputs and inputs[path] != identity:
                raise ValueError('Inconsistent screening input identity')
            inputs[path] = identity
        records = read_rows(records_path)
        if len(records) != report['rows']:
            raise ValueError('Screen count mismatch')
        for row in records:
            tid = row['trajectory_id']
            if tid in rows or tid not in expected:
                raise ValueError('Duplicate or unknown screened trace')
            metadata = expected[tid]
            if (any(row[k] != metadata[k] for k in ('repo', 'instance_id'))
                    or row['source']['sha256'] != metadata['shard_sha256']
                    or type(row['serialized_source_tokens']) is not int
                    or row['serialized_source_tokens'] <= 0
                    or row['training_approved'] is not False
                    or row['native_context_measured'] is not False):
                raise ValueError('Invalid screened record')
            rows[tid] = row
    if set(rows) != set(expected):
        raise ValueError('Screening does not cover exact cohort')
    if any(file_record(Path(path)) != identity for path, identity in inputs.items()):
        raise ValueError('Screening input drift')
    ranked = sorted(rows.values(), key=lambda r: (r['serialized_source_tokens'], r['trajectory_id']))
    args.output.mkdir(parents=True, exist_ok=False)
    records_path = args.output/'ranked.jsonl'
    records_path.write_bytes(b''.join(canonical_json(r) for r in ranked))
    report = {'rows': len(ranked), 'inputs': inputs, 'records': file_record(records_path),
              'training_approved': False, 'native_context_measured': False,
              'scope': 'Complete cost-screened cohort; source token ranking only, not native fit or agent performance'}
    (args.output/'report.json').write_bytes(canonical_json(report))
    print({'rows': len(ranked), 'shortest': ranked[:5]})


if __name__ == '__main__':
    main()
