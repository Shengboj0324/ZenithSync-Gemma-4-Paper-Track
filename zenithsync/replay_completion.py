"""Explicit assistant-authored completion actions before native submission."""

import re

from .replay_correction import verify_correction_result
from .replay_history import native_replay_history


def validate_completion_plan(plan):
    required = {'schema_version', 'author', 'reason', 'source_actions', 'final_patch', 'commands'}
    if (not isinstance(plan, dict) or set(plan) != required
            or type(plan['schema_version']) is not int or plan['schema_version'] != 1
            or plan['author'] != 'assistant'
            or not isinstance(plan['reason'], str) or not plan['reason'].strip()):
        raise ValueError('Explicit assistant completion plan required')
    for key in ('source_actions', 'final_patch'):
        identity = plan[key]
        if (not isinstance(identity, dict) or set(identity) != {'sha256', 'size_bytes'}
                or not isinstance(identity['sha256'], str)
                or re.fullmatch('[0-9a-f]{64}', identity['sha256']) is None
                or type(identity['size_bytes']) is not int
                or not 0 < identity['size_bytes'] <= 2 * 1024**2):
            raise ValueError('Bound source actions and final patch required')
    commands = plan['commands']
    if not isinstance(commands, list) or not 1 <= len(commands) <= 8:
        raise ValueError('One to eight completion commands required')
    for row in commands:
        if (not isinstance(row, dict) or set(row) != {'command', 'expected_exit_code'}
                or not isinstance(row['command'], str) or not row['command'].strip()
                or '\0' in row['command'] or type(row['expected_exit_code']) is not int
                or not 0 <= row['expected_exit_code'] <= 255):
            raise ValueError('Explicit completion command and process exit required')
    if commands[-1]['expected_exit_code'] != 0:
        raise ValueError('Completion must end with a successful command')
    return plan


def completed_replay_history(events, *, plan, system, problem, allowed_tools):
    """Verify the declared suffix and preserve source versus added authorship."""
    plan = validate_completion_plan(plan)
    count = len(plan['commands'])
    if not isinstance(events, list) or len(events) < count + 2:
        raise ValueError('Source prefix, completion and final submission required')
    prefix, suffix, final = events[:-count-1], events[-count-1:-1], events[-1]
    if any(e.get('kind') in ('completion', 'finish') or 'adapter_authored' in e for e in prefix):
        raise ValueError('Unexpected completion or submission in source prefix')
    previous = -1
    for event in [*prefix, final]:
        index = event.get('source_index')
        if type(index) is not int or index <= previous:
            raise ValueError('Source order changed')
        previous = index
    for event, command in zip(suffix, plan['commands']):
        if (set(event) != {'source_index', 'adapter_authored', 'kind', 'result', 'native_calls'}
                or event['source_index'] is not None or event['adapter_authored'] is not True
                or event['kind'] != 'completion'
                or event['native_calls'] != [{'name': 'run_command',
                    'arguments': {'command': command['command']}, 'result': event['result']}]):
            raise ValueError('Completion event differs from reviewed plan')
        verify_correction_result(event['result'], command['expected_exit_code'])
    if (final.get('kind') != 'finish' or 'adapter_authored' in final
            or final.get('result', {}).get('status') != 'ok'
            or final.get('native_calls') != [{'name': 'submit_patch', 'arguments': {},
                                              'result': final.get('result')}]):
        raise ValueError('Successful source-terminal submission required')
    # The underlying projection uses ordered indices for call IDs. Restore the
    # actual source positions in its mapping; added actions have no source index.
    projected = native_replay_history(
        [{**event, 'source_index': i} for i, event in enumerate(events)],
        system=system, problem=problem, allowed_tools=allowed_tools)
    for row in projected['mapping']:
        ordinal = row['source_index']
        event = events[ordinal]
        row.update(event_index=ordinal, source_index=event['source_index'],
                   adapter_authored=event.get('adapter_authored', False))
    projected['scope'] += '; explicit assistant completion actions, separately attributed'
    return projected
