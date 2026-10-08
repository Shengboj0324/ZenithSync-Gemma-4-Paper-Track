"""Validate declared split isolation; semantic contamination needs a later audit."""

from .contracts import digest


def validate_splits(value: object) -> dict:
    if not isinstance(value, dict) or set(value) != {"schema_version", "status", "tasks"}:
        raise ValueError("invalid split manifest")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1:
        raise ValueError("unsupported split schema")
    if value["status"] not in ("draft", "frozen") or not isinstance(value["tasks"], list):
        raise ValueError("invalid split status or tasks")
    if value["status"] == "frozen" and not value["tasks"]:
        raise ValueError("cannot freeze an empty cohort")
    identifiers = set()
    groups = {}
    for task in value["tasks"]:
        required = {"task_id", "repository_group", "leakage_group", "split", "input_sha256"}
        if not isinstance(task, dict) or set(task) != required:
            raise ValueError("invalid task fields")
        for key in required:
            if not isinstance(task[key], str) or not task[key].strip():
                raise ValueError(f"invalid task {key}")
        digest(task["input_sha256"])
        if task["split"] not in ("train", "development", "confirmation"):
            raise ValueError("unknown split")
        if task["task_id"] in identifiers:
            raise ValueError("duplicate task ID")
        identifiers.add(task["task_id"])
        # Content, repository, and known duplicate/fork families cannot cross splits.
        for key in ("repository_group", "leakage_group", "input_sha256"):
            group = (key, task[key])
            if group in groups and groups[group] != task["split"]:
                raise ValueError(f"cross-split leakage in {key}")
            groups[group] = task["split"]
    return {"status": value["status"], "task_count": len(identifiers)}
