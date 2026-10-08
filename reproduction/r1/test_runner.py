"""Checks of receipt handling, distinct from the software-repair evaluation."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class ReceiptTests(unittest.TestCase):
    def test_failure_exit_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = subprocess.run([sys.executable, str(Path(__file__).with_name("run_command.py")),
                "--cwd", directory, "--out", str(root / "receipt"), "--", sys.executable,
                "-c", "print('expected failure'); raise SystemExit(7)"], capture_output=True)
            self.assertEqual(result.returncode, 0)
            receipt = json.loads((root / "receipt/receipt.json").read_text())
            self.assertEqual(receipt["returncode"], 7)
            self.assertFalse(receipt["timed_out"])
            self.assertEqual((root / "receipt/stdout.txt").read_text(), "expected failure\n")

    def test_timeout_is_explicit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run([sys.executable, str(Path(__file__).with_name("run_command.py")),
                "--cwd", directory, "--out", str(root / "receipt"), "--timeout", "0.1", "--",
                sys.executable, "-c", "import time; time.sleep(10)"], check=True, capture_output=True)
            receipt = json.loads((root / "receipt/receipt.json").read_text())
            self.assertTrue(receipt["timed_out"])
            self.assertNotEqual(receipt["returncode"], 0)

    def test_existing_receipt_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            saved = root / "receipt"
            saved.mkdir()
            (saved / "receipt.json").write_text("existing evidence")
            result = subprocess.run([sys.executable, str(Path(__file__).with_name("run_command.py")),
                "--cwd", directory, "--out", str(saved), "--", sys.executable, "-c", "pass"], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual((saved / "receipt.json").read_text(), "existing evidence")


if __name__ == "__main__":
    unittest.main()
