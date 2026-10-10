"""Rank pinned source histories by serialized token cost, without executing them.

This proxy includes source observations and reasoning. It is neither native
context length nor a lower/upper bound on that length; it cannot admit training.
"""

import argparse
from importlib.metadata import version
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record, load_json
from zenithsync.trajectory_import import convert_swe_hero_history


def select_rows(cohort, census, *, shard_sha256, reserved):
    """Bind cohort identities to the census before deserializing any history."""
    indexed = {}
    for row in census:
        tid = row['trajectory_id']
        if tid in indexed:
            raise ValueError('Duplicate census trajectory')
        indexed[tid] = row
    selected = {}
    seen = set()
    for row in cohort:
        tid = row['trajectory_id']
        if tid in seen:
            raise ValueError('Duplicate cohort trajectory')
        seen.add(tid)
        source = indexed.get(tid)
        keys = ('instance_id', 'repo', 'dataset', 'shard_sha256', 'row_index')
        if source is None or any(row[k] != source[k] for k in keys):
            raise ValueError('Cohort identity differs from census')
        if (row['reserved_repository_exact_match'] is not False
                or source['reserved_repository_exact_match'] is not False
                or row['repo'].casefold() in reserved):
            raise ValueError('Reserved repository in screening cohort')
        if row['shard_sha256'] == shard_sha256:
            selected[tid] = row
    return selected


def read_rows(path):
    with path.open() as stream:
        return [json.loads(line) for line in stream]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--shard-index', type=int, choices=range(14), required=True)
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if version('tokenizers') != '0.22.2':
        raise ValueError('Pinned tokenizers 0.22.2 required')
    census_dir = ROOT / 'evidence/data/swe-hero-corpus-001/census'
    cohort_dir = ROOT / 'evidence/data/swe-rebench-budget-cohort-001'
    official = ROOT / 'evidence/p1/task-index-001/receipt.json'
    manifest = ROOT / 'evidence/p1/model-intake-001/model-manifest.json'
    paths = [census_dir/'report.json', census_dir/'index.jsonl',
             cohort_dir/'report.json', cohort_dir/'joined.jsonl', official,
             manifest, Path(__file__), ROOT/'zenithsync/trajectory_import.py',
             ROOT/'zenithsync/conversation.py', ROOT/'zenithsync/artifacts.py']
    bindings = {str(p): file_record(p) for p in paths}
    census = load_json(census_dir/'report.json')
    cohort = load_json(cohort_dir/'report.json')
    if (bindings[str(census_dir/'index.jsonl')] != census['index']
            or bindings[str(official)] != census['official_index']
            or bindings[str(cohort_dir/'joined.jsonl')] != cohort['joined']):
        raise ValueError('Screening registry binding changed')
    source = census['inputs'][args.shard_index]
    shard = (ROOT/source['shard']).resolve()
    intake_path = (ROOT/source['intake']).resolve()
    if not shard.is_relative_to(ROOT) or not intake_path.is_relative_to(ROOT):
        raise ValueError('Source path outside repository')
    bindings[str(shard)] = file_record(shard)
    bindings[str(intake_path)] = file_record(intake_path)
    intake = load_json(intake_path)
    if (bindings[str(shard)] != source['identity']
            or bindings[str(intake_path)] != source['intake_identity']
            or source['identity'] not in intake['downloaded'].values()
            or intake['dataset'] != 'nvidia/SWE-Hero-openhands-trajectories'
            or intake['revision'] != '150bc119e52c647216fce285fd801f16b6fd745b'):
        raise ValueError('Source provenance mismatch')
    reserved = {r.casefold() for r in load_json(official)['repo_counts']}
    selected = select_rows(read_rows(cohort_dir/'joined.jsonl'),
        read_rows(census_dir/'index.jsonl'),
        shard_sha256=source['identity']['sha256'], reserved=reserved)
    tokenizer_path = args.model/'tokenizer.json'
    asset = [r for r in load_json(manifest)['files'] if r['path'] == 'tokenizer.json']
    bindings[str(tokenizer_path)] = file_record(tokenizer_path)
    if len(asset) != 1 or bindings[str(tokenizer_path)] != {
            k: asset[0][k] for k in ('sha256', 'size_bytes')}:
        raise ValueError('Model tokenizer identity mismatch')
    from tokenizers import Tokenizer
    import pyarrow as pa
    import pyarrow.dataset as ds
    tokenizer = Tokenizer.from_file(str(tokenizer_path))
    tokenizer.no_truncation()
    tokenizer.no_padding()
    scanner = ds.dataset(shard, format='parquet').scanner(batch_size=8,
        columns=['trajectory_id', 'instance_id', 'repo', 'trajectory'],
        filter=ds.field('trajectory_id').isin(pa.array(list(selected), type=pa.string())))
    args.output.mkdir(parents=True, exist_ok=False)
    seen = set()
    records = []
    for batch in scanner.to_batches():
        for row in batch.to_pylist():
            tid = row['trajectory_id']
            if tid not in selected or tid in seen:
                raise ValueError('Unexpected or repeated source row')
            metadata = selected[tid]
            if any(row[k] != metadata[k] for k in ('instance_id', 'repo')):
                raise ValueError('Deserialized source identity mismatch')
            seen.add(tid)
            messages = convert_swe_hero_history(row['trajectory'])['messages']
            serialized = canonical_json(messages)
            count = len(tokenizer.encode(serialized.decode('utf-8'),
                                         add_special_tokens=False).ids)
            records.append({'trajectory_id': tid, 'instance_id': row['instance_id'],
                'repo': row['repo'], 'source': source['identity'],
                'serialized_source_tokens': count, 'serialized_bytes': len(serialized),
                'training_approved': False, 'native_context_measured': False})
    if seen != set(selected):
        raise ValueError('Incomplete source screening')
    if any(file_record(Path(p)) != identity for p, identity in bindings.items()):
        raise ValueError('Screening inputs changed')
    records.sort(key=lambda r: (r['serialized_source_tokens'], r['trajectory_id']))
    result_path = args.output/'ranked.jsonl'
    with result_path.open('xb') as stream:
        for row in records:
            stream.write(canonical_json(row))
    report = {'status': 'source_cost_screen_complete', 'rows': len(records),
        'bindings': bindings, 'records': file_record(result_path),
        'versions': {'tokenizers': version('tokenizers'), 'pyarrow': version('pyarrow')},
        'training_approved': False, 'native_context_measured': False,
        'scope': 'Ranking proxy only: canonical converted source message JSON, no chat template, '
                 'special tokens, padding or truncation; no replay, correctness or native fit claim'}
    (args.output/'report.json').write_bytes(canonical_json(report))
    print({'rows': len(records), 'shortest': records[:3]})


if __name__ == '__main__':
    main()
