"""Record paired JUnit outcomes without turning test counts into solve rates."""

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from zenithsync.artifacts import canonical_json, file_record
from zenithsync.evaluation import compare_junit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    inputs = {'baseline': file_record(args.baseline),
              'candidate': file_record(args.candidate)}
    result = compare_junit(args.baseline, args.candidate)
    if inputs != {'baseline': file_record(args.baseline),
                  'candidate': file_record(args.candidate)}:
        raise ValueError('JUnit input changed during comparison')
    receipt = {'schema_version': 1, 'status': 'paired_case_comparison_recorded',
               'inputs': inputs, 'comparison': result,
               'sources': {name: file_record(ROOT / name) for name in
                           ['scripts/compare_evaluations.py', 'zenithsync/evaluation.py']}}
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'receipt.json').write_bytes(canonical_json(receipt))
    print('Paired cases:', result['case_count'], 'changes:', len(result['changed_cases']))


if __name__ == '__main__':
    main()
