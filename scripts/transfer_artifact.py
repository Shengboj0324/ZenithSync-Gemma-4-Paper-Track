"""Publish or restore a curated manifest using R2, with a retained receipt.

The manifest travels with the deployment bundle and must be trusted separately.
This command does not ingest an arbitrary repository or scan it for secrets.
"""

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from zenithsync.artifacts import canonical_json, file_record, load_json, validate_manifest
from zenithsync.object_store import ArtifactStore


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["publish", "restore"])
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--max-bytes", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--prefix", default="artifacts/v1")
    args = parser.parse_args()
    manifest = validate_manifest(load_json(args.manifest))
    total = sum(row["size_bytes"] for row in manifest["files"])
    if args.max_bytes < 0 or total > args.max_bytes:
        raise ValueError("manifest exceeds explicit transfer budget")
    args.output.mkdir(parents=True, exist_ok=False)
    source_names = ["scripts/transfer_artifact.py", "zenithsync/object_store.py",
                    "zenithsync/artifacts.py", "zenithsync/contracts.py"]
    sources = {name: file_record(ROOT / name) for name in source_names}
    manifest_identity = file_record(args.manifest)
    import boto3
    from boto3.s3.transfer import TransferConfig
    from botocore.config import Config
    credentials = dict(os.environ)
    if args.env_file is not None:
        from dotenv import dotenv_values
        # Explicit environment wins over optional dotenv values.
        credentials = {**dotenv_values(args.env_file), **credentials}
    required = ["R2_ENDPOINT_URL", "R2_BUCKET_NAME", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY"]
    if any(not credentials.get(name) for name in required):
        raise ValueError("required R2 credential fields are missing")
    client = boto3.client("s3", endpoint_url=credentials["R2_ENDPOINT_URL"],
                          region_name="auto", aws_access_key_id=credentials["R2_ACCESS_KEY_ID"],
                          aws_secret_access_key=credentials["R2_SECRET_ACCESS_KEY"],
                          config=Config(connect_timeout=15, read_timeout=60,
                                        retries={"mode": "standard", "total_max_attempts": 3}))
    transfer = TransferConfig(multipart_threshold=16 * 1024**2,
                              multipart_chunksize=64 * 1024**2, max_concurrency=2)

    class Client:
        def get_object(self, **kwargs):
            return client.get_object(**kwargs)

        def put_object(self, **kwargs):
            return client.put_object(**kwargs)

        def upload_file(self, filename, bucket, key):
            lock = threading.Lock()
            sent, reported = 0, time.monotonic()

            def progress(amount):
                nonlocal sent, reported
                with lock:
                    sent += amount
                    now = time.monotonic()
                    if now - reported >= 15:
                        print(f"Upload progress: {sent} bytes transferred in current object.", flush=True)
                        reported = now

            print("Uploading one content-addressed object.", flush=True)
            client.upload_file(filename, bucket, key, Config=transfer, Callback=progress)
            print("Upload returned; remote hash verification follows.", flush=True)

    print(f"Starting {args.operation}: {len(manifest['files'])} files, {total} bytes.", flush=True)
    store = ArtifactStore(Client(), credentials["R2_BUCKET_NAME"], prefix=args.prefix)
    if args.operation == "publish":
        result = store.publish(args.directory, manifest)
    else:
        result = store.restore(manifest, args.directory, max_bytes=args.max_bytes)
    if sources != {name: file_record(ROOT / name) for name in source_names}:
        raise RuntimeError("implementation changed during transfer")
    if manifest_identity != file_record(args.manifest):
        raise RuntimeError("manifest changed during transfer")
    receipt = {"schema_version": 1, "operation": args.operation,
               "timestamp_utc": datetime.now(timezone.utc).isoformat(),
               "status": "verified", "manifest_file": manifest_identity,
               "sources": sources, "result": result, "boto3_version": boto3.__version__}
    (args.output / "receipt.json").write_bytes(canonical_json(receipt))
    print(f"{args.operation.capitalize()} verified; receipt saved.", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Transfer failed ({type(error).__name__}); no passing receipt written.", file=sys.stderr)
        raise SystemExit(1)
