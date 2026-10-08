"""Run a bounded experiment command and preserve its exit status and raw output."""

import argparse
import datetime
import hashlib
import json
import os
import signal
import subprocess
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cwd", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=180)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command
    if command[:1] == ["--"]:
        command = command[1:]
    if not command or args.timeout <= 0:
        parser.error("a command and positive timeout are required")
    args.out.mkdir(parents=True, exist_ok=False)
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    start = time.monotonic()
    timed_out = False
    with (args.out / "stdout.txt").open("wb") as stdout, (args.out / "stderr.txt").open("wb") as stderr:
        process = subprocess.Popen(command, cwd=args.cwd, stdout=stdout,
                                   stderr=stderr, start_new_session=True)
        try:
            code = process.wait(timeout=args.timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            code = process.wait()
    receipt = {"command": command, "cwd": str(args.cwd.resolve()),
               "started_at": started, "wall_seconds": time.monotonic() - start,
               "timeout_seconds": args.timeout, "timed_out": timed_out,
               "returncode": code}
    receipt["sha256"] = {name: hashlib.sha256((args.out / name).read_bytes()).hexdigest()
                         for name in ("stdout.txt", "stderr.txt")}
    (args.out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
