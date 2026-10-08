# Replication and product-selection protocol

October 7, 2026. Protocol with an initial completed reproduction/baseline pilot; later mechanism and holdout stages remain unexecuted. Implements the selection method accepted by the user and extends the [continuous plan](12-continuous-implementation-plan.md). Each full engineering cycle remains approximately 8–14 hours including acceptance work; early rejection gates can end an unpromising investigation sooner.

## Selection contract

Before adopting a product, produce four inspectable objects: a difficult real task, a strong baseline attempt, a falsifiable failure explanation, and a measured mechanism advantage. Novelty and competition compatibility are separate required gates. A compelling explanation without a reproducible task fails; a working product duplicating the nearest competitor also fails this project's differentiation standard.

Every candidate receives one of: **lead**, **ready to reproduce**, **reproduced failure**, **mechanism supported**, **adopted**, **rejected**, or **blocked by evidence/access**. These are project records, not instructions to use any task-status tool. Present state: F01 is blocked by artifact access; F03's Raft case is reproduced but rejected as current evidence of a necessary new mechanism because all three ordinary baseline attempts repaired it under the targeted checks. F02, F04 and the other F03 cases remain unreplicated; F05–F06 remain leads. No candidate is adopted. [R1 results](18-reproduction-cycle-results.md) govern the current decision.

## Cycle R1 — validate one task and its oracle

Start with F01's asynchronous form bug. Allocate roughly two hours to provenance and setup, four to reproduction, three to oracle validation and controls, and one to a reviewable record. If a valid real artifact cannot be reproduced within the resource cap, record that result and move to the next accessible candidate; do not replace it silently with an easier synthetic task.

Freeze full repository hashes, harness revision, dependency lockfiles, OS/runtime, task prompt, test assets and artifact licenses. Keep reference fixes and evaluator internals outside the agent workspace. Check out only the failing snapshot; prevent retrieval of upstream fixes through Git history, internet access, caches or helper tools. Record any access that cannot be isolated.

Establish three controls: the original failure appears, the reference fix passes the intended regression test, and a no-change patch still fails. Where practical, a plausible wrong patch should fail too. Review whether tests encode the actual stated requirement and accept semantically valid alternate fixes. The test must discriminate behavior, not exact patch text or root-line agreement.

**Acceptance:** reproducible receipts and an independently interpretable oracle. If environment setup fails, classify infrastructure failure; it is not evidence that an agent lacks coding ability. Synthetic reduced examples may aid diagnosis but cannot replace the real task in the reported result.

## Cycle R2 — challenge the failure with a strong baseline

Pin exact available model versions and agent releases at execution time. Use documented, competent settings and sufficient tool instructions. Include a frontier agent with appropriate runtime tools, the official Gemma baseline if compatible, and the nearest specialist system. Published historical model names are not substitutes for current baseline execution.

Use approximately two hours for configuration and prompt review, five for capped runs, three for trace analysis and independent assessment, and one for closeout. Repetitions estimate within-task variability; they do not create independent tasks. If one simple instruction or supported tool resolves the failure reliably, record a baseline correction rather than inventing a new mechanism.

**Acceptance:** full attempts including failures, unchanged patches, timeouts and tool errors; a failure taxonomy with counterevidence. Separate observed behavior (“no discriminating experiment executed”) from inferred cause (“the model anchored on a hypothesis”). Classify missing information, tool access, experiment choice, hypothesis generation, patch synthesis and evaluator defects separately.

No baseline may be intentionally weakened by removing normal context or tools. If a commercial tool is unavailable, use a documented substitute and narrow the claim. Do not present that comparison as beating the commercial system.

## Cycle R3 — minimal mechanism and causal ablations

Implement only after R1–R2 pass. For F01, the minimal mechanism is a bounded experiment constructor/selector, not a general chat platform. Define supported interventions, legality checks, observations and stopping conditions before coding. No handcrafted answer mapping, task identifier dispatch, embedded reference patch, or manually supplied true explanation may enter autonomous evaluation.

Allow roughly one hour for specification, five for implementation, three for component and integration validation, two for comparison, and one for documentation. A longer implementation needs another cycle with explicit unfinished status.

Compare four core configurations:

| Model | Ordinary strong harness with same tools | Harness plus proposed mechanism |
| --- | --- | --- |
| Gemma | G0 | G1 |
| Frontier model | F0 | F1 |

Add the nearest specialized method and these ablations: direct instruction to design discriminating experiments, random legal experiments, coverage-guided selection, and hand-supplied hypotheses as an explicitly labeled oracle upper bound. For runtime debugging, assess InspectCoder and DebugHarness explicitly, adapting only where their supported task domains permit a faithful comparison. Match observed information, compute opportunities and total budget. Account for experiment generation, instrumentation, execution, summarization and model inference—not just final patch tokens.

Interpretation matters: G1>G0 shows a Gemma improvement; G1>F0 shows a system comparison; F1>G1 means the mechanism may help stronger models more. None alone establishes a Gemma-specific capability. The method can be useful without proving that Gemma is generally smarter.

**Acceptance:** mechanistic evidence plus improved independently judged repair outcomes. Entropy reduction, explanation quality and confidence are secondary diagnostics. Reject if gains come entirely from extra tools, extra compute, answer leakage or a manually curated hypothesis set.

## Cycle R4 — unseen tasks and decision

Before further tuning, freeze the mechanism, task selection, primary endpoint and analysis. Use an independent holdout with repository or bug-family separation. Tasks already inspected in this study belong only to development. For generated variants, split their parent bug family together; superficial renaming does not remove contamination.

Allocate a cycle to dataset/oracle audit, capped evaluation, analysis and a decision. Large evaluations may span multiple cycles; an underpowered pilot does not become confirmatory because the timebox ended.

**Adoption requires all of the following:** valid real tasks, persistent baseline failures, an explanatory ablation, practically meaningful improvement with uncertainty, a narrow distinguishing operation surviving prior-art review, and a feasible path into the competition harness. A failed novelty gate may still justify an engineering baseline, but not the advertised novel contribution. Record reject/revise decisions as prominently as positive results.

## Statistical specification

### Primary endpoint and estimand

For repair task i, define Y=1 only when the submitted patch builds, satisfies the independent task oracle, passes the declared regression checks and stays within budget. Retain all eligible sampled tasks in the main denominator. Specify a separate policy for invalid tasks before evaluating methods and report every exclusion with reasons. Do not silently remove difficult timeouts.

For paired binary outcomes, let D_i=Y_method,i - Y_baseline,i and estimate:

\[
\widehat\Delta=\frac{1}{n}\sum_{i=1}^{n}D_i.
\]

If tasks are independent, D is in {-1,0,1}, q=P(|D|=1), and Delta=E[D], then Var(D)=q-Delta^2. Thus Var(Delta_hat)=(q-Delta^2)/n under those assumptions. Use an exact paired test such as McNemar for an appropriate single-run binary comparison; with repeated runs and shared repositories, analyze paired task summaries and use repository-level resampling or a justified hierarchical model. Do not treat seeds as independent repositories.

A rough normal-approximation planning calculation is:

\[
n\approx (z_{1-\alpha/2}+z_{1-\beta})^2
\frac{q-\Delta^2}{\Delta^2}.
\]

For illustrative q=0.30, Delta=0.10, alpha=0.05 and target power about 0.80, using 1.96 and 0.84 gives n≈227.36, rounded up to 228 independent pairs. This is neither a guaranteed power calculation nor a requirement to run 228 tasks regardless of budget. Estimate discordance in the pilot; exact tests, clustering, multiple comparisons and exclusions change requirements. With too few independent repositories, even a bootstrap interval may be unstable. Report that limitation.

Predeclare one primary hypothesis and a practically meaningful effect. Correct confirmatory multiple comparisons, for example with Holm's procedure. Keep exploratory subgroup discovery separate. Do not repeatedly peek and stop at significance; use a fixed design or a specified sequential method with valid error control.

### Reliability claims

Zero observed failures do not establish zero risk. For n independent identically distributed Bernoulli trials with zero failures, the one-sided 95% exact upper bound on failure probability is:

\[
p_{upper}=1-0.05^{1/n}.
\]

At n=300 this is approximately 0.009936, or 0.994%. Correlated schedules or test inputs invalidate treating all runs as independent. Formal guarantees require a declared model and proved premises; test results remain empirical evidence.

### Performance tasks

For F04, correctness is a gate before timing. Use paired measurements with warmup policy, randomized order, documented hardware contention, compiler/build options and robust uncertainty. Define the workload distribution in advance. A possible aggregate is the weighted log-speedup L=sum_j w_j log(t_base,j/t_patch,j), with nonnegative weights summing to one; exp(L) is its geometric summary. Also report tail slowdowns and invalid patches. An average can conceal a disastrous subgroup regression.

Cross-machine tests measure portability; they must not quietly alter the target deployment distribution after seeing results. A reference patch that does not improve the declared workload is an oracle-quality issue requiring review, not automatic agent success.

## Mathematical and implementation assurance

For the finite selector in document 15, exhaustively compare optimized selection with brute force on small instances. Test identical hypotheses, empty consistent sets, unavailable separating experiments, noisy or contradictory outcomes, invalid schedules, zero/negative costs, and budget exhaustion. These tests validate the declared component, not arbitrary software correctness.

Use explicit typed evidence objects for observation versus prediction, measured versus estimated cost, and supported versus counterfactual interventions. Preserve raw observations for auditing. Numerical routines need stability checks; probabilities must normalize without silently concealing invalid likelihoods. Any proof must name its exact assumptions and tie them to implementation checks or openly unverified premises.

For concurrency, a bounded scheduler can establish only the explored or formally modeled scope. For numerical work, a mathematical derivation must distinguish exact arithmetic from floating-point execution. No production-readiness or absolute-correctness claim follows from a successful demo.

## Runtime and competition gate

Use the verified harness rather than assume arbitrary tool installation is allowed. The earlier record in document 11 gives a twelve-hour aggregate code-track budget including setup. If there were 120 tasks, 43,200/120 gives 360 seconds per task before overhead; the task count is an assumption, not a guaranteed organizer allocation. A long vendor debugging session is not evidence of feasibility under that budget.

Measure startup, model loading, instrumentation and tail task cost. If experiment selection helps only outside permitted tools or consumes too much runtime, either restrict it to a supported subset with an evidence-based policy or reject code-track fit. Paper merit and code-score value must be assessed separately. Reverify official rules before submission work.

## Mandatory cycle closeout

Update this protocol and document 12 after each actual cycle. Record: objective; commits and environment; task manifest; exact model/harness versions; prompts and budgets; all run receipts; baseline and intervention outcomes; uncertainty; ablations; proof assumptions; infrastructure failures; novelty findings; competition compatibility; accepted/revise/rejected decision; remaining unknowns; and the next bounded deliverable.

The initial pilot closes as **reproduction and baseline challenge complete; product promotion rejected on available evidence**. Later mechanism comparisons and holdout validation remain pending and unjustified for the solved case. This is not a claim of an implemented novel method, an experimentally superior Gemma agent, a full engineering phase, or a guaranteed competition result.
