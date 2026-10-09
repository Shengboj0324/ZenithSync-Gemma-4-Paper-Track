"""Explicit source-text projection into Gemma's pre-action channel.

This is a transport convention, not a claim that source content was originally
a private reasoning field. Source records and transformation hashes must remain
available. It changes no tool name, argument value, call ID or result text.
"""

import hashlib

from .artifacts import canonical_json
from .conversation import normalize_history
from .trajectory_import import SOURCE_TOOLS


def project_pre_action_text(messages):
    normalized = normalize_history(messages, allowed_tools=set(SOURCE_TOOLS), allow_pending=True)
    user_indices = [index for index, message in enumerate(normalized) if message['role'] == 'user']
    if len(user_indices) != 1 or any(message['role'] == 'assistant' for message in normalized[:user_indices[0]]):
        raise ValueError('Projection requires one initial user turn; native later-user reasoning guard is unqualified')
    transformations = []
    for index, message in enumerate(normalized):
        if 'reasoning' in message or 'reasoning_content' in message:
            raise ValueError('Source already contains reasoning fields')
        if message['role'] == 'assistant' and message.get('tool_calls') and message['content']:
            text = message['content']
            message['reasoning'] = text
            message['content'] = ''
            transformations.append({'message_index': index, 'source_field': 'content',
                'destination_field': 'reasoning', 'text_sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
                'text_characters': len(text)})
    return {'messages': normalized, 'transformations': transformations,
            'source_history_sha256': hashlib.sha256(canonical_json(messages)).hexdigest(),
            'projected_history_sha256': hashlib.sha256(canonical_json(normalized)).hexdigest(),
            'scope': 'Single-user source transport projection only; not tool semantics, replay or training approval'}
