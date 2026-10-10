"""Execution parity and rejection boundaries for source search adaptation."""
from pathlib import Path
import subprocess
import tempfile
import unittest

from scripts.replay_source_teacher import adapt_source_search, preflight


class SourceSearchReplayTests(unittest.TestCase):
    def commands(self, root):
        return [
            f'grep -n "Choices for a categorical distribution" {root}/grid.py',
            f'grep -n -A 2 -B 1 "ValueError\\|invalid\\|unsupported" {root}/grid.py',
            f'grep -rn "GridSampler.*Categorical\\|CategoricalDistribution" {root}/grid.py',
            f'find {root} -name "*.py" | grep -i grid | head -10',
            f'find {root} -name "*.py" -exec grep -l "3534" {{}} \\;',
        ]

    def test_real_shell_execution_parity_including_no_matches(self):
        with tempfile.TemporaryDirectory(prefix='search-replay-') as temporary:
            source = Path(temporary)/'source'
            mapped = Path(temporary)/'mapped'
            text = ('# Choices for a categorical distribution\n'
                    '# ValueError\n# invalid\n# unsupported\n'
                    '# GridSampler uses CategoricalDistribution\n# 3534\n')
            for directory in (source, mapped):
                directory.mkdir()
                (directory/'grid.py').write_text(text)
                (directory/'other.txt').write_text('3534\n')
            for present in (True, False):
                if not present:
                    for directory in (source, mapped):
                        (directory/'grid.py').write_text('# no matching text\n')
                for command in self.commands(str(source)):
                    with self.subTest(command=command, present=present):
                        adapted = adapt_source_search(command, str(source))
                        self.assertIsNotNone(adapted)
                        self.assertEqual(adapted, command.replace(str(source), '/workspace', 1))
                        actual = adapted.replace('/workspace', str(mapped), 1)
                        original = subprocess.run(['/bin/sh', '-c', command], capture_output=True, timeout=5)
                        replayed = subprocess.run(['/bin/sh', '-c', actual], capture_output=True, timeout=5)
                        self.assertEqual(original.returncode, replayed.returncode)
                        for field in ('stdout', 'stderr'):
                            self.assertEqual(
                                getattr(original, field).replace(str(source).encode(), b'<repo>'),
                                getattr(replayed, field).replace(str(mapped).encode(), b'<repo>'))

    def test_unreviewed_shell_extensions_and_paths_reject(self):
        root = '/workspace/example__repo__1.0'
        for command in self.commands(root):
            for suffix in ('; pwd', ' && pwd', '\n', ' > /tmp/out', ' | cat'):
                self.assertIsNone(adapt_source_search(command + suffix, root))
        invalid = [
            f'grep -n "$(pwd)" {root}/grid.py',
            f'grep -n "`pwd`" {root}/grid.py',
            f'grep -n "$HOME" {root}/grid.py',
            f'find {root} -name "*.py" -exec rm {{}} \\;',
            f'find {root} -name "*.py" -delete',
        ]
        for command in invalid:
            self.assertIsNone(adapt_source_search(command, root))
        for path in (root + '/../grid.py', root + '/.git/config',
                     root + '-other/grid.py', '/workspace/grid.py', root + '//grid.py'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                adapt_source_search(f'grep -n "two words" {path}', root)

    def test_preflight_preserves_timeout_metadata_without_mutation(self):
        root = '/workspace/example__repo__1.0'
        for command in self.commands(root):
            arguments = {'command': command, 'timeout': 30}
            messages = [{'tool_calls': [{'function': {'name': 'execute_bash', 'arguments': arguments}}]}]
            action = preflight(messages, root)[0]
            self.assertEqual(action['command'], command.replace(root, '/workspace', 1))
            self.assertEqual(action['source_timeout_seconds'], 30)
            self.assertEqual(arguments, {'command': command, 'timeout': 30})


if __name__ == '__main__':
    unittest.main()
