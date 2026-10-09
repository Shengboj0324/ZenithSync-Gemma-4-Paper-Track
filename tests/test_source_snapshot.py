from pathlib import Path
import tempfile
import unittest

from zenithsync.source_snapshot import git, sanitize


class SourceSnapshotTests(unittest.TestCase):
    def fixture(self, root):
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


if __name__ == '__main__':
    unittest.main()
