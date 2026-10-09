"""Compile a launch plan with the official SDK, without starting a server."""

import argparse
from datetime import datetime, timezone
from importlib.metadata import version
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")
from zenithsync.artifacts import canonical_json, file_record, load_json
from zenithsync.serving import sdk_config_arguments


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    profile = load_json(args.profile)
    config = sdk_config_arguments(profile, args.model_dir)
    if version("adk-submission") != "0.2.13":
        raise RuntimeError("launch planning requires the newly pinned official SDK")
    from adk_submission import VllmConfig, VllmServer
    command = VllmServer(VllmConfig(**config)).build_cmd()
    for flag, value in [("--tool-call-parser", "gemma4"), ("--reasoning-parser", "gemma4"),
                        ("--served-model-name", profile["model_alias"]), ("--host", "127.0.0.1")]:
        if command.count(flag) != 1 or command[command.index(flag)+1] != value:
            raise RuntimeError("official SDK command differs from required profile")
    if "--lora-modules" in command or "--enable-lora" in command:
        raise RuntimeError("unexpected adapter activation")
    args.output.mkdir(parents=True, exist_ok=False)
    receipt = {"schema_version":1, "status":"launch_plan_compiled_not_executed",
               "timestamp_utc":datetime.now(timezone.utc).isoformat(), "argv":command,
               "sdk_version":version("adk-submission"), "profile":file_record(args.profile),
               "sources":{name:file_record(ROOT/name) for name in
                   ["scripts/plan_serving.py","zenithsync/serving.py","tests/test_serving.py"]},
               "target_platform":profile["platform"], "target_python":profile["python"],
               "gpu_verified":False,
               "limitation":"Regenerate on the Pod to use its interpreter and model path; CPU compilation is not launch validation."}
    (args.output/"receipt.json").write_bytes(canonical_json(receipt))
    print("Official SDK launch plan compiled; no server or GPU started.")


if __name__ == "__main__":
    main()
