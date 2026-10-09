"""Exercise the installed official Gemma parser with labeled synthetic strings.

This tests parsing, not model generation. Known lossy parsing is recorded rather
than hidden behind an aggregate success claim.
"""

import argparse
import hashlib
from importlib.metadata import version
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    if version('vllm') != '0.19.1' or version('transformers') != '5.13.1':
        raise ValueError('requires the qualified P1 parser versions')
    from transformers import AutoTokenizer
    from vllm.tool_parsers.gemma4_tool_parser import Gemma4ToolParser
    from vllm.entrypoints.openai.chat_completion.protocol import ChatCompletionRequest
    import vllm.tool_parsers.gemma4_tool_parser as implementation

    tokenizer = AutoTokenizer.from_pretrained(args.model_dir, local_files_only=True, trust_remote_code=False)
    request = ChatCompletionRequest(model='gemma-4-31b-it-qat-w4a16-ct',
                                    messages=[{'role': 'user', 'content': 'Synthetic parser test'}])
    quoted = '<|"|>'
    def call(name, body):
        return '<|tool_call>call:' + name + '{' + body + '}<tool_call|>'
    cases = [
        ('plain_text', 'Completed.', []),
        ('read_file', call('read_file', f'path:{quoted}probe.txt{quoted}'),
         [('read_file', {'path': 'probe.txt'})]),
        ('unicode_punctuation', call('read_file', f'path:{quoted}src/数据,{{x}}.py{quoted}'),
         [('read_file', {'path': 'src/数据,{x}.py'})]),
        ('parallel', call('first', 'count:2') + call('second', 'enabled:false'),
         [('first', {'count': 2}), ('second', {'enabled': False})]),
        ('nested', call('inspect', f'options:{{rate:0.25,enabled:true}},items:[1,{quoted}two{quoted}],empty:null'),
         [('inspect', {'options': {'rate': 0.25, 'enabled': True}, 'items': [1, 'two'], 'empty': None})]),
        ('truncated_outer_call', '<|tool_call>call:read_file{path:' + quoted + 'probe.txt', []),
    ]
    def extract(text):
        result = Gemma4ToolParser(tokenizer).extract_tool_calls(text, request)
        return [(t.function.name, json.loads(t.function.arguments)) for t in result.tool_calls]
    records = []
    for name, text, expected in cases:
        actual = extract(text)
        records.append({'name': name, 'synthetic_input': text, 'expected': expected,
                        'actual': actual, 'matched': actual == expected})
    boundaries = []
    for name, text in [
        ('duplicate_key', call('read_file', f'path:{quoted}first{quoted},path:{quoted}second{quoted}')),
        ('scientific_notation', call('inspect', 'tolerance:1e-6')),
    ]:
        boundaries.append({'name': name, 'synthetic_input': text, 'actual': extract(text)})
    matched = all(item['matched'] for item in records)
    receipt = {'schema_version': 1, 'status': 'parser_fixture_checks_passed' if matched else 'parser_fixture_checks_failed',
               'vllm': version('vllm'), 'transformers': version('transformers'),
               'implementation_sha256': hashlib.sha256(Path(implementation.__file__).read_bytes()).hexdigest(),
               'probe_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               'fixtures': records, 'boundary_observations': boundaries,
               'limitations': ['Synthetic strings, no model-generated outputs',
                               'No streaming qualification',
                               'Duplicate raw keys may be lost before application JSON validation',
                               'Tool-specific schema validation remains required']}
    (args.output / 'receipt.json').write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + '\n')
    print('Parser fixture matches:', sum(item['matched'] for item in records), '/', len(records))
    return 0 if matched else 1


if __name__ == '__main__':
    raise SystemExit(main())
