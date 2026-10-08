"""Exercise released swegemma tools on synthetic fixtures in real Linux containers.

No LLM calls, competition task fixes, training or performance estimates. Containers
have no network or host mounts. Only containers created by this run are removed.
"""

import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

from adk_submission import ModelRegistry, compile_submission
from swegemma.config import build_submission_limits
from docker.errors import NotFound
from swegemma.context import SwegemmaContext
from swegemma.sandbox import ContainerConfig, ContainerManager


SEED = {
    "arithmetic.py": "def add(a, b):\n    return a - b\n",
    "test_arithmetic.py": "from arithmetic import add\n\ndef test_add():\n    assert add(7, 3) == 10\n",
    "obsolete.txt": "synthetic obsolete file\n",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    # Follow the selected Docker context without changing global settings.
    if "DOCKER_HOST" not in os.environ:
        host = subprocess.check_output(
            ["docker", "context", "inspect", "--format", "{{.Endpoints.docker.Host}}"],
            text=True, timeout=15,
        ).strip()
        if not host:
            raise RuntimeError("Docker context has no endpoint")
        os.environ["DOCKER_HOST"] = host
    manager = ContainerManager(ContainerConfig(image=args.image, reuse_containers=False))
    image = manager.client.images.get(args.image)
    manager.config.image = image.id
    created = []
    records = []
    started = datetime.now(timezone.utc).isoformat()
    start_ns = time.monotonic_ns()
    failure = None

    def check(name, condition, detail=None):
        records.append({"check": name, "passed": bool(condition), "detail": detail})
        if not condition:
            raise AssertionError(name)

    def call(tools, name, **kwargs):
        result = tools[name](**kwargs)
        records.append({"tool": name, "arguments": kwargs, "response": result})
        return result

    def new_container():
        cid = manager.start()
        created.append(cid)
        config = manager.client.containers.get(cid).attrs["HostConfig"]
        check("network_and_resource_limits", config["NetworkMode"] == "none"
              and config["Memory"] == 4 * 1024**3 and config["CpuQuota"] == 200000,
              {k: config[k] for k in ("NetworkMode", "Memory", "CpuQuota")})
        with tempfile.TemporaryDirectory() as temporary:
            staging = Path(temporary)
            for name, content in SEED.items():
                file = staging / name
                file.write_text(content)
                manager.copy_to(cid, file, "/workspace/" + name)
        initialized = manager.exec(cid, "git init -q && printf '__pycache__/\\n.pytest_cache/\\n' > .git/info/exclude && git add . && git commit -qm baseline && git tag _swegemma_baseline")
        check("seed_initialized", initialized.exit_code == 0, initialized.stderr)
        return cid

    try:
        cid = new_container()
        ctx = SwegemmaContext(docker_manager=manager, container_id=cid,
                             task_id="synthetic-r0", repo="synthetic/r0",
                             max_tool_calls=40, max_time_minutes=5, max_exec_seconds=30,
                             graph_dir="/nonexistent-r0-graphs", embeddings_dir="/nonexistent-r0-embeddings")
        ctx.start_agent_session()
        tools = ctx.create_tools()
        check("nine_actual_bound_tools", len(tools) == 9, sorted(tools))
        models = ModelRegistry()
        model = "gemma-4-31b-it-qat-w4a16-ct"
        models.register(model, model)
        limits, generation = build_submission_limits()
        starter = Path(__file__).resolve().parents[1] / "artifacts/official/gemma-4-developer-agent/sample_submission"
        agent = compile_submission(starter, tool_registry=tools, model_registry=models,
                                   limits=limits, generation_constraints=generation)
        check("starter_compiles_with_real_bound_tools", agent.name == "swe_baseline_agent" and len(agent.tools) == 10)
        status = call(tools, "get_status")
        check("status_does_not_consume_call", status["tool_calls_used"] == 0)
        failed = call(tools, "run_command", command="python -m pytest -q test_arithmetic.py")
        check("unfixed_fixture_fails", failed["status"] == "error"
              and failed["details"]["exit_code"] == 1, failed)
        read = call(tools, "read_file", filepath="arithmetic.py", start_line=1, end_line=1)
        check("inclusive_line_read", read["content"].strip() == "def add(a, b):")
        escaped = call(tools, "write_file", filepath="../escape.txt", content="synthetic")
        check("path_escape_rejected", escaped["status"] == "error", escaped)
        call(tools, "write_file", filepath="ambiguous.txt", content="same same\n")
        ambiguous = call(tools, "edit_file", filepath="ambiguous.txt", old_string="same", new_string="different")
        check("ambiguous_edit_rejected", ambiguous["status"] == "error", ambiguous)
        unchanged = call(tools, "read_file", filepath="ambiguous.txt")
        check("failed_edit_is_unchanged", unchanged["content"] == "same same" and manager.exec(cid, "cat ambiguous.txt").stdout == "same same\n")
        edited = call(tools, "edit_file", filepath="arithmetic.py", old_string="return a - b", new_string="return a + b")
        check("exact_edit", edited["status"] == "ok" and edited["strategy"] == "exact", edited)
        written = call(tools, "write_file", filepath="added.txt", content="synthetic new file\n")
        check("new_file_written", written["status"] == "ok")
        removed = call(tools, "run_command", command="rm obsolete.txt ambiguous.txt && python -m pytest -q test_arithmetic.py")
        check("fixed_fixture_passes", removed["status"] == "ok", removed)
        # Missing graph assets must not be mistaken for evidence about source code.
        for name, kwargs in (("get_code_neighbors", {"node": "add"}),
                             ("search_similar_code", {"query": "add"}),
                             ("get_code_subgraph", {"nodes": ["add"]})):
            result = call(tools, name, **kwargs)
            check(name + "_missing_assets", result["status"] == "error", result)
        timed = SwegemmaContext(docker_manager=manager, container_id=cid,
                               max_tool_calls=1, max_time_minutes=1, max_exec_seconds=1)
        timed.start_agent_session()
        timeout = call(timed.create_tools(), "run_command", command="python -c 'import time; time.sleep(3)'")
        check("command_timeout", timeout.get("error_type") == "TimeoutExceeded", timeout)
        exhausted = SwegemmaContext(docker_manager=manager, container_id=cid,
                                   max_tool_calls=0, max_time_minutes=1)
        exhausted.start_agent_session()
        limited_tools = exhausted.create_tools()
        denied = call(limited_tools, "write_file", filepath="denied.txt", content="must not exist")
        check("exhausted_budget_denies_mutation", denied["status"] == "error", denied)
        check("denied_file_absent", manager.exec(cid, "test ! -e denied.txt").exit_code == 0)
        submitted = call(limited_tools, "submit_patch")
        check("submit_survives_call_exhaustion", submitted["status"] == "ok"
              and exhausted.tool_calls_used == 0, submitted)
        patch = exhausted.submitted_patch
        check("modified_added_deleted_files_captured", all(x in patch for x in (
            "diff --git a/arithmetic.py b/arithmetic.py", "new file mode", "deleted file mode")))
        patch_file = args.output / "synthetic.patch"
        patch_file.write_text(patch)
        fresh = new_container()
        original = manager.exec(fresh, "python -m pytest -q test_arithmetic.py")
        check("fresh_container_still_unfixed", original.exit_code == 1, original.stdout)
        manager.copy_to(fresh, patch_file, "/tmp/candidate.patch")
        applied = manager.exec(fresh, "git apply /tmp/candidate.patch && python -m pytest -q test_arithmetic.py")
        check("captured_patch_passes_in_fresh_container", applied.exit_code == 0, applied.stdout + applied.stderr)
    except Exception as error:
        failure = {"type": type(error).__name__, "message": str(error)}
    finally:
        for cid in created:
            manager.stop(cid)
        remaining = []
        for cid in created:
            try:
                manager.client.containers.get(cid)
            except NotFound:
                continue
            remaining.append(cid)
        receipt = {
            "schema_version": 1, "started_utc": started,
            "finished_utc": datetime.now(timezone.utc).isoformat(),
            "elapsed_ns": time.monotonic_ns() - start_ns,
            "evidence_kind": "synthetic_real_tool_linux_integration",
            "image_id": image.id, "image_architecture": image.attrs["Architecture"],
            "packages": {n: version(n) for n in ("swegemma", "adk-submission", "adk-eval-core", "google-adk")},
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "records": records, "failure": failure, "remaining_containers": remaining,
            "model_inference": "not_run", "competition_repair_performance": "not_measured",
            "official_phase_two_grading": "not_run",
        }
        (args.output / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": sum("check" in r for r in records),
                      "failure": failure, "remaining_containers": remaining}, indent=2))
    return 0 if failure is None and not remaining else 1


if __name__ == "__main__":
    raise SystemExit(main())
