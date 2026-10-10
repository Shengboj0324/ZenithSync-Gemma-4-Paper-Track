"""Assess an explicit V2 replay bundle without admitting it to training."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record, load_json
from zenithsync.mini_replay_admission import assess_mini_replay_bundle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('attempt', 'history', 'grade', 'tokens', 'candidate', 'profile', 'task', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--historical-source-map', type=Path,
                        help='Explicit original-code to archived-code mapping; exact hashes required')
    parser.add_argument('--session-resources', type=Path)
    args = vars(parser.parse_args())
    output = args.pop('output')
    historical_map = args.pop('historical_source_map')
    if historical_map is not None:
        map_identity = file_record(historical_map)
        args['historical_sources'] = load_json(historical_map)
    sources = {name: file_record(ROOT / name) for name in (
        'scripts/assess_mini_replay.py', 'zenithsync/mini_replay_admission.py',
        'zenithsync/replay_history.py', 'zenithsync/training_batch.py',
        'zenithsync/pytest_controls.py', 'zenithsync/submission_reconciliation.py')}
    for name in ('zenithsync/resource_replay_binding.py', 'zenithsync/session_resource_bundle.py',
                 'zenithsync/session_resource_replay.py'):
        sources[name] = file_record(ROOT / name)
    report = assess_mini_replay_bundle(root=ROOT, **args)
    if historical_map is not None:
        if file_record(historical_map) != map_identity:
            raise ValueError('Historical source mapping changed')
        report['historical_source_map'] = map_identity
    if any(file_record(ROOT / name) != identity for name, identity in sources.items()):
        raise ValueError('Assessment implementation changed')
    report['sources'] = sources
    output.mkdir(parents=True, exist_ok=False)
    (output / 'report.json').write_bytes(canonical_json(report))
    print({key: report[key] for key in ('mechanical_checks_passed', 'mechanical_blockers',
                                      'input_tokens', 'supervised_tokens')})


if __name__ == '__main__':
    main()
