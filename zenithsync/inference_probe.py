"""Acceptance checks for a real generated tool call, not a simulated model."""

from .conversation import normalize_arguments


def extract_read_call(response: object) -> dict:
    if not isinstance(response, dict) or not isinstance(response.get("choices"), list) or len(response["choices"]) != 1:
        raise ValueError("expected exactly one completion choice")
    choice = response["choices"][0]
    if not isinstance(choice, dict) or not isinstance(choice.get("message"), dict):
        raise ValueError("missing assistant message")
    if choice.get("finish_reason") not in ("tool_calls", "stop"):
        raise ValueError("tool-call response is truncated or incomplete")
    message = choice["message"]
    if message.get("role") != "assistant":
        raise ValueError("completion has incorrect role")
    calls = message.get("tool_calls")
    if not isinstance(calls, list) or len(calls) != 1:
        raise ValueError("model did not generate exactly one tool call")
    call = calls[0]
    if not isinstance(call, dict) or call.get("type") != "function":
        raise ValueError("invalid generated call type")
    identifier = call.get("id")
    if not isinstance(identifier, str) or not identifier.strip():
        raise ValueError("generated call has no ID")
    function = call.get("function")
    if not isinstance(function, dict) or function.get("name") != "read_file":
        raise ValueError("generated call names an unauthorized tool")
    arguments = normalize_arguments(function.get("arguments"))
    if arguments != {"path": "probe.txt"}:
        raise ValueError("generated call violates the probe tool schema")
    return {"id": identifier, "type": "function",
            "function": {"name": "read_file", "arguments": arguments}}


def extract_final_text(response: object) -> str:
    if not isinstance(response, dict) or not isinstance(response.get("choices"), list) or len(response["choices"]) != 1:
        raise ValueError("expected exactly one final completion")
    choice = response["choices"][0]
    if not isinstance(choice, dict) or choice.get("finish_reason") != "stop":
        raise ValueError("final response did not terminate normally")
    message = choice.get("message")
    if not isinstance(message, dict) or message.get("role") != "assistant" or message.get("tool_calls"):
        raise ValueError("final response is not a completed assistant answer")
    text = message.get("content")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("final response has no text")
    return text.strip()
