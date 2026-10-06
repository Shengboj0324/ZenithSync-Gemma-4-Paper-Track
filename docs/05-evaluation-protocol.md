# Evaluation protocol and statistical analysis

The evaluation must distinguish three possibilities: the method fixes more issues, it saves useful resources, or it merely changes which failures occur. Freeze this protocol before the final evaluation. No task-level experiments have been run in this planning round.

## Data validity before model comparison

The official development set and its base snapshots are described in [competition facts](01-competition-facts.md). Organizer comments indexed on [Ryan Holbrook's discussion page](https://www.kaggle.com/ryanholbrook/discussion) report public-task environment failures and reasoning-token handling changes. These are warnings to validate the local environment, not a claim that every current task is broken or every fix is deployed. Record the exact harness version and direct incident links in the next round.

For each candidate task, an evaluator isolated from the model should establish:

1. The repository is at the recorded base commit and setup succeeds under the pinned environment.
2. The authorized evaluator reproducer fails before the reference fix for the expected behavioral reason, rather than dependency failure or test collection failure.
3. The reference fix makes the intended tests pass and does not violate the declared regression-test policy.
4. Repeating the checks gives consistent outcomes. Quarantine flakiness under a prespecified retry limit.
5. Graph nodes and source spans align with the base snapshot; embeddings align with their node IDs. Treat a 256-dimensional vector as an opaque feature until its generation method is documented.

Define environment-based exclusions before seeing treatment outcomes. Keep an exclusion manifest with reason, version, and evidence. Never exclude a task because the proposed system fails it. Report the original cohort size, audited eligible size, evaluated size, invalid-environment count, and model failure count separately.

## Split design

The standard resource plan provisionally allocates 20 public tasks to a pilot, 29 to development, and 80 to an untouched local holdout. These counts sum to 129 but are targets, conditional on auditing and grouping. Group tasks sharing a base commit, issue family, backport, duplicate fix, or near-identical source change; group preservation takes precedence over exact counts. Stratify feasible groups by repository and date without consulting method outcomes.

Pilot and development data are not confirmatory. Select prompts, retrieval budgets, weights, and baselines using only those data. If fitting a controller, split development groups again into fitting and calibration; with so little data, a simple fixed controller is the default. A learned controller needs additional authorized training tasks and a new resource estimate.

For generalization, freeze at least 60 external tasks from several repositories absent from development, ideally six or more. Candidate source: [SWE-bench-Live](https://swe-bench-live.github.io/). Audit licenses, dependencies, duplicates with public tasks, and model-training contamination risk. A recent benchmark is not proof of uncontaminated model pretraining. Record task timestamps, benchmark revision, and any known model training cutoff; unknown cutoff remains unknown.

A same-repository public holdout demonstrates transfer to other issues, not to other repositories. Use the external cohort as the generalization evidence. If an external cohort is impossible, narrow the paper's quality claim and report leave-one-repository-out development diagnostics without treating four repositories as a large population sample.

## Prevent reference leakage

| Agent may access | Evaluator-only material |
| --- | --- |
| Authorized issue text and pre-fix repository | Gold fix and acceptance-test patch |
| Permitted hints, if equally available to all methods | Hidden expected outcomes and aggregate grading feedback |
| Graphs/embeddings derived from that snapshot | Future commits, linked solution PRs, post-fix graph text |
| Tests already present at the base commit and tests it writes | Holdout outcomes used to choose a new prompt or controller |

Strip prohibited material from the runtime rather than merely telling the model to ignore it. Put grader files outside the accessible mount. Freeze labels before analysis and compare file-access/tool logs with the allowed schema. Audit caches and repository memory for cross-task leakage. Agent-written tests can guide repair, but they do not replace independent acceptance tests.

## Baselines and matched conditions

| ID | System | Role |
| --- | --- | --- |
| B0 | Official starter or minimal fixed editor with ordinary source search | Sanity and deployment baseline |
| B1 | Lexical plus semantic retrieval under fixed token budget | Tests whether graph structure is necessary |
| B2 | Tuned fixed graph traversal with the same editor | Primary comparator for H1 |
| B3 | Faithful LocAgent or RepoGraph integration where feasible | Closest-work challenge; otherwise label the adaptation and exact differences |
| P | Reliability-aware bundle selection with fixed editor | Proposed method |

The standard confirmatory run compares B1, B2, and P; B0 and B3 enter development. If B3 materially outperforms B2 during development, promote B3 to the primary comparator and freeze that choice before holdout. Do not keep a weak B2 primary just to simplify the win. Preserve at least one graph and one graph-free comparator in the confirmatory matrix.

Fix model checkpoint, quantization, sampling settings, maximum output length, editor/test logic, hardware, environment, available tools, and total budget. Give baselines a comparable tuning budget and document it. A baseline receiving fewer candidate sources or fewer retries is not matched. Count reliability verification and bundle construction in P's cost.

Two experiments answer different questions:

- **Equal-budget efficacy:** all methods receive the same caps; compare issue resolution and actual resources used.
- **Efficiency frontier:** vary prespecified caps and plot resolved fraction against cumulative tokens and wall time. Include preprocessing and rerun cost; show both cold and amortized graph costs.

Changing graph representation and controller together can confound attribution. Include a same-node-text, structure-removed condition. Hold candidate snippets fixed when testing topology serialization; separately test structure's effect on candidate discovery. Distinguish those interventions in captions.

## Minimum ablations

| Intervention | What it isolates | Interpretation if performance is unchanged |
| --- | --- | --- |
| Set all valid reliability weights equal | Reliability mechanism | No evidence that reliability weighting contributes |
| Select individual snippets instead of bundles | Complementarity handling | Bundling may be unnecessary |
| Remove graph edges while preserving candidate text | Explicit structural information | Benefits may arise from text or candidate selection |
| Replace adaptive control with fixed budget, if implemented | Value of adaptivity | Drop the controller or restrict its claim |
| Remove supplied embeddings, retaining lexical seeds | Dependence on competition-specific assets | A gain suggests a more portable method; a loss defines the dependency |

Run a development ablation pilot first. Confirm only the ablation central to the final claim on fresh tasks; the small development matrix is exploratory. Do not present a 20-task ablation as definitive mechanism identification.

For H3, perturb retrieval graphs, not source code or the grading target. Prespecify 0%, 10%, and 30% relation deletion, and a separate endpoint-rewiring condition. Preserve node text and match edge count where possible. Use seeded perturbations, distinguish random from targeted corruption, and report impossible-to-rewire cases. Synthetic corruption measures sensitivity to that intervention; it does not estimate the natural prevalence of graph errors.

For clean outcome `Y_m(0)` and corrupted outcome `Y_m(ρ)`, estimate the interaction

\[
I(\rho)=[\bar Y_P(\rho)-\bar Y_P(0)]-[\bar Y_{P\mathrm{-blind}}(\rho)-\bar Y_{P\mathrm{-blind}}(0)].
\]

Positive `I` means P loses less performance than its reliability-blind variant in that comparison. Pair by issue and perturbation seed. Inspect the clean baseline too: a system already failing nearly everything has little remaining performance to lose.

## Metrics and denominators

Primary: `resolved / all prespecified eligible attempted tasks`. Count agent crashes, timeouts, no patch, and malformed patches as unresolved. Infrastructure failures must follow a uniform blinded retry policy; publish their count and a sensitivity analysis counting unresolved infrastructure cases as failures. Never silently reduce the denominator.

Secondary: cumulative input/output tokens, wall time, device-hours, peak per-device memory, invalid tool calls, regression failures, context-source provenance errors, and setup time. Report medians and tails as well as totals. Cost per resolved issue is `total cost / total resolved`, including all failures; undefined when none resolve. Do not use success-only runtime as the sole efficiency metric.

Localization diagnostics may use patch-derived locations in the evaluator only. Report file recall and all-relevant-file recall at a declared `k`. Reference edit locations are imperfect proxies: alternate valid patches can touch different locations. Localization is not the final repair metric.

## Statistical plan

For one frozen run per issue, let `d_i=Y_Pi-Y_Bi∈{-1,0,1}` and `Δ̂=mean(d_i)`. Report the paired effect and uncertainty. Let `b` count P-only wins and `c` baseline-only wins. The two-sided exact McNemar test uses the discordant total:

\[
p=\min\left(1,2\sum_{j=0}^{\min(b,c)}{b+c\choose j}2^{-(b+c)}\right).
\]

If `b+c=0`, set `p=1`. This test assumes independent paired units; duplicates and repository correlation weaken that assumption. Pair bootstrap intervals over issues describe the sampled issue cohort. For broader claims, report per-repository effects and repository-cluster sensitivity; six repositories still provide limited cluster inference. Do not claim universal significance from an issue-level p-value alone.

Repeated seeds are nested in issues. Average per-issue outcomes or use a hierarchical analysis/bootstrap; never count three runs on one issue as three independent issues. A primary fixed seed provides a low-cost comparison; rerun a prespecified subset with additional seeds for stability, and report that subset rule.

Prespecify one primary efficacy comparison and one primary budget. Use Holm adjustment across a declared family of confirmatory secondary tests. Budget curves, subgroups, and unplanned ablations are exploratory unless separately registered. Do not keep sampling until a desired p-value appears.

### Numerical checks with invented observations

If a baseline solves 39/129 and P solves 52/129, their rates are 30.23% and 40.31%. The corresponding Wilson 95% intervals are approximately `[22.97%,38.63%]` and `[32.24%,48.94%]`. These overlapping marginal intervals do not determine the paired comparison.

With `b=23`, `c=10`, 29 both-correct cases, and 67 both-wrong cases, those marginals are consistent. The paired gain is `13/129=10.08` percentage points, with exact McNemar `p≈0.03508`. Different discordance patterns with the same marginals can change the evidence. These are illustrative numbers; they are not ZenithSync results.

Let `q=P(|d_i|=1)` and true gain `δ=E[d_i]`. Then `Var(d_i)=q-δ²`. An approximate planning calculation for two-sided 5% testing and 80% power is

\[
n\approx(1.96+0.8416)^2\frac{q-\delta^2}{\delta^2}.
\]

For assumed `q=.30`, this gives about 228 independent tasks for a 10-point gain and 935 after rounding up for a 5-point gain. This is a normal-approximation planning heuristic, not exact McNemar power; compute exact/simulated power after the pilot estimates discordance. Clustering, multiple comparisons, and unequal repositories increase uncertainty. Even all 129 public tasks would not guarantee useful power, and the actual untouched holdout is smaller.

### Claim decisions

| Claim | Evidence gate | Wording if the gate fails |
| --- | --- | --- |
| Better repair | Positive paired confidence bound for the primary comparison, coherent external evidence, no unequal-budget explanation | Report estimated difference and uncertainty; no superiority claim |
| Same-quality efficiency | Prespecified noninferiority margin, e.g. 3 percentage points, with lower one-sided 95% bound on `Δ` above `-.03`, plus prespecified meaningful cost reduction, e.g. 20% | “Lower measured cost with unresolved quality tradeoff” |
| Robustness mechanism | Prespecified interaction favoring P, supported by corruption and clean results | Describe observed sensitivity; no causal robustness claim |
| Generalization | External repositories with frozen settings and visible per-repository outcomes | Restrict conclusions to tested repositories/cohorts |

Margins and cost thresholds are planning choices to justify before holdout, not official thresholds. A nonsignificant difference is not equivalence. With small samples, the honest result may be inconclusive.

## Required experiment record

Each run needs: run ID; cohort/split; task/repository/base commit; task-source and license reference; model/tokenizer/harness/config hashes; method; seed; graph revision and perturbation seed; start/finish times; setup/model/tool/grade durations; cumulative tokens; peak memory; patch hash; grader result; failure class; and immutable log location. Record failed runs too.

Use separate configuration records for selection weights, candidate caps, graph serialization, prompts, stopping rule, and regression policy. The final paper tables must be generated from the frozen per-task records with a documented aggregation rule. No values should be copied manually from a preferred notebook run.
