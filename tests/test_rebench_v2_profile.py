from pathlib import Path
import unittest
from unittest.mock import patch

from scripts.compare_source_snapshot import run_image
from scripts.qualify_rebench_v2 import publisher_test_targets, validate_source_allowance, validate_v2_profile


class V2ProfileTests(unittest.TestCase):
    def setUp(self):
        self.profile = {'root': '/package', 'module': 'package',
            'python': '/usr/local/bin/python',
            'expected_origin': '/package/src/package/__init__.py',
            'test_targets': ['tests/test_module.py']}

    def test_system_python_and_src_layout_are_explicit(self):
        self.assertEqual(validate_v2_profile(self.profile), self.profile)

    def test_resource_profile_requires_exact_identity_and_budget(self):
        resource = {'receipt': {'sha256': 'a'*64, 'size_bytes': 100}, 'max_bytes': 500}
        self.assertEqual(validate_v2_profile({**self.profile, 'session_resources': resource})['session_resources'], resource)
        for value in (None, {}, {**resource, 'max_bytes': True},
                      {**resource, 'max_bytes': 0}, {**resource, 'receipt': {}},
                      {**resource, 'receipt': {'sha256': 'no', 'size_bytes': 100}}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_v2_profile({**self.profile, 'session_resources': value})
        for value in (False, 1, None):
            with self.assertRaises(ValueError):
                validate_v2_profile({**self.profile, 'publisher_nodes_only': value})

    def test_publisher_selection_covers_both_groups_and_rejects_foreign_nodes(self):
        task = {'FAIL_TO_PASS': ['tests/a.py::test_fix'], 'PASS_TO_PASS': ['tests/a.py::test_old']}
        self.assertEqual(publisher_test_targets(task, ['tests/a.py']),
                         ['tests/a.py::test_fix', 'tests/a.py::test_old'])
        for nodes in (['tests/b.py::test_fix'], ['--help'], [None], [[]],
                      ['tests/a.py::'], ['tests/a.py::test_old']):
            with self.subTest(nodes=nodes), self.assertRaises(ValueError):
                publisher_test_targets({**task, 'FAIL_TO_PASS': nodes}, ['tests/a.py'])

    def test_supplemental_tests_require_explicit_unique_identities(self):
        profile = {**self.profile, 'supplemental_pass_to_pass': ['tests/a.py::test_backend']}
        self.assertEqual(validate_v2_profile(profile), profile)
        for nodes in (None, 'test', ['test', 'test'], [''], ['test x'], [None]):
            with self.subTest(nodes=nodes), self.assertRaises(ValueError):
                validate_v2_profile({**self.profile, 'supplemental_pass_to_pass': nodes})

    def test_truncated_parameter_selects_function_without_duplicate_collection(self):
        task = {'FAIL_TO_PASS': ['tests/a.py::test_fix'], 'PASS_TO_PASS': [
            'tests/a.py::TestLabels::test_label[op0-Exp(2',
            'tests/a.py::TestLabels::test_label[op1-Exp(3',
            'tests/a.py::TestLabels::test_label[complete]',
            'tests/a.py::test_other[exact]']}
        self.assertEqual(publisher_test_targets(task, ['tests/a.py']), [
            'tests/a.py::test_fix', 'tests/a.py::TestLabels::test_label',
            'tests/a.py::test_other[exact]'])

    def test_function_expansion_does_not_relax_outcome_coverage(self):
        from zenithsync.pytest_controls import compare_controls
        key = 'tests/a.py::test_label[Exp(2'
        nodes = [key + ' Z)]', 'tests/a.py::test_label[unlisted]']
        document = {'collected': nodes, 'collection_errors': [], 'exitstatus': 0,
                    'reports': [{'nodeid': node, 'when': phase, 'outcome': 'passed'}
                                for node in nodes for phase in ('setup', 'call', 'teardown')]}
        self.assertEqual(publisher_test_targets(
            {'FAIL_TO_PASS': [], 'PASS_TO_PASS': [key]}, ['tests/a.py']),
            ['tests/a.py::test_label'])
        with self.assertRaisesRegex(ValueError, 'expectation coverage differs'):
            compare_controls(document, document, {'FAIL_TO_PASS': [], 'PASS_TO_PASS': [key],
                                                  'FAIL_TO_FAIL': [], 'PASS_TO_FAIL': []})

    def test_pytest_root_is_explicit_and_limited_to_repository(self):
        profile = {**self.profile, 'pytest_root': '/package'}
        self.assertEqual(validate_v2_profile(profile), profile)
        for root in ('/package/tests', '/other', '--help', None):
            with self.subTest(root=root), self.assertRaises(ValueError):
                validate_v2_profile({**self.profile, 'pytest_root': root})

    def test_flat_layout_requires_matching_repository_origin(self):
        profile = {**self.profile, 'layout': 'flat',
                   'expected_origin': '/package/package/__init__.py'}
        self.assertEqual(validate_v2_profile(profile), profile)
        for change in ({'layout': 'other'}, {'layout': None},
                       {'expected_origin': '/package/src/package/__init__.py'},
                       {'unexpected': True}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_v2_profile({**profile, **change})

    def test_flat_source_allowance_is_scoped_to_reviewed_package(self):
        self.assertEqual(validate_source_allowance(['dynaconf/validator.py'],
                         package_root='dynaconf'), ['dynaconf/validator.py'])
        for paths in (['src/validator.py'], ['tests/test_validator.py'],
                      ['dynaconf_other/validator.py'], ['dynaconf/../validator.py'],
                      ['dynaconf/.git/validator.py']):
            with self.subTest(paths=paths), self.assertRaises(ValueError):
                validate_source_allowance(paths, package_root='dynaconf')
        for package_root in (None, '', 'tests', '../dynaconf', '/dynaconf'):
            with self.subTest(package_root=package_root), self.assertRaises(ValueError):
                validate_source_allowance(['dynaconf/validator.py'], package_root=package_root)

    def test_ambiguous_or_injected_profiles_reject(self):
        for key, value in [('root', '/package/../other'), ('root', None),
            ('module', None), ('module', 'p; import os'), ('python', 'python'),
            ('python', '/usr//bin/python'), ('python', '/usr/../bin/python'),
            ('expected_origin', '/installed/package/__init__.py'),
            ('test_targets', ['--help']), ('test_targets', ['/tmp/tests.py']),
            ('test_targets', ['../tests.py']), ('test_targets', [None]),
            ('test_targets', [{}]), ('test_targets', []),
            ('test_targets', ['test_a.py', 'test_a.py'])]:
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                validate_v2_profile({**self.profile, key: value})

    def test_invalid_entrypoints_never_start_a_container(self):
        with patch('scripts.compare_source_snapshot.subprocess.run') as run:
            for executable in (None, 'python', '/a/../python', '/a//python', '/a;echo'):
                with self.subTest(executable=executable), self.assertRaises(ValueError):
                    run_image('sha256:' + 'a' * 64, Path('/unused'), entrypoint=executable)
            run.assert_not_called()

    def test_candidate_allowance_excludes_tests_metadata_and_ambiguous_paths(self):
        self.assertEqual(validate_source_allowance(['src/package/module.py']),
                         ['src/package/module.py'])
        for paths in (None, [], [None], ['tests/test_module.py'], ['/src/module.py'],
                      ['src/../module.py'], ['src//module.py'], ['src/.git/module.py'],
                      ['src/module.py', 'src/module.py'], ['src/module.py;echo']):
            with self.subTest(paths=paths), self.assertRaises(ValueError):
                validate_source_allowance(paths)


if __name__ == '__main__':
    unittest.main()
