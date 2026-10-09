"""Record checkpoint storage evidence without GPU use or weight deserialization."""

import argparse
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from zenithsync.artifacts import canonical_json, file_record, load_json, verify
from zenithsync.model_intake import inspect_safetensors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    # A new directory prevents accidental replacement of prior evidence.
    args.output.mkdir(parents=True, exist_ok=False)
    sources = ["zenithsync/model_intake.py", "zenithsync/artifacts.py",
               "zenithsync/contracts.py", "tests/test_model_intake.py",
               "tests/test_foundation.py", "scripts/verify_model_storage.py"]
    identity = {name: file_record(ROOT / name) for name in sources}
    result = subprocess.run([sys.executable, "-m", "unittest", "discover",
                             "-s", "tests", "-v"], cwd=ROOT,
                            capture_output=True, text=True, timeout=120)
    (args.output / "tests.log").write_text(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError("tests failed; inspect tests.log")
    manifest = load_json(args.manifest)
    manifest_identity = file_record(args.manifest)
    verify(args.model_dir, manifest)
    inspection = inspect_safetensors(args.model_dir / "model.safetensors")
    if identity != {name: file_record(ROOT / name) for name in sources}:
        raise RuntimeError("validation sources changed during run")
    if manifest_identity != file_record(args.manifest):
        raise RuntimeError("manifest changed during run")
    receipt = {"schema_version": 1,
               "timestamp_utc": datetime.now(timezone.utc).isoformat(),
               "status": "storage_checks_passed",
               "model_manifest": manifest_identity, "sources": identity,
               "inspection": inspection,
               "limitations": ["Input directory must remain quiescent",
                               "No numerical weight scan",
                               "No GPU inference or adapter training",
                               "Local hashes do not authenticate publisher provenance"]}
    (args.output / "receipt.json").write_bytes(canonical_json(receipt))
    print("Storage verification passed; receipt written. GPU validation remains pending.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
