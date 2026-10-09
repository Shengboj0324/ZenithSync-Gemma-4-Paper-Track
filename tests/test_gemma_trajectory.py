import copy
import unittest

from zenithsync.gemma_trajectory import project_pre_action_text


class GemmaTrajectoryTests(unittest.TestCase):
    def history(self):
        return [{'role': 'user', 'content': 'Inspect'},
                {'role': 'assistant', 'content': 'First inspect 🌍. ', 'tool_calls': [
                    {'id': 'a', 'type': 'function', 'function': {'name': 'execute_bash', 'arguments': {'command': 'pwd'}}}]},
                {'role': 'tool', 'tool_call_id': 'a', 'content': 'RESULT'}]

    def test_exact_text_and_tool_identity_preserved_without_mutation(self):
        source = self.history()
        before = copy.deepcopy(source)
        result = project_pre_action_text(source)
        self.assertEqual(source, before)
        self.assertEqual(result['messages'][1]['reasoning'], source[1]['content'])
        self.assertEqual(result['messages'][1]['content'], '')
        self.assertEqual(result['messages'][1]['tool_calls'], source[1]['tool_calls'])
        self.assertEqual(result['messages'][2]['content'], 'RESULT')
        self.assertEqual(len(result['transformations']), 1)

    def test_later_user_and_preuser_assistant_rejected(self):
        for source in [self.history() + [{'role': 'user', 'content': 'Again'}],
                       [{'role': 'assistant', 'content': 'Before user'}] + self.history()]:
            with self.assertRaises(ValueError):
                project_pre_action_text(source)

    def test_existing_reasoning_not_overwritten(self):
        source = self.history()
        source[1]['reasoning'] = 'Existing'
        with self.assertRaises(ValueError):
            project_pre_action_text(source)

    def test_plain_assistant_response_not_reclassified(self):
        source = [{'role': 'user', 'content': 'Hello'}, {'role': 'assistant', 'content': 'Hello'}]
        result = project_pre_action_text(source)
        self.assertEqual(result['messages'], source)
        self.assertEqual(result['transformations'], [])
