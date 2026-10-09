"""Evaluator-only pytest plugin: observe imports inside the test process.

Installed outside the repository under test. Never supplied to the agent. This
is a local qualification gate, not an organizer-approved harness modification.
"""

import hashlib
import json
import os
from pathlib import Path
import sys

import pytest


def observe_modules(names, workspace):
    """Record loaded modules without importing or changing source precedence."""
    root = Path(workspace).resolve(strict=True)
    rows = []
    for name in names:
        module = sys.modules.get(name)
        filename = getattr(module, '__file__', None)
        row = {'module': name, 'loaded': module is not None, 'file': filename,
               'inside_workspace': False, 'sha256': None}
        if isinstance(filename, str):
            path = Path(filename).resolve(strict=True)
            row['file'] = str(path)
            row['inside_workspace'] = path.is_relative_to(root)
            row['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        rows.append(row)
    return rows


def _record(stage):
    report = Path(os.environ['ZENITH_SOURCE_REPORT'])
    names = json.loads(os.environ['ZENITH_SOURCE_MODULES'])
    if not isinstance(names, list) or not names or any(
        not isinstance(n, str) or not all(p.isidentifier() for p in n.split('.')) for n in names
    ):
        raise pytest.UsageError('Invalid source-observation module list')
    rows = observe_modules(names, os.environ['ZENITH_SOURCE_ROOT'])
    record = {'stage': stage, 'modules': rows,
              'valid': all(r['loaded'] and r['inside_workspace'] for r in rows)}
    # The report lives in a fresh evaluator container, outside the checkout.
    with report.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(record, sort_keys=True) + '\n')
    return record['valid']


def pytest_collection_finish(session):
    if not _record('collection_finished'):
        raise pytest.UsageError('Source qualification failed: required modules are not from the checkout')


def pytest_sessionfinish(session, exitstatus):
    if not _record('session_finished'):
        session.exitstatus = pytest.ExitCode.USAGE_ERROR
