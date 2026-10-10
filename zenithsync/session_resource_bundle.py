"""Load explicitly reviewed response bundles for offline Session replay.

Hashes establish byte identity, not authenticity, rights, or training admission.
All validation finishes before a caller receives a transport payload.
"""
import base64
import hashlib
import io
from pathlib import Path
import tarfile

from .artifacts import canonical_json, file_record, load_json


def _filename(value):
    if (not isinstance(value, str) or value in ('', '.', '..', 'receipt.json', 'capture-receipt.json')
            or '/' in value or '\\' in value or ':' in value
            or any(ord(c) < 32 for c in value)):
        raise ValueError('Response filename must be a distinct local basename')
    return value


def load_session_resource_bundle(directory: Path, *, max_bytes: int):
    """Return base64 records and bindings after a complete capture/body check."""
    if type(max_bytes) is not int or max_bytes <= 0:
        raise ValueError('Positive explicit response-byte budget required')
    receipt_path = directory / 'receipt.json'
    capture_path = directory / 'capture-receipt.json'
    bindings = {name: file_record(directory / name)
                for name in ('receipt.json', 'capture-receipt.json')}
    receipt = load_json(receipt_path)
    if (not isinstance(receipt, dict)
            or set(receipt) != {'schema_version', 'capture_receipt', 'responses', 'training_approved'}
            or type(receipt['schema_version']) is not int or receipt['schema_version'] != 1
            or receipt['training_approved'] is not False
            or receipt['capture_receipt'] != bindings['capture-receipt.json']):
        raise ValueError('Invalid or unbound response bundle receipt')
    capture = load_json(capture_path)
    records = receipt['responses']
    if not isinstance(records, list) or not records:
        raise ValueError('Nonempty explicit response list required')
    captured = capture.get('responses') if isinstance(capture, dict) else None
    if not isinstance(captured, list) or len(captured) != len(records):
        raise ValueError('Bundle must cover the complete declared capture')
    by_url = {}
    for item in captured:
        if (not isinstance(item, dict) or not isinstance(item.get('requested_url'), str)
                or type(item.get('status')) is not int or item['status'] != 200
                or item.get('final_url') != item['requested_url']
                or not isinstance(item.get('retrieved_at'), str) or not item['retrieved_at'].strip()
                or item['requested_url'] in by_url):
            raise ValueError('Capture must contain unique direct successful responses')
        by_url[item['requested_url']] = item
    resources = {}
    total = 0
    names = set()
    for item in records:
        if not isinstance(item, dict) or set(item) != {'file', 'url', 'content_type', 'identity'}:
            raise ValueError('Invalid response entry')
        name = _filename(item['file'])
        url = item['url']
        if not isinstance(url, str) or url in resources or name in names or url not in by_url:
            raise ValueError('Duplicate or uncaptured response')
        observed = by_url[url]
        if (observed.get('identity') != item['identity']
                or observed.get('content_type') != item['content_type']):
            raise ValueError('Response differs from declared capture')
        path = directory / name
        identity = file_record(path)
        if identity != item['identity'] or total + identity['size_bytes'] > max_bytes:
            raise ValueError('Response identity or cumulative byte budget mismatch')
        body = path.read_bytes()
        if hashlib.sha256(body).hexdigest() != identity['sha256'] or len(body) != identity['size_bytes']:
            raise ValueError('Response changed during loading')
        bindings[name] = identity
        total += len(body)
        names.add(name)
        resources[url] = {'body': base64.b64encode(body).decode('ascii'),
                          'sha256': identity['sha256'], 'content_type': item['content_type']}
    if set(resources) != set(by_url):
        raise ValueError('Incomplete capture coverage')
    if bindings != {name: file_record(directory / name) for name in bindings}:
        raise ValueError('Bundle changed during loading')
    return resources, {'files': bindings, 'response_count': len(resources),
                       'response_bytes': total, 'training_approved': False}


def session_resource_payload(directory: Path, *, max_bytes: int):
    """Encode the validated bundle deterministically for sandbox staging."""
    resources, bindings = load_session_resource_bundle(directory, max_bytes=max_bytes)
    return canonical_json(resources), bindings


DIRECTORY = '/opt/zenithsync-session-resources'
STARTUP = '''import os, sys
try:
    import base64, json
    from pathlib import Path
    from session_resource_replay import install_session_resource_replay
    data=json.loads(Path('/opt/zenithsync-session-resources/resources.json').read_text())
    resources={url:dict(record, body=base64.b64decode(record['body'], validate=True))
               for url,record in data.items()}
    _resource_events=[]
    _restore_session_resources=install_session_resource_replay(resources,_resource_events)
except Exception as error:
    sys.stderr.write('Session resource startup failed: '+type(error).__name__+'\\n')
    os._exit(78)
'''


def stage_session_resources(manager, container_id, directory: Path, adapter: Path, *, max_bytes: int):
    """Copy only hash-checked bodies, reviewed transport and startup code."""
    payload, bindings = session_resource_payload(directory, max_bytes=max_bytes)
    adapter_identity = file_record(adapter)
    adapter_body = adapter.read_bytes()
    if (hashlib.sha256(adapter_body).hexdigest() != adapter_identity['sha256']
            or file_record(adapter) != adapter_identity):
        raise ValueError('Session transport changed during staging')
    files = {'resources.json': payload, 'session_resource_replay.py': adapter_body,
             'sitecustomize.py': STARTUP.encode('utf-8')}
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode='w') as archive:
        for name, body in files.items():
            entry = tarfile.TarInfo(name)
            entry.size, entry.mode = len(body), 0o444
            archive.addfile(entry, io.BytesIO(body))
    result = manager.exec(container_id, 'mkdir -p ' + DIRECTORY, timeout=10)
    if result.exit_code:
        raise ValueError('Session resource staging directory unavailable')
    if not manager.client.containers.get(container_id).put_archive(DIRECTORY, stream.getvalue()):
        raise ValueError('Session resource staging failed')
    return {'bundle': bindings, 'adapter': adapter_identity, 'directory': DIRECTORY,
            'startup_sha256': hashlib.sha256(files['sitecustomize.py']).hexdigest()}
