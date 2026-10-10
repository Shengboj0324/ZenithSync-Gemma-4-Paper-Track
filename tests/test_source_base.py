from pathlib import Path
import tempfile
import unittest

from tests import test_source_snapshot
from zenithsync.source_base import normalize_base
from zenithsync.source_snapshot import git


class SourceBaseTests(unittest.TestCase):
    def fixture(self, path):
        repo, base, solution, _ = test_source_snapshot.SourceSnapshotTests().fixture(path)
        git(repo, 'checkout', solution)
        return repo, base, solution

    def test_exact_base_and_no_checkout_hook_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, base, head = self.fixture(Path(tmp))
            hook = repo/'.git/hooks/post-checkout'
            hook.parent.mkdir(exist_ok=True)
            hook.write_text('#!/bin/sh\ntouch hook-ran\n');hook.chmod(0o755)
            result = normalize_base(repo, expected_head=head, target_base=base)
            self.assertEqual(result['base_commit'], base)
            self.assertEqual((repo/'module.py').read_text(), 'value = 1\n')
            self.assertFalse((repo/'hook-ran').exists())
            self.assertFalse(result['agent_workspace_approved'])
            self.assertEqual(git(repo, 'cat-file', '-e', head).returncode, 0)

    def test_wrong_head_and_dirty_tree_rejected_before_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, base, head = self.fixture(Path(tmp))
            with self.assertRaisesRegex(ValueError, 'initial checkout'):
                normalize_base(repo, expected_head=base, target_base=base)
            (repo/'module.py').write_text('dirty\n')
            with self.assertRaisesRegex(ValueError, 'Tracked changes'):
                normalize_base(repo, expected_head=head, target_base=base)
            self.assertEqual(git(repo, 'rev-parse', 'HEAD').stdout.strip().decode(), head)
            self.assertEqual((repo/'module.py').read_text(), 'dirty\n')

    def test_untracked_file_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, base, head = self.fixture(Path(tmp))
            (repo/'untracked.txt').write_text('preserve')
            normalize_base(repo, expected_head=head, target_base=base)
            self.assertEqual((repo/'untracked.txt').read_text(), 'preserve')


if __name__ == '__main__':
    unittest.main()
