# External task runtime: current qualification boundary

This runtime prepares external development tasks for the native agent tools.
It is not a training-admitted corpus, hidden-grader replacement, or completed P1.
Only one preselected Pyramid task currently has the source/environment controls
described in `33-public-data-intake.md`.

## Task separation

`scripts/prepare_source_task.py` verifies the source shard and selected row against
the joined issue hash and evaluator controls. It writes:

- `agent/task.json`: opaque task ID, repository, sanitized snapshot commit, issue.
- `workspace.json`: immutable local image identity and qualified adapter identity.
- `evaluator/task.json`: original base, solution identity, image and test location.
- `evaluator/expected.json`: publisher outcomes, including expected failures.

Only the agent projection goes into the model prompt. The package is never mounted
inside the agent container. The opaque ID prevents copying the source ID's solution
commit into the prompt. The original issue body is retained after removing a sole,
well-formed `[ISSUE]` wrapper. Ambiguous wrappers reject instead of dropping text.
This is structural exclusion, not proof that arbitrary issue prose is answer-free.

The package at `artifacts/official/source-task-001` is tied to
`evidence/data/source-task-package-001/manifest.json`. The original-to-sanitized
base relationship is supported by exact source-tree equivalence. Do not interpret
the sanitized commit as the original repository's historical commit.

## Rollout driver

`scripts/run_source_task.py` defaults to dry-run. It verifies task/candidate
manifests, SDK versions, adapter identity, fixed 40-call/40-turn/10-minute limits,
native prompt construction, and documented context-compaction settings. Dry-run
starts neither a container nor a model. Passing evidence is
`evidence/data/source-task-dry-run-004`.

Execution requires both `--execute` and an explicit approved session record with
at least 1,200 seconds remaining. The endpoint is loopback only; the script never
creates or restarts a Pod. It prepares the qualified local image, compiles the
candidate against bound native tools, logs ADK events incrementally, and retains
the submitted patch on failure where available. The agent container is separate
from evaluation and is removed on exit. A submitted patch is not a solved task.

The execution path has now run with explicitly scripted offline fixtures, but
has not run with Gemma or a real model HTTP endpoint. It uses one ADK invocation,
without the official outer loop's nudges or retry plugins. Its results must not
be presented as exact competition-harness parity. Graph and embedding indexes
are unavailable for this source task and cannot be claimed as working features.

## Evidence and next gates

The task projection's tests cover exact field separation, opaque identity and
wrapper rejection. Core suite: 163 run, 148 passed, 15 skipped. Initial dry-run
attempts exposed required `EvalConfig` fields and the SDK YAML loader signature;
both were corrected before the passing dry-run. No inference result follows from
configuration validation.

## Offline lifecycle qualification

`--fixture` is mutually exclusive with `--execute`. It uses a scripted in-process
ADK model and never connects to the configured HTTP endpoint. Receipts and model
request captures identify the fixture and set training approval false. These are
integration tests, not synthetic repair-training data or performance evidence.

Five actual ADK/Docker runs passed the predicates in
`scripts/verify_source_runner_lifecycle.py`:

| Fixture | Observed behavior |
| --- | --- |
| Success | Native file write and submission; 3 model events, 1 budgeted tool call |
| Submit then fail | Intentional model exception after submission; identical patch retained |
| Timeout | One model request cancelled at the fixture's 1-second timeout; no events or patch |
| Turn limit | Stops at 40 model events; 39 tools execute because the last call encounters the turn guard |
| Tool limit | One response asks for 42 tools; 40 execute and 2 return `BudgetExceeded` |

All five owned containers were removed. Captured requests contain neither the
solution commit nor evaluator metadata field names. This is a specific checked
separation property, not a general semantic leakage proof. Usage figures are
synthetic and must not be used for throughput, cost, or efficiency estimates.
The timeout case tests asynchronous model cancellation; it does not establish
timely cancellation of a blocking subprocess or slow native tool.

Evidence: `evidence/data/source-runner-lifecycle-001` and
`source-runner-lifecycle-audit-001`. Exact driver/fixture source versions matching
recorded hashes are retained under the former's `source-versions` directory.
Next qualify slow-tool and cleanup-failure behavior, independent grading of saved
runner outputs, and real model HTTP behavior. Only then consider an explicitly
authorized GPU rollout. Real model attempts and scripted integration fixtures
must remain separate throughout corpus admission and performance reporting.

## Saved-output grading and slow-tool checks

`scripts/grade_source_attempt.py` now grades saved submitted patches in a fresh
offline evaluator. It verifies the package, agent task, submission state and
patch hash; rejects protected-file modifications; checks the original base and
staged patch bytes; and compares every JUnit case with publisher expectations.
Evaluator execution failures are distinct from expectation mismatches. This
first profile supports only the qualified Pyramid task.

Grading the scripted lifecycle fixture correctly yields 19 mismatches across 994
cases, unchanged from the buggy base. The fixture's harmless added file earns no
repair credit. Separate rejection checks confirm that tampered patches,
unsubmitted outputs and wrong task identities fail before evaluator output
creation. Evidence: `source-attempt-grade-001`, `source-grader-rejection-001`.

The `slow-tool` fixture reduces the native command timeout to one second. A
Python child schedules a file write four seconds later. The native tool returns
`TimeoutExceeded`; after a further five-second wait, a second native command
confirms that the file does not exist. Two actual runs passed, and the latest
also verifies the new cleanup helper against a live container. This establishes
the tested cooperative subprocess case, not arbitrary signal-resistant process
trees or precise hard real-time cancellation. Evidence:
`source-runner-slow-tool-001` and `002`.

`zenithsync/container_cleanup.py` records removal as true, false, or unknown.
Stop/query errors are retained; the driver writes a receipt before rejecting
unverified cleanup. Controlled unit tests cover a remaining container after a
stop error, an unavailable absence query, and confirmed absence despite a stop
error. These are simulated API failures, not injected outages in Docker itself.
Core suite: 166 run, 151 passed, 15 skipped. Real Gemma HTTP execution, broader
repository coverage, and training admission remain unqualified.

## Production-client HTTP transport check

`--http-fixture` is mutually exclusive with model execution and in-process fixtures.
It starts a private loopback HTTP server on an ephemeral port, then uses the same
`setup_gemma_model_registry`/LiteLLM client path as real execution. It cannot route
to an external model endpoint. Both the server receipt and attempt carry explicit
fixture labels and synthetic-usage flags.

The success case used three non-streaming chat-completion requests with all nine
compiled tool schemas. Native write/submission result IDs returned correctly in
subsequent HTTP requests, and the submitted fixture patch was retained. An
intentional 503 produced one request, no retries, no submission, and an explicit
`ServiceUnavailableError`. Agent containers and fixture servers stopped in both
cases. No headers or credentials are retained in HTTP records.

Independent grading of the success fixture collected all 994 cases and retained
the expected 19 mismatches. The artifact's `http-success` label survives grading;
no repair credit is inferred. `verify_source_http_client.py` checks the exchanges,
cleanup, task separation, tool results and grading linkage. Evidence:
`source-http-client-001`, `source-http-grade-001`, `source-http-client-audit-001`.

This qualifies the tested local non-streaming HTTP protocol and error path. It
does not qualify Gemma generation, native tokenizer/serving behavior, streaming,
network outages, or arbitrary server responses. With local plumbing established,
the next data priority is broader task/environment coverage and native trajectory
admission; keep integration fixtures out of the training corpus.

## Full source grading-contract census

`audit_source_expectation_corpus.py` verifies all eight pinned R2E shards before
and after reading and exports only task identities and aggregate expectation
counts. Across 4,578 tasks in ten repository basenames, 4,577 contracts have
nonempty test identities and supported statuses. One Orange3 task
(`f813020a9c0a0450df07ba20529b117665426249`, shard 0, row 157) contains a blank
test identity and remains excluded from this contract gate.

Of valid contracts, 2,374 expect only passes and 2,203 also expect failures or
errors. All 189 Pyramid contracts include expected failures. Pandas alone has
62,215 expected ERROR occurrences across its task contracts. These counts are
not unique tests, observed runtime errors, or evidence that a reference fix is
correct. The census does not resolve publisher identity collisions or establish
which outcomes discriminate the buggy base from the reference repair.

Consequently, metadata-valid tasks are not admitted to training. Next expand
independent base/reference controls to other repositories, preserve expected
failure states, and reject environments without a reproducible discriminating
signal. This census also identifies two source repositories absent from the
first acquired Hero trajectory shard (Orange3 and Pillow); source task coverage
must not be confused with available teacher trajectory coverage.

Evidence: `evidence/data/source-expectation-corpus-001`. Four new contract tests
cover duplicate keys, malformed/empty mappings, retained failure states, and
failure-only contracts. Full local suite: 170 run, 155 passed, 15 skipped.

## Second repository: Tornado evaluator controls

The pinned Tornado source task
`34edd2e8020b42cd16c3dc9a8c0417b9fae1e6d4` now has two independent pairs of
base/reference controls. Its image uses a custom unittest runner, so
`qualify_tornado_evaluator.py` invokes that runner's loader and result class,
retains fully qualified identities, and exports JUnit outcomes. Missing,
duplicate, or unrepresentable outcome identities reject the run. This profile
is separate from Pyramid's pytest profile and is not a universal adapter.

Both runs gave identical outcomes: base 29 passed / one failed; reference all
30 passed. The sole differing case is `GenTest.test_multi_future`. The reference
matches every pinned publisher expectation, while the base disagrees on that
case. Git first-parent checks, source import paths, unchanged tracked files,
non-OOM execution, and container cleanup passed. The tests ran offline in
separate disposable evaluator containers; reference code was never presented
to an agent.

Evidence: `tornado-evaluator-controls-001` and `002`, `tornado-expectations-001`
and `002`, and `tornado-evaluator-audit-001` under `evidence/data`. This establishes
a reproducible discriminating signal for one additional task. It does not
establish general Tornado coverage, hidden-test completeness, trajectory replay,
or agent success. Next sanitize this source snapshot and qualify native tool
execution before evaluating teacher or model patches. No GPU was required.
