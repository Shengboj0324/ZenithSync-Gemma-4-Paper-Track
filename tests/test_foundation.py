"""Synthetic contract tests, never evidence of model or repair performance."""

from dataclasses import asdict
import hashlib
import itertools
import json
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
import zipfile

from zenithsync.archive import inspect_zip
from zenithsync.artifacts import canonical_json, inventory, load_json, verify
from zenithsync.contracts import Budget, Event, Kind, Phase, TaskState, context_fits, replay
from zenithsync.splits import validate_splits


A = hashlib.sha256(b"synthetic candidate A").hexdigest()
B = hashlib.sha256(b"synthetic candidate B").hexdigest()
RECEIPT = hashlib.sha256(b"synthetic runner receipt").hexdigest()


class BudgetTests(unittest.TestCase):
    def test_exhaustive_admission_matches_discrete_capacity(self):
        for limit in range(12):
            for reserve in range(limit + 1):
                for charged, requested in itertools.product(range(15), repeat=2):
                    budget = Budget(limit, reserve, charged)
                    # Independent finite-slot reference (including overdrawn budgets).
                    slots = list(range(limit))[charged:]
                    expected = charged <= limit and len(slots) >= reserve + requested
                    self.assertEqual(budget.admits(requested), expected)
                    self.assertEqual(budget.available_ns, max(0, len(slots) - reserve))

    def test_charges_compose_without_losing_overruns(self):
        for first, second in itertools.product(range(15), repeat=2):
            initial = Budget(10, 2)
            actual = initial.charge(first).charge(second)
            self.assertEqual(actual, initial.charge(first + second))
            self.assertEqual(actual.overrun_ns, max(0, first + second - 10))
        huge = 10**80
        self.assertTrue(Budget(huge, 1, huge - 2).admits(1))
        self.assertFalse(Budget(huge, 1, huge - 2).admits(2))

    def test_invalid_numeric_types(self):
        for invalid in (True, False, -1, 1.0, float("nan"), float("inf"), "1", None):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    Budget(invalid, 0)
                with self.assertRaises(ValueError):
                    Budget(10, 0).charge(invalid)
                with self.assertRaises(ValueError):
                    Budget(10, 0).admits(invalid)
        with self.assertRaises(ValueError):
            Budget(2, 3)

    def test_context_boundary(self):
        for counts in itertools.product(range(5), repeat=3):
            required = len([None] * counts[0] + [None] * counts[1] + [None] * counts[2])
            for limit in range(15):
                self.assertEqual(context_fits(input_tokens=counts[0], output_tokens=counts[1],
                                             protocol_tokens=counts[2], limit_tokens=limit),
                                 required <= limit)


class StateTests(unittest.TestCase):
    def started(self):
        return TaskState().apply(Event(0, Kind.START))

    def test_stale_checks_rejected_and_status_cleared(self):
        state = self.started().apply(Event(1, Kind.CANDIDATE, candidate_sha256=A))
        state = state.apply(Event(2, Kind.CHECK, RECEIPT, A, True))
        self.assertTrue(state.check_passed)
        state = state.apply(Event(3, Kind.CANDIDATE, candidate_sha256=B))
        self.assertIsNone(state.check_passed)
        self.assertIsNone(state.check_receipt_sha256)
        for kind in (Kind.CHECK, Kind.SUBMIT):
            with self.assertRaises(ValueError):
                state.apply(Event(4, kind, RECEIPT, A, False if kind == Kind.CHECK else None))

    def test_submit_does_not_invent_success(self):
        state = self.started().apply(Event(1, Kind.CANDIDATE, candidate_sha256=A))
        submitted = state.apply(Event(2, Kind.SUBMIT, RECEIPT, A))
        self.assertEqual(submitted.phase, Phase.SUBMITTED)
        self.assertIsNone(submitted.check_passed)
        with self.assertRaises(ValueError):
            submitted.apply(Event(3, Kind.OBSERVATION, RECEIPT))

    def test_latest_check_can_fail(self):
        state = self.started().apply(Event(1, Kind.CANDIDATE, candidate_sha256=A))
        state = state.apply(Event(2, Kind.CHECK, RECEIPT, A, True))
        self.assertFalse(state.apply(Event(3, Kind.CHECK, RECEIPT, A, False)).check_passed)

    def test_replay_and_sequence_integrity(self):
        events = [Event(0, Kind.START), Event(1, Kind.HYPOTHESIS, RECEIPT),
                  Event(2, Kind.OBSERVATION, RECEIPT), Event(3, Kind.STOP, RECEIPT)]
        self.assertEqual(replay(events).phase, Phase.STOPPED)
        for invalid in (events + [events[-1]], events[1:], events[:1] + events[2:]):
            with self.assertRaises(ValueError):
                replay(invalid)
        with self.assertRaises(ValueError):
            self.started().apply(Event(1, Kind.START))

    def test_event_shapes(self):
        for kwargs in ({"kind": "start"}, {"kind": Kind.CHECK},
                       {"kind": Kind.START, "passed": False},
                       {"kind": Kind.CANDIDATE, "candidate_sha256": "bad"},
                       {"kind": Kind.START, "schema_version": True}):
            with self.assertRaises(ValueError):
                Event(sequence=0, **kwargs)

    def test_invalid_state_cannot_be_restored(self):
        for kwargs in ({"phase": "working"}, {"next_sequence": True},
                       {"candidate_sha256": A}, {"phase": Phase.WORKING},
                       {"check_passed": True}, {"check_receipt_sha256": RECEIPT},
                       {"phase": Phase.SUBMITTED, "next_sequence": 2}):
            with self.assertRaises(ValueError):
                TaskState(**kwargs)

    def test_all_event_kinds_at_ready_and_terminal_states(self):
        events = [Event(0, Kind.START), Event(0, Kind.OBSERVATION, RECEIPT),
                  Event(0, Kind.HYPOTHESIS, RECEIPT),
                  Event(0, Kind.CANDIDATE, candidate_sha256=A),
                  Event(0, Kind.CHECK, RECEIPT, A, True),
                  Event(0, Kind.SUBMIT, RECEIPT, A), Event(0, Kind.STOP, RECEIPT)]
        for event in events:
            if event.kind in (Kind.START, Kind.STOP):
                TaskState().apply(event)
            else:
                with self.assertRaises(ValueError):
                    TaskState().apply(event)
            stopped = TaskState().apply(Event(0, Kind.STOP, RECEIPT))
            with self.assertRaises(ValueError):
                stopped.apply(Event(**{**asdict(event), "sequence": 1}))


class FilesystemTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.payload = self.root / "payload"
        self.payload.mkdir()
        (self.payload / "config.json").write_bytes(b"{}\n")

    def manifest(self):
        return inventory(self.payload, kind="fixture", source="synthetic", revision="v1")

    def test_known_digest_and_deterministic_inventory(self):
        first = self.manifest()
        self.assertEqual(first["files"][0]["sha256"], hashlib.sha256(b"{}\n").hexdigest())
        self.assertEqual(first["files"][0]["size_bytes"], 3)
        self.assertEqual(canonical_json(first), canonical_json(self.manifest()))
        verify(self.payload, first)

    def test_changed_extra_missing_files(self):
        manifest = self.manifest()
        target = self.payload / "config.json"
        for mode in ("changed", "missing", "extra"):
            with self.subTest(mode=mode):
                target.write_bytes(b"{}\n")
                if mode == "changed":
                    target.write_bytes(b"[]\n")
                elif mode == "missing":
                    target.unlink()
                else:
                    (self.payload / "extra").write_bytes(b"x")
                with self.assertRaises(ValueError):
                    verify(self.payload, manifest)

    def test_symlink_file_and_directory_rejected(self):
        for destination in (self.payload / "config.json", self.root):
            link = self.payload / "link"
            link.symlink_to(destination)
            with self.assertRaises(ValueError):
                self.manifest()
            link.unlink()

    def test_special_file_rejected(self):
        import os
        os.mkfifo(self.payload / "pipe")
        with self.assertRaises(ValueError):
            self.manifest()

    def test_manifest_schema_rejects_bad_inputs(self):
        for path in ("../x", "/x", "a//b", "./x", "a\\b", "C:x", "x\0y"):
            manifest = self.manifest()
            manifest["files"][0]["path"] = path
            with self.assertRaises(ValueError):
                verify(self.payload, manifest)
        manifest = self.manifest()
        manifest["files"].append(manifest["files"][0])
        with self.assertRaises(ValueError):
            verify(self.payload, manifest)

    def test_strict_json(self):
        path = self.root / "input.json"
        for invalid in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}'):
            path.write_text(invalid)
            with self.assertRaises(ValueError):
                load_json(path)

    def zip(self, records):
        path = self.root / "submission.zip"
        with zipfile.ZipFile(path, "w") as archive:
            for name, data in records:
                archive.writestr(name, data)
        return path

    def inspect(self, path, **kwargs):
        return inspect_zip(path, max_bytes=kwargs.get("max_bytes", 1024),
                           max_entries=kwargs.get("max_entries", 10))

    def test_archive_cannot_claim_official_compatibility(self):
        result = self.inspect(self.zip([("agent.yaml", "synthetic: true\n")]))
        self.assertEqual(result["official_compatibility"], "unverified")
        self.assertEqual(result["yaml_validation"], "not_performed")

    def test_all_official_root_aliases_and_ambiguity(self):
        for root in ("agent.yaml", "agent.yml", "root_agent.yaml", "root_agent.yml"):
            self.inspect(self.zip([(root, "synthetic: true\n")]))
        with self.assertRaises(ValueError):
            self.inspect(self.zip([("agent.yaml", "x"), ("root_agent.yml", "y")]))

    def test_archive_bad_paths(self):
        for name in ("../x", "/x", "a/../x", "a\\b", "a//b", "C:x"):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    self.inspect(self.zip([("agent.yaml", "x"), (name, "y")]))

    def test_archive_conflicts_and_missing_root(self):
        for records in ([('nested/agent.yaml', 'x')], [('agent.yaml', '')],
                        [('agent.yaml', 'x'), ('AGENT.yaml', 'y')],
                        [('agent.yaml', 'x'), ('a', 'y'), ('a/b', 'z')]):
            with self.assertRaises(ValueError):
                self.inspect(self.zip(records))

    def test_archive_limits_and_symlinks(self):
        path = self.zip([("agent.yaml", "123")])
        for limits in ({"max_bytes": 2}, {"max_entries": 0}):
            with self.assertRaises(ValueError):
                self.inspect(path, **limits)
        self.inspect(path, max_bytes=3, max_entries=1)
        link = zipfile.ZipInfo("link")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        with self.assertRaises(ValueError):
            self.inspect(self.zip([("agent.yaml", "x"), (link, "target")]))

    def test_cli_round_trip_and_fail_closed(self):
        prefix = [sys.executable, "-m", "zenithsync"]
        result = subprocess.run(prefix + ["inventory", str(self.payload), "--kind", "fixture",
                                "--source", "synthetic", "--revision", "v1"], capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = self.root / "manifest.json"
        manifest.write_bytes(result.stdout)
        verified = subprocess.run(prefix + ["verify", str(self.payload), str(manifest)], capture_output=True)
        self.assertEqual(verified.returncode, 0, verified.stderr)
        (self.payload / "extra").write_text("change")
        failed = subprocess.run(prefix + ["verify", str(self.payload), str(manifest)], capture_output=True)
        self.assertEqual(failed.returncode, 2)
        self.assertEqual(failed.stdout, b"")
        event_file = self.root / "events.json"
        event_file.write_bytes(canonical_json([asdict(Event(0, Kind.START)),
                                               asdict(Event(1, Kind.STOP, RECEIPT))]))
        replayed = subprocess.run(prefix + ["replay", str(event_file)], capture_output=True)
        self.assertEqual(replayed.returncode, 0, replayed.stderr)
        self.assertEqual(json.loads(replayed.stdout)["phase"], "stopped")


class SplitTests(unittest.TestCase):
    def task(self, **changes):
        return {"task_id": "synthetic-1", "repository_group": "repo-1",
                "leakage_group": "family-1", "split": "train", "input_sha256": A, **changes}

    def test_empty_draft_is_not_frozen_evaluation(self):
        self.assertEqual(validate_splits({"schema_version": 1, "status": "draft", "tasks": []})["task_count"], 0)
        with self.assertRaises(ValueError):
            validate_splits({"schema_version": 1, "status": "frozen", "tasks": []})

    def test_each_leakage_dimension(self):
        for key in ("repository_group", "leakage_group", "input_sha256"):
            original = self.task()
            second = self.task(task_id="synthetic-2", repository_group="repo-2",
                               leakage_group="family-2", input_sha256=B, split="confirmation")
            second[key] = original[key]
            with self.assertRaises(ValueError):
                validate_splits({"schema_version": 1, "status": "frozen", "tasks": [original, second]})

    def test_distinct_splits_and_duplicate_id(self):
        original = self.task()
        second = self.task(task_id="synthetic-2", repository_group="repo-2",
                           leakage_group="family-2", input_sha256=B, split="confirmation")
        manifest = {"schema_version": 1, "status": "frozen", "tasks": [original, second]}
        self.assertEqual(validate_splits(manifest)["task_count"], 2)
        second["task_id"] = original["task_id"]
        with self.assertRaises(ValueError):
            validate_splits(manifest)


if __name__ == "__main__":
    unittest.main()
