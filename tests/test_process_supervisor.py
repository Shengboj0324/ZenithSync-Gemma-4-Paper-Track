from datetime import datetime, timedelta, timezone
import os
import signal
from pathlib import Path
import sys
import tempfile
import unittest

from zenithsync.process_supervisor import run_bounded


@unittest.skipUnless(os.name == 'posix', 'POSIX process groups required')
class ProcessSupervisorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def run_worker(self, code, maximum=5):
        return run_bounded([sys.executable, '-c', code], log_path=self.root/'worker.log',
            deadline=datetime.now(timezone.utc)+timedelta(seconds=10),
            maximum_seconds=maximum, grace_seconds=0.15)

    def test_normal_completion_and_nonzero_exit(self):
        result = self.run_worker("print('retained output')")
        self.assertTrue(result['success'])
        self.assertIn('retained output', (self.root/'worker.log').read_text())
        (self.root/'worker.log').unlink()
        result = self.run_worker('raise SystemExit(7)')
        self.assertFalse(result['success'])
        self.assertEqual(result['returncode'], 7)

    def test_escalates_when_worker_ignores_termination(self):
        result = self.run_worker('import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(30)', 0.5)
        self.assertEqual(result['reason'], 'deadline_exceeded')
        self.assertTrue(result['kill_escalated'])
        self.assertFalse(result['process_group_remaining'])
        self.assertFalse(result['success'])

    def test_expired_deadline_does_not_launch(self):
        marker = self.root/'should-not-exist'
        with self.assertRaisesRegex(ValueError, 'expired'):
            run_bounded([sys.executable, '-c', f"open({str(marker)!r},'w').close()"],
                log_path=self.root/'worker.log', deadline=datetime.now(timezone.utc)-timedelta(seconds=1),
                maximum_seconds=1)
        self.assertFalse(marker.exists())
        self.assertFalse((self.root/'worker.log').exists())

    def test_insufficient_cleanup_window_does_not_launch(self):
        with self.assertRaisesRegex(ValueError, 'cleanup allowance'):
            run_bounded([sys.executable, '-c', 'pass'], log_path=self.root/'worker.log',
                deadline=datetime.now(timezone.utc)+timedelta(seconds=1),
                maximum_seconds=1, grace_seconds=1)
        self.assertFalse((self.root/'worker.log').exists())

    def test_deadline_stops_inherited_child_group(self):
        child_pid = self.root/'child.pid'
        code = (
            "import subprocess,sys,signal,time,pathlib\n"
            "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)'])\n"
            f"pathlib.Path({str(child_pid)!r}).write_text(str(child.pid))\n"
            "def stopped(sig,frame):\n"
            "    child.wait(timeout=2)\n"
            "    raise SystemExit(0)\n"
            "signal.signal(signal.SIGTERM,stopped)\n"
            "time.sleep(30)\n")
        result = run_bounded([sys.executable, '-c', code], log_path=self.root/'worker.log',
            deadline=datetime.now(timezone.utc)+timedelta(seconds=10),
            maximum_seconds=0.5, grace_seconds=2)
        self.assertEqual(result['reason'], 'deadline_exceeded')
        self.assertFalse(result['success'])
        self.assertFalse(result['process_group_remaining'])
        with self.assertRaises(ProcessLookupError):
            os.kill(int(child_pid.read_text()), 0)

    def test_cooperative_worker_obeys_stop_request(self):
        stop = self.root/'stop.request'
        result = run_bounded([sys.executable, '-c',
            f"import pathlib,time; pathlib.Path({str(stop)!r}).touch(); time.sleep(30)"],
            log_path=self.root/'worker.log', stop_path=stop,
            deadline=datetime.now(timezone.utc)+timedelta(seconds=10),
            maximum_seconds=5, grace_seconds=0.2)
        self.assertEqual(result['reason'], 'stop_requested')
        self.assertFalse(result['success'])
        self.assertFalse(result['process_group_remaining'])

    def test_supervisor_interruption_cleans_worker_and_restores_handler(self):
        worker_pid = self.root/'worker.pid'
        previous = signal.getsignal(signal.SIGTERM)
        code = ("import os,signal,time,pathlib; "
                f"pathlib.Path({str(worker_pid)!r}).write_text(str(os.getpid())); "
                "os.kill(os.getppid(),signal.SIGTERM); time.sleep(30)")
        with self.assertRaises(InterruptedError):
            self.run_worker(code)
        self.assertEqual(signal.getsignal(signal.SIGTERM), previous)
        with self.assertRaises(ProcessLookupError):
            os.kill(int(worker_pid.read_text()), 0)


if __name__ == '__main__':
    unittest.main()
