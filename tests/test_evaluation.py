import tempfile
import unittest
from pathlib import Path

from zenithsync.evaluation import compare_junit, junit_outcomes


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def report(self, filename, contents):
        path = self.root / filename
        path.write_text(contents)
        return path

    def test_preserves_failure_error_and_skip_transitions(self):
        before = self.report('before.xml', '''<testsuite tests="3">
          <testcase classname="C" name="a"><failure/></testcase>
          <testcase classname="C" name="b"><error/></testcase>
          <testcase classname="C" name="c"><skipped/></testcase>
        </testsuite>''')
        after = self.report('after.xml', '''<testsuite tests="3">
          <testcase classname="C" name="c"><skipped/></testcase>
          <testcase classname="C" name="a"/>
          <testcase classname="C" name="b"><failure/></testcase>
        </testsuite>''')
        result = compare_junit(before, after)
        self.assertEqual(result['baseline_counts'], {'failed': 1, 'error': 1, 'skipped': 1})
        self.assertEqual(result['candidate_counts'], {'failed': 1, 'passed': 1, 'skipped': 1})
        self.assertEqual(result['changed_cases'], [
            {'test': 'C::a', 'baseline': 'failed', 'candidate': 'passed'},
            {'test': 'C::b', 'baseline': 'error', 'candidate': 'failed'}])

    def test_rejects_missing_or_ambiguous_evidence(self):
        fixtures = [
            '<testsuite tests="0"/>',
            '<testsuite tests="2"><testcase classname="C" name="a"/></testsuite>',
            '<testsuite tests="1"><testcase name="a"/></testsuite>',
            '<testsuite tests="2"><testcase classname="C" name="a"/><testcase classname="C" name="a"/></testsuite>',
            '<testsuite tests="1"><testcase classname="C" name="a"><failure/><skipped/></testcase></testsuite>',
        ]
        for index, content in enumerate(fixtures):
            with self.subTest(index=index), self.assertRaises(ValueError):
                junit_outcomes(self.report(str(index) + '.xml', content))

    def test_does_not_compare_different_test_sets(self):
        before = self.report('before.xml', '<testsuite tests="1"><testcase classname="C" name="a"/></testsuite>')
        after = self.report('after.xml', '<testsuite tests="1"><testcase classname="C" name="b"/></testsuite>')
        with self.assertRaisesRegex(ValueError, 'Unpaired'):
            compare_junit(before, after)


if __name__ == '__main__':
    unittest.main()
