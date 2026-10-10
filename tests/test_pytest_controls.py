import copy
import unittest

from zenithsync.pytest_controls import call_outcomes, compare_controls, compare_candidate


def observation(outcomes):
    return {'collected': list(outcomes), 'collection_errors': [],
            'exitstatus': int('failed' in outcomes.values()),
            'reports': [{'nodeid': node, 'when': phase,
                         'outcome': outcome if phase == 'call' else 'passed'}
                        for node, outcome in outcomes.items()
                        for phase in ('setup', 'call', 'teardown')]}


class PairedControlTests(unittest.TestCase):
    def setUp(self):
        self.base = observation({'test[x one]': 'passed', 'test[x two]': 'passed', 'repair': 'failed'})
        self.reference = observation({'test[x one]': 'passed', 'test[x two]': 'passed', 'repair': 'passed'})
        self.expected = {'PASS_TO_PASS': ['test[x'], 'FAIL_TO_PASS': ['repair'],
                         'PASS_TO_FAIL': [], 'FAIL_TO_FAIL': []}

    def test_collision_members_all_retained(self):
        result = compare_controls(self.base, self.reference, self.expected)
        self.assertEqual(result['full_test_count'], 3)
        self.assertEqual(result['collision_groups'], {'test[x': ['test[x one]', 'test[x two]']})

    def test_one_hidden_member_failure_rejected(self):
        altered = observation({'test[x one]': 'failed', 'test[x two]': 'passed', 'repair': 'passed'})
        with self.assertRaises(ValueError):
            compare_controls(self.base, altered, self.expected)

    def test_missing_and_duplicate_phases_rejected(self):
        for reports in (self.base['reports'][:-1], self.base['reports'] + self.base['reports'][:1]):
            with self.subTest(reports=len(reports)), self.assertRaises(ValueError):
                call_outcomes({**self.base, 'reports': reports})

    def test_setup_error_skip_and_exit_contradiction_rejected(self):
        for phase, outcome in (('setup', 'failed'), ('call', 'skipped'), ('teardown', 'failed')):
            altered = copy.deepcopy(self.base)
            next(r for r in altered['reports'] if r['when'] == phase)['outcome'] = outcome
            with self.subTest(phase=phase), self.assertRaises(ValueError):
                call_outcomes(altered)
        for status in (0, True, 2):
            with self.subTest(status=status), self.assertRaises(ValueError):
                call_outcomes({**self.base, 'exitstatus': status})

    def test_coverage_and_conflicting_expectations_rejected(self):
        for expected in ({**self.expected, 'PASS_TO_PASS': []},
                         {**self.expected, 'FAIL_TO_FAIL': ['repair']}):
            with self.assertRaises(ValueError):
                compare_controls(self.base, self.reference, expected)
        with self.assertRaises(ValueError):
            compare_controls(self.base, observation({'repair': 'passed'}), self.expected)

    def test_candidate_failure_is_a_disagreement_not_runtime_error(self):
        result = compare_candidate(self.reference, self.base)
        self.assertFalse(result['all_cases_match_reference'])
        self.assertEqual(result['disagreements'], [
            {'nodeid': 'repair', 'expected': 'passed', 'actual': 'failed'}])
        self.assertTrue(compare_candidate(self.reference, self.reference)['all_cases_match_reference'])

    def test_candidate_missing_test_is_not_a_partial_score(self):
        with self.assertRaises(ValueError):
            compare_candidate(self.reference, observation({'repair': 'passed'}))

    def test_explicit_extra_regression_preserves_publisher_coverage(self):
        base = observation({'repair': 'failed', 'backend': 'passed'})
        reference = observation({'repair': 'passed', 'backend': 'passed'})
        expected = {'FAIL_TO_PASS': ['repair'], 'PASS_TO_PASS': [],
                    'FAIL_TO_FAIL': [], 'PASS_TO_FAIL': []}
        result = compare_controls(base, reference, expected,
                                  supplemental_pass_to_pass=['backend'])
        self.assertEqual(result['full_test_count'], 2)
        self.assertEqual(result['publisher_key_count'], 1)
        self.assertEqual(result['supplemental_pass_to_pass'], ['backend'])
        for extras in ([], ['missing'], ['repair'], ['backend', 'backend'], 'backend'):
            with self.subTest(extras=extras), self.assertRaises(ValueError):
                compare_controls(base, reference, expected, supplemental_pass_to_pass=extras)
        for role in ('base', 'reference'):
            failed = observation({'repair': 'failed' if role == 'base' else 'passed',
                                  'backend': 'failed'})
            with self.subTest(role=role), self.assertRaises(ValueError):
                compare_controls(failed if role == 'base' else base,
                                 failed if role == 'reference' else reference, expected,
                                 supplemental_pass_to_pass=['backend'])

    def test_supplemental_declaration_cannot_hide_parameter_groups(self):
        expected = {'FAIL_TO_PASS': [], 'PASS_TO_PASS': [],
                    'FAIL_TO_FAIL': [], 'PASS_TO_FAIL': []}
        cases = observation({'backend[x one]': 'passed', 'backend[x two]': 'passed'})
        with self.assertRaises(ValueError):
            compare_controls(cases, cases, expected, supplemental_pass_to_pass=['backend[x'])
