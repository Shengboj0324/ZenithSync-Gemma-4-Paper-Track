"""Offline executable checks of the supplied tokenizer and tool chat template.

Run in a minimal tokenizer-only environment; this never instantiates a model.
Synthetic conversations below are test inputs, not generated model responses.
"""

import argparse
from datetime import datetime, timezone
from importlib.metadata import version
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from zenithsync.artifacts import canonical_json, file_record, load_json


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    os.environ["HF_HUB_OFFLINE"] = "1"
    from transformers import AutoTokenizer

    files = ["config.json", "generation_config.json", "tokenizer.json",
             "tokenizer_config.json", "chat_template.jinja"]
    identities = {name: file_record(args.model_dir / name) for name in files}
    source_identity = file_record(Path(__file__))
    config = load_json(args.model_dir / "config.json")
    generation = load_json(args.model_dir / "generation_config.json")
    text = config["text_config"]
    require(config["model_type"] == "gemma4", "unexpected model family")
    tokenizer = AutoTokenizer.from_pretrained(args.model_dir, local_files_only=True,
                                              trust_remote_code=False)
    require(len(tokenizer) == text["vocab_size"], "vocabulary size mismatch")
    require(tokenizer.chat_template == (args.model_dir / "chat_template.jinja").read_text(),
            "loaded template differs from supplied file")
    for name, expected in (("pad", 0), ("eos", 1), ("bos", 2)):
        actual = getattr(tokenizer, name + "_token_id")
        require(actual == expected == text[name + "_token_id"], "special token mismatch")
        configured = generation[name + "_token_id"]
        require(actual in configured if isinstance(configured, list) else actual == configured,
                "generation special token mismatch")
    tokens = ["<|turn>", "<turn|>", "<|tool_call>", "<tool_call|>",
              "<|tool_response>", "<tool_response|>", "<|channel>", "<channel|>"]
    token_ids = {}
    for token in tokens:
        ids = tokenizer.encode(token, add_special_tokens=False)
        require(len(ids) == 1 and tokenizer.convert_ids_to_tokens(ids[0]) == token,
                "protocol token is not an exact single token")
        token_ids[token] = ids[0]
    require(len(set(token_ids.values())) == len(token_ids), "protocol token IDs collide")

    tools = [{"type": "function", "function": {
        "name": "read_file", "description": "Read a repository file",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string", "description": "Repository-relative path"}},
            "required": ["path"]}}}]
    user = {"role": "user", "content": "Inspect src/example.py before editing."}
    call = {"role": "assistant", "content": "", "tool_calls": [
        {"id": "fixture-call-1", "type": "function", "function": {
            "name": "read_file", "arguments": {"path": "src/example.py"}}}]}
    response = {"role": "tool", "tool_call_id": "fixture-call-1",
                "content": "def example():\n    return 'α'\n"}
    cases = [("plain", [user], None, False),
             ("system", [{"role": "system", "content": "Inspect before editing."}, user],
              tools, False),
             ("thinking", [user], tools, True),
             ("pending_call", [user, call], tools, False),
             ("tool_continuation", [user, call, response], tools, False),
             ("completed_exchange", [user, call, response,
                 {"role": "assistant", "content": "The file returns a Greek letter."},
                 {"role": "user", "content": "Now add a test."}], tools, False)]
    records = []
    for name, messages, declarations, thinking in cases:
        options = dict(tools=declarations, add_generation_prompt=True,
                       enable_thinking=thinking)
        rendered = tokenizer.apply_chat_template(messages, tokenize=False, **options)
        encoded = tokenizer.apply_chat_template(messages, tokenize=True, **options)
        if isinstance(encoded, dict) or hasattr(encoded, "keys"):
            encoded = encoded["input_ids"]
        require(encoded == tokenizer.encode(rendered, add_special_tokens=False),
                "template tokenization differs from explicit encoding")
        require(rendered.startswith(tokenizer.bos_token) and encoded.count(tokenizer.bos_token_id) == 1,
                "missing or duplicated BOS token")
        require(len(encoded) < 32768, "fixture exceeds deployment context limit")
        if name in {"pending_call", "tool_continuation", "completed_exchange"}:
            require('<|tool_call>call:read_file{path:<|"|>src/example.py<|"|>}<tool_call|>'
                    in rendered, "structured tool arguments rendered incorrectly")
        if name in {"tool_continuation", "completed_exchange"}:
            require("<|tool_response>response:read_file{" in rendered and
                    "<tool_response|>" in rendered and "unknown" not in rendered,
                    "tool response failed to bind to its call ID")
        (args.output / (name + ".txt")).write_text(rendered)
        records.append({"case": name, "token_count": len(encoded),
                        "rendered": file_record(args.output / (name + ".txt"))})
    for sample in ["def f(x):\n    return x + 1\n", "α 中文 🧪", "  leading\n\tindent"]:
        require(tokenizer.decode(tokenizer.encode(sample, add_special_tokens=False),
                                 skip_special_tokens=False) == sample,
                "code or Unicode roundtrip changed text")
    require(identities == {name: file_record(args.model_dir / name) for name in files},
            "model metadata changed during verification")
    require(source_identity == file_record(Path(__file__)), "verifier changed during run")
    receipt = {"schema_version": 1, "status": "offline_tokenizer_checks_passed",
               "timestamp_utc": datetime.now(timezone.utc).isoformat(),
               "source": source_identity, "model_metadata": identities,
               "versions": {p: version(p) for p in ["transformers", "tokenizers", "jinja2"]},
               "cases": records, "protocol_token_ids": token_ids,
               "generation_stop_ids": generation["eos_token_id"],
               "scope": "synthetic input rendering and tokenization; no model generation"}
    (args.output / "receipt.json").write_bytes(canonical_json(receipt))
    print("Offline tokenizer and six chat-template cases passed; no model inference performed.")


if __name__ == "__main__":
    main()
