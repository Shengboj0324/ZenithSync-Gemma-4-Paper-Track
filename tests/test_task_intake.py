"""Synthetic official-schema fixtures, with explicit leakage sentinels."""

import json
from pathlib import Path
import tempfile
import unittest

from zenithsync.task_intake import agent_input, jsonl_bytes, load_official_tasks, select_pilot


def row(identifier="repo_2", repository="owner/repo"):
    return {"instance_id": identifier, "repo": repository, "base_commit": "a" * 40,
            "created_at": "2026-01-01T00:00:00Z", "hints_text": "SECRET_HINT_SENTINEL",
            "problem_statement": "Synthetic task description",
            "patch": "SECRET_FIX_SENTINEL", "test_patch": "SECRET_TEST_SENTINEL"}


class TaskIntakeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "tasks.jsonl"

    def test_only_allowlisted_fields_reach_agent(self):
        self.path.write_bytes(jsonl_bytes([row()]))
        value = agent_input(load_official_tasks(self.path)[0])
        self.assertEqual(set(value), {"instance_id", "repo", "base_commit", "problem_statement"})
        self.assertNotIn(b"SECRET_", jsonl_bytes([value]))

    def test_pilot_selection_and_repository_reservation(self):
        rows = [row(), row("repo_1"), row("other_1", "owner/other")]
        pilot, reservation = select_pilot(rows, "owner/repo")
        self.assertEqual(pilot["instance_id"], "repo_1")
        self.assertEqual(reservation["excluded_from_confirmation"], ["repo_1", "repo_2"])
        self.assertFalse(reservation["confirmation_split_frozen"])
        self.assertEqual(select_pilot(list(reversed(rows)), "owner/repo"), (pilot, reservation))

    def test_duplicate_ids_and_schema_drift_rejected(self):
        for rows in ([row(), row()], [{**row(), "new_gold_field": "secret"}],
                     [{k:v for k,v in row().items() if k != "patch"}]):
            self.path.write_bytes(jsonl_bytes(rows))
            with self.assertRaises(ValueError):
                load_official_tasks(self.path)

    def test_malformed_identity_and_types_rejected(self):
        for field, value in [("instance_id", "../escape"), ("base_commit", "main"),
                             ("repo", "single"), ("patch", None), ("test_patch", "")]:
            with self.subTest(field=field):
                self.path.write_text(json.dumps({**row(), field:value}) + "\n")
                with self.assertRaises(ValueError):
                    load_official_tasks(self.path)

    def test_duplicate_keys_and_empty_rows_rejected(self):
        for raw in (b"", b"\n", b'{"instance_id":"a","instance_id":"b"}\n'):
            self.path.write_bytes(raw)
            with self.assertRaises(ValueError):
                load_official_tasks(self.path)


if __name__ == "__main__":
    unittest.main()
