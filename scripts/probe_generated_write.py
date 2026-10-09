"""Retain raw generated tokens and parsed multi-argument tool calls; no file execution."""

import argparse
from importlib.metadata import version
import json
from pathlib import Path
import time
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(args.model_dir, local_files_only=True, trust_remote_code=False)
    tool = {'type':'function','function':{'name':'write_file','description':'Write a file.',
        'parameters':{'type':'object','properties':{'filepath':{'type':'string'},'content':{'type':'string'}},
                      'required':['filepath','content'],'additionalProperties':False}}}
    cases = [('simple', 'x = 1\n'), ('multiline_quotes', 'greeting = "hello"\nprint(greeting)\n'),
             ('fstring_unicode', 's = "hello 🌍"\nprint(f"{len(s)}: {s}")\n'),
             ('content_first_fstring', 's = "hello 🌍"\nprint(f"{len(s)}: {s}")\n')]
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    results = []
    for name, content in cases:
        expected = {'filepath':'probe.py','content':content}
        if name.startswith('content_first'):
            expected = {'content':content, 'filepath':'probe.py'}
        payload = {'model':'gemma-4-31b-it-qat-w4a16-ct',
            'messages':[{'role':'user','content':'Call write_file exactly once using these arguments: '+json.dumps(expected)}],
            'tools':[tool], 'tool_choice':'auto', 'temperature':0, 'max_tokens':1024,
            'return_token_ids':True}
        (args.output/(name+'-request.json')).write_text(json.dumps(payload,indent=2)+'\n')
        started = time.monotonic()
        request = urllib.request.Request('http://127.0.0.1:8000/v1/chat/completions',
            data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer EMPTY'})
        with opener.open(request, timeout=180) as response:
            body = response.read(8*1024*1024+1)
        if len(body)>8*1024*1024:
            raise ValueError('Response exceeds cap')
        (args.output/(name+'-response.json')).write_bytes(body)
        decoded = json.loads(body)
        choice = decoded['choices'][0]
        ids = choice.get('token_ids')
        if not isinstance(ids,list) or not ids:
            raise ValueError('Raw generation token IDs were not returned')
        raw = tokenizer.decode(ids,skip_special_tokens=False)
        (args.output/(name+'-raw.txt')).write_text(raw)
        calls = choice['message'].get('tool_calls') or []
        actual = None
        if len(calls)==1 and calls[0]['function']['name']=='write_file':
            actual = json.loads(calls[0]['function']['arguments'])
        results.append({'case':name,'expected':expected,'actual':actual,'exact_match':actual==expected,
                        'elapsed_seconds':time.monotonic()-started,'finish_reason':choice['finish_reason']})
    (args.output/'receipt.json').write_text(json.dumps({'status':'generated_write_probe_recorded',
        'versions':{name:version(name) for name in ['transformers','vllm']},'cases':results,
        'scope':'Generated synthetic tool calls with raw token evidence; no file tool executed'},indent=2)+'\n')
    print('Exact generated argument matches:',sum(r['exact_match'] for r in results),'/',len(results))


if __name__=='__main__':
    main()
