"""Run a real two-request Gemma tool-continuation probe against a local server.

Do not run until the user restarts the GPU Pod and the server is verified ready.
The model must read an unpredictable on-disk marker through an actual tool call.
"""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import secrets
import sys
import tempfile
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import _pairs, canonical_json, file_record
from zenithsync.conversation import normalize_history
from zenithsync.inference_probe import extract_final_text, extract_read_call


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        raise ValueError("invalid loopback port")
    args.output.mkdir(parents=True, exist_ok=False)
    model = "gemma-4-31b-it-qat-w4a16-ct"
    timings = []

    def request(path, payload=None):
        req = urllib.request.Request(f"http://127.0.0.1:{args.port}/v1/{path}",
            data=canonical_json(payload) if payload is not None else None,
            headers={"Content-Type":"application/json", "Authorization":"Bearer EMPTY"})
        started = time.monotonic_ns()
        # Do not route a loopback probe through environment-configured proxies.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(req, timeout=180) as response:
            body = response.read(8 * 1024 * 1024 + 1)
        timings.append(time.monotonic_ns() - started)
        if len(body) > 8 * 1024 * 1024:
            raise ValueError("inference response exceeds byte cap")
        value = json.loads(body, object_pairs_hook=_pairs)
        (args.output/f"response-{len(timings)}.json").write_bytes(canonical_json(value))
        return value

    models = request("models")
    if model not in {item["id"] for item in models["data"]}:
        raise ValueError("server does not expose the required model alias")
    tool = {"type":"function", "function":{"name":"read_file",
        "description":"Read the probe file from disk.",
        "parameters":{"type":"object","properties":{"path":{"type":"string","enum":["probe.txt"]}},
                      "required":["path"],"additionalProperties":False}}}
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary)/"probe.txt"
        marker = "probe_" + secrets.token_hex(24)
        path.write_text(marker)
        messages = [{"role":"user", "content":
            "Use read_file to read probe.txt. Then return only the exact marker found in that file."}]
        first = request("chat/completions", {"model":model,"messages":messages,
            "tools":[tool],"tool_choice":"auto","temperature":0,"max_tokens":512})
        call = extract_read_call(first)
        messages.append({"role":"assistant","content":"","tool_calls":[call]})
        # This path is fixed by the validated schema, never taken from unchecked output.
        observed = path.read_text()
        messages.append({"role":"tool","tool_call_id":call["id"],"content":observed})
        normalized = normalize_history(messages, allowed_tools={"read_file"})
        wire = json.loads(canonical_json(normalized))
        for message in wire:
            for tc in message.get("tool_calls", []):
                tc["function"]["arguments"] = json.dumps(tc["function"]["arguments"])
        final = request("chat/completions", {"model":model,"messages":wire,
            "tools":[tool],"tool_choice":"none","temperature":0,"max_tokens":512})
        if extract_final_text(final) != marker:
            raise ValueError("model did not reproduce the actual tool result exactly")
        marker_identity = file_record(path)
    receipt = {"schema_version":1,"status":"real_tool_continuation_probe_passed",
        "timestamp_utc":datetime.now(timezone.utc).isoformat(),"model_alias":model,
        "http_wall_times_ns":timings,"marker_file":marker_identity,
        "sources":{name:file_record(ROOT/name) for name in
            ["scripts/probe_inference.py","zenithsync/inference_probe.py","zenithsync/conversation.py"]},
        "scope":"one real generated tool call and continuation; not repair performance or training readiness"}
    (args.output/"receipt.json").write_bytes(canonical_json(receipt))
    print("Real tool-call and continuation probe passed.")


if __name__ == "__main__":
    main()
