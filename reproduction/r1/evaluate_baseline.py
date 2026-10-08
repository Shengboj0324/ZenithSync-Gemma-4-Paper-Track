"""Evaluate production changes in a fresh tree with immutable upstream tests."""

import argparse
import hashlib
import io
import json
import subprocess
import sys
import tarfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("trial")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    descriptor = json.loads((root / "evidence" / (args.trial + "-input.json")).read_text())
    workspace = Path(descriptor["workspace"])
    receipt = json.loads((root / "evidence" / args.trial / "receipt.json").read_text())
    if receipt["timed_out"] or receipt["returncode"] != 0:
        raise RuntimeError("Baseline process did not complete normally; inspect trace before evaluation")
    target = root / "workspaces" / (args.trial + "-evaluation")
    target.mkdir(parents=True, exist_ok=False)
    archive_bytes = subprocess.check_output(["git", "-C", str(root / "artifacts/raft-upstream"),
                                             "archive", descriptor["base_commit"]])
    with tarfile.open(fileobj=io.BytesIO(archive_bytes)) as archive:
        archive.extractall(target, filter="data")
    names = subprocess.check_output(["git", "-C", str(workspace), "diff", "--name-only", "HEAD"], text=True).splitlines()
    names += subprocess.check_output(["git", "-C", str(workspace), "ls-files", "--others", "--exclude-standard"], text=True).splitlines()
    changes = []
    excluded_build_files = 0
    for name in sorted(set(names)):
        if name.startswith((".test-go-cache/", ".go-build/", ".go-cache/")):
            excluded_build_files += 1
            continue
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Invalid patch path")
        source = workspace / relative
        if source.is_symlink():
            raise ValueError("Symlinks require separate review")
        record = {"path": name}
        if name.endswith("_test.go") or name.endswith(".md") or name in ("race-tests.log", "batch-tests.log", "peerchange-test.log"):
            record["disposition"] = "retained for audit; not applied to evaluator"
        elif not name.endswith(".go"):
            raise ValueError("Non-Go production change requires separate review: " + name)
        elif source.is_file():
            contents = source.read_bytes()
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(contents)
            record.update(disposition="applied", sha256=hashlib.sha256(contents).hexdigest())
        else:
            raise ValueError("Production deletion requires separate review: " + name)
        changes.append(record)
        if source.is_file():
            saved = root / "evidence" / args.trial / "changed-files" / relative
            saved.parent.mkdir(parents=True, exist_ok=True)
            saved.write_bytes(source.read_bytes())
    fixture = (root / "shutdown_regression_test.go").read_bytes()
    (target / "r1_regression_test.go").write_bytes(fixture)
    (root / "evidence" / (args.trial + "-changes.json")).write_text(json.dumps(
        {"changes": changes, "excluded_go_build_cache_files": excluded_build_files}, indent=2) + "\n")
    command = [sys.executable, str(root / "run_command.py"), "--cwd", str(target),
               "--out", str(root / "evidence" / (args.trial + "-evaluation")), "--timeout", "180", "--",
               "go", "test", "-race", "-json", "-run",
               "^TestR1|^TestRaft_(AfterShutdown|UserSnapshot|AutoSnapshot|SnapshotRestore)$",
               "-count=3", "-timeout=150s", "."]
    subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
