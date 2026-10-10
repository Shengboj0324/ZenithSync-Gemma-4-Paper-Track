"""Candidate source allowance rejects path ambiguity before container execution."""
import unittest
from scripts.grade_rebench_replay import source_allowlist


class ReplaySourceAllowlistTests(unittest.TestCase):
    def test_explicit_source_files(self):
        paths=['nodebook/nodebookcore.py','nodebook/utils.py']
        self.assertEqual(source_allowlist(paths), paths)

    def test_rejects_ambiguous_or_metadata_paths(self):
        for paths in ([], ['a','a'], [''], ['.'], ['/tmp/a'], ['../a'], ['a/../b'],
                      ['a//b'], ['a/./b'], ['.git/config'], ['a/.git/b'], ['a\x00b']):
            with self.subTest(paths=paths), self.assertRaises(ValueError):
                source_allowlist(paths)


if __name__=='__main__':
    unittest.main()
