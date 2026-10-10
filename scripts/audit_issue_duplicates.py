"""Fingerprint nonreserved candidate issue text without reading oracle patches.

Exact text equality is a review signal, not proof that code tasks are equivalent.
Whitespace normalization is separately marked heuristic because code whitespace
can be meaningful. No held-out issue bodies are read and no split is frozen.
"""
import argparse
import hashlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.screen_source_token_cost import read_rows
from zenithsync.artifacts import canonical_json, file_record, load_json


def fingerprint_issues(rows):
    records = []
    seen = set()
    for row in rows:
        task = row['instance_id']
        body = row['problem_statement']
        if (not isinstance(task, str) or not task or task in seen
                or not isinstance(body, str) or not body.strip()):
            raise ValueError('Unique task identity and nonempty issue text required')
        seen.add(task)
        raw = body.encode('utf-8')
        normalized = ' '.join(body.split()).encode('utf-8')
        records.append({'task_id': task, 'repo': row['repo'],
                        'utf8_bytes': len(raw),
                        'exact_sha256': hashlib.sha256(raw).hexdigest(),
                        'whitespace_sha256': hashlib.sha256(normalized).hexdigest()})
    records.sort(key=lambda r: r['task_id'])
    groups = {}
    for field in ('exact_sha256', 'whitespace_sha256'):
        indexed = {}
        for record in records:
            indexed.setdefault(record[field], []).append(record['task_id'])
        groups[field] = [{'sha256': digest, 'tasks': tasks}
                         for digest, tasks in sorted(indexed.items()) if len(tasks) > 1]
    return records, groups


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    cohort = ROOT/'evidence/data/swe-rebench-budget-cohort-001'
    registry = ROOT/'evidence/data/swe-rebench-task-join-full-001/report.json'
    official = ROOT/'evidence/p1/task-index-001/receipt.json'
    paths = [cohort/'report.json', cohort/'joined.jsonl', registry, official,
             Path(__file__), ROOT/'scripts/screen_source_token_cost.py']
    bindings = {str(p):file_record(p) for p in paths}
    if bindings[str(cohort/'joined.jsonl')] != load_json(cohort/'report.json')['joined']:
        raise ValueError('Cohort identity changed')
    reserved = {r.casefold() for r in load_json(official)['repo_counts']}
    tasks = {}
    fields = ('instance_id', 'repo', 'base_commit', 'environment_setup_commit',
              'source_task_shard_sha256', 'source_task_row')
    for row in read_rows(cohort/'joined.jsonl'):
        if row['reserved_repository_exact_match'] is not False or row['repo'].casefold() in reserved:
            raise ValueError('Reserved candidate rejected before issue access')
        task = {k:row[k] for k in fields}
        key = row['instance_id']
        if key in tasks and tasks[key] != task:
            raise ValueError('Conflicting candidate task identity')
        tasks[key] = task
    shards = load_json(registry)['task_shards']
    seen = set()
    bodies = []
    import pyarrow.parquet as pq
    for digest in sorted({r['source_task_shard_sha256'] for r in tasks.values()}):
        matching = [r for r in shards if r['identity']['sha256'] == digest]
        if len(matching) != 1:
            raise ValueError('Ambiguous source shard')
        source = matching[0]
        path = (ROOT/source['path']).resolve(strict=True)
        intake_path = (ROOT/source['intake_path']).resolve(strict=True)
        if not path.is_relative_to(ROOT) or not intake_path.is_relative_to(ROOT):
            raise ValueError('Source paths outside repository')
        bindings[str(path)] = file_record(path)
        bindings[str(intake_path)] = file_record(intake_path)
        intake = load_json(intake_path)
        if (bindings[str(path)] != source['identity']
                or bindings[str(intake_path)] != source['intake']
                or source['identity'] not in intake['downloaded'].values()
                or intake['dataset'] != 'nebius/SWE-rebench'
                or intake['revision'] != '89cdfbab4ab1bd8f5a658bb212d1b63624f4f881'):
            raise ValueError('Source provenance mismatch')
        selected = {k:v for k,v in tasks.items() if v['source_task_shard_sha256'] == digest}
        filters = [('instance_id', 'in', list(selected))]
        metadata = pq.read_table(path, columns=list(fields[:4]), filters=filters).to_pylist()
        if len(metadata) != len(selected) or len({r['instance_id'] for r in metadata}) != len(selected):
            raise ValueError('Missing or duplicate task identity')
        for row in metadata:
            if row['repo'].casefold() in reserved or any(
                    row[k] != selected[row['instance_id']][k] for k in fields[:4]):
                raise ValueError('Source metadata mismatch before issue read')
        rows = pq.read_table(path, columns=['instance_id','repo','problem_statement'],
                             filters=filters).to_pylist()
        for row in rows:
            key = row['instance_id']
            if key in seen or key not in selected or row['repo'] != selected[key]['repo']:
                raise ValueError('Unexpected deserialized issue')
            seen.add(key)
            bodies.append(row)
    if seen != set(tasks):
        raise ValueError('Incomplete issue fingerprint coverage')
    records, groups = fingerprint_issues(bodies)
    if any(file_record(Path(p)) != identity for p,identity in bindings.items()):
        raise ValueError('Audit inputs changed')
    args.output.mkdir(parents=True, exist_ok=False)
    path = args.output/'fingerprints.jsonl'
    path.write_bytes(b''.join(canonical_json(r) for r in records))
    report = {'task_count':len(records), 'inputs':bindings, 'fingerprints':file_record(path),
              'duplicate_groups':groups, 'reserved_bodies_read':False,
              'training_approved':False, 'split_frozen':False,
              'scope':'Candidate cohort issue text only; no semantic, patch, vendored-code or hidden-evaluation independence guarantee.'}
    (args.output/'report.json').write_bytes(canonical_json(report))
    print({'tasks':len(records), 'groups':{k:len(v) for k,v in groups.items()}})


if __name__ == '__main__':
    main()
