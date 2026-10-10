"""Cross-check V2 replay evidence; never authorize training from local receipts."""
import hashlib
from pathlib import Path

from .artifacts import canonical_json, file_record, load_json
from .pytest_controls import compare_candidate, compare_controls
from .replay_history import mini_replay_history
from .submission_reconciliation import scratch_cleanup_command
from .training_batch import collate_training_examples
from .resource_replay_binding import verify_resource_replay_binding
from .session_resource_bundle import session_resource_payload


def assess_mini_replay_bundle(*, root, attempt, history, grade, tokens, candidate,
                             profile, task, max_input_tokens=32768,
                             output_reserve=8192, max_tool_calls=40,
                             historical_sources=None, session_resources=None):
    """Recompute history, test comparisons, target counts, and budget decisions.

    Hashes detect drift in supplied evidence, not fabricated evidence. The caller
    must separately qualify the executor, rights, splits and task semantics.
    """
    for value in (max_input_tokens, max_tool_calls):
        if type(value) is not int or value <= 0:
            raise ValueError('Positive integer budgets required')
    if type(output_reserve) is not int or not 0 <= output_reserve < max_input_tokens:
        raise ValueError('Output reserve must fit context')
    root = Path(root).resolve(strict=True)
    identities = {}

    def path(value):
        result = (root / value).resolve(strict=True)
        if not result.is_relative_to(root):
            raise ValueError('Evidence outside workspace')
        return result

    def record(value):
        resolved = path(value)
        identity = file_record(resolved)
        if str(resolved) in identities and identities[str(resolved)] != identity:
            raise ValueError('Evidence changed during assessment')
        identities[str(resolved)] = identity
        return identity

    def read(value):
        record(value)
        return load_json(path(value))

    def verify(value, expected):
        if record(value) != expected:
            raise ValueError('Evidence identity mismatch: ' + str(value))

    # Historical executions bind the code that actually ran, not today's edits.
    # Only explicitly mapped source files may use archived bytes. Task, token,
    # patch, and receipt evidence always resolves at its original location.
    if historical_sources is None:
        historical_sources = {}
    if not isinstance(historical_sources, dict):
        raise ValueError('Historical source mapping must be an object')
    archives, used_archives = {}, {}
    for original, archived in historical_sources.items():
        if not isinstance(original, str) or not isinstance(archived, str):
            raise ValueError('Historical source paths must be strings')
        original_path, archived_path = path(original), path(archived)
        relative = original_path.relative_to(root)
        archive_relative = archived_path.relative_to(root)
        if (relative.parts[0] not in ('scripts', 'zenithsync') or relative.suffix != '.py'
                or archive_relative.parts[:2] != ('artifacts', 'official')
                or len(archive_relative.parts) != len(relative.parts) + 3
                or archive_relative.parts[3:] != relative.parts):
            raise ValueError('Only matching archived implementation sources may be mapped')
        key = str(original_path)
        if key in archives:
            raise ValueError('Duplicate normalized historical source')
        archives[key] = archived_path

    attempt, history, grade, tokens = map(Path, (attempt, history, grade, tokens))
    replay = read(attempt / 'receipt.json')
    history_receipt = read(history / 'receipt.json')
    grading = read(grade / 'report.json')
    audit = read(tokens / 'report.json')
    for document, key in ((history_receipt, 'input_bindings'), (grading, 'inputs'),
                           (audit, 'input_bindings')):
        for name, identity in document[key].items():
            original = str(path(name))
            if original in archives:
                archive = archives[original]
                verify(archive, identity)
                used_archives[original] = {'archive': str(archive), 'identity': identity}
            else:
                verify(name, identity)
    if set(used_archives) != set(archives):
        raise ValueError('Unused historical source mapping')
    # Require the grading receipt to bind this exact replay and submitted patch.
    grade_inputs = {str(path(name)): identity for name, identity in grading['inputs'].items()}
    for name in ('receipt.json', 'submitted.patch'):
        if grade_inputs.get(str(path(attempt / name))) != record(attempt / name):
            raise ValueError('Grading belongs to another replay')
    verify(attempt / 'receipt.json', history_receipt['attempt'])
    verify(attempt / 'submitted.patch', replay['patch'])
    verify(attempt / 'intended.patch', replay['intended_patch'])
    if (replay['native_submission_equals_source_export'] is not True
            or replay['patch'] != replay['intended_patch']):
        raise ValueError('Native patch differs from source intended export')
    verify(candidate, replay['candidate'])
    verify(profile, replay['profile'])
    for name in ('history', 'tools', 'mapping'):
        verify(history / (name + '.json'), history_receipt[name])
    for name in ('history', 'tools'):
        if audit[name] != history_receipt[name]:
            raise ValueError('Token audit belongs to another history')
    if (replay['status'] != 'replayed_not_graded' or replay['cleanup']['removed'] is not True
            or replay.get('standalone_cleanup') is not True
            or replay['source_observations_reused'] is not False
            or grading['sanitized_snapshot'] is not True):
        raise ValueError('Completed portable replay and sanitized evaluation required')
    source, task_data, reviewed = read(candidate), read(task), read(profile)
    resource_proof, resource_files = verify_resource_replay_binding(
        replay, reviewed, path(session_resources) if session_resources is not None else None)
    resource_payload = None
    if resource_proof is None:
        if any(key in document for document, key in (
                (history_receipt, 'resource_environment'), (grading, 'session_resources'),
                (grading, 'resource_profile'))):
            raise ValueError('Resource claims without a bound replay environment')
    else:
        if (history_receipt.get('resource_environment') != resource_proof
                or grading.get('session_resources') != resource_proof['staging']['bundle']):
            raise ValueError('Replay, history and grading resource environments differ')
        resource_profile = grading.get('resource_profile')
        if (not isinstance(resource_profile, str)
                or grade_inputs.get(str(path(resource_profile))) != record(resource_profile)
                or read(resource_profile).get('session_resources') != reviewed['session_resources']):
            raise ValueError('Grading requires the same explicitly bound resource review')
        history_inputs = {str(path(name)): identity for name, identity in history_receipt['input_bindings'].items()}
        for name, identity in resource_files.items():
            verify(name, identity)
            if history_inputs.get(str(path(name))) != identity:
                raise ValueError('History does not bind the verified resource inputs')
            if Path(name).name != 'resource_replay_binding.py' and grade_inputs.get(str(path(name))) != identity:
                raise ValueError('Grading does not bind the verified resource inputs')
        resource_payload, _ = session_resource_payload(path(session_resources),
            max_bytes=reviewed['session_resources']['max_bytes'])
    if (source['task_metadata'] != replay['task']
            or any(task_data[key] != replay['task'][key] for key in ('repo', 'instance_id', 'base_commit'))
            or grade_inputs.get(str(path(task))) != record(task)):
        raise ValueError('Task identity mismatch')
    events, messages, tools, mapping = [read(value) for value in (
        attempt / 'events.json', history / 'history.json', history / 'tools.json', history / 'mapping.json')]
    allowed = {tool['function']['name'] for tool in tools}
    if len(tools) != 9 or len(allowed) != 9:
        raise ValueError('Nine native tool schemas required')
    reconstructed = mini_replay_history(events, source_messages=source['messages'],
        system=messages[0]['content'], problem=task_data['problem_statement'], allowed_tools=allowed)
    if reconstructed['messages'] != messages or reconstructed['mapping'] != mapping:
        raise ValueError('History differs from fresh native exchanges')
    expected_command = scratch_cleanup_command(python=reviewed['python'],
                                               scratch_paths=reviewed['scratch_paths'])
    if events[-2]['arguments'] != {'command': expected_command}:
        raise ValueError('Cleanup action differs from reviewed implementation')
    calls = sum(event['name'] != 'submit_patch' for event in events)
    if (type(replay['tool_calls']) is not int or replay['tool_calls'] != calls
            or type(history_receipt['exchanges']) is not int
            or history_receipt['exchanges'] != len(events)):
        raise ValueError('Native exchange count mismatch')
    outcomes = {}
    for role in ('base', 'reference', 'candidate'):
        execution = read(grade / role / 'receipt.json')
        runtime = read(grade / role / 'runtime.json')
        if (execution != grading['controls'][role] or execution['image_id'] != replay['image']
                or any(execution[key] != 0 for key in ('returncode', 'cleanup_returncode', 'copy_returncode'))
                or execution['state']['OOMKilled'] or 'error' in runtime
                or runtime.get('tracked_diff_unchanged_by_tests') is not True):
            raise ValueError('Invalid evaluator execution')
        outcomes[role] = read(grade / role / 'outcomes.json')
        if resource_proof is not None:
            payload_path = grade / role / 'session_resources.json'
            record(payload_path)
            if path(payload_path).read_bytes() != resource_payload:
                raise ValueError('Executed grader resource bytes differ from replay bundle')
            verify(grade / role / 'session_resource_replay.py', resource_proof['staging']['adapter'])
            resource_events = read(grade / role / 'resource-events.json')
            if not isinstance(resource_events, list) or not resource_events:
                raise ValueError('Recorded-resource grading requires transport observations')
            resources = read(payload_path)
            for event in resource_events:
                if (not isinstance(event, dict) or event.get('allowed') is not True
                        or event.get('live_transport_executed') is not False
                        or event.get('method') != 'GET' or event.get('url') not in resources
                        or event.get('reason') is not None):
                    raise ValueError('Unsupported or failed grader resource event')
        if (runtime.get('tests_started') is not True
                or runtime.get('pytest_exit') != outcomes[role]['exitstatus']):
            raise ValueError('Runtime test status contradicts outcomes')
    expectations = {'FAIL_TO_PASS': task_data['FAIL_TO_PASS'],
                    'PASS_TO_PASS': task_data['PASS_TO_PASS'], 'FAIL_TO_FAIL': [], 'PASS_TO_FAIL': []}
    supplemental = None
    if 'supplemental_profile' in grading:
        supplemental_path = path(grading['supplemental_profile'])
        if grade_inputs.get(str(supplemental_path)) != record(supplemental_path):
            raise ValueError('Supplemental controls require a bound evaluator profile')
        supplemental = read(supplemental_path)['supplemental_pass_to_pass']
        if not supplemental:
            raise ValueError('Supplemental profile must declare additional tests')
    controls = compare_controls(outcomes['base'], outcomes['reference'], expectations,
                                supplemental_pass_to_pass=supplemental)
    comparison = compare_candidate(outcomes['reference'], outcomes['candidate'])
    if controls != grading['comparison'] or comparison != grading['candidate_comparison']:
        raise ValueError('Grading summary contradicts complete test outcomes')
    verify(tokens / 'tokens.json', audit['token_candidate'])
    encoded = read(tokens / 'tokens.json')
    for name in ('history', 'tools'):
        if encoded[name] != history_receipt[name]:
            raise ValueError('Token arrays belong to another history')
    for field, declared in (('input_ids', 'input_sha256'), ('labels', 'labels_sha256')):
        if hashlib.sha256(canonical_json(encoded[field])).hexdigest() != audit[declared]:
            raise ValueError('Token array hash mismatch')
    count = len(encoded['input_ids'])
    batch = collate_training_examples([encoded], pad_token_id=encoded['pad_token_id'],
        vocab_size=encoded['vocab_size'], max_length=max(count, max_input_tokens))
    if (type(audit['input_tokens']) is not int or audit['input_tokens'] != count
            or type(audit['supervised_tokens']) is not int
            or audit['supervised_tokens'] != batch['supervised_tokens']
            or audit['truncated'] is not False):
        raise ValueError('Token counts or truncation contradict arrays')
    blockers = []
    if not comparison['all_cases_match_reference']:
        blockers.append('candidate_does_not_match_reference')
    if calls > max_tool_calls:
        blockers.append('native_call_budget_exceeded')
    if count + output_reserve > max_input_tokens:
        blockers.append('input_plus_output_reserve_exceeds_context')
    if any(file_record(Path(name)) != identity for name, identity in identities.items()):
        raise ValueError('Evidence changed during assessment')
    result = {'schema_version': 1, 'instance_id': task_data['instance_id'],
        'historical_sources': used_archives,
        'trajectory_id': source['source_metadata']['trajectory_id'], 'identities': identities,
        'grading_backend': 'swe_rebench_v2_full_nodeid_reference',
        'input_tokens': count, 'supervised_tokens': batch['supervised_tokens'],
        'native_tool_calls': calls, 'mechanical_blockers': blockers,
        'mechanical_checks_passed': not blockers, 'training_approved': False,
        'policy': {'max_input_tokens': max_input_tokens, 'output_reserve': output_reserve,
                   'max_tool_calls': max_tool_calls},
        'remaining_gates': ['rights_and_attribution', 'frozen_split_and_duplicate_review',
                            'task_semantic_alignment', 'training_runtime_and_memory'],
        'limitations': ['Evidence consistency does not authenticate arbitrary supplied receipts.',
                       'Tokenization is hash-bound to a prior audit, not rerun here.',
                       'Reconstructed conditioning and adapter-authored suffix require review.',
                       'This result is not learned model improvement or training approval.']}
    if resource_proof is not None:
        result['resource_environment'] = resource_proof
        result['remaining_gates'].append('captured_response_rights_and_supervision_review')
        result['limitations'].append('Current recorded response bodies do not establish historical website equivalence.')
    return result
