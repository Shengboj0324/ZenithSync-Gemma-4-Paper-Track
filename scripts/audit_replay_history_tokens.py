"""Qualify untruncated native replay tokens and assistant masks without training."""
import argparse
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from zenithsync.artifacts import canonical_json,file_record
from zenithsync.training_masks import assistant_training_tokens


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--history',type=Path,required=True)
    p.add_argument('--model',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if version('transformers')!='5.13.1' or version('tokenizers')!='0.22.2':
        raise ValueError('Pinned tokenizer runtime required')
    receipt=json.loads((args.history/'receipt.json').read_text())
    for name in ('history','tools'):
        if file_record(args.history/(name+'.json'))!=receipt[name]:
            raise ValueError('History artifact changed')
    manifest=json.loads((ROOT/'evidence/p1/model-intake-001/model-manifest.json').read_text())
    assets={}
    for name in ('chat_template.jinja','tokenizer.json','tokenizer_config.json'):
        row=next(r for r in manifest['files'] if r['path']==name)
        assets[name]=file_record(args.model/name)
        if assets[name]!={k:row[k] for k in ('sha256','size_bytes')}:
            raise ValueError('Tokenizer asset mismatch')
    from transformers import AutoTokenizer
    tokenizer=AutoTokenizer.from_pretrained(args.model,local_files_only=True,trust_remote_code=False)
    messages=json.loads((args.history/'history.json').read_text())
    tools=json.loads((args.history/'tools.json').read_text())
    encoded=assistant_training_tokens(tokenizer,messages,
        template_sha256=assets['chat_template.jinja']['sha256'],
        allowed_tools={t['function']['name'] for t in tools},tools=tools)
    if any(file_record(args.model/name)!=identity for name,identity in assets.items()):
        raise ValueError('Tokenizer changed during encoding')
    args.output.mkdir(parents=True,exist_ok=False)
    report={'input_tokens':len(encoded['input_ids']),
        'supervised_tokens':sum(x!=-100 for x in encoded['labels'][1:]),
        'input_sha256':hashlib.sha256(canonical_json(encoded['input_ids'])).hexdigest(),
        'labels_sha256':hashlib.sha256(canonical_json(encoded['labels'])).hexdigest(),
        'within_32768_input_cap':len(encoded['input_ids'])<=32768,
        'history':receipt['history'],'tools':receipt['tools'],'assets':assets,
        'script':file_record(Path(__file__)),'mask_implementation':file_record(ROOT/'zenithsync/training_masks.py'),
        'training_approved':False,'truncated':False,
        'scope':'Native rendering, token identity and assistant-only span masks including all nine tool schemas; no GPU fit or training admission'}
    (args.output/'report.json').write_bytes(canonical_json(report))
    print({k:report[k] for k in ('input_tokens','supervised_tokens','within_32768_input_cap')})


if __name__=='__main__':main()
