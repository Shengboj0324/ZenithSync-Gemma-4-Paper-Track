"""Audit recorded offline source-runner lifecycle fixtures without model credit."""

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
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    reports = {}
    expected = {
        'success': (True, None, 3, 1),
        'submit-then-fail': (True, 'RuntimeError', 2, 1),
        'timeout': (False, 'TimeoutError', 0, 0),
        'turn-limit': (False, 'LlmCallsLimitExceededError', 40, 39),
        'tool-limit': (False, None, 2, 40),
    }
    private = json.loads((ROOT / 'artifacts/official/source-task-001/evaluator/task.json').read_text())
    for name, (submitted, error, llm_calls, tool_calls) in expected.items():
        directory = args.directory / name
        receipt = json.loads((directory / 'receipt.json').read_text())
        requests_raw = (directory / 'fixture-requests.json').read_text()
        requests = json.loads(requests_raw)
        require(receipt['fixture'] == requests['fixture'] == name, 'Fixture identity mismatch')
        require(receipt['training_approved'] is False and requests['training_approved'] is False,
                'Fixture must never be training approved')
        require(receipt['container_removed'] is True, 'Container cleanup not established')
        require(receipt['patch_submitted'] == submitted, 'Submission state differs')
        require(receipt.get('error_type') == error, 'Unexpected terminal error')
        require(receipt['llm_calls'] == llm_calls and receipt['tool_calls'] == tool_calls,
                'Budget accounting differs from expected lifecycle')
        require(file_record(directory / 'agent.patch') == receipt['patch'], 'Patch identity mismatch')
        require(private['solution_commit'] not in requests_raw, 'Solution commit leaked into model requests')
        require('expected_output_json' not in requests_raw and 'solution_commit' not in requests_raw,
                'Evaluator metadata exposed to fixture model')
        if not submitted:
            require((directory / 'agent.patch').read_bytes() == b'', 'Unsubmitted fixture has patch bytes')
        events = [json.loads(line) for line in (directory / 'events.jsonl').read_text().splitlines()]
        responses = [part['function_response']['response']
                     for event in events for part in (event.get('content') or {}).get('parts', [])
                     if part.get('function_response')]
        if name == 'tool-limit':
            require(len(responses) == 42, 'Expected all batched tool results')
            require(sum(r.get('status') == 'ok' for r in responses) == 40, 'Tool limit not enforced')
            require(sum(r.get('error_type') == 'BudgetExceeded' for r in responses) == 2,
                    'Excess tool calls must receive budget errors')
        if name == 'timeout':
            require(len(requests['requests']) == 1 and not events, 'Timeout fixture emitted unexpected events')
        reports[name] = {'receipt': file_record(directory / 'receipt.json'),
                         'requests': file_record(directory / 'fixture-requests.json'),
                         'events': file_record(directory / 'events.jsonl'),
                         'request_count': len(requests['requests']), 'checks_passed': True}
    success = (args.directory / 'success/agent.patch').read_bytes()
    require(success == (args.directory / 'submit-then-fail/agent.patch').read_bytes(),
            'Failure did not retain the same submitted fixture patch')
    require(b'OFFLINE LIFECYCLE FIXTURE; NOT A REPAIR' in success, 'Missing explicit fixture marker')
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'report.json').write_bytes(canonical_json({
        'schema_version': 1, 'status': 'offline_lifecycle_checks_passed', 'fixtures': reports,
        'script': file_record(Path(__file__)), 'model_quality_evidence': False,
        'scope': 'Scripted ADK lifecycle only; real model HTTP, slow tool cancellation, grading and training not qualified'}))
    print('Five offline lifecycle fixtures verified; no model-quality claim')


if __name__ == '__main__':
    main()
