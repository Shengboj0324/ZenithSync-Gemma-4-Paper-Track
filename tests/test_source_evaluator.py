from pathlib import Path
import tempfile
import unittest

from zenithsync.source_evaluator import compare_publisher_expectations


class SourceEvaluatorTests(unittest.TestCase):
    def evaluate(self, cases, expected):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'report.xml'
            path.write_text(f'<testsuite tests="{len(cases)}">' + ''.join(cases) + '</testsuite>')
            return compare_publisher_expectations(path, expected)

    def test_collision_requires_every_member_to_match(self):
        cases = ['<testcase classname="a.Test" name="method"/>',
                 '<testcase classname="b.Test" name="method"><failure/></testcase>']
        report = self.evaluate(cases, {'Test.method': 'PASSED'})
        self.assertFalse(report['all_cases_match_publisher_expectations'])
        self.assertEqual(len(report['collisions']['Test.method']), 2)
        self.assertEqual(report['disagreements'][0]['test'], 'b.Test::method')

    def test_expected_failure_is_not_silently_rewritten_as_pass(self):
        report = self.evaluate(['<testcase classname="a.Test" name="method"><failure/></testcase>'],
                               {'Test.method': 'FAILED'})
        self.assertTrue(report['all_cases_match_publisher_expectations'])

    def test_missing_and_unexpected_groups_reject(self):
        report = self.evaluate(['<testcase classname="a.Test" name="actual"/>'],
                               {'Test.expected': 'PASSED'})
        self.assertFalse(report['all_cases_match_publisher_expectations'])
        self.assertEqual(report['missing_groups'], ['Test.expected'])
        self.assertEqual(report['unexpected_groups'], ['Test.actual'])


if __name__ == '__main__':
    unittest.main()
