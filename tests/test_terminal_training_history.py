import unittest

from zenithsync.training_masks import normalize_training_history


def action(name, identifier='a'):
    return {'role': 'assistant', 'content': '', 'tool_calls': [
        {'id': identifier, 'type': 'function', 'function': {'name': name, 'arguments': {}}}]}


class TerminalTrainingHistoryTests(unittest.TestCase):
    def test_default_still_rejects_missing_response(self):
        with self.assertRaises(ValueError):
            normalize_training_history([action('finish')], allowed_tools={'finish'})

    def test_opt_in_preserves_terminal_call_without_response(self):
        result = normalize_training_history([action('finish')], allowed_tools={'finish'},
                                            terminal_call_tools={'finish'})
        self.assertEqual(result, [action('finish')])

    def test_nonterminal_and_interrupted_calls_rejected(self):
        for history in [[action('execute_bash')],
                        [action('execute_bash'), action('finish', 'b')],
                        [{'role': 'assistant', 'content': 'Done'}]]:
            with self.assertRaises(ValueError):
                normalize_training_history(history, allowed_tools={'finish', 'execute_bash'},
                                           terminal_call_tools={'finish'})

    def test_invalid_terminal_registry_rejected(self):
        for registry in [set(), ['finish'], {'unknown'}]:
            with self.assertRaises(ValueError):
                normalize_training_history([action('finish')], allowed_tools={'finish'},
                                           terminal_call_tools=registry)
