"""Synthetic provenance cases; actual pytest integration is exercised separately."""

import importlib.util
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


class SourceObservationTests(unittest.TestCase):
    def test_loaded_module_uses_resolved_path_and_content_hash(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root/'workspace'
            workspace.mkdir()
            module = workspace/'example.py'
            module.write_bytes(b'x = 1\n')
            spec = importlib.util.spec_from_file_location('source_probe',
                Path(__file__).resolve().parents[1]/'scripts/evaluator_source_plugin.py')
            plugin = importlib.util.module_from_spec(spec)
            with patch.dict(sys.modules, {'pytest': SimpleNamespace()}):
                spec.loader.exec_module(plugin)
            with patch.dict(sys.modules, {'example': SimpleNamespace(__file__=str(module))}):
                row = plugin.observe_modules(['example'], workspace)[0]
            self.assertTrue(row['loaded'])
            self.assertTrue(row['inside_workspace'])
            self.assertEqual(row['file'], str(module.resolve()))
            self.assertEqual(row['sha256'], '9e26bf369911c45c243c684147b23fc9e1dcfcf257d299a1c632016a6fcd33f4')

    def test_prefix_collision_and_missing_module_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root/'workspace'
            workspace.mkdir()
            outside = root/'workspace-untrusted'
            outside.mkdir()
            module = outside/'example.py'
            module.write_text('x = 1\n')
            spec = importlib.util.spec_from_file_location('source_probe',
                Path(__file__).resolve().parents[1]/'scripts/evaluator_source_plugin.py')
            plugin = importlib.util.module_from_spec(spec)
            with patch.dict(sys.modules, {'pytest': SimpleNamespace()}):
                spec.loader.exec_module(plugin)
            with patch.dict(sys.modules, {'outside_example': SimpleNamespace(__file__=str(module))}):
                rows = plugin.observe_modules(['outside_example', 'absent_zenith_module'], workspace)
            self.assertFalse(rows[0]['inside_workspace'])
            self.assertFalse(rows[1]['loaded'])
            self.assertFalse(rows[1]['inside_workspace'])


if __name__ == '__main__':
    unittest.main()
