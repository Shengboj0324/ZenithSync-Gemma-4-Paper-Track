#!/usr/bin/env python3
"""Record non-executing review hints for explicitly selected Python snippets."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from zenithsync.artifacts import canonical_json, file_record
from zenithsync.source_test_risk import review_python_test_source


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, action='append', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    rows = []
    for source in args.source:
        before = file_record(source)
        result = review_python_test_source(source.read_text(encoding='utf-8'))
        if file_record(source) != before:
            raise ValueError('Source changed during review')
        rows.append({'path': str(source), 'identity': before, 'review': result})
    report = {
        'sources': rows,
        'admission_decision': None,
        'limitations': [
            'Hints require human or executable follow-up; they are not verdicts.',
            'No findings does not establish correctness or training suitability.',
            'Literal substring and syntactic handler matching only; no control-flow proof.',
            'Aliases, computed messages and interpolated strings may be missed.',
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('xb') as stream:
        stream.write(canonical_json(report))


if __name__ == '__main__':
    main()
