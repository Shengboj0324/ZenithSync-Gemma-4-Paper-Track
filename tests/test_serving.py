"""Serving profile validation; synthetic directories do not imply model readiness."""

import copy
from pathlib import Path
import tempfile
import unittest

from zenithsync.artifacts import load_json
from zenithsync.serving import sdk_config_arguments, validate_profile


class ServingTests(unittest.TestCase):
    def setUp(self):
        self.profile = load_json(Path(__file__).resolve().parents[1]/"configs/p1-serving.json")

    def test_profile_mapping_preserves_model_boundaries(self):
        with tempfile.TemporaryDirectory() as directory:
            before = copy.deepcopy(self.profile)
            args = sdk_config_arguments(self.profile, Path(directory))
            self.assertFalse(args["enable_lora"])
            self.assertEqual(args["tool_call_parser"], "gemma4")
            self.assertEqual(args["reasoning_parser"], "gemma4")
            self.assertEqual(args["max_model_len"], 32768)
            self.assertEqual(self.profile, before)

    def test_invalid_bounds_rejected(self):
        for key, value in [("schema_version", True), ("port", True), ("port", 65536),
                           ("max_model_len", 32769), ("max_num_seqs", 0),
                           ("tensor_parallel_size", 3), ("gpu_memory_utilization", float("nan")),
                           ("gpu_memory_utilization", float("inf")), ("gpu_memory_utilization", 1),
                           ("gpu_memory_utilization", True), ("host", "0.0.0.0"),
                           ("adapters", ["placeholder"]), ("tool_call_parser", "hermes")]:
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                validate_profile({**self.profile, key:value})

    def test_extra_fields_and_symlink_rejected(self):
        with self.assertRaises(ValueError):
            validate_profile({**self.profile, "extra_args":["--trust-remote-code"]})
        with tempfile.TemporaryDirectory() as directory:
            link = Path(directory)/"link"
            link.symlink_to(directory, target_is_directory=True)
            with self.assertRaises(ValueError):
                sdk_config_arguments(self.profile, link)


if __name__ == "__main__":
    unittest.main()
