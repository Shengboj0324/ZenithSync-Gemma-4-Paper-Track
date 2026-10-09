"""Record installed-package parity and isolated CPU import checks on Linux.

Run after an offline, hash-enforced installation and pip check. This does not
allocate a GPU, load model weights, or establish CUDA kernel compatibility.
"""

import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform
import subprocess
import sys
import time


MODULES = (
    'torch', 'transformers', 'compressed_tensors', 'xgrammar',
    'swegemma', 'adk_submission', 'google.adk',
    'vllm.tool_parsers.gemma4_tool_parser',
    'vllm.reasoning.gemma4_reasoning_parser',
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    if platform.system() != 'Linux' or platform.machine() != 'x86_64' or sys.version_info[:2] != (3, 12):
        raise ValueError('probe requires Linux x86_64 with Python 3.12')
    report_bytes = args.report.read_bytes()
    report = json.loads(report_bytes)
    mismatches = []
    for package in report['install']:
        metadata = package['metadata']
        try:
            installed = version(metadata['name'])
        except Exception as error:
            installed = f'{type(error).__name__}: {error}'
        if installed != metadata['version']:
            mismatches.append({'name': metadata['name'], 'expected': metadata['version'],
                               'installed': installed})
    imports = []
    for module in MODULES:
        started = time.monotonic()
        command = [sys.executable, '-I', '-c',
                   'import importlib,sys; importlib.import_module(sys.argv[1])', module]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=180)
            output = result.stdout + result.stderr
            status = 'passed' if result.returncode == 0 else 'failed'
            returncode = result.returncode
        except subprocess.TimeoutExpired as error:
            output = (error.stdout or b'').decode(errors='replace') + (error.stderr or b'').decode(errors='replace')
            status, returncode = 'timeout', None
        filename = module.replace('.', '_') + '.log'
        (args.output / filename).write_text(output)
        imports.append({'module': module, 'status': status, 'returncode': returncode,
                        'elapsed_seconds': time.monotonic() - started, 'log': filename,
                        'log_sha256': hashlib.sha256(output.encode()).hexdigest()})
        print(module, status, flush=True)
    passed = not mismatches and all(item['status'] == 'passed' for item in imports)
    receipt = {'schema_version': 1, 'timestamp_utc': datetime.now(timezone.utc).isoformat(),
               'status': 'cpu_runtime_probe_passed' if passed else 'cpu_runtime_probe_failed',
               'python': sys.version, 'platform': platform.platform(),
               'report_sha256': hashlib.sha256(report_bytes).hexdigest(),
               'probe_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               'package_count': len(report['install']), 'version_mismatches': mismatches,
               'imports': imports, 'limitations': ['No model loading or CUDA kernel execution',
                    'No real generated tool calls or repair evaluation',
                    'CPU-only container may expose GPU-dependent import failures']}
    (args.output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
