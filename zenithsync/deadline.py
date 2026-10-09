"""POSIX main-thread deadline for bounded diagnostic I/O.

This interrupts Python/socket waits, not arbitrary uninterruptible native code
or remote GPU billing. The serving process has its own session supervisor.
"""

from contextlib import contextmanager
import math
import signal
import threading


class DeadlineExpired(TimeoutError):
    """The diagnostic's wall-clock allowance expired."""


@contextmanager
def wall_deadline(seconds):
    if not math.isfinite(seconds) or seconds <= 0:
        raise ValueError('Deadline must be positive and finite')
    if threading.current_thread() is not threading.main_thread():
        raise RuntimeError('Deadline requires the main thread')
    if not hasattr(signal, 'setitimer'):
        raise RuntimeError('Deadline requires POSIX interval timers')
    if signal.getitimer(signal.ITIMER_REAL) != (0.0, 0.0):
        raise RuntimeError('Refusing to replace an existing timer')
    previous = signal.getsignal(signal.SIGALRM)

    def expired(signum, frame):
        raise DeadlineExpired('Diagnostic wall-clock deadline expired')

    signal.signal(signal.SIGALRM, expired)
    try:
        signal.setitimer(signal.ITIMER_REAL, seconds)
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
