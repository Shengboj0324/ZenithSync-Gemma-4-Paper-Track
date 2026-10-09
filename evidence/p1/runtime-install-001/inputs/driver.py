import json, pathlib, subprocess, sys, time
out = pathlib.Path('/out')
steps = [
 ('install', [sys.executable, '-m', 'pip', 'install', '--no-cache-dir', '--no-index', '--find-links', '/wheels', '--require-hashes', '-r', '/inputs/requirements.lock'], 1800),
 ('dependency_check', [sys.executable, '-m', 'pip', 'check'], 120),
 ('runtime_probe', [sys.executable, '/inputs/probe.py', '--report', '/inputs/report.json', '--output', '/out/probe'], 1800),
]
results = []
for name, command, timeout in steps:
 start = time.monotonic()
 with (out / (name + '.log')).open('w') as log:
  try:
   result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
   code = result.returncode
  except subprocess.TimeoutExpired:
   code = 124
 results.append({'step': name, 'command': command, 'exit_code': code, 'elapsed_seconds': time.monotonic() - start})
 (out / 'steps.json').write_text(json.dumps(results, indent=2) + '\n')
 print(name, code, flush=True)
 if code:
  sys.exit(code)
