"""Exercise normalized synthetic tool histories with the actual local tokenizer."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record
from zenithsync.conversation import normalize_history


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    os.environ["HF_HUB_OFFLINE"] = "1"
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(args.model_dir, local_files_only=True,
                                              trust_remote_code=False)
    records = []
    for arguments in ({"path":"src/α.py"}, {"path":"src/file.py","start_line":1,"end_line":3}):
        renders = []
        for transport in (arguments, json.dumps(arguments)):
            messages = [{"role":"user","content":"Read the specified file."},
                        {"role":"assistant","content":None,"tool_calls":[
                            {"id":"fixture-1","type":"function","function":{
                                "name":"read_file","arguments":transport}}]},
                        {"role":"tool","tool_call_id":"fixture-1","content":"synthetic result"}]
            normalized = normalize_history(messages, allowed_tools={"read_file"})
            rendered = tokenizer.apply_chat_template(normalized, tokenize=False,
                                                       add_generation_prompt=True)
            if "<|tool_call>call:read_file{" not in rendered or "<|tool_response>response:read_file{" not in rendered:
                raise ValueError("normalized history lost tool call/result linkage")
            renders.append(rendered)
        if renders[0] != renders[1]:
            raise ValueError("JSON and mapping transports render differently")
        path = args.output / f"case-{len(records)+1}.txt"
        path.write_text(renders[0])
        records.append({"argument_keys":sorted(arguments),"render":file_record(path)})
    source_names = ["scripts/verify_conversation.py","zenithsync/conversation.py",
                    "tests/test_conversation.py"]
    receipt = {"schema_version":1,"status":"conversation_template_checks_passed",
               "timestamp_utc":datetime.now(timezone.utc).isoformat(),"cases":records,
               "sources":{name:file_record(ROOT/name) for name in source_names},
               "model_metadata":{name:file_record(args.model_dir/name) for name in
                    ["chat_template.jinja","tokenizer.json","tokenizer_config.json"]},
               "scope":"synthetic histories with actual template; no generated calls or execution"}
    (args.output/"receipt.json").write_bytes(canonical_json(receipt))
    print("Normalized JSON and mapping tool calls render identically in the supplied template.")


if __name__ == "__main__":
    main()
