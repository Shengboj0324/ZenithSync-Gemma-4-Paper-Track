# Continuous implementation and acceptance plan

Updated October 7, 2026. **Living plan; implementation has not started.** Codex owns implementation, mathematical design, engineering, tests, analysis, and evidence preparation. The entrant supplies account access, eligibility decisions, and resource authorization. This document governs cycle cadence; [joint strategy](11-code-track-and-joint-strategy.md) governs competition constraints and [evaluation protocol](05-evaluation-protocol.md) governs experiments.

The objective is a reproducible, competitive repair agent with defensible research results. Mathematical sophistication must improve a justified objective or explain observed behavior. No fabricated results, task-specific answer lookup, leaked reference patches, or cosmetic chat interface presented as a working system. Explicit configuration constants and clearly labeled synthetic test fixtures are legitimate; hardcoded benchmark outcomes are not.

## Cycle structure

Use **8–14 hours per engineering cycle**, including protected acceptance work. A nominal 12-hour cycle allocates one hour to design and scope, six to implementation, three to verification, one to comparison, and one to assessment and documentation. Reallocate after measurement; never omit validation to meet the timebox. A phase may require several cycles. Do not fill time with unnecessary work or declare unfinished work accepted when time expires.

At cycle start, select one bounded deliverable, baseline commit, hypothesis, resource cap, failure conditions, and acceptance criteria. During implementation, checkpoint resumable work and test incrementally. At closeout, assign **accepted**, **revise**, or **blocked** with evidence. Record active engineering time, experiment runtime, and elapsed wall time separately. The cycle target is not a promise of unattended execution between chats.

## Phases and exit gates

| Phase | Main work across one or more cycles | Required exit evidence |
| --- | --- | --- |
| 1. Establish contracts | Inspect authorized official harness; pin model, tool schemas and environment; isolate evaluator assets; freeze data manifests | Starter runs; gold and no-fix controls audited; valid archive; leakage checks; measured resource baseline |
| 2. Build reliable execution | Implement bounded tool use, recoverable state, patch preservation, stopping, offline behavior and runtime accounting | Integration and failure-injection tests; timeout recovery; reproducible cold runs; budget reserve justified on measured workloads |
| 3. Establish mathematical components | Specify selector/scheduler objectives, assumptions, invariants and numerical behavior; implement only compatible mechanisms | Proof or counterexample for each mathematical claim; exhaustive small-instance comparisons where feasible; implementation matches the specification |
| 4. Compare interventions | Evaluate reasoning, retrieval, graph reliability, stopping or retries against the stable baseline; change one explanatory factor at a time | Matched development comparisons, ablations, uncertainty and full cost accounting; retain simple baseline when complexity is unhelpful |
| 5. Train selectively | If evidence justifies it, validate trajectory provenance and adapter support; pilot targeted tuning | Licensed and isolated training data; reproducible training; frozen-checkpoint evaluation; measured net value after load/runtime costs. Skip if unjustified |
| 6. Confirm results | Freeze candidate and analysis; evaluate untouched tasks and external generalization; inspect failure modes | Primary effect and interval, all-task denominator, reproducible tables and explicit limits; no test-set retuning disguised as confirmation |
| 7. Qualify artifacts | Rebuild cleanly, test offline and adverse cases, replay realistic full workloads, audit dependencies and submission packaging | Exact artifact hash and manifest; target-compatible execution; measured runtime feasibility; recoverable stable champion |
| 8. Freeze and refine | Freeze paper method/results; continue code improvements through the same gates; prepare final selections | Paper claims trace to frozen evidence; later code changes carry separate versions and results; actual submission state checked when submission is authorized |

Phases 3–5 are selective and iterative. Return to phase 2 when infrastructure invalidates measurements. Engineering qualification begins early; final qualification repeats only after relevant changes. Deadline pressure reduces scope, never evidence standards.

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
| Candidate mechanism | Optional graph selection, reasoning, recovery or tuning; prioritize measured bottlenecks |
| Deadline allocation | Preserve separate paper/code freezes; revise the resource schedule after each cycle |

## Required closeout and next cycle

After **every** implementation cycle, append a record below and update current variables, next-cycle scope, and affected technical/evaluation/resource/decision documents. Preserve old records and frozen results. No cycle is closed until documentation and evidence agree.

Each record includes: cycle ID; timestamps and three time measures; objective; baseline/candidate hashes; changes; proof and test evidence paths; task/config/run manifests; measured metrics and intervals; costs; failures and unresolved assumptions; six-category assessment; integration and promotion decisions; rollback reference; and next bounded objective. Use “not measured” where applicable. Do not manufacture an aggregate quality score from subjective ratings.

| Record | Status | Evidence and next action |
| --- | --- | --- |
| Planning, October 7 | Documentation only; no implementation cycle completed | Next cycle: phase 1, authorized harness inspection and smallest reproducible baseline. Resolve access and resource caps first; preserve protected evaluation tasks |

Once implementation begins, add detailed cycle records under this table or link them here from a dedicated cycle-log directory. Update this plan as evidence changes; retain the acceptance standards unless an explicitly justified revision improves their validity.
