import copy
import os
import unittest

from zenithsync.optimizer_checkpoint import capture_adamw_checkpoint, restore_adamw_checkpoint


@unittest.skipUnless(os.environ.get('ZENITHSYNC_TEST_TORCH') == '1',
                     'Requires explicitly selected Torch environment')
class OptimizerCheckpointTests(unittest.TestCase):
    def setUp(self):
        import torch
        self.torch = torch
        torch.set_num_threads(1)
        self.rows = [('left', torch.nn.Parameter(torch.tensor([0.5, -0.7], dtype=torch.float64))),
                     ('right', torch.nn.Parameter(torch.tensor([0.1, 0.2], dtype=torch.float64)))]
        self.optimizer = torch.optim.AdamW([value for _, value in self.rows], lr=.01,
                                           weight_decay=.02, foreach=False, fused=False)
        self.step(self.rows, self.optimizer)
        self.payload = copy.deepcopy(capture_adamw_checkpoint(self.optimizer, self.rows, completed_steps=1))

    def step(self, rows, optimizer):
        optimizer.zero_grad(set_to_none=True)
        sum((value.square().sum() + value.sum() * .3) for _, value in rows).backward()
        optimizer.step()

    def test_next_update_matches_continuous_run(self):
        resumed = [(name, self.torch.nn.Parameter(value.detach().clone())) for name, value in self.rows]
        optimizer = self.torch.optim.AdamW([value for _, value in resumed], lr=.01,
                                           weight_decay=.02, foreach=False, fused=False)
        restore_adamw_checkpoint(optimizer, resumed, self.payload)
        self.step(self.rows, self.optimizer)
        self.step(resumed, optimizer)
        for (_, left), (_, right) in zip(self.rows, resumed, strict=True):
            self.torch.testing.assert_close(left, right, rtol=0, atol=0)
        first = capture_adamw_checkpoint(self.optimizer, self.rows, completed_steps=2)
        second = capture_adamw_checkpoint(optimizer, resumed, completed_steps=2)
        for identity, state in first['optimizer_state']['state'].items():
            for key, value in state.items():
                self.torch.testing.assert_close(value, second['optimizer_state']['state'][identity][key], rtol=0, atol=0)

    def test_names_and_order_protect_equal_shapes(self):
        for rows in [list(reversed(self.rows)), [('renamed', self.rows[0][1]), self.rows[1]]]:
            with self.assertRaises(ValueError):
                restore_adamw_checkpoint(self.optimizer, rows, self.payload)

    def test_malformed_moments_and_steps_rejected(self):
        for field, value in [('step', 2), ('exp_avg', float('nan')),
                             ('exp_avg_sq', float('inf')), ('exp_avg_sq', -1)]:
            payload = copy.deepcopy(self.payload)
            payload['optimizer_state']['state'][0][field].fill_(value)
            with self.assertRaises(ValueError):
                restore_adamw_checkpoint(self.optimizer, self.rows, payload)

    def test_hyperparameter_drift_rejected_before_restore(self):
        optimizer = self.torch.optim.AdamW([value for _, value in self.rows], lr=.02,
                                           weight_decay=.02, foreach=False, fused=False)
        with self.assertRaisesRegex(ValueError, 'hyperparameters'):
            restore_adamw_checkpoint(optimizer, self.rows, self.payload)
        self.assertEqual(len(optimizer.state), 0)

    def test_ownership_and_missing_state_rejected(self):
        with self.assertRaisesRegex(ValueError, 'different parameters'):
            capture_adamw_checkpoint(self.optimizer, list(reversed(self.rows)), completed_steps=1)
        payload = copy.deepcopy(self.payload)
        del payload['optimizer_state']['state'][0]
        with self.assertRaisesRegex(ValueError, 'coverage'):
            restore_adamw_checkpoint(self.optimizer, self.rows, payload)
