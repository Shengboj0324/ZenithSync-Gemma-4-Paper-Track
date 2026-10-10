"""Serialize inspected Open-SWE mini histories without claiming native semantics."""

from .conversation import normalize_history
from .trajectory_import import SourceHistoryError


def convert_mini_history(history):
    """Infer only single-pending response links; preserve text and reasoning.

    The last bash call remains unanswered. No output, completion, successful
    execution or patch correctness is inferred from its command text.
    """
    if not isinstance(history, list) or not history:
        raise SourceHistoryError('empty_or_invalid_history')
    messages, links = [], []
    pending = None
    for index, source in enumerate(history):
        if not isinstance(source, dict) or set(source) != {
                'role', 'content', 'reasoning_content', 'tool_calls'}:
            raise SourceHistoryError('source_message_schema_drift')
        role = source['role']
        if role not in {'system', 'user', 'assistant', 'tool'}:
            raise SourceHistoryError('unsupported_source_role')
        content = source['content']
        if content is None and role == 'assistant':
            content = ''
        if not isinstance(content, str):
            raise SourceHistoryError('nontext_content')
        reasoning = source['reasoning_content']
        if reasoning is not None and not isinstance(reasoning, str):
            raise SourceHistoryError('nontext_reasoning')
        if reasoning and role != 'assistant':
            raise SourceHistoryError('reasoning_outside_assistant')
        message = {'role': role, 'content': content}
        if role == 'assistant' and reasoning is not None:
            message['reasoning_content'] = reasoning
        calls = source['tool_calls']
        if role == 'tool':
            if calls not in (None, []):
                raise SourceHistoryError('tool_response_contains_calls')
            if pending is None:
                raise SourceHistoryError('orphan_tool_response')
            call_id, call_index = pending
            message.update(tool_call_id=call_id, name='bash')
            links.append({'response_index': index, 'call_index': call_index,
                          'call_id': call_id, 'basis': 'inferred_single_pending_call'})
            pending = None
        else:
            if pending is not None:
                raise SourceHistoryError('interrupted_tool_exchange')
            if calls not in (None, []):
                if role != 'assistant' or not isinstance(calls, list):
                    raise SourceHistoryError('calls_outside_assistant')
                if len(calls) != 1:
                    raise SourceHistoryError('ambiguous_parallel_response_linkage')
                message['tool_calls'] = calls
                try:
                    message = normalize_history([message], allowed_tools={'bash'}, allow_pending=True)[0]
                except ValueError as error:
                    raise SourceHistoryError('invalid_source_call') from error
                call = message['tool_calls'][0]
                arguments = call['function']['arguments']
                if (set(arguments) != {'command'} or not isinstance(arguments['command'], str)
                        or not arguments['command'].strip()):
                    raise SourceHistoryError('invalid_bash_arguments')
                pending = (call['id'], index)
        messages.append(message)
    if pending is None:
        raise SourceHistoryError('missing_pending_terminal_bash_call')
    try:
        normalized = normalize_history(messages, allowed_tools={'bash'}, allow_pending=True)
    except ValueError as error:
        raise SourceHistoryError('source_history_validation_failed') from error
    return {'messages': normalized, 'response_links': links,
            'terminal_pending_call_id': pending[0],
            'terminal_status': 'unanswered_source_bash_call_not_execution_evidence',
            'training_approved': False,
            'scope': 'Serialization only. Bash retains source semantics; no command executed or rewritten.'}
