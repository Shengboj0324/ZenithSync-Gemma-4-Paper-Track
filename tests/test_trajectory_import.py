import copy
import unittest

from zenithsync.trajectory_import import convert_swe_hero_history, SourceHistoryError


def call(identifier, name, arguments='{}'):
    return {'role': 'assistant', 'content': None, 'tool_calls': [
        {'id': identifier, 'type': 'function', 'function': {'name': name, 'arguments': arguments}}]}


class TrajectoryImportTests(unittest.TestCase):
    def history(self):
        return [{'role': 'user', 'content': 'Inspect', 'tool_calls': None},
                call('existing-id', 'execute_bash', '{"command":"pwd"}'),
                {'role': 'tool', 'content': 'RESULT', 'tool_calls': None},
                call('existing-finish', 'finish')]

    def test_preserves_content_ids_and_records_inference(self):
        source = self.history()
        before = copy.deepcopy(source)
        result = convert_swe_hero_history(source)
        self.assertEqual(source, before)
        self.assertEqual(len(result['messages']), len(source))
        self.assertEqual(result['messages'][2]['content'], 'RESULT')
        self.assertEqual(result['messages'][2]['tool_call_id'], 'existing-id')
        self.assertEqual(result['response_links'][0]['basis'], 'inferred_single_pending_call')
        self.assertEqual(result['terminal_pending_call_id'], 'existing-finish')
        self.assertEqual(result['messages'][-1]['role'], 'assistant')

    def test_parallel_calls_never_assume_response_order(self):
        source = self.history()
        source[1]['tool_calls'].append(call('second', 'think')['tool_calls'][0])
        with self.assertRaisesRegex(SourceHistoryError, 'ambiguous_parallel'):
            convert_swe_hero_history(source)

    def test_orphan_and_interruption_rejected(self):
        source = self.history()
        for invalid in [source[2:], source[:2] + source[3:]]:
            with self.assertRaises(SourceHistoryError):
                convert_swe_hero_history(invalid)

    def test_missing_or_nonfinish_terminal_call_rejected(self):
        source = self.history()
        for invalid in [source[:-1], source[:-1] + [call('end', 'execute_bash')]]:
            with self.assertRaisesRegex(SourceHistoryError, 'missing_terminal_finish'):
                convert_swe_hero_history(invalid)

    def test_duplicate_ids_bad_arguments_and_unknown_tools_rejected(self):
        for final in [call('existing-id', 'finish'), call('new', 'unknown'),
                      call('new', 'finish', '{"a":1,"a":2}')]:
            with self.assertRaises(SourceHistoryError):
                convert_swe_hero_history(self.history()[:-1] + [final])
