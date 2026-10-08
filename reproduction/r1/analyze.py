"""Derive descriptive results from receipts, never from agent success claims."""

import collections
import hashlib
import json
import statistics
from pathlib import Path


def read_events(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def checked_receipt(directory):
    receipt = json.loads((directory / "receipt.json").read_text())
    for name, expected in receipt["sha256"].items():
        actual = hashlib.sha256((directory / name).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError("Evidence hash mismatch: " + str(directory / name))
    return receipt


def test_outcome(directory):
    receipt = checked_receipt(directory)
    events = read_events(directory / "stdout.txt")
    counts = collections.Counter((event["Test"], event["Action"]) for event in events
        if "Test" in event and event.get("Action") in ("pass", "fail", "skip"))
    return {"returncode": receipt["returncode"], "timed_out": receipt["timed_out"],
            "wall_seconds": receipt["wall_seconds"],
            "tests": [{"name": test, "action": action, "count": count}
                      for (test, action), count in sorted(counts.items())]}


def main():
    root = Path(__file__).resolve().parent / "evidence"
    required_tests = {"TestR1ShutdownWithPendingSnapshot", "TestR1NormalSnapshotPreservesData",
        "TestR1SnapshotAfterShutdown", "TestRaft_AfterShutdown", "TestRaft_SnapshotRestore",
        "TestRaft_AutoSnapshot", "TestRaft_UserSnapshot"}
    trials = []
    for name in ("baseline-01", "baseline-02", "baseline-03"):
        receipt = checked_receipt(root / name)
        events = read_events(root / name / "stdout.txt")
        finished = [event for event in events if event.get("type") == "turn.completed"]
        if len(finished) != 1:
            raise ValueError("Expected one completed baseline turn: " + name)
        outcome = test_outcome(root / (name + "-evaluation"))
        passes = {entry["name"] for entry in outcome["tests"]
                  if entry["action"] == "pass" and entry["count"] == 3}
        success = (receipt["returncode"] == 0 and not receipt["timed_out"]
                   and outcome["returncode"] == 0 and not outcome["timed_out"]
                   and required_tests <= passes)
        completed_commands = [event["item"] for event in events
            if event.get("type") == "item.completed"
            and event.get("item", {}).get("type") == "command_execution"]
        trials.append({"trial": name, "targeted_repair_success": success,
            "agent_wall_seconds": receipt["wall_seconds"], "usage": finished[0].get("usage"),
            "completed_shell_commands": len(completed_commands),
            "nonzero_shell_commands": sum(item.get("exit_code") != 0 for item in completed_commands),
            "evaluation": outcome})
    controls = {name: test_outcome(root / name) for name in
        ("original-race", "reference-race", "disabled-snapshots-control", "reference-full", "baseline-01-full", "baseline-03-full")}
    times = [trial["agent_wall_seconds"] for trial in trials]
    result = {"scope": "One historical bug; three baseline attempts; no proposed-method comparison",
        "trials": trials, "controls": controls,
        "targeted_successes": sum(trial["targeted_repair_success"] for trial in trials),
        "attempts": len(trials), "median_agent_seconds": statistics.median(times),
        "min_agent_seconds": min(times), "max_agent_seconds": max(times),
        "total_agent_seconds": sum(times),
        "comparative_method_lift": None, "gemma_performance": None,
        "monetary_cost": None,
        "uncertainty": "No cross-task inference from these repeats; service sampling and training exposure are uncontrolled."}
    (root / "analysis.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: value for key, value in result.items() if key not in ("trials", "controls")}, indent=2))


if __name__ == "__main__":
    main()
