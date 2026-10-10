import copy
import importlib.util
from types import SimpleNamespace
import unittest

@unittest.skipUnless(importlib.util.find_spec('torch'),'Torch runtime required')
class CorpusOptimizationTests(unittest.TestCase):
    def setup_model(self):
        import torch
        class CausalModel(torch.nn.Module):
            def __init__(self):
                super().__init__();self.embedding=torch.nn.Embedding(8,4,dtype=torch.float64)
                self.output=torch.nn.Linear(4,8,dtype=torch.float64)
            def forward(self,input_ids,labels,attention_mask):
                logits=self.output(self.embedding(input_ids))
                loss=torch.nn.functional.cross_entropy(logits[:,:-1].reshape(-1,8),labels[:,1:].reshape(-1),ignore_index=-100)
                return SimpleNamespace(loss=loss)
        torch.manual_seed(23)
        return CausalModel()

    def examples(self):
        return [{'input_ids':[1,2,3,4],'labels':[-100,2,3,4]},
                {'input_ids':[1,5,6],'labels':[-100,-100,6]}]

    def batches(self,groups):
        import torch
        from zenithsync.training_batch import collate_training_examples
        return [{k:torch.tensor(v) for k,v in collate_training_examples(g,pad_token_id=0,vocab_size=8,max_length=8)['batch'].items()} for g in groups]

    def test_unequal_target_microbatches_match_full_loss_gradients_and_adamw(self):
        import torch
        from zenithsync.corpus_optimization import token_weighted_step
        full=self.setup_model();split=copy.deepcopy(full)
        opts=[torch.optim.AdamW(m.parameters(),lr=0.01,foreach=False) for m in [full,split]]
        examples=self.examples()
        a=token_weighted_step(full,opts[0],self.batches([examples]))
        b=token_weighted_step(split,opts[1],self.batches([[x] for x in examples]))
        self.assertEqual(b['microbatch_supervised_tokens'],[3,1]);self.assertEqual(a['supervised_tokens'],4)
        self.assertAlmostEqual(a['token_mean_loss'],b['token_mean_loss'],places=13)
        for x,y in zip(full.parameters(),split.parameters(),strict=True):
            torch.testing.assert_close(x.grad,y.grad,rtol=1e-12,atol=1e-12)
            torch.testing.assert_close(x,y,rtol=1e-12,atol=1e-12)
        for x,y in zip(opts[0].state.values(),opts[1].state.values(),strict=True):
            for key in x:torch.testing.assert_close(x[key],y[key],rtol=1e-12,atol=1e-12)

    def test_invalid_padding_rejected_before_update(self):
        import torch
        from zenithsync.corpus_optimization import token_weighted_step
        model=self.setup_model();before=copy.deepcopy(model.state_dict())
        optimizer=torch.optim.AdamW(model.parameters())
        batches=self.batches([self.examples()]);batches[0]['labels'][1,-1]=0
        with self.assertRaises(ValueError):token_weighted_step(model,optimizer,batches)
        for key,value in model.state_dict().items():self.assertTrue(torch.equal(value,before[key]))
        self.assertFalse(optimizer.state)

    def test_nonfinite_loss_does_not_step(self):
        import torch
        from zenithsync.corpus_optimization import token_weighted_step
        model=self.setup_model();before=copy.deepcopy(model.state_dict())
        model.forward=lambda **kwargs:SimpleNamespace(loss=next(model.parameters()).sum()*float('nan'))
        optimizer=torch.optim.AdamW(model.parameters())
        with self.assertRaises(ValueError):token_weighted_step(model,optimizer,self.batches([self.examples()]))
        for key,value in model.state_dict().items():self.assertTrue(torch.equal(value,before[key]))
        self.assertFalse(optimizer.state)

    def test_optimizer_and_data_cursor_resume_matches_uninterrupted(self):
        import torch
        from zenithsync.corpus_optimization import token_weighted_step
        from zenithsync.training_schedule import make_schedule,iter_updates
        from zenithsync.optimizer_checkpoint import capture_adamw_checkpoint,restore_adamw_checkpoint
        examples=self.examples();lookup={str(i):e for i,e in enumerate(examples)}
        metadata=[{'example_id':key,'input_tokens':len(e['input_ids']),
                   'supervised_tokens':sum(x!=-100 for x in e['labels'][1:])} for key,e in lookup.items()]
        plan=make_schedule(metadata,corpus_content_sha256='a'*64,seed=12,
                           target_supervised_tokens=8,max_epochs=2,max_update_supervised_tokens=3)
        model=self.setup_model();optimizer=torch.optim.AdamW(model.parameters(),lr=0.01,foreach=False)
        updates=list(iter_updates(plan));saved=None
        for update in updates:
            batches=self.batches([[lookup[r['example_id']]] for r in update['examples']])
            token_weighted_step(model,optimizer,batches)
            if update['step']==1:
                saved=(copy.deepcopy(model.state_dict()),copy.deepcopy(capture_adamw_checkpoint(
                    optimizer,list(model.named_parameters()),completed_steps=1)),update['next_cursor'])
        resumed=self.setup_model();resumed.load_state_dict(saved[0])
        resumed_optimizer=torch.optim.AdamW(resumed.parameters(),lr=0.01,foreach=False)
        restore_adamw_checkpoint(resumed_optimizer,list(resumed.named_parameters()),saved[1])
        for update in iter_updates(plan,resume=saved[2]):
            token_weighted_step(resumed,resumed_optimizer,self.batches(
                [[lookup[r['example_id']]] for r in update['examples']]))
        for x,y in zip(model.parameters(),resumed.parameters(),strict=True):self.assertTrue(torch.equal(x,y))
        for x,y in zip(optimizer.state.values(),resumed_optimizer.state.values(),strict=True):
            for key in x:self.assertTrue(torch.equal(x[key],y[key]))

if __name__=='__main__':unittest.main()
