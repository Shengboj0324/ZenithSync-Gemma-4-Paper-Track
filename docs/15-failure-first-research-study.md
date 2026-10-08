# Failure-first selection study

**Subsequent evidence:** [R1 reproduction results](18-reproduction-cycle-results.md) now supersede the replication-pending status below for the Raft case. The defect reproduced, but three fresh ordinary baseline attempts repaired it; no product promotion followed. The remainder of this document preserves the preceding literature study.

Research date: October 7, 2026. Status: literature, product-documentation, and published-trace inspection completed for the scope below; local replication not performed. This study supersedes earlier recommendations to select a product before demonstrating a persistent failure. It does not establish a new algorithm, Gemma superiority, or universal correctness.

## Decision

Investigate **agents committing to the wrong explanation when several causes fit the visible symptom** first. Use asynchronous application bugs as the first manageable reproduction domain, with distributed-system cases as possible later generalization. The investigation is justified by concrete traces, not by a claim that frontier agents cannot debug.

The research question is: **after both agents receive the same runtime tools, can automatically constructed experiments that separate competing explanations improve correct repair per unit cost?** This is a question to falsify, not an adopted product. Generic causal debugging, replay, schedule exploration, and information-gain selection already have substantial prior art. A product built from those ingredients is not automatically differentiated enough for this project.

Keep cross-layer performance optimization as the second investigation. Put long-term code evolution behind an evaluator-validity gate. Do not choose numerical repair or an agent-trajectory judge as the lead without stronger task-level evidence and a distinct operation.

## What the investigation actually covered

The search followed five failure families across research manuscripts, benchmark artifacts, published agent attempts, vendor technical documentation, firsthand discussion, and news. Queries combined agent failure, runtime debugging, distributed repair, code erosion, numerical bugs, performance optimization, causal intervention, and experimental design. Papers were examined beyond their abstracts where indicated in the [source ledger](16-failure-evidence-and-source-ledger.md). The browser was used to inspect a task dashboard and expand an actual failed baseline trace.

This is a broad, bounded study, not a review of the entire internet. X search reached a login wall. Three YouTube pages were located, but transcript export failed; their audiovisual content is not evidence in this report. Forum comments identify possible pain points but do not establish incidence or capability limits. Vendor benchmarks carry selection and evaluator risks. Negative evidence and benchmark audits are included rather than dismissed.

The currently available evidence has three distinct levels: a published aggregate, an inspectable published attempt, and an independently reproduced attempt. We reached the second level for one web-debugging case. None of the candidates has reached the third level here. Older model failures do not establish failures of today's strongest configurations.

## Comparison and selection

These are ordinal research priorities, not fabricated numerical scores.

| Priority / family | User-visible failure | Evidence strength in this study | Existing competition | Decision |
| --- | --- | --- | --- | --- |
| 1. Ambiguous runtime causes | A plausible patch addresses the displayed error but leaves the triggering sequence intact | Published trace inspected; additional systems cases in papers and company experiment | Replay, Undo, Antithesis, ConFixAgent; established experimental design | Reproduce with equally equipped agents; novelty unproven |
| 2. Cross-layer performance | A feature works but remains slow because the expensive operation is elsewhere | Concrete optimization case and quantitative published comparisons | PerfAgent, profilers, optimization agents and benchmarks | Secondary; ordinary profiling loop is already occupied |
| 3. Iterative feature evolution | Successive changes regress earlier behavior or make later changes harder | Research benchmark; causal interpretation and evaluator validity contested | Existing long-running harnesses, regression testing, architectural planning | Audit tasks before method development |
| 4. Scientific/numerical failures | Outputs look plausible but violate numerical or scientific requirements | Relevant papers; no clean current-frontier repair trace reproduced | Herbie, numerical analyzers, scientific coding benchmarks | Reserve domain, not selected |
| 5. Agent mistake localization | An agent repeats an unproductive approach or cannot identify its first consequential error | Recent trace-judging research | Specialized trajectory judges and inference-time selection | Useful baseline component; weak standalone differentiation |

### 1. Ambiguous runtime causes

The AB-9 task and inspected attempt are recorded precisely in document 16. Our inference is that an attractive explanation can survive source inspection because the agent has not performed an experiment that distinguishes it from a competing explanation. This is a hypothesis about the trace, not a demonstrated cognitive diagnosis or proof of the application's root cause.

Distributed systems provide harder variants. DDBench studies 60 historical bugs across 13 repositories. It reports average repair improvement from 32.6% to 50.6% with curated operational context, but examples also show context misleading a strong agent. The evidence motivates studying what information an agent requests, not assuming more context always helps. Curated context is an oracle-assisted condition whose collection cost must be counted in an autonomous system. [DDBench, evaluation and case studies](https://arxiv.org/html/2608.14863v1).

**Why the obvious product fails our novelty test:** Replay and Undo already expose execution evidence to coding agents; Antithesis supplies deterministic simulation and AI-assisted workflows. ConFixAgent already combines concurrency detection, happens-before context, LLM repair, and iterative checking. Its discussion explicitly limits overall soundness/completeness despite ambitious introductory wording. A replay wrapper, a causal graph, or an LLM plus model checker is insufficient differentiation. [Replay tools](https://docs.replay.io/reference/replay-mcp/tools), [Undo AI](https://docs.undo.io/UndoAI.html), [Antithesis](https://antithesis.com/docs/ai/overview/), [ConFixAgent](https://arxiv.org/html/2604.05753v1).

**Further overlap found in the final check:** InspectCoder already uses interactive state inspection and reversible runtime perturbations to test hypotheses; its task setting is primarily self-repair of generated functions. DebugHarness applies hypothesis-driven live debugging and replay to native repository vulnerabilities. DoVer generates and executes interventions in agent trajectories, an adjacent domain rather than ordinary application code. Thus even active hypothesis testing, not just passive replay, is occupied. [InspectCoder, sections 2.3–2.5](https://arxiv.org/html/2510.18327v1), [DebugHarness, section 3](https://arxiv.org/html/2604.03610v1), [DoVer, sections 3–4](https://arxiv.org/html/2512.06749v1).

**Possible operation to investigate, not a cleared novelty gap:** construct an executable intervention from disagreement between hypotheses, with no human identifying the relevant variable or schedule. Test whether that operation contributes beyond both the systems above and a frontier agent instructed to do exactly this with the same tools. If the strong agent produces equivalent experiments at comparable cost, reject the product distinction. If only a hand-selected hypothesis set makes it work, the result is an oracle demonstration, not autonomy. The generic product claim “an agent that tests its explanations” is rejected now; only a narrower, demonstrably different operation could survive.

### 2. Cross-layer performance optimization

PerfAgent reports expert-matching GSO performance rising from 19.6% to 39.2% with GPT-5.1, using native-aware profiling, continued optimization, and regression feedback. Its NumPy string example exposes a bottleneck below Python. This is direct evidence for a tool-and-feedback limitation, but also a ready-made competitor. These are paper-reported historical results, not current leaderboard results or our measurements. [PerfAgent, methods, case study, and ablations](https://arxiv.org/html/2607.19653v1).

The potentially interesting residual question is performance across **unseen workload regimes**, not speed on a visible microbenchmark. An intervention would need to infer where cost behavior changes and choose informative measurements, then preserve semantics while improving a declared deployment distribution. This overlaps autotuning and Bayesian optimization; it has not passed a dedicated prior-art audit.

A separate benchmark audit found substantial dependence on machine and validity filters: only 39/102 GSO reference optimizations were valid across all four tested machines. Its high aggregate agent success involved at least one of multiple submissions, not a single universal agent. This weakens simplistic leaderboard comparisons. [Performance-benchmark audit](https://arxiv.org/html/2607.01211v1).

Reject this direction if gains disappear on held-out sizes, dtypes, layouts, or machines; if profiler feedback alone explains them; or if the competition does not reward the target behavior. Do not call a faster wrong result an optimization.

### 3. Long-term code evolution

SlopCodeBench's initial study reports low checkpoint completion and worsening structural measurements during iterative development. The strongest reported strict checkpoint score in that version is 17.2%. However, difficulty grows with accumulated requirements; complexity growth alone does not identify an agent-induced cause. [SlopCodeBench v1, evaluation and metrics](https://arxiv.org/html/2603.24755v1).

An independent public audit reports oracle defects, hidden expectations, sampling concerns, and weak links between structural scores and future outcomes. It is a working audit rather than a peer-reviewed replication, and its findings have not been reproduced here. Nevertheless, these are concrete reasons to audit the instrument before designing a solution around its score. [Audit and pinned revisions](https://raw.githubusercontent.com/kimjune01/slopcodebench-audit/main/AUDIT.md).

The necessary experiment compares continuing an existing implementation with a fresh implementation given the **same cumulative specification**, resources, tests, and dependencies. The meaningful endpoint is future feature completion without regressions. Token count, function length, and cyclomatic complexity can be secondary explanatory variables; minimizing them is not itself the product outcome. Existing harness work also addresses persistent progress and evaluation. [Anthropic harness design](https://www.anthropic.com/engineering/harness-design-long-running-apps).

### 4. Numerical and scientific correctness

InterFLOPBench evaluates classification rather than end-to-end repair and reports strong results in several categories. Its discussion raises distinctions between its labels and scientific accuracy, including silent precision loss. It is therefore evidence that oracle definitions matter, not clean evidence that strong coding agents broadly fail numerical work. [InterFLOPBench](https://arxiv.org/html/2606.31308v1).

AInsteinBench offers scientific repository tasks, but the inspected HTML did not render the detailed appendix needed to audit particular claimed failures. Its tasks and test oracles need case-level verification before adoption. [AInsteinBench](https://arxiv.org/html/2512.21373v1). Existing numerical transformation systems also narrow novelty. [Herbie](https://herbie.uwplse.org/).

This could become a strong specialist direction if we find a real algorithm change, independent high-precision or analytic oracle, and a frontier baseline that fails despite appropriate numerical tools. We do not currently have that complete package.

### 5. Failure analysis of the agent itself

Traverse/Scout studies identifying consequential mistakes in agent traces and reports advantages from a specialized small model. This supports the possibility of specialization, but also occupies much of the trajectory-judge proposal. Trace judgment is not equivalent to successful software repair. [Traverse/Scout](https://arxiv.org/html/2609.17930v1).

Use such methods as comparison components where applicable. Do not repackage an already studied verifier as the project's novel product.

## Mathematical formulation for the first investigation

The following is our proposed experimental specification. Its ingredients are established ideas; it is not a novelty claim or a theorem about real software correctness.

Let H be a finite set of executable candidate explanations and E the feasible experiments. Experiment e produces observation Y at total cost c(e). For deterministic hypotheses, h(e) predicts an outcome. After observations D, retain the consistent set:

\[
V(D)=\{h\in H: h(e_i)=y_i\text{ for every observed }(e_i,y_i)\}.
\]

A robust one-step choice minimizes the largest remaining cell:

\[
e^*\in\arg\min_{e\in E:c(e)\le B}
\max_y |\{h\in V(D):h(e)=y\}|.
\]

This has a limited but exact interpretation. If the true explanation belongs to H, predictions and measurements are correct, and the experiment partitions V into cells of maximum size m, at most m hypotheses survive. If every step can split the survivors into cells no larger than half, a single explanation is isolated within ceiling(log2 |H|) steps. Such balanced experiments may not exist, and multiple causes may need to be represented jointly. Two explanations with identical predictions over E are unidentifiable by this experiment set. No amount of resampling fixes missing observability.

For noisy observations, a Bayesian alternative maximizes expected information gain per cost:

\[
\frac{I(H;Y\mid e,D)}{c(e)}
=\frac{\mathbb E_{Y\mid e,D}
 [D_{KL}(p(H\mid D,e,Y)\Vert p(H\mid D))]}{c(e)}.
\]

LLM confidence is not a calibrated likelihood. Without justified likelihoods, use explicitly labeled heuristics or empirical predictive models and test calibration. Maintain an explicit outside-model possibility; if every hypothesis is contradicted, expand or abandon H rather than report certainty. Maximizing information is not necessarily maximizing repair success: an informative distinction may be irrelevant to the patch. Compare this selector with random experiments, coverage-guided experiments, and experiments chosen directly by the same LLM.

Sequential experimental design is already used in other agent research, including Model Discovery Agent; dynamic partial-order reduction already reduces redundant schedule exploration. Their domains and assumptions differ, but neither mathematical vocabulary is new. [Model Discovery Agent](https://arxiv.org/html/2608.09696v1), [Flanagan and Godefroid, dynamic partial-order reduction](https://escholarship.org/uc/item/47c9f29c).

### Logical back-check of intervention validity

Changing thread order, request completion order, or input representation is only meaningful when the resulting execution remains legal for the target system. Arbitrarily forcing an internal state can manufacture impossible bugs. Instrumentation can also change timing and suppress the original failure. Preserve baseline behavior, record intervention scope, and distinguish feasible executions from diagnostic counterfactuals.

A successful explanation still does not prove a successful repair. The final patch needs independent regression tests and perturbations not used to select it. A finite schedule bound or a proved local invariant must be reported with that boundary. There is no honest universal correctness guarantee for arbitrary repositories from this workflow.

## Competition and product decision boundary

The code-track assumptions in [document 11](11-code-track-and-joint-strategy.md) remain the repository's earlier verification record; rules were not newly verified in this study. External replay services, custom instrumentation, network access, or special runtimes must not be assumed available in the submission harness. A useful standalone debugging product can still be a poor code-track choice.

For a specialist affecting fraction f of evaluation tasks, improving that subset by d while losing r on other tasks gives an illustrative total change f*d - (1-f)*r. For example, f=0.10, d=0.30, r=0.02 produces only 0.012, or 1.2 percentage points. These are hypothetical values, not an estimated benchmark distribution. Measure coverage and opportunity cost before specialization.

Adopt a direction only after its actual failure survives a strong baseline, its mechanism beats the nearest alternative within budget, its distinctive operation survives a focused prior-art audit, and its target tasks fit the competition. Until then, the correct output is a research decision and a falsifiable protocol—not a claim that we have found an agent capability others lack.
