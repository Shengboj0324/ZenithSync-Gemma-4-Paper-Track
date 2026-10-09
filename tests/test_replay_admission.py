import json
from pathlib import Path
import tempfile
import unittest

from zenithsync.artifacts import canonical_json, file_record
from zenithsync.replay_admission import assess_replay_bundle
from zenithsync.replay_history import native_replay_history


class ReplayAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ('attempt', 'history', 'grade', 'tokens'):
            (self.root / name).mkdir()
        self.write('attempt/submitted.patch', 'fixture patch')
        events = []
        for index, name in enumerate(('read_file', 'submit_patch')):
            result = {'status': 'ok'}
            events.append({'source_index': index, 'kind': 'view' if index == 0 else 'finish',
                'result': result, 'native_calls': [{'name': name, 'arguments': {}, 'result': result}]})
        self.write('attempt/events.json', events)
        self.write('attempt/receipt.json', {'patch': self.record('attempt/submitted.patch'),
            'status': 'replayed_not_graded', 'cleanup': {'removed': True},
            'available_tools': ['read_file', 'submit_patch'], 'tool_calls': 1,
            'instance_id': 'fixture', 'trajectory_id': 'fixture'})
        projected = native_replay_history(events, system='system', problem='issue',
                                          allowed_tools={'read_file', 'submit_patch'})
        self.write('history/history.json', projected['messages'])
        self.write('history/mapping.json', projected['mapping'])
        self.write('history/tools.json', [{'function': {'name': name}} for name in ('read_file', 'submit_patch')])
        self.write('history/receipt.json', {'attempt': self.record('attempt/receipt.json'),
            'events': self.record('attempt/events.json'), 'history': self.record('history/history.json'),
            'tools': self.record('history/tools.json'), 'exchanges': 2})
        self.write('grade/report.json', {'attempt': self.record('attempt/receipt.json'),
            'patch': self.record('attempt/submitted.patch'), 'grading': {
                'all_cases_match_publisher_expectations': True, 'case_count': 1,
                'disagreements': [], 'missing_groups': [], 'unexpected_groups': []}})
        self.write('tokens/report.json', {'history': self.record('history/history.json'),
            'tools': self.record('history/tools.json'), 'input_tokens': 10,
            'supervised_tokens': 3, 'truncated': False})

    def write(self, name, value):
        (self.root / name).write_bytes(value.encode() if isinstance(value, str) else canonical_json(value))

    def record(self, name):
        return file_record(self.root / name)

    def assess(self, **kwargs):
        policy = dict(max_input_tokens=20, output_reserve=10, max_tool_calls=1)
        policy.update(kwargs)
        return assess_replay_bundle(**{name: self.root / name for name in ('attempt', 'history', 'grade', 'tokens')}, **policy)

    def test_exact_boundary_never_approves_training(self):
        result = self.assess()
        self.assertTrue(result['mechanical_checks_passed'])
        self.assertFalse(result['training_approved'])
        self.assertEqual(result['native_tool_calls'], 1)

    def test_reserve_overflow_blocks_without_truncation(self):
        result = self.assess(output_reserve=11)
        self.assertEqual(result['mechanical_blockers'], ['input_plus_output_reserve_exceeds_context'])

    def test_changed_patch_and_mapping_rejected(self):
        self.write('attempt/submitted.patch', 'changed')
        with self.assertRaisesRegex(ValueError, 'patch identity'):
            self.assess()
        self.write('attempt/submitted.patch', 'fixture patch')
        self.write('history/mapping.json', [])
        with self.assertRaisesRegex(ValueError, 'captured native'):
            self.assess()

    def test_contradictory_grading_and_boolean_counts_rejected(self):
        path = self.root / 'grade/report.json'
        report = json.loads(path.read_text())
        report['grading']['missing_groups'] = ['test_missing']
        self.write('grade/report.json', report)
        with self.assertRaisesRegex(ValueError, 'Contradictory'):
            self.assess()
        report['grading']['missing_groups'] = []
        self.write('grade/report.json', report)
        token = json.loads((self.root / 'tokens/report.json').read_text())
        token['supervised_tokens'] = True
        self.write('tokens/report.json', token)
        with self.assertRaisesRegex(ValueError, 'token counts'):
            self.assess()


if __name__ == '__main__':
    unittest.main()
