"""Preflight by default; execute bounded diagnostic requests only with --execute.

No returned tool is executed. A fresh approved session file is required for live
requests. A transport/serialization/disagreement failure stops the experiment.
"""

import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record, load_json, verify
from zenithsync.tool_diagnostic import assess_write_response
from zenithsync.deadline import wall_deadline
from prepare_write_diagnostic import rendered_ids


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--model-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--session', type=Path)
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        raise ValueError('Invalid loopback port')
    manifest = load_json(args.manifest)
    verify(args.directory, manifest)
    plan = load_json(args.directory/'plan.json')
    if plan['schema_version'] != 1 or len(plan['schedule']) != 12 or len(plan['cases']) != 4:
        raise ValueError('Unexpected diagnostic plan shape')
    if plan['max_seconds'] != 1500 or plan['request_timeout_seconds'] != 120:
        raise ValueError('Unexpected diagnostic budget')
    if version('transformers') != '5.13.1':
        raise ValueError('Pinned tokenizer runtime required')
    for name, expected in plan['tokenizer_sources'].items():
        if name not in {'tokenizer.json','tokenizer_config.json','chat_template.jinja','config.json'}:
            raise ValueError('Unexpected tokenizer source')
        if file_record(args.model_dir/name) != expected:
            raise ValueError('Tokenizer differs from prepared experiment')
    if set(plan['tokenizer_sources']) != {'tokenizer.json','tokenizer_config.json','chat_template.jinja','config.json'}:
        raise ValueError('Incomplete tokenizer identity')
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(args.model_dir,local_files_only=True,trust_remote_code=False)
    cases = {c['id']:c for c in plan['cases']}
    if len(cases) != 4 or any(s['case'] not in cases for s in plan['schedule']):
        raise ValueError('Invalid case schedule')
    for case in cases.values():
        payload = case['payload']
        if payload['model'] != plan['model'] or payload['max_completion_tokens'] != 4096:
            raise ValueError('Unexpected model/output budget')
        if case['prompt_tokens'] + 4096 > 32768:
            raise ValueError('Context budget exceeded')
        ids = rendered_ids(tokenizer, payload)
        if len(ids) != case['prompt_tokens'] or hashlib.sha256(canonical_json(ids)).hexdigest() != case['prompt_token_sha256']:
            raise ValueError('Prepared prompt differs from current serialization')
    args.output.mkdir(parents=True, exist_ok=False)
    sources = {str(p.relative_to(ROOT)):file_record(p) for p in
               [Path(__file__).resolve(), ROOT/'scripts/prepare_write_diagnostic.py', ROOT/'zenithsync/tool_diagnostic.py', ROOT/'zenithsync/deadline.py']}
    receipt = {'status':'preflight_passed_not_executed','sources':sources,
               'manifest':file_record(args.manifest),'records':[],
               'scope':plan['scope'],'model':plan['model']}
    (args.output/'preflight.json').write_bytes(canonical_json(receipt))
    if not args.execute:
        print('Prepared diagnostic verified; no model requests sent')
        return
    if args.session is None or version('vllm') != '0.19.1':
        raise ValueError('Live execution requires session authorization and qualified vLLM environment')
    session = load_json(args.session)
    deadline = datetime.fromisoformat(session['validation_deadline_utc'])
    if deadline.tzinfo is None:
        raise ValueError('Timezone-aware session deadline required')
    remaining = (deadline-datetime.now(timezone.utc)).total_seconds()
    if not 1500 <= remaining <= 4*3600:
        raise ValueError('Need at least 25 minutes within a bounded approved session')
    stop_at = time.monotonic()+1500
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    receipt.update(status='running', session=file_record(args.session), started_utc=datetime.now(timezone.utc).isoformat())
    try:
        with wall_deadline(1500):
            for index, scheduled in enumerate(plan['schedule']):
                if stop_at-time.monotonic() < 120:
                    receipt['status'] = 'stopped_before_request_budget_overrun'
                    break
                case = cases[scheduled['case']]
                folder = args.output/f'{index:02d}'
                folder.mkdir()
                payload = canonical_json(case['payload'])
                (folder/'request.json').write_bytes(payload)
                request = urllib.request.Request(f'http://127.0.0.1:{args.port}/v1/chat/completions',
                    data=payload, headers={'Content-Type':'application/json','Authorization':'Bearer EMPTY'})
                started = time.monotonic()
                with opener.open(request,timeout=120) as response:
                    body = response.read(8*1024*1024+1)
                if len(body)>8*1024*1024:
                    raise ValueError('Response exceeds byte cap')
                (folder/'response.json').write_bytes(body)
                decoded = load_json(folder/'response.json')
                if decoded.get('model') != plan['model']:
                    raise ValueError('Response model alias differs from plan')
                choice = decoded['choices'][0]
                ids = choice.get('token_ids')
                if not isinstance(ids,list) or not ids or any(type(x)is not int or x<0 for x in ids):
                    raise ValueError('Valid raw token IDs absent')
                raw = tokenizer.decode(ids,skip_special_tokens=False)
                (folder/'raw.txt').write_text(raw)
                prompt = decoded.get('prompt_token_ids')
                if not isinstance(prompt,list) or hashlib.sha256(canonical_json(prompt)).hexdigest()!=case['prompt_token_sha256']:
                    raise ValueError('Server prompt serialization differs from offline preflight')
                result = assess_write_response(decoded,raw,case['expected'])
                result.update(case=case['id'],repeat=scheduled['repeat'],elapsed_seconds=time.monotonic()-started,
                              response=file_record(folder/'response.json'),raw=file_record(folder/'raw.txt'))
                (folder/'result.json').write_bytes(canonical_json(result))
                receipt['records'].append(result)
                if result['classification']=='native_transport_disagreement':
                    receipt['status']='stopped_on_parser_disagreement'
                    break
            else:
                receipt['status']='all_planned_requests_recorded'
    except Exception as error:
        receipt.update(status='stopped_on_execution_error',error_type=type(error).__name__,error=str(error)[:500])
        raise
    finally:
        receipt['finished_utc']=datetime.now(timezone.utc).isoformat()
        receipt['sources_unchanged']=sources=={name:file_record(ROOT/name)for name in sources}
        receipt['manifest_unchanged']=receipt['manifest']==file_record(args.manifest)
        try:
            verify(args.directory, manifest)
            receipt['artifact_unchanged']=True
        except (ValueError, OSError):
            receipt['artifact_unchanged']=False
        if not all(receipt[key] for key in ['sources_unchanged','manifest_unchanged','artifact_unchanged']):
            receipt['status']='invalidated_by_changed_inputs'
        (args.output/'receipt.json').write_bytes(canonical_json(receipt))
    if receipt['status']=='invalidated_by_changed_inputs':
        raise RuntimeError('Diagnostic inputs changed during execution')
    print('Diagnostic recorded:',receipt['status'])


if __name__=='__main__':
    main()
