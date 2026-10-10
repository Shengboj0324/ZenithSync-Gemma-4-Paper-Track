"""Deterministic repository coverage sampling, not an agent benchmark sample."""
import hashlib
from .artifacts import canonical_json


def stratified_repository_batch(records, *, excluded_repositories, seed, per_stratum=8):
    """Choose shortest-proxy trace per repo, then sample four cost strata.

    Equal-sized rank strata use deterministic identity tie breaks. Selection is
    deterministic hash ranking within each stratum, with no replacement. Proxy
    lengths must never be interpreted as native lengths or supervised tokens.
    """
    if type(seed) is not int or type(per_stratum) is not int or per_stratum <= 0:
        raise ValueError('Integer seed and positive stratum size required')
    excluded = {name.casefold() for name in excluded_repositories}
    seen = set()
    best = {}
    for row in records:
        for key in ('repo', 'trajectory_id', 'instance_id'):
            if not isinstance(row.get(key), str) or not row[key].strip():
                raise ValueError('Missing candidate identity')
        if (type(row.get('serialized_source_tokens')) is not int
                or row['serialized_source_tokens'] <= 0):
            raise ValueError('Positive source proxy count required')
        if row['trajectory_id'] in seen:
            raise ValueError('Duplicate trajectory identity')
        seen.add(row['trajectory_id'])
        repo = row['repo'].casefold()
        if repo in excluded:
            continue
        rank = (row['serialized_source_tokens'], row['trajectory_id'])
        if repo not in best or rank < (best[repo]['serialized_source_tokens'], best[repo]['trajectory_id']):
            best[repo] = dict(row)
    ordered = sorted(best.values(), key=lambda r: (r['serialized_source_tokens'], r['repo'].casefold(), r['trajectory_id']))
    if len(ordered) < 4 * per_stratum:
        raise ValueError('Insufficient distinct repositories for four full strata')
    result = []
    for index in range(4):
        group = ordered[index * len(ordered)//4:(index+1) * len(ordered)//4]
        def priority(row):
            return hashlib.sha256(canonical_json([seed, index, row['repo'].casefold()])).hexdigest()
        for row in sorted(group, key=lambda r: (priority(r), r['repo'].casefold()))[:per_stratum]:
            result.append({**row, 'stratum': index, 'stratum_population': len(group),
                           'selection_hash': priority(row)})
    return result
