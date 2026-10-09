"""Loopback-only scripted HTTP fixture; never evidence of model capabilities."""

from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading

from zenithsync.artifacts import canonical_json


@contextmanager
def source_http_fixture(scenario, output):
    if scenario not in {'success', 'server-error'}:
        raise ValueError('Unknown HTTP fixture')
    output.mkdir(parents=True, exist_ok=False)
    records = []
    lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            self.connection.settimeout(15)
            size = int(self.headers.get('Content-Length', '-1'))
            if self.path != '/v1/chat/completions' or not 0 <= size <= 2 * 1024**2:
                self.send_error(400)
                return
            request = json.loads(self.rfile.read(size))
            with lock:
                index = len(records)
                records.append({'request': request})
                if scenario == 'server-error':
                    status, response = 503, {'error': {'message': 'Intentional offline HTTP failure',
                        'type': 'fixture_error', 'code': 'fixture_unavailable'}}
                elif request.get('stream'):
                    status, response = 400, {'error': {'message': 'This fixture qualifies non-streaming only'}}
                else:
                    if index == 0:
                        message = {'role': 'assistant', 'content': None, 'tool_calls': [{
                            'id': 'http_fixture_write', 'type': 'function', 'function': {
                                'name': 'write_file', 'arguments': json.dumps({'filepath': 'diagnostic.txt',
                                    'content': 'OFFLINE HTTP FIXTURE; NOT A REPAIR\n'})}}]}
                    elif index == 1:
                        message = {'role': 'assistant', 'content': None, 'tool_calls': [{
                            'id': 'http_fixture_submit', 'type': 'function', 'function': {
                                'name': 'submit_patch', 'arguments': '{}'}}]}
                    else:
                        message = {'role': 'assistant', 'content': 'Offline HTTP fixture complete.'}
                    status, response = 200, {'id': f'fixture-{index}', 'object': 'chat.completion',
                        'created': 0, 'model': request.get('model'), 'choices': [{'index': 0,
                            'message': message, 'finish_reason': 'tool_calls' if index < 2 else 'stop'}],
                        'usage': {'prompt_tokens': 100, 'completion_tokens': 1, 'total_tokens': 101}}
                records[-1].update(status=status, response=response)
                (output / 'exchanges.json').write_bytes(canonical_json(records))
            body = canonical_json(response)
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}/v1'
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        (output / 'receipt.json').write_bytes(canonical_json({
            'fixture': scenario, 'requests': len(records), 'server_stopped': not thread.is_alive(),
            'synthetic_usage': True, 'training_approved': False, 'model_quality_evidence': False}))
        if thread.is_alive():
            raise RuntimeError('HTTP fixture thread remains active')
