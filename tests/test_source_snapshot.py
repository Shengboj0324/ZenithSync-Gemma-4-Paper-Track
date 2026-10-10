from pathlib import Path
import tempfile
import unittest

from zenithsync.source_snapshot import git, is_relative_to, sanitize, tracked_snapshot


class SourceSnapshotTests(unittest.TestCase):
    def test_blob_hash_matches_git_for_binary_modes_and_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp).resolve()
            git(repo, '-c', 'init.templateDir=', 'init')
            contents = {'empty': b'', 'binary': bytes(range(256)),
                        'unicode': 'π\r\n雪\n'.encode(), 'run': b'#!/bin/sh\nexit 0\n'}
            for name, content in contents.items():
                (repo / name).write_bytes(content)
            (repo / 'run').chmod(0o755)
            (repo / 'link').symlink_to('unicode')
            git(repo, 'add', '--all')
            rows = tracked_snapshot(repo)
            self.assertEqual(len(rows), 5)
            for row in rows:
                content = b'unicode' if row['path'] == 'link' else contents[row['path']]
                expected = git(repo, 'hash-object', '--no-filters', '--stdin',
                               data=content).stdout.strip().decode()
                self.assertEqual(row['blob'], expected)
            (repo / 'binary').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'differs from tracked Git blob'):
                tracked_snapshot(repo)

    def test_containment_uses_components_not_string_prefixes(self):
        self.assertTrue(is_relative_to(Path('/repo/child'), Path('/repo')))
        self.assertTrue(is_relative_to(Path('/repo'), Path('/repo')))
        self.assertFalse(is_relative_to(Path('/repo-other/child'), Path('/repo')))
        self.assertFalse(is_relative_to(Path('/other/repo'), Path('/repo')))
        self.assertFalse(is_relative_to(Path('repo/child'), Path('/repo')))

    def fixture(self, root):
        root = root.resolve()
        repo = root / 'repo'
        repo.mkdir()
        git(repo, '-c', 'init.templateDir=', 'init')
        (repo / 'module.py').write_text('value = 1\n')
        git(repo, 'add', 'module.py')
        git(repo, 'commit', '-m', 'base')
        base = git(repo, 'rev-parse', 'HEAD').stdout.strip().decode()
        (repo / 'module.py').write_text('value = 2\n')
        git(repo, 'add', 'module.py')
        git(repo, 'commit', '-m', 'solution')
        solution = git(repo, 'rev-parse', 'HEAD').stdout.strip().decode()
        git(repo, 'checkout', base)
        oracle = root / 'grading'
        oracle.mkdir()
        (oracle / 'test.py').write_text('reference test')
        return repo, base, solution, oracle

    def test_exact_tree_and_solution_unreachability(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, base, solution, oracle = self.fixture(Path(tmp))
            receipt = sanitize(repo, expected_base=base, solution=solution, oracle_paths=[oracle])
            self.assertTrue(receipt['exact_tree_preserved'])
            self.assertEqual((repo / 'module.py').read_text(), 'value = 1\n')
            self.assertFalse(oracle.exists())
            self.assertNotEqual(git(repo, 'cat-file', '-e', solution, check=False).returncode, 0)
            self.assertEqual(git(repo, 'rev-list', '--all', '--count').stdout.strip(), b'1')

    def test_wrong_base_and_modified_source_fail_before_deletion(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, base, solution, oracle = self.fixture(Path(tmp))
            with self.assertRaises(ValueError):
                sanitize(repo, expected_base=solution, solution=solution, oracle_paths=[oracle])
            (repo / 'module.py').write_text('changed')
            with self.assertRaises(ValueError):
                sanitize(repo, expected_base=base, solution=solution, oracle_paths=[oracle])
            self.assertTrue(oracle.exists())
            self.assertEqual(git(repo, 'cat-file', '-e', solution).returncode, 0)

    def test_tracked_oracle_overlap_fails_before_deletion(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, base, solution, oracle = self.fixture(Path(tmp))
            with self.assertRaises(ValueError):
                sanitize(repo, expected_base=base, solution=solution,
                         oracle_paths=[oracle, repo / 'module.py'])
            self.assertTrue(oracle.exists())
            self.assertEqual(git(repo, 'cat-file', '-e', solution).returncode, 0)


    def test_explicit_ancestor_mode_preserves_r2e_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, base, intermediate, oracle = self.fixture(Path(tmp))
            git(repo, 'checkout', intermediate)
            (repo / 'module.py').write_text('value = 3\n')
            git(repo, 'add', 'module.py')
            git(repo, 'commit', '-m', 'second PR commit')
            solution = git(repo, 'rev-parse', 'HEAD').stdout.strip().decode()
            git(repo, 'checkout', base)
            with self.assertRaisesRegex(ValueError, 'first parent'):
                sanitize(repo, expected_base=base, solution=solution, oracle_paths=[oracle])
            self.assertTrue(oracle.exists())
            receipt = sanitize(repo, expected_base=base, solution=solution,
                               oracle_paths=[oracle], solution_relation='ancestor')
            self.assertEqual(receipt['solution_relation'], 'ancestor')
            self.assertEqual((repo / 'module.py').read_text(), 'value = 1\n')
            for commit in (base, intermediate, solution):
                self.assertNotEqual(git(repo, 'cat-file', '-e', commit, check=False).returncode, 0)

    def test_invalid_ancestry_fails_before_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, base, solution, oracle = self.fixture(Path(tmp))
            git(repo, 'checkout', solution)
            with self.assertRaisesRegex(ValueError, 'not an ancestor'):
                sanitize(repo, expected_base=solution, solution=base,
                         oracle_paths=[oracle], solution_relation='ancestor')
            self.assertTrue(oracle.exists())
            self.assertEqual(git(repo, 'cat-file', '-e', base).returncode, 0)

    def test_already_absent_mode_is_explicit_and_never_claims_ancestry(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, base, present, oracle = self.fixture(Path(tmp))
            with self.assertRaisesRegex(ValueError, 'verifiably absent'):
                sanitize(repo, expected_base=base, solution=present,
                         oracle_paths=[oracle], solution_relation='already_absent')
            self.assertTrue(oracle.exists())
            absent = 'f' * 40
            with self.assertRaises(ValueError):
                sanitize(repo, expected_base=base, solution=absent,
                         oracle_paths=[oracle], solution_relation='ancestor')
            result = sanitize(repo, expected_base=base, solution=absent,
                              oracle_paths=[oracle], solution_relation='already_absent')
            self.assertFalse(result['solution_ancestry_verified'])
            self.assertTrue(result['exact_tree_preserved'])
            self.assertEqual((repo / 'module.py').read_text(), 'value = 1\n')
            self.assertNotEqual(git(repo, 'cat-file', '-e', present, check=False).returncode, 0)


if __name__ == '__main__':
    unittest.main()
