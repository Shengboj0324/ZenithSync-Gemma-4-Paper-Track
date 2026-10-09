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

## Tornado source snapshot and native workspace

The Tornado snapshot build preserves the exact original Git tree, all 225
tracked files (1,455,510 bytes), file modes, and per-file content hashes. It
replaces history with one parentless commit and removes the known generated
grading directory and test launcher. The reusable native workspace probe verifies
that the solution commit is inaccessible, imports resolve under `/workspace`,
source reads work, and an untouched submission exports an empty patch. That probe
also passed against the previously qualified Pyramid snapshot.

The original repository's `tornado.test.gen_test` module has 28 cases, all passing
in both original and sanitized images with identical fully qualified outcomes.
These are distinct from the 30 generated grading cases used in the evaluator
controls. An initial text-parser attempt rejected an interleaved logging message;
the successful comparison uses structured unittest result callbacks, rejects
missing/duplicate outcomes, and retains the original failure evidence.

Evidence: `tornado-snapshot-build-001`, `tornado-workspace-probe-001`,
`pyramid-workspace-probe-001`, and `tornado-snapshot-comparison-001` / `002`.
The build context is `artifacts/official/tornado-snapshot-build-001`.
Original oracle data remains in Docker lower layers, so the snapshot must only be
used in the offline, unmounted agent sandbox without Docker-engine access. It is
not a scrubbed distributable image or an exhaustive image-content audit. These
checks qualify workspace transport and a relevant source test module; they admit
no training examples. Next qualify native patch transport and replay on this
second repository before any real-model rollout.

## First adapted native teacher replay: Tornado

`replay_tornado_teacher.py` verifies the pinned Hero shard and selects trajectory
`4d152574-6d53-4924-b9a6-c58d47a5d6d8` by exact task identity. It preflights the
reviewed tool profile, maps its repository root to `/workspace`, and executes
its actions in order through native tools in the sanitized offline container.
Editor directory views become bounded listings; file views use native read
limits, creates refuse overwrites, and replacements use native edit semantics.
Three teacher `think` actions are recorded as not executed. Recorded teacher
observations are not reused as evidence, and source `finish` becomes native patch
submission. This is action replay with adapted observations, not proof of full
OpenHands semantic equivalence or a newly generated Gemma trajectory.

The 62 source actions produced 58 charged native tool calls. Four shell commands
returned errors, which are retained in the event record. All mutations and the
submission succeeded. The native submitted patch contains changes to
`tornado/gen.py` and an added `reproduce_issue.py`; native submission filtering
omits the teacher's test-named scratch files. Cleanup was verified.

`grade_tornado_teacher.py` applied those saved patch bytes to a fresh original
base image and ran the qualified publisher test runner. All 30 cases passed,
with no missing groups, unexpected groups, or expectation disagreements. The
tracked patch remained unchanged during grading. The evaluator's generated tests
were never mounted in the replay container. Evidence:
`tornado-teacher-replay-001`, `tornado-teacher-grade-001`.

The replay uses a 100-call data-qualification ceiling and 30-second command
limits. Its 58-call trace exceeds the current 40-call competition profile and
must not be counted as a competition-budget success. Training admission remains
false pending context/mask qualification, rights and contamination review, and a
policy for budget-compatible trajectories. No source observations can be paired
with the adapted native calls without reconciliation. Four profile tests cover
path escape rejection, shell-root mapping, interactive/unknown action rejection,
and exclusion of teacher thought content from executable actions.

## Fresh native history and exact tokenizer qualification

The second Tornado replay records the exact native function name, arguments,
and returned result for each executed action. `native_replay_history` requires
strict source-event ordering, exactly one matching native exchange per executed
action, and a final submission exchange; it does not infer missing results.
Three teacher thought actions are omitted. Stable synthetic call IDs are linkage
metadata, not evidence of additional tool execution.

`build_replay_history.py` combines these 59 native exchanges with the pinned source
issue and an explicitly reconstructed base-candidate system prompt. It reuses
the nine-tool schema snapshot from the qualified pinned HTTP-client fixture and
checks the tool-name set. The resulting 120-message history contains no copied
teacher reasoning or final success narrative. This is diagnostic action-only
supervision, not a claim that the teacher was conditioned on the reconstructed
prompt or that original observations equal replay observations.

`audit_replay_history_tokens.py` verifies the pinned tokenizer assets and exact
native rendering/token identity, then checks assistant-only masks against
character spans and token offsets. With all nine tool schemas included, the full
history has **28,933 input tokens** and **6,764 supervised next-token targets**.
No truncation or packing is applied. It fits a 32,768 input-token cap, leaving
3,835 tokens; this is not an 8,192-token generation reserve or a demonstrated GPU
training fit. Training targets cover assistant actions, never tool results.

The second saved replay patch independently passes all 30 grading cases.
Evidence: `tornado-teacher-replay-002`, `tornado-teacher-grade-002`,
`tornado-native-history-001`, `tornado-native-tokens-001`. Four additional
projection tests reject missing, inconsistent, parallel, and reordered exchanges
and verify fresh-result linkage. Core suite: 178 run, 163 passed, 15 skipped.
Training approval remains false: 58 charged calls exceed the current competition
profile; prompt/observation adaptation, rights/contamination, corpus-level
coverage, and long-context GPU qualification remain unresolved admission gates.

## Corpus replay priorities

`plan_trajectory_replays.py` joins the pinned 2,500-trace source shard to its exact
context census. It estimates one charged native call per shell/editor action,
excluding reasoning and terminal submission, while retaining interactive-shell,
empty-command, and unsupported-editor flags. The estimate is a screening measure,
not a measured runtime count or complete semantic-adaptation check.

417 source histories have at most 40 estimated charged calls. Of these, 136 also
fit the earlier 32,768 source-token cap and have no known adapter flags. The
per-repository joint counts are Pyramid 7, aiohttp 4, datalad 6, coveragepy 5,
NumPy 58, pandas 42, Scrapy 9, Tornado 5. Source token counts omit tool schemas
and output reserve and differ from fresh native replay lengths, so this screen
must not be used as final context admission.

One candidate per repository is selected by minimum SHA256(revision + NUL +
trajectory ID) within the joint-fit pool, with a documented call-budget fallback
if needed. All eight selected tasks have successfully resolved GitHub first
parents and content-addressed Linux amd64 registry images. Selection artifacts
retain full task linkage. This cost/coverage-driven set is not a representative
performance sample, and failures must not be replaced silently.

Evidence: `replay-selection-001` / `002` and
`replay-environment-resolution-001`. Longer teacher traces are not automatically
invalid SFT material; the deployment budget and the training sequence policy are
separate decisions. No source trace receives training approval from this screen.

The selected budget-priority Tornado task
`86cc31f52992fb9d11f92de6fd5496842fea2265` (33 estimated source calls) now has
its own base/reference controls: base 38 passed / one error; reference 39 passed.
The reference matches every publisher expectation and the base does not.
Evidence: `tornado-budget-controls-001`, `tornado-budget-expectations-001`.
Its source isolation and native replay remain pending; the earlier task's
successful replay cannot be transferred as evidence for this task.

## First replay within the 40-call profile

The selected Tornado task `86cc31f52992fb9d11f92de6fd5496842fea2265` now has a
sanitized source snapshot and a native teacher replay under an enforced 40-call
ceiling. `build_source_snapshot.py` provides a reusable offline build procedure
for already-local pinned source images; `replay_tornado_teacher.py --profile`
accepts validated task, image, source-root, and budget identities. The original
reviewed task remains the default compatibility profile. A profile is configuration,
not an assertion that an arbitrary task's tool semantics are qualified.

The replay used **33 charged native calls**, retained 34 full exchanges including
submission, and produced a 495-byte patch. The missing sanitized `run_tests.sh`
view and an unsuccessful grep are retained as errors; neither is rewritten into
a successful observation. The saved patch passed **39/39** independent grading
cases and exactly matched the publisher contract. The grader now re-reads the
hash-verified source Parquet row to check exported expectations before execution.
All owned containers were removed.

The fresh action-only history has 70 messages and, including all nine schemas,
**14,884 input tokens** / **3,890 supervised next-token targets**. Native template
rendering, token equality, and assistant-only span masks pass without truncation.
Its input length plus an 8,192-token reserve is 23,076, below 32,768. This is
arithmetic context capacity, not measured long-context GPU training memory or a
claim that the original teacher saw the reconstructed native observations/prompt.

Evidence: `tornado-budget-snapshot-build-001`, `tornado-budget-workspace-probe-001`,
`tornado-budget-replay-001`, `tornado-budget-grade-001`,
`tornado-budget-history-001`, and `tornado-budget-tokens-001`.
Three new profile tests reject invalid budgets/identity/root configurations and
verify alternate-root mapping. Core suite: 183 run, 168 passed, 15 skipped.
This is the first locally qualified teacher patch/history fitting both current
runtime-call and context screens. Training approval remains false pending rights,
contamination, observation/prompt policy, dataset-level coverage and GPU-fit gates.

## Second budget-compatible repository: Pyramid

The selected Pyramid task `48a04855ad4f1f1ae6af934090f35a4ad035ed67` uses a
`src/pyramid` layout and a merge solution commit. Source sanitization verifies the
publisher's first-parent base locally and preserves its exact tracked tree.
The qualified workspace probe explicitly checks the src-layout import path.
Base/reference controls collect 835 cases: base 753 passed / 82 failed,
reference 755 passed / 80 failed. The reference exactly satisfies the 830
publisher groups, retaining every colliding fully qualified case.

Its pinned Hero trajectory `476ee9ff-2fdc-4d32-8a27-20c378f37744` replayed with
**29 charged calls** under the 40-call ceiling and produced a 520-byte patch.
Independent grading matches all **835 case expectations**, including the 80
expected failures; this is not an all-tests-passing suite. Fresh native history
contains 30 exchanges / 62 messages, **18,924 input tokens**, and **3,868
supervised targets**, including nine schemas and without truncation. Adding an
8,192-token reserve gives 27,116 tokens, within 32,768. This does not establish
training memory fit. Both recorded read/grep errors remain visible in the history.

Generic entry points are now `replay_source_teacher.py` and
`grade_replayed_patch.py`, with compatibility wrappers at the original Tornado
names. The shared grader supports only the two qualified repository profiles;
it does not treat arbitrary pytest/unittest environments as equivalent. A new
Tornado regression grading run still matches all 39 expectations. Core suite
remains 183 run / 168 passed / 15 skipped, and live checks cover both grader profiles.

Evidence: `pyramid-budget-controls-001`, `pyramid-budget-expectations-001`,
`pyramid-budget-snapshot-build-001`, `pyramid-budget-workspace-probe-001`,
`pyramid-budget-replay-001`, `pyramid-budget-grade-001`,
`pyramid-budget-history-001`, `pyramid-budget-tokens-001`, and
`tornado-budget-grade-002`. All work used local offline containers; cleanup was
verified. Training approval remains false. The two selected successes are
mechanism checks, not an unbiased repair-rate estimate or new Gemma performance.
