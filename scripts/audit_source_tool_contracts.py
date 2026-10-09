"""Census tool argument shapes and transport gaps; no command execution or translation."""
import argparse
from collections import Counter, defaultdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record, load_json
from zenithsync.trajectory_import import convert_swe_hero_history


def path_category(path):
    if not isinstance(path, str):
        return 'non_string'
    if '..' in path.split('/'):
        return 'parent_traversal'
    if path == '/workspace':
        return 'workspace_root'
    if path.startswith('/workspace/'):
        return 'workspace_descendant'
    if path == '/testbed' or path.startswith('/testbed/'):
        return 'testbed'
    if path == '/tmp' or path.startswith('/tmp/'):
        return 'temporary'
    return 'other_absolute' if path.startswith('/') else 'relative'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--shard', type=Path, required=True)
    parser.add_argument('--intake', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    intake = load_json(args.intake)
    identity = file_record(args.shard)
    if identity not in intake['downloaded'].values():
        raise ValueError('Shard differs from pinned intake')
    import pyarrow.parquet as pq
    parquet = pq.ParquetFile(args.shard)
    args.output.mkdir(parents=True, exist_ok=False)
    counts, affected = Counter(), Counter()
    shapes, types = defaultdict(Counter), defaultdict(Counter)
    paths, actions = Counter(), Counter()
    seen = set()
    with (args.output/'rows.jsonl').open('xb') as stream:
        for batch in parquet.iter_batches(batch_size=8, columns=['trajectory_id', 'repo', 'trajectory']):
            for row in batch.to_pylist():
                if row['trajectory_id'] in seen:
                    raise ValueError('Duplicate trajectory ID')
                seen.add(row['trajectory_id'])
                flags = Counter()
                converted = convert_swe_hero_history(row['trajectory'])
                for message in converted['messages']:
                    for call in message.get('tool_calls', []):
                        function = call['function']
                        name, arguments = function['name'], function['arguments']
                        counts[name] += 1
                        shapes[name][','.join(sorted(arguments))] += 1
                        for key, value in arguments.items():
                            types[name + '.' + key][type(value).__name__] += 1
                        if name == 'execute_bash':
                            for key in ('is_input', 'timeout'):
                                if key in arguments:
                                    flags['shell_' + key + '_field'] += 1
                            if arguments.get('command') == '':
                                flags['empty_shell_command'] += 1
                        elif name == 'str_replace_editor':
                            action = arguments.get('command')
                            if not isinstance(action, str):
                                raise ValueError('Editor action is not text')
                            actions[action] += 1
                            category = path_category(arguments.get('path'))
                            paths[category] += 1
                            if category != 'workspace_descendant':
                                flags['editor_path_' + category] += 1
                            if action not in ('view', 'create', 'str_replace'):
                                flags['editor_nonstandard_action'] += 1
                            bounds = arguments.get('view_range')
                            if isinstance(bounds, list) and len(bounds) == 2 and bounds[1] == -1:
                                flags['view_to_end_sentinel'] += 1
                affected.update(flags.keys())
                stream.write(canonical_json({'trajectory_id': row['trajectory_id'], 'repo': row['repo'],
                    'observed_adaptation_flags': dict(flags), 'training_approved': False}))
    if len(seen) != parquet.metadata.num_rows or file_record(args.shard) != identity:
        raise ValueError('Incomplete census or source changed')
    receipt = {'schema_version': 1, 'status': 'argument_contract_census_not_training_approved',
        'rows': len(seen), 'dataset': intake['dataset'], 'revision': intake['revision'], 'shard': identity,
        'tool_counts': dict(counts), 'argument_key_sets': {k: dict(v) for k, v in shapes.items()},
        'argument_types': {k: dict(v) for k, v in types.items()}, 'editor_actions': dict(actions),
        'editor_path_categories': dict(paths), 'affected_histories': dict(affected),
        'row_records': file_record(args.output/'rows.jsonl'),
        'sources': {name: file_record(ROOT/name) for name in ('scripts/audit_source_tool_contracts.py',
            'zenithsync/trajectory_import.py', 'zenithsync/conversation.py')},
        'scope': 'Source shape census only. Flags are observed transport differences, not exhaustive '
                 'semantic incompatibility detection. Unflagged commands are not certified equivalent. '
                 'No model_patch read, shell execution, tool-response rewrite, task success or replay claim.'}
    (args.output/'receipt.json').write_bytes(canonical_json(receipt))
    print({'tool_counts': dict(counts), 'actions': dict(actions), 'paths': dict(paths), 'affected_histories': dict(affected)})


if __name__ == '__main__':
    main()
