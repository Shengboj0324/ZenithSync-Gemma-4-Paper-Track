import unittest

from zenithsync.source_task import project_source_issue


class SourceTaskTests(unittest.TestCase):
    def project(self, text):
        return project_source_issue(problem_statement=text, repo='owner/repo',
            source_instance_id='owner__repo-' + 'a' * 40,
            source_revision='b' * 40, snapshot_commit='c' * 40)

    def test_explicit_projection_and_opaque_identity(self):
        task = self.project('[ISSUE]\nFix the described behavior.\n[/ISSUE]')
        self.assertEqual(set(task), {'instance_id', 'repo', 'base_commit', 'problem_statement'})
        self.assertEqual(task['problem_statement'], 'Fix the described behavior.')
        self.assertNotIn('a' * 40, task['instance_id'])
        self.assertEqual(task['base_commit'], 'c' * 40)

    def test_ambiguous_wrappers_reject_instead_of_discarding_content(self):
        for text in ['[ISSUE]one[/ISSUE][ISSUE]two[/ISSUE]',
                     'additional text[ISSUE]one[/ISSUE]', '[ISSUE][/ISSUE]']:
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.project(text)


if __name__ == '__main__':
    unittest.main()
