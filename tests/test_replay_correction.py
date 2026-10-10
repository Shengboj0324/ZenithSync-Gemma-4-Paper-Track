import copy
import unittest

from zenithsync.replay_correction import (
    validate_correction_plan, verify_correction_binding, verify_correction_result)
from zenithsync.replay_history import mini_replay_history


def plan_fixture():
    return {'schema_version': 1, 'author': 'assistant', 'reason': 'Observed documentation defect',
            'source_patch': {'sha256': 'a' * 64, 'size_bytes': 20},
            'corrected_patch': {'sha256': 'b' * 64, 'size_bytes': 30},
            'commands': [{'command': 'check', 'expected_exit_code': 1},
                         {'command': 'repair && check && export', 'expected_exit_code': 0}]}


class ReplayCorrectionTests(unittest.TestCase):
    def test_plan_rejects_ambiguous_or_false_provenance(self):
        plan = plan_fixture()
        self.assertEqual(validate_correction_plan(plan), plan)
        variants = [dict(plan, author='original_teacher'), dict(plan, schema_version=True),
                    dict(plan, corrected_patch=plan['source_patch']), dict(plan, commands=[]),
                    dict(plan, reason=' '), dict(plan, observed_result='fake')]
        for field, value in [('size_bytes', True), ('sha256', 'not-a-digest')]:
            bad = copy.deepcopy(plan)
            bad['source_patch'][field] = value
            variants.append(bad)
        for value in (True, -1, 256, '0'):
            bad = copy.deepcopy(plan)
            bad['commands'][0]['expected_exit_code'] = value
            variants.append(bad)
        for bad in variants:
            with self.subTest(plan=bad), self.assertRaises(ValueError):
                validate_correction_plan(bad)

    def test_failure_requires_actual_matching_command_exit(self):
        failure = {'status': 'error', 'error_type': 'CommandError', 'details': {'exit_code': 1}}
        verify_correction_result(failure, 1)
        verify_correction_result({'status': 'ok', 'exit_code': 0}, 0)
        for bad in ({**failure, 'error_type': 'TimeoutError'},
                    {**failure, 'details': {'exit_code': True}},
                    {**failure, 'details': {'exit_code': 2}}, {'status': 'ok', 'exit_code': 1}):
            with self.assertRaises(ValueError):
                verify_correction_result(bad, 1)
        with self.assertRaises(ValueError):
            verify_correction_result({'status': 'ok', 'exit_code': 0}, False)

    def test_patch_bindings_cannot_claim_original_teacher_export(self):
        plan = plan_fixture()
        replay = {'correction': plan, 'source_intended_patch': plan['source_patch'],
                  'patch': plan['corrected_patch'], 'intended_patch': plan['corrected_patch'],
                  'native_submission_equals_source_export': False,
                  'native_submission_equals_corrected_export': True}
        self.assertEqual(verify_correction_binding({'correction': plan}, replay), plan)
        for field, value in [('native_submission_equals_source_export', True),
                             ('patch', plan['source_patch']), ('correction', None)]:
            with self.assertRaises(ValueError):
                verify_correction_binding({'correction': plan}, {**replay, field: value})
        with self.assertRaises(ValueError):
            verify_correction_binding({}, replay)

    def test_history_preserves_failed_correction_and_separate_authorship(self):
        source = [{'role': 'assistant', 'content': '', 'tool_calls': [{
            'id': 'terminal', 'type': 'function', 'function': {'name': 'bash', 'arguments': {
                'command': 'echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && cat patch.txt'}}}]}]
        plan = plan_fixture()
        def event(name, arguments, result):
            return {'source_index': None, 'adapter_authored': True, 'name': name,
                    'arguments': arguments, 'result': result}
        events = [event('run_command', {'command': 'check'}, {
            'status': 'error', 'error_type': 'CommandError',
            'details': {'exit_code': 1, 'stdout': 'actual failure'}}),
            event('run_command', {'command': plan['commands'][1]['command']},
                  {'status': 'ok', 'exit_code': 0}),
            event('run_command', {'command': 'cleanup'}, {'status': 'ok'}),
            event('submit_patch', {}, {'status': 'ok'})]
        def project(value, correction=plan):
            return mini_replay_history(value, source_messages=source, system='system', problem='issue',
                                       allowed_tools={'run_command', 'submit_patch'}, correction_plan=correction)
        result = project(events)
        self.assertEqual([r.get('correction_index') for r in result['mapping']], [0, 1, None, None])
        self.assertEqual(result['mapping'][0]['author'], 'assistant')
        self.assertIn('actual failure', result['messages'][3]['content'])
        with self.assertRaises(ValueError):
            project(events, None)
        for field, value in [('source_index', 1), ('adapter_authored', False),
                             ('arguments', {'command': 'different'})]:
            bad = copy.deepcopy(events)
            bad[0][field] = value
            with self.assertRaises(ValueError):
                project(bad)


if __name__ == '__main__':
    unittest.main()
