"""Bind static-budget candidate traces to verified SWE-rebench task metadata."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record, load_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    summary_path = ROOT / 'evidence/data/corpus-action-budget-full-001/report.json'
    summary = load_json(summary_path)
    eligible = {}
    for source in summary['inputs']:
        records = ROOT / source['path'] / 'records.jsonl'
        if file_record(records) != source['records']:
            raise ValueError('Budget records changed')
        for line in records.open():
            row = json.loads(line)
            if (row['dataset'] == 'nebius/SWE-rebench' and row['serialization_valid']
                    and row['within_40_estimated_calls'] and not row['known_adapter_flags']):
                if row['estimated_native_charged_calls'] > 40:
                    raise ValueError('Contradictory budget flag')
                if row['trajectory_id'] in eligible:
                    raise ValueError('Duplicate eligible trajectory')
                eligible[row['trajectory_id']] = row
    joined_path = ROOT / 'evidence/data/swe-rebench-task-join-full-001/joined.jsonl'
    join_report = ROOT / 'evidence/data/swe-rebench-task-join-full-001/report.json'
    joined_identity = file_record(joined_path)
    if joined_identity != load_json(join_report)['joined']:
        raise ValueError('Source task join changed')
    selected = []
    seen = set()
    for line in joined_path.open():
        task = json.loads(line)
        tid = task['trajectory_id']
        if tid not in eligible:
            continue
        if tid in seen or task['reserved_repository_exact_match']:
            raise ValueError('Duplicate or reserved candidate')
        seen.add(tid)
        if any(task[key] != eligible[tid][key] for key in ('repo', 'instance_id')):
            raise ValueError('Budget and source-task identity mismatch')
        if task['source_image_reference']:
            selected.append(task)
    if seen != set(eligible) or file_record(joined_path) != joined_identity:
        raise ValueError('Incomplete or unstable candidate join')
    args.output.mkdir(parents=True, exist_ok=False)
    selected_path = args.output / 'joined.jsonl'
    selected_path.write_bytes(b''.join(canonical_json(row) for row in selected))
    result = {'eligible_traces': len(eligible), 'image_present_traces': len(selected),
              'unique_tasks': len({(r['repo'].casefold(), r['instance_id']) for r in selected}),
              'unique_repositories': len({r['repo'].casefold() for r in selected}),
              'joined': file_record(selected_path), 'source_join': joined_identity,
              'budget_summary': file_record(summary_path), 'script': file_record(Path(__file__)),
              'training_approved': False,
              'scope': 'Cost-prioritized image-present cohort; not an unbiased performance sample or admission'}
    (args.output / 'report.json').write_bytes(canonical_json(result))
    print({key: result[key] for key in ('eligible_traces', 'image_present_traces', 'unique_tasks', 'unique_repositories')})


if __name__ == '__main__':
    main()
