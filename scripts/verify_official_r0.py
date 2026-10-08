"""CPU-only contract checks against the downloaded official ADK compiler.

Tool bindings deliberately raise if executed. No model or sandbox is invoked.
Use the acquisition virtual environment, not the dependency-free core runtime.
"""

import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import shutil
import sys
import tempfile
import time

from adk_submission import (
    GenerationConstraints, ModelRegistry, NumericRange, SubmissionLimits,
    compile_submission,
)
from adk_submission.discovery import discover_declared_models
from adk_submission.errors import SubmissionError, SubmissionValidationError
from adk_submission.schema import SandboxedAgentConfig


MODEL = "gemma-4-31b-it-qat-w4a16-ct"
TOOLS = ("run_command", "read_file", "edit_file", "write_file", "get_status",
         "submit_patch", "get_code_neighbors", "search_similar_code", "get_code_subgraph")


def unavailable_tool(name):
    def tool():
        raise RuntimeError("Compilation-only binding; execution is forbidden")
    tool.__name__ = name
    return tool


def compile_only(root: Path):
    recognized = ("agent.yaml", "agent.yml", "root_agent.yaml", "root_agent.yml")
    if sum((root / name).is_file() for name in recognized) != 1:
        raise ValueError("project packaging policy requires exactly one root configuration")
    # Values transcribed from the released swegemma 0.2.7 config.py;
    # full swegemma import/runtime is not exercised by this compiler check.
    limits = SubmissionLimits(
        max_total_size_bytes=3 * 1024**3, max_yaml_size_bytes=50 * 1024**2,
        max_skill_size_bytes=50 * 1024**2, max_file_count=10000,
        max_yaml_files=1000, max_instruction_chars=1000000,
        max_total_instruction_chars=10000000, max_agents=500,
        max_sub_agent_depth=50, max_skills=1000, max_loop_iterations=500,
        allowed_file_extensions=frozenset({".yaml", ".yml", ".md", ".txt", ".py", ".json", ".safetensors"}),
        adapter_extensions=frozenset({".safetensors"}),
    )
    generation = GenerationConstraints(
        allowed_fields=None, max_output_tokens=NumericRange(1, 32768),
        thinking_budget=NumericRange(0, 32768),
        defaults={"max_output_tokens": 16384, "thinking_config": {"thinking_budget": 4096}},
    )
    # Exact alias for this profile. Organizer prefix normalization is not copied.
    if discover_declared_models(root) != {MODEL}:
        raise ValueError("expected the exact competition model alias throughout")
    models = ModelRegistry()
    models.register(MODEL, MODEL)
    return compile_submission(root, tool_registry={n: unavailable_tool(n) for n in TOOLS},
                              model_registry=models, limits=limits,
                              generation_constraints=generation)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    packages = {name: version(name) for name in ("adk-submission", "google-adk", "pydantic", "PyYAML")}
    if packages["adk-submission"] != "0.2.12" or packages["google-adk"] != "1.36.1":
        raise ValueError("official compiler profile version mismatch")
    original = (args.assets / "sample_submission").resolve()
    args.output.mkdir(parents=True, exist_ok=False)
    started = datetime.now(timezone.utc).isoformat()
    start_ns = time.monotonic_ns()
    results = []
    agent = compile_only(original)
    if agent.name != "swe_baseline_agent" or len(agent.tools) != 10:
        raise AssertionError("unexpected starter tree")
    results.append({"case": "unchanged_official_starter", "passed": True,
                    "agent_class": type(agent).__name__, "tools": len(agent.tools)})
    # Each mutation is made only in an ephemeral copy; official assets remain intact.
    cases = {
        "multiple_roots": lambda p: shutil.copyfile(p / "agent.yaml", p / "root_agent.yml"),
        "unknown_tool": lambda p: (p / "agent.yaml").write_text(
            f"name: invalid\nmodel: {MODEL}\ninstruction: synthetic test\ntools: [nonexistent_tool]\n"),
        "wrong_model": lambda p: (p / "agent.yaml").write_text("name: invalid\nmodel: other_model\n"),
        "forbidden_field": lambda p: (p / "agent.yaml").write_text(
            f"name: invalid\nmodel: {MODEL}\ninstruction: synthetic test\ngenerate_content_config:\n  http_options: {{}}\n"),
        "output_overflow": lambda p: (p / "configs/sampling.yaml").write_text("max_output_tokens: 32769\n"),
        "include_escape": lambda p: (p / "agent.yaml").write_text(
            f"name: invalid\nmodel: {MODEL}\ninstruction: !include ../../outside.md\n"),
        "missing_adapter": lambda p: (p / "agent.yaml").write_text(
            f"name: invalid\nmodel: {MODEL}\ninstruction: synthetic test\nadapter: missing_adapter\n"),
        "disallowed_binary": lambda p: (p / "weights.bin").write_bytes(b"synthetic disallowed payload"),
    }
    for name, mutate in cases.items():
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "submission"
            shutil.copytree(original, root)
            mutate(root)
            try:
                compile_only(root)
            except (SubmissionError, ValueError) as error:
                expected = {
                    "multiple_roots": "ValueError", "unknown_tool": "ToolNotFoundError",
                    "wrong_model": "ValueError", "forbidden_field": "SubmissionSchemaError",
                    "output_overflow": "SubmissionValidationError", "include_escape": "PathTraversalError",
                    "missing_adapter": "AdapterNotFoundError", "disallowed_binary": "SubmissionValidationError",
                }
                results.append({"case": name, "passed": type(error).__name__ == expected[name],
                                "rejection": type(error).__name__, "message": str(error)})
            else:
                results.append({"case": name, "passed": False, "rejection": None})
    probes = []
    for alias in ("agent.yml", "root_agent.yaml", "root_agent.yml"):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "submission"
            shutil.copytree(original, root)
            (root / "agent.yaml").rename(root / alias)
            try:
                compile_only(root)
            except SubmissionValidationError as error:
                probes.append({"alias": alias, "compiled": False, "error": str(error)})
            else:
                probes.append({"alias": alias, "compiled": True})
    schema = json.dumps(SandboxedAgentConfig.model_json_schema(), sort_keys=True, indent=2) + "\n"
    (args.output / "agent-schema.json").write_text(schema)
    hashes = {str(p.relative_to(original)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(original.rglob("*")) if p.is_file()}
    receipt = {
        "schema_version": 1, "started_utc": started,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "elapsed_ns": time.monotonic_ns() - start_ns,
        "packages": packages, "checks": results, "root_alias_probes": probes,
        "starter_sha256": hashes,
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "schema_sha256": hashlib.sha256(schema.encode()).hexdigest(),
        "model_inference": "not_run", "tool_execution": "not_run",
        "bindings": "compile_only_placeholders_raise_on_execution",
        "full_swegemma_runtime": "not_run",
    }
    (args.output / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(results, indent=2))
    return 0 if all(r["passed"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
