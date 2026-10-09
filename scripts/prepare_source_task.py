"""Package one qualified source task into distinct agent/evaluator projections."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record, inventory
from zenithsync.source_task import project_source_issue


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    args = parser.parse_args()
    # This first package is explicitly restricted to the qualified Pyramid case.
    resolution_path = ROOT / 'evidence/data/source-environment-resolution-001/00/result.json'
    snapshot_path = ROOT / 'evidence/data/source-snapshot-build-001/receipt.json'
    controls_path = ROOT / 'evidence/data/source-expectations-001/report.json'
    resolution = json.loads(resolution_path.read_text())
    snapshot = json.loads(snapshot_path.read_text())
    controls = json.loads(controls_path.read_text())
    if controls['base']['all_cases_match_publisher_expectations'] is not False or controls['reference']['all_cases_match_publisher_expectations'] is not True:
        raise ValueError('Positive and negative evaluator controls required')
    if controls['resolution'] != file_record(resolution_path):
        raise ValueError('Control resolution identity mismatch')
    shard = controls['source']['shard']
    relative = f'data/train-{shard:05d}-of-00008.parquet'
    path = ROOT / f'artifacts/data/quarantine/r2e-gym-shard-{shard:03d}' / relative
    intake = json.loads((ROOT / f'evidence/data/r2e-gym-shard-{shard:03d}/receipt.json').read_text())
    identity = file_record(path)
    if identity != controls['source']['identity'] or identity != intake['downloaded'][relative]:
        raise ValueError('Source shard identity mismatch')
    import pyarrow.parquet as pq
    table = pq.read_table(path, columns=['repo_name', 'commit_hash', 'problem_statement', 'expected_output_json'])
    selected = table.slice(controls['source']['row_index'], 1).to_pylist()
    if len(selected) != 1:
        raise ValueError('Missing source row')
    row = selected[0]
    source_id = resolution['instance_id']
    if row['commit_hash'] != source_id.rsplit('-', 1)[-1] or row['repo_name'] != 'pyramid' or resolution['repo'] != 'Pylons/pyramid':
        raise ValueError('Task identity mismatch')
    joined = [json.loads(line) for line in (ROOT / 'evidence/data/source-task-join-002/joined.jsonl').read_text().splitlines()]
    matching = [item for item in joined if item['instance_id'] == source_id and item['repo'] == resolution['repo']]
    if len(matching) != 1 or matching[0]['problem_statement_sha256'] != hashlib.sha256(row['problem_statement'].encode()).hexdigest():
        raise ValueError('Issue identity differs from joined source task')
    if snapshot['base_commit'] != resolution['git']['base_commit'] or snapshot['exact_tree_preserved'] is not True:
        raise ValueError('Snapshot source equivalence not established')
    task = project_source_issue(problem_statement=row['problem_statement'], repo=resolution['repo'],
        source_instance_id=source_id, source_revision=intake['revision'], snapshot_commit=snapshot['snapshot_commit'])
    expected_path = ROOT / 'evidence/data/source-expectations-001/publisher-expected.json'
    expected = json.loads(expected_path.read_text())
    if expected != json.loads(row['expected_output_json']):
        raise ValueError('Evaluator expectations differ from source row')
    args.output.mkdir(parents=True, exist_ok=False)
    args.evidence.mkdir(parents=True, exist_ok=False)
    (args.output / 'agent').mkdir()
    (args.output / 'evaluator').mkdir()
    (args.output / 'agent/task.json').write_bytes(canonical_json(task))
    (args.output / 'evaluator/expected.json').write_bytes(canonical_json(expected))
    (args.output / 'evaluator/task.json').write_bytes(canonical_json({
        'source_instance_id': source_id, 'repo': resolution['repo'],
        'base_commit': resolution['git']['base_commit'], 'solution_commit': row['commit_hash'],
        'image': resolution['registry']['pinned_image'], 'test_path': '/r2e_tests',
        'expectation_rule': 'all_fully_qualified_cases_match_publisher_groups'}))
    (args.output / 'workspace.json').write_bytes(canonical_json({
        'image': 'sha256:397c5e0c8991ee3d2ab594052f66e9fd2cf2d9df45a67fd1a6445e00caf6fea1',
        'snapshot_commit': snapshot['snapshot_commit'], 'source_tree': snapshot['source_tree'],
        'adapter': file_record(ROOT / 'zenithsync/source_workspace.py')}))
    receipt = {'schema_version': 1, 'source': controls['source'], 'source_revision': intake['revision'],
        'source_problem_sha256': matching[0]['problem_statement_sha256'],
        'agent_task': file_record(args.output / 'agent/task.json'),
        'projection': 'Opaque task ID, snapshot base, exact issue body with sole wrapper removed',
        'controls': file_record(controls_path), 'snapshot': file_record(snapshot_path),
        'script': file_record(Path(__file__)), 'implementation': file_record(ROOT / 'zenithsync/source_task.py'),
        'training_approved': False, 'scope': 'One development task; only agent/task.json is model-visible'}
    (args.evidence / 'receipt.json').write_bytes(canonical_json(receipt))
    (args.evidence / 'manifest.json').write_bytes(canonical_json(inventory(args.output,
        kind='fixture', source='Qualified external development task; evaluator files private to grader', revision='source-task-001')))
    print('Separated development task projections prepared; no model invocation')


if __name__ == '__main__':
    main()
