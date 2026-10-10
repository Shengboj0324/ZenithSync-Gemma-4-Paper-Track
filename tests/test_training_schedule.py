import copy
import unittest
from zenithsync.training_schedule import make_schedule,iter_updates,initial_cursor


class TrainingScheduleTests(unittest.TestCase):
    def plan(self,**changes):
        args={'corpus_content_sha256':'a'*64,'seed':7,'target_supervised_tokens':19,
              'max_epochs':3,'max_update_supervised_tokens':7}
        args.update(changes)
        return make_schedule([{'example_id':'a','input_tokens':9,'supervised_tokens':5},
                              {'example_id':'b','input_tokens':6,'supervised_tokens':3}],**args)

    def test_every_example_once_per_complete_epoch_and_bounded_overshoot(self):
        p=self.plan();u=list(iter_updates(p));last=u[-1]['next_cursor']
        self.assertGreaterEqual(last['consumed_supervised_tokens'],19)
        self.assertLess(last['consumed_supervised_tokens'],19+5)
        self.assertEqual(sorted(r['example_id'] for x in u if x['epoch']==0 for r in x['examples']),['a','b'])
        self.assertTrue(all(0<x['supervised_tokens']<=7 for x in u))
        self.assertEqual(last['consumed_input_tokens'],sum(x['input_tokens'] for x in u))
        self.assertEqual(last['consumed_supervised_tokens'],sum(x['supervised_tokens'] for x in u))

    def test_resume_at_every_boundary_reproduces_suffix(self):
        p=self.plan();all_updates=list(iter_updates(p))
        for i in range(len(all_updates)+1):
            cursor=initial_cursor(p) if i==0 else all_updates[i-1]['next_cursor']
            self.assertEqual(list(iter_updates(p,resume=cursor)),all_updates[i:])

    def test_rejects_changed_plan_or_corrupt_cursor(self):
        p=self.plan();cursor=list(iter_updates(p))[0]['next_cursor']
        for key,value in [('consumed_supervised_tokens',999),('completed_updates',True),
                          ('prefix_sha256','0'*64),('completed_updates',1000)]:
            with self.subTest(key=key),self.assertRaises(ValueError):
                list(iter_updates(p,resume={**cursor,key:value}))
        with self.assertRaises(ValueError):list(iter_updates(self.plan(seed=8),resume=cursor))
        damaged=copy.deepcopy(p);damaged['examples'][0]['input_tokens']+=1
        with self.assertRaises(ValueError):list(iter_updates(damaged))

    def test_no_implicit_repetition_or_truncation(self):
        for values in [{'target_supervised_tokens':25},{'max_update_supervised_tokens':4},
                       {'seed':True},{'max_epochs':0}]:
            with self.subTest(values=values),self.assertRaises(ValueError):self.plan(**values)


if __name__=='__main__':unittest.main()
