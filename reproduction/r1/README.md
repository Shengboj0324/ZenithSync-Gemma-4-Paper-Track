# R1: real-task reproduction and baseline challenge

The selected React task could not be acquired: its repository returned 404 and its published archives returned 403. The cycle therefore uses the previously shortlisted HashiCorp Raft issue 268. This is an independent component-level reproduction on the original repository, not execution of the DDBench benchmark or the original dqlite deployment.

Pinned original: `9a647f6c2bb9e057c49b85176086ab94a210c09d`.
Pinned upstream repair: `2e997410f28efe8106fc606d21cb655be1b05dee`.
The original source retains its upstream license; see `LICENSE` in either acquired snapshot. Source trees and dependencies are excluded from this project's Git index.

`shutdown_regression_test.go` exercises the real snapshot worker and shutdown API, using controlled peers for the other workers. Its liveness test waits until a configuration request is actually queued, then initiates shutdown without servicing that request. This implements the reported event order. A 250 ms deadline detects nontermination for this small fixture; it is not a production latency requirement or a measured speedup. Normal persistence and post-shutdown behavior are separate controls.

## Re-execution

Cleanup: removed the original/reference and three baseline-evaluation working trees after byte-for-byte comparison against the retained pinned source, regression fixture and saved production changes. Removed generated Python bytecode too. The pinned upstream checkout, all evidence and scripts remain. The disabled-snapshots negative-control workspace is retained because its `snapshot.go` contains a distinct modification. Recorded receipt paths describe historical executions; the five removed working directories no longer exist. Run `prepare.py` to regenerate original/reference trees. Historical baseline evaluator trees can be reconstructed from the original revision plus `evidence/baseline-*/changed-files/` production files and the regression fixture; do not overwrite historical evidence or count a reconstruction as a new evaluation.

Requirements: Python with `tarfile` extraction filters, Git, Go, and network access for initial source/dependency acquisition. This run used Python 3 and Go 1.24.3 on macOS arm64. No Docker daemon was available or required for the Raft case.

On a fresh copy, from the project root:

```sh
python3 reproduction/r1/prepare.py
python3 reproduction/r1/run_command.py --cwd reproduction/r1/workspaces/original --out reproduction/r1/evidence/new-original --timeout 180 -- go test -race -json -run '^TestR1' -count=3 -timeout=150s .
python3 reproduction/r1/run_command.py --cwd reproduction/r1/workspaces/reference --out reproduction/r1/evidence/new-reference --timeout 180 -- go test -race -json -run '^TestR1|^TestRaft_(AfterShutdown|UserSnapshot|AutoSnapshot|SnapshotRestore)$' -count=3 -timeout=150s .
```

The original is expected to fail the liveness test. The reference must pass. Preparation and result directories deliberately refuse overwriting existing experiments. `run_command.py` stores raw output, command, exit code, wall time, timeout status, and output hashes. Its own successful execution means a receipt was written, not that the tested command passed; inspect `receipt.json`.

Baseline trials use `run_baseline.py <new-trial-id>` and an authenticated Codex CLI, then `evaluate_baseline.py <trial-id>`. These commands consume account usage. Each baseline starts from a clean temporary repository without upstream history or this project's documents. The prompt, model request, reasoning setting and 600-second cap are fixed. No independent agent receives this conversation's history. Memory is disabled and user configuration is ignored. Scope instructions restrict external access, but there is no claimed cryptographic or OS-enforced proof of read isolation; inspect the complete command trace.

The evaluator copies production changes into a fresh original tree and retains original tests. Agent-written tests are saved for audit but do not define success. The independent fixture is added only after patch generation. Dependency changes, deletions and unexpected production-file types require separate review rather than automatic acceptance.

## Interpretation

Three repeats of one public historical bug are three attempts, not three independent bugs. Model pretraining exposure cannot be excluded. The requested model name is a service identifier, not an immutable weight hash. Runtime includes investigation and tests; zero reported billing is never inferred from missing price data. No Gemma method, specialist-tool superiority or cross-task performance claim follows from this pilot.

An initial evaluator compilation error (`*Config` versus `Config`) is retained in `evidence/original-controls`; it is a fixture development error, not an agent failure. Corrected controls are stored separately. The deliberately invalid disabled-snapshots control checks that avoiding the problematic feature does not count as a repair.
