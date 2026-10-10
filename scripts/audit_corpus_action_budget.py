"""Screen one pinned corpus shard for replay cost, excluding reserved tasks.

Counts are static estimates, not execution, context-fit, rights or admission.
One shard per immutable output allows failures to be retried independently.
"""

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.plan_trajectory_replays import action_budget
from zenithsync.artifacts import canonical_json, file_record, load_json
from zenithsync.trajectory_import import convert_swe_hero_history, SourceHistoryError


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--shard-index', type=int, choices=range(14), required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    census = ROOT / 'evidence/data/swe-hero-corpus-001/census'
    report = load_json(census / 'report.json')
    index = census / 'index.jsonl'
    official = ROOT / 'evidence/p1/task-index-001/receipt.json'
    if file_record(index) != report['index'] or file_record(official) != report['official_index']:
        raise ValueError('Census binding changed')
    source = report['inputs'][args.shard_index]
    path = (ROOT / source['shard']).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError('Source path escapes repository')
    identity = file_record(path)
    intake = load_json(ROOT / source['intake'])
    if (identity != source['identity'] or identity not in intake['downloaded'].values()
            or intake['dataset'] != 'nvidia/SWE-Hero-openhands-trajectories'
            or intake['revision'] != '150bc119e52c647216fce285fd801f16b6fd745b'):
        raise ValueError('Source provenance mismatch')
    reserved = {repo.casefold() for repo in load_json(official)['repo_counts']}
    selected = {}
    excluded = 0
    for line in index.open():
        row = json.loads(line)
        if row['shard_sha256'] != identity['sha256']:
            continue
        is_reserved = row['repo'].casefold() in reserved
        if row['reserved_repository_exact_match'] is not is_reserved:
            raise ValueError('Reserved repository flag inconsistent')
        if is_reserved:
            excluded += 1
            continue
        if row['trajectory_id'] in selected:
            raise ValueError('Duplicate trajectory identity')
        selected[row['trajectory_id']] = row
    import pyarrow.dataset as ds
    scanner = ds.dataset(path, format='parquet').scanner(
        columns=['trajectory_id', 'instance_id', 'repo', 'trajectory'], batch_size=16,
        filter=ds.field('trajectory_id').isin(list(selected)))
    args.output.mkdir(parents=True, exist_ok=False)
    seen = set()
    counts = Counter()
    repositories = Counter()
    records = args.output / 'records.jsonl'
    with records.open('xb') as output:
        for batch in scanner.to_batches():
            for row in batch.to_pylist():
                tid = row['trajectory_id']
                if tid in seen or tid not in selected:
                    raise ValueError('Unexpected or duplicate deserialized row')
                metadata = selected[tid]
                if any(row[key] != metadata[key] for key in ('repo', 'instance_id')):
                    raise ValueError('Source metadata mismatch')
                seen.add(tid)
                item = {key: metadata[key] for key in ('repo', 'instance_id', 'trajectory_id', 'dataset')}
                try:
                    history = convert_swe_hero_history(row['trajectory'])
                    budget = action_budget(history['messages'])
                    item.update(budget, serialization_valid=True)
                    fit = budget['estimated_native_charged_calls'] <= 40
                    item['within_40_estimated_calls'] = fit
                    counts['serialization_valid'] += 1
                    counts['within_40_estimated_calls'] += fit
                    if fit and not budget['known_adapter_flags']:
                        counts['within_40_without_known_flags'] += 1
                        repositories[row['repo']] += 1
                except SourceHistoryError as error:
                    item.update(serialization_valid=False, reason=str(error))
                    counts['serialization_invalid'] += 1
                item['training_approved'] = False
                output.write(canonical_json(item))
    if seen != set(selected) or file_record(path) != identity:
        raise ValueError('Incomplete or unstable source audit')
    result = {'status': 'static_audit_complete', 'source': source, 'rows': len(seen),
              'excluded_reserved_rows': excluded, 'counts': dict(counts),
              'budget_fit_repository_counts': dict(sorted(repositories.items())),
              'records': file_record(records), 'census': file_record(census / 'report.json'),
              'script': file_record(Path(__file__)), 'training_approved': False,
              'scope': 'One estimated charged call per shell/editor action; no replay or token fit established'}
    (args.output / 'report.json').write_bytes(canonical_json(result))
    print({'rows': len(seen), 'excluded_reserved_rows': excluded, **dict(counts)})


if __name__ == '__main__':
    main()
