"""Conversation boundary checks using synthetic tool exchanges."""

import copy
import unittest

from zenithsync.conversation import normalize_arguments, normalize_history


def history():
    return [{"role":"user","content":"Read the file."},
            {"role":"assistant","content":None,"tool_calls":[
                {"id":"a","type":"function","function":{
                    "name":"read_file","arguments":'{"path":"src/a.py"}'}}]},
            {"role":"tool","tool_call_id":"a","content":"fixture content"}]


class ConversationTests(unittest.TestCase):
    def normalize(self, messages, **kwargs):
        return normalize_history(messages, allowed_tools={"read_file"}, **kwargs)

    def test_string_mapping_equivalence_and_no_mutation(self):
        original=history(); before=copy.deepcopy(original)
        result=self.normalize(original)
        mapped=history(); mapped[1]["tool_calls"][0]["function"]["arguments"]={"path":"src/a.py"}
        self.assertEqual(result,self.normalize(mapped))
        self.assertEqual(original,before)
        self.assertEqual(result[2]["name"],"read_file")
        result[1]["tool_calls"][0]["function"]["arguments"]["path"]="changed"
        self.assertEqual(original,before)

    def test_invalid_json_shapes_nonfinite_duplicate_keys(self):
        for value in ['{"x":1,"x":2}', '{"x":NaN}', '[]', 'null',
                      {"x":float("inf")}, {1:"value"}, {"x":(1,2)}]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                normalize_arguments(value)

    def test_byte_limit_and_nested_json_values(self):
        self.assertEqual(normalize_arguments({"x":[True,None,1.5,{"α":"β"}]}),
                         {"x":[True,None,1.5,{"α":"β"}]})
        with self.assertRaises(ValueError):
            normalize_arguments('{"x":"long"}',max_bytes=5)

    def test_orphan_duplicate_conflicting_and_reused_ids(self):
        cases=[history()+[history()[2]], [history()[2]]]
        conflict=history(); conflict[2]["name"]="write_file";cases.append(conflict)
        cases.append(history()+[history()[1]])
        for value in cases:
            with self.assertRaises(ValueError):self.normalize(value)

    def test_pending_calls_only_when_explicit(self):
        with self.assertRaises(ValueError):self.normalize(history()[:2])
        self.assertEqual(len(self.normalize(history()[:2],allow_pending=True)),2)
        with self.assertRaises(ValueError):
            self.normalize(history()[:2]+[{"role":"user","content":"Continue"}],allow_pending=True)

    def test_parallel_results_can_arrive_in_different_order(self):
        messages=history()
        other=copy.deepcopy(messages[1]["tool_calls"][0]);other["id"]="b"
        messages[1]["tool_calls"].append(other)
        messages.insert(2,{"role":"tool","tool_call_id":"b","content":"second"})
        self.assertEqual([x["tool_call_id"] for x in self.normalize(messages)[2:]], ["b","a"])

    def test_unknown_tools_and_fields_fail_closed(self):
        bad=history();bad[1]["tool_calls"][0]["function"]["name"]="invented"
        with self.assertRaises(ValueError):self.normalize(bad)
        bad=history();bad[0]["unrecognized"]="extra"
        with self.assertRaises(ValueError):self.normalize(bad)


if __name__=="__main__":unittest.main()
