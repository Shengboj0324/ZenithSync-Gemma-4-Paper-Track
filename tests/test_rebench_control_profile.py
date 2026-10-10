"""Reject evaluator profile ambiguity and argument/path injection."""
import unittest
from scripts.run_rebench_controls import validate_profile


class ControlProfileTests(unittest.TestCase):
    def setUp(self):
        self.profile = {'instance_id': 'stitchfix__nodebook-8',
                        'python': '/opt/conda/envs/testbed/bin/python',
                        'module': 'nodebook', 'expected_origin': '/testbed/nodebook/__init__.py',
                        'test_targets': ['tests/test_nodebookcore.py']}

    def test_reviewed_profile_and_node_selector(self):
        self.assertEqual(validate_profile(self.profile), self.profile)
        self.profile['test_targets'] = ['tests/test_nodebookcore.py::TestExample::test_one']
        validate_profile(self.profile)

    def test_rejects_unsafe_or_ambiguous_profiles(self):
        mutations = [('module', 'nodebook; import os'), ('python', '/usr/bin/python'),
                     ('expected_origin', '/testbed/../external.py'),
                     ('test_targets', ['--override-ini=addopts=']),
                     ('test_targets', ['/tmp/tests.py']), ('test_targets', ['../tests.py']),
                     ('test_targets', ['tests.py', 'tests.py']), ('test_targets', []),
                     ('test_targets', [None]), ('test_targets', 'tests.py')]
        for key, value in mutations:
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                validate_profile({**self.profile, key: value})
        with self.assertRaises(ValueError):
            validate_profile({**self.profile, 'extra': True})


if __name__ == '__main__':
    unittest.main()
