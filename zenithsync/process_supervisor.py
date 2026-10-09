"""Bound an owned POSIX process group; never manages cloud billing.

Children must remain in the inherited process group. This is lifecycle control
for trusted workers, not confinement against processes that detach themselves.
"""

from datetime import datetime, timezone
from contextlib import contextmanager
import math
import os
from pathlib import Path
import signal
import subprocess
import time
import threading


@contextmanager
def _termination_handler():
    if threading.current_thread() is not threading.main_thread():
        raise RuntimeError('Supervisor must own main-thread signal handling')
    previous = {sig: signal.getsignal(sig) for sig in [signal.SIGTERM, signal.SIGINT]}

    def interrupted(signum, frame):
        raise InterruptedError(f'Supervisor interrupted by signal {signum}')

    try:
        for sig in previous:
            signal.signal(sig, interrupted)
        yield
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)


def _group_exists(group):
    try:
        os.killpg(group, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        # Lack of permission cannot establish that the group has disappeared.
        return True
    return True


def _signal_group(group, sig):
    try:
        os.killpg(group, sig)
    except ProcessLookupError:
        pass
    except PermissionError:
        # Retain the unresolved group in the final result; never claim cleanup.
        return False
    return True


def run_bounded(argv, *, log_path: Path, deadline: datetime, maximum_seconds: float,
                grace_seconds: float = 5.0, env=None, stop_path: Path | None = None):
    """Launch once, enforce wall/monotonic bounds and retain honest exit status.

Exit zero means only process success; acceptance requires the worker's verified
artifacts separately. A timeout or descendant leak cannot become a success.
"""
    if os.name != 'posix':
        raise RuntimeError('POSIX process groups required')
    for value in [maximum_seconds, grace_seconds]:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise ValueError('Positive finite process time limits required')
    if deadline.tzinfo is None or deadline.utcoffset() is None:
        raise ValueError('An aware session deadline is required')
    remaining = (deadline - datetime.now(timezone.utc)).total_seconds()
    if remaining <= 0:
        raise ValueError('Session deadline expired before launch')
    if remaining <= 2 * grace_seconds:
        raise ValueError('Session has insufficient cleanup allowance')
    if not isinstance(argv, list) or not argv or any(not isinstance(x, str) or not x or '\0' in x for x in argv):
        raise ValueError('Explicit nonempty argument vector required')
    if stop_path is not None and stop_path.exists():
        raise ValueError('Stop request already exists')
    started = time.monotonic()
    # Reserve both graceful termination and final wait within the session cap.
    expires = started + min(maximum_seconds, remaining - 2 * grace_seconds)
    process = None
    reason = 'interrupted'
    escalated = False
    with _termination_handler(), log_path.open('xb') as log:
        try:
            process = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=log,
                stderr=subprocess.STDOUT, env=env, start_new_session=True)
            while True:
                # Check the limits before accepting an exit observed at the boundary.
                if time.monotonic() >= expires or datetime.now(timezone.utc) >= deadline:
                    reason = 'deadline_exceeded'
                    break
                if stop_path is not None and stop_path.exists():
                    reason = 'stop_requested'
                    break
                code = process.poll()
                if code is not None:
                    reason = 'exited' if not _group_exists(process.pid) else 'descendant_leak'
                    break
                time.sleep(min(0.05, max(0.0, expires - time.monotonic())))
        finally:
            if process is not None:
                if _group_exists(process.pid):
                    _signal_group(process.pid, signal.SIGTERM)
                    cleanup_deadline = time.monotonic() + grace_seconds
                    while time.monotonic() < cleanup_deadline:
                        process.poll()
                        if not _group_exists(process.pid):
                            break
                        time.sleep(0.02)
                    if _group_exists(process.pid):
                        escalated = True
                        _signal_group(process.pid, signal.SIGKILL)
                # SIGKILL cannot immediately interrupt an uninterruptible kernel wait.
                try:
                    process.wait(timeout=grace_seconds)
                except subprocess.TimeoutExpired:
                    pass
    group_remaining = _group_exists(process.pid)
    return {'reason': reason, 'returncode': process.returncode,
            'success': reason == 'exited' and process.returncode == 0 and not group_remaining,
            'kill_escalated': escalated, 'process_group_remaining': group_remaining,
            'elapsed_seconds': time.monotonic() - started,
            'scope': 'Owned process-group lifecycle only; no task acceptance or Pod billing claim'}
