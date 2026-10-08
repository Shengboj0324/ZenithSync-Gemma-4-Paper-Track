# Continuous implementation and acceptance plan

Updated October 7, 2026. **Living plan; user adopted a foundation-first, trainable Gemma agent. Platform implementation and Gemma training have not started.** Codex owns implementation, mathematical design, engineering, tests, analysis, and evidence preparation. The entrant supplies account access, eligibility decisions, and resource authorization. This document governs cycle cadence; [platform specification and handoff](19-agent-platform-and-model-handoff.md) governs the current build, [joint strategy](11-code-track-and-joint-strategy.md) governs competition constraints, and [evaluation protocol](05-evaluation-protocol.md) governs experiments.

The objective is a reproducible, competitive repair agent with defensible research results. Mathematical sophistication must improve a justified objective or explain observed behavior. No fabricated results, task-specific answer lookup, leaked reference patches, or cosmetic chat interface presented as a working system. Explicit configuration constants and clearly labeled synthetic test fixtures are legitimate; hardcoded benchmark outcomes are not.

## Cycle structure

**R1 closeout — October 7:** accepted as a bounded bug reproduction and baseline challenge; **revise the product hypothesis, no promotion**. The React artifact was inaccessible. The previously shortlisted real Raft shutdown defect was reproduced in a controlled component test. Three fresh `gpt-6.1-sol` high-reasoning attempts each passed 21 independent targeted race-enabled checks. Agent times were 314.606, 321.029 and 401.253 seconds. Broader suites retain two failures also present on the upstream reference repair. See [complete results and limits](18-reproduction-cycle-results.md). This does not establish Gemma performance or mechanism lift. Stop before R3: the required persistent baseline failure was not demonstrated. The next research input must be a different accessible failure set, not a product build around this solved example. This early gate did not consume or claim an 8–14-hour implementation phase; hands-on engineering time was not separately instrumented.

Use **8–14 hours per engineering cycle**, including protected acceptance work. A nominal 12-hour cycle allocates one hour to design and scope, six to implementation, three to verification, one to comparison, and one to assessment and documentation. Reallocate after measurement; never omit validation to meet the timebox. A phase may require several cycles. Do not fill time with unnecessary work or declare unfinished work accepted when time expires.

At cycle start, select one bounded deliverable, baseline commit, hypothesis, resource cap, failure conditions, and acceptance criteria. During implementation, checkpoint resumable work and test incrementally. At closeout, assign **accepted**, **revise**, or **blocked** with evidence. Record active engineering time, experiment runtime, and elapsed wall time separately. The cycle target is not a promise of unattended execution between chats.

## Phases and exit gates

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
| Compute, storage and cash caps | Unset; establish before resource-consuming work; include training and failed runs |
| Hardware and runtime reserve | Unmeasured; derive from the actual supported environment and stress runs |
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
