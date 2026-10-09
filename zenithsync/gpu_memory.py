"""Device-wide sampled memory telemetry, distinct from allocator peak counters."""

import csv
import io
import re
import subprocess
import threading
import time

from zenithsync.artifacts import canonical_json


def parse_memory_csv(text):
    devices = {}
    for row in csv.reader(io.StringIO(text)):
        if len(row) != 3:
            raise ValueError('Expected GPU UUID, used MiB and total MiB')
        identifier, used, total = (value.strip() for value in row)
        if not re.fullmatch(r'GPU-[0-9a-fA-F-]+', identifier) or identifier in devices:
            raise ValueError('Invalid or duplicate GPU UUID')
        if not used.isascii() or not used.isdecimal() or not total.isascii() or not total.isdecimal():
            raise ValueError('Unavailable or malformed GPU memory measurement')
        used_bytes, total_bytes = int(used) * 1024**2, int(total) * 1024**2
        if total_bytes <= 0 or used_bytes > total_bytes:
            raise ValueError('GPU memory measurement outside physical bounds')
        devices[identifier] = {'used_bytes': used_bytes, 'total_bytes': total_bytes}
    if not devices:
        raise ValueError('No GPU memory measurements')
    return devices


def read_device_memory():
    result = subprocess.run(['nvidia-smi', '--query-gpu=uuid,memory.used,memory.total',
                             '--format=csv,noheader,nounits'], check=True,
                            capture_output=True, text=True, timeout=5)
    return parse_memory_csv(result.stdout)


class DeviceMemoryMonitor:
    """Sample all GPUs reported by nvidia-smi every second after each read.

    Sampled maxima are lower bounds on actual peaks. They include other GPU
    clients and driver allocations and are not attributed to the worker alone.
    A read failure prevents successful monitor completion, but does not replace
    an exception already raised by the training worker. Partial JSONL persists.
    """

    def __init__(self, path):
        self.path = path
        self._stop = threading.Event()
        self._error = None
        self._stream = None
        self._thread = None
        self._devices = None
        self._samples = 0
        self._maxima = {}
        self._start = None

    def _sample(self):
        devices = read_device_memory()
        identities = {key: row['total_bytes'] for key, row in devices.items()}
        if self._devices is not None and identities != self._devices:
            raise ValueError('GPU identities or capacities changed during monitoring')
        self._devices = identities
        record = {'elapsed_seconds': time.monotonic() - self._start, 'devices': devices}
        self._stream.write(canonical_json(record))
        self._stream.flush()
        self._samples += 1
        for key, row in devices.items():
            self._maxima[key] = max(self._maxima.get(key, 0), row['used_bytes'])

    def _run(self):
        try:
            while not self._stop.wait(1.0):
                self._sample()
        except BaseException as error:
            self._error = error
            self._stop.set()

    def __enter__(self):
        if self._start is not None:
            raise RuntimeError('Monitor instances cannot be reused')
        self._start = time.monotonic()
        self._stream = self.path.open('xb')
        try:
            self._sample()
            self._thread = threading.Thread(target=self._run, name='gpu-memory-monitor', daemon=True)
            self._thread.start()
        except BaseException:
            self._stream.close()
            raise
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._stop.set()
        self._thread.join(timeout=6)
        if self._thread.is_alive():
            # Do not race an active writer by closing its file. The external
            # process-group supervisor remains responsible for hard cleanup.
            self._error = RuntimeError('GPU memory reader failed to terminate')
        else:
            try:
                if self._error is None:
                    self._sample()
            except BaseException as error:
                self._error = error
            finally:
                self._stream.close()
        if self._error is not None and exc_type is None:
            raise RuntimeError('GPU memory monitoring incomplete') from self._error
        return False

    def summary(self):
        if self._thread is None or self._thread.is_alive() or self._error is not None:
            raise RuntimeError('Completed successful monitoring required')
        return {'samples': self._samples, 'sampled_max_used_bytes': dict(self._maxima),
                'device_total_bytes': dict(self._devices),
                'scope': 'All nvidia-smi GPUs; sampled maxima, not continuous peaks or worker-only memory'}
