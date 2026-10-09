"""Prepare a paired, offline-qualified tool serialization experiment; no inference."""

import argparse
import copy
import hashlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record, inventory, load_json
from zenithsync.conversation import normalize_arguments, normalize_history


def rendered_ids(tokenizer, payload):
    messages = copy.deepcopy(payload['messages'])
    checked = copy.deepcopy(messages)
    for message in checked:
        if 'reasoning' in message and 'reasoning_content' in message:
            if message['reasoning'] != message['reasoning_content']:
                raise ValueError('Conflicting captured reasoning aliases')
            # The released SDK sent both equal aliases. Validate linkage using
            # one alias, while preserving the captured wire payload unchanged.
            del message['reasoning_content']
    normalize_history(checked, allowed_tools={t['function']['name'] for t in payload['tools']})
    for message in messages:
        # vLLM's OpenAI content mode wraps text parts before applying this
        # multimodal template. The system-list branch adds a trailing space.
        if isinstance(message.get('content'), str):
            message['content'] = [{'type': 'text', 'text': message['content']}]
        for call in message.get('tool_calls', []):
            call['function']['arguments'] = normalize_arguments(call['function']['arguments'])
    return tokenizer.apply_chat_template(messages, tools=payload['tools'], tokenize=True, return_dict=False,
        add_generation_prompt=True, **payload.get('chat_template_kwargs', {}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model-dir', type=Path, required=True)
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    from importlib.metadata import version
    if version('transformers') != '5.13.1':
        raise ValueError('Pinned tokenizer runtime required')
    from transformers import AutoTokenizer
    manifest = load_json(ROOT/'evidence/p1/model-intake-001/model-manifest.json')
    expected = {r['path']:r for r in manifest['files']}
    tokenizer_sources = {}
    for name in ['tokenizer.json','tokenizer_config.json','chat_template.jinja','config.json']:
        record = file_record(args.model_dir/name)
        if record != {k:expected[name][k] for k in ['sha256','size_bytes']}:
            raise ValueError('Tokenizer/config differs from model intake')
        tokenizer_sources[name] = record
    tokenizer = AutoTokenizer.from_pretrained(args.model_dir,local_files_only=True,trust_remote_code=False)
    original = load_json(args.capture/'original-request.json')
    response = load_json(args.capture/'response.json')
    if original['model'] != 'gemma-4-31b-it-qat-w4a16-ct':
        raise ValueError('Unexpected model alias')
    actual_ids = response['prompt_token_ids']
    calibration = rendered_ids(tokenizer, original)
    if calibration != actual_ids:
        raise ValueError(f'Local serialization does not reproduce recorded prompt: {len(calibration)} vs {len(actual_ids)} tokens')
    contents = {
        'simple':'answer = 1\n',
        'structured':'def describe(s):\n    data = {"filepath:": s, "bytes": len(s.encode("utf-8"))}\n    return f"{data[\'bytes\']}: {s}"\n\nprint(describe("hello 🌍"))\n',
    }
    cases = []
    for content_name, content in contents.items():
        expected_args = {'content':content,'filepath':'serialization_probe.py'}
        instruction = ('For this tool serialization diagnostic, call write_file exactly once with the following '
                       'argument object. Do not execute other tools.\n'+canonical_json(expected_args).decode())
        for context in ['short','repository']:
            payload = copy.deepcopy(original)
            payload.update(max_completion_tokens=4096, return_token_ids=True, seed=0)
            if context == 'short':
                payload['messages'] = [payload['messages'][0]]
            payload['messages'].append({'role':'user','content':instruction})
            ids = rendered_ids(tokenizer, payload)
            if len(ids)+4096 > 32768:
                raise ValueError('Experiment exceeds the qualified context budget')
            cases.append({'id':content_name+'_'+context,'content_case':content_name,'context':context,
                          'payload':payload,'expected':expected_args,'prompt_tokens':len(ids),
                          'prompt_token_sha256':hashlib.sha256(canonical_json(ids)).hexdigest()})
    schedule = []
    for repeat in range(3):
        for content_name in contents:
            contexts = ['short','repository'] if repeat % 2 == 0 else ['repository','short']
            schedule.extend({'case':content_name+'_'+context,'repeat':repeat} for context in contexts)
    args.directory.mkdir(parents=True, exist_ok=False)
    args.output.mkdir(parents=True, exist_ok=False)
    plan = {'schema_version':1,'status':'prepared_not_executed','model':original['model'],
            'cases':cases,'schedule':schedule,'max_seconds':1500,'request_timeout_seconds':120,
            'source_capture':{name:file_record(args.capture/name) for name in ['original-request.json','response.json']},
            'tokenizer_sources':tokenizer_sources,
            'scope':'12 fixed development requests; same schemas/settings across context arms; no file tool execution; repeats are not independent tasks'}
    (args.directory/'plan.json').write_bytes(canonical_json(plan))
    artifact = inventory(args.directory,kind='fixture',source='Reserved development context plus explicit synthetic string fixtures',revision='write-diagnostic-v1')
    (args.output/'manifest.json').write_bytes(canonical_json(artifact))
    (args.output/'receipt.json').write_bytes(canonical_json({'status':'offline_experiment_prepared',
        'source':file_record(Path(__file__)),'calibration_tokens':len(calibration),
        'calibration_matches_recorded_gpu_prompt':True,'case_tokens':{c['id']:c['prompt_tokens']for c in cases},
        'requests':len(schedule),'manifest':file_record(args.output/'manifest.json'),'tokenizer_sources':tokenizer_sources}))
    print('Prepared',len(schedule),'requests; recorded prompt reproduced exactly:',len(calibration),'tokens')


if __name__ == '__main__':
    main()
