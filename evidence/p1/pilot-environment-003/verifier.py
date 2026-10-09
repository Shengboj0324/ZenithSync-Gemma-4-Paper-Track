"""Run official offline setup and existing pilot tests; no reference patch or model."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")
from zenithsync.artifacts import canonical_json, file_record, load_json, verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--dependencies", type=Path, required=True)
    parser.add_argument("--dependency-manifest", type=Path, required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-path-override", action="store_true",
                        help="Diagnostic only: prioritize workspace source; not official-runtime acceptance")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    verify(args.bundle, load_json(args.manifest))
    verify(args.dependencies, load_json(args.dependency_manifest))
    from adk_submission import ModelRegistry
    from swegemma.config import EvalConfig
    from swegemma.sandbox import ContainerConfig, ContainerManager
    from swegemma.harness.container_setup import extract_snapshot, setup_container_wheels, setup_container_workspace

    if "DOCKER_HOST" not in os.environ:
        os.environ["DOCKER_HOST"] = subprocess.check_output(
            ["docker","context","inspect","--format","{{.Endpoints.docker.Host}}"],
            text=True, timeout=15).strip()
    os.environ["KAGGLE_SANDBOX_DIR"] = str(ROOT / "artifacts/official/gemma-4-developer-agent/sandbox")
    manager = ContainerManager(ContainerConfig(image=args.image, reuse_containers=False))
    image = manager.client.images.get(args.image)
    manager.config.image = image.id
    config = EvalConfig(tasks_path=args.bundle/"tasks.jsonl", snapshots_dir=args.bundle/"snapshots",
                        results_dir=args.output, submission_dir=ROOT/"artifacts/official/gemma-4-developer-agent/sample_submission",
                        models=ModelRegistry(), wheels_dir=args.dependencies/"wheels")
    task = json.loads((args.bundle/"tasks.jsonl").read_text())
    container = manager.start()
    result = {}
    try:
        attrs = manager.client.containers.get(container).attrs
        if attrs["HostConfig"]["NetworkMode"] != "none" or attrs["Mounts"]:
            raise RuntimeError("sandbox network or mounts differ from required isolation")
        extract_snapshot(manager, container, args.bundle/"snapshots"/(task["instance_id"]+".tgz"))
        setup_container_wheels(manager, container, config)
        setup_container_workspace(manager, container, repo=task["repo"], config=config)
        prefix = "PYTHONPATH=/workspace/src:/workspace " if args.source_path_override else ""
        imported = manager.exec(container, prefix + "python -c 'import requests; print(requests.__file__)'")
        (args.output/"import.log").write_text(imported.stdout + imported.stderr)
        if imported.exit_code != 0 or not imported.stdout.strip().startswith("/workspace/"):
            diagnostic = manager.exec(container, "pip install --no-index --find-links=/wheels --no-build-isolation --no-deps -e /workspace")
            (args.output/"editable-install-diagnostic.log").write_text(diagnostic.stdout + diagnostic.stderr)
            paths = manager.exec(container, "python -c 'import sys; print(sys.path)'")
            (args.output/"python-path.log").write_text(paths.stdout + paths.stderr)
            raise RuntimeError("workspace package import failed or resolved outside snapshot")
        command = prefix + "python -m pytest -q tests/test_structures.py tests/test_hooks.py --junitxml=/tmp/p1-smoke.xml"
        tested = manager.exec(container, command)
        (args.output/"pytest.log").write_text(tested.stdout + tested.stderr)
        report = manager.exec(container, "cat /tmp/p1-smoke.xml")
        if report.exit_code != 0:
            raise RuntimeError("JUnit report missing")
        (args.output/"junit.xml").write_text(report.stdout)
        xml = ET.fromstring(report.stdout)
        cases = list(xml.iter("testcase"))
        failures = sum(1 for case in cases if any(case.find(tag) is not None for tag in ("failure","error","skipped")))
        if tested.exit_code != 0 or not cases or failures:
            raise RuntimeError("offline baseline subset failed or skipped tests")
        result = {"tests_passed":len(cases),"command":command,"network":"none",
                  "workspace_import":imported.stdout.strip(),"test_exit_code":tested.exit_code}
    finally:
        manager.stop(container)
    verify(args.bundle, load_json(args.manifest))
    verify(args.dependencies, load_json(args.dependency_manifest))
    (args.output/"receipt.json").write_bytes(canonical_json({
        "schema_version":1,"status":("diagnostic_source_override_subset_passed" if args.source_path_override
                                      else "official_offline_setup_and_subset_passed"),
        "source_path_override":args.source_path_override,
        "timestamp_utc":datetime.now(timezone.utc).isoformat(),"image_id":image.id,
        "verifier":file_record(Path(__file__)),"bundle_manifest":file_record(args.manifest),
        "dependency_manifest":file_record(args.dependency_manifest),"result":result,
        "scope":"existing structures/hooks tests only; no task repair, hidden grading or model"}))
    print(f"Source-verified subset passed: {result['tests_passed']} tests; source override={args.source_path_override}.")


if __name__ == "__main__":
    main()
