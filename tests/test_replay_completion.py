import copy
import unittest

from zenithsync.replay_completion import completed_replay_history, validate_completion_plan


class CompletionReplayTests(unittest.TestCase):
    def fixture(self):
        plan = {'schema_version': 1, 'author': 'assistant', 'reason': 'Correct verification',
                'source_actions': {'sha256': 'a' * 64, 'size_bytes': 20},
                'final_patch': {'sha256': 'b' * 64, 'size_bytes': 30},
                'commands': [{'command': 'check_bad', 'expected_exit_code': 1},
                             {'command': 'check_fixed', 'expected_exit_code': 0}]}
        def event(index, kind, name, arguments, result, **extra):
            return {'source_index': index, 'kind': kind, 'result': result,
                    'native_calls': [{'name': name, 'arguments': arguments, 'result': result}], **extra}
        events = [event(4, 'shell', 'run_command', {'command': 'source'},
                        {'status': 'ok', 'exit_code': 0})]
        for row in plan['commands']:
            result = ({'status': 'error', 'error_type': 'CommandError', 'details': {'exit_code': 1}}
                      if row['expected_exit_code'] else {'status': 'ok', 'exit_code': 0})
            events.append(event(None, 'completion', 'run_command', {'command': row['command']},
                                result, adapter_authored=True))
        events.append(event(8, 'finish', 'submit_patch', {}, {'status': 'ok'}))
        return plan, events

    def project(self, plan, events):
        return completed_replay_history(events, plan=plan, system='system', problem='issue',
                                        allowed_tools={'run_command', 'submit_patch'})

    def test_expected_failure_preserved_and_authorship_explicit(self):
        plan, events = self.fixture()
        result = self.project(plan, events)
        self.assertEqual([m['source_index'] for m in result['mapping']], [4, None, None, 8])
        self.assertEqual([m['adapter_authored'] for m in result['mapping']], [False, True, True, False])
        self.assertIn('CommandError', result['messages'][5]['content'])
        self.assertFalse(result['training_approved'])

    def test_invalid_plans_rejected(self):
        original, _ = self.fixture()
        variants = []
        for key, value in [('author', 'teacher'), ('schema_version', True), ('commands', [])]:
            plan = copy.deepcopy(original); plan[key] = value; variants.append(plan)
        plan = copy.deepcopy(original); plan['final_patch']['size_bytes'] = True; variants.append(plan)
        plan = copy.deepcopy(original); plan['commands'][-1]['expected_exit_code'] = 1; variants.append(plan)
        for plan in variants:
            with self.assertRaises(ValueError):
                validate_completion_plan(plan)

    def test_forged_or_missing_completion_observations_rejected(self):
        plan, original = self.fixture()
        variants = []
        for key, value in [('source_index', 6), ('adapter_authored', False), ('kind', 'shell')]:
            events = copy.deepcopy(original); events[1][key] = value; variants.append(events)
        events = copy.deepcopy(original)
        events[1]['result']['error_type'] = 'TimeoutError'; variants.append(events)
        events = copy.deepcopy(original)
        events[2]['native_calls'][0]['arguments']['command'] = 'unreviewed'; variants.append(events)
        variants.append(original[:1] + original[2:])
        variants.append(original[:1] + list(reversed(original[1:3])) + original[3:])
        for events in variants:
            with self.assertRaises(ValueError):
                self.project(plan, events)

    def test_source_order_and_submission_arguments_checked(self):
        plan, events = self.fixture()
        events[-1]['source_index'] = 3
        with self.assertRaises(ValueError):
            self.project(plan, events)
        plan, events = self.fixture()
        events[-1]['native_calls'][0]['arguments'] = {'fake': True}
        with self.assertRaises(ValueError):
            self.project(plan, events)
