"""Exercise metadata projections without reading trajectory or patch bodies."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from zenithsync.artifacts import file_record

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(importlib.util.find_spec('pyarrow'), 'Requires isolated data runtime')
class TrajectoryMetadataAuditTests(unittest.TestCase):
    def run_audit(self, *, new_schema, outcome=1):
        import pyarrow as pa
        import pyarrow.parquet as pq
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            values = {'repo': ['example/repo'], 'instance_id': ['example__repo-1'],
                      'license': ['MIT'], 'trajectory_id': ['trace-1']}
            if new_schema:
                values.update(language=['python'], resolved=[outcome],
                    hf_dataset_name=['nebius/SWE-rebench-V2'], tools=[[]],
                    metadata=[{'reference_patch': {'patch': 'must not be inspected'}}],
                    messages=[[{'role': 'invalid-body-role', 'content': 'not inspected'}]])
                dataset = 'nvidia/Open-SWE-Traces'
            else:
                values.update(dataset=['source'], model_patch=['not inspected'],
                    trajectory=[[{'role': 'invalid-body-role', 'content': 'not inspected'}]])
                dataset = 'nvidia/SWE-Hero-openhands-trajectories'
            shard = root / 'data.parquet'
            pq.write_table(pa.table(values), shard)
            intake = root / 'intake.json'
            intake.write_text(json.dumps({'dataset': dataset, 'revision': 'a' * 40,
                                         'downloaded': {'data.parquet': file_record(shard)}}))
            output = root / 'output'
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/audit_trajectory_metadata.py'),
                '--shard', str(shard), '--intake', str(intake), '--output', str(output)],
                capture_output=True, text=True, timeout=30)
            report = json.loads((output / 'receipt.json').read_text()) if output.exists() else None
            return result, report

    def test_both_schemas_only_project_metadata(self):
        for new in (False, True):
            with self.subTest(new_schema=new):
                result, report = self.run_audit(new_schema=new)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(report['rows'], 1)
                self.assertFalse(report['trajectory_or_patch_bodies_read'])
                self.assertFalse(report['training_approval'])
                self.assertNotIn('messages', report['read_columns'])
                self.assertNotIn('metadata', report['read_columns'])
                self.assertEqual(report['publisher_outcome_rows'], {'1': 1} if new else {})

    def test_unknown_outcome_preserved_and_invalid_outcomes_rejected(self):
        result, report = self.run_audit(new_schema=True, outcome=-1)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report['publisher_outcome_rows'], {'-1': 1})
        for outcome in (True, 2, None):
            with self.subTest(outcome=outcome):
                result, report = self.run_audit(new_schema=True, outcome=outcome)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('Invalid language or publisher outcome', result.stderr)
                self.assertIsNone(report)


if __name__ == '__main__':
    unittest.main()
