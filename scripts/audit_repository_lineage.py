"""Read GitHub identity metadata only; never open reserved evaluation task bodies."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.resolve_source_environments import fetch
from zenithsync.artifacts import canonical_json,file_record


def project_repository(obj):
    def identity(value):
        if type(value.get('id')) is not int or value['id']<=0:
            raise ValueError('Missing immutable repository ID')
        if (not isinstance(value.get('full_name'),str)
                or re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',value['full_name']) is None
                or any(part in ('.','..') for part in value['full_name'].split('/'))):
            raise ValueError('Malformed repository name')
        return {'id':value['id'],'full_name':value['full_name']}
    result=identity(obj)
    if type(obj.get('fork')) is not bool:raise ValueError('Missing fork indicator')
    result['fork']=obj['fork']
    if obj['fork']:
        result['parent']=identity(obj['parent']);result['network_root']=identity(obj['source'])
    else:result['network_root']=identity(obj)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    selected_path=ROOT/'evidence/data/replay-selection-002/selected.json'
    selected=json.loads(selected_path.read_text())
    evaluation_path=ROOT/'evidence/p1/task-index-001/receipt.json'
    evaluation=json.loads(evaluation_path.read_text())
    training={r['repo'] for r in selected};reserved=set(evaluation['repo_counts'])
    args.output.mkdir(parents=True,exist_ok=False)
    import requests
    results={}
    with requests.Session() as session:
        for repo in sorted(training|reserved):
            if re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repo) is None:raise ValueError('Invalid requested repo')
            url='https://api.github.com/repos/'+repo
            try:
                raw,_=fetch(session,url,headers={'Accept':'application/vnd.github+json'})
                result={'status':'resolved',**project_repository(json.loads(raw)),
                        'response_sha256':hashlib.sha256(raw).hexdigest()}
            except (requests.RequestException,ValueError,KeyError,TypeError) as error:
                result={'status':'unresolved','error_type':type(error).__name__,
                        'http_status':getattr(getattr(error,'response',None),'status_code',None)}
            results[repo]={**result,'url':url}
            (args.output/'repositories.json').write_bytes(canonical_json(results))
            print({'repo':repo,'status':result['status']},flush=True)
    complete=all(r['status']=='resolved' for r in results.values())
    overlaps=[]
    for candidate in sorted(training):
        for heldout in sorted(reserved):
            a,b=results[candidate],results[heldout]
            if a['status']=='resolved' and b['status']=='resolved':
                if a['id']==b['id'] or a['network_root']['id']==b['network_root']['id']:
                    overlaps.append({'candidate':candidate,'reserved':heldout})
    report={'retrieved_at':datetime.now(timezone.utc).isoformat(),
        'inputs':{'selection':file_record(selected_path),'evaluation_metadata':file_record(evaluation_path)},
        'script':file_record(Path(__file__)),'repositories':file_record(args.output/'repositories.json'),
        'source_repositories':sorted(training),'reserved_repositories':sorted(reserved),
        'identity_resolution_complete':complete,'known_network_overlaps':overlaps,
        'identity_screen_passed':complete and not overlaps,'training_approved':False,
        'scope':'Current GitHub canonical IDs and declared fork-network roots only. No evaluation bodies read.',
        'limitations':['Detached copies, historical forks, vendored code and semantic duplicates are not excluded.',
                       'No proof of independence from model pretraining or hidden evaluation repositories.']}
    (args.output/'report.json').write_bytes(canonical_json(report))


if __name__=='__main__':main()
