import copy
import unittest

from zenithsync.training_batch import collate_training_examples


class TrainingBatchTests(unittest.TestCase):
    def test_padding_is_positional_even_when_pad_is_a_real_token(self):
        examples = [{'input_ids': [2, 0, 3], 'labels': [-100, 0, 3]},
                    {'input_ids': [2, 4], 'labels': [-100, 4]}]
        original = copy.deepcopy(examples)
        result = collate_training_examples(examples, pad_token_id=0, vocab_size=8, max_length=3)
        self.assertEqual(result['batch']['attention_mask'], [[1, 1, 1], [1, 1, 0]])
        self.assertEqual(result['batch']['labels'], [[-100, 0, 3], [-100, 4, -100]])
        self.assertEqual(result['per_example_supervised_tokens'], [2, 1])
        self.assertEqual(result['supervised_tokens'], 3)
        self.assertEqual(examples, original)
        result['batch']['input_ids'][0][0] = 7
        self.assertEqual(examples, original)

    def test_rejects_silent_loss_or_coverage_changes(self):
        bad = [[], [{'input_ids': [1, 2, 3, 4], 'labels': [-100, 2, 3, 4]}],
               [{'input_ids': [1, 2], 'labels': [-100]}],
               [{'input_ids': [1, 2], 'labels': [-100, 3]}],
               [{'input_ids': [1, 2], 'labels': [-100, -100]}],
               [{'input_ids': [1, 2], 'labels': [1, 2]}],
               [{'input_ids': [True, 2], 'labels': [-100, 2]}],
               [{'input_ids': [1, 8], 'labels': [-100, 8]}]]
        for example in bad:
            with self.subTest(example=example), self.assertRaises(ValueError):
                collate_training_examples(example, pad_token_id=0, vocab_size=8, max_length=3)


if __name__ == '__main__':
    unittest.main()
