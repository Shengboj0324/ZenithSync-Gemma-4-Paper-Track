"""CPU-only validation of the versioned P1 serving profile."""

import math
from pathlib import Path


FIELDS = {"schema_version", "status", "model_alias", "publisher_version", "python",
          "platform", "host", "port", "max_model_len", "dtype", "tool_call_parser",
          "reasoning_parser", "gpu_memory_utilization", "tensor_parallel_size",
          "startup_timeout_seconds", "max_num_seqs", "adapters", "qualification_scope"}


def validate_profile(profile: object) -> dict:
    if not isinstance(profile, dict) or set(profile) != FIELDS:
        raise ValueError("unexpected serving profile fields")
    exact = {"schema_version": 1, "publisher_version": 2,
             "model_alias": "gemma-4-31b-it-qat-w4a16-ct", "python": "3.12",
             "platform": "linux_x86_64", "host": "127.0.0.1", "dtype": "bfloat16",
             "tool_call_parser": "gemma4", "reasoning_parser": "gemma4"}
    for key, expected in exact.items():
        if type(profile[key]) is not type(expected) or profile[key] != expected:
            raise ValueError(f"unsupported P1 serving value: {key}")
    for key, lower, upper in [("port", 1024, 65535), ("max_model_len", 1, 32768),
                              ("startup_timeout_seconds", 1, 1200), ("max_num_seqs", 1, 256)]:
        value = profile[key]
        if type(value) is not int or not lower <= value <= upper:
            raise ValueError(f"invalid serving bound: {key}")
    if type(profile["tensor_parallel_size"]) is not int or profile["tensor_parallel_size"] not in (1, 2, 4):
        raise ValueError("unsupported tensor parallelism")
    fraction = profile["gpu_memory_utilization"]
    if type(fraction) not in (int, float) or not math.isfinite(fraction) or not 0 < fraction < 1:
        raise ValueError("GPU memory fraction must be finite and strictly between zero and one")
    if profile["adapters"] != []:
        raise ValueError("P1 base-model profile must not mount unqualified adapters")
    for key in ("status", "qualification_scope"):
        if not isinstance(profile[key], str) or not profile[key].strip():
            raise ValueError(f"missing profile annotation: {key}")
    return profile


def sdk_config_arguments(profile: object, model_dir: Path) -> dict:
    """Return official VllmConfig arguments; never import or start a GPU runtime."""
    p = validate_profile(profile)
    if model_dir.is_symlink() or not model_dir.is_dir():
        raise ValueError("model directory must exist and must not be a symlink")
    return {"model": str(model_dir.resolve()), "host": p["host"], "port": p["port"],
            "max_model_len": p["max_model_len"], "dtype": p["dtype"],
            "gpu_memory_utilization": p["gpu_memory_utilization"],
            "tool_call_parser": p["tool_call_parser"], "reasoning_parser": p["reasoning_parser"],
            "enable_auto_tool_choice": True, "enable_lora": False,
            "tensor_parallel_size": p["tensor_parallel_size"],
            "startup_timeout": p["startup_timeout_seconds"],
            "extra_args": ["--max-num-seqs", str(p["max_num_seqs"]),
                           "--served-model-name", p["model_alias"]]}
