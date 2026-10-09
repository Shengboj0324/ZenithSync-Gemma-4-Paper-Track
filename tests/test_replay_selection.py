import unittest
from scripts.plan_trajectory_replays import action_budget


class ReplaySelectionTests(unittest.TestCase):
    def test_counting_does_not_charge_reasoning_or_submission(self):
        calls=[('think',{}),('execute_bash',{'command':'pwd'}),
               ('str_replace_editor',{'command':'view'}),('finish',{})]
        messages=[{'tool_calls':[{'function':{'name':name,'arguments':args}}]} for name,args in calls]
        result=action_budget(messages)
        self.assertEqual(result['estimated_native_charged_calls'],2)
        self.assertEqual(sum(result['source_tool_counts'].values()),4)
        self.assertEqual(result['known_adapter_flags'],{})

    def test_unknown_semantics_remain_flagged(self):
        messages=[{'tool_calls':[
            {'function':{'name':'execute_bash','arguments':{'command':'','is_input':True}}},
            {'function':{'name':'str_replace_editor','arguments':{'command':'undo_edit'}}}]}]
        self.assertEqual(action_budget(messages)['known_adapter_flags'],
            {'interactive_shell':1,'empty_shell_command':1,'unqualified_editor_action':1})


if __name__=='__main__':unittest.main()
