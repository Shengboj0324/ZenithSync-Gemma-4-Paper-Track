import copy
import json
import unittest

from zenithsync.replay_history import mini_replay_history


class MiniReplayHistoryTests(unittest.TestCase):
    def setUp(self):
        self.source = [{'role': 'user', 'content': 'issue'}]
        for index, command in enumerate(('git diff',
                'echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && cat patch.txt')):
            self.source.append({'role': 'assistant', 'content': 'source thought',
                'tool_calls': [{'id': str(index), 'type': 'function', 'function': {
                    'name': 'bash', 'arguments': {'command': command}}}]})
            if index == 0:
                self.source.append({'role': 'tool', 'tool_call_id': str(index),
                                    'content': 'SOURCE RESPONSE MUST NOT BE REUSED'})
        self.events = [
            {'source_index': 1, 'adapter_authored': False, 'name': 'run_command',
             'arguments': {'command': 'git diff'},
             'result': {'status': 'ok', 'stdout': 'fresh captured bytes'}},
            {'source_index': None, 'adapter_authored': True, 'name': 'run_command',
             'arguments': {'command': 'explicit cleanup'}, 'result': {'status': 'ok'}},
            {'source_index': None, 'adapter_authored': True, 'name': 'submit_patch',
             'arguments': {}, 'result': {'status': 'ok'}}]

    def project(self, events):
        return mini_replay_history(events, source_messages=self.source,
            system='native system', problem='issue', allowed_tools={'run_command', 'submit_patch'})

    def test_preserves_fresh_bytes_and_adapter_authorship(self):
        result = self.project(self.events)
        encoded = json.dumps(result['messages'])
        self.assertIn('fresh captured bytes', encoded)
        self.assertNotIn('source thought', encoded)
        self.assertNotIn('SOURCE RESPONSE', encoded)
        self.assertEqual([row['adapter_authored'] for row in result['mapping']], [False, True, True])
        self.assertEqual([row['source_index'] for row in result['mapping']], [1, None, None])
        self.assertFalse(result['training_approved'])

    def test_missing_changed_or_misattributed_actions_reject(self):
        for change in ('missing', 'command', 'order', 'authorship', 'failed', 'extra'):
            events = copy.deepcopy(self.events)
            if change == 'missing':
                events.pop(0)
            elif change == 'command':
                events[0]['arguments']['command'] = 'git reset --hard'
            elif change == 'order':
                events.reverse()
            elif change == 'authorship':
                events[1]['source_index'] = 3
                events[1]['adapter_authored'] = False
            elif change == 'failed':
                events[-1]['result']['status'] = 'error'
            else:
                events.append(copy.deepcopy(events[-1]))
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.project(events)


if __name__ == '__main__':
    unittest.main()
