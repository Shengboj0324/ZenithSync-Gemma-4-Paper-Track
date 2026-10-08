"""Acquire pinned upstream snapshots; never execute upstream setup scripts."""

import io
import subprocess
import tarfile
from pathlib import Path

BASE = "9a647f6c2bb9e057c49b85176086ab94a210c09d"
REFERENCE = "2e997410f28efe8106fc606d21cb655be1b05dee"


def main():
    root = Path(__file__).resolve().parent
    upstream = root / "artifacts/raft-upstream"
    if not upstream.exists():
        upstream.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--quiet", "https://github.com/hashicorp/raft.git",
                        str(upstream)], check=True)
    for label, revision in (("original", BASE), ("reference", REFERENCE)):
        resolved = subprocess.check_output(["git", "-C", str(upstream), "rev-parse", revision], text=True).strip()
        if resolved != revision:
            raise ValueError("Pinned source did not resolve exactly")
        target = root / "workspaces" / label
        target.mkdir(parents=True, exist_ok=False)
        data = subprocess.check_output(["git", "-C", str(upstream), "archive", revision])
        with tarfile.open(fileobj=io.BytesIO(data)) as archive:
            archive.extractall(target, filter="data")
        (target / "r1_regression_test.go").write_bytes((root / "shutdown_regression_test.go").read_bytes())
        print(label, revision, target)


if __name__ == "__main__":
    main()
