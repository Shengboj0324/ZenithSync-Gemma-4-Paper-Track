# R1 reproduction cycle: evidence and product decision

October 7, 2026. **Completed bounded reproduction and baseline pilot. Product-promotion decision: NO-GO on the available evidence.** The original defect was reproduced, and the ordinary strong baseline repaired it in all three attempts under the targeted acceptance checks. No final agentic product is adopted; no comparative benefit of the proposed mechanism was established.

## Scope and task selection

The purpose is to test whether an actual, reproducible failure of a strong coding agent justifies implementing the proposed experiment-selection mechanism. Successful reproduction of a software bug alone is insufficient: the agent failure and the mechanism advantage must also be demonstrated.

The first candidate, Replay AB-9, could not be acquired through the available access paths. Its public task dashboard loaded in the browser, but the linked repository returned HTTP 404 and both published archives returned HTTP 403. These are access outcomes, not evidence of poor agent performance or proof that the repository was deleted. See the [access receipt](../reproduction/r1/evidence/artifact-access-check.json).

The cycle moved to the already-shortlisted [HashiCorp Raft issue 268](https://github.com/hashicorp/raft/issues/268). Its reported failure concerns shutdown overlapping snapshot work; the upstream repair is [commit 2e997410](https://github.com/hashicorp/raft/commit/2e997410f28efe8106fc606d21cb655be1b05dee). This is an independent reproduction on that real repository, not execution of DDBench or reproduction of the original dqlite deployment.

Original snapshot: `9a647f6c2bb9e057c49b85176086ab94a210c09d`.
Reference snapshot: `2e997410f28efe8106fc606d21cb655be1b05dee`.
Environment: Go 1.24.3, macOS 27.0.1 arm64. Source and environment are recorded in the [manifest](../reproduction/r1/evidence/manifest.json).

## What was actually executed

The [independent test fixture](../reproduction/r1/shutdown_regression_test.go) runs the repository's actual snapshot worker and shutdown API. Controlled peers supply the FSM snapshot and leave a queued configuration request unanswered, corresponding to a main worker that has exited. This is a component-level schedule, not an end-to-end cluster with production traffic. Source code is not replaced by a toy implementation.

The liveness test observes that the request has entered the buffer before initiating shutdown. It then requires shutdown to finish, with the snapshot caller receiving the shutdown error. A 250 ms test deadline detects the blocked waiter; it is an evaluator bound, not a new timeout inserted into the product or a production latency target. The test cleans up the deliberately pending request only after recording failure.

Two companion controls require a normal snapshot to preserve the fixture's data and reject a snapshot requested after shutdown. Four existing upstream tests exercise shutdown, snapshot restoration, automatic snapshots and user snapshots. The independent evaluator repeats these seven tests three times with the race detector. Repeated schedules improve reproducibility evidence but do not constitute independent bug coverage.

A deliberately invalid implementation that disables snapshots is rejected by the normal-snapshot control. An initial fixture compilation error involving a pointer versus value configuration was repaired before evaluating agents; its receipt is retained and excluded from agent outcomes. No failed development run was relabeled as a software or model failure.

## Baseline design and isolation

Three new Codex CLI sessions use the requested service model `gpt-6.1-sol`, high reasoning, CLI 0.160.1, a fixed [prompt](../reproduction/r1/baseline-prompt.txt), and a 600-second wall limit each. This is one strong available coding-agent configuration, not a comparison against every frontier model or a guarantee that this is the strongest possible setup.

Each session receives a fresh temporary repository containing only the original source snapshot and its existing tests, with a newly initialized one-commit history. It does not receive the upstream fix, independent fixture, task identifier, research documents, or this conversation. Memory is disabled and user configuration ignored. Instructions prohibit network research and outside task materials. Command traces are retained for auditing, but instruction-level restrictions are not a proof of complete filesystem isolation. Unknown pretraining exposure to this public historical bug remains possible.

The evaluator applies production changes to another fresh original tree, retaining upstream tests. Agent-written tests are saved for review but are not the success oracle. The primary acceptance criterion is the independent targeted suite, not the agent's final explanation. A broader suite is separately reported rather than silently omitted.

The [evaluation-plan receipt](../reproduction/r1/evidence/evaluation-plan.json) records three attempts and the stop condition. It was saved after attempt 1 began but before its outcome was known; this is a documented pilot, not a prospectively registered confirmatory study.

## Measured results

The [machine-readable analysis](../reproduction/r1/evidence/analysis.json) is calculated from command receipts and test events, not agent self-reports. Raw outputs, hashes, prompts, patches and changed files are retained in the [evidence directory](../reproduction/r1/evidence).

| Configuration | Independent targeted result | Measured time | Meaning |
| --- | --- | --- | --- |
| Original, race-enabled | Liveness failed 3/3; normal persistence and post-shutdown controls passed 3/3 each | 1.803 s total command time | The original defect is exposed; this is not an agent attempt |
| Upstream repair, race-enabled | All seven tests passed in each of three repetitions: 21/21 | 8.699 s total command time | Positive control; compilation/cache effects included |
| Baseline attempt 1 | 21/21 targeted checks passed | 314.606 s agent; 4.244 s independent evaluation | Accepted for reproduced defect |
| Baseline attempt 2 | 21/21 targeted checks passed | 321.029 s agent; 4.186 s independent evaluation | Accepted for reproduced defect |
| Baseline attempt 3 | 21/21 targeted checks passed | 401.253 s agent; 4.272 s independent evaluation | Accepted for reproduced defect |
| Invalid disabled-snapshots control | Normal-snapshot test failed | 2.625 s command time | Suppressing the feature is rejected |

Baseline targeted repair success is **3/3 attempts on one bug**. Median end-to-end agent time is **321.029 seconds**, range **314.606–401.253 seconds**, total **1,036.887 seconds** across attempts. These are descriptive measurements. The reference's command time and the agents' investigation times measure different activities and must not be presented as a speedup comparison. In particular, the original hang's evaluator timeout is not its true completion latency.

All three agents independently localized the abandoned configuration response wait, generated a shutdown-aware `select`, and added their own regression tests. Their production changes affect `snapshot.go`; the upstream fix instead generalizes cancellation in the future type and connects it at the call site. The independent evaluator accepts the alternate repair behavior rather than requiring textual agreement with upstream.

### Usage and operational cost

| Attempt | Reported input tokens | Cached input tokens | Input minus cached | Reported output tokens | Completed shell commands |
| --- | --- | --- | --- | --- | --- |
| 1 | 1,026,880 | 966,400 | 60,480 | 9,248 | 21 |
| 2 | 863,259 | 806,528 | 56,731 | 9,387 | 22 |
| 3 | 1,473,835 | 1,395,200 | 78,635 | 11,086 | 32 |

Token counts are the CLI's cumulative turn usage, not unique source tokens or simultaneous context size. Reported reasoning-output fields are preserved in the raw analysis and are not added again to output tokens. Monetary cost was not supplied or independently measured. The larger third-attempt runtime includes broader validation and troubleshooting; it does not establish slower reasoning or an inferior patch. Cache permissions, sandbox networking, compilation and repeated test effort materially affect wall time.

The three trials have identical source-archive and prompt hashes. Inspection of completed command traces found no external source-fetch or reference-history retrieval commands. This supports, but does not prove, the intended isolation; model training exposure remains unknown.

### Broader-suite qualification

The reference repair and baseline attempt 1 were each independently evaluated with `go test -race -json -count=1 -timeout=150s ./...` outside the agent sandbox. Both recorded **123 passes, one skip, and two failures**: `TestRaft_LeaderLeaseExpire` and `TestRaft_LeadershipTransferLeaderRejectsClientRequests`. This is evidence that these failures are not unique to the agent patch. It is not permission to call the full suite green or proof that every failure is harmless.

The third agent's internal validation also reported broader transport/fuzzy timeouts and snapshot timing issues. Its independent targeted evaluation still passed. Its separate outside-sandbox full suite also recorded **123 passes, one skip, and the same two leadership failures**, taking 30.578 seconds. Thus the extra internal failures did not recur in this external run; a single non-recurrence does not explain or disprove intermittent failures. Full-suite raw results are available for the reference and attempts 1 and 3; attempt 2 received the declared targeted independent evaluation, not a separate full-suite run.

### Statistical interpretation

No estimate of mechanism lift is available because no proposed mechanism was run. No Gemma score is available. Both are `null` in the analysis, not zero. There is no valid paired significance test comparing two methods here.

Even if the three trials were independent identically distributed samples for this one task, three successes yield only a one-sided 95% exact lower bound of `0.05^(1/3) ≈ 0.368` on that task's success probability. Those assumptions are not established, and the bound says nothing about other bugs. Thus “3/3 observed” must not become “guaranteed reliable.” The selection decision rests on lack of demonstrated need and differentiation, not on a statistically proved universal ceiling.

## Mathematical and logical assessment

Let S denote the caller awaiting shutdown, W the snapshot worker, and F its outstanding configuration future. In the reproduced state, the dependencies are S waits for W, and W waits for F. Once the main worker exits without responding, no producer remains that can resolve F. The original response-channel receive therefore cannot complete in that state.

The baseline repair makes the response wait select between a response and the closed shutdown channel. In the reproduced no-response state, the shutdown branch is enabled. Under eventual worker scheduling, finite snapshot cleanup, and termination of other shutdown workers, W exits and releases S. Receiving a legitimate configuration response also preserves the channel synchronization needed before reading the returned configuration.

This is a bounded liveness argument about a specific dependency, not a universal proof of repository correctness. The [assumption record](../reproduction/r1/evidence/liveness-argument.json) excludes arbitrary snapshot implementations, all possible cluster executions and unseen coding tasks. Successful testing cannot establish zero failure probability. No information-gain selector, causal-learning algorithm, Gemma tuning or other proposed advanced mechanism was needed to obtain the observed baseline repairs.

## Interpretation limits

- One historical bug is insufficient to estimate prevalence or general coding-agent capability. Three attempts are not three tasks.
- The controlled schedule exposes a known failure state; it does not measure natural production failure frequency.
- The fixture was authored after inspecting the upstream fix. Its controls and untouched-baseline evaluation reduce oracle circularity but do not make it a blind benchmark design.
- Model service identifiers are recorded, but immutable model weights and sampling seeds are unavailable. Shared prefix caches and runtime variation affect timings.
- End-to-end agent time includes reading, editing, test compilation and validation. It is not pure model inference latency or a competition-hardware benchmark.
- No Gemma run, proposed-method run, specialist-method comparison, holdout task evaluation or monetary cost measurement has occurred. Their values are unknown, not zero.
- Artifact access and sandbox restrictions are separately classified. They cannot be counted as model reasoning failures.

## Product decision gate

The result must distinguish three questions: can the software bug be reproduced, can an ordinary strong agent repair it, and does our mechanism improve on that baseline? The first two have positive evidence in all three completed trials. The third has no measured result. Baseline success is counterevidence to using this case to justify a necessary new capability; it is not proof that a future mechanism could never reduce cost or help other cases.

Do not promote the current debugging proposal into a final product on this evidence. A valid future target needs an accessible, harder task set on which the tool-equipped baseline actually exhibits a persistent limitation, followed by a distinct mechanism and a matched comparison. Adding advanced mathematics to a solved example would not satisfy the user's standard.

This was an early selection-gate cycle, not a completed 8–14-hour mechanism implementation phase. It stopped before implementing a novel selector because the required baseline failure was not established. Neither a product interface nor a mathematical embellishment would repair that missing premise. The repository planning documents are updated with this negative adoption result, not with an unsupported final-product commitment.

## Completion audit

| Requested outcome | Evidence and disposition |
| --- | --- |
| Create and execute a reproduction cycle | Real pinned repository, independent executable fixture, positive/negative controls and retained command receipts; completed at component scope |
| Strong baseline attempts | Three fresh sessions with matching prompt/source hashes; patches independently evaluated; completed |
| Results and detailed performance analysis | Measured success, runtime, usage, broader-suite failures and statistical limits above; completed |
| Mathematical/logical back-check | Explicit liveness assumptions and synchronization argument; no universal guarantee or invented advanced contribution |
| Promote a final product only if justified | Gate did not pass: no persistent baseline failure or mechanism advantage was demonstrated; final product deliberately not adopted |
| Explain the negative decision | Baseline repairs, prior-art overlap, one-task scope, access and environment limitations are explicit |
| Verify deliverables | Sixteen saved command receipts had their output hashes checked; prompt hashes matched all three trials; analysis recomputed; local links, Python compilation, runner unit tests and diff whitespace checks passed |

The missing mechanism/Gemma comparisons are the reason promotion is withheld, not evidence of their failure. The requested reproduction-and-report cycle is complete under its negative-decision branch; the larger research program remains unproven.
