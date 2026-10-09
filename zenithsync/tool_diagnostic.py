"""Independent, strict grammar check for two-string native Gemma write calls.

Diagnostic only: not a replacement production parser. Inputs containing native
delimiter tokens as literal file content are outside this experiment's grammar.
"""

import re

from .conversation import normalize_arguments

START, END, QUOTE = '<|tool_call>', '<tool_call|>', '<|"|>'


def parse_native_write(raw):
    if raw.count(START) != 1 or raw.count(END) != 1:
        raise ValueError('Expected exactly one complete native call')
    begin = raw.index(START) + len(START)
    end = raw.index(END)
    body = raw[begin:end].strip()
    prefix = 'call:write_file{'
    if not body.startswith(prefix) or not body.endswith('}'):
        raise ValueError('Unexpected native function or incomplete body')
    body = body[len(prefix):-1]
    result = {}
    while body.strip():
        match = re.match(r'\s*(filepath|content)\s*:\s*', body)
        if not match or match[1] in result:
            raise ValueError('Unknown or duplicate argument')
        key = match[1]
        body = body[match.end():]
        if not body.startswith(QUOTE):
            raise ValueError('Native string opening delimiter missing')
        body = body[len(QUOTE):]
        stop = body.find(QUOTE)
        if stop < 0:
            raise ValueError('Native string closing delimiter missing')
        result[key] = body[:stop]
        body = body[stop + len(QUOTE):].lstrip()
        if not body:
            break
        if not body.startswith(',') or not body[1:].strip():
            raise ValueError('Invalid argument separator')
        body = body[1:]
    if set(result) != {'filepath', 'content'}:
        raise ValueError('Required argument absent')
    return result


def assess_write_response(response, raw, expected):
    choice = response['choices'][0]
    if choice['finish_reason'] == 'length':
        return {'classification': 'output_budget_exhausted'}
    try:
        native = parse_native_write(raw)
    except ValueError as error:
        return {'classification': 'native_format_invalid_or_out_of_scope', 'detail': str(error)}
    calls = choice['message'].get('tool_calls') or []
    parsed = None
    if len(calls) == 1 and calls[0]['function']['name'] == 'write_file':
        try:
            parsed = normalize_arguments(calls[0]['function']['arguments'])
        except ValueError:
            pass
    if native != parsed:
        return {'classification': 'native_transport_disagreement', 'native': native, 'parsed': parsed}
    return {'classification': 'exact_match' if native == expected else 'instruction_mismatch',
            'native': native, 'parsed': parsed}
