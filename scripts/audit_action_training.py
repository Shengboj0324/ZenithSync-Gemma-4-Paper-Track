"""Measure experimental next-action supervision without exporting training data."""

import argparse
from importlib.metadata import version
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from zenithsync.action_training import action_training_tokens
from zenithsync.artifacts import canonical_json, file_record
from zenithsync.conversation import normalize_history
from zenithsync.training_masks import assistant_training_tokens


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--history', type=Path, required=True)
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if version('transformers') != '5.13.1' or version('tokenizers') != '0.22.2':
        raise ValueError('Pinned tokenizer runtime required')
    receipt = json.loads((args.history / 'receipt.json').read_text())
    sources = {name: file_record(args.history / (name + '.json'))
               for name in ('history', 'tools')}
    if any(sources[name] != receipt[name] for name in sources):
        raise ValueError('History artifact changed')
    manifest = json.loads((ROOT / 'evidence/p1/model-intake-001/model-manifest.json').read_text())
    assets = {}
    for name in ('chat_template.jinja', 'tokenizer.json', 'tokenizer_config.json'):
        expected = next(row for row in manifest['files'] if row['path'] == name)
        assets[name] = file_record(args.model / name)
        if assets[name] != {key: expected[key] for key in ('sha256', 'size_bytes')}:
            raise ValueError('Tokenizer asset mismatch')
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True,
                                             trust_remote_code=False)
    tools = json.loads((args.history / 'tools.json').read_text())
    allowed = {tool['function']['name'] for tool in tools}
    messages = normalize_history(json.loads((args.history / 'history.json').read_text()),
                                 allowed_tools=allowed)
    rows = []
    occurrences = set()
    full = assistant_training_tokens(tokenizer, messages,
        template_sha256=assets['chat_template.jinja']['sha256'],
        allowed_tools=allowed, tools=tools)
    covered_positions = set()
    for index, message in enumerate(messages):
        if message['role'] != 'assistant':
            continue
        encoded = action_training_tokens(tokenizer, messages, target_index=index,
            template_sha256=assets['chat_template.jinja']['sha256'],
            allowed_tools=allowed, tools=tools)
        occurrence = (sources['history']['sha256'], index, encoded['target_call_id'])
        if occurrence in occurrences:
            raise ValueError('Duplicate source action occurrence')
        occurrences.add(occurrence)
        if encoded['input_ids'] != full['input_ids'][:len(encoded['input_ids'])]:
            raise ValueError('Action tokens differ from their full-history prefix')
        positions = {position for position, label in enumerate(encoded['labels'])
                     if position > 0 and label != -100}
        if covered_positions & positions:
            raise ValueError('Overlapping action target positions')
        if any(encoded['labels'][position] != full['labels'][position]
               for position in positions):
            raise ValueError('Action target labels differ from full-history labels')
        covered_positions.update(positions)
        row = {key: value for key, value in encoded.items() if key not in ('input_ids', 'labels')}
        row['input_tokens'] = len(encoded['input_ids'])
        row['fits_with_8192_reserve'] = row['input_tokens'] + 8192 <= 32768
        rows.append(row)
        print(f"Action {len(rows)}: {row['input_tokens']} input, "
              f"{row['supervised_tokens']} targets, fits={row['fits_with_8192_reserve']}", flush=True)
    if not rows:
        raise ValueError('History contains no action targets')
    expected_positions = {position for position, label in enumerate(full['labels'])
                          if position > 0 and label != -100}
    if covered_positions != expected_positions:
        raise ValueError('Action targets do not partition full-history supervision')
    if any(file_record(args.history / (name + '.json')) != identity
           for name, identity in sources.items()):
        raise ValueError('History changed during audit')
    if any(file_record(args.model / name) != identity for name, identity in assets.items()):
        raise ValueError('Tokenizer changed during audit')
    fitting = [row for row in rows if row['fits_with_8192_reserve']]
    report = {'schema_version': 1, 'sources': sources, 'assets': assets, 'actions': rows,
        'total_actions': len(rows), 'fitting_actions': len(fitting),
        'total_unique_target_tokens': sum(row['supervised_tokens'] for row in rows),
        'fitting_unique_target_tokens': sum(row['supervised_tokens'] for row in fitting),
        'fitting_repeated_context_tokens': sum(row['context_tokens'] for row in fitting),
        'fitting_input_tokens': sum(row['input_tokens'] for row in fitting),
        'training_approved': False, 'token_arrays_exported': False,
        'exact_full_history_target_partition': True,
        'scope': 'Full causal prefixes; one source action occurrence per example. '
                 'Overlapping context is not new target data. All prefixes require the '
                 'same task/repository split. No new independent benchmark tasks or training admission.',
        'implementation': {name: file_record(ROOT / name) for name in
            ('scripts/audit_action_training.py', 'zenithsync/action_training.py',
             'zenithsync/training_masks.py', 'zenithsync/conversation.py')}}
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'report.json').write_bytes(canonical_json(report))


if __name__ == '__main__':
    main()
