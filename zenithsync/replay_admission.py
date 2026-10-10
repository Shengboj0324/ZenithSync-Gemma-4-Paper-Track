"""Cross-check replay evidence before rights, split, and GPU admission reviews.

This verifies local evidence consistency, not the truth of arbitrary supplied
receipts. It never approves training or treats a replay as a new model result.
"""
from pathlib import Path

from .artifacts import file_record, load_json
from .replay_history import native_replay_history


def assess_replay_bundle(*, attempt: Path, history: Path, grade: Path,
                         tokens: Path, max_input_tokens: int,
                         output_reserve: int, max_tool_calls: int) -> dict:
    for name, value in [('max_input_tokens', max_input_tokens),
                        ('max_tool_calls', max_tool_calls)]:
        if type(value) is not int or value <= 0:
            raise ValueError(name + ' must be a positive integer')
    if type(output_reserve) is not int or not 0 <= output_reserve < max_input_tokens:
        raise ValueError('Invalid output reserve')
    paths = {
        'attempt': attempt / 'receipt.json', 'events': attempt / 'events.json',
        'patch': attempt / 'submitted.patch', 'history_receipt': history / 'receipt.json',
        'history': history / 'history.json', 'mapping': history / 'mapping.json',
        'tools': history / 'tools.json', 'grade': grade / 'report.json',
        'tokens': tokens / 'report.json',
    }
    identities = {name: file_record(path) for name, path in paths.items()}
    data = {name: load_json(path) for name, path in paths.items() if name != 'patch'}
    replay, receipt = data['attempt'], data['history_receipt']
    grading, token_report = data['grade'], data['tokens']
    backend = grading.get('backend', 'r2e_publisher_groups')
    if backend not in ('r2e_publisher_groups', 'swe_rebench_full_nodeid_reference'):
        raise ValueError('Unknown grading backend')
    if backend == 'swe_rebench_full_nodeid_reference' and grading['task'] != replay['instance_id']:
        raise ValueError('Graded task differs from replay')
    graded_patch = grading['inputs']['patch'] if backend == 'swe_rebench_full_nodeid_reference' else grading['patch']
    for label, declared, actual in [
        ('replay patch', replay['patch'], identities['patch']),
        ('graded patch', graded_patch, identities['patch']),
        ('graded attempt', grading['attempt'], identities['attempt']),
        ('history attempt', receipt['attempt'], identities['attempt']),
        ('history events', receipt['events'], identities['events']),
        ('history content', receipt['history'], identities['history']),
        ('history tools', receipt['tools'], identities['tools']),
        ('token history', token_report['history'], identities['history']),
        ('token tools', token_report['tools'], identities['tools']),
    ]:
        if declared != actual:
            raise ValueError(label + ' identity mismatch')
    if replay['status'] != 'replayed_not_graded' or replay['cleanup']['removed'] is not True:
        raise ValueError('Completed replay and verified cleanup required')
    messages = data['history']
    if (not isinstance(messages, list) or len(messages) < 4
            or messages[0].get('role') != 'system' or messages[1].get('role') != 'user'):
        raise ValueError('Expected reconstructed initial system and issue messages')
    allowed = {tool['function']['name'] for tool in data['tools']}
    if len(allowed) != len(data['tools']) or allowed != set(replay['available_tools']):
        raise ValueError('Native tool schema set mismatch')
    reconstructed = native_replay_history(data['events'], system=messages[0]['content'],
        problem=messages[1]['content'], allowed_tools=allowed)
    if reconstructed['messages'] != messages or reconstructed['mapping'] != data['mapping']:
        raise ValueError('History differs from captured native exchanges')
    if type(receipt['exchanges']) is not int or receipt['exchanges'] != len(data['mapping']):
        raise ValueError('Exchange count mismatch')
    # The replay runner charges all native exchanges except terminal submission.
    actual_calls = sum(call['name'] != 'submit_patch' for event in data['events']
                       for call in event['native_calls'])
    if type(replay['tool_calls']) is not int or replay['tool_calls'] != actual_calls:
        raise ValueError('Charged native call count mismatch')
    input_count, supervised = token_report['input_tokens'], token_report['supervised_tokens']
    if (type(input_count) is not int or type(supervised) is not int
            or not 0 < supervised < input_count):
        raise ValueError('Invalid supervised/input token counts')
    if token_report['truncated'] is not False:
        raise ValueError('Truncated or unspecified tokenization rejected')
    result = grading['grading']
    match_key = ('all_cases_match_reference' if backend == 'swe_rebench_full_nodeid_reference'
                 else 'all_cases_match_publisher_expectations')
    matches = result[match_key]
    if type(matches) is not bool or type(result['case_count']) is not int or result['case_count'] <= 0:
        raise ValueError('Invalid grading result')
    consistency_keys = (('disagreements',) if backend == 'swe_rebench_full_nodeid_reference'
                        else ('disagreements', 'missing_groups', 'unexpected_groups'))
    inconsistencies = any(result[key] for key in consistency_keys)
    if matches and inconsistencies:
        raise ValueError('Contradictory grading summary')
    blockers = []
    if not matches:
        blockers.append('publisher_expectations_not_matched')
    if actual_calls > max_tool_calls:
        blockers.append('native_call_budget_exceeded')
    if input_count + output_reserve > max_input_tokens:
        blockers.append('input_plus_output_reserve_exceeds_context')
    if any(file_record(paths[name]) != identity for name, identity in identities.items()):
        raise ValueError('Evidence changed during assessment')
    return {
        'schema_version': 1, 'instance_id': replay['instance_id'],
        'trajectory_id': replay['trajectory_id'], 'identities': identities,
        'grading_backend': backend,
        'policy': {'max_input_tokens': max_input_tokens, 'output_reserve': output_reserve,
                   'max_tool_calls': max_tool_calls},
        'input_tokens': input_count, 'supervised_tokens': supervised,
        'native_tool_calls': actual_calls, 'mechanical_blockers': blockers,
        'mechanical_checks_passed': not blockers, 'training_approved': False,
        'remaining_gates': ['rights_and_attribution', 'frozen_split_and_duplicate_review',
                            'source_and_evaluator_qualification', 'training_runtime_and_memory'],
        'limitations': ['Cross-artifact consistency, not authenticity of arbitrary local receipts.',
                       'Token counts are linked to tokenizer audit; encoding is not rerun here.',
                       'Initial prompt was reconstructed; teacher conditioning is not established.',
                       'A matching teacher patch is not evidence of a new model improvement.'],
    }
