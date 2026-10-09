import importlib.util
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'candidates/p1-observation-memory/skills/source-observations/scripts/observe.py'
spec = importlib.util.spec_from_file_location('observation_skill', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SourceObservationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = Path(self.temp.name).resolve()
        self.root = self.store / 'repo'
        self.root.mkdir()
        self.file = self.root / 'source.py'
        self.file.write_bytes('α = 1\r\nresult = α\r\n'.encode())

    def capture(self):
        return module.snapshot(self.root, 'source.py', 1, 1, self.store)

    def test_exact_unicode_and_line_endings_without_repository_writes(self):
        record = self.capture()
        self.assertEqual(record['record']['excerpt'], 'α = 1\r\n')
        self.assertEqual(module.recall(self.root, record['handle'])['status'], 'current_source_match')
        self.assertEqual(list(self.root.iterdir()), [self.file])
        self.assertFalse(Path(record['handle']).is_relative_to(self.root))

    def test_changes_outside_excerpt_invalidate_and_hide_old_excerpt(self):
        record = self.capture()
        self.file.write_bytes('α = 1\r\nresult = 0\r\n'.encode())
        recalled = module.recall(self.root, record['handle'])
        self.assertEqual(recalled['status'], 'stale')
        self.assertNotIn('record', recalled)

    def test_corruption_and_workspace_mismatch_rejected(self):
        record = self.capture()
        with self.assertRaises(ValueError):
            module.recall(self.store, record['handle'])
        path = Path(record['handle'])
        path.write_bytes(path.read_bytes() + b' ')
        with self.assertRaises(ValueError):
            module.recall(self.root, record['handle'])

    def test_path_escape_symlink_and_invalid_range_rejected(self):
        (self.root / 'link').symlink_to(self.file)
        for path in ('../source.py', str(self.file), 'link', '.git/config'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                module.snapshot(self.root, path, 1, 1, self.store)
        for start, end in ((0, 1), (2, 1), (1, 3), (1, 101), (True, 1)):
            with self.subTest(start=start, end=end), self.assertRaises(ValueError):
                module.snapshot(self.root, 'source.py', start, end, self.store)

    def test_missing_source_and_oversized_excerpt_are_not_success(self):
        record = self.capture()
        self.file.unlink()
        with self.assertRaises(FileNotFoundError):
            module.recall(self.root, record['handle'])
        self.file.write_text('x' * 8193)
        with self.assertRaises(ValueError):
            self.capture()
