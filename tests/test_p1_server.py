"""Real subprocess lifecycle checks with an explicitly synthetic SDK fixture."""

from datetime import datetime, timedelta, timezone
import importlib.util
import json
import os
from pathlib import Path
import signal
import socket
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

PATH = Path(__file__).resolve().parents[1] / 'scripts/run_p1_server.py'
spec = importlib.util.spec_from_file_location('p1_server_driver', PATH)
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)


class ServerLifecycleTests(unittest.TestCase):
    def exercise(self, child_code, seconds, startup, expected_error):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with socket.socket() as port_socket:
                port_socket.bind(('127.0.0.1', 0))
                port = port_socket.getsockname()[1]
            profile = root / 'profile.json'
            profile.write_text(json.dumps({'host': '127.0.0.1', 'port': port,
                                           'startup_timeout_seconds': startup}))
            session = root / 'session.json'
            session.write_text(json.dumps({'validation_deadline_utc':
                (datetime.now(timezone.utc)+timedelta(seconds=seconds)).isoformat()}))
            output = root / 'result'
            class FakeServer:
                def __init__(self, config):
                    self.log_path = str(root / 'unused-sdk.log')
                    Path(self.log_path).touch()
                    self.health_url = f'http://127.0.0.1:{port}/health'
                def build_cmd(self):
                    return [sys.executable, '-c', child_code]
                def build_env(self):
                    return dict(os.environ)
            fixture = types.SimpleNamespace(VllmConfig=lambda **kw: kw, VllmServer=FakeServer)
            argv = ['driver', '--profile', str(profile), '--session', str(session),
                    '--model-dir', str(root), '--output', str(output)]
            handlers = {sig: signal.getsignal(sig) for sig in (signal.SIGTERM, signal.SIGINT)}
            try:
                with patch.object(sys, 'argv', argv), patch.dict(sys.modules, {'adk_submission': fixture}), \
                     patch.object(driver, 'version', return_value='0.2.13'), \
                     patch.object(driver, 'sdk_config_arguments', return_value={}):
                    if expected_error:
                        with self.assertRaises(expected_error):
                            driver.main()
                    else:
                        driver.main()
            finally:
                for sig, handler in handlers.items():
                    signal.signal(sig, handler)
            result = json.loads((output / 'status.json').read_text())
            self.assertIsNotNone(result['server_returncode'])
            with self.assertRaises(ProcessLookupError):
                os.kill(result['pid'], 0)
            self.assertTrue((output / 'server.log').exists())
            return result, (output / 'server.log').read_text()

    def test_child_failure_preserves_exit_and_log(self):
        result, log = self.exercise("print('synthetic-startup-failure',flush=True); raise SystemExit(17)",
                                    10, 5, RuntimeError)
        self.assertEqual(result['server_returncode'], 17)
        self.assertIn('synthetic-startup-failure', log)
        self.assertEqual(result['status'], 'failed')

    def test_unready_child_is_terminated_at_startup_timeout(self):
        result, _ = self.exercise('import time; time.sleep(30)', 10, 0.1, TimeoutError)
        self.assertEqual(result['error_type'], 'TimeoutError')

    def test_session_deadline_terminates_live_child(self):
        result, _ = self.exercise('import time; time.sleep(30)', 0.4, 10, None)
        self.assertEqual(result['status'], 'session_deadline_reached')


if __name__ == '__main__':
    unittest.main()
