"""Bounded, CPU-only inspection of checkpoint storage, without loading weights.

This checks byte layout, not numerical weight validity or loader compatibility.
Inputs must be in an owned, quiescent directory (as with artifacts.inventory).
Unknown dtypes are rejected rather than assigned a guessed storage width.
"""

from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import stat

from .artifacts import _pairs


# Deliberately limited to byte-aligned storage types; packed W4 uses I32 here.
DTYPE_BYTES = {"BOOL": 1, "U8": 1, "I8": 1, "I16": 2, "U16": 2,
               "F16": 2, "BF16": 2, "I32": 4, "U32": 4, "F32": 4,
               "I64": 8, "U64": 8, "F64": 8}
MAX_HEADER_BYTES = 16 * 1024 * 1024


def _integer(value: object) -> bool:
    return type(value) is int and 0 <= value <= 2**64 - 1


def _invalid_constant(value: str) -> None:
    raise ValueError(f"nonfinite JSON constant: {value}")


def inspect_safetensors(path: Path) -> dict:
    """Validate complete interval coverage and exact tensor byte counts.

    Each tensor has length itemsize * product(shape). Sorting its half-open
    interval and requiring start == previous end proves no gaps or overlap.
    Zero-length intervals are permitted only at tensor boundaries.
    """
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode):
        raise ValueError("checkpoint must be a regular file, not a symlink")
    with path.open("rb") as stream:
        opened = os.fstat(stream.fileno())
        if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
            raise ValueError("checkpoint replaced during inspection")
        prefix = stream.read(8)
        if len(prefix) != 8:
            raise ValueError("truncated header length")
        size = int.from_bytes(prefix, "little")
        if not 2 <= size <= MAX_HEADER_BYTES or 8 + size > opened.st_size:
            raise ValueError("invalid or excessive header length")
        raw = stream.read(size)
        if len(raw) != size or not raw.startswith(b"{"):
            raise ValueError("invalid header encoding or truncation")
        try:
            header = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs,
                                parse_constant=_invalid_constant)
        except (UnicodeError, RecursionError) as exc:
            raise ValueError("invalid header encoding or nesting") from exc
        if not isinstance(header, dict):
            raise ValueError("header must be an object")
        metadata = header.pop("__metadata__", {})
        if not isinstance(metadata, dict) or any(
                not isinstance(v, str) for v in metadata.values()):
            raise ValueError("metadata must map strings to strings")
        buffer_size = opened.st_size - 8 - size
        intervals = []
        dtypes = Counter()
        for name, tensor in header.items():
            if not isinstance(tensor, dict) or set(tensor) != {
                    "dtype", "shape", "data_offsets"}:
                raise ValueError(f"invalid tensor descriptor: {name}")
            dtype, shape, offsets = (tensor[k] for k in
                                     ("dtype", "shape", "data_offsets"))
            if not isinstance(dtype, str) or dtype not in DTYPE_BYTES:
                raise ValueError(f"unsupported storage dtype: {name}")
            if not isinstance(shape, list) or len(shape) > 64 or not all(
                    _integer(dimension) for dimension in shape):
                raise ValueError(f"invalid tensor shape: {name}")
            if not isinstance(offsets, list) or len(offsets) != 2 or not all(
                    _integer(offset) for offset in offsets):
                raise ValueError(f"invalid tensor offsets: {name}")
            start, end = offsets
            if not start <= end <= buffer_size:
                raise ValueError(f"tensor outside data buffer: {name}")
            if end - start != math.prod(shape) * DTYPE_BYTES[dtype]:
                raise ValueError(f"tensor shape/storage length mismatch: {name}")
            intervals.append((start, end, name))
            dtypes[dtype] += 1
        cursor = 0
        for start, end, name in sorted(intervals):
            if start != cursor:
                raise ValueError(f"data gap or overlap: {name}")
            cursor = end
        if cursor != buffer_size:
            raise ValueError("unindexed trailing data")
        after = os.fstat(stream.fileno())
    signature = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    if signature(before) != signature(after) or signature(after) != signature(path.lstat()):
        raise ValueError("checkpoint changed during inspection")
    return {"schema_version": 1, "scope": "storage_structure_only",
            "file_size_bytes": opened.st_size, "header_size_bytes": size,
            "header_sha256": hashlib.sha256(raw).hexdigest(),
            "data_size_bytes": buffer_size, "tensor_count": len(header),
            "dtype_counts": dict(sorted(dtypes.items())),
            "numerical_weights_checked": False, "gpu_loader_checked": False}
