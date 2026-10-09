"""Synthetic API responses validate rejection paths, never inference claims."""

import copy
import unittest

from zenithsync.inference_probe import extract_final_text, extract_read_call


def call_response():
    return {"choices": [{"finish_reason": "tool_calls", "message": {"role": "assistant", "tool_calls": [
        {"id": "test-call", "type": "function", "function": {
            "name": "read_file", "arguments": '{"path":"probe.txt"}'}}]}}]}


class ProbeTests(unittest.TestCase):
    def test_valid_call_preserves_identity(self):
        response = call_response()
        before = copy.deepcopy(response)
        call = extract_read_call(response)
        self.assertEqual(call["id"], "test-call")
        self.assertEqual(call["function"]["arguments"], {"path": "probe.txt"})
        self.assertEqual(response, before)

    def test_untrusted_tool_paths_names_and_extra_arguments_rejected(self):
        for name, arguments in [("run_command", '{"path":"probe.txt"}'),
                                ("read_file", '{"path":"../.env"}'),
                                ("read_file", '{"path":"probe.txt","other":true}'),
                                ("read_file", '{"path":"probe.txt","path":"probe.txt"}')]:
            response = call_response()
            response["choices"][0]["message"]["tool_calls"][0]["function"] = {
                "name": name, "arguments": arguments}
            with self.assertRaises(ValueError):
                extract_read_call(response)

    def test_missing_or_multiple_calls_rejected(self):
        for calls in ([], [None], [{}, {}]):
            response = call_response()
            response["choices"][0]["message"]["tool_calls"] = calls
            with self.assertRaises(ValueError):
                extract_read_call(response)

    def test_truncated_call_rejected_even_with_valid_arguments(self):
        response = call_response()
        response["choices"][0]["finish_reason"] = "length"
        with self.assertRaises(ValueError):
            extract_read_call(response)

    def test_truncated_or_tool_final_response_rejected(self):
        good = {"choices": [{"finish_reason": "stop", "message": {
            "role": "assistant", "content": " marker "}}]}
        self.assertEqual(extract_final_text(good), "marker")
        for finish in ("length", "tool_calls", None):
            bad = copy.deepcopy(good)
            bad["choices"][0]["finish_reason"] = finish
            with self.assertRaises(ValueError):
                extract_final_text(bad)


if __name__ == "__main__":
    unittest.main()
