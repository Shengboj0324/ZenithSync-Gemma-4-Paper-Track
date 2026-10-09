import unittest
from scripts.audit_source_tool_contracts import path_category


class ToolPathCategories(unittest.TestCase):
    def test_root_boundaries_and_traversal(self):
        expected = {'/workspace': 'workspace_root', '/workspace/a.py': 'workspace_descendant',
                    '/workspace2/a.py': 'other_absolute', '/workspace/../a': 'parent_traversal',
                    '../a': 'parent_traversal', '/tmp/a': 'temporary', '/tmp2/a': 'other_absolute',
                    '/testbed/a': 'testbed', 'a.py': 'relative', '/workspace/α.py': 'workspace_descendant'}
        for path, category in expected.items():
            with self.subTest(path=path):
                self.assertEqual(path_category(path), category)
        self.assertEqual(path_category(None), 'non_string')
