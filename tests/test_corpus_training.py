"""Synthetic admission fixtures exercise the complete local update path."""
import copy
import importlib.util
import unittest


@unittest.skipUnless(importlib.util.find_spec('torch'), 'Torch runtime required')
class CorpusTrainingTests(unittest.TestCase):
    def setUp(self):
        from tests.test_training_corpus import CorpusTests
        from tests.test_corpus_optimization import CorpusOptimizationTests
        from zenithsync.training_corpus import GATES, corpus_content_identity
        self.fixture = CorpusTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        fixture = self.fixture
        fixture.manifest['status'] = 'admitted'
        fixture.write('fixture-evidence.json', fixture.alignment_evidence())
        for gate in GATES:
            fixture.write(gate+'.json', {
                'gate': gate, 'status': 'passed',
                'corpus_content_sha256': corpus_content_identity(fixture.manifest),
                'evidence': [fixture.ref('fixture-evidence.json')]})
            fixture.manifest['admission'][gate] = fixture.ref(gate+'.json')
        fixture.load(purpose='training')
        self.corpus = fixture.indexed(purpose='training')
        self.model = CorpusOptimizationTests().setup_model()
        self.update = {'examples': [{'example_id': 'trace1', 'input_tokens': 3,
                                    'supervised_tokens': 1}],
                       'input_tokens': 3, 'supervised_tokens': 1}

    def test_indexed_update_matches_eager_and_releases_tensors(self):
        import torch
        import weakref
        from zenithsync.corpus_training import train_corpus_update
        from zenithsync.corpus_optimization import token_weighted_step
        eager = copy.deepcopy(self.model)
        left = torch.optim.AdamW(self.model.parameters(), lr=0.01, foreach=False)
        right = torch.optim.AdamW(eager.parameters(), lr=0.01, foreach=False)
        refs = []
        def observe(module, args, kwargs):
            refs.extend(weakref.ref(tensor) for tensor in kwargs.values())
        handle = self.model.register_forward_pre_hook(observe, with_kwargs=True)
        self.addCleanup(handle.remove)
        actual = train_corpus_update(self.model, left, self.corpus, self.update, max_sequence_tokens=8)
        expected = token_weighted_step(eager, right, [{
            'input_ids': torch.tensor([[1, 2, 3]]),
            'labels': torch.tensor([[-100, -100, 3]]),
            'attention_mask': torch.tensor([[1, 1, 1]])}])
        self.assertEqual(actual, expected)
        for a, b in zip(self.model.parameters(), eager.parameters(), strict=True):
            self.assertTrue(torch.equal(a, b))
        self.assertTrue(all(ref() is None for ref in refs))

    def test_changed_tokens_bad_counts_and_capacity_cannot_step(self):
        import torch
        from zenithsync.corpus_training import train_corpus_update
        before = copy.deepcopy(self.model.state_dict())
        optimizer = torch.optim.AdamW(self.model.parameters())
        invalid = copy.deepcopy(self.update)
        invalid['supervised_tokens'] = 2
        for update, capacity in [(invalid, 8), (self.update, 2)]:
            with self.assertRaises(ValueError):
                train_corpus_update(self.model, optimizer, self.corpus, update,
                                    max_sequence_tokens=capacity)
        self.fixture.write('tokens.json', {})
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            train_corpus_update(self.model, optimizer, self.corpus, self.update, max_sequence_tokens=8)
        self.assertFalse(optimizer.state)
        for name, value in self.model.state_dict().items():
            self.assertTrue(torch.equal(value, before[name]))

    def test_stream_underrun_overrun_and_late_exception_cannot_step(self):
        import torch
        from zenithsync.corpus_optimization import streamed_token_weighted_step
        batch = {'input_ids': torch.tensor([[1, 2, 3]]),
                 'labels': torch.tensor([[-100, -100, 3]]),
                 'attention_mask': torch.tensor([[1, 1, 1]])}
        def failing_stream():
            yield batch
            raise ValueError('late read failure')
        for stream, total in [(iter([batch]), 2), (iter([batch, batch]), 1), (failing_stream(), 2)]:
            optimizer = torch.optim.AdamW(self.model.parameters())
            before = copy.deepcopy(self.model.state_dict())
            with self.assertRaises(ValueError):
                streamed_token_weighted_step(self.model, optimizer, stream,
                                             expected_supervised_tokens=total)
            self.assertFalse(optimizer.state)
            self.assertTrue(all(p.grad is None for p in self.model.parameters()))
            for name, value in self.model.state_dict().items():
                self.assertTrue(torch.equal(value, before[name]))

    def test_stream_releases_previous_batch_before_requesting_next(self):
        import torch
        import weakref
        from zenithsync.corpus_optimization import streamed_token_weighted_step
        references = []
        def batches():
            for token in (3, 4, 5):
                self.assertTrue(all(ref() is None for ref in references))
                batch = {'input_ids': torch.tensor([[1, 2, token]]),
                         'labels': torch.tensor([[-100, -100, token]]),
                         'attention_mask': torch.tensor([[1, 1, 1]])}
                references[:] = [weakref.ref(value) for value in batch.values()]
                yield batch
                del batch
        optimizer = torch.optim.AdamW(self.model.parameters())
        report = streamed_token_weighted_step(self.model, optimizer, batches(),
                                              expected_supervised_tokens=3)
        self.assertEqual(report['microbatch_supervised_tokens'], [1, 1, 1])
        self.assertTrue(all(ref() is None for ref in references))


if __name__ == '__main__':
    unittest.main()
