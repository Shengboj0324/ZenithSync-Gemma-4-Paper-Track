"""Assess linked replay evidence without approving training or starting a GPU."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record
from zenithsync.replay_admission import assess_replay_bundle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('attempt', 'history', 'grade', 'tokens', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--max-input-tokens', type=int, default=32768)
    parser.add_argument('--output-reserve', type=int, default=8192)
    parser.add_argument('--max-tool-calls', type=int, default=40)
    args = parser.parse_args()
    result = assess_replay_bundle(attempt=args.attempt, history=args.history,
        grade=args.grade, tokens=args.tokens, max_input_tokens=args.max_input_tokens,
        output_reserve=args.output_reserve, max_tool_calls=args.max_tool_calls)
    result['implementation'] = file_record(ROOT / 'zenithsync/replay_admission.py')
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'report.json').write_bytes(canonical_json(result))
    print({key: result[key] for key in ('mechanical_checks_passed', 'mechanical_blockers', 'training_approved')})


if __name__ == '__main__':
    main()
