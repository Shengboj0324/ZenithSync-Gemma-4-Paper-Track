"""Run R0 tests and an isolated offline CLI smoke test; retain a fresh receipt.

Usage: python3 scripts/verify_r0.py --output evidence/r0/<new-run-directory>
No model calls or remote resources are used. Existing receipts are never replaced.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import zipapp


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    args.output.mkdir(parents=True, exist_ok=False)
    started = datetime.now(timezone.utc).isoformat()
    start_ns = time.monotonic_ns()
    sources = {}
    for folder in ("zenithsync", "tests", "scripts", "examples"):
        for path in sorted((root / folder).rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                sources[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    completed = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
                               cwd=root, capture_output=True, timeout=120)
    log = completed.stdout + completed.stderr
    (args.output / "tests.log").write_bytes(log)
    # Packaging smoke uses only source files, without installed site-packages,
    # inherited PYTHONPATH, network downloads, or the repository as working dir.
    with tempfile.TemporaryDirectory() as temporary:
        temp = Path(temporary)
        staged = temp / "stage"
        shutil.copytree(root / "zenithsync", staged / "zenithsync",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        (staged / "__main__.py").write_text(
            "from zenithsync.__main__ import main\nraise SystemExit(main())\n"
        )
        executable = temp / "zenithsync.pyz"
        zipapp.create_archive(staged, executable)
        smoke = subprocess.run([sys.executable, "-I", str(executable), "check-splits",
                                str(root / "examples/splits.draft.json")],
                               cwd=temp, capture_output=True, timeout=30)
        invalid = temp / "invalid.json"
        invalid.write_text('{"schema_version":1,"status":"frozen","tasks":[]}')
        rejected = subprocess.run([sys.executable, "-I", str(executable), "check-splits", str(invalid)],
                                  cwd=temp, capture_output=True, timeout=30)
    (args.output / "offline-smoke.stdout").write_bytes(smoke.stdout)
    (args.output / "offline-smoke.stderr").write_bytes(smoke.stderr)
    try:
        smoke_valid = (smoke.returncode == 0 and json.loads(smoke.stdout) ==
                       {"status": "draft", "task_count": 0}
                       and rejected.returncode == 2 and rejected.stdout == b"")
    except (ValueError, UnicodeError):
        smoke_valid = False
    (args.output / "offline-rejection.stderr").write_bytes(rejected.stderr)
    receipt = {
        "schema_version": 1, "evidence_kind": "synthetic_foundation_validation",
        "started_utc": started, "finished_utc": datetime.now(timezone.utc).isoformat(),
        "elapsed_ns": time.monotonic_ns() - start_ns,
        "python": sys.version, "platform": platform.platform(),
        "source_sha256": sources, "tests_returncode": completed.returncode,
        "tests_log_sha256": hashlib.sha256(log).hexdigest(),
        "offline_smoke_passed": smoke_valid,
        "offline_rejection_returncode": rejected.returncode,
        "official_harness_compatibility": "unverified",
        "gemma_inference": "not_run", "repair_performance": "not_measured",
    }
    (args.output / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    sys.stdout.write(log.decode("utf-8", errors="replace"))
    print(f"Offline isolated CLI: {'passed' if smoke_valid else 'failed'}")
    print(f"Receipt: {args.output / 'receipt.json'}")
    return 0 if completed.returncode == 0 and smoke_valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
