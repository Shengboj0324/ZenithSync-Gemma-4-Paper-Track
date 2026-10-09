"""Audit source histories structurally, retaining hashes rather than bodies."""

import argparse
from collections import Counter
import hashlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record, load_json
from zenithsync.trajectory_import import convert_swe_hero_history, SourceHistoryError
from zenithsync.gemma_trajectory import project_pre_action_text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--shard', type=Path, required=True)
    parser.add_argument('--intake', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--project-pre-action-text', action='store_true')
    args = parser.parse_args()
    identity = file_record(args.shard)
    intake = load_json(args.intake)
    if identity not in intake['downloaded'].values():
        raise ValueError('Shard differs from pinned source intake')
    import pyarrow.parquet as pq
    parquet = pq.ParquetFile(args.shard)
    args.output.mkdir(parents=True, exist_ok=False)
    statuses, roles, tools, call_sizes = (Counter() for _ in range(4))
    counts = {'rows': 0, 'converted': 0, 'messages': 0, 'inferred_response_links': 0}
    chronology = {'nonempty_assistant_text_with_call': 0, 'followed_by_tool_response': 0,
                  'projected_messages': 0}
    seen = set()
    with (args.output / 'row-audit.jsonl').open('xb') as output:
        for batch in parquet.iter_batches(batch_size=8, columns=['repo', 'instance_id', 'trajectory_id', 'trajectory']):
            for row in batch.to_pylist():
                if row['trajectory_id'] in seen:
                    raise ValueError('Duplicate trajectory identity')
                seen.add(row['trajectory_id'])
                history = row['trajectory']
                raw_hash = hashlib.sha256(canonical_json(history)).hexdigest()
                record = {key: row[key] for key in ['repo', 'instance_id', 'trajectory_id']}
                record.update(source_history_sha256=raw_hash, training_approved=False)
                counts['rows'] += 1
                try:
                    converted = convert_swe_hero_history(history)
                except SourceHistoryError as error:
                    reason = str(error)
                    statuses[reason] += 1
                    record.update(status='rejected', reason=reason)
                else:
                    statuses['structurally_converted'] += 1
                    messages = converted['messages']
                    for index, message in enumerate(messages):
                        if message['role'] == 'assistant' and message.get('tool_calls') and message['content'].strip():
                            chronology['nonempty_assistant_text_with_call'] += 1
                            if index + 1 < len(messages) and messages[index + 1]['role'] == 'tool':
                                chronology['followed_by_tool_response'] += 1
                    if args.project_pre_action_text:
                        projection = project_pre_action_text(messages)
                        chronology['projected_messages'] += len(projection['transformations'])
                        record.update(projected_history_sha256=projection['projected_history_sha256'],
                            projection_provenance_sha256=hashlib.sha256(canonical_json(projection['transformations'])).hexdigest(),
                            projected_messages=len(projection['transformations']))
                    counts['converted'] += 1
                    counts['messages'] += len(messages)
                    counts['inferred_response_links'] += len(converted['response_links'])
                    for message in messages:
                        roles[message['role']] += 1
                        calls = message.get('tool_calls', [])
                        if calls:
                            call_sizes[len(calls)] += 1
                        for call in calls:
                            tools[call['function']['name']] += 1
                    record.update(status='structurally_converted', message_count=len(messages),
                        inferred_response_links=len(converted['response_links']),
                        converted_history_sha256=hashlib.sha256(canonical_json(messages)).hexdigest(),
                        linkage_provenance_sha256=hashlib.sha256(canonical_json(converted['response_links'])).hexdigest(),
                        terminal_status=converted['terminal_status'])
                output.write(canonical_json(record))
    if counts['rows'] != parquet.metadata.num_rows or file_record(args.shard) != identity:
        raise ValueError('Row count mismatch or source changed during audit')
    (args.output / 'receipt.json').write_bytes(canonical_json({
        'schema_version': 1, 'status': 'structural_conversion_audited_not_training_approved',
        'dataset': intake['dataset'], 'revision': intake['revision'], 'shard': identity,
        'counts': counts, 'outcomes': dict(statuses), 'roles': dict(roles), 'tools': dict(tools),
        'chronology': chronology, 'pre_action_text_projection': args.project_pre_action_text,
        'calls_per_assistant_message': dict(call_sizes),
        'row_audit': file_record(args.output / 'row-audit.jsonl'),
        'sources': {name: file_record(ROOT / name) for name in
                    ['zenithsync/trajectory_import.py', 'zenithsync/conversation.py', 'zenithsync/gemma_trajectory.py',
                     'scripts/audit_trajectory_conversion.py']},
        'scope': 'Programmatic history inspection; no model_patch column, command execution, replay, native mask or success qualification'}))
    print({'counts': counts, 'outcomes': dict(statuses), 'tools': dict(tools)})


if __name__ == '__main__':
    main()
