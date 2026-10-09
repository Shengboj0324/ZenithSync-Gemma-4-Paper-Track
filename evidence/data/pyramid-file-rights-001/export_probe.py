"""Task-specific, offline export of explicitly observed tracked source files."""
import hashlib
import json
from pathlib import Path
import subprocess

root = Path('/testbed')
out = Path('/audit')
out.mkdir()
paths = ['README.rst', 'src/pyramid/settings.py', 'tests/test_settings.py']
tracked = set(subprocess.check_output(['git', 'ls-files', '-z'], cwd=root).decode().split('\0'))
records = []
for name in paths:
    source = root / name
    if name not in tracked or source.is_symlink() or not source.resolve().is_relative_to(root):
        raise RuntimeError('Expected safe tracked source file')
    if source.stat().st_size > 1024 * 1024:
        raise RuntimeError('Unexpected source size')
    content = source.read_bytes()
    dest = out / 'source' / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(content)
    records.append({'path': name, 'size_bytes': len(content), 'sha256': hashlib.sha256(content).hexdigest()})
(out / 'files.json').write_text(json.dumps(records))
(out / 'snapshot.json').write_bytes(Path('/opt/zenithsync/source-snapshot.json').read_bytes())
