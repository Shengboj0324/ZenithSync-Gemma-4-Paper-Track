"""Review hints must not become implicit positive or negative labels."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from zenithsync.source_test_risk import review_python_test_source


class SourceTestRiskTests(unittest.TestCase):
    def test_flags_unconditional_claim_but_never_decides_admission(self):
        r = review_python_test_source('assert check()\nprint("All tests PASSED")\n')
        self.assertEqual(r['findings'][0]['line'], 2)
        self.assertEqual(r['findings'][0]['kind'], 'unconditional_module_success_message')
        self.assertIsNone(r['admission_decision'])

    def test_conditional_success_is_not_called_unconditional(self):
        r = review_python_test_source('if check():\n    print("All tests passed")\n')
        self.assertEqual(r['findings'], [])
        self.assertIsNone(r['admission_decision'])

    def test_broad_handlers_are_hints_even_when_reraising(self):
        for handler in ('Exception', 'BaseException', '(ValueError, Exception)'):
            r = review_python_test_source('try:\n    check()\nexcept '+handler+':\n    raise\n')
            self.assertEqual(r['findings'][0]['kind'], 'broad_exception_handler')
        r = review_python_test_source('try:\n    check()\nexcept:\n    pass\n')
        self.assertEqual(r['findings'][0]['line'], 3)

    def test_narrow_handler_and_nonclaim_print_are_not_flagged(self):
        r = review_python_test_source('try:\n    check()\nexcept ValueError:\n    print("expected")\n')
        self.assertEqual(r['findings'], [])

    def test_unparseable_or_nontext_inputs_do_not_pass_silently(self):
        r = review_python_test_source('def incomplete(')
        self.assertFalse(r['parsed'])
        self.assertEqual(r['findings'][0]['kind'], 'syntax_error')
        self.assertIsNone(r['admission_decision'])
        for source in (None, b'pass', 1):
            with self.assertRaises(ValueError):
                review_python_test_source(source)

    def test_source_is_never_executed(self):
        r = review_python_test_source('raise RuntimeError("must not execute")\n')
        self.assertTrue(r['parsed'])
        self.assertEqual(r['findings'], [])

    def test_cli_binds_source_and_preserves_existing_report(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source.py'
            output = Path(directory) / 'report.json'
            content = b'raise RuntimeError("do not execute")\nprint("passed")\n'
            source.write_bytes(content)
            command = [sys.executable, str(root / 'scripts/review_python_test_source.py'),
                       '--source', str(source), '--output', str(output)]
            run = subprocess.run(command, capture_output=True, text=True, timeout=20)
            self.assertEqual(run.returncode, 0, run.stderr)
            saved = output.read_bytes()
            report = json.loads(saved)
            self.assertIsNone(report['admission_decision'])
            self.assertEqual(report['sources'][0]['identity'], {
                'sha256': hashlib.sha256(content).hexdigest(), 'size_bytes': len(content)})
            self.assertEqual(report['sources'][0]['review']['findings'][0]['line'], 2)
            retry = subprocess.run(command, capture_output=True, text=True, timeout=20)
            self.assertNotEqual(retry.returncode, 0)
            self.assertEqual(output.read_bytes(), saved)


if __name__ == '__main__':
    unittest.main()
