import copy
import unittest

from zenithsync.mini_source_history import convert_mini_history
from zenithsync.trajectory_import import SourceHistoryError


def message(role, content='', calls=None, reasoning=None):
    return {'role': role, 'content': content, 'tool_calls': calls,
            'reasoning_content': reasoning}


def call(identifier, command):
    return {'id': identifier, 'type': 'function',
            'function': {'name': 'bash', 'arguments': {'command': command}}}


def history():
    return [message('system', 'Source instructions'), message('user', 'Repair'),
            message('assistant', 'Inspect', [call('a', 'pwd')], 'Source reasoning'),
            message('tool', 'An unchanged observation'),
            message('assistant', '', [call('b', 'arbitrary final command')])]


class MiniSourceHistoryTests(unittest.TestCase):
    def test_links_text_reasoning_and_unexecuted_terminal_preserved(self):
        original = history()
        result = convert_mini_history(original)
        self.assertEqual(result['response_links'], [{'response_index': 3,
            'call_index': 2, 'call_id': 'a', 'basis': 'inferred_single_pending_call'}])
        self.assertEqual(result['messages'][2]['reasoning_content'], 'Source reasoning')
        self.assertEqual(result['messages'][3]['content'], original[3]['content'])
        self.assertEqual(len(result['messages']), len(original))
        self.assertIn('not_execution_evidence', result['terminal_status'])
        self.assertFalse(result['training_approved'])
        result['messages'][-1]['tool_calls'][0]['function']['arguments']['command'] = 'changed'
        self.assertEqual(original, history())

    def test_ambiguous_missing_duplicate_and_interrupted_links_rejected(self):
        variants = []
        parallel = history(); parallel[2]['tool_calls'].append(call('c', 'ls')); variants.append(parallel)
        duplicate = history(); duplicate[-1]['tool_calls'][0]['id'] = 'a'; variants.append(duplicate)
        interrupted = history(); interrupted.insert(3, message('user', 'interrupt')); variants.append(interrupted)
        orphan = history(); orphan.insert(2, message('tool', 'orphan')); variants.append(orphan)
        variants.extend([history()[:-1], history() + [message('tool', 'final result')]])
        for variant in variants:
            with self.subTest(variant=variant), self.assertRaises(SourceHistoryError):
                convert_mini_history(variant)

    def test_bad_arguments_tool_names_and_reasoning_rejected(self):
        for arguments in ({'command': ''}, {'command': 2}, {'command': 'pwd', 'timeout': 10},
                          '{"command":"pwd","command":"ls"}'):
            variant = history(); variant[2]['tool_calls'][0]['function']['arguments'] = arguments
            with self.subTest(arguments=arguments), self.assertRaises(SourceHistoryError):
                convert_mini_history(variant)
        for role_index, value in ((0, 'reason'), (3, 'reason'), (2, 42)):
            variant = history(); variant[role_index]['reasoning_content'] = value
            with self.assertRaises(SourceHistoryError): convert_mini_history(variant)
        variant = history(); variant[2]['tool_calls'][0]['function']['name'] = 'execute_bash'
        with self.assertRaises(SourceHistoryError): convert_mini_history(variant)

    def test_no_source_fields_silently_discarded(self):
        variant = copy.deepcopy(history()); variant[3]['tool_call_id'] = 'a'
        with self.assertRaisesRegex(SourceHistoryError, 'schema_drift'):
            convert_mini_history(variant)


if __name__ == '__main__':
    unittest.main()
