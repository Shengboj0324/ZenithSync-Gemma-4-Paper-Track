"""Extract pinned teacher actions for review, without executing source commands."""

import argparse
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record, load_json
from zenithsync.trajectory_import import convert_swe_hero_history


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--instance-id', default='biolink__biolink-model-toolkit-172')
    parser.add_argument('--trajectory-id', help='Review one exact census-bound trajectory')
    args = parser.parse_args()
    import json
    import pyarrow.parquet as pq
    census = ROOT / 'evidence/data/swe-hero-corpus-001/census'
    report = load_json(census / 'report.json')
    official = ROOT / 'evidence/p1/task-index-001/receipt.json'
    if (file_record(census / 'index.jsonl') != report['index']
            or file_record(official) != report['official_index']):
        raise ValueError('Census or reserved repository input changed')
    reserved = {name.casefold() for name in load_json(official)['repo_counts']}
    rows = [json.loads(line) for line in (census / 'index.jsonl').open()]
    rows = [row for row in rows if row['instance_id'] == args.instance_id
            and (args.trajectory_id is None or row['trajectory_id'] == args.trajectory_id)]
    if not rows or len({row['trajectory_id'] for row in rows}) != len(rows):
        raise ValueError('Unexpected source trajectory multiplicity')
    if args.trajectory_id is not None and len(rows) != 1:
        raise ValueError('Exact trajectory selection must be unique')
    args.output.mkdir(parents=True, exist_ok=False)
    summaries = []
    for row in rows:
        if row['reserved_repository_exact_match'] or row['repo'].casefold() in reserved:
            raise ValueError('Reserved repository must not be deserialized')
        sources = [s for s in report['inputs'] if s['identity']['sha256'] == row['shard_sha256']]
        if len(sources) != 1:
            raise ValueError('Ambiguous source shard')
        source = sources[0]
        path = (ROOT / source['shard']).resolve()
        if not path.is_relative_to(ROOT):
            raise ValueError('Source outside repository')
        identity = file_record(path)
        intake = load_json(ROOT / source['intake'])
        if (identity != source['identity'] or identity not in intake['downloaded'].values()
                or intake['dataset'] != 'nvidia/SWE-Hero-openhands-trajectories'
                or intake['revision'] != '150bc119e52c647216fce285fd801f16b6fd745b'):
            raise ValueError('Source provenance mismatch')
        records = pq.read_table(path, columns=['instance_id', 'trajectory_id', 'repo', 'trajectory'],
                               filters=[('trajectory_id', '=', row['trajectory_id'])]).to_pylist()
        if (len(records) != 1 or records[0]['instance_id'] != row['instance_id']
                or records[0]['repo'] != row['repo']):
            raise ValueError('Trajectory metadata linkage mismatch')
        history = convert_swe_hero_history(records[0]['trajectory'])
        actions = [{'message_index': i, **call['function']}
                   for i, message in enumerate(history['messages'])
                   for call in message.get('tool_calls', [])]
        if file_record(path) != identity:
            raise ValueError('Source changed during extraction')
        destination = args.output / row['trajectory_id']
        destination.mkdir()
        (destination / 'actions.json').write_bytes(canonical_json(actions))
        summary = {'trajectory_id': row['trajectory_id'], 'source': source, 'metadata': row,
                   'actions': file_record(destination / 'actions.json'),
                   'counts': dict(Counter(action['name'] for action in actions)),
                   'training_approved': False, 'executed': False}
        (destination / 'receipt.json').write_bytes(canonical_json(summary))
        summaries.append(summary)
        print({'trajectory': row['trajectory_id'], 'counts': summary['counts']}, flush=True)
    (args.output / 'report.json').write_bytes(canonical_json({
        'traces': summaries, 'census': file_record(census / 'report.json'),
        'script': file_record(Path(__file__)), 'training_approved': False}))


if __name__ == '__main__':
    main()
