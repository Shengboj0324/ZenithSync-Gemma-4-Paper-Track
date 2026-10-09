"""Verify local HTTP fixture evidence through the real model-client adapter."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--grade', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    private = json.loads((ROOT / 'artifacts/official/source-task-001/evaluator/task.json').read_text())
    records = {}
    for mode, count, code in [('success', 3, 200), ('server-error', 1, 503)]:
        root = args.directory / mode
        receipt = json.loads((root / 'receipt.json').read_text())
        server = json.loads((root / 'http-fixture/receipt.json').read_text())
        exchanges = json.loads((root / 'http-fixture/exchanges.json').read_text())
        require(receipt['fixture'] == 'http-' + mode, 'Missing explicit fixture identity')
        require(receipt['training_approved'] is False and server['model_quality_evidence'] is False,
                'Fixture must not receive training or performance credit')
        require(receipt['container_removed'] is True and server['server_stopped'] is True,
                'Fixture resources not cleaned up')
        require(len(exchanges) == server['requests'] == count, 'Unexpected request/retry count')
        require(all(item['status'] == code for item in exchanges), 'Unexpected HTTP result')
        for item in exchanges:
            request = item['request']
            require(request['model'] == 'gemma-4-31b-it-qat-w4a16-ct', 'Wrong served model alias')
            require(not request.get('stream'), 'Only non-streaming behavior qualified')
            require(len(request['tools']) == 9, 'Expected compiled base candidate tools')
            require(private['solution_commit'] not in json.dumps(request), 'Reference identity leaked')
        if mode == 'success':
            require(receipt['patch_submitted'] is True and receipt['tool_calls'] == 1,
                    'Expected native write and submission')
            replies = [m for m in exchanges[-1]['request']['messages'] if m['role'] == 'tool']
            require([m['tool_call_id'] for m in replies] == ['http_fixture_write', 'http_fixture_submit'],
                    'Native tool response IDs did not round-trip')
            require(all(json.loads(m['content'])['status'] == 'ok' for m in replies),
                    'Native tool invocation failed')
            require(b'OFFLINE HTTP FIXTURE; NOT A REPAIR' in (root / 'agent.patch').read_bytes(),
                    'Missing explicit fixture patch marker')
        else:
            require(receipt['error_type'] == 'ServiceUnavailableError' and receipt['patch_submitted'] is False,
                    'HTTP failure misclassified as a successful submission')
        records[mode] = {'receipt': file_record(root / 'receipt.json'),
                         'exchanges': file_record(root / 'http-fixture/exchanges.json')}
    grade = json.loads((args.grade / 'receipt.json').read_text())
    require(grade['attempt'] == records['success']['receipt'], 'Grade belongs to another attempt')
    require(grade['fixture'] == 'http-success', 'Fixture label lost during independent grading')
    require(grade['status'] == 'graded_against_source_expectations', 'Independent grading did not finish')
    require(grade['score']['all_cases_match_publisher_expectations'] is False,
            'Transport fixture unexpectedly received repair credit')
    require(len(grade['score']['disagreements']) == 19 and grade['score']['case_count'] == 994,
            'Expected qualified baseline outcomes')
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'report.json').write_bytes(canonical_json({
        'status': 'local_http_client_checks_passed', 'fixtures': records,
        'grade': file_record(args.grade / 'receipt.json'), 'script': file_record(Path(__file__)),
        'scope': 'Real client against scripted loopback HTTP only; no Gemma inference or quality claim'}))
    print('HTTP tool round-trip, no-retry failure and independent grading checks passed')


if __name__ == '__main__':
    main()
