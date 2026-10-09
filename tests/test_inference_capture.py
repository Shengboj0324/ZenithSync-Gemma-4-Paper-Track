"""Synthetic transport checks, not model quality tests."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import tempfile
import threading
import unittest
import urllib.error
import urllib.request

from zenithsync.inference_capture import capture_inference


class CaptureTests(unittest.TestCase):
    def test_request_change_and_response_preservation(self):
        received = []
        response_bytes = b'{"choices": [], "token_ids": [123]}'

        class Upstream(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_POST(self):
                received.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(response_bytes)

        server = ThreadingHTTPServer(('127.0.0.1', 0), Upstream)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        payload = {'model': 'synthetic', 'messages': [{'role': 'user', 'content': 'data 🌍'}]}
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            with tempfile.TemporaryDirectory() as temporary:
                output = Path(temporary)/'capture'
                with capture_inference(output, server.server_port) as endpoint:
                    request = urllib.request.Request(endpoint+'/chat/completions',
                        data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
                    with opener.open(request, timeout=5) as response:
                        self.assertEqual(response.read(), response_bytes)
                self.assertEqual(received, [{**payload, 'return_token_ids': True}])
                self.assertEqual(json.loads((output/'0001/original-request.json').read_bytes()), payload)
                self.assertEqual((output/'0001/response.json').read_bytes(), response_bytes)
                self.assertEqual(json.loads((output/'0001/status.json').read_bytes()), {'http_status':200})
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_streaming_rejected_without_forwarding(self):
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)/'capture'
            with capture_inference(output, 18000) as endpoint:
                request = urllib.request.Request(endpoint+'/chat/completions', data=b'{"stream":true}')
                with self.assertRaises(urllib.error.HTTPError) as raised:
                    opener.open(request, timeout=5)
                self.assertEqual(raised.exception.code, 400)
            self.assertEqual(list(output.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
