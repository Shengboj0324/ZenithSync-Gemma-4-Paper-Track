"""Atomic, no-overwrite checkpoint files for owned POSIX directories.

Only deserialize trusted, independently hash-bound local training artifacts.
This storage layer does not validate model/optimizer/cursor semantic compatibility.
"""
import hashlib
import os
from pathlib import Path
import stat
import tempfile

from .artifacts import file_record
from .contracts import digest


def _budget(value):
    if type(value) is not int or value <= 0:
        raise ValueError('Positive checkpoint byte budget required')


def _directory(path):
    if any(part.is_symlink() for part in [path, *path.parents]) or not path.is_dir():
        raise ValueError('Owned nonsymlink checkpoint directory required')


def save_checkpoint(path: Path, payload, *, max_bytes):
    """Publish a complete file atomically; an existing checkpoint is never replaced.

    Fsync errors after publication are reported as failures, but may leave a
    complete destination file. Inspect its identity instead of blindly retrying.
    Filesystem/hardware durability guarantees must still be qualified on the Pod.
    """
    import torch
    _budget(max_bytes)
    _directory(path.parent)
    if path.exists() or path.is_symlink():
        raise FileExistsError(path)
    descriptor, temporary = tempfile.mkstemp(prefix='.checkpoint-', dir=path.parent)
    temporary = Path(temporary)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            class BoundedWriter:
                def write(self, data):
                    if stream.tell() + len(data) > max_bytes:
                        raise ValueError('Checkpoint exceeds byte budget')
                    return stream.write(data)

                def flush(self):
                    stream.flush()

                def tell(self):
                    return stream.tell()

            torch.save(payload, BoundedWriter())
            stream.flush()
            os.fsync(stream.fileno())
        identity = file_record(temporary)
        # Hard-link publication is atomic and fails if another writer already
        # claimed this destination. Both names are on the same filesystem.
        os.link(temporary, path)
        temporary.unlink()
        directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
        return identity
    finally:
        temporary.unlink(missing_ok=True)


def load_checkpoint(path: Path, *, expected_identity, max_bytes):
    """Hash and deserialize through the same descriptor; load tensors onto CPU.

    Serialized bytes are bounded, not tensor allocations for hostile files.
    weights_only reduces deserialization exposure; it is not a resource sandbox.
    """
    import torch
    _budget(max_bytes)
    _directory(path.parent)
    if not isinstance(expected_identity, dict) or set(expected_identity) != {'sha256', 'size_bytes'}:
        raise ValueError('Exact checkpoint identity required')
    digest(expected_identity['sha256'])
    size = expected_identity['size_bytes']
    if type(size) is not int or not 0 < size <= max_bytes:
        raise ValueError('Checkpoint exceeds byte budget')
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size != size:
            raise ValueError('Checkpoint type or size mismatch')
        hasher = hashlib.sha256()
        while chunk := stream.read(1024 * 1024):
            hasher.update(chunk)
        if hasher.hexdigest() != expected_identity['sha256']:
            raise ValueError('Checkpoint hash mismatch')
        stream.seek(0)
        payload = torch.load(stream, map_location='cpu', weights_only=True)
        after = os.fstat(stream.fileno())
        signature = lambda value: (value.st_dev, value.st_ino, value.st_size,
                                   value.st_mtime_ns, value.st_ctime_ns)
        if signature(before) != signature(after):
            raise ValueError('Checkpoint changed while reading')
    return payload
