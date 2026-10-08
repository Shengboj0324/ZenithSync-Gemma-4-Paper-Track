"""Execute an independent, bounded baseline trial on a clean upstream snapshot.

The filesystem separation removes nearby answer files and Git history. The
scope instructions are not a proof of read isolation or training-data novelty.
"""

import argparse
import hashlib
import io
import json
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("trial")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    manifest = json.loads((root / "evidence/manifest.json").read_text())
    workspace = Path(tempfile.mkdtemp(prefix="gemma-r1-baseline-"))
    data = subprocess.check_output(["git", "-C", str(root / "artifacts/raft-upstream"),
                                    "archive", manifest["base_commit"]])
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        archive.extractall(workspace, filter="data")
    subprocess.run(["git", "init", "-q", str(workspace)], check=True)
    subprocess.run(["git", "-C", str(workspace), "add", "."], check=True)
    subprocess.run(["git", "-C", str(workspace), "-c", "user.name=Reproduction",
                    "-c", "user.email=reproduction@localhost", "commit", "-qm", "Baseline snapshot"], check=True)
    prompt = (root / "baseline-prompt.txt").read_text()
    out = root / "evidence" / args.trial
    if out.exists():
        raise FileExistsError(out)
    descriptor = root / "evidence" / (args.trial + "-input.json")
    if descriptor.exists():
        raise FileExistsError(descriptor)
    descriptor.write_text(json.dumps({"workspace": str(workspace),
        "model_requested": "gpt-6.1-sol", "reasoning_effort": "high",
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "source_archive_sha256": hashlib.sha256(data).hexdigest(),
        "base_commit": manifest["base_commit"],
        "limits": "600 seconds; no external diagnosis/reference materials; instruction-level read boundary"}, indent=2) + "\n")
    command = [sys.executable, str(root / "run_command.py"), "--cwd", str(workspace),
               "--out", str(out), "--timeout", "600", "--", "codex", "exec",
               "--ignore-user-config", "--ephemeral", "--json", "-s", "workspace-write",
               "-m", "gpt-6.1-sol", "-c", "model_reasoning_effort=\"high\"",
               "-c", "project_doc_max_bytes=0", "--disable", "memories", prompt]
    subprocess.run(command, check=True)
    patch = subprocess.check_output(["git", "-C", str(workspace), "diff", "HEAD", "--binary"])
    (out / "patch.diff").write_bytes(patch)
    status = subprocess.check_output(["git", "-C", str(workspace), "status", "--porcelain"])
    (out / "git-status.txt").write_bytes(status)
    print("Baseline workspace:", workspace)


if __name__ == "__main__":
    main()
