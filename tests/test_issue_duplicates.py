import unittest
from scripts.audit_issue_duplicates import fingerprint_issues


class IssueDuplicateTests(unittest.TestCase):
    def row(self, task, body):
        return {'instance_id':task, 'repo':'owner/repo', 'problem_statement':body}

    def test_whitespace_match_is_not_exact_equality(self):
        rows, groups = fingerprint_issues([self.row('a','x = 1\n'), self.row('b','x  = 1')])
        self.assertFalse(groups['exact_sha256'])
        self.assertEqual(groups['whitespace_sha256'][0]['tasks'], ['a','b'])
        self.assertNotEqual(rows[0]['exact_sha256'], rows[1]['exact_sha256'])

    def test_case_and_unicode_are_not_silently_normalized(self):
        _, groups = fingerprint_issues([self.row('a','X'), self.row('b','x'),
                                       self.row('c','é'), self.row('d','e\u0301')])
        self.assertFalse(groups['exact_sha256'])
        self.assertFalse(groups['whitespace_sha256'])

    def test_exact_match_and_order_independence(self):
        rows = [self.row('z','same issue'),self.row('a','same issue')]
        self.assertEqual(fingerprint_issues(rows), fingerprint_issues(rows[::-1]))
        self.assertEqual(fingerprint_issues(rows)[1]['exact_sha256'][0]['tasks'], ['a','z'])

    def test_duplicate_identity_and_empty_issue_rejected(self):
        for rows in ([self.row('a','x'),self.row('a','y')], [self.row('a',' \n')]):
            with self.assertRaises(ValueError):fingerprint_issues(rows)


if __name__ == '__main__':
    unittest.main()
