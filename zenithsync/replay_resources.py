"""Stage explicitly pinned public resource responses in a disposable sandbox."""

import base64
import io
from pathlib import Path
import tarfile

from .artifacts import canonical_json, file_record, load_json

DIRECTORY = '/opt/zenithsync-resource-replay'
STARTUP = '''import os, sys
try:
    import base64, json
    from pathlib import Path
    from offline_resources import install_resource_replay
    data=json.loads(Path('/opt/zenithsync-resource-replay/resources.json').read_text())
    _resource_events=[]
    _restore_resources=install_resource_replay({url:(base64.b64decode(v['body']),v['sha256'])
        for url,v in data.items()},_resource_events)
except Exception as error:
    sys.stderr.write('Offline resource startup failed: '+type(error).__name__+'\\n')
    os._exit(78)
'''


def stage_resources(manager, container_id, bundle, adapter):
    """Verify bytes, then copy only response bodies and transport code; no tests."""
    metadata = load_json(bundle / 'receipt.json')
    resources = {}
    for name, value in metadata['files'].items():
        if Path(name).name != name or file_record(bundle / name) != value['identity']:
            raise ValueError('Resource identity mismatch')
        body = (bundle / name).read_bytes()
        import hashlib
        if hashlib.sha256(body).hexdigest() != value['identity']['sha256']:
            raise ValueError('Resource changed during staging')
        url = value['original_url']
        if url in resources:
            raise ValueError('Duplicate resource URL')
        resources[url] = {'body': base64.b64encode(body).decode(),
                          'sha256': value['identity']['sha256']}
    files = {'resources.json': canonical_json(resources),
             'offline_resources.py': adapter.read_bytes(), 'sitecustomize.py': STARTUP.encode()}
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode='w') as archive:
        for name, body in files.items():
            info = tarfile.TarInfo(name)
            info.size, info.mode = len(body), 0o444
            archive.addfile(info, io.BytesIO(body))
    # Override startup PYTHONPATH for the staging operation itself; subsequent
    # Python processes must successfully install the response adapter or exit.
    result = manager.exec(container_id, 'mkdir -p ' + DIRECTORY, timeout=10)
    if result.exit_code:
        raise ValueError('Resource staging directory unavailable')
    if not manager.client.containers.get(container_id).put_archive(DIRECTORY, stream.getvalue()):
        raise ValueError('Resource staging failed')
    return {'receipt': file_record(bundle / 'receipt.json'), 'adapter': file_record(adapter),
            'directory': DIRECTORY, 'response_count': len(resources)}
