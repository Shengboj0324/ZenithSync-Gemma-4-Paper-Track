"""Strict SWE-Hero serialization conversion; not a tool-semantic adapter.

Response linkage is inferred only from a single outstanding source call.
Inferred linkage never establishes that a command ran or an issue was solved.
"""

from .conversation import normalize_history

SOURCE_TOOLS = frozenset({'think', 'str_replace_editor', 'execute_bash', 'finish'})


class SourceHistoryError(ValueError):
    """Stable reason code, without echoing source code or message bodies."""


def convert_swe_hero_history(history):
    if not isinstance(history, list) or not history:
        raise SourceHistoryError('empty_or_invalid_history')
    messages, links = [], []
    pending = None
    for index, source in enumerate(history):
        if not isinstance(source, dict) or set(source) != {'role', 'content', 'tool_calls'}:
            raise SourceHistoryError('source_message_schema_drift')
        role, content, calls = source['role'], source['content'], source['tool_calls']
        if role not in {'system', 'user', 'assistant', 'tool'}:
            raise SourceHistoryError('unsupported_source_role')
        if content is None and role == 'assistant':
            content = ''
        if not isinstance(content, str):
            raise SourceHistoryError('nontext_content')
        message = {'role': role, 'content': content}
        if role == 'tool':
            if calls not in (None, []):
                raise SourceHistoryError('tool_response_contains_calls')
            if pending is None:
                raise SourceHistoryError('orphan_tool_response')
            call_id, tool_name, call_index = pending
            message['tool_call_id'] = call_id
            message['name'] = tool_name
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
                    checked = normalize_history([message], allowed_tools=set(SOURCE_TOOLS), allow_pending=True)[0]
                except ValueError as error:
                    raise SourceHistoryError('invalid_source_call') from error
                message = checked
                call = checked['tool_calls'][0]
                pending = (call['id'], call['function']['name'], index)
        messages.append(message)
    if pending is None or pending[1] != 'finish':
        raise SourceHistoryError('missing_terminal_finish_call')
    try:
        normalized = normalize_history(messages, allowed_tools=set(SOURCE_TOOLS), allow_pending=True)
    except ValueError as error:
        raise SourceHistoryError('native_history_validation_failed') from error
    return {'messages': normalized, 'response_links': links,
            'terminal_pending_call_id': pending[0],
            'terminal_status': 'unanswered_source_finish_call_not_execution_evidence',
            'scope': 'Source serialization only; tools retain OpenHands semantics; not training approved'}
