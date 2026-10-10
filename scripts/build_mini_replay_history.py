"""Reconstruct a quarantined native history from an explicitly adapted mini replay."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record, load_json
from zenithsync.replay_history import mini_replay_history
from zenithsync.submission_reconciliation import scratch_cleanup_command
from zenithsync.resource_replay_binding import verify_resource_replay_binding


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('candidate', 'attempt', 'profile', 'task', 'task-receipt', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--session-resources', type=Path)
    args = parser.parse_args()
    protocol_path = ROOT / 'evidence/data/source-http-client-001/success/http-fixture/exchanges.json'
    official_path = ROOT / 'evidence/p1/task-index-001/receipt.json'
    paths = [args.candidate, args.profile, args.task, args.task_receipt, protocol_path, official_path,
             args.attempt / 'receipt.json', args.attempt / 'events.json',
             args.attempt / 'submitted.patch', Path(__file__),
             ROOT / 'zenithsync/replay_history.py', ROOT / 'zenithsync/conversation.py',
             ROOT / 'zenithsync/resource_replay_binding.py',
             ROOT / 'zenithsync/submission_reconciliation.py', ROOT / 'zenithsync/artifacts.py']
    bindings = {str(path): file_record(path) for path in paths}
    attempt = load_json(args.attempt / 'receipt.json')
    candidate = load_json(args.candidate)
    profile = load_json(args.profile)
    resource_proof, resource_files = verify_resource_replay_binding(attempt, profile, args.session_resources)
    for name, identity in resource_files.items():
        if file_record(Path(name)) != identity:
            raise ValueError('Resource input changed before history reconstruction')
        bindings[name] = identity
        paths.append(Path(name))
    if (attempt['status'] != 'replayed_not_graded'
            or attempt['cleanup']['removed'] is not True
            or attempt.get('standalone_cleanup') is not True
            or attempt['source_observations_reused'] is not False
            or attempt['candidate'] != bindings[str(args.candidate)]
            or attempt['profile'] != bindings[str(args.profile)]
            or attempt['patch'] != bindings[str(args.attempt / 'submitted.patch')]):
        raise ValueError('Completed portable replay with matching inputs required')
    if candidate['task_metadata'] != attempt['task']:
        raise ValueError('Source and native task metadata differ')
    reserved = {name.casefold() for name in load_json(official_path)['repo_counts']}
    if attempt['task']['repo'].casefold() in reserved:
        raise ValueError('Reserved repository excluded')
    task_receipt = load_json(args.task_receipt)
    if task_receipt['task'] != bindings[str(args.task)]:
        raise ValueError('Task differs from extraction receipt')
    task = load_json(args.task)
    if any(task[key] != attempt['task'][key] for key in ('repo', 'instance_id', 'base_commit')):
        raise ValueError('Issue identity differs from replay')
    protocol = load_json(protocol_path)[0]['request']
    tools = protocol['tools']
    names = {tool['function']['name'] for tool in tools}
    if len(tools) != 9 or len(names) != 9:
        raise ValueError('Pinned nine-tool native protocol required')
    events = load_json(args.attempt / 'events.json')
    expected_cleanup = scratch_cleanup_command(python=profile['python'],
                                               scratch_paths=profile['scratch_paths'])
    if len(events) < 2 or events[-2]['arguments'] != {'command': expected_cleanup}:
        raise ValueError('Adapter cleanup differs from the reviewed standalone action')
    result = mini_replay_history(events,
        source_messages=candidate['messages'], system=protocol['messages'][0]['content'],
        problem=task['problem_statement'], allowed_tools=names)
    if any(file_record(path) != bindings[str(path)] for path in paths):
        raise ValueError('History projection inputs changed')
    args.output.mkdir(parents=True, exist_ok=False)
    for name, content in (('history', result['messages']), ('tools', tools),
                          ('mapping', result['mapping'])):
        (args.output / (name + '.json')).write_bytes(canonical_json(content))
    receipt = {'input_bindings': bindings, 'attempt': bindings[str(args.attempt / 'receipt.json')],
        'history': file_record(args.output / 'history.json'),
        'tools': file_record(args.output / 'tools.json'),
        'mapping': file_record(args.output / 'mapping.json'),
        'exchanges': len(result['mapping']), 'training_approved': False,
        'scope': result['scope'],
        'limitations': ['Reconstructed conditioning is not the original teacher prompt.',
                       'Original teacher reasoning is omitted.',
                       'Adapter-authored cleanup and submission are synthetic actions.',
                       'Serialization is not training admission or semantic validation.']}
    if resource_proof is not None:
        receipt['resource_environment'] = resource_proof
        receipt['limitations'].append('Recorded current response bodies alter the environment; rights and historical equivalence are not established.')
    (args.output / 'receipt.json').write_bytes(canonical_json(receipt))
    print({'messages': len(result['messages']), 'exchanges': receipt['exchanges']})


if __name__ == '__main__':
    main()
