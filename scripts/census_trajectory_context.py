"""Measure complete projected native histories; never truncate or admit training data."""

import argparse
from collections import defaultdict
import hashlib
from importlib.metadata import version
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record, load_json
from zenithsync.gemma_trajectory import project_pre_action_text
from zenithsync.trajectory_import import convert_swe_hero_history


def summarize(lengths, caps):
    """Exact finite-census counts, with explicitly defined nearest-rank quantiles."""
    if not lengths or any(type(n) is not int or n <= 0 for n in lengths):
        raise ValueError('Expected nonempty positive integer token lengths')
    if not caps or any(type(n) is not int or n <= 0 for n in caps) or len(set(caps)) != len(caps):
        raise ValueError('Expected distinct positive integer context caps')
    ordered = sorted(lengths)
    count = len(ordered)
    return {'histories': count, 'input_tokens': sum(ordered),
            'min': ordered[0], 'max': ordered[-1],
            'quantile_rule': 'nearest rank: sorted[ceil(p*n)-1]',
            'quantiles': {str(p): ordered[(p * count + 99) // 100 - 1] for p in (50, 90, 95, 99)},
            'caps': {str(cap): {'within_cap': sum(n <= cap for n in ordered),
                              'over_cap': sum(n > cap for n in ordered),
                              'input_tokens_in_within_cap_histories': sum(n for n in ordered if n <= cap)}
                     for cap in sorted(caps)}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--shard', type=Path, required=True)
    parser.add_argument('--intake', type=Path, required=True)
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if version('transformers') != '5.13.1' or version('tokenizers') != '0.22.2':
        raise ValueError('Qualified tokenizer versions required')
    intake = load_json(args.intake)
    identity = file_record(args.shard)
    if identity not in intake['downloaded'].values():
        raise ValueError('Shard differs from pinned intake')
    manifest = load_json(ROOT / 'evidence/p1/model-intake-001/model-manifest.json')
    assets = {}
    for name in ('chat_template.jinja', 'tokenizer.json', 'tokenizer_config.json'):
        expected = next(row for row in manifest['files'] if row['path'] == name)
        assets[name] = file_record(args.model / name)
        if assets[name] != {key: expected[key] for key in ('sha256', 'size_bytes')}:
            raise ValueError('Tokenizer identity mismatch')
    import pyarrow.parquet as pq
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True, trust_remote_code=False)
    parquet = pq.ParquetFile(args.shard)
    args.output.mkdir(parents=True, exist_ok=False)
    by_repo = defaultdict(list)
    seen = set()
    records_path = args.output / 'lengths.jsonl'
    with records_path.open('xb') as stream:
        for batch in parquet.iter_batches(batch_size=8, columns=['repo', 'trajectory_id', 'trajectory']):
            for row in batch.to_pylist():
                trace_id = row['trajectory_id']
                if trace_id in seen:
                    raise ValueError('Duplicate trajectory ID')
                seen.add(trace_id)
                converted = convert_swe_hero_history(row['trajectory'])
                projected = project_pre_action_text(converted['messages'])
                ids = tokenizer.apply_chat_template(projected['messages'], tokenize=True,
                    add_generation_prompt=False, truncation=False, padding=False, return_dict=False)
                if not isinstance(ids, list) or not ids or any(type(n) is not int or n < 0 for n in ids):
                    raise ValueError('Expected one nonempty token-ID sequence')
                by_repo[row['repo']].append(len(ids))
                stream.write(canonical_json({'repo': row['repo'], 'trajectory_id': trace_id,
                    'input_tokens': len(ids), 'projected_history_sha256': projected['projected_history_sha256'],
                    'input_ids_sha256': hashlib.sha256(canonical_json(ids)).hexdigest()}))
                if len(seen) % 25 == 0:
                    stream.flush()
                    print({'completed': len(seen), 'expected': parquet.metadata.num_rows}, flush=True)
    if len(seen) != parquet.metadata.num_rows or file_record(args.shard) != identity:
        raise ValueError('Incomplete census or changed source')
    if any(file_record(args.model / name) != record for name, record in assets.items()):
        raise ValueError('Tokenizer changed during census')
    caps = [8192, 16384, 32768, 65536, 131072]
    receipt = {'schema_version': 1, 'status': 'context_census_complete_not_training_approved',
        'dataset': intake['dataset'], 'revision': intake['revision'], 'shard': identity,
        'tokenizer_assets': assets, 'records': file_record(records_path),
        'overall': summarize([n for values in by_repo.values() for n in values], caps),
        'by_repository': {repo: summarize(values, caps) for repo, values in sorted(by_repo.items())},
        'versions': {name: version(name) for name in ('transformers', 'tokenizers', 'pyarrow')},
        'sources': {name: file_record(ROOT / name) for name in (
            'scripts/census_trajectory_context.py', 'zenithsync/trajectory_import.py',
            'zenithsync/gemma_trajectory.py', 'zenithsync/conversation.py')},
        'scope': 'Exact complete-history input lengths for this shard only. No tool schemas, '
                 'mask qualification, output-generation reserve, truncation, replay, GPU fit or training admission. '
                 'Input tokens include prompts and tool results; these are not supervised-token counts.'}
    (args.output / 'receipt.json').write_bytes(canonical_json(receipt))
    print(receipt['overall'], flush=True)


if __name__ == '__main__':
    main()
