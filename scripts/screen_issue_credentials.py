"""Screen a hash-bound issue list without logging issue text or credential values."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record, load_json
from zenithsync.source_credentials import scan_text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--issues', type=Path, required=True)
    parser.add_argument('--max-bytes', type=int, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    identity = file_record(args.issues)
    if args.max_bytes <= 0 or identity['size_bytes'] > args.max_bytes:
        raise ValueError('Issue file exceeds the explicit byte ceiling')
    sources = {name: file_record(ROOT / name) for name in
               ['scripts/screen_issue_credentials.py', 'zenithsync/source_credentials.py']}
    rows = load_json(args.issues)
    if not isinstance(rows, list):
        raise ValueError('Expected an issue list')
    findings = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or not isinstance(row.get('problem_statement'), str):
            raise ValueError('Every issue requires text')
        # Use row numbers, not untrusted IDs or snippets, in diagnostics.
        matches = scan_text(row['problem_statement'])
        if matches:
            findings.append({'row_index': index, 'findings': matches})
    if file_record(args.issues) != identity:
        raise ValueError('Issues changed during screening')
    if sources != {name: file_record(ROOT / name) for name in sources}:
        raise ValueError('Screen implementation changed')
    report = {'schema_version': 1, 'input': identity, 'sources': sources,
              'rows_screened': len(rows), 'flagged_rows': findings,
              'scope': 'Known credential-shaped literals in issue problem_statement strings only.',
              'decision': 'review_required' if findings else 'no_known_indicators',
              'training_approved': False}
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'report.json').write_bytes(canonical_json(report))
    print({'rows_screened': len(rows), 'flagged_rows': len(findings), 'decision': report['decision']})


if __name__ == '__main__':
    main()
