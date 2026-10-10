"""Extract evaluator-only patches for an identity-verified, nonreserved task."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record, load_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resolution', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    resolution_identity = file_record(args.resolution)
    task = load_json(args.resolution)['task']
    official_path = ROOT / 'evidence/p1/task-index-001/receipt.json'
    official_identity = file_record(official_path)
    reserved = {r.casefold() for r in load_json(official_path)['repo_counts']}
    if task['repo'].casefold() in reserved:
        raise ValueError('Reserved repository')
    registry_path = ROOT / 'evidence/data/swe-rebench-task-join-full-001/report.json'
    registry_identity = file_record(registry_path)
    matches = [s for s in load_json(registry_path)['task_shards']
               if s['identity']['sha256'] == task['source_task_shard_sha256']]
    if len(matches) != 1:
        raise ValueError('Nonunique source shard')
    shard = matches[0]
    source = ROOT / shard['path']
    intake_path = ROOT / shard['intake_path']
    if file_record(source) != shard['identity'] or file_record(intake_path) != shard['intake']:
        raise ValueError('Source identity drift')
    intake = load_json(intake_path)
    if (intake['dataset'] != 'nebius/SWE-rebench'
            or intake['revision'] != '89cdfbab4ab1bd8f5a658bb212d1b63624f4f881'
            or shard['identity'] not in intake['downloaded'].values()):
        raise ValueError('Source provenance mismatch')
    import pyarrow.parquet as pq
    filters = [('instance_id', '=', task['instance_id'])]
    identity_columns = ['instance_id', 'repo', 'base_commit', 'environment_setup_commit']
    rows = pq.read_table(source, columns=identity_columns, filters=filters).to_pylist()
    if (len(rows) != 1 or rows[0]['repo'].casefold() in reserved
            or any(rows[0][key] != task[key] for key in identity_columns)):
        raise ValueError('Task identity mismatch before oracle access')
    columns = ['patch', 'test_patch', 'meta', 'install_config',
               'FAIL_TO_PASS', 'FAIL_TO_FAIL', 'PASS_TO_PASS', 'PASS_TO_FAIL']
    rows = pq.read_table(source, columns=columns, filters=filters).to_pylist()
    if len(rows) != 1:
        raise ValueError('Nonunique oracle record')
    row = rows[0]
    if any(not isinstance(row[k], str) or not row[k].strip() for k in ['patch', 'test_patch']):
        raise ValueError('Expected nonempty text patches')
    if (file_record(source) != shard['identity'] or file_record(intake_path) != shard['intake']
            or file_record(args.resolution) != resolution_identity
            or file_record(official_path) != official_identity
            or file_record(registry_path) != registry_identity):
        raise ValueError('Input changed during extraction')
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'reference.patch').write_text(row.pop('patch'))
    (args.output / 'tests.patch').write_text(row.pop('test_patch'))
    (args.output / 'metadata.json').write_bytes(canonical_json(row))
    receipt = {'task': task, 'source': shard['identity'], 'intake': shard['intake'],
               'resolution': resolution_identity, 'official_index': official_identity,
               'source_registry': registry_identity, 'script': file_record(Path(__file__)),
               'files': {name: file_record(args.output / name)
                         for name in ['reference.patch', 'tests.patch', 'metadata.json']},
               'training_approved': False, 'scope': 'Evaluator-only; never expose oracle patches to agent.'}
    (args.output / 'receipt.json').write_bytes(canonical_json(receipt))
    print({'task': task['instance_id'], 'files': receipt['files']})


if __name__ == '__main__':
    main()
