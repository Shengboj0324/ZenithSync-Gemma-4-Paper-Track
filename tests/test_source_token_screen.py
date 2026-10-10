"""Protect metadata-only screening from reserved data and identity substitution."""
import unittest

from scripts.screen_source_token_cost import select_rows


class SourceTokenSelectionTests(unittest.TestCase):
    def setUp(self):
        self.row = {'trajectory_id': 'trace', 'instance_id': 'task',
                    'repo': 'owner/project', 'dataset': 'source',
                    'shard_sha256': 'a'*64, 'row_index': 4,
                    'reserved_repository_exact_match': False}

    def select(self, cohort, census=None, reserved=frozenset()):
        return select_rows(cohort, [self.row] if census is None else census,
                           shard_sha256='a'*64, reserved=reserved)

    def test_selects_only_requested_shard(self):
        other = dict(self.row, trajectory_id='other', shard_sha256='b'*64)
        self.assertEqual(self.select([self.row, other], [self.row, other]),
                         {'trace': self.row})

    def test_rejects_reserved_name_even_if_both_flags_are_false(self):
        row = dict(self.row, repo='OWNER/PROJECT')
        with self.assertRaisesRegex(ValueError, 'Reserved'):
            self.select([row], [row], {'owner/project'})

    def test_rejects_identity_substitution_in_every_linkage_field(self):
        for key in ('instance_id', 'repo', 'dataset', 'shard_sha256', 'row_index'):
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'identity'):
                self.select([dict(self.row, **{key: 'substituted'})])

    def test_rejects_duplicate_cohort_and_census(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate cohort'):
            self.select([self.row, self.row])
        with self.assertRaisesRegex(ValueError, 'Duplicate census'):
            self.select([self.row], [self.row, self.row])

    def test_rejects_reserved_flag_on_unselected_shard(self):
        row = dict(self.row, shard_sha256='b'*64,
                   reserved_repository_exact_match=True)
        with self.assertRaisesRegex(ValueError, 'Reserved'):
            self.select([row], [row])


if __name__ == '__main__':
    unittest.main()
