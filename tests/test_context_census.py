import unittest

from scripts.census_trajectory_context import summarize


class ContextCensusTests(unittest.TestCase):
    def test_boundaries_and_conservation(self):
        result = summarize([9, 1, 8, 8, 16], [8, 16])
        self.assertEqual(result['input_tokens'], 42)
        self.assertEqual(result['quantiles'], {'50': 8, '90': 16, '95': 16, '99': 16})
        self.assertEqual(result['caps']['8'], {'within_cap': 3, 'over_cap': 2,
                                            'input_tokens_in_within_cap_histories': 17})
        for cap in result['caps'].values():
            self.assertEqual(cap['within_cap'] + cap['over_cap'], 5)

    def test_singleton_and_invalid_counts(self):
        self.assertEqual(summarize([3], [1])['quantiles'], dict.fromkeys(('50', '90', '95', '99'), 3))
        for lengths, caps in (([], [8]), ([0], [8]), ([True], [8]), ([1.5], [8]),
                              ([1], []), ([1], [8, 8]), ([1], [False])):
            with self.subTest(lengths=lengths, caps=caps), self.assertRaises(ValueError):
                summarize(lengths, caps)
