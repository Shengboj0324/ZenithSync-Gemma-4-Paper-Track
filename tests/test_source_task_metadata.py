import json
import unittest

from zenithsync.source_task_metadata import match_trajectory, project_r2e_task


class SourceTaskMetadataTests(unittest.TestCase):
    def row(self):
        return {
            'repo_name': 'repo', 'commit_hash': 'b' * 40,
            'docker_image': 'publisher/repo_final:' + 'b' * 40,
            'parsed_commit_content': json.dumps({'old_commit_hash': 'a' * 40,
                'new_commit_hash': 'b' * 40, 'file_diffs': 'ORACLE_FIX'}),
            'execution_result_content': json.dumps({'repo_name': 'repo',
                'new_commit_hash': 'b' * 40, 'test_file_codes': 'ORACLE_TEST'}),
            'problem_statement': 'Repair behavior', 'prompt': 'ORACLE_PROMPT',
        }

    def test_projection_and_exact_join(self):
        task = project_r2e_task(self.row())
        self.assertEqual(task['base_commit'], 'a' * 40)
        self.assertNotIn('ORACLE', json.dumps(task))
        self.assertFalse(task['environment_verified'])
        self.assertTrue(match_trajectory(task, repo='owner/repo', instance_id='owner__repo-' + 'b' * 40))
        self.assertFalse(match_trajectory(task, repo='owner/repo', instance_id='other__repo-' + 'b' * 40))
        self.assertFalse(match_trajectory(task, repo='owner/repo', instance_id='owner__repo-' + 'a' * 40))

    def test_conflicting_identity(self):
        for field, value in [('commit_hash', 'a' * 40), ('docker_image', 'publisher/repo:latest')]:
            row = self.row()
            row[field] = value
            with self.assertRaises(ValueError):
                project_r2e_task(row)

    def test_duplicate_json_identity(self):
        row = self.row()
        row['parsed_commit_content'] = '{"old_commit_hash":"x","old_commit_hash":"y"}'
        with self.assertRaises(ValueError):
            project_r2e_task(row)

    def test_unresolved_first_parent_is_not_a_commit_hash(self):
        row = self.row()
        row['parsed_commit_content'] = json.dumps({'old_commit_hash': 'b' * 40 + '^',
                                                  'new_commit_hash': 'b' * 40})
        task = project_r2e_task(row)
        self.assertIsNone(task['base_commit'])
        self.assertEqual(task['base_ref'], 'b' * 40 + '^')
        row['parsed_commit_content'] = json.dumps({'old_commit_hash': 'b' * 40 + '^; malicious',
                                                  'new_commit_hash': 'b' * 40})
        with self.assertRaises(ValueError):
            project_r2e_task(row)


if __name__ == '__main__':
    unittest.main()
