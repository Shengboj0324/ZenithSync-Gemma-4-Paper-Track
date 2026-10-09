import unittest

from scripts.audit_source_expectation_corpus import summarize_contract


class ExpectationCorpusTests(unittest.TestCase):
    def test_duplicate_keys_are_rejected_even_when_values_agree(self):
        self.assertFalse(summarize_contract('{"a":"PASSED","a":"PASSED"}')['valid'])

    def test_invalid_contracts_do_not_gain_acceptance(self):
        for raw in ('null', '{}', '[]', '{"a":true}', '{"a":"UNKNOWN"}', '{" ":"PASSED"}', None):
            with self.subTest(raw=raw):
                self.assertFalse(summarize_contract(raw)['valid'])

    def test_expected_failure_is_retained_and_no_test_names_exported(self):
        result = summarize_contract('{"secret_test":"FAILED","b":"PASSED"}')
        self.assertTrue(result['valid'])
        self.assertFalse(result['all_passed_contract'])
        self.assertEqual(result['status_counts'], {'FAILED': 1, 'PASSED': 1})
        self.assertNotIn('secret_test', str(result))

    def test_failure_only_contract_is_explicit(self):
        result = summarize_contract('{"a":"ERROR"}')
        self.assertTrue(result['valid'])
        self.assertFalse(result['has_passed_expectation'])


if __name__ == '__main__':
    unittest.main()
