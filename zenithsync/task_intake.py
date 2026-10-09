"""Strict official-task projection: evaluator patches never enter agent inputs."""

import json
from pathlib import Path
import re

from .artifacts import _pairs, canonical_json


FIELDS = {"instance_id", "repo", "base_commit", "created_at", "hints_text",
          "problem_statement", "patch", "test_patch"}
AGENT_FIELDS = ("instance_id", "repo", "base_commit", "problem_statement")
MAX_LINE_BYTES = 16 * 1024 * 1024


def load_official_tasks(path: Path) -> list[dict]:
    """Read a bounded JSONL index and fail closed on schema drift or duplicates."""
    rows, seen = [], set()
    with path.open("rb") as stream:
        while raw := stream.readline(MAX_LINE_BYTES + 1):
            if len(raw) > MAX_LINE_BYTES:
                raise ValueError("task row exceeds byte limit")
            if not raw.strip():
                raise ValueError("blank task row")
            row = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs)
            if not isinstance(row, dict) or set(row) != FIELDS:
                raise ValueError("unexpected official task fields")
            if any(not isinstance(value, str) for value in row.values()):
                raise ValueError("task fields must be strings")
            if any(not row[key].strip() for key in FIELDS - {"hints_text"}):
                raise ValueError("required task field is empty")
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", row["instance_id"]):
                raise ValueError("invalid task identifier")
            if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", row["repo"]):
                raise ValueError("invalid repository identifier")
            if not re.fullmatch(r"[0-9a-f]{40}", row["base_commit"]):
                raise ValueError("task requires an exact Git commit")
            if row["instance_id"] in seen:
                raise ValueError("duplicate task identifier")
            seen.add(row["instance_id"])
            rows.append(row)
            if len(rows) > 10000:
                raise ValueError("task index exceeds row limit")
    if not rows:
        raise ValueError("empty task index")
    return rows


def agent_input(task: dict) -> dict:
    """Explicit allowlist; callers must first validate the official index.

    Excludes hints as well as patches. This is structural separation, not a
    semantic guarantee that arbitrary issue text contains no answer clues.
    """
    return {key: task[key] for key in AGENT_FIELDS}


def select_pilot(rows: list[dict], repository: str) -> tuple[dict, dict]:
    """Select by identifier only and reserve the entire pilot repository for dev.

    Does not freeze a confirmation split or use outcome/patch content to select.
    """
    candidates = sorted((row for row in rows if row["repo"] == repository),
                        key=lambda row: row["instance_id"])
    if not candidates:
        raise ValueError("pilot repository is absent")
    pilot = candidates[0]
    reservation = {"schema_version": 1, "status": "development_reservation",
                   "selection_rule": "lexicographically first task ID in chosen repository",
                   "pilot_id": pilot["instance_id"], "repository": repository,
                   "excluded_from_confirmation": [r["instance_id"] for r in candidates],
                   "confirmation_split_frozen": False}
    return agent_input(pilot), reservation


def jsonl_bytes(rows: list[dict]) -> bytes:
    return b"".join(canonical_json(row) for row in rows)
