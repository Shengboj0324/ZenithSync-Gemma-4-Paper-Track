import unittest
from zenithsync.replay_observations import audit_observations


class ReplayObservationTests(unittest.TestCase):
    def event(self,result,index=1):
        return {'source_index':index,'native_calls':[{'name':'run_command',
                'arguments':{'command':'fixture'},'result':result}]}

    def test_missing_flag_is_unknown_not_false(self):
        r=audit_observations([self.event({'status':'ok','exit_code':0,'stdout':'PASSED'})])
        self.assertIsNone(r['calls'][0]['reported_truncation'])
        self.assertEqual(r['truncation_unspecified_calls'],1)
        self.assertFalse(r['training_approved'])

    def test_wrapped_error_retains_exit_code_and_output(self):
        r=audit_observations([self.event({'status':'error','details':{'exit_code':1,
                             'stdout':'','stderr':'','is_truncated':False}})])
        self.assertEqual(r['nonzero_exit_calls'],1)
        self.assertEqual(r['status_counts'],{'error':1})
        self.assertEqual(r['calls'][0]['text_fields']['details.stdout']['utf8_bytes'],0)

    def test_any_explicit_truncation_is_preserved(self):
        r=audit_observations([self.event({'status':'ok','is_truncated':False,
                                        'details':{'truncated':True}})])
        self.assertEqual(r['explicitly_truncated_calls'],1)

    def test_ambiguous_or_boolean_exit_code_rejected(self):
        for result in ({'status':'ok','exit_code':True},
                       {'status':'error','exit_code':1,'details':{'exit_code':2}}):
            with self.assertRaises(ValueError):audit_observations([self.event(result)])

    def test_duplicate_or_reordered_events_rejected(self):
        for indices in ((1,1),(2,1)):
            with self.assertRaises(ValueError):
                audit_observations([self.event({'status':'ok'},i) for i in indices])

    def test_text_hash_detects_observation_change(self):
        a=audit_observations([self.event({'status':'ok','stdout':'before'})])
        b=audit_observations([self.event({'status':'ok','stdout':'after'})])
        self.assertNotEqual(a['calls'][0]['result_sha256'],b['calls'][0]['result_sha256'])


if __name__=='__main__':unittest.main()
