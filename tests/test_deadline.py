import signal
import socket
import threading
import time
import unittest
import urllib.request

from zenithsync.deadline import DeadlineExpired, wall_deadline


class DeadlineTests(unittest.TestCase):
    def test_stalled_http_is_interrupted_and_cleanup_runs(self):
        listener = socket.socket()
        listener.bind(('127.0.0.1', 0))
        listener.listen(1)
        listener.settimeout(3)
        stop = threading.Event()

        def server():
            with listener:
                conn, _ = listener.accept()
                with conn:
                    conn.recv(8192)
                    # Headers arrive promptly; body never does. A per-socket
                    # timeout is deliberately longer than our wall deadline.
                    conn.sendall(b'HTTP/1.1 200 OK\r\nContent-Length: 100\r\n\r\n')
                    stop.wait(3)

        worker = threading.Thread(target=server)
        worker.start()
        previous = signal.getsignal(signal.SIGALRM)
        cleaned = False
        started = time.monotonic()
        try:
            with self.assertRaises(DeadlineExpired):
                try:
                    with wall_deadline(0.2):
                        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
                        with opener.open(f'http://127.0.0.1:{listener.getsockname()[1]}', timeout=5) as response:
                            response.read()
                finally:
                    cleaned = True
        finally:
            stop.set()
            worker.join(4)
        self.assertTrue(cleaned)
        self.assertFalse(worker.is_alive())
        self.assertLess(time.monotonic() - started, 2)
        self.assertEqual(signal.getitimer(signal.ITIMER_REAL), (0, 0))
        self.assertEqual(signal.getsignal(signal.SIGALRM), previous)

    def test_nested_timer_is_preserved(self):
        with wall_deadline(5):
            with self.assertRaises(RuntimeError):
                with wall_deadline(1):
                    self.fail('Nested timer was accepted')
            self.assertGreater(signal.getitimer(signal.ITIMER_REAL)[0], 3)


if __name__ == '__main__':
    unittest.main()
