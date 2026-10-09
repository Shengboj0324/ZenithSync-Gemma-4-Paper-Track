# Local subprocess source-selection audit

The released getting-started notebook selects the subprocess backend. We ran
SWE-gemma 0.2.10 `verify_task` locally on macOS/Python 3.13 using the reserved
Requests snapshot, an empty agent patch, and one synthetic source-origin test.
The same verifier source was used for both paired runs.

- Unmodified backend (source-005): one test failed. Requests imported from the
  host .venv site-packages, not the snapshot checkout.
- Diagnostic source-path control (source-004): one test passed after prepending
  /workspace/src:/workspace to PYTHONPATH for the pytest command.
- Initial source-001 never collected tests because pytest was absent; it is
  not evidence of source selection. Source-002 stopped at the version guard.

The isolated host environment installed pytest 9.1.1 from existing local wheels
and exposed the project host dependencies. The official manager inherits host
site-packages, sets PYTHONPATH to the workspace root, and skips editable package
installation. A src-layout checkout therefore needs additional source discovery
in this tested environment. The control changes only the diagnostic invocation;
it is not a modification to the official scorer or a benchmark repair result.

This is local evidence, not proof of hidden Kaggle grader behavior. The Requests
repair still lacks clean official evaluation. GPU compute was not used.
