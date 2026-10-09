"""Project captured native exchanges without inventing reasoning or observations."""
from .artifacts import canonical_json
from .conversation import normalize_history


def native_replay_history(events, *, system, problem, allowed_tools):
    if not isinstance(system,str) or not system.strip() or not isinstance(problem,str) or not problem.strip():
        raise ValueError('Explicit system and issue text required')
    messages=[{'role':'system','content':system},{'role':'user','content':problem}]
    mapping=[]
    previous=-1
    for event in events:
        index=event['source_index']
        if type(index) is not int or index<=previous:
            raise ValueError('Source event order is not strictly increasing')
        previous=index
        calls=event['native_calls']
        if event['kind']=='think':
            if calls or event['result']['status']!='not_executed':
                raise ValueError('Teacher thought unexpectedly executed')
            continue
        if len(calls)!=1 or calls[0]['result']!=event['result']:
            raise ValueError('Missing, ambiguous, or inconsistent native exchange')
        call=calls[0]
        if call['name'] not in allowed_tools or not isinstance(call['arguments'],dict):
            raise ValueError('Unknown native tool or arguments')
        call_id=f'replay_{index:06d}'
        start=len(messages)
        messages.extend([
            {'role':'assistant','content':'','tool_calls':[{'id':call_id,'type':'function',
                'function':{'name':call['name'],'arguments':call['arguments']}}]},
            {'role':'tool','name':call['name'],'tool_call_id':call_id,
                'content':canonical_json(call['result']).decode('utf-8').rstrip('\n')},
        ])
        mapping.append({'source_index':index,'assistant_message_index':start,'call_id':call_id})
    if not mapping or messages[-2]['tool_calls'][0]['function']['name']!='submit_patch':
        raise ValueError('Native submission exchange required')
    return {'messages':normalize_history(messages,allowed_tools=allowed_tools),
            'mapping':mapping,'training_approved':False,
            'scope':'Recorded native exchanges with reconstructed initial prompt; no teacher reasoning or final narrative'}
