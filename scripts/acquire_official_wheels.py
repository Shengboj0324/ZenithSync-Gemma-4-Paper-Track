"""Acquire the listed official sandbox wheels with bounded parallel downloads.

Downloaded archives are CRC-checked and hashed. This records local provenance;
the official listing supplies sizes, not publisher SHA-256 signatures.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record, inventory, load_json, relative_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--listing", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source_identity = file_record(args.listing)
    rows = [r for r in load_json(args.listing) if r["name"].startswith("wheels/")]
    names = set()
    for row in rows:
        name = relative_path(row["name"])
        if len(name.split("/")) != 2 or not name.endswith(".whl") or name in names:
            raise ValueError("invalid or duplicate wheel listing entry")
        if type(row["size"]) is not int or not 0 < row["size"] < 100_000_000:
            raise ValueError("wheel size outside bounded acquisition policy")
        names.add(name)
    if not rows or sum(r["size"] for r in rows) > 100_000_000:
        raise ValueError("wheel listing exceeds acquisition budget")
    args.output.mkdir(parents=True, exist_ok=True)
    args.directory.mkdir(parents=True, exist_ok=True)
    journal = args.output / "downloads.jsonl"
    previous = {}
    if journal.exists():
        for line in journal.read_text().splitlines():
            record = json.loads(line)
            previous[record["path"]] = record
    from kaggle.api.kaggle_api_extended import KaggleApi

    def acquire(row):
        path = args.directory / row["name"]
        if os.path.lexists(path):
            record = previous.get(row["name"])
            if record is None or file_record(path) != {k:record[k] for k in ("sha256","size_bytes")}:
                raise ValueError("existing wheel has no matching completed acquisition record")
            return record
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="wheel-download-", dir=args.output) as staging:
            api = KaggleApi()
            api.authenticate()
            api.competition_download_file("gemma-4-developer-agent", row["name"],
                                          path=staging, quiet=True)
            downloaded = Path(staging) / path.name
            if downloaded.stat().st_size != row["size"]:
                raise ValueError("download size differs from official listing")
            with zipfile.ZipFile(downloaded) as archive:
                if archive.testzip() is not None:
                    raise ValueError("wheel CRC validation failed")
            record = {"path": row["name"], **file_record(downloaded)}
            if os.path.lexists(path):
                raise FileExistsError("wheel destination appeared during download")
            downloaded.rename(path)
        return record

    completed = []
    with journal.open("a") as log, ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(acquire, row) for row in rows]
        for future in as_completed(futures):
            record = future.result()
            completed.append(record)
            log.write(canonical_json(record).decode())
            log.flush()
            os.fsync(log.fileno())
            print(f"Verified {len(completed)}/{len(rows)} official wheels.", flush=True)
    if source_identity != file_record(args.listing):
        raise RuntimeError("official listing changed during acquisition")
    manifest = inventory(args.directory, kind="harness", source="official competition sandbox wheels",
                         revision="saved-listing-2026-10-08")
    if manifest["files"] != sorted(completed, key=lambda row:row["path"]):
        raise ValueError("wheel directory contains unaccounted files")
    (args.output / "manifest.json").write_bytes(canonical_json(manifest))
    (args.output / "receipt.json").write_bytes(canonical_json({
        "schema_version":1,"status":"official_wheels_acquired",
        "timestamp_utc":datetime.now(timezone.utc).isoformat(),"listing":source_identity,
        "verifier":file_record(Path(__file__)),"wheel_count":len(completed),
        "total_bytes":sum(r["size_bytes"] for r in completed),
        "scope":"download size, archive CRC and local hashes; runtime compatibility pending"}))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Wheel acquisition failed ({type(error).__name__}); inspect completed journal entries.",file=sys.stderr)
        raise SystemExit(1)
