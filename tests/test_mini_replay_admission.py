"""Disposable synthetic evidence exercises consistency checks, not model quality."""
import hashlib
from pathlib import Path
import tempfile
import unittest

from zenithsync.artifacts import canonical_json, file_record, load_json
from zenithsync.mini_replay_admission import assess_mini_replay_bundle
from zenithsync.pytest_controls import compare_candidate, compare_controls
from zenithsync.replay_history import mini_replay_history
from zenithsync.submission_reconciliation import scratch_cleanup_command


class MiniAdmissionTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.args = dict(root=self.root, attempt=Path('attempt'), history=Path('history'),
                         grade=Path('grade'), tokens=Path('tokens'), candidate=Path('candidate.json'),
                         profile=Path('profile.json'), task=Path('task.json'))
        task = {'repo': 'fixture/example', 'instance_id': 'fixture__example-1',
                'base_commit': 'a' * 40, 'problem_statement': 'Fixture issue',
                'FAIL_TO_PASS': ['test.py::test_fix'], 'PASS_TO_PASS': []}
        self.write('task.json', task)
        source = [{'role': 'user', 'content': 'issue'}]
        for index, command in enumerate(('git diff',
                'echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && cat patch.txt')):
            source.append({'role': 'assistant', 'content': '', 'tool_calls': [
                {'id': str(index), 'type': 'function', 'function': {
                    'name': 'bash', 'arguments': {'command': command}}}]})
            if index == 0:
                source.append({'role': 'tool', 'tool_call_id': str(index), 'content': 'old'})
        metadata = {key: task[key] for key in ('repo', 'instance_id', 'base_commit')}
        self.write('candidate.json', {'task_metadata': metadata, 'messages': source,
                                     'source_metadata': {'trajectory_id': 'fixture'}})
        profile = {'python': '/usr/bin/python3', 'scratch_paths': ['patch.txt']}
        self.write('profile.json', profile)
        events = [
            {'source_index': 1, 'adapter_authored': False, 'name': 'run_command',
             'arguments': {'command': 'git diff'}, 'result': {'status': 'ok', 'stdout': 'fresh'}},
            {'source_index': None, 'adapter_authored': True, 'name': 'run_command',
             'arguments': {'command': scratch_cleanup_command(**profile)}, 'result': {'status': 'ok'}},
            {'source_index': None, 'adapter_authored': True, 'name': 'submit_patch',
             'arguments': {}, 'result': {'status': 'ok'}}]
        self.write('attempt/events.json', events)
        self.write('attempt/submitted.patch', {'fixture': 'patch bytes are not executed'})
        self.write('attempt/intended.patch', {'fixture': 'patch bytes are not executed'})
        replay = {'status': 'replayed_not_graded', 'cleanup': {'removed': True},
            'standalone_cleanup': True, 'injected_support_modules': False,
            'source_observations_reused': False, 'task': metadata,
            'candidate': self.identity('candidate.json'), 'profile': self.identity('profile.json'),
            'patch': self.identity('attempt/submitted.patch'),
            'intended_patch': self.identity('attempt/intended.patch'),
            'native_submission_equals_source_export': True,
            'tool_calls': 2, 'image': 'fixture-image'}
        self.write('attempt/receipt.json', replay)
        names = {'run_command', 'submit_patch'} | {'fixture_tool_' + str(i) for i in range(7)}
        tools = [{'type': 'function', 'function': {'name': name}} for name in sorted(names)]
        result = mini_replay_history(events, source_messages=source, system='system',
                                    problem=task['problem_statement'], allowed_tools=names)
        for name, value in (('history', result['messages']), ('mapping', result['mapping']), ('tools', tools)):
            self.write('history/' + name + '.json', value)
        linked = {name: self.identity('history/' + name + '.json') for name in ('history', 'tools', 'mapping')}
        self.write('history/receipt.json', {**linked, 'attempt': self.identity('attempt/receipt.json'),
                                          'input_bindings': {}, 'exchanges': 3})
        controls, outcomes = {}, {}
        for role in ('base', 'reference', 'candidate'):
            execution = {'image_id': 'fixture-image', 'returncode': 0, 'cleanup_returncode': 0,
                         'copy_returncode': 0, 'state': {'OOMKilled': False}}
            controls[role] = execution
            self.write('grade/' + role + '/receipt.json', execution)
            self.write('grade/' + role + '/runtime.json', {'tracked_diff_unchanged_by_tests': True,
                'tests_started': True, 'pytest_exit': int(role == 'base')})
            outcomes[role] = {'collected': ['test.py::test_fix'], 'collection_errors': [],
                'exitstatus': int(role == 'base'), 'reports': [
                    {'nodeid': 'test.py::test_fix', 'when': phase,
                     'outcome': 'failed' if role == 'base' and phase == 'call' else 'passed'}
                    for phase in ('setup', 'call', 'teardown')]}
            self.write('grade/' + role + '/outcomes.json', outcomes[role])
        expected = {'FAIL_TO_PASS': task['FAIL_TO_PASS'], 'PASS_TO_PASS': [], 'FAIL_TO_FAIL': [], 'PASS_TO_FAIL': []}
        self.write('grade/report.json', {'sanitized_snapshot': True, 'controls': controls,
            'inputs': {name: self.identity(name) for name in ('attempt/receipt.json', 'attempt/submitted.patch', 'task.json')},
            'comparison': compare_controls(outcomes['base'], outcomes['reference'], expected),
            'candidate_comparison': compare_candidate(outcomes['reference'], outcomes['candidate'])})
        encoded = {'input_ids': [1, 2, 3, 4], 'labels': [-100, -100, 3, 4],
                   'pad_token_id': 0, 'vocab_size': 10, **{k: linked[k] for k in ('history', 'tools')}}
        self.write('tokens/tokens.json', encoded)
        self.write('tokens/report.json', {'input_bindings': {}, 'token_candidate': self.identity('tokens/tokens.json'),
            'input_tokens': 4, 'supervised_tokens': 2, 'truncated': False,
            **{k: linked[k] for k in ('history', 'tools')},
            'input_sha256': hashlib.sha256(canonical_json(encoded['input_ids'])).hexdigest(),
            'labels_sha256': hashlib.sha256(canonical_json(encoded['labels'])).hexdigest()})

    def write(self, name, value):
        target = self.root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(canonical_json(value))

    def identity(self, name):
        return file_record(self.root / name)

    def test_supplemental_controls_are_recomputed_from_bound_profile(self):
        node = 'test.py::test_backend'
        self.write('evaluator-profile.json', {'supplemental_pass_to_pass': [node]})
        outcomes = {}
        for role in ('base', 'reference', 'candidate'):
            filename = 'grade/' + role + '/outcomes.json'
            value = load_json(self.root / filename)
            value['collected'].append(node)
            value['reports'].extend({'nodeid': node, 'when': phase, 'outcome': 'passed'}
                                    for phase in ('setup', 'call', 'teardown'))
            self.write(filename, value)
            outcomes[role] = value
        grading = load_json(self.root / 'grade/report.json')
        grading['supplemental_profile'] = 'evaluator-profile.json'
        grading['inputs']['evaluator-profile.json'] = self.identity('evaluator-profile.json')
        expected = {'FAIL_TO_PASS': ['test.py::test_fix'], 'PASS_TO_PASS': [],
                    'FAIL_TO_FAIL': [], 'PASS_TO_FAIL': []}
        grading['comparison'] = compare_controls(outcomes['base'], outcomes['reference'],
                                                 expected, supplemental_pass_to_pass=[node])
        grading['candidate_comparison'] = compare_candidate(outcomes['reference'], outcomes['candidate'])
        self.write('grade/report.json', grading)
        self.assertTrue(assess_mini_replay_bundle(**self.args)['mechanical_checks_passed'])
        del grading['inputs']['evaluator-profile.json']
        self.write('grade/report.json', grading)
        with self.assertRaisesRegex(ValueError, 'bound evaluator profile'):
            assess_mini_replay_bundle(**self.args)

    def test_consistent_evidence_never_approves_training(self):
        report = assess_mini_replay_bundle(**self.args)
        self.assertTrue(report['mechanical_checks_passed'])
        self.assertFalse(report['training_approved'])
        self.assertEqual(report['supervised_tokens'], 2)

    def test_context_and_call_budget_failures_are_reported(self):
        report = assess_mini_replay_bundle(**self.args, max_input_tokens=5,
                                          output_reserve=2, max_tool_calls=1)
        self.assertFalse(report['mechanical_checks_passed'])
        self.assertEqual(set(report['mechanical_blockers']),
                         {'input_plus_output_reserve_exceeds_context', 'native_call_budget_exceeded'})

    def test_changed_patch_rejects(self):
        self.write('attempt/submitted.patch', {'fixture': 'changed'})
        with self.assertRaises(ValueError):
            assess_mini_replay_bundle(**self.args)

    def test_orphan_resource_claims_cannot_approve_portable_replay(self):
        for filename, key in (('history/receipt.json', 'resource_environment'),
                              ('grade/report.json', 'session_resources'),
                              ('grade/report.json', 'resource_profile')):
            original = load_json(self.root/filename)
            self.write(filename, {**original, key: {}})
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'Resource claims without'):
                assess_mini_replay_bundle(**self.args)
            self.write(filename, original)

    def test_historical_code_requires_explicit_exact_archive(self):
        original = 'scripts/qualifier.py'
        archive = 'artifacts/official/old-run/scripts/qualifier.py'
        self.write(original, {'code': 'old'})
        self.write(archive, {'code': 'old'})
        grading = load_json(self.root / 'grade/report.json')
        grading['inputs'][original] = self.identity(original)
        self.write('grade/report.json', grading)
        self.write(original, {'code': 'new'})
        with self.assertRaisesRegex(ValueError, 'Evidence identity mismatch'):
            assess_mini_replay_bundle(**self.args)
        report = assess_mini_replay_bundle(**self.args, historical_sources={original: archive})
        self.assertTrue(report['mechanical_checks_passed'])
        self.assertEqual(len(report['historical_sources']), 1)
        self.write(archive, {'code': 'wrong'})
        with self.assertRaisesRegex(ValueError, 'Evidence identity mismatch'):
            assess_mini_replay_bundle(**self.args, historical_sources={original: archive})

    def test_data_remapping_and_unused_code_mappings_reject(self):
        archive = 'artifacts/official/old-run/task.json'
        self.write(archive, load_json(self.root / 'task.json'))
        with self.assertRaisesRegex(ValueError, 'Only matching archived'):
            assess_mini_replay_bundle(**self.args, historical_sources={'task.json': archive})
        original = 'scripts/unused.py'
        archive = 'artifacts/official/old-run/scripts/unused.py'
        self.write(original, {}); self.write(archive, {})
        with self.assertRaisesRegex(ValueError, 'Unused historical'):
            assess_mini_replay_bundle(**self.args, historical_sources={original: archive})

    def test_summary_cannot_hide_actual_candidate_failure(self):
        outcomes = load_json(self.root / 'grade/candidate/outcomes.json')
        outcomes['reports'][1]['outcome'] = 'failed'
        outcomes['exitstatus'] = 1
        self.write('grade/candidate/outcomes.json', outcomes)
        self.write('grade/candidate/runtime.json', {'tracked_diff_unchanged_by_tests': True,
                                                  'tests_started': True, 'pytest_exit': 1})
        with self.assertRaisesRegex(ValueError, 'Grading summary'):
            assess_mini_replay_bundle(**self.args)

    def test_rehashed_arrays_still_must_match_audit_hashes(self):
        encoded = load_json(self.root / 'tokens/tokens.json')
        encoded['labels'][2] = -100
        self.write('tokens/tokens.json', encoded)
        audit = load_json(self.root / 'tokens/report.json')
        audit['token_candidate'] = self.identity('tokens/tokens.json')
        self.write('tokens/report.json', audit)
        with self.assertRaisesRegex(ValueError, 'Token array hash'):
            assess_mini_replay_bundle(**self.args)


if __name__ == '__main__':
    unittest.main()
