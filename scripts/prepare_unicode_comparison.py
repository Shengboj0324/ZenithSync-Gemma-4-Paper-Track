"""Build a paired prompt-representation experiment from the qualified plan.

Only the JSON spelling of the requested argument object varies within each
context pair. This prepares inputs; it does not assert an improvement.
"""

import argparse
import copy
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record, inventory, load_json, verify
from prepare_write_diagnostic import rendered_ids


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model-dir', type=Path, required=True)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if version('transformers') != '5.13.1':
        raise ValueError('Qualified tokenizer version required')
    source_dir = ROOT/'artifacts/official/p1-write-diagnostic-001'
    source_manifest = ROOT/'evidence/p1/write-diagnostic-prepare-001/manifest.json'
    verify(source_dir, load_json(source_manifest))
    original = load_json(source_dir/'plan.json')
    for name, record in original['tokenizer_sources'].items():
        if file_record(args.model_dir/name) != record:
            raise ValueError('Tokenizer identity changed')
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(args.model_dir, local_files_only=True, trust_remote_code=False)
    cases = []
    for context in ['short', 'repository']:
        source = next(c for c in original['cases'] if c['id'] == 'structured_'+context)
        prefix, encoded = source['payload']['messages'][-1]['content'].split('\n', 1)
        if json.loads(encoded) != source['expected']:
            raise ValueError('Source instruction does not encode expected arguments')
        for representation in ['escaped', 'literal']:
            case = copy.deepcopy(source)
            case.update(id=representation+'_'+context, content_case=representation)
            spelling = json.dumps(case['expected'], ensure_ascii=representation == 'escaped',
                                  sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n'
            if json.loads(spelling) != case['expected']:
                raise ValueError('Representation changed intended arguments')
            case['payload']['messages'][-1]['content'] = prefix+'\n'+spelling
            ids = rendered_ids(tokenizer, case['payload'])
            if len(ids)+4096 > 32768:
                raise ValueError('Context limit exceeded')
            case.update(prompt_tokens=len(ids), prompt_token_sha256=hashlib.sha256(canonical_json(ids)).hexdigest())
            # In the control arm, retain the exact previously measured input.
            if representation == 'escaped' and case['payload'] != source['payload']:
                raise ValueError('Escaped control differs from original request')
            cases.append(case)
    plan = copy.deepcopy(original)
    plan['cases'] = cases
    plan['schedule'] = [
        {'case': arm+'_'+context, 'repeat': repeat}
        for repeat in range(3) for context in ['short', 'repository']
        for arm in (['escaped', 'literal'] if repeat % 2 == 0 else ['literal', 'escaped'])
    ]
    plan['source_plan'] = file_record(source_dir/'plan.json')
    plan['scope'] = ('12 paired development requests; vary only requested-argument JSON spelling within context; '
                     'fixed-seed repeats are not independent tasks; no returned tools executed')
    args.directory.mkdir(parents=True, exist_ok=False)
    args.output.mkdir(parents=True, exist_ok=False)
    (args.directory/'plan.json').write_bytes(canonical_json(plan))
    manifest = inventory(args.directory, kind='fixture', source=plan['scope'], revision='unicode-comparison-v1')
    (args.output/'manifest.json').write_bytes(canonical_json(manifest))
    (args.output/'receipt.json').write_bytes(canonical_json({
        'status': 'prepared_not_executed', 'source': file_record(Path(__file__)),
        'source_plan': plan['source_plan'], 'decoded_arguments_equal': True,
        'escaped_controls_identical': True, 'case_tokens': {c['id']: c['prompt_tokens'] for c in cases},
        'manifest': file_record(args.output/'manifest.json')}))
    print('Prepared 12 requests; paired JSON decodes identically; escaped controls unchanged')


if __name__ == '__main__':
    main()
