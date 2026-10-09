"""Deadline-bound full-checkpoint qualification; does not start or stop Pods."""

import argparse
from datetime import datetime
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, inventory, load_json
from zenithsync.process_supervisor import run_bounded
from scripts.run_p1_training_worker import require_volume


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--manifest-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--volume-root', type=Path, default=Path('/workspace'))
    parser.add_argument('--session-deadline', required=True,
                        help='Previously approved absolute ISO-8601 deadline with timezone')
    args = parser.parse_args()
    deadline = datetime.fromisoformat(args.session_deadline)
    require_volume(args.output, args.volume_root)
    args.output.mkdir(parents=True, exist_ok=False)
    worker_output = args.output / 'worker'
    command = [sys.executable, str(ROOT / 'scripts/run_p1_training_worker.py'),
               '--model', str(args.model.resolve()), '--manifest', str(args.manifest.resolve()),
               '--manifest-sha256', args.manifest_sha256, '--output', str(worker_output.resolve()),
               '--volume-root', str(args.volume_root.resolve())]
    env = dict(os.environ)
    env['PYTHONUNBUFFERED'] = '1'
    lifecycle = run_bounded(command, log_path=args.output / 'worker.log', deadline=deadline,
        maximum_seconds=900, env=env, stop_path=args.output / 'STOP')
    (args.output / 'lifecycle.json').write_bytes(canonical_json(lifecycle))
    if not lifecycle['success']:
        raise RuntimeError('Worker failed, timed out, or did not clean up its process group')
    worker = load_json(worker_output / 'worker.json')
    qualification = load_json(worker_output / 'qualification/receipt.json')
    if (worker['status'] != 'full_checkpoint_one_update_reload_passed'
            or qualification['status'] != 'one_update_and_reload_passed'
            or qualification['trainable_parameters'] != 30607360):
        raise ValueError('Worker artifacts do not establish full-checkpoint qualification')
    # The worker's inventory predates its receipt; verify only those exact files
    # independently, allowing the receipt itself as the sole extra file.
    artifact_root = worker_output / 'qualification'
    from zenithsync.artifacts import file_record
    expected = qualification['artifacts']['files']
    actual = inventory(artifact_root, kind='fixture', source='qualification', revision='001')['files']
    actual = [row for row in actual if row['path'] != 'receipt.json']
    if actual != expected:
        raise ValueError('Qualification artifacts changed after worker verification')
    receipt = {'schema_version': 1, 'status': 'supervised_full_checkpoint_qualification_passed',
               'worker_receipt': file_record(worker_output / 'worker.json'),
               'qualification_receipt': file_record(artifact_root / 'receipt.json'),
               'scope': 'Single fixture/update/reload; not corpus, serving or repair quality qualification'}
    (args.output / 'receipt.json').write_bytes(canonical_json(receipt))
    print('Bounded full-checkpoint qualification passed; Pod billing state unchanged')


if __name__ == '__main__':
    main()
