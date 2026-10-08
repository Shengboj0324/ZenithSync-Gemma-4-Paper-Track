"""ZIP structural preflight only; official YAML/ADK validation is unresolved."""

import hashlib
from pathlib import Path
import stat
import zipfile

from .artifacts import relative_path
from .contracts import natural

ROOT_CONFIGS = frozenset({"agent.yaml", "agent.yml", "root_agent.yaml", "root_agent.yml"})


def inspect_zip(path: Path, *, max_bytes: int, max_entries: int) -> dict:
    natural(max_bytes, "max_bytes")
    natural(max_entries, "max_entries")
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        if len(entries) > max_entries:
            raise ValueError("archive entry limit exceeded")
        names = set()
        portable_names = set()
        files = []
        total = 0
        for entry in entries:
            if entry.orig_filename != entry.filename:
                raise ValueError("noncanonical ZIP filename")
            name = relative_path(entry.filename[:-1] if entry.is_dir() else entry.filename)
            if name in names or name.casefold() in portable_names:
                raise ValueError("duplicate or case-colliding archive path")
            names.add(name)
            portable_names.add(name.casefold())
            mode = entry.external_attr >> 16
            file_type = stat.S_IFMT(mode)
            if file_type not in (0, stat.S_IFREG, stat.S_IFDIR):
                raise ValueError("archive contains symlink or special file")
            if (file_type == stat.S_IFDIR and not entry.is_dir()
                    or file_type == stat.S_IFREG and entry.is_dir()):
                raise ValueError("inconsistent directory metadata")
            if entry.flag_bits & 1:
                raise ValueError("encrypted archive unsupported")
            if entry.is_dir():
                if entry.file_size:
                    raise ValueError("directory has content")
                continue
            if total + entry.file_size > max_bytes:
                raise ValueError("archive byte limit exceeded")
            hasher = hashlib.sha256()
            size = 0
            with archive.open(entry) as stream:
                while chunk := stream.read(1024 * 1024):
                    size += len(chunk)
                    if total + size > max_bytes:
                        raise ValueError("archive byte limit exceeded")
                    hasher.update(chunk)
            if size != entry.file_size:
                raise ValueError("ZIP size mismatch")
            total += size
            files.append({"path": name, "size_bytes": size, "sha256": hasher.hexdigest()})
        file_names = {record["path"].casefold() for record in files}
        for name in portable_names:
            parts = name.split("/")
            if any("/".join(parts[:i]) in file_names for i in range(1, len(parts))):
                raise ValueError("file/directory path conflict")
        roots = [record for record in files if record["path"] in ROOT_CONFIGS]
        if len(roots) != 1 or roots[0]["size_bytes"] == 0:
            raise ValueError("exactly one nonempty root agent configuration required")
    return {"structural_preflight": "passed", "official_compatibility": "unverified",
            "yaml_validation": "not_performed", "uncompressed_bytes": total,
            "files": sorted(files, key=lambda r: r["path"])}
