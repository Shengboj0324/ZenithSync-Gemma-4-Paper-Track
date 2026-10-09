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
