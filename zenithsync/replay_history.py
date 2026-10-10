"""Project captured native exchanges without inventing reasoning or observations."""
from .artifacts import canonical_json
from .conversation import normalize_history


def mini_replay_history(events, *, source_messages, system, problem, allowed_tools):
    """Project exact source commands followed by explicitly authored native actions.

    The source terminal only exports a patch. Its replacement cleanup and native
    submission remain attributed to the adapter in the separate message mapping.
    No source responses, reasoning, or success narratives enter this projection.
    """
    source = normalize_history(source_messages, allowed_tools={'bash'}, allow_pending=True)
    commands = []
    for index, message in enumerate(source):
        for call in message.get('tool_calls', []):
            arguments = call['function']['arguments']
            if set(arguments) != {'command'} or not isinstance(arguments['command'], str):
                raise ValueError('Exact source bash command required')
            commands.append((index, arguments))
    terminals = {'echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && cat patch.txt',
                 'echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && cat /testbed/patch.txt'}
    if not commands or commands[-1][1]['command'] not in terminals:
        raise ValueError('Reviewed source terminal required')
    if not isinstance(events, list) or len(events) != len(commands) + 1:
        raise ValueError('Every nonterminal source command and both adapter actions required')
    projected = []
    for ordinal, event in enumerate(events):
        if (not isinstance(event, dict) or set(event) != {
                'source_index', 'adapter_authored', 'name', 'arguments', 'result'}
                or type(event['adapter_authored']) is not bool
                or not isinstance(event['result'], dict)):
            raise ValueError('Exact native event with explicit authorship required')
        if ordinal < len(commands) - 1:
            index, arguments = commands[ordinal]
            if (event['adapter_authored'] or type(event['source_index']) is not int
                    or event['source_index'] != index or event['name'] != 'run_command'
                    or event['arguments'] != arguments):
                raise ValueError('Native source command differs from recorded source')
        else:
            if event['adapter_authored'] is not True or event['source_index'] is not None:
                raise ValueError('Adapter suffix cannot claim source authorship')
            expected = 'submit_patch' if ordinal == len(events) - 1 else 'run_command'
            if event['name'] != expected or event['result'].get('status') != 'ok':
                raise ValueError('Successful cleanup and submission required')
            if expected == 'submit_patch' and event['arguments'] != {}:
                raise ValueError('Native submission takes no arguments')
        projected.append({'source_index': ordinal, 'kind': 'action',
            'result': event['result'], 'native_calls': [{key: event[key]
                for key in ('name', 'arguments', 'result')}]})
    result = native_replay_history(projected, system=system, problem=problem,
                                   allowed_tools=allowed_tools)
    for ordinal, mapping in enumerate(result['mapping']):
        mapping.update(event_index=ordinal, source_index=events[ordinal]['source_index'],
                       adapter_authored=events[ordinal]['adapter_authored'])
    result['scope'] += '; cleanup and submission are adapter-authored, explicitly mapped'
    return result


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
