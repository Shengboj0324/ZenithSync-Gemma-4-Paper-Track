"""Launch the pinned local server with retained logs and a session deadline.

This driver does not stop the Pod or establish repair/training correctness.
An empty stop.request file in the output directory requests early termination.
"""

import argparse
from datetime import datetime, timezone
from importlib.metadata import version
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record, load_json
from zenithsync.serving import sdk_config_arguments


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', type=Path, required=True)
    parser.add_argument('--model-dir', type=Path, required=True)
    parser.add_argument('--session', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    session = load_json(args.session)
    deadline = datetime.fromisoformat(session['validation_deadline_utc'])
    if deadline.tzinfo is None:
        raise ValueError('Session deadline requires a timezone')
    remaining = (deadline - datetime.now(timezone.utc)).total_seconds()
    if not 0 < remaining <= 14400:
        raise ValueError('Deadline expired or exceeds the approved four-hour cap')
    if version('adk-submission') != '0.2.13':
        raise ValueError('Pinned SDK required')
    from adk_submission import VllmConfig, VllmServer

    profile = load_json(args.profile)
    server = VllmServer(VllmConfig(**sdk_config_arguments(profile, args.model_dir)))
    # SDK construction creates an unused log; retain our own log instead.
    Path(server.log_path).unlink()
    with socket.socket() as check:
        check.bind((profile['host'], profile['port']))
    args.output.mkdir(parents=True, exist_ok=False)
    argv = server.build_cmd()
    env = server.build_env()
    env.update(HF_HUB_OFFLINE='1', HF_HUB_DISABLE_TELEMETRY='1',
               LITELLM_LOCAL_MODEL_COST_MAP='True', OTEL_SDK_DISABLED='true')
    record = {'schema_version': 1, 'status': 'starting', 'argv': argv,
              'deadline_utc': deadline.isoformat(), 'source': file_record(Path(__file__)),
              'profile': file_record(args.profile), 'session': file_record(args.session),
              'scope': 'Server lifecycle and health only; no inference success claim'}

    def save():
        temporary = args.output / '.status.tmp'
        temporary.write_bytes(canonical_json(record))
        temporary.replace(args.output / 'status.json')

    def interrupted(signum, frame):
        raise InterruptedError(f'Supervisor signal {signum}')

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    started = time.monotonic()
    end = started + remaining
    startup_end = min(end, started + profile['startup_timeout_seconds'])
    process = None
    save()
    try:
        with (args.output / 'server.log').open('wb') as log:
            process = subprocess.Popen(argv, env=env, stdout=log,
                                       stderr=subprocess.STDOUT, start_new_session=True)
            record['pid'] = process.pid
            save()
            while process.poll() is None:
                now = time.monotonic()
                if now >= end:
                    record['status'] = 'session_deadline_reached'
                    break
                if (args.output / 'stop.request').exists():
                    record['status'] = 'stop_requested'
                    break
                if record['status'] == 'starting':
                    if now >= startup_end:
                        raise TimeoutError('Server startup deadline reached')
                    try:
                        with opener.open(server.health_url, timeout=min(2, startup_end-now)) as response:
                            ready = response.status == 200
                    except OSError:
                        ready = False
                    if ready:
                        record.update(status='ready', startup_seconds=time.monotonic()-started)
                        save()
                        print('Server health ready; generation remains unverified.', flush=True)
                time.sleep(min(2, max(0, end-time.monotonic())))
            else:
                raise RuntimeError(f'Server exited with code {process.returncode}')
    except BaseException as error:
        record.update(status='failed', error_type=type(error).__name__, error=str(error))
        raise
    finally:
        if process is not None:
            # Signal only the process group created by this driver, including workers.
            try:
                os.killpg(process.pid, signal.SIGTERM)
                process.wait(timeout=15)
            except ProcessLookupError:
                pass
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
            record['server_returncode'] = process.poll()
        record['elapsed_seconds'] = time.monotonic()-started
        save()


if __name__ == '__main__':
    main()
