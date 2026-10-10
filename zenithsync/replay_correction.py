"""Explicit, hash-bound correction plans; no invented observations or admission."""
import re


def validate_correction_plan(plan):
    if (not isinstance(plan, dict) or set(plan) != {
            'schema_version', 'author', 'reason', 'source_patch', 'corrected_patch', 'commands'}
            or type(plan['schema_version']) is not int or plan['schema_version'] != 1
            or plan['author'] != 'assistant'
            or not isinstance(plan['reason'], str) or not plan['reason'].strip()):
        raise ValueError('Explicit assistant-authored correction plan required')
    for key in ('source_patch', 'corrected_patch'):
        value = plan[key]
        if (not isinstance(value, dict) or set(value) != {'sha256', 'size_bytes'}
                or not isinstance(value['sha256'], str)
                or re.fullmatch('[0-9a-f]{64}', value['sha256']) is None
                or type(value['size_bytes']) is not int or not 0 < value['size_bytes'] <= 2 * 1024**2):
            raise ValueError('Bound patch identity required')
    if plan['source_patch'] == plan['corrected_patch']:
        raise ValueError('Correction must describe a different patch')
    commands = plan['commands']
    if not isinstance(commands, list) or not 1 <= len(commands) <= 8:
        raise ValueError('Correction requires one to eight explicit commands')
    for row in commands:
        if (not isinstance(row, dict) or set(row) != {'command', 'expected_exit_code'}
                or not isinstance(row['command'], str) or not row['command'].strip()
                or '\0' in row['command']
                or type(row['expected_exit_code']) is not int
                or not 0 <= row['expected_exit_code'] <= 255):
            raise ValueError('Explicit correction command and process exit required')
    if commands[-1]['expected_exit_code'] != 0:
        raise ValueError('Correction must end with a successful verification/export command')
    return plan


def verify_correction_result(result, expected_exit_code):
    """Accept native process results only, including an explicitly expected failure."""
    if (not isinstance(result, dict) or type(expected_exit_code) is not int
            or not 0 <= expected_exit_code <= 255):
        raise ValueError('Native correction result required')
    if expected_exit_code == 0:
        valid = result.get('status') == 'ok' and type(result.get('exit_code')) is int
        actual = result.get('exit_code')
    else:
        detail = result.get('details')
        valid = (result.get('status') == 'error' and result.get('error_type') == 'CommandError'
                 and isinstance(detail, dict) and type(detail.get('exit_code')) is int)
        actual = detail.get('exit_code') if isinstance(detail, dict) else None
    if not valid or actual != expected_exit_code:
        raise ValueError('Correction command did not produce the reviewed process exit')


def verify_correction_binding(profile, replay):
    """Check provenance claims; callers must separately verify all patch bytes."""
    if 'correction' not in profile:
        if any(key in replay for key in ('correction', 'source_intended_patch',
                                        'native_submission_equals_corrected_export')):
            raise ValueError('Correction claims require a reviewed plan')
        if replay.get('native_submission_equals_source_export') is not True:
            raise ValueError('Source submission equality required')
        return None
    plan = validate_correction_plan(profile['correction'])
    if (replay.get('correction') != plan or replay.get('source_intended_patch') != plan['source_patch']
            or replay.get('patch') != plan['corrected_patch']
            or replay.get('intended_patch') != plan['corrected_patch']
            or replay.get('native_submission_equals_source_export') is not False
            or replay.get('native_submission_equals_corrected_export') is not True):
        raise ValueError('Correction patch provenance differs from reviewed plan')
    return plan
