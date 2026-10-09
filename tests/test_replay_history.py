import copy
import unittest
from zenithsync.replay_history import native_replay_history


def event(index=2):
    result={'status':'ok','text':'fresh observation'}
    return {'source_index':index,'kind':'finish','result':result,
            'native_calls':[{'name':'submit_patch','arguments':{},'result':result}]}


class ReplayHistoryTests(unittest.TestCase):
    def project(self,events):
        return native_replay_history(events,system='system',problem='issue',allowed_tools={'submit_patch'})

    def test_fresh_result_and_stable_linkage(self):
        r=self.project([event()])
        assistant,tool=r['messages'][-2:]
        self.assertEqual(tool['tool_call_id'],assistant['tool_calls'][0]['id'])
        self.assertIn('fresh observation',tool['content'])
        self.assertEqual(assistant['content'],'')

    def test_mismatch_and_missing_calls_reject(self):
        for change in ('mismatch','missing','parallel'):
            e=copy.deepcopy(event())
            if change=='mismatch':e['result']={'status':'error'}
            elif change=='missing':e['native_calls']=[]
            else:e['native_calls']*=2
            with self.subTest(change=change):
                with self.assertRaises(ValueError):self.project([e])

    def test_reordered_events_reject(self):
        with self.assertRaises(ValueError):self.project([event(4),event(2)])

    def test_reasoning_not_fabricated_as_a_tool(self):
        think={'source_index':0,'kind':'think','native_calls':[],
               'result':{'status':'not_executed'}}
        r=self.project([think,event()])
        self.assertEqual(len(r['messages']),4)
        self.assertFalse(r['training_approved'])


if __name__=='__main__':unittest.main()
