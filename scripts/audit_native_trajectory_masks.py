"""Deterministic per-repository native mask audit; no truncation or training."""

import argparse
import hashlib
from importlib.metadata import version
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record, load_json
from zenithsync.trajectory_import import convert_swe_hero_history, SOURCE_TOOLS
from zenithsync.training_masks import assistant_training_tokens
from zenithsync.gemma_trajectory import project_pre_action_text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--shard', type=Path, required=True)
    parser.add_argument('--intake', type=Path, required=True)
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--project-pre-action-text', action='store_true')
    args = parser.parse_args()
    if version('transformers') != '5.13.1' or version('tokenizers') != '0.22.2':
        raise ValueError('Qualified tokenizer versions required')
    intake = load_json(args.intake)
    identity = file_record(args.shard)
    if identity not in intake['downloaded'].values():
        raise ValueError('Shard differs from pinned intake')
    manifest = load_json(ROOT / 'evidence/p1/model-intake-001/model-manifest.json')
    for name in ['chat_template.jinja', 'tokenizer.json', 'tokenizer_config.json']:
        row = next(item for item in manifest['files'] if item['path'] == name)
        if file_record(args.model / name) != {key: row[key] for key in ['sha256', 'size_bytes']}:
            raise ValueError('Tokenizer identity mismatch')
    import pyarrow.parquet as pq
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True, trust_remote_code=False)
    template_sha = file_record(args.model / 'chat_template.jinja')['sha256']
    parquet = pq.ParquetFile(args.shard)
    selected = {}
    for batch in parquet.iter_batches(columns=['repo', 'trajectory_id']):
        for row in batch.to_pylist():
            rank = (hashlib.sha256((intake['revision'] + '\0' + row['trajectory_id']).encode()).hexdigest(),
                    row['trajectory_id'])
            if row['repo'] not in selected or rank < selected[row['repo']]:
                selected[row['repo']] = rank
    wanted = {value[1] for value in selected.values()}
    args.output.mkdir(parents=True, exist_ok=False)
    selection = {'rule': 'minimum SHA256(revision + NUL + trajectory_id), then ID, within each repository',
                 'selected': {repo: value[1] for repo, value in selected.items()},
                 'scope': 'Deterministic diagnostic selection, not a random population estimator'}
    (args.output / 'selection.json').write_bytes(canonical_json(selection))
    records = []
    for batch in parquet.iter_batches(batch_size=8, columns=['repo', 'trajectory_id', 'trajectory']):
        for row in batch.to_pylist():
            if row['trajectory_id'] not in wanted:
                continue
            converted = convert_swe_hero_history(row['trajectory'])
            record = {'repo': row['repo'], 'trajectory_id': row['trajectory_id'],
                      'history_sha256': hashlib.sha256(canonical_json(converted['messages'])).hexdigest()}
            messages = converted['messages']
            if args.project_pre_action_text:
                projection = project_pre_action_text(messages)
                messages = projection['messages']
                record.update(projected_history_sha256=projection['projected_history_sha256'],
                    mapped_assistant_messages=len(projection['transformations']),
                    projection_provenance_sha256=hashlib.sha256(canonical_json(projection['transformations'])).hexdigest())
            try:
                encoded = assistant_training_tokens(tokenizer, messages,
                    template_sha256=template_sha, allowed_tools=set(SOURCE_TOOLS), terminal_call_tools={'finish'})
            except ValueError:
                # Keep a failed selected case rather than replacing it with an easier one.
                record.update(status='native_mask_rejected')
            else:
                count = len(encoded['input_ids'])
                record.update(status='native_mask_passed', input_tokens=count,
                    supervised_tokens=sum(value != -100 for value in encoded['labels'][1:]),
                    input_sha256=hashlib.sha256(canonical_json(encoded['input_ids'])).hexdigest(),
                    labels_sha256=hashlib.sha256(canonical_json(encoded['labels'])).hexdigest(),
                    exceeds_qualified_24_token_fixture=count > 24,
                    exceeds_proposed_64_token_pilot_cap=count > 64,
                    exceeds_current_32768_serving_cap=count > 32768)
            records.append(record)
            (args.output / 'cases.json').write_bytes(canonical_json(records))
            print({'completed_cases': len(records), 'selected_cases': len(wanted),
                   'status': record['status'], 'input_tokens': record.get('input_tokens')}, flush=True)
    if len(records) != len(wanted) or file_record(args.shard) != identity:
        raise ValueError('Missing selected rows or changed source')
    (args.output / 'receipt.json').write_bytes(canonical_json({
        'schema_version': 1, 'status': 'diagnostic_complete_not_training_approved',
        'shard': identity, 'selection': file_record(args.output / 'selection.json'),
        'cases': records, 'passed': sum(row['status'] == 'native_mask_passed' for row in records),
        'pre_action_text_projection': args.project_pre_action_text,
        'versions': {name: version(name) for name in ['transformers', 'tokenizers', 'pyarrow']},
        'sources': {name: file_record(ROOT / name) for name in ['zenithsync/training_masks.py',
                   'zenithsync/trajectory_import.py', 'zenithsync/gemma_trajectory.py',
                   'scripts/audit_native_trajectory_masks.py']},
        'scope': 'Native rendering/token identity and span masking only; no tool schemas supplied, truncation, replay or training'}))


if __name__ == '__main__':
    main()
