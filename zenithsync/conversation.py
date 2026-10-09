"""Validated text-only tool history for the supplied Gemma chat template.

This normalizes transport syntax and call/result linkage. Tool-specific argument
schemas, execution authorization and generated Gemma-token parsing are separate.
"""

import json
import re

from .artifacts import _pairs, canonical_json


def _reject_constant(value: str) -> None:
    raise ValueError("nonfinite tool argument")


def normalize_arguments(value: object, *, max_bytes: int = 1024 * 1024) -> dict:
    if type(max_bytes) is not int or max_bytes <= 0:
        raise ValueError("argument byte cap must be a positive integer")
    try:
        if isinstance(value, str):
            if len(value.encode("utf-8")) > max_bytes:
                raise ValueError("tool arguments exceed byte cap")
            value = json.loads(value, object_pairs_hook=_pairs, parse_constant=_reject_constant)
        if not isinstance(value, dict):
            raise ValueError("tool arguments must be a JSON object")
        # JSON roundtrip detaches caller-owned values and rejects nonfinite data.
        def check_keys(item):
            if isinstance(item, dict):
                if any(not isinstance(key, str) for key in item):
                    raise ValueError("argument object keys must be strings")
                for child in item.values():
                    check_keys(child)
            elif isinstance(item, list):
                for child in item:
                    check_keys(child)
            elif item is not None and type(item) not in (str, int, float, bool):
                raise ValueError("arguments contain a non-JSON value")
        check_keys(value)
        payload = canonical_json(value)
        if len(payload) > max_bytes:
            raise ValueError("normalized tool arguments exceed byte cap")
        return json.loads(payload)
    except (RecursionError, UnicodeError, TypeError) as exc:
        raise ValueError("invalid tool argument representation") from exc


def normalize_history(messages: object, *, allowed_tools: set[str],
                      allow_pending: bool = False) -> list[dict]:
    """Bind every tool response exactly once; reject interrupted exchanges.

    Pending calls are accepted only at the end and only when explicitly requested
    for tool dispatch. Generation should use the default complete-history mode.
    """
    if not isinstance(messages, list) or not messages:
        raise ValueError("history must be a nonempty list")
    if not isinstance(allowed_tools, set) or any(
            not isinstance(name, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name)
            for name in allowed_tools):
        raise ValueError("invalid tool registry")
    if type(allow_pending) is not bool:
        raise ValueError("allow_pending must be boolean")
    output, pending, seen = [], {}, set()
    for index, message in enumerate(messages):
        if not isinstance(message, dict):
            raise ValueError("message must be an object")
        role = message.get("role")
        fields = {"role", "content"}
        if role == "assistant":
            fields |= {"tool_calls", "reasoning", "reasoning_content"}
        elif role == "tool":
            fields |= {"tool_call_id", "name"}
        elif role not in ("system", "developer", "user"):
            raise ValueError("unsupported message role")
        if set(message) - fields:
            raise ValueError("unsupported message fields")
        if role in ("system", "developer") and index != 0:
            raise ValueError("system/developer instruction must precede conversation")
        content = message.get("content", "")
        if content is None and role == "assistant":
            content = ""
        if not isinstance(content, str):
            raise ValueError("this history adapter requires text content")
        normalized = {"role": role, "content": content}
        if role == "tool":
            identifier = message.get("tool_call_id")
            if not isinstance(identifier, str) or identifier not in pending:
                raise ValueError("orphan or duplicate tool response")
            name = pending.pop(identifier)
            if "name" in message and message["name"] != name:
                raise ValueError("tool response name conflicts with call ID")
            normalized.update(tool_call_id=identifier, name=name)
        else:
            if pending:
                raise ValueError("tool exchange interrupted before all results arrived")
            if role == "assistant":
                if "reasoning" in message and "reasoning_content" in message:
                    raise ValueError("ambiguous reasoning fields")
                for field in ("reasoning", "reasoning_content"):
                    if field in message:
                        if not isinstance(message[field], str):
                            raise ValueError("reasoning must be text")
                        normalized[field] = message[field]
                if "tool_calls" in message:
                    calls = message["tool_calls"]
                    if not isinstance(calls, list) or not calls:
                        raise ValueError("tool_calls must be a nonempty list")
                    normalized["tool_calls"] = []
                    for call in calls:
                        if not isinstance(call, dict) or set(call) != {"id", "type", "function"}:
                            raise ValueError("invalid tool call fields")
                        identifier = call["id"]
                        if not isinstance(identifier, str) or not identifier.strip() or identifier in seen:
                            raise ValueError("missing or reused tool call ID")
                        function = call["function"]
                        if call["type"] != "function" or not isinstance(function, dict) or set(function) != {"name", "arguments"}:
                            raise ValueError("invalid function call")
                        name = function["name"]
                        if not isinstance(name, str) or name not in allowed_tools:
                            raise ValueError("unknown tool")
                        arguments = normalize_arguments(function["arguments"])
                        seen.add(identifier)
                        pending[identifier] = name
                        normalized["tool_calls"].append({"id": identifier, "type": "function",
                            "function": {"name": name, "arguments": arguments}})
        output.append(normalized)
    if pending and not allow_pending:
        raise ValueError("tool results are missing")
    return output
