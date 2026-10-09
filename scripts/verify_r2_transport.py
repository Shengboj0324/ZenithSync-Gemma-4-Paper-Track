"""Live R2 multipart upload/readback/restore of explicitly synthetic data."""

import argparse
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from zenithsync.artifacts import canonical_json, file_record, inventory, verify
from zenithsync.object_store import ArtifactStore


def main():
    import boto3
    from boto3.s3.transfer import TransferConfig
    from botocore.config import Config
    from dotenv import dotenv_values

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    credentials = dotenv_values(ROOT / ".env")
    required = ["R2_ENDPOINT_URL", "R2_BUCKET_NAME", "R2_ACCESS_KEY_ID",
                "R2_SECRET_ACCESS_KEY"]
    if any(not credentials.get(name) for name in required):
        raise ValueError("required R2 environment fields are missing")
    client = boto3.client("s3", endpoint_url=credentials["R2_ENDPOINT_URL"],
                          region_name="auto",
                          aws_access_key_id=credentials["R2_ACCESS_KEY_ID"],
                          aws_secret_access_key=credentials["R2_SECRET_ACCESS_KEY"],
                          config=Config(connect_timeout=15, read_timeout=60,
                                        retries={"mode": "standard", "total_max_attempts": 3}))
    transfer = TransferConfig(multipart_threshold=8 * 1024**2,
                              multipart_chunksize=5 * 1024**2, max_concurrency=2)

    class BoundedClient:
        def get_object(self, **kwargs):
            return client.get_object(**kwargs)

        def put_object(self, **kwargs):
            return client.put_object(**kwargs)

        def upload_file(self, filename, bucket, key):
            return client.upload_file(filename, bucket, key, Config=transfer)

    source_names = ["zenithsync/object_store.py", "zenithsync/artifacts.py",
                    "zenithsync/contracts.py", "scripts/verify_r2_transport.py",
                    "tests/test_object_store.py"]
    identities = {name: file_record(ROOT / name) for name in source_names}
    store = ArtifactStore(BoundedClient(), credentials["R2_BUCKET_NAME"],
                          prefix="verification/p1/transport-v1")
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        source = root / "source"
        source.mkdir()
        # Public deterministic test bytes, containing no account or project data.
        block = bytes(range(256)) * 4096
        with (source / "multipart.bin").open("wb") as stream:
            for _ in range(10):
                stream.write(block)
            stream.write(b"synthetic-fixture")
        (source / "empty.bin").write_bytes(b"")
        manifest = inventory(source, kind="fixture", source="zenithsync synthetic R2 test",
                             revision="transport-v1")
        publication = store.publish(source, manifest)
        repeated = store.publish(source, manifest)
        restoration = store.restore(manifest, root / "restored", max_bytes=11 * 1024**2)
        verify(root / "restored", manifest)
        if repeated["uploaded_files"] != 0 or repeated["reused_files"] != 2:
            raise RuntimeError("idempotent publication check failed")
    if identities != {name: file_record(ROOT / name) for name in source_names}:
        raise RuntimeError("validation sources changed during run")
    (args.output / "fixture-manifest.json").write_bytes(canonical_json(manifest))
    receipt = {"schema_version": 1, "status": "live_roundtrip_passed",
               "timestamp_utc": datetime.now(timezone.utc).isoformat(),
               "publication": publication, "repeat_publication": repeated,
               "restoration": restoration, "sources": identities,
               "boto3_version": boto3.__version__,
               "manifest_sha256": hashlib.sha256(canonical_json(manifest)).hexdigest(),
               "scope": "synthetic multipart and zero-byte artifacts; not bulk model transfer"}
    (args.output / "receipt.json").write_bytes(canonical_json(receipt))
    print("Live R2 upload, hash readback, repeat publication and restore passed.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        # SDK exceptions can embed request details; do not emit credentials or URLs.
        print(f"R2 verification failed ({type(error).__name__}); no passing receipt written.",
              file=sys.stderr)
        raise SystemExit(1)
