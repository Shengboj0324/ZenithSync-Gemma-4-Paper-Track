import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from zenithsync.artifacts import canonical_json, file_record

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(importlib.util.find_spec('pyarrow'), 'pyarrow required')
class CorpusCensusTests(unittest.TestCase):
    def test_cross_shard_duplicates_and_reserved_repositories(self):
        import pyarrow as pa
        import pyarrow.parquet as pq
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            sources = []
            for shard, rows in enumerate([
                [('fixture/repo', 'issue-a', 'trace-1'), ('fixture/repo', 'issue-a', 'trace-2')],
                [('fixture/repo', 'issue-a', 'trace-1'), ('PSF/REQUESTS', 'issue-b', 'trace-3')],
            ]):
                path = base / f'{shard}.parquet'
                pq.write_table(pa.Table.from_pylist([dict(repo=r, instance_id=i, trajectory_id=t,
                    license='fixture-unverified', dataset='fixture') for r, i, t in rows]), path)
                receipt = base / f'{shard}.json'
                receipt.write_bytes(canonical_json({'dataset': 'nvidia/SWE-Hero-openhands-trajectories',
                    'revision': '150bc119e52c647216fce285fd801f16b6fd745b',
                    'downloaded': {path.name: file_record(path)}}))
                sources.append({'shard': str(path), 'intake': str(receipt)})
            spec = base / 'sources.json'
            spec.write_bytes(canonical_json(sources))
            output = base / 'output'
            command = [sys.executable, str(ROOT / 'scripts/census_trajectory_corpus.py'),
                       '--sources', str(spec), '--output', str(output)]
            result = subprocess.run(command, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((output / 'report.json').read_text())
            self.assertEqual(report['rows'], 4)
            self.assertEqual(report['unique_repository_issue_pairs'], 2)
            self.assertEqual(report['duplicate_trajectory_id_rows'], 1)
            self.assertEqual(report['extra_trajectories_for_repeated_issues'], 2)
            self.assertEqual(report['reserved_repository_exact_match_rows'], {'psf/requests': 1})
            self.assertFalse(report['training_approved'])
            self.assertFalse(report['trajectory_or_patch_bodies_read'])
            # Supplying the same shard twice must not inflate corpus coverage.
            spec.write_bytes(canonical_json([sources[0], sources[0]]))
            command[-1] = str(base / 'duplicate-output')
            result = subprocess.run(command, capture_output=True, text=True, timeout=30)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Unverified or repeated shard', result.stderr)


if __name__ == '__main__':
    unittest.main()
