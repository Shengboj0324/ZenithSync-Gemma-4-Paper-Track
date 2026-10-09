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


class CorpusSelectionTests(unittest.TestCase):
    def row(self, **changes):
        return {'repo': 'owner/repo', 'instance_id': 'issue', 'trajectory_id': 'trace',
                'dataset': 'R2E-Gym/R2E-Gym-Subset', 'reserved_repository_exact_match': False, **changes}

    def test_reserved_exclusion_precedes_source_selection(self):
        from zenithsync.source_task_metadata import select_r2e_metadata
        selected, counts = select_r2e_metadata([
            self.row(),
            self.row(repo='ENCODE/HTTPX', trajectory_id='reserved',
                     reserved_repository_exact_match=True, dataset='other'),
            self.row(trajectory_id='unsupported', dataset='other'),
        ], reserved_repositories=['encode/httpx'])
        self.assertEqual(len(selected), 1)
        self.assertEqual(counts, {'input_rows': 3, 'selected_r2e_rows': 1,
            'excluded_reserved_rows': 1, 'other_source_rows_not_joined': 1})

    def test_forged_or_nonboolean_exclusion_flag_rejects(self):
        from zenithsync.source_task_metadata import select_r2e_metadata
        for row in [self.row(repo='encode/httpx'), self.row(reserved_repository_exact_match=0)]:
            with self.subTest(row=row), self.assertRaises(ValueError):
                select_r2e_metadata([row], reserved_repositories=['encode/httpx'])

    def test_duplicate_id_across_source_categories_rejects(self):
        from zenithsync.source_task_metadata import select_r2e_metadata
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            select_r2e_metadata([self.row(), self.row(dataset='other')], reserved_repositories=[])


class SwebenchIdentityTests(unittest.TestCase):
    def row(self, **changes):
        return {'repo': 'owner/repo', 'instance_id': 'owner__repo-12',
            'base_commit': 'a' * 40, 'environment_setup_commit': 'b' * 40,
            'docker_image': 'publisher/image:tag', 'image_name': 'publisher/image:tag',
            'license_name': 'MIT License', 'patch': 'ORACLE',
            'problem_statement': 'PRIVATE_ISSUE', **changes}

    def test_projection_excludes_oracles_and_preserves_distinct_commits(self):
        from zenithsync.source_task_metadata import project_swebench_task_identity
        result = project_swebench_task_identity(self.row())
        self.assertNotIn('ORACLE', json.dumps(result))
        self.assertNotIn('PRIVATE_ISSUE', json.dumps(result))
        self.assertNotEqual(result['base_commit'], result['environment_setup_commit'])
        self.assertFalse(result['training_approved'])
        self.assertFalse(result['environment_verified'])

    def test_missing_declarations_are_not_invented(self):
        from zenithsync.source_task_metadata import project_swebench_task_identity
        result = project_swebench_task_identity(self.row(license_name=None, docker_image=None, image_name=None))
        self.assertIsNone(result['publisher_license_declaration'])
        self.assertIsNone(result['source_image_reference'])

    def test_inconsistent_id_images_and_commit_rejected(self):
        from zenithsync.source_task_metadata import project_swebench_task_identity
        for changes in [{'instance_id': 'another__repo-12'},
                        {'image_name': 'different/image'}, {'base_commit': 'main'},
                        {'docker_image': 'image; command'}]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                project_swebench_task_identity(self.row(**changes))

    def test_source_filter_does_not_assume_r2e(self):
        from zenithsync.source_task_metadata import select_source_metadata
        rows = [{'repo': 'owner/repo', 'instance_id': 'owner__repo-12', 'trajectory_id': 'id',
                 'dataset': 'nebius/SWE-rebench', 'reserved_repository_exact_match': False}]
        selected, counts = select_source_metadata(rows, reserved_repositories=[], source_dataset='nebius/SWE-rebench')
        self.assertEqual(len(selected), 1)
        self.assertEqual(counts['selected_source_rows'], 1)


if __name__ == '__main__':
    unittest.main()
