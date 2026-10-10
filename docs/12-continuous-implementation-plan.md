# Continuous implementation and acceptance plan

Updated October 8, 2026. **Living plan; user adopted a foundation-first, trainable Gemma agent. P0 is accepted within its recorded scope. P1 has real GPU inference and submitted-patch evidence, but is not fully accepted; training has not started.** Codex owns implementation, mathematical design, engineering, tests, analysis, and evidence preparation. The entrant supplies account access, eligibility decisions, and resource authorization. This document governs cycle cadence; [platform specification and handoff](19-agent-platform-and-model-handoff.md) governs the current build, [joint strategy](11-code-track-and-joint-strategy.md) governs competition constraints, and [evaluation protocol](05-evaluation-protocol.md) governs experiments.

The objective is a reproducible, competitive repair agent with defensible research results. Mathematical sophistication must improve a justified objective or explain observed behavior. No fabricated results, task-specific answer lookup, leaked reference patches, or cosmetic chat interface presented as a working system. Explicit configuration constants and clearly labeled synthetic test fixtures are legitimate; hardcoded benchmark outcomes are not.

## Cycle structure

**R1 closeout — October 7:** accepted as a bounded bug reproduction and baseline challenge; **revise the product hypothesis, no promotion**. The React artifact was inaccessible. The previously shortlisted real Raft shutdown defect was reproduced in a controlled component test. Three fresh `gpt-6.1-sol` high-reasoning attempts each passed 21 independent targeted race-enabled checks. Agent times were 314.606, 321.029 and 401.253 seconds. Broader suites retain two failures also present on the upstream reference repair. See [complete results and limits](18-reproduction-cycle-results.md). This does not establish Gemma performance or mechanism lift. Stop before R3: the required persistent baseline failure was not demonstrated. The next research input must be a different accessible failure set, not a product build around this solved example. This early gate did not consume or claim an 8–14-hour implementation phase; hands-on engineering time was not separately instrumented.

Use **8–14 hours per engineering cycle**, including protected acceptance work. A nominal 12-hour cycle allocates one hour to design and scope, six to implementation, three to verification, one to comparison, and one to assessment and documentation. Reallocate after measurement; never omit validation to meet the timebox. A phase may require several cycles. Do not fill time with unnecessary work or declare unfinished work accepted when time expires.

At cycle start, select one bounded deliverable, baseline commit, hypothesis, resource cap, failure conditions, and acceptance criteria. During implementation, checkpoint resumable work and test incrementally. At closeout, assign **accepted**, **revise**, or **blocked** with evidence. Record active engineering time, experiment runtime, and elapsed wall time separately. The cycle target is not a promise of unattended execution between chats.

## Phases and exit gates

P1 implementation evidence is tracked in [document 24](24-p1-implementation-status.md). The October 8 checkpoint storage gate passed; GPU inference and P1 acceptance remain pending.

**October 7 scope replacement:** build the general agent now; do not wait for a new specialist product hypothesis. Earlier graph, synthesis, migration, undo, simulator and GPU-optimization proposals are not mandatory components. Failure-first comparisons remain the gate for claiming a novel advantage. The historical R1 instruction to stop before R3 applied to the discarded mechanism, not the platform phases below. This documentation update is not an implementation cycle.

| Phase | Main work across one or more cycles | Required exit evidence |
| --- | --- | --- |
| P0. Contracts and skeleton | Obtain HARNESS_README.md and starter; pin schemas; design state/event records, packaging and dependency boundaries | Contract tests and archive validation; no fabricated model calls; fixtures explicitly synthetic. Can begin without weights |
| P1. Model intake and inference | Confirm user's downloaded path/version; inspect and hash complete model package; run exact quantized model and multi-turn tool calls | GPU memory/latency receipt; parsed tool calls and tool-result continuation; real starter task and captured patch. Runpod first required here |
| P2. Complete agent execution | Implement inspect/localize/edit/test/recover/submit; state transitions, bounded calls, checkpointing and offline behavior | Actual end-to-end tasks; interrupted/failed-tool tests; patch preservation and budget exhaustion checks. Linux worker needed here or earlier for harness smoke tests |
| P3. Independent evaluation | Audit task images and test oracles; freeze splits; record untuned Gemma baseline across task families | All-task denominator, failure categories, repeats and resource metrics; evaluator assets isolated from agent |
| P4. Core capability improvement | Compare repository context selection, reasoning settings, test selection, recovery and cost-aware stopping | Matched development comparisons and ablations; mathematical claim checks; simple baseline retained if stronger |
| P5. Training pipeline and pilot | Curate licensed trajectories; prove compatible adapter training/export/load; run supervised LoRA pilot with train-only feedback | Loss-mask and gradient checks, checkpoint resume/reload, independent post-training repair evaluation; no automatic promotion from lower loss |
| P6. Trained capability expansion | Tune data mixtures and difficult-task curriculum; evaluate preference/RL methods only with sound rewards and compute | Reproducible checkpoint and held-out gains under equal budgets; regression and contamination audit; unhelpful adapters rejected |
| P7. Platform and submission qualification | CLI/batch interface, run inspection, artifact registry, restart/cancel controls; offline clean build and full-budget replay | Target-runtime compatibility, manifests/hashes, restore test, packaged champion. Cloud services remain outside scored execution |
| P8. Research and releases | Identify a measured specialist gap, audit prior art, compare a novel intervention; freeze separate paper and code artifacts | Claims supported by frozen evidence; novelty optional for baseline completion but required for novelty claims; submission status checked separately |

P4–P6 are iterative. Building and testing a training pipeline is part of the adopted platform; deploying a trained adapter requires evidence. Full RL and specialist mechanisms remain conditional. Return to P2 when infrastructure invalidates measurements. Every phase may take multiple 8–14-hour cycles. Deadline pressure reduces scope, never evidence standards.

## Acceptance and correctness

Every cycle closes with these six assessments, marking a category inapplicable only with a reason:

1. **Mathematical validity:** maintain a claim ledger linking assumptions, derivation or proof, implementation, numerical tolerances, counterexamples, and limits. Check boundary cases and dimensions. A coverage-surrogate theorem does not prove repair success; a continuous concave allocation argument does not establish optimality for unknown discrete task responses.
2. **Software validity:** require focused unit, property, integration and regression checks appropriate to the change. Compare small optimization instances with an independent exhaustive reference. Exercise malformed tool output, empty evidence, interrupted execution and resource exhaustion where relevant. Verify real patch production and grading end to end.
3. **Statistical validity:** predeclare the primary comparison, estimand, cohort, meaningful effect, analysis and stopping rule. Pair tasks across methods; account for repeated seeds and repository dependence. Report effect sizes and uncertainty. Few repositories limit generalization; more seeds do not create independent tasks. Use a fixed confirmatory analysis or a justified sequential procedure, not repeated uncorrected significance checks.
4. **Fair comparison:** use the same task manifest, model constraints, grading and declared budget conditions. Count failures and timeouts; report setup and preprocessing. Audit exclusions before comparing methods. Keep development, confirmatory and leaderboard evidence distinct.
5. **Engineering quality:** assess maintainability, interface compatibility, reproducibility, observability, resource consumption and failure recovery. Remove unnecessary mechanisms. Evaluate numerical stability and deterministic replay where supported; record unavoidable nondeterminism.
6. **Evidence integrity:** every reported result traces to retained logs, configuration, data/environment versions and artifact hashes. Label planned, synthetic, measured and proved content distinctly. Missing evidence is unresolved, never inferred into a passing result.

**Integration acceptance and champion promotion are separate.** Correct infrastructure can be accepted without an accuracy gain. A performance intervention becomes champion only under predeclared repair and resource criteria. For paired outcomes, report the average task-level difference, with uncertainty appropriate to the sampling design. If superiority is required, an interval crossing the required improvement threshold is inconclusive. Efficiency promotion requires its declared accuracy noninferiority and resource criteria. Choose margins before viewing results; insufficient power cannot establish equivalence.

No finite test suite guarantees arbitrary patches or all future executions. Guarantees must name their domain: a proved property under stated assumptions, verified bounded states, or observed behavior on identified tests. Known correctness defects, invalid statistics, leakage, or missing critical evidence block promotion. A polished demo cannot override these gates.

## Adjustable variables

| Variable | Current setting and revision rule |
| --- | --- |
| Cycle duration and phase count | 8–14 hours; nominal 12. Estimate remaining cycles after the baseline pilot |
| Compute, storage and cash caps | First P1 GPU session: four hours at observed $1.79/hour, about $7.16 compute maximum; remote work ended early, Pod stop remains user-controlled. New sessions need their own cap |
| Hardware and runtime reserve | A100 80GB inference observed at up to 67,231 MiB in recorded samples; not a whole-run peak or training-memory estimate |
| Cohorts, seeds and evaluation budget | Provisional in document 5; freeze before relevant comparisons; log changes and lost holdout status |
| Effect threshold, noninferiority margin, confidence level | Declare per comparison before outcomes; use document 5 as the starting protocol, not a post-hoc choice |
| Candidate mechanism | Core Gemma agent adopted; specialist novelty undecided. Prioritize measured localization, editing, tool-use and budget failures |
| Deadline allocation | Preserve separate paper/code freezes; revise the resource schedule after each cycle |

## Required closeout and next cycle

After **every** implementation cycle, append a record below and update current variables, next-cycle scope, and affected technical/evaluation/resource/decision documents. Preserve old records and frozen results. No cycle is closed until documentation and evidence agree.

Each record includes: cycle ID; timestamps and three time measures; objective; baseline/candidate hashes; changes; proof and test evidence paths; task/config/run manifests; measured metrics and intervals; costs; failures and unresolved assumptions; six-category assessment; integration and promotion decisions; rollback reference; and next bounded objective. Use “not measured” where applicable. Do not manufacture an aggregate quality score from subjective ratings.

| Record | Status | Evidence and next action |
| --- | --- | --- |
| Planning, October 7 | Documentation only; no implementation cycle completed | Next cycle: phase 1, authorized harness inspection and smallest reproducible baseline. Resolve access and resource caps first; preserve protected evaluation tasks |
| Foundation-first revision, October 7 | Plan updated; live overview/model/plugin checks completed; no GPU allocated | Next cycle P0: official harness/starter intake, contract fixtures, state schema and packaging. Model required at P1; ask for downloaded folder/version then. Runpod read succeeded, DigitalOcean account active, Cloudflare not discoverable in current plugin search. See document 19 |

Once implementation begins, add detailed cycle records under this table or link them here from a dedicated cycle-log directory. Update this plan as evidence changes; retain the acceptance standards unless an explicitly justified revision improves their validity.


### R0 local foundation checkpoint — October 7, 2026

R0 means P0 in this plan. Status: **revise / official integration pending**. Baseline commit `20b44be`; uncommitted candidate identity is the per-file SHA-256 map in [local-002 receipt](../evidence/r0/local-002/receipt.json). Historical reproduction evidence is unchanged. Implementation and claim audit: [document 20](20-r0-foundation.md). Provider preparation: [document 21](21-cloud-preparation.md).

- Implemented: pure state/event contracts, exact budget and context admission, artifact manifests and verification, split validation, bounded ZIP structure inspection, CLI and offline verification script.
- Verification: 25 synthetic contract/integration tests passed; isolated zipapp success and rejection exits passed. Test log: [local-002/tests.log](../evidence/r0/local-002/tests.log). The earlier local-001 receipt predates a correction to zipapp exit-code propagation in the verification script; local-002 supersedes it for packaging evidence.
- Timing: recorded verification began 2026-10-08 00:40:27.143545 UTC and ended 00:40:27.435433 UTC; monotonic duration 0.291682625 seconds. Active engineering time and total session wall time were not instrumented. This checkpoint does not claim an 8–14-hour cycle was completed.
- Metrics: repair rate, model latency, training improvement and comparative confidence intervals not measured. No billable resources created; local energy/API costs not measured. Existing account charges not audited.
- Mathematical assessment: exact arithmetic and invariant arguments documented with bounded independent references. Software assessment: local checks pass; Linux and official runtime remain unverified. Statistical and fair-comparison assessment: no empirical treatment comparison yet; draft split only. Engineering assessment: standard-library package, explicit errors and retained failure paths. Evidence assessment: source hashes and real logs retained; fixtures labeled synthetic.
- Failure analysis: authenticated rule acceptance is now verified in Chrome, but the official files have not been retrieved. Browser navigation to Data did not yield readable file contents during this attempt. No official YAML contract was invented. Submission preflight cannot establish ADK compatibility.
- Integration decision: local foundation verified within documented assumptions; full R0 not accepted. Champion promotion: inapplicable, no model candidate. Rollback reference: baseline commit above; preserve historical reproduction files and any later user changes.
- Next bounded work: retrieve the authorized harness/starter, pin its exact contracts and offline dependencies, implement corresponding integration tests, then confirm the downloaded model path before P1. Runpod and DigitalOcean authenticated reads succeeded again. Cloudflare and SSH remain unverified.


### R0 official contract checkpoint — October 7, 2026

Status: **progress; Linux integration pending**. The asset-access blocker was resolved by authenticated Kaggle CLI using existing local credentials. The official guide, starter, notebook and four host wheels were downloaded and hashed. No task reference fixes were read. See [official audit](22-official-contract-audit.md).

- Baseline remains `20b44be`; candidate identity is in [core-003](../evidence/r0/local-003/receipt.json) and [compiler-004](../evidence/r0/compiler-004/receipt.json). Local tests: 26 passed plus isolated offline CLI checks. Official CPU compilation: unchanged starter plus eight rejection checks passed; three alias probes retained separately, two exposing a documented discrepancy.
- Compiler run: 2026-10-08T00:48:59.081900+00:00 to 2026-10-08T00:48:59.172494+00:00, 0.090594041 measured seconds. Core verification: 0.341357917 seconds. Engineering/session durations not instrumented; no claim of completing an 8–14-hour cycle.
- Correctness: retained algebraic/invariant checks, actual schema export, exact negative-error checks. Software: core/CPU compiler passed; Linux daemon unavailable. Statistics/comparison: no model evaluation, therefore no repair effect estimate. Engineering: isolated dependency tooling; core remains standard-library-only. Evidence: asset hashes, package inventory, source tool signatures and receipts retained. Test-fixture defects and upstream discrepancies are explicitly recorded in document 22.
- Cost: no billable resource created; acquisition traffic/local/API costs not measured. Promotion: no trained candidate or measured performance. Integration: full Linux sandbox/tool execution unresolved, despite successful CPU compilation. Historical compiler-002 negative-check attribution is superseded by compiler-004.
- Next scope: make the installed Docker daemon available or use an authorized bounded Linux worker; qualify the real sandbox/tool contracts. Model path and GPU spending cap are needed for P1, not for CPU compilation. The user no longer needs to download the harness/starter manually. Rollback uses the baseline commit while preserving historical evidence and unrelated changes.


### R0 Linux acceptance checkpoint — October 7, 2026

- Decision: **accept R0/P0 contracts and skeleton**, with all eight P0 deliverables audited in document 20. This closes infrastructure qualification only; no trained candidate or performance promotion.
- Candidate identity: [local-004 source hashes](../evidence/r0/local-004/receipt.json); [Linux receipt 002](../evidence/r0/linux-002/receipt.json) and [audit](../evidence/r0/linux-002/audit.json) pin the integration script, image and supporting evidence. Baseline/rollback reference remains `20b44be`; preserve prior evidence and unrelated changes.
- Software: 26 core tests pass on macOS and Linux; isolated zipapp checks pass; nine CPU compiler checks pass; 25 real-tool integration checks pass. Starter compilation now uses actual bound tools and the official limits builder. Exact synthetic patch transfers into a fresh container and passes there. No test containers remain.
- Mathematical assessment: exact arithmetic and state invariants remain supported by the claim ledger; tool integration adds observed boundary behavior, not a universal proof. Statistical assessment and fair comparison: inapplicable to performance promotion because no model or task cohort was evaluated. Engineering assessment: isolated no-network containers, pinned image, explicit failures and cleanup. Evidence assessment: retained failed Linux run and corrected representation check, immutable receipts and source hashes.
- Timing: Linux integration started 2026-10-08T00:57:32.035081+00:00 and finished 2026-10-08T00:57:42.257523+00:00; measured duration 10.222385958 seconds. Active engineering/session durations were not instrumented; this does not claim an 8–14-hour cycle.
- Costs: no paid resource created; local compute, transfer and API costs unmeasured. Repair rate, latency, confidence intervals and training gains remain unmeasured.
- Unresolved later-phase gates: actual checkpoint/loader, successful graph retrieval on real assets, full offline host installation, official Phase 2 grading, target GPU execution and comparative evaluation. Linux execution here uses AMD64 emulation on ARM64 macOS.
- Next bounded objective P1: receive complete model folder and Kaggle revision, inventory and verify it, establish experiment/storage/runtime caps, then propose the exact GPU allocation and run real inference plus an adapter compatibility smoke test. Prepare provider access as described in document 21; DigitalOcean and R2 allocation is not needed to finish R0.


### Data research update — October 8, 2026

See [document 23](23-data-requirements-and-acquisition-plan.md) for the proposed data plan supporting the user-preferred three 50M-token candidates. This is a research/planning update, not an implementation cycle or permission to spend on teacher generation. External sources are shortlisted, not yet admitted. Mixtures are provisional and total 50M processed tokens per candidate; they do not imply 150M unique source tokens. P1 requires only a small development subset; freeze contamination groups before corpus ingestion. Official task assets total approximately 22.42GB in the saved download listing; expanded environments are extra. Next gate: authenticated source-rule check, task/environment intake and native baseline traces. No training gains or data-quality acceptance are claimed.

### P1 first GPU session — October 8, 2026

Status: **revise / partial integration evidence**, no trained-candidate promotion. [Session report](27-p1-gpu-validation-report.md) records the environment correction, two actual attempts, independent local grading and remaining gates. Remote work lasted about 42 minutes after the approved start; active engineering time and the final billed Pod duration were not instrumented. The server stopped and temporary remote access was cleaned up. The user was notified to stop the Pod. Subsequent documentation and evaluator checks are local.

Next bounded work: finish durable recovery verification for the updated deployment/evidence; resolve official evaluator source selection and baseline compatibility, then investigate tool-call variability with captured failures. No bulk synthetic generation or training begins merely because the model loaded. P4 remains the main synthetic trajectory phase; P5 uses qualified training data for the pilot, and P6 owns the proposed three up-to-50M processed-token candidates.

Recovery closeout: the revised 75-file deployment bundle was published to R2, independently restored and passed all 77 tests from the restored copy ([qualification](../evidence/p1/deployment-restore-003/qualification.json)). The 28 evaluator dependency wheels also passed independent restoration. The separate audit archive was published and a fresh absolute-path restore independently verified all 493 members ([qualification](../evidence/p1/evidence-restore-002/qualification.json)). The first restore returned a passing receipt, but its destination was absent at follow-up; this unexplained discrepancy is retained in `evidence-restore-001/follow-up.json` and that first receipt is not treated as accepted recovery evidence. This archive contains evaluator outcomes and must not be used as agent context or training data. These recovery checks do not waive the remaining P1 acceptance gates.

### P1 local follow-up: final-destination recovery checks

Progress: strengthened restoration to verify the promoted public directory and bind its absolute path before transport callbacks. Two new fault tests passed; the complete local and freshly restored suites each passed 79 tests. A live R2 restore passed the revised path check. Deployment bundle 004 supersedes bundle 003 for this implementation and passed independent restoration ([qualification](../evidence/p1/deployment-restore-004/qualification.json)). The initial missing-directory anomaly remains unexplained; no cause was inferred from the new tests. The fifth unchanged evaluator failure was traced to HTTP fixture response construction, not changed Requests code. P1 remains unaccepted; continue evaluator compatibility and model/tool qualification locally before requesting any further GPU session. No GPU work or training ran in this follow-up.

### P1 local follow-up: actual pytest-process source qualification

Progress: implemented an evaluator-only source gate observing loaded modules inside pytest. The uncorrected environment is rejected before execution; the corrected environment passes the source gate, matches exact snapshot-plus-agent-patch source hashes, and retains all 324 previous per-case outcomes. All 81 local and restored-copy software tests passed. Deployment bundle 005 includes the plugin and corresponding tests and passed independent R2 recovery ([qualification](../evidence/p1/deployment-restore-005/qualification.json)). No GPU inference or training ran.

This strengthens the validity of local measurements without asserting that the organizer runtime has been repaired. Remaining work includes broader model/tool qualification and a defensible resolution of official evaluator incompatibilities. P1 remains unaccepted; the active implementation objective is unchanged.

### P1 requirements audit and resource evidence

The [requirements audit](28-p1-requirements-audit.md) separates the published intake/inference exit criteria from the broader reliability, independent evaluation and training obligations. It indexes actual memory/latency measurements and retains every unresolved limitation. The Pod is now confirmed `EXITED` by an authenticated read. No inference or training was started. The broad objective remains active; this audit is not a phase waiver or an assertion of training readiness. Next work must address a functional qualification gap rather than accumulating redundant packaging or test-count updates.

### P1 network-dependent evaluator qualification — October 8, 2026

The unchanged Requests baseline and captured agent patch were evaluated in the
same pinned Docker image with bridge networking, an explicit local diagnostic
source-path override, and source provenance checked inside pytest. Four timeout
failures disappeared from both runs. Of 324 paired cases, only the target
content-length regression changed (failure to pass); the candidate has 321
passed, one failed, and two skipped (including xfail). The remaining failure
is the HTTP fixture rejecting a negative-port redirect before delivering it
to Requests. Both official aggregate results remain false. This does not
establish Kaggle environment parity or an overall benchmark solve.

Added reusable JUnit comparison that rejects empty reports, duplicate identities,
ambiguous outcomes, declared-count mismatches, and different case sets. All 90
local tests passed. Individual tests are not independent task-level statistical
samples. Evidence: `evidence/p1/repair-network-comparison-001/receipt.json`.
No GPU work or training ran. Next: resolve the fixture/runtime compatibility
boundary without altering benchmark assertions, and continue training-readiness
qualification separately from this single repair.

### P1 clean local repair qualification — October 8, 2026

The unchanged agent patch now receives local resolved=true through the released
verifier: 322 passed and two skipped (one xfail); baseline has 321 passed, one
failed and two skipped. Exactly the target regression changes across 324 paired
cases. See [analysis](../evidence/p1/repair-compatible-comparison-001/analysis.md).
Historical HTTP fixture dependencies and a fresh per-run unpacked-wheel cache
were needed in addition to the previously recorded source-path/network controls.
The runner now records actual fixture versions and manifest identity. All 90
local tests passed. No GPU time or training was used. Official target parity,
broader reliability, and training qualification remain open; do not rerun this
same repair simply to accumulate repetitions.

### Training representation preflight — October 8, 2026

The pinned compressed-tensors path decompresses for forward execution. Static
checkpoint accounting gives 60.8757 GiB of dense BF16 weights, excluding working
memory. The [representation readiness note](31-training-representation-readiness.md)
sets the next CPU gradient/adapter and bounded GPU qualification steps. No long
training run, new weights, or H100 fit is approved by these static calculations.

### Synthetic CPU adapter qualification — October 8, 2026

The real compressed-tensors codec and PEFT passed a synthetic exact-grid
roundtrip, independent gradient comparison, frozen-base check, measurable
adapter effect, and exact adapter save/reload. See document 31 and
`evidence/p1/adapter-cpu-002/receipt.json`. This is CPU Torch 2.14.1, not the
CUDA training runtime. Next qualify a reduced Gemma architecture, masking
and optimizer resume before preparing the full-checkpoint GPU pilot. No
model-training or repair-performance gain is claimed from the toy fixture.

### Reduced Gemma training mechanics — October 8, 2026

Pinned Gemma4 code with random reduced dimensions passed exact adapter coverage,
independent masked-loss and logit-gradient checks, frozen-base integrity, and
bitwise optimizer-resume equivalence under non-reentrant checkpointing and
zero dropout. Receipt: `evidence/p1/gemma-training-cpu-002/receipt.json`. This
does not establish native chat-mask correctness, full-checkpoint training,
CUDA memory fit, stochastic resume, or a performance gain. Next prepare native
conversation masks and loader qualification locally; no GPU work occurred.

### Native assistant supervision — October 8, 2026

Added template-hash-bound assistant masks with exact native text/token identity
and character-boundary checks. Four actual-tokenizer fixtures and three invalid
input checks passed, including exclusion of a tool result containing model-turn
markers. Evidence: `evidence/p1/training-masks-001/receipt.json`. No corpus is
approved by these fixtures; padding/packing and full-checkpoint gradients are
not yet qualified. No GPU work occurred.

### Native batching integration — October 8, 2026

Native assistant masks now feed a strict independent-sequence collator. Actual
Gemma token IDs and full vocabulary passed reduced-model CPU loss/gradient
equivalence checks between a padded batch and token-weighted microbatches
with unequal target counts. Masked padding changes leave loss unchanged.
All 92 unit tests passed. Evidence: `evidence/p1/native-training-batch-001`.
Packing and full-checkpoint loader/CUDA qualification remain open. No GPU
compute or training corpus was used.

### Compressed BF16 loader qualification — October 8, 2026

A reduced random Gemma BF16 model was packed to W4/group32, saved, reloaded via
the pinned Transformers quantizer, and trained for one adapter update on CPU.
Loaded state matches its decompressed reference exactly; base remains frozen;
adapter reload reproduces logits exactly. Receipt:
`evidence/p1/compressed-gemma-loader-001/receipt.json`. Next prepare the bounded
full-checkpoint GPU bundle; no full-model training readiness, vLLM adapter
compatibility, or performance gain is claimed. No GPU compute was used.

### Full-checkpoint test preparation — October 8, 2026

PEFT 0.21.2 metadata satisfies all ten active dependencies against the existing
Linux/Python 3.12 GPU lock; no core-package change is planned. Added a pinned
supplement and a [bounded qualification specification](32-full-checkpoint-gpu-qualification.md)
with an explicit unexecuted profile. Next implement and locally test the worker
and external deadline supervisor. This is preparation, not full-model training
qualification or GPU execution.

### Training supervisor implementation — October 8, 2026

Implemented external POSIX process-group deadlines, stop requests, termination
escalation and interruption cleanup. Seven lifecycle tests passed on macOS and
local Linux; the full suite passed 99 tests. The training worker itself and
GPU integration remain pending. No GPU time was used. Evidence:
`evidence/p1/process-supervisor-001`.

### Frozen-state audit implementation update

Added bounded-chunk state fingerprinting for the training qualification worker,
including parameters and persistent buffers, with explicit adapter exclusions.
Six dedicated CPU tests passed. Integrated the check into the reduced BF16
compressed Gemma loader/adapter probe; evidence is recorded under
`evidence/p1/training-state-001` and `evidence/p1/compressed-gemma-loader-002`.
Full CUDA worker integration and checkpoint qualification remain pending;
this update does not approve a training streak or close P1 acceptance.

### Shared adapter qualification engine

Implemented `zenithsync/training_pilot.py`: exact target/shape and adapter-count
checks, non-reentrant checkpointing, one AdamW update, finite gradient and
parameter checks, frozen state fingerprints, adapter/optimizer export, complete
first-model scope release, independent reload, and predeclared output comparison.
The reduced compressed BF16 Gemma probe passed with 7,808 trainable parameters
and zero reload logit error. Weak references confirmed the first base object
was released before the second load. Ten focused tests passed, including
wrong-target, missing-supervision, altered-reload-base and output-preservation
failures. Evidence: `evidence/p1/training-pilot-cpu-002` and
`evidence/p1/training-pilot-tests-001`.

Remaining: full CUDA entry point, native-tokenized fixture integration, runtime
and storage preflight, memory measurements, supervisor integration and actual
GPU qualification. Optimizer state is saved but resume is not qualified by
this engine. CPU results do not qualify full-model training or repair quality.

### Full-checkpoint command and native fixture integration

Added a deadline-supervised full-checkpoint command and CUDA worker, with
persistent-filesystem checks, exact manifest verification, pinned core runtime
versions, single-device/no-competing-process admission, exact projection count,
native supervision and shared update/reload qualification. Native fixture
preflight passed: 24 input tokens, five supervised targets. Three storage
admission tests passed, including symlink escape rejection. CLI imports/help
are checked without loading the model. Evidence:
`evidence/p1/training-worker-preflight-001`.

No GPU command has been executed. Device-wide memory sampling, curated
deployment preparation and actual full-checkpoint qualification remain open.
The command does not start/stop the Pod or extend session authorization.

### Device-wide telemetry and deployable source closure

Added persistent initial/periodic/final device-memory samples, strict parsing,
identity/capacity consistency and failure propagation. Six monitoring tests
passed; the core suite passed 108 tests with ten separately scoped Torch tests
skipped. Prepared an explicit 19-file source bundle and verified both CLI
imports outside the checkout and in a network-disabled Linux container.
Evidence: `evidence/p1/gpu-memory-monitor-001` and
`evidence/p1/training-deployment-001`. Device readings are sampled maxima,
not continuous peak bounds. Full CUDA execution remains unperformed; no
training-corpus or coding-quality claim follows from this preparation.

### H100 full-checkpoint attempt and setup diagnosis

Verified persistent storage, idle H100, 251 runtime pins and PEFT dependencies.
The full checkpoint loaded/decompressed, but the first qualification attempt
was stopped after 278.84 seconds of prolonged CPU-heavy setup. Supervisor
cleanup and zero remaining GPU memory were confirmed. No update/reload success
is claimed. Default Torch thread counts were 104/104; added explicit 4/1 thread
limits and stage timestamps for the next bounded attempt. Ten focused tests
and the reduced compressed-model probe passed after this instrumentation.
Evidence: `evidence/p1/full-training-gpu-001`,
`evidence/p1/training-thread-limit-001`, `evidence/p1/training-pilot-cpu-003`.

### Full-checkpoint H100 one-update qualification passed

The revised bounded worker completed in 216.195 seconds. All 30,607,360
rank-four adapter parameters matched expected targets/counts; loss and gradients
were finite; an optimizer update changed the adapter; frozen state remained
identical; export and fresh reload reproduced logits exactly. The diagnostic
used only one 24-token synthetic example with five supervised targets.
Peak Torch allocated/reserved memory was 60.919/71.961 GiB; maximum sampled
device-wide memory was 72.632 GiB. Process cleanup and zero remaining GPU memory
were confirmed. The temporary session SSH key was removed, preserving other keys.

Complete outputs remain on the network volume and in a local copy verified
against the remote manifest. Evidence: `evidence/p1/full-training-gpu-002`;
large artifacts: `artifacts/official/p1-full-training-gpu-002`;
R2 publication: `evidence/p1/full-training-gpu-publish-002`.
P1 remains open. Next functional gates are full-model resume/stability and
realistic sequence-length admission, adapter serving compatibility, qualified
data ingestion and held-out agent evaluation. No long training streak has begun.

### Optimizer export audit and identity-bound resume contract

Audited the actual H100 export locally: all 820 states/30,607,360 parameter
elements have finite moments, nonnegative second moments, step one and
first-step Adam consistency within a declared numerical tolerance. The old
export has no names, so full-model resume remains unqualified. Added explicit
ordered name/shape/dtype and hyperparameter validation for new optimizer
checkpoints. Five contract tests and four engine failure tests pass; a reduced
Gemma export/reload probe passes with the new format. No GPU run occurred for
this change. Evidence: `evidence/p1/exported-optimizer-audit-002`,
`evidence/p1/optimizer-contract-001`, `evidence/p1/training-pilot-cpu-004`.

### Pinned public-data quarantine intake

Acquired and hash-verified one 151.8 MB SWE-Hero shard plus pinned source cards
and Nebius metadata/LICENSE. The shard contains 2,500 distinct issue records
over eight repositories; the first-shard selection is not representative.
Metadata-only inspection found no exact competition-repository overlap but
identified missing explicit tool-response IDs and no row-level resolved field.
No trace body or patch was read by this audit and no source was training-approved.
Implemented bounded publisher-hash verification, four download tests, and a
metadata-only audit. See [current findings and admission work](33-public-data-intake.md).

### Source-history conversion without fabricated tool outcomes

Implemented a strict SWE-Hero converter that preserves source call IDs, links
responses only to one outstanding call, retains unanswered terminal finish
calls, and records inferred-link provenance. All 2,500 acquired histories passed
its structural contract: 296,414 messages and 144,457 inferred links. Five
rejection/preservation tests passed. No commands were executed, no task-success
label was invented, and no source tool was renamed to imply runtime equivalence.
Native pending-call supervision, tool semantics, replay, rights and broader
contamination remain open. Evidence: `evidence/data/swe-hero-conversion-audit-001`.

### Native supervision qualified; long-context admission gap measured

Added explicit terminal-tool supervision without weakening default complete
history checks. Four contract tests and six positive/six negative native
tokenizer fixtures pass. A predetermined per-repository sample of eight real
trajectories passes full render/token identity and mask checks without truncation.
Lengths range from 32,376 to 114,224 tokens; seven exceed the current 32,768
serving cap and all exceed the actual 24-token GPU qualification fixture.
Next data admission work must address context handling jointly with the runtime,
not silently truncate traces. Tool semantics, replay, rights and contamination
remain open. Evidence: `evidence/data/native-trajectory-masks-001`.

### Imported-history causal ordering correction

Found that naive native rendering moves source assistant text accompanying a
tool call behind its result. This affects 104,196 result-followed messages in
the acquired shard. Added an explicit, provenance-preserving field projection
into Gemma's pre-action channel, with guards against later-user text loss and
reasoning-field collisions. The native synthetic fixture verifies chronology
and invariance of earlier tokens under changed future results. Four unit tests
pass; all 2,500 histories meet structural projection preconditions and the same
eight sampled traces pass native mask checks. Their lengths remain too large
for current admission. Earlier mask results were format consistency, not proof
of semantic chronology. No training data was promoted and no GPU was used.

### Full-shard context measurement and admission decision

Measured all 2,500 projected native histories without truncation: 120,914,948
input-token occurrences, median 44,981, maximum 183,776. Only 250 histories fit
32,768 input tokens, with NumPy/pandas increasing to 82% of that retained subset.
None fit 16,384. Eight prior native-mask cases match exact token hashes. Two new
statistics tests pass; the core suite has 127 passes and 15 explicit skips.
Evidence: `evidence/data/context-census-001`; details and mathematical target
accounting are in `docs/33-public-data-intake.md`. Next implement and replay-test
a shared runtime/training context policy before admission; do not silently
truncate or count these raw input tokens toward approved candidate budgets.
GPU use remains unnecessary for this local data-policy work.

### Competition context configuration and summarizer audit

The local repair driver left compaction and cache disabled, unlike the acquired
competition README. It now supplies documented settings using pinned ADK 1.36.1
and records them in attempt receipts. Deployment bundle 006 includes the helper
and passes archive verification and isolated CLI import. The actual-ADK offline
probe reproduces omission of structured tool calls/results from summary input.
This is a diagnostic finding, not a successful memory mechanism. Core suite:
127 passed, 15 skipped. No GPU or real summarizer call was made.

Revised next step: reproduce the pinned runner's selection/trigger behavior and
official request stream before designing context transformations. A custom
compactor needs a supported competition deployment path. Future admitted data
must retain actual summary/continuation pairs and evaluate observation recovery.
Historical repair evidence does not establish compaction compatibility.
Evidence: `evidence/p1/harness-compaction-002`.

### Runner-level compaction reproduction

Ran three actual-ADK offline cases with six local tool calls inside one user
invocation. Synthetic prompt usage 14,335 produced no compaction; 14,336 produced
five summaries and excluded the oldest tool observation from later agent input.
The disabled control retained it. Original tool events remain in session storage.
The runner compacts before model calls as well as post-invocation; the earlier
docstring-based post-invocation description was incomplete and is corrected.
Source bytes match pinned ADK. These are synthetic-model integration tests, not
GPU or learned-agent performance tests. Evidence: `evidence/p1/compaction-runner-002`.
Next qualify recovery and capture actual summaries during a bounded future
GPU session; local context/data work remains available before that session.

### Supported source-observation recovery candidate

Added a separate untrained declarative candidate with an ADK source-observation
skill. It saves actual source excerpts outside the repository and checks whole-file
freshness before recall. Five focused tests pass. The pinned compiler and actual
ADK script wrapper pass snapshot/recall/staleness checks across separate processes.
This does not yet qualify the production sandbox or demonstrate model adoption
and repair gains. Compare against the preserved baseline after executor and
compaction-recovery integration checks; account for added tool/token costs.

The compiler version guard detected older packages in the general environment.
Pinned versions now run in an isolated overlay; the earlier compaction config
check was repeated under the correct harness and still passes (probe 003).
Evidence: `evidence/p1/observation-skill-001` and `harness-compaction-003`.

### Actual Docker skill execution and patch isolation

The recovery candidate compiles against real bound tools and executes through
the released sandbox executor in a pinned local Linux container with networking
disabled and no host mounts. Exact recall survives separate calls; actual source
edits invalidate records. The workspace stays clean until the intended source
edit, and official patch extraction includes only that edit. The owned container
was removed and cleanup verified. Evidence: `evidence/p1/observation-sandbox-001`.
No GPU or model was used. Next integrate deterministic compaction/recovery and
cost accounting before testing whether Gemma uses this capability effectively.

### Compiled candidate through runner compaction and real skill dispatch

Integrated actual ADK runner/compaction, compiled candidate, bound tools and
Docker executor in two controlled cases. A scripted summary retaining the handle
permits exact source recovery after the original observation leaves context;
dropping the handle prevents recovery. The source marker is fresh, and recall
uses only information present in the current model request. Snapshot/recall each
consume one harness tool call; summary requests are reported separately.
Evidence: `evidence/p1/observation-recovery-001`. No model quality, real token
cost, learned retention rate or training-data claim follows. Both containers
were removed. Next learned-agent comparison needs an explicitly bounded GPU
session; local source-data qualification and ingestion remain open in parallel.

### Actual Gemma paired development run

Used the still-running H100 within the existing approved four-hour session.
The driver now selects either immutable candidate and records its identity;
both use the same checkpoint, 40-turn/40-tool/10-minute budgets and documented
compaction. Deadline enforcement reserves 30 seconds for cleanup. Deployment
bundle 007 includes both candidates and manifests. Core suite: 132 passed,
15 skipped. Neither candidate was modified between attempts.

On repeated development task `requests_6589`, both produced source patches and
passed the paired compatible local grading. The base hit the turn limit despite
submitting; the observation candidate finished without an agent error but used
no skill tools. Captured total tokens, including summary requests, were 384,697
versus 312,008. This single ordered pair does not establish an efficiency gain,
and cannot attribute any difference to unused observation recovery. Do not adopt
or train toward the candidate on this evidence alone. Next select an independent
development scenario where loss/recovery is actually exercised, with a fixed
comparison protocol and no oracle leakage.

Initial grading used the wrong original container image and failed the source
origin measurement before tests. Both failures remain in grade-001; grade-002
uses the previously qualified compatibility image and passes source checks.
Results are local diagnostics with a source-path override and network-enabled
test environment, not hidden-grader parity. Evidence:
`evidence/p1/observation-comparison-live-001` and `observation-comparison-grade-002`.
Server ran 441.32 seconds including startup, shut down cleanly, and GPU memory
returned to zero. Temporary SSH access was revoked and the tunnel closed.

### Corpus tool contracts and success-label qualification

Audited argument shapes for all 2,500 acquired histories. Found 1,874 root-directory
views, 231 shell-input calls across 122 histories, 468 explicit shell timeouts,
six editor undos and 298 open-ended view ranges. These require explicit semantic
handling; ordinary tool renaming is not a valid native-runtime conversion.
The linked paper also retains unresolved Hero trajectories, and its reported
composition differs from the pinned card. No row-level success is inferred.
Evidence: `evidence/data/source-tool-contracts-001`. Next join source tasks and
base-state metadata, then replay or regenerate with native tools before admission.

### Source task metadata recovered

Acquired and checksum-verified all 4,578 R2E-Gym subset tasks (~944 MB compressed).
All 2,500 acquired Hero trajectories join to a source task. Added a strict metadata
projection that excludes oracle content and distinguishes unresolved first-parent
references from actual base commit hashes. The initial full-hash assumption was
rejected by real data and corrected; no environment or training admission follows
from the join alone. Core suite: 137 passed, 15 skipped.

Next: resolve base references and image digests, audit oracle isolation in actual
source environments, then qualify native tool replay/regeneration. No GPU run is
needed for the metadata stage. Evidence: `evidence/data/source-task-join-001`.

### Source environment resolution and isolation finding

Completed R2 readback verification for all eight source task shards (~944 MB).
Resolved immutable Linux/amd64 image digests and first-parent commits for a fixed
eight-repository sample. Local inspection of the first sample (Pyramid) confirmed
the intended base commit but also accessible solution Git objects and generated
grading tests. The inspection container was removed; no GPU work was used.
Core suite: 140 passed, 15 skipped.

Next implement a sanitized agent snapshot with an independent evaluator, verify
that intended source/dependencies still execute, and then qualify native replay.
Do not promote these trajectories based on metadata joins or publisher labels.
Evidence: `source-environment-resolution-001`, `source-image-probe-001`.

### Sanitized source snapshot and reference-control qualification

For the fixed Pyramid task, built a fresh one-commit workspace that preserves
the exact original Git tree (891 paths) while removing known grading artifacts
and original solution history from the agent-visible filesystem. Original versus
sanitized repository tests match on all 2,470 cases: 2,433 passed/37 failed each.
Shared failures remain unresolved; this is preservation evidence, not a green
repository or general isolation guarantee.

Separate evaluator controls reveal a lossy upstream test-name convention. Added
an all-members comparison that preserves full case identities and the publisher's
expected failures. The reference matches all 994 actual cases; the buggy base has
19 mismatches. No learned agent ran and no trajectory was admitted to training.
Next connect native tools and patch export to this sanitized/evaluator split,
then expand qualification across the preselected repositories. Continue locally.

### Native source workspace and patch transfer

Added a reusable snapshot-to-native-workspace adapter with source identity checks
and strict handling of the known installer leftover. Qualified actual native
command/read/edit/submit operations, empty baseline submission, byte-identical
patch application in a separate evaluator, and unchanged results across all 994
evaluator cases. This used an explicit random-comment transport fixture with no
model invocation, so it earns no repair credit and is excluded from training.

Evidence: `evidence/data/native-source-transport-006`, with earlier integration
failures retained. Next expose the sanitized/evaluator split through a repeatable
task runner, including task-prompt provenance and runtime budgets, before any
model-driven rollout or corpus admission. Broader repository qualification and
the training campaign remain open; local work does not require a running Pod.

### External task packaging and rollout-driver dry-run

Prepared a manifest-backed task package with disjoint model-visible and evaluator
projections, including an opaque task ID and source issue hash verification.
Added a bounded ADK source-task driver and verified its dry-run using pinned SDKs.
Its model execution path remains unqualified; no GPU restart is needed yet.
The core suite has 148 passed and 15 skipped. Next exercise its actual lifecycle
with an explicit offline fixture and connect independent patch grading.
See `34-source-task-runtime.md` for artifacts, scope and remaining gates.

### Actual offline source-runner lifecycle

Ran five scripted fixtures through the actual new ADK/Docker execution path:
success, exception after submission, asynchronous model timeout, 40-turn limit,
and 42 requested tools against a 40-call budget. Verified exact patch retention,
40 successful/2 rejected batched calls, model-input metadata separation, and
cleanup of all five containers. No model quality or training credit is assigned.
Evidence: `source-runner-lifecycle-001`, `source-runner-lifecycle-audit-001`.
Next: slow-tool cancellation, cleanup-failure receipts, independent grading of
saved outputs, and real HTTP behavior. GPU execution is still unnecessary.

### Independent saved-patch grading and bounded native commands

Added manifest/identity-checked grading of saved runner patches in a separate
evaluator. The scripted file-addition fixture remains unsolved (19 mismatches),
and tampered/unsubmitted/wrong-task inputs reject before evaluator execution.
Verified native slow-command timeout with no delayed file write after its
scheduled time. Cleanup failures now retain explicit uncertainty in receipts;
controlled API-failure tests and a live successful cleanup pass.
Core suite: 151 passed, 15 skipped. No model inference or GPU work occurred.
Next qualify the real HTTP client path locally, then broaden task qualification
and corpus preparation before requesting a GPU session.

### Production-client loopback HTTP qualification

Exercised the real registered HTTP client against explicit local scripted
responses. Native tool calls/results round-trip and produce a saved patch;
503 fails after one request without retries. Both paths clean up their servers
and containers. Independent grading preserves the fixture label and reports
the expected unsolved baseline, not model success. No GPU was used.
Evidence: `source-http-client-audit-001`. Next expand source data/environment
coverage and admission; Gemma execution and training remain separate gates.

### Source contract census update

The complete pinned R2E source census now covers 4,578 tasks / ten repository
basenames. One Orange3 contract has a blank test identity; 2,203 otherwise valid
contracts include expected failures/errors. All remain unapproved for training
until runtime controls establish a reproducible repair signal. Expand repository
qualification before scaling native rollouts. See `34-source-task-runtime.md`
and `evidence/data/source-expectation-corpus-001`. Pod remains stopped; this work
and the 170-test local suite require no GPU.

### Tornado runtime qualification update

Two independent base/reference runs now qualify one Tornado evaluator task:
29/30 passes at the buggy base, 30/30 at the reference, with exact publisher
expectation agreement only for the reference. Both repeats match, and source
integrity and cleanup checks passed. This expands evaluator coverage beyond
Pyramid; source snapshot isolation and native trajectory execution remain next.
No training examples were admitted and no Pod restart was needed.

### Tornado workspace update

The exact-tree sanitized Tornado snapshot now passes native import/read/empty-
submission checks. All 28 original gen_test cases give identical passing outcomes
before/after sanitization. The shared workspace probe also passes on Pyramid.
Next: native patch transfer and teacher trajectory replay, with independent
Tornado grading. Preserve the distinction between 28 original repository tests
and 30 generated evaluator tests. GPU remains unnecessary for these checks.

### First independently graded teacher replay

One pinned Tornado Hero trace now executes through adapted native tools and its
saved patch passes all 30 independent grading cases. The replay has 58 charged
calls and exceeds the 40-call competition profile. It is explicitly not admitted
to training. Next qualify fresh-observation trajectory construction and context/
mask limits, then expand replay coverage without treating this single success as
population-level evidence. All work was local; no GPU or new model generation.

### Native training representation update

The twice-graded Tornado replay now has a fresh-observation, action-only native
history: 59 exchanges, 28,933 input tokens, 6,764 supervised targets, exact native
Gemma token/mask checks passing with nine tool schemas and no truncation.
This is diagnostic data, not admitted training data: the reconstructed prompt
and 58-call trajectory require explicit policy and fidelity checks. Next expand
budget-compatible source replay coverage and qualify training memory using
measured sequence lengths before requesting another GPU session.

### Corpus-scale replay selection

The 2,500-trace census yields 417 histories within the estimated 40-call budget,
including 136 joint source-context/call-budget candidates without known adapter
flags. A deterministic eight-repository shortlist has pinned image/revision
metadata ready for qualification. Prioritize these new candidates before more
long-trace demonstrations. Use fresh native lengths and independently graded
patches for admission; source metadata is only a replay-cost screen. Local suite:
180 tests run, 165 passed, 15 skipped.

### Budget-compatible replay milestone

The selected shorter Tornado trace now replays in 33 calls under the enforced
40-call ceiling, passes all 39 independent grading cases, and renders into
14,884 native input tokens with 3,890 supervised targets. Source build/replay
configuration is reusable and validated. This is evidence for one teacher repair,
not trained Gemma performance or corpus admission. Next extend the same pathway
to the selected Pyramid candidate, then other repositories, while maintaining
rights/contamination and fresh-observation admission gates. No Pod needed yet.

### Cross-repository budget-compatible replay

The selected Pyramid trace now replays in 29 calls, produces a patch matching
all 835 independent case expectations (80 remain expected failures), and renders
into 18,924 input / 3,868 supervised tokens without truncation. Together with
Tornado, two repositories now have budget-compatible graded teacher histories.
Shared replay/grading entry points replace task-specific implementation names;
compatibility wrappers preserve earlier commands. Next expand to additional
selected repositories and resolve admission gates; these two traces do not form
an abundant training corpus or prove Gemma performance. No GPU was used.

### Admission evidence and source-license correction

Live rules review confirms conditional external-data/model allowance. Current
GitHub repository-ID/fork-network metadata shows no overlap between the eight
source repositories and four reserved official repositories. This is a limited
identity screen, not semantic contamination clearance. Exact source notices
revealed that Pyramid's MIT row label does not describe its mixed-license tree;
keep it quarantined pending file-level review. Preserve Tornado's Apache notice
and all transformation attribution. See `35-data-rights-and-evaluation-isolation.md`.
Do not scale acquisition based on unverified publisher license labels alone.

### P1 local follow-up — 2026-10-09: replay source provenance

- Verified the admission-review R2 upload: 23 files, 116,081 bytes, remote hash
  readback complete (`admission-review-publish-001`).
- Exported the short Pyramid replay's three directly observed source files from
  its immutable snapshot; matched the recorded reads and final edited read with
  explicit terminal-newline normalization. Accounted for all 19 shell outputs.
- Narrowed the rights finding: this trace does not show rendered docs bodies,
  but its source is not MIT-only; dependency warning snippets and derived
  redistribution notices still require coverage. Kept training approval false.
- Recorded a concrete quality hazard: a teacher-written test prints failure while
  exiting zero. Independent grading, not exit status or success prose, controls
  outcome labels. No GPU work was started; P1 remains incomplete.

### P1 local follow-up — linked replay preflight

Added `assess_replay_admission.py` and its consistency-checking module. Saved
patches, grades, native history, event mappings, schemas and token audit now have
an executable cross-artifact check. Reconstructed histories and charged-call
counts are independently compared; no training approval is issued by this tool.
The two short traces pass these mechanical checks. The long Tornado trace fails
both the 40-call limit and the 32,768 context limit with an 8,192 output reserve.
Local suite: 190 run, 175 passed, 15 skipped. Rights/split/runtime gates remain;
no Pod restart or training campaign was performed.

### P1 local follow-up — full pinned trajectory acquisition

Expanded acquisition from one to all 14 SWE-Hero shards at the same immutable
revision. Publisher size and SHA-256 checks passed. The full metadata census has
34,269 trajectories, 1,695 repository names and 11,766 repository–issue pairs,
with no duplicate trajectory IDs. It found 73 encode/httpx rows overlapping a
reserved repository; these are explicitly flagged for exclusion. No trajectory
or patch bodies were read by the census. See `36-full-trajectory-corpus-intake.md`.

This materially broadens the raw supply, but 22,503 trajectories repeat existing
issues, and 24,048 rows come from source datasets outside the currently qualified
R2E task adapter. Do not extrapolate the two successful native replay examples to
this corpus. Raw R2 transfers are underway; use each verified publish receipt
before claiming a shard is stored remotely. Training admission remains false.

### P1 local follow-up — verified R2 corpus and expanded task join

All 14 pinned raw shard bundles are now verified in R2 (2,402,170,043 bytes,
including cards/metadata), with manifest-linked receipts. A separate 151,559,597
byte shard restore passed destination checksum validation. The full census bundle
is also remotely verified. No GPU was used.

Expanded the task join to consume the verified full metadata index. Exclusion
runs before source selection: 73 reserved-repository rows excluded, 10,221 R2E
traces joined to 3,442 unique tasks, zero unmatched R2E traces, 23,975 other-source
rows left outside this adapter. This joins identities only; broad environment,
rights, native token/mask and replay admission remain incomplete. Local suite:
194 run, 178 passed, 16 skipped; separate PyArrow census integration passed.

### P1 local follow-up — SWE-rebench filtered source join

Implemented a metadata-only adapter for the largest remaining trajectory source.
The pinned 6,542-task filtered table joins 17,798 traces to 6,125 tasks across
1,686 repositories. All 73 reserved-repository rows are excluded first. There
are 318 unmatched traces across 111 tasks; investigate the larger source release
rather than guessing mappings. Nine matched rows lack publisher license terms,
and 103 declare ZPL 2.1; rights remain unresolved despite simplified trajectory
labels. Image strings exist for all matched rows but are not digest-resolved or
runtime-qualified. See `37-swe-rebench-source-adapter.md`.

Validation for this adapter: 198 tests run, 182 passed, 16 skipped. The raw
filtered table is remotely checksum-verified in R2. Missing terms, unmatched
identities, unresolved images and evaluator qualification remain explicit gates;
no training or GPU work was performed.

### P1 local follow-up — full SWE-rebench task identity coverage

Acquired both full-release task shards at the pinned revision and extended the
join command with an explicit source split. All 18,116 nonreserved SWE-rebench
traces now match 6,236 tasks across 1,687 repositories. The previously unresolved
318 traces map to 111 tasks without image references: do not substitute guessed
images. Filtered results reproduce exactly, and all common task metadata agrees.
Source shard hashes and row positions are retained for controlled retrieval.
Suite: 198 run, 182 passed, 16 skipped. No GPU work or training approval.

### P1 local follow-up — SWE-rebench images

Pinned all eight images in a reproducible cross-repository metadata sample. Pulled
only the smallest (1.27 GB compressed) locally and inspected it in a read-only,
networkless container. Its Git HEAD matches the task base and tracked files are
clean, but 624 commits and extra root files remain accessible. This is not yet
an isolated agent image. Next: source sanitization and independent evaluator
controls. The probe container was removed; no task tests, agent or GPU ran.
Suite: 200 run, 184 passed, 16 skipped. See the source-adapter document for scope.

### P1 local follow-up — SWE-rebench source snapshot

Built and independently verified a parentless exact-tree snapshot for the first
SWE-rebench image: 30 files/290,019 bytes preserved; old base/head/merge commits
inaccessible via Git; root issue/env artifacts removed. An initial first-parent
assumption failed and was retained as evidence. Explicit ancestor validation now
supports multi-commit SWE-rebench PRs; R2E retains its strict first-parent default.
Task evaluator and runtime compatibility remain unverified. Docker lower layers
retain original bytes and must not be agent-accessible. Latest suite: 204 run,
188 passed, 16 skipped. Improved file-mutation diagnostics without weakening the
guard; intermittent source-metadata changes remain an open local reliability issue.


### P1 evaluator qualification update — 2026-10-09

Biolink task 172 base/reference controls both stop in fixture setup (93/93
errors each); no test assertions execute. Captured and hash-pinned the two
Biolink 4.2.1 resources required by the fixture. Offline replay and paired
assertion-level verification remain outstanding; see document 37. New
resource/diagnosis bundles still require R2 publication. Pod remains stopped.


### P1 offline evaluator controls — 2026-10-09

Biolink task 172 now reaches all assertions offline: base 92/93 passing and
reference 93/93 passing, with the intended failure-to-pass transition. Exact
resource bodies are hash-pinned; no assertions changed. Full suite: 210 tests,
22 skipped; six adapter tests passed separately. Continue with source-harness
identity mapping and sanitized-image parity before admitting trajectories.
Pod remains stopped; this is evaluator evidence, not model improvement.


### P1 sanitized source controls — 2026-10-09

Confirmed task-172 evaluator equivalence between original and sanitized images:
all 93 full identities have identical outcomes; all 82 publisher expectation
groups match without suppressing collisions. Added strict paired-control
validation and five adversarial tests. Suite: 215 tests, 193 passed, 22 skipped.
Continue source trajectory integration and rights/admission work; no model
performance claim or training readiness follows. Pod remains stopped.


### P1 candidate grading path — 2026-10-09

Task-172 patch grader now rejects an empty repair, accepts the known reference
repair, and rejects added test files before execution. This establishes grader
behavior only. Full suite: 217 tests, 195 passed, 22 skipped. Located three
source trajectories for provenance/action review and subsequent native replay.
Runpod remains unnecessary and stopped; training admission remains pending.


### P1 teacher data screening — 2026-10-09

Verified all three task-172 trajectories. Their 55/56/49 executable actions
exceed the 40-call limit. Editor-only diagnostic projections distinguish one
failing repair and one passing repair; the second trace needs state-divergence
analysis. These are not full replays or training-admitted examples. Prioritize
third-trace native replay, followed by independently validated shorter data.
All work remains local; no Pod restart is needed.


### P1 native Biolink replay integration — pending runtime result

Implemented task-environment selection, pinned response staging, and explicit
source-shard loading for native replay. Suite: 219 tests, 197 passed, 22 skipped.
One local replay process is live but waiting on dependency reads before
container startup (session 46435). Preserve and poll it; no duplicate run.
No new training admission, replay completion, or GPU requirement is claimed.


### P1 source-state discrepancy audit — 2026-10-09

Isolated the second teacher trace's first replacement mismatch to one line's
four-space indentation difference. Preserve source-state uncertainty and do
not force the trace to apply. The original native replay process remains live
in dependency loading; continue polling session 46435 before any retry.


### P1 corpus-wide budget screening — 2026-10-09

Completed static screening of all 34,196 non-reserved traces (73 excluded).
4,507 fit estimated 40-call cost without currently detected adapter flags,
covering 2,753 distinct issues across 913 repositories. This expands the
replay-candidate pool; it does not admit training data or prove token sufficiency.
The original Biolink replay session 46435 remains pending dependency imports.
Continue that exact process, then prioritize additional candidates from the
corpus-wide pool with issue-level isolation and independently graded outcomes.


### P1 budget-first environment cohort — 2026-10-09

Bound 2,621 image-backed, statically budget-fit SWE-rebench trajectories to
1,575 issues / 902 repositories. Resolved eight deterministic image identities
from this cohort without downloading layers. Prefer this pool for additional
replays; it remains unqualified for training. Existing Biolink replay session
46435 continues, with no duplicate workload or Runpod restart.


### P1 replay retry after verified terminal failure

Biolink replay-001 ended during resource hash validation; its container cleanup
is verified. Both resources subsequently matched stable pinned hashes. Fresh
replay-002 (session 88472) is now running; poll it before any further retry.
Budget-cohort evidence R2 publication verified. Runpod remains stopped.


### P1 native SWE-rebench success; admission still pending

Rebuilt a self-contained native harness runtime to avoid workspace dependency
read stalls; core pins and shared dependency versions retained, import-origin
and dependency checks passed. Native Biolink replay-003 completed with fresh
observations and a submitted patch that independently matches all 93 expected
test outcomes. Both containers cleaned up. Its 48 charged calls exceed the
40-call limit, so this remains compatibility evidence, not admitted training
data or model performance. Next: audit native masks/context and accelerate
qualification of budget-fit corpus candidates. Runpod remains stopped.


### P1 native context and mask audit — 2026-10-09

Linked Biolink replay, exact patch grading, reconstructed native history, and
pinned-tokenizer masks. History: 26,118 input / 5,530 supervised tokens; input
plus reserve 34,310 exceeds 32,768, and 48 calls exceeds 40. Admission checker
correctly rejects both constraints. Extended grading-backend identity checks;
full rerun 221 tests, 199 passed, 22 skipped. Keep this as compatibility evidence
and pursue budget-fit corpus candidates; no GPU training is authorized by these
results and Runpod remains stopped.


### P1 budget-fit task triage — 2026-10-09

Completed provenance-bound issue/environment extraction for eight budget-fit
SWE-rebench tasks without reading solution/test patches. Reviewed test breadth,
issue type and estimated call counts; prioritize nodebook AST repair (35 calls,
1 new regression / 18 preserved tests) for the next environment qualification,
then an encoding case. Counts are publisher declarations, not execution results.
Do not equate static call fit with native token fit or corpus admission. Keep the
full data goal unchanged; next work is local snapshot/evaluator qualification.
Runpod remains stopped. Detailed comparison: document 37.


### P1 second SWE-rebench evaluator qualification — 2026-10-09

Nodebook original-image paired controls reproduce 19/19 expected transitions
(18 base passes to 19 reference passes). Generalized evaluator input extraction
and explicit execution profiles; Biolink regression still matches 93/93
transitions. Full local suite: 201 passed, 22 skipped after metadata-guard
failures were retained and stable reruns completed. No GPU used. Next qualify
sanitized Nodebook source and replay/context, then expand corpus admission;
original-image tests alone do not approve a training example.


### P1 budget-fit native replay — 2026-10-09

Nodebook second snapshot preserves its exact tracked tree and reproduces all
19 original-image test transitions. First replay safely rejected a retained
untracked issue file; declared cleanup was corrected and a new snapshot verified.
The subsequent native teacher replay completed within 35/40 charged tool calls,
submitted a hash-bound patch and cleaned up. Patch grading and native context
admission remain pending. Added reusable snapshot verification and exact teacher
selection; full suite 202 passed / 22 skipped. Runpod remains stopped.


### P1 Nodebook mechanical candidate qualification — 2026-10-09

Independent replay-patch grade matches 19/19 expected outcomes; empty-patch and
unauthorized-file negative controls behave correctly. Pinned token audit yields
17,353 input / 4,183 supervised tokens; with 8,192 reserve, context is 25,545 of
32,768. Tool budget is 35/40. Linked mechanical admission passes. This remains
unapproved training data pending rights, frozen split/duplicate checks, remaining
source qualification and GPU runtime validation. Full suite 204 passed / 22
skipped, followed by focused allowance checks and regrading. Keep Runpod stopped.
Next advance corpus rights/isolation and assembly using this linked evidence.


### P1 provenance and trainable candidate export — 2026-10-09

Captured Nodebook tracked source and identified dependency notices; compared all
four direct-read spans, retaining one truncated tool observation. Added an
attribution record. Expanded identity isolation to the eight selected source
repositories and four reserved repositories; no current declared fork-network
or canonical-ID overlap. Semantic duplication and frozen splits remain open.
Exported actual token/label arrays, matching prior audit hashes and collator
counts, into quarantine for later corpus assembly. The GPU worker remains a
synthetic fixture qualifier, not yet a production corpus trainer. Next implement
corpus isolation/assembly and the real-data training path under explicit gates.
Runpod remains stopped.


### P1 real-data corpus loader and deployment preflight — 2026-10-09

Implemented portable quarantine corpus assembly and a hash-bound loader. It
validates token/audit identities, exact label/count accounting, aggregate bytes,
no truncation, duplicate sequences and declared cross-split families. Separate
content-bound rights/split/runtime receipts are required for training loads;
these are consistency gates, not proofs of arbitrary receipt authenticity.
Assembled one real Nodebook candidate (17,353 input / 4,183 supervised targets).
Staged CLI inspection passes outside the repository, and training-purpose access
is denied for the real quarantine corpus. Full suite: 212 passed, 22 skipped.
The first source-bundle staging attempt rejected filesystem metadata drift on
p1-training-pilot.json; stable rereads and a fresh bundle succeeded without
weakening inventory guards. The GPU qualification worker is still fixture-based.
Next: deterministic bounded real-data batching, token-weighted optimizer loop
and resumable corpus state. Details and current limits are in document 38.
# Corpus optimization progress — 2026-10-09

Implemented whole-example deterministic schedules, exact supervised-target
accounting, verified data-cursor resume, and single-device token-weighted
gradient accumulation. Eight focused CPU tests passed, including bitwise
deterministic optimizer/cursor resume. A reduced actual Gemma backend test passed
loss, gradient and AdamW batch-equivalence checks. Repository suite: 243 tests,
216 passed, 27 skipped. Four staged CLI imports passed. See document 38 and
`evidence/p1/corpus-optimization-001` for scope and tolerances.

No Pod restart or training campaign occurred. The real candidate remains
quarantined. Next work is bounded corpus iteration and complete worker/checkpoint
integration, followed by admitted data expansion and real-sequence GPU memory
qualification. No full-scale readiness, accuracy gain or error-free guarantee is
established by these CPU checks.
# Indexed corpus progress — 2026-10-09

Added an indexed corpus reader that validates all examples and split/admission
invariants before exposing metadata, then rehashes token files on demand.
The schedule CLI now avoids retaining all token arrays. Real Nodebook fetches
and schedule/update files match the materialized implementation exactly.
Twelve corpus tests pass; the full suite has 247 tests, 220 passed and 27 skipped.
Four staged CLI imports pass. No GPU or optimizer execution was performed.

This bounds retained token data to individual examples, not total process RSS:
manifest metadata and per-example JSON decoding still consume memory. Next:
connect indexed fetching to bounded training microbatches and complete resume
checkpoints, then qualify full-model GPU behavior. Data remains quarantined.
# Streamed optimizer integration — 2026-10-09

Connected indexed training data to supervised-token-weighted accumulation with
one complete example resident at a time. Exact metadata/target checks and
end-of-stream validation precede the optimizer step. Synthetic admission fixtures
verify numerical equivalence and error paths; weak-reference checks verify tensor
release before fetching the next microbatch. Twenty-four focused tests passed,
including reduced Gemma; four stream tests passed after the tensor-lifetime test
was added. The repository run had 250 tests, 220 passed and 30 skipped.

The corpus-update bridge is implemented, but the full worker/checkpoint/RNG
integration remains open. Actual data remains quarantined, and no GPU was used.
Full-model long-sequence memory and BF16/LoRA behavior require a later authorized
GPU session after local integration is ready. See document 38 for limitations.
# Stochastic resume progress — 2026-10-09

Implemented global Python/NumPy/Torch RNG capture and validated restoration with
runtime/determinism settings bound to the payload. CPU dropout training resumes
with exact loss, weight and AdamW moment agreement after model/optimizer/cursor
reconstruction. Eleven focused tests and four staged CLI imports pass. No GPU
used. CUDA RNG recovery remains untested; custom generators and worker processes
are out of scope for this helper.

Next: atomically publish and restore a complete checkpoint from disk, connect
recovery to the training worker, finish data admission/expansion and then qualify
the real full-model training path on an explicitly restarted Pod. P1 is ongoing.
# Durable storage progress — 2026-10-09

Implemented no-overwrite atomic checkpoint publication, serialized-byte ceilings,
fsync and same-descriptor hash-checked weights-only loading. A fresh subprocess
restored synthetic model/AdamW/RNG state and reproduced the next dropout update
exactly. Failure tests cover partial/tampered files, write exceptions, over-budget
serialization, symlinks and FIFOs. Fifteen focused tests pass; staged CLI checks
pass. The prior full suite ran 257 tests with 220 passed and 37 skipped.

Next: bind adapter/frozen-base identity, corpus, schedule/cursor and configuration
into the complete checkpoint contract, then wire worker save/resume. Actual
network-volume durability, GPU behavior and real data training remain unqualified.
The Pod was not restarted; the full P1 objective remains active.
# Bound adapter recovery — 2026-10-09

Implemented adapter-only checkpoint binding to base/corpus/config/schedule
identities, frozen-state fingerprints, module modes, exact data cursor, AdamW
and RNG state. CPU disk save/resume reproduces the remaining dropout schedule
exactly. Incompatible identities, tensor/state/count/mode changes are rejected
before parameter application. Eighteen focused tests pass; the repository suite
ran 261 tests, 220 passed and 41 skipped. Four staged CLI imports pass.

Next: connect these contracts into the actual training worker with finite run
budgets, checkpoint publication and resume. Qualify PEFT/full-model restore,
frozen-state scan cost, long-sequence memory and real data on GPU only after
local integration and admission work are ready. No Pod restart or real training.
# Budgeted training session — 2026-10-09

Integrated indexed corpus fetching, deterministic schedules, streamed optimizer
updates and bound checkpoint/resume into a reusable session loop. Update/time/
sequence/checkpoint budgets are explicit. The committed cursor advances only
after durable checkpoint publication. Five session tests cover exact resumed
execution, preserved prior checkpoints after disk failure, input rejection and
budget stops. Twenty-three focused tests pass; the repository suite ran 266 tests
with 220 passed and 46 skipped. Four staged CLI import checks pass.

Next: connect this loop to the full Gemma/PEFT worker, pinned runtime checks,
volume verification, durable reports and hard deadline supervision. Real data
remains quarantined; data expansion/admission and GPU qualification remain open.
No Pod restart and no real-data optimization occurred.
# Full corpus worker wiring — 2026-10-09

Connected CPU admission/config preflight, exact Gemma LoRA attachment, the
budgeted training loop, bound checkpoint resume, pinned runtime/volume/model
checks and deadline supervision in new corpus-worker entrypoints. Added a
proposed one-update qualification config. The real quarantined candidate is
correctly rejected before loading a model. No Pod restart or real training.

Reduced Gemma + PEFT update/restore passes, along with fourteen focused tests.
Repository suite: 271 tests, 224 passed, 47 skipped. Six staged CLI imports pass.
Full 31B GPU execution, supervisor end-to-end behavior with that worker,
long-sequence memory, throughput and resume remain unverified. Next: review and
test worker orchestration/error paths, complete corpus admission/expansion, and
prepare a concrete GPU qualification only after those prerequisites are ready.
# Supervisor evidence reconciliation — 2026-10-09

Added independent schedule/checkpoint/metric/budget reconciliation before the
supervisor accepts a session. Resume bindings are checked before worker launch;
worker execution identity must match the supervisor's own calculation. Actual
locally produced Torch checkpoints pass reconciliation, while altered reports,
payloads, paths, bytes and unsupported stop reasons fail. Thirteen focused tests
pass; full suite has 276 tests, 229 passed and 47 skipped. Six CLI imports pass.

GPU execution remains pending. Next priorities are full worker failure-path
coverage and data admission/expansion; CPU evidence is not a full-model readiness
or repair-performance claim. The Pod remains unused.
# Data expansion: Mailmerge controls — 2026-10-09

Downloaded and probed the pinned Mailmerge-135 environment. The base/reference
controls reproduce all 27 publisher transitions (26 versus 27 passing tests).
The selected teacher has 37 shell/editor calls before native adaptation. The
image exposes 906 reachable commits, so source isolation is mandatory before
replay. No training approval or real optimizer update is claimed.

**Mailmerge follow-up:** isolated exact-tree snapshot verified, 37-call native
replay completed, and its patch matched all 27 reference tests. Untruncated
history has 30,191 inputs / 7,415 targets; input plus the 8,192 output reserve
exceeds the 32,768 context budget by 5,615, so admission remains denied. Source
and selected dependency notices are retained. The runtime path aliases were
verified and capture containment corrected. Regression: 277 tests, 230 passed,
47 skipped. Next data work should evaluate the alternate trace or other tasks
without weakening the declared context criterion.

Next: bind the public solution commit, build/verify an exact-tree isolated source
snapshot, replay and grade the selected trace, then evaluate native context length
and rights/split admission. The Pod remains stopped; this work uses local CPU.


### Mailmerge alternate trace: independent replay and context rejection

Trace `8ac352d1-ec64-4e81-8999-778c27f6739c` was extracted from the pinned
SWE-Hero shard 011, reviewed, and replayed against the same verified offline
snapshot. All 37 charged shell/editor calls completed; the container was removed.
The submitted patch changes only the CSV reader encoding to `utf-8-sig`.
Independent grading matched all 27 reference outcomes, with zero disagreements.
This is teacher replay evidence, not learned Gemma performance.

The untruncated native history has 28,451 input tokens and 7,870 supervised
targets. With the unchanged 8,192-token output reserve, total demand is 36,643:
3,875 above the 32,768 limit. Assessment `swe-rebench-mailmerge-native-admission-002`
rejects training admission. Both reviewed Mailmerge traces fail this policy;
no reserve reduction or truncation was used. Rights and split admission remain
separate, unfinished requirements. No training corpus admission is implied.

This supersedes the earlier next-step note proposing the already completed
Mailmerge snapshot/replay. Next acquisition work should select a different
shorter candidate, preserving independent grading and the same context gate.
The Runpod Pod remains stopped; all this work ran locally.


### Complete source-token cost screening (local, no GPU)

Implemented `scripts/screen_source_token_cost.py` and
`scripts/merge_source_token_screens.py`. The screening binds census, cohort,
reserved repository index, intake receipts, source shards and exact model
tokenizer bytes before deserializing selected histories. All 14 shards now
cover exactly 2,621 image-present candidates (1,575 tasks, 902 repositories).
The merged result is `evidence/data/source-token-cost-full-001`.

Ranking uses the token count of canonical converted source-message JSON with
no truncation, padding or special tokens. This includes source observations
and reasoning. It is NOT native replay context, a bound on native length, a
quality score, or training admission. No token-fit threshold is inferred from
this proxy. Native replay, independent grading, actual token masking and
context admission remain mandatory. The sample remains cost-selected and
cannot estimate unbiased agent performance.

The eight shortest distinct repositories were bound to task records, their
Linux amd64 image metadata resolved (no layer download), and their issue and
environment records reviewed. Evidence: `source-token-shortlist-001`,
`source-token-images-002`, `source-token-task-review-001`. Shortness alone is
insufficient: dkey and mypy_extensions request version information/changes;
Narwhals requests documentation despite four published fail-to-pass tests,
which warrants inspecting evaluator relevance before use. Other candidates
include optional dataframe mutation, decorator return propagation, logger
optional arguments, debug-expression formatting and empty-file lint behavior.
These are potential bootstrap examples, not evidence of industrial capability.

Five selection tests cover reserved names and flags, linkage substitution,
duplicates and shard boundaries. A real incomplete cohort was rejected before
merge output. The first empty-shard run exposed an Arrow null-type issue;
explicit string typing fixed it, and all empty shards subsequently completed.
A source metadata change on first read stopped another attempt; the failure
was retained and a fresh run passed unchanged byte-identity guards. Final CPU
suite: 282 tests, 258 passed, 24 skipped in the isolated Torch environment.
No CUDA/full-model capability follows from those results.

Next: inspect task/evaluator relevance for a code-behavior candidate, then
qualify its clean-source controls and replay. Expand task diversity and
complexity alongside context feasibility; do not optimize training quality
solely for shortness. The Pod remains stopped; P1 and corpus admission remain
incomplete.


### Task/evaluator alignment requirement and corpus schema v2

The pinned task `narwhals-dev__narwhals-941` fails task-alignment review.
Its request asks for README media links, but the evaluator adds dataframe
column-selection assertions; all four published fail-to-pass cases exercise
that behavior. The reference patch contains both documentation and indexing
changes. Record `evidence/data/task-alignment-narwhals-001/review.json` binds
these inputs and rejects all three corresponding candidates in the screened
cohort. The oracle patches remain evaluator-only. This finding does not
establish a dataset-wide error rate.

Corpus schema v2 supersedes the earlier three-gate admission contract: it
requires `task_alignment`, `rights_and_attribution`, `split_isolation`, and
`runtime_qualification`. Alignment evidence must review the stated behavior,
reference change and evaluator relevance for every included task, including
incidental merge changes and missing test coverage. A green evaluator result
is insufficient. Generic receipt validation enforces content identity and
evidence presence; it does not automatically establish the semantic truth of
a review. No genuine passing alignment receipt has been created yet.

Schema v1 remains readable for inspection but cannot train, even if it carries
legacy passed receipts. New assembly emits v2. The real Nodebook candidate was
rebuilt as `artifacts/data/quarantine/training-corpus-002` and remains quarantine:
17,353 input tokens / 4,183 supervised targets, one example. Its manifest hash
is `f9b731e8af73f3e7597abc6c14dc4aeafaeee8e6cee0ffa94fe2de5b5d87fc5d`.
The schema change alters corpus content identity; schedules and admission
receipts must be regenerated and reviewed, never relabeled from v1.

Actual v1 and v2 candidate training denials are retained in
`evidence/p1/task-alignment-denial-001`. The current worker bundle passed all
six isolated CLI imports in `evidence/p1/task-alignment-source-001`. Final
CPU suite: 285 tests, 261 passed, 24 skipped. Tests include forged alignment
bindings, omitted alignment gates and an otherwise admitted legacy corpus.
These checks establish local enforcement, not semantic review accuracy or
full-model/CUDA qualification. P1 remains active; no GPU was used.

Next: select a substantive code-behavior candidate whose problem statement,
reference patch and tests agree; perform paired controls and native replay.
Continue rights, split and task review before any real admission or training.


### Shortlist alignment review and Datetransform base inspection

Reviewed the seven remaining shortlisted task/reference/test bundles; the
inputs and decisions are in `source-token-alignment-inputs-001` and
`task-alignment-shortlist-001`. Mypy_extensions task 57 is rejected for the
same class of issue/evaluator mismatch: its request is a version update, but
its added evaluator checks NoReturn deprecation. Three cohort traces are
affected. Dkey task 18 is held: its reference queries `VersionInfo('mgen')`
while exposing dkey version information, and its tests only assert attribute
existence. This is insufficient evidence of correct version provenance.

Pydbg, Ignite, flake8-fancy-header, easy-ptvsd and Datetransform have provisional
static alignment, with narrow coverage limits explicitly recorded. None has
received training approval. The findings are from a cost-selected eight-task
shortlist; they cannot estimate a dataset-wide error rate.

Datetransform task 2 was selected for further qualification: optional mutation
is a concrete behavioral contract, with tests for the default copy behavior
and explicit inplace=True. Its pinned image was pulled locally and probed
without running task tests. The image checkout is
`51571c772ad0939dd35f1e9788fbbabfd8117b88`, not the expected
`33b75b1948cad92aa4edf91850887f27562b0632`. Read-only Git inspection confirms
the expected commit exists and has tree
`696e971b020003634b90ffa249380b5bead8fc50`. The only tracked differences
between base and image HEAD are files `=1.0.0` and `=1.16.0`; the image HEAD
commit is titled Environment setup changes. The original full Git history
also contains the solution commits, so it is unsuitable as an agent workspace.

Evidence: `datetransform-probe-001`, `datetransform-base-audit-001`. Both owned
probe containers were removed. No repair score or environment compatibility
claim was produced. Next: derive an explicitly bound baseline at the requested
commit, verify the exact tree, then run base/reference controls and sanitize
solution history before replay. Preserve the original image and all identity
checks; do not reinterpret the setup commit as the official base.

This cycle changed data-quality evidence and candidate selection, not training
code. The Pod remains stopped; P1 is incomplete and no data was admitted.


### Datetransform exact-base normalization and paired controls

Implemented `zenithsync/source_base.py` and
`scripts/prepare_rebench_baseline.py` for disposable evaluator containers whose
image HEAD is an environment setup commit. The build requires a successful
probe bound to the immutable parent image, the observed initial HEAD and clean
tracked source. It performs a non-forced detached checkout, disables checkout
hooks, verifies the target tree, and hashes every tracked file against Git
blobs. Untracked files and solution history deliberately remain; the result
is explicitly not an agent-approved workspace. The parent image is unchanged.

Datetransform's derived baseline is
`sha256:e5c7fa51e8347815c94030d656efecb882773209da57a6c7fd3c708c7fb651cd`.
Readback preserves nine tracked files at commit
`33b75b1948cad92aa4edf91850887f27562b0632`, tree
`696e971b020003634b90ffa249380b5bead8fc50`. Evidence is in
`datetransform-baseline-001`, `datetransform-baseline-readback-001`,
`datetransform-baseline-input-001`, and `datetransform-controls-001`.

Paired evaluator controls import `datetransform.transform` from the checkout
and match all three published transitions by full test identity: base passes
one and fails two, reference passes all three. Test execution did not modify
the tracked diff, and owned control/readback containers were removed. This
qualifies the narrow three-test evaluator behavior, not broad correctness or
agent performance. No teacher replay or trained model ran in this cycle.

New tests cover wrong initial HEAD, tracked edits, checkout-hook suppression,
exact base restoration and preservation of unrelated untracked files. Final
CPU suite: 288 tests, 264 passed, 24 skipped. Runtime code for the normalizer
also executed successfully inside the real Linux baseline build.

Next: bind the solution commit, sanitize reachable history and known oracle
files while preserving the exact tree, independently verify the resulting
workspace, repeat paired controls to check parity, then replay and grade a
selected trajectory. Rights, split and semantic admission remain separate.
No GPU was used; keep the Pod stopped. P1 remains incomplete.


### Datetransform sanitized replay and two-example corpus integration

Bound PR 2 solution head `82085ef8e7f17cce30732a179cf5cf280eaa1754` and merge
`7331185d854f14734a33ee00a84367d33c2aada0` to the captured GitHub response.
Snapshot builds now accept an explicit successful probe of the same pinned
image to normalize a setup HEAD before sanitization. The original strict
base requirement remains the default. Independent verification also checks
that the former setup HEAD is inaccessible.

Datetransform snapshot
`sha256:5f0dad187211379bfa4e913571460b9ab47eb0264263b0d0472a35dced139d0c`
preserves the nine tracked base files and has one parentless commit. Base,
solution, merge and setup commits are inaccessible; declared oracle paths
are absent. This audits the mounted filesystem, not inherited Docker layers.
Paired controls on the snapshot match the qualified baseline exactly: one
base pass and two base failures, three reference passes.

Trace `2bd25bdd-8342-4fb7-99a8-6ef15a2ea5ff` was source-reviewed and replayed
with fresh native observations, 27 charged calls, no executed teacher thoughts
and successful disposable-container cleanup. Its submitted source-only patch
adds `inplace=False` and copies the dataframe when false. Independent grading
matched all three evaluator outcomes. These tests cover a narrow one-row date
example, not general dataframe aliasing correctness or learned model behavior.

The untruncated history contains 14,126 input tokens / 4,574 supervised targets.
Adding the unchanged 8,192 output reserve gives 22,318, leaving 10,450 tokens
under 32,768. `datetransform-native-admission-001` passes mechanical checks
without approving training. Evidence uses the `datetransform-*` directories
for source, snapshot, controls, replay, grade, history, tokens and admission.

Assembled schema-v2 `artifacts/data/quarantine/training-corpus-003`: two real
examples across two tasks/repositories, 31,479 input tokens and 8,757 supervised
targets. Manifest SHA-256:
`5c0fb2f37acf0d2b425f983c5db38316b15f97482231b4641371b4d8baf921ef`.
A seed-7401, one-epoch dry schedule with an 8,192-target per-update ceiling
produces two whole-example updates, zero target overshoot and no repetition.
The real corpus is still rejected for training. Rights, split isolation, task
alignment receipts and runtime admission remain unresolved. This tiny corpus
is pipeline qualification material, not sufficient campaign data.

Final CPU regression suite: 288 tests, 264 passed, 24 skipped; snapshot building,
verification, controls and replay also ran locally in Linux containers. No
GPU was used. Next: rights and complete admission review for these candidates,
continued diverse corpus expansion, then full-model runtime qualification when
local prerequisites justify restarting the Pod. P1 remains incomplete.


### Rights capture compatibility and restored corpus validation

Datetransform source capture preserves all nine tracked files and MIT license
(Copyright 2020 Brandon Schabell). The Python 3.7 metadata path now uses the
installed backport and compatible canonical path-containment checks. Selected
notices were captured for pandas 1.3.5, NumPy 1.21.6, python-dateutil
2.9.0.post0, pytz 2025.2 and six 1.17.0. Installed pytest 7.1.2 has no
discoverable notice. Default capture still rejects this absence; an explicit
inventory option preserves the missing-notice flag without approving rights.
Both initial failures and a fresh default-denial check are retained.

The matching pytest 7.1.2 upstream source archive was downloaded from PyPI,
verified against its published SHA-256, and its LICENSE preserved separately.
This supplements attribution evidence but does not prove installed Conda build
identity or complete all dependency/observation rights review.

The 83-file Datetransform replay archive was independently restored from R2.
The restored two-example corpus validates at the exact original manifest hash;
both the regenerated schedule and update stream match the original bytes.
Counts remain 31,479 input / 8,757 supervised tokens and two dry updates.
Training admission remains false. Evidence: `datetransform-replay-restore-001`,
`training-corpus-restored-inspect-001`, `training-corpus-restored-schedule-001`.

Current readiness is consolidated in document 39 and linked first from README.
The latest CPU suite remains 288 tests, 264 passed, 24 skipped. No GPU was used.
Next: complete attribution and split/admission evidence while expanding corpus
coverage; do not treat two quarantined examples as sufficient campaign data.


### Current repository identity and issue-duplicate audit

Live GitHub metadata resolves Nodebook and Datetransform plus the four reserved
repositories. No canonical-ID or declared fork-network-root overlap was found
(`current-corpus-lineage-001`). Reserved task bodies were not read.

New `audit_issue_duplicates.py` verifies the pinned candidate cohort and task
shards, validates source metadata before reading candidate issue text, and
records exact UTF-8 hashes separately from whitespace-normalized heuristics.
It covered all 1,575 candidate tasks and found two exact duplicate pairs:
Mobly 164/165 and Hidrokit 121/122. Whitespace screening found the same pairs.
Neither pair includes the current two assembled tasks. Source text equality
is a grouping/review signal, not proof of task equivalence; case and Unicode
forms are deliberately not conflated.

`current-corpus-split-review-001` binds the actual corpus, identity audit and
fingerprint evidence to a validated draft grouping using fork-network IDs and
exact issue hashes. No training admission or frozen split was created. This
review does not exclude detached copies, semantic/patch duplication, vendored
source, unknown hidden evaluation data or model-pretraining exposure. It cannot
be interpreted as a dataset-wide independence guarantee.

Four new tests cover exact-versus-whitespace equality, case/Unicode separation,
order independence and duplicate/empty input rejection. The final CPU suite
ran 292 tests: 268 passed, 24 skipped. Next: complete attribution and task
review while expanding the qualified corpus, and resolve the final split before
training. No GPU was used; P1 remains incomplete.


### Native observation audit and direct-source attribution

Added reusable replay observation inventory with exact text/result identities,
root and wrapped command exit codes, explicit truncation flags, and unknown
status when a flag is absent. It validates event ordering and charged-call
counts against the completed replay receipt. It does not equate successful
tool execution or printed test claims with correctness, and does not remove
failed observations from the training history.

Datetransform: 27 charged calls plus submission; 27 ok results and one error
(the empty no-match grep result, exit 1). No explicit truncation is reported;
20 responses have no truncation flag, including response types without file
content. Nodebook: 35 charged calls plus submission; all report ok, but one
source read is explicitly truncated and 31 responses have no truncation flag.
Do not conflate full token serialization with full underlying observations.
Evidence: `datetransform-observation-audit-001`, `nodebook-observation-audit-001`.

All five Datetransform direct read_file observations match preserved base
source or sequential unique edits under the native line rendering. Three
unique edits were checked, including two in a temporary diagnostic script.
The source attribution record and span hashes are in
`datetransform-file-rights-001`. This closes direct-read byte correspondence
for that trace, not arbitrary shell-output rights or semantic equivalence
to the original teacher's observations. Shell diagnostics and conditioning
fidelity remain explicit review obligations. No rights or training admission
was granted.

Six new tests cover missing versus explicit truncation flags, wrapped errors,
ambiguous/boolean exit codes, event ordering and changed observation hashes.
Final CPU suite: 298 tests, 274 passed, 24 skipped. The two-example corpus,
labels and schedules are unchanged; no GPU was used. Next: complete remaining
attribution and admission review, expand corpus coverage, and qualify GPU
execution only after the exact candidate bundle is ready.


### Task alignment coverage cycle — 2026-10-09

Implemented exact task/repository review coverage in corpus admission, with
negative tests for omitted, duplicate, foreign and unresolved reviews. Full CPU
regression: 302 tests, 278 passed, 24 skipped. Worker source bundle and isolated
CLI checks refreshed. Real corpus remains two quarantined examples with 8,757
supervised tokens; no real approval or GPU training occurred. Next: complete
semantic and rights reviews and expand the qualified corpus before GPU use.


### Semantic probe and corpus exclusion cycle — 2026-10-09

Executed base/candidate probes in exact local snapshot containers, no GPU.
Nodebook passes its 19 publisher cases but misses annotation dependencies and
leaks parameter scope in added counterexamples: exclude its trajectory.
Datetransform passes 18 added copy/inplace/time/row-count cases versus 0 on base.
Selection 003 and corpus 004 now contain only Datetransform: 14,126 input and
4,574 supervised tokens, quarantine only. No teacher trajectory was rewritten
to conceal a failure. Next: expand qualification, finish rights/admission and
regenerate the schedule for the final approved corpus. Old schedules are stale.


### Easy-ptvsd evaluator qualification — 2026-10-09

Pinned image matches declared base commit. Original image retains seven Git
commits and is evaluator-only pending sanitization. Base/reference controls
match all four publisher outcomes: base 3 pass / 1 fail, reference 4 pass.
Nineteen additional mocked-debugger checks give base 4/19 and reference 19/19;
these cover return identity, forwarding, class/static methods, call order and
exception identity. They test the publisher reference, not a teacher or model.
Evidence: `evidence/data/easyptvsd-review-001/review.json`. Next: sanitize and
replay shortest eligible trajectory, then grade, tokenize and review rights.
Current assembled corpus remains one quarantined Datetransform example. No GPU.


### Easy-ptvsd sanitized replay and integration — 2026-10-09

Verified ten tracked files in an exact-tree snapshot with one parentless commit,
no remotes, known oracle paths absent, and old base/head/merge commits inaccessible.
Verification concerns the mounted filesystem, not inherited Docker layer bytes.
Snapshot base/reference outcomes match original controls for all four test IDs.

Shortest trace `a148d74a-1367-4d52-8c47-a73008f73e7e` replayed but failed the
source-path restriction because its submitted patch retains `reproduce_issue.py`.
Retained the failure and did not edit its patch. The alternate trace
`40eb374a-0850-4770-8b29-61e6905e5c55` performs its own cleanup, submits only
`easy_ptvsd.py`, and passes 4/4 independent evaluator outcomes and 19/19 added
semantic probes. Replayed observations are fresh; original teacher conditioning
on those observations is not established.

Alternate history: 15,297 input / 4,527 supervised tokens; plus 8,192 reserve is
23,489, below 32,768 by 9,279 tokens. Mechanical admission passes; training remains
unapproved. Selection 004 and corpus 005 combine this trace with Datetransform:
29,423 input / 9,101 supervised tokens. All four real admission gates remain
unresolved. Next: attribution/rights, observation review, broader supply, updated
split isolation and scheduling. No GPU used.


### Easy-ptvsd attribution and restore cycle — 2026-10-09

R2 replay archive restored (91 files); corpus 005 validates through indexed
scheduling. Local and restored schedule/updates bytes match exactly: two
whole-example updates, 9,101 supervised tokens, zero overshoot, one epoch.
This is an inspection schedule, not training approval or GPU-fit evidence.

Captured ten repository files including MIT LICENSE.md and pytest 8.3.3 notice.
ptvsd 3.0.0 has no installed/archive standalone notice; captured its source
headers and referenced Apache 2.0 text. All seven installed Python source files
match the hash-verified PyPI archive. This does not certify the whole environment
or exhaustive rights. Attribution review: evidence/data/easyptvsd-rights-review-001.

Replay observation audit found five errors (missing issue reads, direct test
import failure, grep no matches, reversed classmethod reproduction). None were
concealed. Twenty-three calls have unspecified truncation status. Continue
observation consistency/attribution and broader qualification; no GPU used.


### Fancy-header branch counterexamples — 2026-10-09

Pinned image matches declared base; publisher base/reference controls match
13 expected outcomes (base 12 pass / 1 fail, reference 13 pass). Additional
12-case source branch probes pass 8/12 on base, 12/12 on reference, and 11/12
on each of three teacher source-edit reconstructions. Two traces suppress
missing-header errors on nonempty inputs; the third suppresses invalid-header
validation for docstring-only input with an empty body. All three are held.

The separate docstring/body branch was tested with its explicit object contract,
not a native newer-Python AST. These probes do not establish cross-version
compatibility or reproduce teacher shell execution. Evidence and exact edits
are retained at evidence/data/fancyheader-semantic-review-001 and
evidence/data/fancyheader-branch-probes-001. Do not equate publisher Python 3.6
passes with branch-complete repair quality. No new example added; corpus stays
at two quarantined examples, 9,101 supervised tokens. Next: qualify another
repository and continue corpus review. No GPU used.


### Supply feasibility and broader qualification batch — 2026-10-09

Verified census: 34,269 raw traces. Current cost-screened, image-present cohort:
2,621 traces, 1,575 tasks, 902 repositories. These counts are not admission.
Corpus 005 remains 9,101 supervised tokens, quarantine only. Under the current
32,768 context cap and 8,192 output reserve, a complete example has at most
24,576 input tokens and at most 24,575 causal supervised targets. Thus even
before prompt/tool masks and quality losses, one trace per task in this cohort
has a single-pass ceiling of 1,575 × 24,575 = 38,705,625 targets. All 2,621 traces
have ceiling 64,411,075. Neither number is available training supply.

A 50M-token candidate therefore requires expanding this cohort, multiple
trajectories per task, repeated exposure, or some combination. Three candidates
may reuse the same corpus; 150M processed targets are not 150M unique targets.
Do not interpret repetitions as independent tasks or evidence. No acceptance
rate is extrapolated from the deliberately chosen small reviewed subset.

Added a deterministic 32-repository review batch: choose each unreviewed
repository's shortest source-proxy trace, divide repositories into four cost
rank strata, select eight per stratum by seeded hash ranking. This widens cost
and repository coverage; it is not an unbiased coding benchmark or proof of
native token fit. All 32 issue descriptions are extracted with pinned task
shard identities. Evidence: evidence/data/qualification-batch-001. Next: review
those tasks and qualify their runtime/trajectory evidence.

Full CPU regression: 305 tests, 281 passed, 24 skipped. No GPU used.


### Broad batch triage and NumPyro mathematical check — 2026-10-09

Read all 32 issue descriptions; extracted identity-checked evaluator-only
patches for all 32 and reviewed reference/test patches for ten. Reviews record
specific missing tests and distinguish issue-only from patch-reviewed tasks.
Priority batch: CRC, NumPyro, Verde, civisml-extensions, geomet, pandas-vet,
hyp3-sdk, litecli. This adds state, tensor-rank, numerical, CV-alignment and
parsing coverage; no examples are approved merely by selection.

For NumPyro composition ranks, derived the minimum feasible input rank as
max(0, max_i[d_i - sum_{j<i}(c_j-d_j)]). The reference's backward recurrence
starts at the final domain rank and visits preceding transforms only. Exact
source/reference functions were checked against forward feasibility and the
closed form for 69,904 bounded abstract sequences: reference 0 disagreements,
base 17,942. This is not JAX or full-task runtime validation.

Held broad reference approval for sktime due to formula documentation/edge
contract gaps and decode due to version/specification and coverage mismatch.
Uvicorn trusted-proxy semantics and magnivore rounding require clarification
from source/contracts before qualification. Corpus remains two quarantined
examples, 9,101 supervised tokens. Evidence: qualification-batch-review-001
and numpyro-compose-math-001. Next: runtime and teacher review for priority tasks.
No GPU used.


### CRC runtime and provenance qualification — 2026-10-09

Resolved Nicoretti__crc-153 against the benchmark's merged solution commit
7ac98da2c6df6bbb91e2793ac69fcf796f9dba14, rather than the unavailable PR head.
The new snapshot independently preserves all 56 tracked files, has one
parentless commit, and removes checked old commits and known oracle paths
from its mounted filesystem. Inherited image layers remain outside this audit.

Original controls could not import crc: its installed editable-path file points
to /crc/src instead of /testbed/src. A diagnostic runner verifies the exact old
path bytes, records their hashes, and applies the same path-only correction in
four disposable offline containers. Original/snapshot base outcomes match
exactly (11 passed, 6 failed); both reference runs pass all 17 cases. Source
imports resolve to the checkout and tests leave tracked diffs unchanged.
Evidence: evidence/data/crc-runtime-controls-002 and crc-snapshot-verify-002.
Earlier failed attempts are retained. No teacher replay or corpus admission is
claimed. Next: integrate the explicit runtime correction into the replay image,
then test digest state preservation and updates interleaved with digest reads.
Corpus remains two quarantined examples, 9,101 supervised tokens; Pod stopped.


### CRC deep checks and native replay — 2026-10-09

Added an independent bit-feedback CRC oracle over GF(2), cross-checked CRC32
against zlib, and checked every 8-bit register state plus all split points of
five bounded messages across 16 configurations and two implementations.
Reference: 4,965 passed; base: 3,433 passed, 1,532 failed. These are dependent
within-task checks, not independent performance samples. Continuation after
reads is explicitly a stronger engineering invariant than the abstract single
final-digest workflow. Scope and derivation: crc-semantic-probes-001/DERIVATION.md.

Packaged the editable-path repair into a local derived image; independently
verified unchanged source snapshot and reproduced all 17 publisher transitions.
Build 003 failed because Docker interpreted the bare image ID as a registry
name; retained that failure. Build 004 uses a local tag with parent identity
checks before and after build; final runtime is pinned by content ID.

Native replay of trace 888c60d0-0a64-4816-aa3b-6c0aaacbf89a completed with
36 charged calls and fresh observations. Its patch retains final_verification.py
and reproduce_issue.py outside the source allowance, so grading stopped before
tests. No artificial cleanup, trimmed patch, training admission or candidate
semantic pass is claimed. Evidence: crc-replay-001, crc-replay-grade-001,
crc-qualification-review-001. The other reviewed CRC traces exceed the current
40-call source-proxy budget. Move to the next priority task rather than change
these acceptance rules for a preferred example. Corpus remains two quarantined
examples / 9,101 supervised tokens. No GPU used; P1 remains incomplete.


### NumPyro teacher mathematical screening — 2026-10-09

Reviewed all three extracted NumPyro-1894 teacher source edits before downloading
the 2.53 GB compressed image. Each adds a singleton special case while retaining
the incorrect multi-transform recurrence. Exact edited functions disagree with
independent forward feasibility and the closed-form rank oracle on 17,936 of
69,904 bounded sequences per trace, despite zero singleton disagreements.
For CorrCholeskyTransform followed by its inverse, all return input rank 2 where
rank 1 is sufficient and minimal. The shortest trace changes its diagnostic
assertion from 1 to 2; preserve that contradiction instead of training on its
success claim. No native replay, JAX evaluation, tensor-value or Jacobian test
is claimed. All three held for positive training; image metadata resolved but
layers not downloaded. Evidence: numpyro-teacher-001, numpyro-teacher-math-001,
numpyro-image-001. Next priority: Verde or civisml task qualification. Current
corpus remains two quarantined examples / 9,101 targets, not training-approved.
Pod remains stopped; P1 is incomplete.


### Verde contract audit and civisml intake — 2026-10-09

Verde-255 has an issue/evaluator API mismatch: the issue asks for `copy`; all
three teachers implement it; reference/tests call `copy_jacobian`. Signature
binding confirms each teacher rejects the evaluator keyword. After parameter
normalization and docstring removal, all three executable function ASTs match
the reference. Hold benchmark alignment, not mathematical correctness; no
renaming, evaluator modification or invented successful replay. Numerical
change-of-variable derivation and limitations are in verde-contract-review-001.

Reviewed civisml-extensions-22 source edits, which cache CV splits to keep
prediction rows aligned with target labels. Selected trajectory
101cfa89-3239-48d5-a2bc-abbbaf09929d for the next native qualification: 40 source
proxy actions and explicit cleanup of five diagnostic files. This is selection,
not acceptance. Resolve deterministic changing-fold negative controls, unequal
fold sizes and sample-weight indexing before admission. Image digest is pinned;
1,432,048,066 compressed bytes, layers not downloaded. Evidence: civisml-review-001,
civisml-teacher-001, civisml-image-001. Corpus unchanged; Pod stopped; P1 incomplete.


### civisml runtime, deterministic controls and replay preflight — 2026-10-09

Pinned runtime downloaded; Python 3.6.13 / sklearn 0.19.2 imports the task from
/testbed. Sanitized snapshot independently preserves 22 tracked files, removes
checked old commits and known oracle paths, and has one parentless commit.
Original and snapshot controls match every publisher transition: base 53/54,
reference 54/54. This one stochastic publisher regression is supplemented by a
deterministic changing-fold mechanism check: base 0/12 aligned, reference and
all three editor variants 12/12. Checks cover unequal folds, estimator column
order, training weights, row coverage and meta parameters using real NumPy but
controlled fitting/job doubles. No model-performance or independence claim.

Cloud-offloaded local files blocked reads. Two owned processes were terminated
only after identifying blocked reads and dataless files; source_snapshot.py and
image metadata were restored byte-identically from manifest-verified archives.
Other hydration races were rejected by inventory checks; successful retries use
fresh paths. No integrity check was weakened. Evidence includes local restoration
receipt and retained partial snapshot context; failed extraction attempts created
no output directories. Successful inputs: civisml-input-004; snapshot build and
verification: civisml-snapshot-002 / civisml-snapshot-verify-002; controls:
civisml-controls-001 / civisml-snapshot-controls-002.

Selected teacher replay stopped before container creation: action 8 uses an
absolute-path grep invocation outside the adapter's reviewed shell form. Next:
implement/test a narrow command mapping, then native replay, actual-patch grading,
context audit and rights checks. No training example admitted. P1 remains
incomplete; Pod stayed stopped. See civisml-replay-preflight-001 and
civisml-alignment-probes-001 for explicit limitations.


### Source grep adapter and civisml native replay — 2026-10-09

Added a narrow standalone `grep -n` mapping for one literal identifier and one
repository file. It accepts reviewed quoting forms and uses source_path plus
shell-safe argument rendering; shell operators, extra files, traversal, metadata
paths and unreviewed patterns reject. Tests compare actual match/no-match
stdout, stderr and exits. Full CPU suite: 307 tests, 283 passed, 24 skipped.
Initial suite had two hydration-related inventory rejections; both logs retained.

Civisml replay 002 completed with 40 charged calls, fresh observations and only
civismlext/stacking.py in the submitted patch. Actual patch passes 54/54 evaluator
cases and 12/12 deterministic method-alignment cases (controlled estimator/job
doubles, not concurrent fitting validation). Observation audit records two
errors, one explicitly truncated output and 31 unspecified truncation statuses;
these are preserved rather than relabeled successful.

Untruncated native history has 84 messages / 41 exchanges, 40,688 input tokens
and 10,867 supervised targets. With the 8,192 output reserve this needs 48,880
context tokens, exceeding the current 32,768 limit by 16,112. Token export
rejected; no tokens were silently dropped. Admission 004 holds this otherwise
passing candidate for context fit; it is not added to the corpus. Next: assess
an explicit, generally applicable observation-budget policy or select fitting
trajectories; any changed replay needs fresh observations and requalification.
Evidence: civisml-replay-002, civisml-grade-002, civisml-candidate-alignment-002,
civisml-history-003, civisml-tokens-004, civisml-admission-004 and
source-grep-regression-001. Corpus unchanged; P1 incomplete; Pod stopped.


### Civisml context-policy analysis — 2026-10-09

Verified swegemma 0.2.10's command cap (5,000 characters per stream), separate
file limits, missing explicit command-truncation flags and duplicated error
stream payloads. Counterfactual tokenization leaves all actions intact and caps
tool payloads only in memory; no altered history/tokens were emitted for training.
Command cap 1,024 plus file cap 2,000 still needs 33,681 tokens including reserve.
Only the tested 512/2,000 policy fits (30,911 total), but information sufficiency
and adaptive repair quality are unverified. Do not lower limits solely to admit
this case. Current policy and corpus remain unchanged.

A future generally applicable observation policy must preserve recoverable full
outputs, explicitly report truncation, be checked against harness compatibility,
and pass multi-task information/repair evaluation using fresh executions. Long
assistant diagnostic scripts also contribute to cost. Evidence and decision:
civisml-context-analysis-001. Continue independent fitting-data qualification;
this is not a Runpod blocker. P1 remains incomplete; Pod remains stopped.


### Geomet native qualification and context gate — 2026-10-09

Reviewed three geomet-101 teacher repairs. All follow the issue's suggested
truthiness-based SRID override. Bounded extracted-function probes cover six
geometry types, five metadata conditions and omitted/None/positive overrides:
base 60/90, reference and each teacher 90/90. Coordinates and input nonmutation
are checked. Separate explicit-zero probes expose a difference: reference 30/30,
teachers 0/30. Do not equate this with a valid-CRS claim; zero-domain contract
remains unresolved. No projection/reprojection validity is asserted.

Pinned image and sanitized snapshot qualify: 36 tracked files, one parentless
commit, old commits/known oracle paths inaccessible in the mounted filesystem.
Original/snapshot publisher controls agree: base 19/23, reference 23/23.
Trace 8f942217-d0bf-4856-9387-3151dcc1df24 replays with 39 charged calls and
explicit diagnostic cleanup. Submitted patch contains only geomet/esri.py,
passes 23/23 tests, and yields exactly the source bytes used in semantic probes.
Observation audit: two errors, two explicit truncations, 29 unspecified statuses.

History: 82 messages / 40 exchanges; 34,811 input tokens, 8,494 targets.
With reserve, context need is 43,003, so mechanical admission rejects it. No
training token export or corpus addition. Evidence: geomet-precedence-probes-001,
geomet-snapshot-verify-001, geomet-snapshot-controls-001, geomet-replay-001,
geomet-grade-001, geomet-candidate-source-001, geomet-tokens-001, geomet-admission-001.

Repeated context failures motivate an explicit turn-level SFT investigation:
keep the full causal prefix through a selected assistant action, supervise only
that action, and exclude later observations/outcomes. Such examples must be
labeled partial trajectories, not complete successful episodes. Qualification
must verify valid exchange boundaries, token/label identity, no duplicated target
counting across overlapping prefixes, task-level split grouping and complete
coverage accounting for omitted long-prefix actions. No observation cropping or
teacher-action rewriting is authorized by this proposal. Compare usefulness
before replacing the full-trajectory corpus format. Current corpus remains two
quarantined examples / 9,101 targets; P1 incomplete; Pod stayed stopped.

### Experimental action supervision audit — 2026-10-09

Implemented `zenithsync/action_training.py` and `scripts/audit_action_training.py`.
Each selected action receives its complete causal prefix, with every earlier
assistant label masked. Future outcomes are excluded. Complete source histories
must validate first; partial examples explicitly end at a pending tool call.
The pinned native tokenizer verifies unchanged serialization, token identities,
assistant spans and context boundaries. The audit additionally requires action
labels to partition the full-history target positions exactly, without overlap.
No token arrays are exported and no training admission is granted.

| History | Fitting / all actions | Fitting / all unique targets | Repeated input tokens for fitting prefixes |
| --- | ---: | ---: | ---: |
| geomet | 24 / 40 | 4,921 / 8,494 | 344,145 |
| civisml | 27 / 41 | 7,448 / 10,867 | 296,504 |
| easyptvsd | 31 / 31 | 4,527 / 4,527 | 257,667 |
| datetransform | 28 / 28 | 4,574 / 4,574 | 220,178 |

All prefixes use input + 8,192 <= 32,768; no observation cropping. Evidence is
`evidence/data/{geomet,civisml,easyptvsd,datetransform}-action-audit-002/report.json`.
These are four source histories, not 140 independent tasks. Prefixes must retain
the source task/repository split. Aggregate token counts do not create new unique
data. All 140 actions partition 28,462 original targets; fitting prefixes cover
110 actions / 21,470 targets. Late supervision remains missing from long cases.

For the two already-fitting histories, 477,845 prefix input tokens replace
29,423 full-history input tokens (about 16.24 times), with the same 9,101 targets.
This is token-processing overhead, not a measured runtime multiplier. Do not
replace full trajectories with this format by default. Conditional mathematical
identity: if each shared position has identical causal model computation, the
sum of per-action target losses equals the full-history target-loss sum when all
actions are included. A token-weighted denominator is required; averaging action
means changes the objective. Dropout, position-dependent kernels, sequence-length
scaling and floating-point effects mean gradient equivalence has not been proved
for the deployed model. Excluding long prefixes also changes the training set.

CPU suite: 312 tests, 288 passed, 24 skipped. Five focused tests cover selection,
causality, mutation isolation, masking and rejection boundaries; real-tokenizer
checks cover the four histories above. The first datetransform audit rejected a
file changed during cloud hydration; the unchanged stable receipt-bound retry
passed. This check was not relaxed. Earlier audit-001 reports remain historical.
Current corpus remains two quarantined examples / 9,101 targets. No GPU training
or learned-gain claim. Pod remains stopped; P1 incomplete. Next work must address
corpus supply and integration without treating partial coverage as completion.

### Additional corpus pilot — 2026-10-09

Pinned NVIDIA [Open-SWE-Traces](https://huggingface.co/datasets/nvidia/Open-SWE-Traces/tree/e192b26a43b8d09f156eeee781aef8e6bd5108ba)
at `e192b26a43b8d09f156eeee781aef8e6bd5108ba`. The current card declares
CC BY 4.0 and reports removal of Git-exploit trajectories from its earlier
release. This is publisher evidence, not our independent exploit/rights audit.
The [paper](https://arxiv.org/html/2606.16038v1) describes multilingual,
multi-teacher distillation; its older corpus totals cannot stand in for the
current pinned revision. Its reported 65,244 successes divided by 207,489 total
trajectories is about 31.45%, not the nearby claimed 40.6%; the denominator for
that rate is unclear. We will use row-level measured counts and preserve unknown
outcomes rather than inherit that aggregate percentage.

Acquired two bounded shards, each matched to publisher size and SHA-256:
OpenHands/Qwen3.5-122B tail shard 16/17 (43,048,099 bytes) and
mini-swe-agent/Qwen3.6-27B tail shard 21/22 (40,259,778 bytes), both SWE-rebench-V2.
Cards and publisher inventories are preserved. Selection was the smallest file
within each chosen framework/teacher/source, not random sampling. No population
success or usability estimate follows from these samples.

| Pilot | Rows | Repositories | Publisher resolved / unresolved / unknown | Python rows |
| --- | ---: | ---: | --- | ---: |
| OpenHands | 463 | 343 | 90 / 251 / 122 | 76 |
| mini-swe-agent | 1,035 | 669 | 360 / 593 / 82 | 224 |

Metadata projection reads no trajectory or patch bodies. Both shards contain one
exact `Textualize/rich` row, reserved by the official task index. Exact reserved
repository exclusion happens before subsequent body projection. No fork or
semantic-duplicate clearance is claimed. The new schema still omits explicit
tool-response IDs; do not silently treat it as native Gemma history.

Inspected only publisher-positive Python histories outside exact reserved repos:
26 OpenHands, 109 mini-swe-agent. All 26 OpenHands histories pass the existing
single-pending response-link diagnostic after explicit projection excluding the
reasoning field (zero reasoning characters in these inspected rows). None fit
40 source shell/editor calls; the shortest has 54. For mini-swe-agent, 28 of 109
have <=40 source bash calls; the shortest has 18. These proxies do not establish
native charged calls, context fit, independent repair correctness or replay.
No source commands were executed, no reference/model patches were read, and no
training examples were admitted. These counts are not new independent tasks
across all existing datasets; cross-source overlap remains to be measured.

Extended the metadata auditor with an explicit Open-SWE-Traces schema branch.
Two isolated-data-runtime tests cover both schemas, projection behavior, unknown
labels and rejection of boolean/out-of-range/null outcomes. Evidence:
`open-swe-{openhands,mini}-metadata-001`, `open-swe-pilot-screen-001`.

Decision: investigate mini-swe-agent terminal/bash semantics and the pinned V2
task/runtime join before bulk download. Do not expand the demonstrated expensive
OpenHands tail-shard route without a broader metadata/token screen. Preserve the
same replay, quality, attribution and split requirements. Current approved
training supply has not increased; corpus 005 remains two quarantined examples.
Pod remains stopped and P1 remains incomplete.

Regression: 314 tests, 288 passed, 26 skipped in the CPU environment; the two
new PyArrow-dependent tests separately passed in the isolated data runtime.

### Mini-swe-agent serialization and V2 task join — 2026-10-09

Added `zenithsync/mini_source_history.py`, a separate source serializer. It accepts
only the inspected four-field message schema and single bash calls, validates
command argument shape, preserves assistant text/reasoning and observation text,
and infers response IDs only with one outstanding call. Parallel, orphan,
interrupted and duplicate exchanges reject. Unknown fields and malformed
arguments reject. A final unanswered bash call remains explicitly unanswered;
its text is not proof of execution, submission or successful repair. No commands
are run or rewritten by the converter.

Pinned [SWE-rebench-V2](https://huggingface.co/datasets/nebius/SWE-rebench-V2/tree/10483de0f50fe5da545942705a76c6150171af7f)
at `10483de0f50fe5da545942705a76c6150171af7f`. Acquired its 428,839,266-byte
Parquet shard with publisher hash/size verification, plus card and LICENSE.
Only task ID, repository, base commit, image tag, language and license metadata
were projected for this join. No task problem bodies or reference patches were
read during this operation. All 28 selected source histories joined uniquely by
task ID with matching casefold repository names, excluding exact reserved repos.
Image tags are source metadata, not verified runtime digests or executable tests.

All 28 converted source histories pass the exact pinned Gemma rendering,
token-identity and assistant-span checks. Sixteen fit input + 8,192 <= 32,768,
with 99,359 source assistant targets in total. The other twelve are retained as
context exclusions. All source assistant text is counted, including source
reasoning embedded in content. The single bash schema, source prompts and
observations differ from our native nine-tool interface, so these are not native
training-token counts or new corpus admissions. No token arrays exported.
Evidence: `evidence/data/mini-source-qualification-001/{receipt,token-report}.json`.

The shortest fitting histories are werkzeug-2971 (11,198 input / 3,853 targets)
and dbt-snowflake-716 (12,216 / 3,068). Select runtime/replay work by clear issue
contracts and practical environment requirements, not length alone. Next:
inspect source shell/session/terminal behavior against the native executor,
pin candidate container digests, verify pristine source and independent grading,
then replay with fresh observations and measure native token costs. Larger data
acquisition remains conditional on this compatibility result.

Four focused converter tests passed. Full CPU suite: 318 tests, 292 passed,
26 skipped. The first source-token run failed because the evidence script name
`tokenize.py` shadowed Python's standard library; it was renamed to
`measure_source_tokens.py`, and all 28 real-history checks then completed.
Failure and passing logs are retained. Current admitted supply has not increased;
corpus 005 still contains two quarantined examples. Pod stayed stopped; P1 remains
incomplete and no learned gain or GPU-fit claim is made.

### Submission contract reconciliation — 2026-10-09

Inspected source command sequences for fitting mini candidates, including
werkzeug-2971, dbt-snowflake-716 and brutils-python-116. Their source finish reads
an exported path-selected patch file. The pinned native submit_patch instead
stages intent-to-add untracked files, captures a baseline diff, then strips
protected files. Thus a source patch export and native submission are not
interchangeable: scratch artifacts can enter the native diff.

Added `zenithsync/submission_reconciliation.py`. The planner supports an explicit
tracked-repair/untracked-scratch profile: the current tracked binary diff must
already equal the intended patch byte-for-byte; the complete nonignored
untracked inventory must exactly match individually reviewed scratch paths.
It rejects staged changes, path traversal, duplicate paths, symlinks and changed
repair bytes. Returned scratch records contain content hashes and sizes. It
performs no cleanup, executes no source commands and grants no training approval.
Scratch designation remains a semantic review responsibility, not a filename
heuristic. The planner is a point-in-time check, not concurrent-writer protection.

Four disposable-Git tests establish the artifact mismatch, exact patch equality
after explicit fixture cleanup, mutation-free planning, and rejection boundaries.
This is not a real task replay. Before integration, any cleanup must appear as
an adapter-authored native action, with file identities rechecked immediately
before deletion and actual post-cleanup native submitted patch equality checked.
Do not call this source-teacher-authored behavior or silently change its repair.
New-source-file and staged-change reconciliation remain unsupported.

Pinned werkzeug-2971 registry metadata to
`swerebenchv2/pallets-werkzeug@sha256:6ccc246ac36fe305dd00e85767d1a0d2ec1216d82792a6eac208c573dd7d5439`:
Linux amd64, 781,021,260 compressed layer bytes. No layers downloaded or runtime
verified. Evidence: `werkzeug-v2-image-001`, `submission-reconciliation-001`.
Next: pristine V2 runtime/control qualification and actual native replay with
explicit submission adaptation; do not accept source labels as repair proof.

Full CPU retry: 322 tests, 296 passed, 26 skipped. Initial run had one failure
and one error when macOS hydration changed inventory metadata for run_p1_server.py
and model_intake.py. Stable rereads and the unchanged test suite then passed.
Both logs retained; integrity checks were not relaxed. P1 remains incomplete,
corpus 005 unchanged and quarantined, Pod stopped.

### Werkzeug V2 original-image controls — 2026-10-09

Pulled the pinned werkzeug-2971 image. Read-only offline inspection verifies
HEAD `2139fa0b2cad96053f807384a6d04d8d09717802`, clean tracked/untracked status,
Python 3.10.19 at `/usr/local/bin/python`, and package origin
`/werkzeug/src/werkzeug/__init__.py`. The image contains 5,684 reachable commits;
it is evaluator-only until sanitization. Registry digest remains
`sha256:6ccc246ac36fe305dd00e85767d1a0d2ec1216d82792a6eac208c573dd7d5439`.

Selected V2 task extraction is evaluator-only. Its problem requests increasing
the PBKDF2 default to 1,000,000 iterations. Reference changes the constant and
changelog; the test patch changes the expected default hash prefix. This is a
historical task contract, not current password-storage guidance or a claim of
cryptographic security. Source-teacher correctness still requires actual replay
and additional relevant compatibility checks.

Added `scripts/qualify_rebench_v2.py` with an explicit src-layout Python profile,
exact task/registry bindings, reserved-repository exclusion and full test-node
comparison. The shared disposable-container runner now accepts a validated
absolute interpreter path; its default remains /usr/bin/python3. Existing
source-bound historical receipts retain their old helper identity; any future
requalification must use a correspondingly pinned implementation bundle.

Original-image controls (final script, controls-002): base 11/12; reference 12/12;
all 12 publisher outcome transitions match, no node-ID collisions. Both runs
import from the declared source and leave their patched tracked diff unchanged.
Containers were offline and cleanup succeeded. No sanitized image, teacher
candidate grade or trained model result is claimed.

Three profile/entrypoint tests pass. An initial negative test caught acceptance
of an absolute test path; validation now rejects absolute, repeated-separator,
traversal and ambiguous target lists before execution. Full CPU suite: 325 tests,
299 passed, 26 skipped. Initial and final control directories are retained.

The cloud-backed local V2 Parquet read timed out. Restored the previously
published 53-file / 431,730,739-byte bundle from R2 into a local /tmp directory;
restore completed with byte verification. Extraction then used that verified
copy. This is an additional recovery check, not permission to delete originals.
Evidence: mini-source-restore-001, werkzeug-v2-{probe,evaluator,profile}-001,
werkzeug-v2-controls-002 and werkzeug-v2-source-001.

Next: sanitize the V2 root layout, verify exact tree preservation and old-history
removal, repeat paired controls, then replay the source actions and explicitly
reconcile submission artifacts. P1 incomplete; current corpus unchanged and
quarantined; Pod remains stopped.

### Werkzeug V2 exact-tree snapshot — 2026-10-09

Snapshot build/verification supports explicit source roots and interpreter paths;
legacy /testbed and /usr/bin/python3 defaults remain. The first Werkzeug build
rejected the ancestry precondition: both PR head and merge objects are absent in
the publisher image, despite older history being retained. No check was disabled
silently. Added explicit `already_absent` solution mode, requiring Git's quiet
commit lookup to return exactly missing-object status with no output. Existing
commits reject that mode; default ancestry behavior remains. Receipts explicitly
set `solution_ancestry_verified: false`. Exact declared base and tracked tree
verification still apply. Absence is not ancestry evidence.

Build 002 produced local image
`sha256:00b4cc4b5bdbc142374db2ea14e6387094e4fca157e3c50392f7dcb0c1ed1854`.
Independent offline verification checks all 311 tracked files, their content,
modes and aggregate manifest against the preserved base tree; one parentless
commit remains, no remotes, no tracked changes. Original base, PR head and merge
commits are inaccessible. Declared oracle paths at both /testbed and /werkzeug
are absent. This covers the mounted filesystem, not arbitrary inherited layers
or a universal absence-of-oracles claim.

Re-ran original and sanitized-image controls with the same current evaluator:
base 11/12 and reference 12/12 on each. Exact full-node-ID outcome maps agree
between images in both roles. Sanitization has not changed these evaluator
outcomes. This does not grade the teacher patch or establish learned performance.
Evidence: werkzeug-v2-snapshot-002, werkzeug-v2-snapshot-verify-002,
werkzeug-v2-controls-003, werkzeug-v2-snapshot-controls-001/original-parity.json.
Failed build 001 remains preserved.

Six source-snapshot tests pass, including rejection of present solutions in the
new absence mode and preservation of exact source bytes. Full CPU suite:
326 tests, 300 passed, 26 skipped. Next: qualify moving /werkzeug into native
/workspace with dependency and /testbed aliases, replay the selected source
commands, and test explicit scratch cleanup plus native patch equality. Source
and native observations must remain distinguished. P1 incomplete; corpus still
quarantined; Pod remained stopped.


### P1 continuation: native V2 replay and independently graded candidate

The selected Werkzeug mini-source trace completed offline native replay in
werkzeug-v2-replay-001. Its 23 nonterminal source commands remained unchanged;
the adapter then issued explicit scratch cleanup and native submit_patch.
There were 24 charged commands and one submission. Four reviewed untracked
scratch files were removed only after tracked diff and complete untracked-set
checks. The submitted 1,103-byte patch exactly equals the source-exported patch
(SHA-256 534f7a271cf231bb692cf9eda4dcff925c8eed7ee55629776a6d51dc7e74da4b).
The owned container was removed. No model executed, and source observations
were not reused. /werkzeug and /testbed resolve to native /workspace; the
preexisting runtime cache was explicitly moved outside the source tree.

Fresh isolated evaluation in werkzeug-v2-candidate-grade-002 verifies base
11/12, reference 12/12, and candidate 12/12, with identical complete test-node
coverage and no candidate/reference disagreements. Candidate execution receives
only its patch and the evaluator test patch, not the reference solution. The
allowance restricts candidate changes to src/werkzeug/security.py. Patch, replay,
task and sanitized-image identities are bound and checked. This is one repair
qualification result, not learned model performance or an independent statistical
estimate. The initial grader preflight compared the replay snapshot receipt hash
to the wrong snapshot file; it rejected before starting a container. That binding
was corrected to receipt.json and both subsequent grading runs completed.

Source command 11 attempts an editable reinstall in a shell pipeline. pip fails
to fetch build dependencies offline, while the final tail command returns zero.
The full failure text is retained in fresh observations. Neither the pipeline's
zero status nor the passing final patch proves installation succeeded. Existing
source imports remain qualified by independent evaluator origin checks.

Latest CPU suite: 327 tests, 301 passed, 26 skipped. Candidate allowance tests
reject traversal, metadata, test-file and duplicate allowances. These checks do
not establish GPU readiness, semantic correctness beyond tested cases, or
training admission. Native prompt reconstruction, token-budget audit, semantic
compatibility probes and admission gates remain pending. The corpus remains
quarantine-only. Keep Runpod stopped; no GPU training was started this cycle.


### P1 continuation: portable adapted history and measured token candidate

A portability audit found replay 001's cleanup depended on a support module
installed only in its disposable container. It remains useful grading evidence,
but is not the selected training-history replay. The new standalone cleanup
command embeds the inspected planner and file-identity routine, requires only
Python standard library and Git, reads the native baseline tag and patch export
at execution time, and exposes deletion as an adapter-authored native action.
No helper package is installed or imported on the replay target. Disposable Git
tests confirm exact patch preservation without an installed project and rejection
of unknown scratch files before deletion. Point-in-time checks still do not
protect against concurrent malicious filesystem writers.

Replay 002 completes 24 charged commands plus submission, with fresh tool
observations and exact intended/native patch equality. Its independent grade 003
again gives base 11/12, reference and candidate 12/12. The source offline install
failure remains visible; no source observations or teacher reasoning are copied.

build_mini_replay_history.py produces 52 messages / 25 exchanges. It verifies
source command order and exact arguments, explicitly maps the two adapter-authored
suffix actions, requires the reviewed standalone cleanup command, checks task,
profile and patch identities, and excludes reserved repositories. History 002
has identical history, mapping and tool bytes to history 001; its receipt adds
explicit cleanup-profile validation. This is reconstructed conditioning, not an
original teacher rollout or a newly generated independent example.

Pinned Gemma token audit 002 exports quarantined token/label arrays after native
nine-tool rendering and collator validation: 12,199 input tokens, 4,607 supervised
tokens. With the planned 8,192 output reserve, 12,377 tokens remain below 32,768.
The audit now checks history input identities again after encoding. A retained
history-validation report binds the identical projection bytes and token report.
No truncation, GPU fit claim, corpus admission, or learned gain is implied.

Full CPU suite: 331 tests, 305 passed, 26 skipped. Two new history tests cover
source-response exclusion, provenance and rejection of dropped, changed,
reordered, misattributed or failed terminal actions. Two additional standalone
cleanup tests use actual disposable Git repositories. The first history build
rejected a cloud-backed protocol file whose metadata changed during hydration;
a stable reread succeeded without relaxing file identity checks.

Next: integrate V2 evidence with mechanical admission, independently probe task
semantics and compatibility, resolve rights/split/runtime gates, and expand
qualified task diversity. Three token candidates would still be radically
insufficient for the planned training scale; this new candidate is not yet in
the existing two-example quarantined corpus. Keep Runpod stopped. P1 incomplete.


### P1 continuation: V2 consistency assessment and corpus 006 round trip

Added a separate V2 mechanical assessment for portable mini-source replays. It
reconstructs every native exchange and provenance mapping; binds task, profile,
replay and grading inputs; verifies intended/submitted patch equality; recomputes
full test-node comparisons from base, reference and candidate outcomes; checks
execution cleanup and test exit statuses; and checks token/label hashes, causal
label constraints, exact shifted-target counts and context/call budgets. It does
not authenticate arbitrary receipts, rerun tokenization, or approve training.
Five disposable-fixture tests exercise valid-but-unapproved evidence, exceeded
budgets, patch mutation, concealed candidate failure and changed token labels.
Werkzeug assessment 002 passes its mechanical checks with remaining gates intact.

Assembled corpus 006 from the two prior exact candidates plus the portable
Werkzeug candidate: three examples/tasks, 41,622 input and 13,708 supervised
tokens. All four schema-v2 admission gates remain null. A direct training-purpose
load fails with "Quarantine corpus cannot train" before any GPU work.
Manifest SHA-256: 016a17c1d590600f85f9f132dfeb1ae1496a8e8578c1b369e5b83344ae189cf3.
Content SHA-256: 9fcf14059899acd24d5dd00a3bfc894d793f21649d8dd4ac891acade8df9c318.

The explicit dry-run schedule uses seed 7401, one epoch, 13,708 target tokens,
and an 8,192-target update cap: three whole-example updates, zero overshoot.
Published all seven corpus files (460,221 bytes) to R2 and restored them into a
fresh /tmp directory. The restored loader reports the identical content hash,
and schedule.json plus updates.jsonl are byte-identical to the local originals.
This verifies the local R2 ingestion round trip, not execution on Runpod's volume.

Initial candidate inspection and schedule 004 rejected cloud-hydration metadata
changes. The failed schedule artifacts remain retained; stable rereads and fresh
schedule 005 succeeded without weakened integrity checks. Latest CPU suite:
336 tests, 310 passed, 26 skipped. Pod remains stopped. This is still a tiny
quarantine corpus, far short of abundant approved data or the 3×50M-token plan.
Next: independent Werkzeug semantic/compatibility checks, V2 rights and split
review, and systematic expansion to additional source tasks. P1 incomplete.


### P1 continuation: independent Werkzeug semantics and source review

The issue's historical contract is a PBKDF2 default of 1,000,000 iterations.
An evaluator-only probe independently checks that requirement and preserves
explicit-parameter behavior, legacy 600,000-iteration hash verification, rejection
of wrong passwords, and the unchanged scrypt default. Inputs include empty,
ordinary, Unicode and embedded-NUL passwords. Low explicit counts are test cases,
not recommended password settings.

The small-count oracle implements the HMAC recurrence from
[RFC 8018 section 5.2](https://www.rfc-editor.org/rfc/rfc8018.html#section-5.2):
U1 = HMAC(P, S || BE32(i)); Uj = HMAC(P, U(j-1)); each output block is the XOR
of all c values, and concatenated blocks are truncated to the requested byte
length. It does not call the standard-library PBKDF2 function internally.
Two known-answer vectors from [RFC 6070](https://www.rfc-editor.org/rfc/rfc6070.txt)
and 324 matrix comparisons with hashlib calibrate the oracle, including multi-
block output and truncation boundaries. Expensive historical/default checks use
hashlib directly. Shared primitive implementations limit independence; this is
not a cryptographic security proof.

All three fresh offline runtimes pass 326 oracle-calibration checks. On 55 task
semantic cases, base passes 48 and fails exactly the seven requested-default
checks; reference and candidate pass all 55 with identical case outcomes.
Calibration counts are separate from task-case counts. The deterministic cases
are not independent statistical samples, and the result is not a learned agent
success-rate gain. Probe execution leaves tracked source unchanged and owned
containers are removed. Evidence: werkzeug-v2-semantic-probes-001.

A separate exact-snapshot source capture compares candidate and reference ASTs
for security.py, excluding only docstrings and source locations. They match;
base and reference do not. The sole changed function docstring is
 generate_password_hash, reflecting the new default. This equivalence excludes
introspection and traceback/source-location behavior and does not establish the
reference is universally correct. The reference also updates CHANGES.rst;
the candidate patch does not claim to reproduce that changelog edit.
Evidence: werkzeug-v2-source-review-001.

Captured the snapshot's tracked LICENSE.txt and copied pinned Open-SWE-Traces
and SWE-rebench-V2 cards plus the task dataset license into attribution evidence.
Both dataset cards declare CC BY 4.0; repository notices remain separate. The
attribution record lists all trajectory transformations and unresolved review
items. No rights, split, runtime or task-alignment corpus gate is automatically
approved. No product/training code changed in this cycle, so the previous full
CPU result remains 310 passed / 26 skipped; the new evaluator probes are reported
separately. Corpus 006 remains three quarantined examples. Pod stays stopped.


### P1 continuation: pipdeptree candidate held after pinned type checks

Reviewed mini-source candidate 168469d9-e93e-438b-9f73-120b2f6f6088 for
 tox-dev__pipdeptree-310. The issue asks for consistent unconstrained dependency
version serialization. Resolved the source image to immutable digest
07746f257fa029380050e8b395ac372c3fd938a598fc05267f1f4dcf0d4c7e2d, acquired it
locally, and verified its clean declared base
06c2f9d518f8bd7d8fa7f3520e231cdf15f0cd7f (410 commits, expected src import).
PR head and merge objects are absent. This image has not been sanitized for
agent execution; no native teacher replay or publisher test grading occurred.

The trace changes ReqPackage.as_dict to return dict[str, str] but leaves its
abstract Package method returning dict[str, str | None]. Repository tox.ini
pins mypy 1.7.1 and pyproject.toml enables strict checking. Prepared exact
Linux/Python-3.10 mypy wheels (with explicitly pinned supporting packages),
hash-checked them, and installed them only in an offline disposable evaluator.
The original image and training/runtime environments were not modified.

Full-source checks under the same checker and installed dependency environment:
base and reference each have three existing errors; the source-observed teacher
patch has those plus two new diagnostics: an incompatible override and an unused
ignore in dag.py. To separate the override from preexisting dependency/type
issues, extracted only the three relevant class method signatures from each
patched source and checked them independently: base and reference pass; the
teacher signature fails with the same override. This is a source-patch screen,
not a fresh model-generated failure or proof the full reference CI passes.

The type distinction is substantive: mutable dict value parameters are invariant,
so dict[str, str] is not a subtype of dict[str, str | None] for this override.
See the [mypy variance explanation](https://mypy.readthedocs.io/en/stable/common_issues.html#invariance-vs-covariance);
the actual experiment used the repository's 1.7.1 pin, not current documentation's
release. Runtime success on the reported JSON case would not remove this static
contract regression. Evidence and decision: pipdeptree-v2-review-001/report.json.
The candidate remains excluded from positive training data. Corpus 006 is
unchanged at three quarantined examples / 13,708 supervised tokens.

Added static_controls.py: bounded noncolored mypy output parsing, exact diagnostic
multiplicity, path/code/message comparison across base/reference/candidate, and
strict summary/exit-code consistency. Source line movements and diagnostic order
do not count as new errors. Unknown output and checker infrastructure failures
reject. Four tests cover new errors amid old ones, line/order invariance,
duplicate multiplicity, and malformed/fatal/contradictory output. This comparison
requires independently qualified equal environments and does not grant admission.

Next: move to the next candidate and reuse the source/runtime checks; do not
silently repair this teacher using the evaluator reference or relabel its
publisher status as verified correctness. Preserve this counterexample for
future negative-example or repair-recovery research with explicit provenance.
Pod remains stopped; no GPU training started. P1 remains incomplete.


Static-control cycle validation: full CPU suite 340 tests, 314 passed, 26 skipped.
The initial run retained one error and one failure caused by cloud hydration
changing run_p1_server.py and model_intake.py metadata during integrity reads.
No checker was relaxed; after that run terminated, a fresh complete run passed.
Both logs are retained in the archived evidence package.


### Dynaconf recursive-equality screen (local, pre-admission)

Pinned original image `sha256:d25a589823a03ab10900ae43aeda1c3845b78d97921702ad91138189ef0d0ad6`
was tested offline at task base `b389b2bbb07b2abb92577e81384f7f939b05c5f5`.
Compared base, publisher reference, and the exact source-observed teacher patch
from message 51. This is evaluator screening, not native agent replay.

Enumerated 202 distinct ordered expression trees of depth at most two using
AND/OR and required-name leaves A/B. Across 40,804 ordered pairs per role,
structural equality mismatches were base 39,800, reference 448, teacher 0.
Registering two independently constructed copies of each tree retained 3, 74,
and 202 entries respectively. Ordered structure is a deliberately conservative
screening oracle; Boolean-equivalent trees need not be structurally equal.
These are exhaustive finite cases, not independent statistical trials.

A concrete reference collision is A AND (A AND B) versus A AND (A OR B).
With A present and B absent, real Dynaconf validation rejects the first and
accepts the second, yet the reference treats them as equal. All four truth-table
rows were checked against those Boolean predicates. The teacher distinguishes
them. This exposes a reference limitation; it does not establish universal
correctness of the teacher or permission to train from evaluator information.

Evidence: `evidence/data/dynaconf-v2-semantic-screen-001`, reproducible drivers in
`evidence/data/dynaconf-v2-semantic-source-001`. All roles imported the repository
package, left tracked source unchanged, and the owned offline container was
removed. Native replay, publisher tests, lineage/snapshot qualification, token
admission, and corpus gates remain pending. No training infrastructure changed.
Corpus 006 remains three quarantined examples / 13,708 supervised tokens.
Runpod stays stopped. P1 remains incomplete.


### Dynaconf native qualification and historical evidence support

Resolved the task's upstream pull request at https://github.com/dynaconf/dynaconf/pull/413.
The old owner path now redirects to a different mirror repository, whose PR 413
returns 404. Canonical upstream validator.py at the task base matches the pinned
image byte-for-byte; this is file-level corroboration, not whole-repository proof.
The original image is clean at the expected base, with 457 reachable commits;
PR head and merge objects are absent. Two failed diagnostic runs are retained:
the diagnostic used the same dictionary key for repository HEAD and PR head.
Run 003 separates these fields and verifies the expected base correctly.

Built and independently verified sanitized snapshot
`sha256:4ddee414e4597204acde8b3ebca8cfb550ff1d0bfcafbba95c2b5d17f90acd5a`:
511 tracked files preserved, one parentless commit, old base/head/merge objects
inaccessible, known oracle files absent. This verifies the mounted filesystem,
not inherited Docker layer contents. Original and snapshot publisher outcome
maps match exactly: base 24/26, reference 26/26.

Native replay 001 completed 26 charged tool calls plus submit_patch, yielding
the exact source-observed patch. Candidate grading passed 26/26 publisher cases.
History 001 contains 56 messages / 27 exchanges. Token audit 001 exported
20,299 input and 6,870 supervised tokens; input plus 8,192 reserve is 28,491,
below 32,768. Mechanical admission 001 passes without granting training approval.
One broad source test command fails collection because optional dependencies
are absent; this error is retained, not transformed into successful verification.
Native replay is teacher trajectory reproduction, not a newly trained agent result.

The qualifier now explicitly supports src and flat package layouts. Exact
repository import origin and package-scoped candidate source allowances remain
required. Historical evidence can explicitly map implementation files to an
archived source copy with the original hash; mapping data, patches, or receipts
is prohibited, and unused mappings reject. Existing Werkzeug evidence was
successfully reassessed with its original archived qualifier in admission 005.
Two prior attempts stopped on macOS cloud hydration metadata changes; after
reading the files locally, the unchanged integrity checks passed. The archived
code is checked as historical evidence; current reconstruction checks still run.

Validation: 13 focused tests pass; complete CPU suite 344 tests, 318 passed,
26 skipped. No GPU checks ran. Source lineage, snapshot, controls, replay,
history, token, and admission evidence are under evidence/data/dynaconf-v2-*.
Dynaconf remains pending final attribution/split/semantic review and assembly;
corpus 006 is unchanged at three quarantined examples / 13,708 supervised tokens.
P1 is incomplete; Runpod remains stopped.


### Corpus 007: four-task quarantine integration

Added the native Dynaconf replay to the quarantine assembly; preserved MIT
repository notice, pinned CC-BY-4.0 dataset cards/license and transformation
notes in dynaconf-v2-attribution-002. Dependency/observation rights and teacher
service-term coverage remain unapproved. Attribution attempt 001 stopped on a
cloud-file metadata change; checks were preserved and attempt 002 succeeded.

Current assembly: four examples and four tasks, 61,921 input tokens and 20,578
supervised tokens. Manifest SHA-256:
`24b6b11a8a111174eac74631043d2804a32bb83b7584a152fc489a6dbcdd0610`.
Content SHA-256: `0a0ac1667b6b6e4096f3aabc0a0c932f7da960d4fcc01e61b7e00f4ad4eb3f7c`.
All four admission gates remain null. Direct purpose=training loading rejects
with `Quarantine corpus cannot train`; no training ran.

Fresh GitHub metadata resolves four source projects, the old Dynaconf mirror,
and all four named reserved repositories. No repository-ID or declared
fork-network overlap is found. The old URL resolves to dynaconf-mirror with fork=false; this metadata alone
cannot establish historical independence.
Dynaconf is explicitly grouped under canonical dynaconf/dynaconf in the corpus.
Final semantic duplicate review, historical/detached-copy grouping, and frozen
splits remain pending; reserved task bodies were not opened.

Published all nine corpus files (684,444 bytes) to R2 and restored to an empty
/tmp directory with verified hashes. Restored loader counts and content hash
match. A one-epoch schedule, seed 7401, target 20,578 supervised tokens and
8,192-token update cap produces four whole-example updates, zero overshoot.
Schedule and updates files from restored data match original bytes exactly.
Schedule attempt 006 stopped on cloud hydration of training_corpus.py; attempt
007 completed with unchanged integrity checks. No optimizer or GPU ran.

Evidence: training-corpus-assembly-007, publish-007, restore-007,
restored-inspection-007, schedule-007, restored-schedule-006, denial-005, and
current-corpus-lineage-002. Code was unchanged this cycle; integration was
verified by actual assembly, rejection, transfer, restore and schedule replay.
The latest code suite remains 318 passed / 26 skipped. Four quarantined examples
are not sufficient for the planned 3x50M candidates; repeated exposure would
not create additional independent tasks. Continue corpus qualification and
admission review locally. Keep Runpod stopped. P1 remains incomplete.


### Workalendar qualification and corpus 008

Qualified peopledoc__workalendar-493, canonical workalendar/workalendar. Original
image digest sha256:3837c3917cae0f429c4540fe570a3d9b68d70615e86995b9a2fc9ea62abebb41
has clean task base 3fd9b831b308f1b0f7e1ca8fffc456ab6bdce56a, 1,008 reachable
commits and no local PR head/merge objects. Sanitized snapshot
sha256:5125f7b3193618806b0a734412dd43486b88fed20d94d49c6cc7467e4735076f
preserves 177 tracked files exactly, one parentless commit, no old base/head/merge
objects or declared oracle paths. Verification concerns the mounted filesystem,
not inherited image layers. Original/snapshot publisher outcomes match exactly:
base 8/11; reference 11/11.

Native replay 002 completed 29 charged calls plus submit_patch; submitted bytes
match the separately screened teacher patch. Candidate passed 11/11 publisher
tests. Independent finite checks: base 0/18, reference 18/18, candidate 18/18.
These cover exact registered/unknown lookups, warning category/count, registry
nonmutation, subclass delegation and exception propagation, not calendar-date
correctness or statistical generalization. An unmatched grep and nonexistent
source-requested pytest node remain errors in the fresh native history. Pipelines
that truncate test output are not treated as independent full-suite evidence.

History 002 has 62 messages / 30 exchanges. Token audit 001: 20,149 input and
7,312 supervised tokens; with 8,192 output reserve, 28,341 fits 32,768.
Mechanical admission 002 passes, without training authorization. Captured the
MIT repository notice and pinned dataset notices; dependency/observation rights
and teacher service terms remain pending.

Local Desktop cloud offloading delayed the existing runtime/profile processes.
Explicit macOS materialization requests allowed them to resume; runtime 001
then correctly rejected a metadata-changing integrity read. Fresh runtime 002
passed. Similar integrity rejections preceded successful semantic-screen 002,
replay 002, history 002, admission 002 and corpus-denial 007. No integrity check
was relaxed; prior outputs/scripts are retained where written.

Corpus 008: five tasks, 82,070 input / 27,890 supervised tokens. All admission
gates remain null and purpose=training is rejected. Manifest SHA-256:
4ced40b5cb89e799a845cd833ae7d34a0c291b170a6a8988f4a028f7e411bf45.
Content SHA-256: b9b1451ea77f89f9a19d50dbc218976af0a8a456bc65f47cf6fcd6d731f626b9.
Published 11 files / 905,531 bytes through publish-009; restored and validated
through restore-008 / restored-inspection-008. One epoch, seed 7401, 8,192-target
update cap: five whole-example updates, zero overshoot. Original schedule-008
and restored-schedule-007 schedule/update bytes match exactly.

Metadata-only lineage audit 003 resolves all five source projects, aliases and
four reserved repositories without known ID/fork-network overlap. This excludes
neither detached copies nor semantic duplicates. No held-out issue bodies read.
No shared implementation changes this cycle; the prior 318-passed/26-skipped
suite is unchanged, not newly rerun. Five quarantined examples remain far below
the planned training supply. Continue local corpus expansion and gate review;
Runpod remains stopped and P1 remains incomplete.


### PennyLane 5716: independent numerical screen, interface gate still closed

Selected the batched StronglyEntanglingLayers issue from 16 source-context-fitting
candidates; mini-candidate-priorities-002 records current status and qualitative
selection rationale. This task adds tensor-shape and quantum-circuit numerical
coverage. It is not yet a sixth corpus example.

Pinned original image sha256:b41317e4fdf7780cc28d1e5eed4a65e69159331091f6749fde7a92f29c5f4a94
runs PennyLane 0.37.0-dev on Python 3.10.19 at clean base
85ff62b9c9218f523ef7ff0535cde7cbf55ebb7b; 4,180 reachable commits,
PR head/merge absent. Verified sanitized snapshot
sha256:e60eb0ef6d062901bedc874d4c731c438b7182d707f06704c0382f8c62800f23
preserves all 1,353 tracked files, one parentless commit, no accessible old
base/head/merge objects or declared oracle paths. Mounted filesystem only;
this does not audit inherited image layers.

Independent dense-state oracle constructs RZ(omega) RY(theta) RZ(phi), Kronecker
operators and explicit computational-basis CNOT permutations, without reusing
the template/decomposition. Rotation convention follows
https://docs.pennylane.ai/en/stable/code/api/pennylane.Rot.html; that current
reference is not a claim about the installed version. Primitive gate calibration
against the pinned runtime establishes matching conventions before comparison.
Seed 5716; batch sizes absent/1/2/4, layer counts 1/2/3, wire counts 1/2/3:
36 cases per version. Reference and source-observed teacher pass 36/36; base
passes 15/36. Candidate maximum absolute state error is 3.554447978966673e-16,
with required atol 1e-11 and rtol 0. Norms also checked. These are finite NumPy
calculations, not independent statistical trials or universal correctness proof.

Screen 002 initially supplied explicit zero ranges for one-wire circuits, which
this constructor rejects. It therefore recorded 12 probe-input failures for
both fixes. Screen 003 uses the supported default in these cases; both runs
are preserved. Other failed attempts stopped on cloud-hydration metadata drift;
none of the integrity checks was relaxed. Runtime 002 is the completed bound run.

Full publisher-module controls collect 44 tests. Base: 29 pass, 12 fail,
3 skip; reference: 41 pass, 3 skip. The strict grader rejects skipped controls.
The skipped tests exercise JAX, TensorFlow, and Torch interfaces, including
gradients; dependencies are absent. Dependency metadata, repository requirements,
test source, and skip mechanism captured under pennylane5716-v2-dependencies-001.
Do not drop these tests or equate 41 passing calls with fully qualified controls.
Next: derive compatible pinned backend dependencies, install in a separately
qualified offline runtime, and rerun complete controls and snapshot parity.
Native source replay, token assessment, attribution and split review remain.

Evidence: pennylane5716-v2-review-001, semantic-screen-003, controls-original-002,
runtime-002, snapshot-verify-001. Shared implementation unchanged this cycle;
prior code suite remains 318 passed / 26 skipped, not newly rerun. Corpus 008
remains five quarantined tasks / 27,890 supervised tokens, all gates pending.
Runpod stays stopped. P1 remains incomplete.


### Corpus 009: PennyLane integration, still quarantined

Six tasks now total 103,227 input / 35,029 supervised tokens. Manifest SHA-256:
`066260151fe14e4778837b124235a25e013d650a3b542915daae79a5f52dd5b0`.
Content SHA-256: `23531344ea84e04f3feb260d5ef9b0155f413974088a761837206f807a6a2b58`.
All four admission gates remain null. Training-denial-008 confirms refusal.

Publish-010 and restore-009 verified 13 files / 1,143,461 bytes. Restored
inspection-009 validates all six examples. Schedule-010 and restored-schedule-008
are byte-identical: seed 7401, one epoch, 35,029 supervised tokens, six
whole-example updates, 8,192-target update cap, zero overshoot. No optimizer or
GPU execution is implied. Failed schedule-009 stopped on cloud-hydration drift.

PennyLane attribution-001 captures Apache-2.0 repository license, observed-file
header and pinned dataset notices. Complete rights review remains pending.
Lineage-004 resolves current canonical repository IDs and declared fork roots
for six source projects, aliases and reserved evaluation repositories, with no
overlap. Detached copies, semantic duplicates and historical forks remain outside
that metadata screen. Native qualification archive verified: 341 files /
1,988,275 bytes. Earlier backend wheel bundle and snapshot archive are also verified.

Current suite: 323 passed / 26 skipped (349 total); focused control/admission
suite: 25 passed. Real-corpus GPU training, held-out learned improvement, final
rights/split approval, and abundant data supply remain unfulfilled. Pod remains
stopped. Next: archive corpus integration evidence, then expand the qualified
candidate pool without treating repeated exposure as new data.


### Two additional positive-supervision exclusions

Linkding 691 remains outside corpus 009 despite passing mechanical grading.
Supervision-review-001 binds two exact unsupported claims to assistant tool-call
commands, which the current loss mask labels: a mock-only test asserts external
website access, and a permissive exception test claims success without proving
its requirement. Preserve original evidence; do not silently sanitize the trace.
A replacement trajectory or separately specified selective-supervision policy
must be qualified before reconsideration. Its initial qualification archive is
verified in R2: 147 files / 712,237 bytes.

Scrapy 6897 is held for a reproduced source-candidate type regression. The pinned
source tox.ini requires mypy 1.14.0 and Python 3.9. Exact extracted constructor
bodies (with explicit external types) pass for base/reference; candidate fails
with `Attribute "path" already defined [no-redef]`. Checker executed on local
Python 3.13 with target 3.9; this is not a full repository or native CI run.
The source command calls this edit a type-annotation fix, so it is unsuitable
positive supervision without replacement. No native replay or publisher tests
were performed for this candidate. See scrapy6897-v2-review-001 and the saved
checker inputs/results. Priority review 003 records both exclusions. Corpus 009
remains six quarantined examples / 35,029 supervised tokens; no GPU work started.


### Kubernetes client 247: source test acceptance counterexample

The source trace's index-28 integration-test function claims successful URL
conversion whenever an exception lacks the substring "hostname is invalid".
An isolated run of its exact class/function definitions accepts both a substitute
that raises an unrelated RuntimeError and a no-op substitute. A negative control
with the expected error substring is rejected. No network or repository code
was executed; this establishes unsound test acceptance, not a broken URL fix.

The candidate is held out of positive supervision because its success-printing
code would become assistant-call training targets under unchanged replay policy.
No native history or token arrays have been produced. Preserve the original
trace and the executable counterexample; do not rewrite it to look successful.
The evidence can support future error-analysis work, but is not automatically
approved as negative training data or a preference pair. Priority review 004
records the hold. Corpus 009 remains unchanged and Runpod remains stopped.
