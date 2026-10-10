import os
import unittest


@unittest.skipUnless(os.environ.get('ZENITHSYNC_TEST_TORCH') == '1',
                     'Explicit Torch/Transformers/PEFT runtime required')
class GemmaTrainingTests(unittest.TestCase):
    def test_real_peft_attachment_update_and_bound_restore(self):
        import torch
        from transformers import Gemma4TextConfig, Gemma4ForCausalLM
        from zenithsync.gemma_training import attach_training_adapter
        from zenithsync.adapter_checkpoint import frozen_state, capture_adapter_checkpoint, restore_adapter_checkpoint
        from zenithsync.corpus_optimization import token_weighted_step
        from zenithsync.training_schedule import make_schedule, iter_updates
        torch.set_num_threads(1)
        shapes = {f'model.layers.{i}.self_attn.q_proj':[16,16] for i in range(2)}
        def fresh():
            torch.manual_seed(91)
            config = Gemma4TextConfig(vocab_size=16,hidden_size=16,intermediate_size=32,
                num_hidden_layers=2,num_attention_heads=2,num_key_value_heads=1,
                num_global_key_value_heads=1,head_dim=8,global_head_dim=8,
                hidden_size_per_layer_input=0,attention_k_eq_v=True,
                layer_types=['sliding_attention','full_attention'],max_position_embeddings=16,
                sliding_window=8,use_cache=False,attention_dropout=0.0)
            config._attn_implementation = 'eager'
            return attach_training_adapter(Gemma4ForCausalLM(config),shapes)
        model = fresh()
        self.assertEqual(sum(p.numel() for p in model.parameters() if p.requires_grad),256)
        frozen = frozen_state(model)
        schedule = make_schedule([{'example_id':'fixture','input_tokens':3,'supervised_tokens':2}],
            corpus_content_sha256='a'*64,seed=1,target_supervised_tokens=4,max_epochs=2,
            max_update_supervised_tokens=2)
        bindings = {'base_manifest_sha256':'b'*64,'corpus_manifest_sha256':'c'*64,
                    'corpus_content_sha256':'a'*64,'schedule_sha256':schedule['schedule_sha256'],
                    'worker_config_sha256':'d'*64}
        def optimizer(m):return torch.optim.AdamW([p for p in m.parameters() if p.requires_grad],lr=0.001,foreach=False)
        batch = {'input_ids':torch.tensor([[2,3,4]]),'labels':torch.tensor([[-100,3,4]]),
                 'attention_mask':torch.tensor([[1,1,1]])}
        opt = optimizer(model)
        token_weighted_step(model,opt,[batch])
        payload = capture_adapter_checkpoint(model,opt,bindings=bindings,schedule=schedule,
            cursor=next(iter_updates(schedule))['next_cursor'],expected_frozen=frozen)
        expected = token_weighted_step(model,opt,[batch])
        restored = fresh();restored_opt = optimizer(restored)
        restore_adapter_checkpoint(restored,restored_opt,payload,bindings=bindings,
                                   schedule=schedule,expected_frozen=frozen)
        actual = token_weighted_step(restored,restored_opt,[batch])
        self.assertEqual(actual,expected)
        for name,value in model.state_dict().items():
            self.assertTrue(torch.equal(value,restored.state_dict()[name]),name)


if __name__ == '__main__':unittest.main()
