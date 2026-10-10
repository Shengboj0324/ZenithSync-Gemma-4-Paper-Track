import unittest

from zenithsync.static_controls import compare_mypy_controls, mypy_diagnostics


def result(errors):
    return {'returncode': int(bool(errors)), 'stdout': '\n'.join(errors + [
        f'Found {len(errors)} errors in 1 file (checked 1 source file)' if errors
        else 'Success: no issues found in 1 source file']) + '\n'}


class StaticControlsTests(unittest.TestCase):
    def test_existing_errors_do_not_hide_new_override(self):
        existing = 'src/a.py:1: error: Existing issue  [arg-type]'
        new = 'src/a.py:9: error: Incompatible return type  [override]'
        output = compare_mypy_controls(result([existing]), result([existing]), result([existing, new]))
        self.assertFalse(output['candidate_has_no_new_diagnostics'])
        self.assertEqual(output['introduced_vs_reference'][0]['code'], 'override')
        self.assertFalse(output['training_approved'])

    def test_line_movement_and_order_are_not_new_errors(self):
        first = 'src/a.py:1: error: A  [arg-type]'
        second = 'src/b.py:2: error: B  [override]'
        output = compare_mypy_controls(result([first, second]), result([first, second]),
                                       result([second.replace(':2:', ':99:'), first.replace(':1:', ':8:')]))
        self.assertTrue(output['candidate_has_no_new_diagnostics'])

    def test_duplicate_error_multiplicity_is_preserved(self):
        error = 'src/a.py:1: error: A  [arg-type]'
        output = compare_mypy_controls(result([error]), result([error]), result([error, error]))
        self.assertEqual(output['introduced_vs_base'][0]['count'], 1)

    def test_infrastructure_and_contradictory_output_reject(self):
        for stdout, code in (('', 0), ('mypy: error: cannot find module', 2),
            ('Success: no issues found in 1 source file\n', 1),
            ('Found 1 error in 1 file (checked 1 source file)\n', 1),
            ('\x1b[31mSuccess: no issues found in 1 source file\n', 0),
            ('unknown output\nSuccess: no issues found in 1 source file\n', 0)):
            with self.subTest(stdout=stdout), self.assertRaises(ValueError):
                mypy_diagnostics(stdout, code)


if __name__ == '__main__':
    unittest.main()
