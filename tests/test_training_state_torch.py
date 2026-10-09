"""Run explicitly in the qualified CPU Torch environment; optional in core CI."""

import hashlib
import os
import unittest

from zenithsync.training_state import fingerprint_state, require_identical_state


@unittest.skipUnless(os.environ.get('ZENITHSYNC_TEST_TORCH') == '1',
                     'Requires explicitly selected Torch environment')
class StateFingerprintTests(unittest.TestCase):
    def setUp(self):
        import torch
        self.torch = torch
        self.model = torch.nn.Linear(4, 2, dtype=torch.bfloat16)
        self.model.register_buffer('counter', torch.tensor(3))
        self.model.register_buffer('empty', torch.empty(0))

    def test_independent_bytes_and_chunk_boundaries(self):
        first = fingerprint_state(self.model, chunk_bytes=1)
        require_identical_state(first, fingerprint_state(self.model, chunk_bytes=7))
        for name, tensor in self.model.state_dict().items():
            raw = tensor.reshape(-1).view(self.torch.uint8).numpy().tobytes()
            self.assertEqual(first[name]['sha256'], hashlib.sha256(raw).hexdigest())
            self.assertEqual(first[name]['bytes'], len(raw))

    def test_buffers_and_parameters_detected(self):
        before = fingerprint_state(self.model)
        self.model.counter.add_(1)
        with self.assertRaisesRegex(ValueError, 'counter'):
            require_identical_state(before, fingerprint_state(self.model))
        before = fingerprint_state(self.model)
        with self.torch.no_grad():
            self.model.weight[0, 0].add_(1)
        with self.assertRaisesRegex(ValueError, 'weight'):
            require_identical_state(before, fingerprint_state(self.model))

    def test_exclusions_are_exact_and_validated(self):
        before = fingerprint_state(self.model, excluded_names=['bias'])
        with self.torch.no_grad():
            self.model.bias.add_(1)
        require_identical_state(before, fingerprint_state(self.model, excluded_names=['bias']))
        for names in [['bi'], ['bias', 'bias'], list(self.model.state_dict())]:
            with self.assertRaises(ValueError):
                fingerprint_state(self.model, excluded_names=names)

    def test_noncontiguous_and_meta_rejected(self):
        self.model.register_buffer('transpose', self.torch.ones(2, 3).T)
        with self.assertRaisesRegex(ValueError, 'transpose'):
            fingerprint_state(self.model)
        del self.model.transpose
        self.model.register_buffer('unmaterialized', self.torch.empty(2, device='meta'))
        with self.assertRaisesRegex(ValueError, 'unmaterialized'):
            fingerprint_state(self.model)

    def test_metadata_and_state_identity_changes(self):
        before = fingerprint_state(self.model)
        self.model.register_buffer('new_buffer', self.torch.tensor(1))
        with self.assertRaisesRegex(ValueError, 'added='):
            require_identical_state(before, fingerprint_state(self.model))
        del self.model.new_buffer
        self.model.counter = self.model.counter.reshape(1)
        with self.assertRaisesRegex(ValueError, 'counter'):
            require_identical_state(before, fingerprint_state(self.model))

    def test_invalid_chunk_sizes(self):
        for size in [True, 0, -1, 0.5]:
            with self.assertRaises(ValueError):
                fingerprint_state(self.model, chunk_bytes=size)


if __name__ == '__main__':
    unittest.main()
