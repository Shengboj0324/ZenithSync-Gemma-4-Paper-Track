"""Extract bounded candidate issue/environment records without reading solution patches."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record, load_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--images', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    official_path = ROOT / 'evidence/p1/task-index-001/receipt.json'
    official_identity = file_record(official_path)
    reserved = {repo.casefold() for repo in load_json(official_path)['repo_counts']}
    join_path = ROOT / 'evidence/data/swe-rebench-task-join-full-001/report.json'
    join_identity = file_record(join_path)
    shards = {item['identity']['sha256']: item for item in load_json(join_path)['task_shards']}
    candidates = []
    inputs = []
    seen = set()
    for path in sorted(args.images.glob('[0-9][0-9][0-9]/result.json')):
        identity = file_record(path)
        result = load_json(path)
        task = result['task']
        key = task['instance_id']
        if task['repo'].casefold() in reserved or key in seen:
            raise ValueError('Reserved or duplicate candidate rejected before body read')
        seen.add(key)
        candidates.append(task)
        inputs.append({'path': str(path), 'identity': identity})
    if not candidates:
        raise ValueError('No resolved candidate records')
    columns = ['instance_id', 'repo', 'base_commit', 'environment_setup_commit',
               'problem_statement', 'install_config', 'requirements', 'environment',
               'FAIL_TO_PASS', 'FAIL_TO_FAIL', 'PASS_TO_PASS', 'PASS_TO_FAIL', 'license_name']
    import pyarrow.parquet as pq
    records = []
    used_sources = []
    for digest in sorted({task['source_task_shard_sha256'] for task in candidates}):
        shard = shards[digest]
        source = ROOT / shard['path']
        intake_path = ROOT / shard['intake_path']
        if file_record(source) != shard['identity'] or file_record(intake_path) != shard['intake']:
            raise ValueError('Pinned source or intake identity mismatch')
        intake = load_json(intake_path)
        if (intake['dataset'] != 'nebius/SWE-rebench'
                or intake['revision'] != '89cdfbab4ab1bd8f5a658bb212d1b63624f4f881'
                or shard['identity'] not in intake['downloaded'].values()):
            raise ValueError('Source provenance mismatch')
        selected = {task['instance_id']: task for task in candidates
                    if task['source_task_shard_sha256'] == digest}
        # Inspect identities first; a forged candidate cannot expose a reserved body.
        identities = pq.read_table(source, columns=columns[:4],
                                   filters=[('instance_id', 'in', list(selected))]).to_pylist()
        if len(identities) != len(selected) or len({row['instance_id'] for row in identities}) != len(selected):
            raise ValueError('Nonunique or missing source task')
        for row in identities:
            if row['repo'].casefold() in reserved or any(
                    row[key] != selected[row['instance_id']][key] for key in columns[:4]):
                raise ValueError('Source identity mismatch before body read')
        rows = pq.read_table(source, columns=columns,
                             filters=[('instance_id', 'in', list(selected))]).to_pylist()
        for row in rows:
            if not isinstance(row['problem_statement'], str) or not row['problem_statement'].strip():
                raise ValueError('Missing issue statement')
            counts = {}
            for group in ('FAIL_TO_PASS', 'FAIL_TO_FAIL', 'PASS_TO_PASS', 'PASS_TO_FAIL'):
                values = json.loads(row[group]) if isinstance(row[group], str) else row[group]
                if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
                    raise ValueError('Invalid publisher test group')
                counts[group] = len(values)
                del row[group]
            row['publisher_test_counts'] = counts
            row['source_shard'] = shard['identity']
            records.append(row)
        if file_record(source) != shard['identity'] or file_record(intake_path) != shard['intake']:
            raise ValueError('Source changed during extraction')
        used_sources.append(shard)
    for item in inputs:
        if file_record(Path(item['path'])) != item['identity']:
            raise ValueError('Candidate input changed')
    if file_record(official_path) != official_identity or file_record(join_path) != join_identity:
        raise ValueError('Selection policy or source registry changed')
    args.output.mkdir(parents=True, exist_ok=False)
    records_path = args.output / 'records.json'
    records_path.write_bytes(canonical_json(sorted(records, key=lambda row: row['instance_id'])))
    receipt = {'candidates': len(records), 'records': file_record(records_path),
               'inputs': inputs, 'sources': used_sources, 'official_index': official_identity,
               'source_registry': join_identity, 'read_columns': columns,
               'solution_patches_read': False, 'test_patches_read': False,
               'training_approved': False, 'script': file_record(Path(__file__)),
               'scope': 'Issue and environment triage only; no execution or training admission.'}
    (args.output / 'receipt.json').write_bytes(canonical_json(receipt))
    print({'candidates': len(records), 'output': str(args.output)})


if __name__ == '__main__':
    main()
