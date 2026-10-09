"""Content-addressed artifact transport using an injected S3-compatible client.

Only explicit, curated, quiescent bundles belong here, never a workspace root.
Remote bytes are streamed and hashed; ETags are never treated as SHA-256.
Local destination parents must be owned and free of concurrent writers.
"""

import hashlib
import json
import os
from pathlib import Path
import tempfile

from .artifacts import canonical_json, relative_path, validate_manifest, verify
from .contracts import digest, natural


class IntegrityError(ValueError):
    """An object does not match its declared content identity."""


def _missing(exc: Exception) -> bool:
    response = getattr(exc, "response", {})
    return response.get("Error", {}).get("Code") in {"NoSuchKey", "404", "NotFound"}


def _snapshot(manifest: object) -> dict:
    result = json.loads(canonical_json(validate_manifest(manifest)))
    paths = {row["path"] for row in result["files"]}
    for path in paths:
        parts = path.split("/")
        if any(part in {".git", ".ssh", ".aws", ".kaggle"} or
               part == ".env" or part.startswith(".env.") for part in parts):
            raise ValueError("credential or workspace metadata path excluded")
        if any("/".join(parts[:i]) in paths for i in range(1, len(parts))):
            raise ValueError("file/directory path collision")
    return result


class ArtifactStore:
    def __init__(self, client, bucket: str, prefix: str = "artifacts/v1"):
        if not isinstance(bucket, str) or not bucket.strip():
            raise ValueError("bucket is required")
        self.client = client
        self.bucket = bucket
        self.prefix = relative_path(prefix)

    def blob_key(self, sha256: str) -> str:
        digest(sha256)
        return f"{self.prefix}/blobs/sha256/{sha256}"

    def _read_verified(self, key: str, record: dict, target=None) -> None:
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        body = response["Body"]
        hasher, size = hashlib.sha256(), 0
        try:
            if response.get("ContentLength") != record["size_bytes"]:
                raise IntegrityError("remote content length differs")
            while chunk := body.read(1024 * 1024):
                size += len(chunk)
                if size > record["size_bytes"]:
                    raise IntegrityError("remote stream exceeds declared size")
                hasher.update(chunk)
                if target is not None:
                    target.write(chunk)
            if size != record["size_bytes"] or hasher.hexdigest() != record["sha256"]:
                raise IntegrityError("remote content digest or size differs")
        finally:
            body.close()

    def publish(self, root: Path, manifest: object) -> dict:
        """Commit a manifest only after all referenced bytes pass readback.

        Retrying reuses verified whole objects. Multipart retries/cleanup are
        delegated to the SDK; a killed process may leave incomplete uploads.
        """
        frozen = _snapshot(manifest)
        verify(root, frozen)
        uploaded, reused = 0, 0
        for record in frozen["files"]:
            key = self.blob_key(record["sha256"])
            try:
                self._read_verified(key, record)
            except Exception as exc:
                if not _missing(exc):
                    raise
                self.client.upload_file(str(root / record["path"]), self.bucket, key)
                self._read_verified(key, record)
                uploaded += 1
            else:
                reused += 1
        # Detect source drift before publishing the bundle's commit marker.
        verify(root, frozen)
        payload = canonical_json(frozen)
        identity = hashlib.sha256(payload).hexdigest()
        key = f"{self.prefix}/manifests/sha256/{identity}.json"
        record = {"sha256": identity, "size_bytes": len(payload)}
        try:
            self._read_verified(key, record)
        except Exception as exc:
            if not _missing(exc):
                raise
            self.client.put_object(Bucket=self.bucket, Key=key, Body=payload,
                                   ContentType="application/json")
            self._read_verified(key, record)
        return {"manifest_sha256": identity, "manifest_key": key,
                "uploaded_files": uploaded, "reused_files": reused,
                "verified_bytes": sum(r["size_bytes"] for r in frozen["files"])}

    def restore(self, manifest: object, destination: Path, *, max_bytes: int) -> dict:
        """Restore a trusted manifest into a new directory, atomically on success.

        No partially validated output is exposed at the destination. The caller
        must authenticate the manifest separately and provide a disk-size cap.
        """
        frozen = _snapshot(manifest)
        natural(max_bytes, "max_bytes")
        total = sum(row["size_bytes"] for row in frozen["files"])
        if total > max_bytes:
            raise ValueError("artifact exceeds restore byte budget")
        if os.path.lexists(destination):
            raise FileExistsError("restore destination already exists")
        parent = destination.parent.resolve(strict=True)
        with tempfile.TemporaryDirectory(prefix=".restore-", dir=parent) as temporary:
            staging = Path(temporary) / "bundle"
            staging.mkdir(mode=0o700)
            for row in frozen["files"]:
                path = staging / row["path"]
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("xb") as stream:
                    self._read_verified(self.blob_key(row["sha256"]), row, stream)
                    stream.flush()
                    os.fsync(stream.fileno())
            verify(staging, frozen)
            if os.path.lexists(destination):
                raise FileExistsError("restore destination appeared during transfer")
            staging.rename(destination)
        return {"restored_files": len(frozen["files"]), "verified_bytes": total}
