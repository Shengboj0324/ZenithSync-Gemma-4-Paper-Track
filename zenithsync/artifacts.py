"""Portable local inventory and verification for quiescent artifact directories.

Not a sandbox for concurrently malicious filesystem writers. Supply an owned,
stable staging directory. Symlinks and nonregular entries are rejected.
"""

import hashlib
import json
import os
from pathlib import Path
import stat

from .contracts import digest, natural


def relative_path(value: str) -> str:
    if (not isinstance(value, str) or not value or "\\" in value or ":" in value
            or any(ord(c) < 32 or ord(c) == 127 for c in value)
            or any(p in ("", ".", "..") for p in value.split("/"))):
        raise ValueError("expected canonical relative POSIX path")
    return value


def _pairs(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> object:
    def invalid_constant(value: str) -> None:
        raise ValueError(f"invalid JSON constant: {value}")
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_pairs,
                      parse_constant=invalid_constant)


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False,
                       separators=(",", ":")) + "\n").encode("utf-8")


def file_record(path: Path) -> dict:
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode):
        raise ValueError(f"not a regular file: {path.name}")
    hasher = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        opened = os.fstat(stream.fileno())
        if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
            raise ValueError("file replaced during inventory")
        while True:
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            hasher.update(chunk)
            size += len(chunk)
        after = os.fstat(stream.fileno())
    signature = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    if signature(before) != signature(after) or size != before.st_size:
        fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
        changed = {name: [getattr(before, name), getattr(after, name)]
                   for name in fields if getattr(before, name) != getattr(after, name)}
        details = {"changed": changed, "read_bytes": size,
                   "flags_before": getattr(before, "st_flags", None),
                   "flags_after": getattr(after, "st_flags", None)}
        raise ValueError("file changed during inventory: " + path.name + "; "
                         + json.dumps(details, sort_keys=True))
    return {"size_bytes": size, "sha256": hasher.hexdigest()}


def inventory(root: Path, *, kind: str, source: str, revision: str) -> dict:
    if kind not in {"model", "harness", "candidate", "fixture"}:
        raise ValueError("unknown artifact kind")
    if any(not isinstance(v, str) or not v.strip() for v in (source, revision)):
        raise ValueError("source and revision are required")
    if root.is_symlink() or not root.is_dir():
        raise ValueError("artifact root must be a directory, not a symlink")
    files = []
    for directory, dirs, names in os.walk(root, followlinks=False):
        for name in sorted(dirs + names):
            path = Path(directory) / name
            mode = path.lstat().st_mode
            if stat.S_ISDIR(mode):
                continue
            record = file_record(path)
            record["path"] = relative_path(path.relative_to(root).as_posix())
            files.append(record)
    if not files:
        raise ValueError("empty artifact directory")
    return {"schema_version": 1, "kind": kind, "source": source,
            "revision": revision, "files": sorted(files, key=lambda r: r["path"])}


def validate_manifest(value: object) -> dict:
    if not isinstance(value, dict) or set(value) != {
        "schema_version", "kind", "source", "revision", "files"
    }:
        raise ValueError("invalid manifest fields")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1:
        raise ValueError("unsupported manifest schema")
    if value["kind"] not in ("model", "harness", "candidate", "fixture"):
        raise ValueError("unknown artifact kind")
    if any(not isinstance(value[k], str) or not value[k].strip()
           for k in ("source", "revision")):
        raise ValueError("source and revision are required")
    if not isinstance(value["files"], list) or not value["files"]:
        raise ValueError("manifest must contain files")
    seen = set()
    for record in value["files"]:
        if not isinstance(record, dict) or set(record) != {"path", "sha256", "size_bytes"}:
            raise ValueError("invalid file record")
        path = relative_path(record["path"])
        if path in seen:
            raise ValueError("duplicate artifact path")
        seen.add(path)
        digest(record["sha256"])
        natural(record["size_bytes"], "size_bytes")
    return value


def verify(root: Path, manifest: object) -> None:
    expected = validate_manifest(manifest)
    actual = inventory(root, kind=expected["kind"], source=expected["source"],
                       revision=expected["revision"])
    records = sorted(expected["files"], key=lambda r: r["path"])
    if actual["files"] != records:
        raise ValueError("artifact differs: missing, extra, changed, or renamed files")
