"""Reproduce native mixed-content chronology and verify a lossless field projection."""

import argparse
from importlib.metadata import version
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record, load_json
from zenithsync.gemma_trajectory import project_pre_action_text
from zenithsync.training_masks import assistant_training_tokens
from zenithsync.trajectory_import import SOURCE_TOOLS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if version('transformers') != '5.13.1':
        raise ValueError('Qualified tokenizer runtime required')
    manifest = load_json(ROOT / 'evidence/p1/model-intake-001/model-manifest.json')
    for name in ['chat_template.jinja', 'tokenizer.json', 'tokenizer_config.json']:
        expected = next(row for row in manifest['files'] if row['path'] == name)
        if file_record(args.model / name) != {key: expected[key] for key in ['sha256', 'size_bytes']}:
            raise ValueError('Tokenizer asset identity mismatch')
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True, trust_remote_code=False)
    history = [{'role': 'user', 'content': 'TASK_SENTINEL'},
        {'role': 'assistant', 'content': 'PRE_ACTION_SENTINEL', 'tool_calls': [
            {'id': 'source-call', 'type': 'function', 'function': {'name': 'execute_bash', 'arguments': {'command': 'pwd'}}}]},
        {'role': 'tool', 'tool_call_id': 'source-call', 'content': 'FUTURE_RESULT_SENTINEL'},
        {'role': 'assistant', 'content': '', 'tool_calls': [
            {'id': 'source-finish', 'type': 'function', 'function': {'name': 'finish', 'arguments': {}}}]}]
    render = lambda messages: tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
    original, original_prefix = render(history), render(history[:2])
    if not original.index('call:execute_bash') < original.index('FUTURE_RESULT_SENTINEL') < original.index('PRE_ACTION_SENTINEL'):
        raise ValueError('Expected template chronology defect was not reproduced')
    if original.startswith(original_prefix):
        raise ValueError('Expected unprojected prefix instability was not reproduced')
    projection = project_pre_action_text(history)
    messages = projection['messages']
    text, prefix = render(messages), render(messages[:2])
    if not text.index('PRE_ACTION_SENTINEL') < text.index('call:execute_bash') < text.index('FUTURE_RESULT_SENTINEL'):
        raise ValueError('Projection did not restore source chronology')
    if not text.startswith(prefix):
        raise ValueError('Projected text is not prefix stable')
    prefix_ids = tokenizer.apply_chat_template(messages[:2], tokenize=True, add_generation_prompt=False, return_dict=False)
    full_ids = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=False, return_dict=False)
    if full_ids[:len(prefix_ids)] != prefix_ids:
        raise ValueError('Projected tokens are not prefix stable')
    changed = [dict(message) for message in messages]
    changed[2]['content'] = 'DIFFERENT_FUTURE_RESULT'
    changed_ids = tokenizer.apply_chat_template(changed, tokenize=True, add_generation_prompt=False, return_dict=False)
    if changed_ids[:len(prefix_ids)] != prefix_ids:
        raise ValueError('Future result changed earlier action tokens')
    encoded = assistant_training_tokens(tokenizer, messages,
        template_sha256=file_record(args.model / 'chat_template.jinja')['sha256'],
        allowed_tools=set(SOURCE_TOOLS), terminal_call_tools={'finish'})
    supervised = tokenizer.decode([value for value in encoded['labels'] if value != -100])
    if 'PRE_ACTION_SENTINEL' not in supervised or 'FUTURE_RESULT_SENTINEL' in supervised:
        raise ValueError('Pre-action text/result supervision is incorrect')
    args.output.mkdir(parents=True, exist_ok=False)
    for name, value in [('unprojected.txt', original), ('projected.txt', text), ('projected-prefix.txt', prefix)]:
        (args.output / name).write_text(value)
    (args.output / 'receipt.json').write_bytes(canonical_json({
        'schema_version': 1, 'status': 'chronology_defect_reproduced_and_fixture_projection_passed',
        'source_text_preserved': messages[1]['reasoning'] == history[1]['content'],
        'projected_prefix_tokens': len(prefix_ids), 'projected_full_tokens': len(full_ids),
        'future_result_prefix_invariance': True, 'projection': projection['transformations'],
        'sources': {name: file_record(ROOT / name) for name in ['zenithsync/gemma_trajectory.py',
                   'zenithsync/training_masks.py', 'scripts/verify_gemma_causal_projection.py']},
        'scope': 'One synthetic single-user fixture; field transport only, no tool execution or training approval'}))
    print('Native chronology defect reproduced; projected text/tokens remain prefix-stable under changed future results')


if __name__ == '__main__':
    main()
