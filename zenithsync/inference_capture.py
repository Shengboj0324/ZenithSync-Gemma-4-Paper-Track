"""Bounded, loopback-only diagnostic capture for nonstreaming inference.

The sole request change asks vLLM to return raw generated token IDs. The original
and forwarded JSON bodies are both retained; response bytes pass through unchanged.
Use only with curated development inputs: bodies may contain repository contents.
"""

from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import itertools
import json
from pathlib import Path
import threading
import urllib.error
import urllib.request

CAP = 16 * 1024 * 1024


@contextmanager
def capture_inference(output: Path, upstream_port: int):
    if type(upstream_port) is not int or not 1024 <= upstream_port <= 65535:
        raise ValueError('Expected an unprivileged loopback port')
    output.mkdir(parents=True, exist_ok=False)
    sequence = itertools.count(1)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def setup(self):
            super().setup()
            self.connection.settimeout(180)

        def do_POST(self):
            if self.path != '/v1/chat/completions':
                self.send_error(404)
                return
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= CAP or self.headers.get('Transfer-Encoding'):
                    raise ValueError('Unsupported request framing')
                original = self.rfile.read(length)
                if len(original) != length:
                    raise ValueError('Incomplete body')
                payload = json.loads(original)
                if not isinstance(payload, dict) or payload.get('stream', False) is not False:
                    raise ValueError('Only nonstreaming JSON requests supported')
            except (ValueError, UnicodeError):
                self.send_error(400)
                return
            record = output / f'{next(sequence):04d}'
            record.mkdir()
            (record / 'original-request.json').write_bytes(original)
            payload['return_token_ids'] = True
            forwarded = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            (record / 'forwarded-request.json').write_bytes(forwarded)
            request = urllib.request.Request(
                f'http://127.0.0.1:{upstream_port}/v1/chat/completions',
                data=forwarded, headers={'Content-Type': 'application/json',
                                         'Authorization': 'Bearer EMPTY'})
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            try:
                try:
                    response = opener.open(request, timeout=180)
                except urllib.error.HTTPError as error:
                    response = error
                with response:
                    status = response.code
                    body = response.read(CAP + 1)
                    content_type = response.headers.get('Content-Type', 'application/json')
                if len(body) > CAP:
                    raise ValueError('Response exceeds capture limit')
            except (OSError, ValueError) as error:
                (record / 'transport-error.txt').write_text(type(error).__name__ + '\n')
                self.send_error(502)
                return
            (record / 'response.json').write_bytes(body)
            (record / 'status.json').write_text(json.dumps({'http_status': status}) + '\n')
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    server.daemon_threads = False
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}/v1'
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
