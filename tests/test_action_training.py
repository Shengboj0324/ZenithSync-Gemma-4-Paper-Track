import copy
import unittest
from unittest.mock import Mock, patch

from zenithsync.action_training import action_prefix, action_training_tokens


def history():
    return [
        {'role': 'system', 'content': 'Use the tools.'},
        {'role': 'user', 'content': 'Repair the issue.'},
        {'role': 'assistant', 'content': '', 'tool_calls': [
            {'id': 'a', 'type': 'function', 'function': {
                'name': 'read_file', 'arguments': {'path': 'a.py'}}}]},
        {'role': 'tool', 'tool_call_id': 'a', 'name': 'read_file',
         'content': 'previous observation'},
        {'role': 'assistant', 'content': '', 'tool_calls': [
            {'id': 'b', 'type': 'function', 'function': {
                'name': 'edit_file', 'arguments': {'path': 'a.py', 'text': 'fix'}}}]},
        {'role': 'tool', 'tool_call_id': 'b', 'name': 'edit_file',
         'content': 'future outcome'},
    ]


class ActionPrefixTests(unittest.TestCase):
    allowed = {'read_file', 'edit_file'}

    def test_future_outcome_is_excluded_and_cannot_change_prefix(self):
        original = history()
        modified = copy.deepcopy(original)
        modified[-1]['content'] = 'different future outcome'
        first = action_prefix(original, target_index=4, allowed_tools=self.allowed)
        self.assertEqual(first, original[:5])
        self.assertEqual(first, action_prefix(modified, target_index=4,
                                             allowed_tools=self.allowed))
        first[-1]['tool_calls'][0]['function']['arguments']['text'] = 'changed'
        self.assertEqual(original[4]['tool_calls'][0]['function']['arguments']['text'], 'fix')

    def test_earlier_context_is_preserved_exactly(self):
        original = history()
        first = action_prefix(original, target_index=2, allowed_tools=self.allowed)
        self.assertEqual(first, original[:3])
        later = action_prefix(original, target_index=4, allowed_tools=self.allowed)
        self.assertEqual(later[:4], original[:4])

    def test_invalid_selection_or_history_rejected(self):
        for index in (True, -1, 0, 1, 3, 5, 6, 4.0):
            with self.subTest(index=index), self.assertRaises(ValueError):
                action_prefix(history(), target_index=index, allowed_tools=self.allowed)
        with self.assertRaises(ValueError):
            action_prefix(history()[:-1], target_index=2, allowed_tools=self.allowed)
        broken = history()
        broken[3]['tool_call_id'] = 'orphan'
        with self.assertRaises(ValueError):
            action_prefix(broken, target_index=4, allowed_tools=self.allowed)


class ActionTokenTests(unittest.TestCase):
    def encode(self, context=None, labels=None):
        tokenizer = Mock()
        tokenizer.apply_chat_template.return_value = [10, 11, 12] if context is None else context
        encoded = {'input_ids': [10, 11, 12, 13, 14],
                   'labels': [-100, 11, -100, -100, 14] if labels is None else labels}
        with patch('zenithsync.action_training.assistant_training_tokens', return_value=encoded):
            return action_training_tokens(tokenizer, history(), target_index=4,
                template_sha256='unused-test-double',
                allowed_tools={'read_file', 'edit_file'}, tools=[])

    def test_prior_assistant_is_masked_and_native_ids_preserved(self):
        result = self.encode()
        self.assertEqual(result['input_ids'], [10, 11, 12, 13, 14])
        self.assertEqual(result['labels'], [-100, -100, -100, -100, 14])
        self.assertEqual(result['supervised_tokens'], 1)
        self.assertEqual(result['context_tokens'], 3)
        self.assertFalse(result['training_approved'])

    def test_changed_context_empty_target_and_wrong_labels_rejected(self):
        for options in ({'context': [10, 99, 12]}, {'context': []},
                        {'labels': [-100, 11, -100, -100, -100]},
                        {'labels': [-100, 11, -100, -100, 99]}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                self.encode(**options)


if __name__ == '__main__':
    unittest.main()
