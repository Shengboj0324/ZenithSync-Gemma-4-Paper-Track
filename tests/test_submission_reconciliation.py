from pathlib import Path
import subprocess
import tempfile
import unittest
import sys

from zenithsync.submission_reconciliation import plan_scratch_cleanup, scratch_cleanup_command


class SubmissionReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.git('init', '-q')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'commit.gpgsign', 'false')
        (self.root / 'source.py').write_text('value = 1\n')
        self.git('add', 'source.py')
        self.git('commit', '-qm', 'baseline')
        self.baseline = self.git('rev-parse', 'HEAD').decode().strip()
        (self.root / 'source.py').write_text('value = 2\n')
        self.patch = self.git('diff', '--binary', self.baseline, '--')
        (self.root / 'patch.txt').write_bytes(self.patch)

    def git(self, *arguments):
        return subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', '-C',
            str(self.root), *arguments], check=True, capture_output=True, timeout=15).stdout

    def plan(self, paths=None, patch=None):
        return plan_scratch_cleanup(self.root, baseline=self.baseline,
            intended_patch=self.patch if patch is None else patch,
            scratch_paths=['patch.txt'] if paths is None else paths)

    def test_native_submission_difference_and_explicit_cleanup_equivalence(self):
        plan = self.plan()
        self.assertFalse(plan['cleanup_performed'])
        self.assertTrue((self.root / 'patch.txt').exists())
        self.git('add', '-N', '.')
        native_before = self.git('diff', '--binary', self.baseline, '--')
        self.assertNotEqual(native_before, self.patch)
        self.assertIn(b'diff --git a/patch.txt b/patch.txt', native_before)
        self.git('reset', '-q')
        # Explicit mutation only in this disposable fixture, not in the planner.
        (self.root / 'patch.txt').unlink()
        self.git('add', '-N', '.')
        self.assertEqual(self.git('diff', '--binary', self.baseline, '--'), self.patch)

    def test_no_silent_dropping_of_unknown_or_tracked_changes(self):
        (self.root / 'extra.py').write_text('extra = 1\n')
        with self.assertRaisesRegex(ValueError, 'Untracked files differ'):
            self.plan()
        (self.root / 'extra.py').unlink()
        (self.root / 'source.py').write_text('value = 3\n')
        with self.assertRaisesRegex(ValueError, 'Tracked repair differs'):
            self.plan()
        self.assertTrue((self.root / 'patch.txt').exists())

    def test_staged_edits_and_wrong_patch_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Tracked repair differs'):
            self.plan(patch=self.patch + b'\n')
        self.git('add', 'source.py')
        with self.assertRaisesRegex(ValueError, 'Staged changes'):
            self.plan()

    def test_traversal_duplicates_and_symlinks_rejected(self):
        for paths in (['../patch.txt'], ['/tmp/patch.txt'], ['patch.txt', 'patch.txt'],
                      ['a/../patch.txt'], ['.git/config']):
            with self.subTest(paths=paths), self.assertRaises(ValueError):
                self.plan(paths=paths)
        (self.root / 'patch.txt').unlink()
        (self.root / 'patch.txt').symlink_to(self.root / 'source.py')
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            self.plan()

    def test_standalone_action_preserves_patch_without_installed_project(self):
        self.git('tag', '_swegemma_baseline')
        command = scratch_cleanup_command(python=sys.executable,
            scratch_paths=['patch.txt'], repository=str(self.root))
        result = subprocess.run(command, shell=True, cwd=self.root,
                                capture_output=True, text=True, timeout=30,
                                env={'PATH': '/usr/bin:/bin'})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.root / 'patch.txt').exists())
        self.assertEqual(self.git('diff', '--binary', self.baseline, '--'), self.patch)

    def test_standalone_action_rejects_unknown_file_before_deleting(self):
        self.git('tag', '_swegemma_baseline')
        (self.root / 'unknown.txt').write_text('preserve me')
        command = scratch_cleanup_command(python=sys.executable,
            scratch_paths=['patch.txt'], repository=str(self.root))
        result = subprocess.run(command, shell=True, cwd=self.root,
                                capture_output=True, text=True, timeout=30)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue((self.root / 'patch.txt').exists())
        self.assertEqual((self.root / 'unknown.txt').read_text(), 'preserve me')


if __name__ == '__main__':
    unittest.main()
