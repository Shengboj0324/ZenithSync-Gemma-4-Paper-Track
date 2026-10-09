"""Pin a deterministic cross-repository sample of SWE-rebench image metadata."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record, load_json
from scripts.resolve_source_environments import dockerhub_tag_identity


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--joined', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--count', type=int, default=8)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not 1 <= args.count <= 20:
        raise ValueError('Bounded metadata sample must contain 1-20 repositories')
    identity = file_record(args.joined)
    if identity != load_json(args.report)['joined']:
        raise ValueError('Joined metadata identity mismatch')
    tasks = {}
    for line in args.joined.read_text().splitlines():
        row = json.loads(line)
        if not row['source_image_reference']:
            continue
        key = (row['repo'], row['instance_id'])
        task = {name: row[name] for name in ('repo', 'instance_id', 'base_commit',
                'environment_setup_commit', 'source_image_reference', 'source_task_shard_sha256', 'source_task_row')}
        if key in tasks and tasks[key] != task:
            raise ValueError('Conflicting task records across trajectories')
        tasks[key] = task
    ranked = sorted(tasks.values(), key=lambda row: hashlib.sha256(
        ('swe-rebench-image-probe-v1\0' + row['instance_id']).encode()).hexdigest())
    selected, repositories = [], set()
    for task in ranked:
        if task['repo'].casefold() not in repositories:
            selected.append(task)
            repositories.add(task['repo'].casefold())
        if len(selected) == args.count:
            break
    if len(selected) != args.count:
        raise ValueError('Insufficient distinct repositories with image references')
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'selected.json').write_bytes(canonical_json(selected))
    import requests
    session = requests.Session()
    results = []
    for index, task in enumerate(selected):
        directory = args.output / f'{index:03d}'
        directory.mkdir()
        tag = task['source_image_reference']
        if ':' not in tag:
            tag += ':latest'
        result = {'task': task, 'requested_tag': tag}
        try:
            result['registry'] = dockerhub_tag_identity(session, tag, directory)
        except Exception as error:
            # Exception text may contain transport details; retain only safe type/status.
            result['error_type'] = type(error).__name__
            response = getattr(error, 'response', None)
            if response is not None:
                result['http_status'] = response.status_code
        results.append(result)
        (directory / 'result.json').write_bytes(canonical_json(result))
        print({'task': task['instance_id'], 'resolved': 'registry' in result,
               'error_type': result.get('error_type')}, flush=True)
    if file_record(args.joined) != identity:
        raise ValueError('Joined metadata changed during resolution')
    (args.output / 'report.json').write_bytes(canonical_json({
        'schema_version': 1, 'retrieved_at': datetime.now(timezone.utc).isoformat(),
        'input': identity, 'requested': len(selected),
        'resolved': sum('registry' in row for row in results), 'results': results,
        'selection': 'SHA256(swe-rebench-image-probe-v1 NUL instance_id), first task per casefolded repository; image-present tasks only.',
        'layers_downloaded': False, 'runtime_verified': False, 'training_approved': False,
        'scope': 'Registry identity, Linux amd64 config and compressed sizes only; no image working-tree, task correctness or evaluator verification.',
        'script': file_record(Path(__file__)), 'resolver': file_record(ROOT / 'scripts/resolve_source_environments.py')}))


if __name__ == '__main__':
    main()
