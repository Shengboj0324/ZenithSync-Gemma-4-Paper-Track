# Technical proposal and mathematical checks

The proposed system chooses source evidence before asking a fixed Gemma repair policy to edit code. The scientific question is whether reliable structural evidence improves the allocation of a limited context and execution budget. All algorithms here are specifications for a later implementation round, not implemented capabilities.

## Task and constraints

For issue `x`, repository snapshot `R`, and graph `G=(V,E)`, let policy `π` produce a patch after a trajectory of retrieval, editing, and local testing. Let `Y(π,x)` be one if the independent evaluator accepts the final patch and zero otherwise. The practical objective is

\[
\max_\pi\;\mathbb{E}_{x\sim D}[Y(\pi,x)]
\quad\text{subject to}\quad
T_x\le B_T,\quad L_x\le B_L,\quad M_x\le B_M.
\]

`T` is elapsed task time including setup and controller overhead; `L` is cumulative model token usage, including repeated history and tool output consumed by the model; `M` is peak device memory. Add an instantaneous context-window constraint separately. A context window is not a cumulative-token allowance. Baselines must obey the same feasible region.

The distribution `D` is unknown. Results on a frozen development-derived holdout and external tasks estimate behavior on those cohorts, not hidden Kaggle performance or universal developer productivity.

## Evidence construction

Use lexical and supplied semantic retrieval to generate candidate symbols from the issue. Obtain a bounded structural neighborhood using the actual harness tools once verified. Default pilot settings are 20 lexical candidates, 20 semantic candidates, and at most two graph hops, with deduplication; these are tuning proposals, not tested values. Compare graph budgets at one and two hops during development.

Each evidence item carries repository commit, file path, symbol or source span, source hash, relation type, graph provenance, and retrieval cost. Source code at the frozen commit is authoritative when graph text disagrees. Static calls do not establish runtime reachability in Python; verified existence is weaker than verified execution behavior.

Define reliability levels operationally:

| Level | Available evidence | Permitted use |
| --- | --- | --- |
| Direct | Symbol/span and relation can be checked in snapshot syntax | Strong structural cue, still not a runtime proof |
| Indirect | Graph relation exists but static resolution is ambiguous | Candidate expansion with explicit uncertainty |
| Invalid | Missing node, stale span, wrong commit, malformed relation | Exclude structural assertion; permit independent lexical fallback |

Represent reliability numerically only as a heuristic weight until calibration data supports a probability interpretation. Initial weights may be `1`, `0.5`, and `0`, frozen before holdout evaluation; report a sensitivity analysis. Never call them probabilities that a patch is correct.

Verification checks whether the asserted relation is supported by the recorded source span and the parser's documented resolution rules. It must not quietly use acceptance tests or reference fixes. Missing edges are different from false edges: provenance checks can reject an unsupported relation but cannot detect every omitted dependency. Predict a larger benefit against detectable stale/incorrect relations than against arbitrary deletion, and test that distinction. Always permit a bounded lexical fallback; freeze its allocation on development and give baselines the same total allowance.

An evidence bundle contains a small source relationship that is meaningful together: caller and callee, overridden and base method, configuration reader and affected consumer. A bundle includes its relevant relation description. Candidate bundles are fixed before selection in the simplest version. This preserves complementary evidence that node-by-node selection might miss.

## A tractable selection objective

Let `U` be a finite set of issue-relevant evidence targets generated from issue terms, candidate symbols, and allowed source analysis. They are proxies for information needs, not ground-truth fix locations. Let `w_u≥0` be fixed weights normalized to sum to one. For candidate bundle `b`, define fixed coverage `a_ub∈[0,1]` from lexical/semantic relevance multiplied by the bundle's reliability weight. All normalization and combination details must be frozen from development data.

A concrete first version uses seed symbols as `U`. Rank lexical and available semantic candidates independently, then set `w_u` proportional to the sum of reciprocal ranks `1/(60+rank(u))`, contributing zero for a missing rank. Normalize after deduplication; the constant 60 is a proposed fixed setting, not a theorem. Use the harness's semantic search instead of inventing a query encoder for supplied embeddings. If that interface is unavailable, declare a lexical-only variant.

For an initial coverage kernel, use `k(u,v)=exp(-d(u,v)/τ)` when a path of at most two edges exists in the explicitly declared source-checked relation projection, `k(u,u)=1`, and zero otherwise. Start with `τ=1`. Define `a_ub=r_b max_{v∈b}k(u,v)`, where `r_b` is the minimum reliability of the bundle's asserted relations; a standalone valid source snippet has reliability one. Keep edge directions in the serialized evidence even if the retrieval-distance projection permits traversal both ways. Invalid bundles can yield valid standalone snippets, but must not preserve the rejected relation. This fully specified prototype favors relevance around ranked seed symbols; it can miss a distant fix and must be compared against the simpler retrievers. Any learned kernel is a separate extension.

For selected bundle set `S`, define

\[
F(S)=\sum_{u\in U}w_u\max_{b\in S}a_{ub},\qquad F(\varnothing)=0.
\]

Choose `S` under a token reservation:

\[
\max_{S\subseteq\mathcal B} F(S),\qquad
\sum_{b\in S}c_b\le B_{\mathrm{evidence}},\qquad c_b>0.
\]

`c_b` counts the complete serialized bundle with delimiters under the actual tokenizer. Conservatively charge duplicated spans to every bundle in the optimizer; deduplicate in the final prompt and measure actual usage. This makes the planning cost additive, although it can waste capacity. A formulation charging the union of overlapping spans is different and requires a different approximation argument. Recount the complete serialized prompt: reserve system text, issue text, output tokens, tool messages, and tokenization boundary overhead. Reject or repack any over-budget serialization.

### What can be proved

For `A⊆B` and `b∉B`, write `m_u(A)=max_{a∈A}a_ua`. Since `m_u(A)≤m_u(B)`,

\[
\Delta(b\mid A)
=\sum_u w_u\max(0,a_{ub}-m_u(A))
\ge\sum_u w_u\max(0,a_{ub}-m_u(B))
=\Delta(b\mid B).
\]

Thus `F` is normalized, monotone, and submodular for fixed nonnegative weights and coverages. This is a standard coverage-style result, not a new theorem. It explains diminishing returns in the surrogate, not in repair success.

With equal costs and a cardinality limit `k`, ordinary marginal-gain greedy obtains at least `1-(1-1/k)^k≥1-1/e` of the best surrogate value: after `i` selections, one of at most `k` optimum elements has marginal value at least `(OPT-F(S_i))/k`; recursively the remaining gap shrinks by at most `1-1/k`. This proof relies on fixed candidate values and the cardinality setting.

For unequal costs, the pilot will use feasible marginal-gain-per-cost selection and compare its result with the best feasible singleton. **Do not attach the cardinality guarantee to this heuristic.** A classical knapsack approximation exists, but invoking it requires implementing and checking the corresponding algorithm, such as the partial-enumeration construction in [Sviridenko 2004](https://www.sciencedirect.com/science/article/pii/S0167637703000622). It may not be worth the runtime. Start with the simpler measured heuristic and exhaustively check small fixtures against the true optimum.

### What cannot be proved from this formulation

The graph may omit the correct location, similarity may be misleading, and a language model can be distracted by additional context. Therefore monotonicity of `F` does not imply monotonicity of `Y`. Actual repair success can require complementary evidence and need not be submodular.

Counterexample: let two snippets `a,b` jointly expose a bug, with `Y(∅)=Y({a})=Y({b})=0` and `Y({a,b})=1`. Then the gain from adding `b` is zero at the empty set and one after seeing `a`, violating diminishing returns. Bundles place a selected kind of complementarity inside an item; they do not represent all possible program dependencies or prove approximation guarantees for repair.

Likewise, replacing `F` with a worst-case minimum over graph variants is not automatically submodular. On ground set `{a,b}`, let `F_1(S)=1[a∈S]` and `F_2(S)=1[b∈S]`. Each is modular, but `min(F_1,F_2)` has the same complementary pattern. A fixed nonnegative weighted average of submodular scenario objectives remains submodular; the minimum generally does not.

## Worked selection example

Take targets with weights `(0.5,0.3,0.2)` and bundles:

| Bundle | Coverage across the three targets | Token cost | Value alone |
| --- | --- | --- | --- |
| A | `(1,0,0)` | 100 | 0.50 |
| B | `(0.6,1,0)` | 100 | 0.60 |
| C | `(0,0,1)` | 50 | 0.20 |

At a 150-token budget, greedy chooses B first (density 0.006), then C (0.004), obtaining 0.80. A+C gives 0.70; A+B is infeasible. Enumerating all eight subsets confirms B+C is optimal for this fixture. That confirms arithmetic and a toy decision, not a software-repair result or general optimality.

## Adaptive extension and its cost

Default version: one evidence-selection stage, a fixed editor, and a fixed allowance for local tests and repairs. Implement this first to isolate the contribution.

Only after it works, consider actions `a∈{expand, read, test, edit, stop}` at state `s`. A decision-theoretic score is

\[
U(a\mid s)=\mathbb E[V(s')\mid s,a]-V(s)-\lambda_T\mathbb E[\Delta T]-\lambda_L\mathbb E[\Delta L],
\]

where `V` is expected eventual repair success under the remaining policy and budget. The multipliers have units of success probability per second and per token. For illustrative values `ΔV=.04`, `ΔT=20`, `ΔL=800`, `λ_T=.0005`, `λ_L=.00001`, the net is `.022`. These inputs are invented for a dimensional check, not calibrated estimates.

The counterfactual benefit of an unchosen action is unobserved. A learned controller would need development-state branching with randomized action assignment or another justified design, grouped by issue and repository; all branching cost belongs in the training budget. A small task pool cannot support a high-dimensional reliable value estimator. Default to a transparent capped rule if calibration is weak.

Stopping because a fitted mean gain is negative is a heuristic; stopping with a lower confidence bound is conservative but not globally optimal. One-step gains can miss two-action complementarity. A stochastic policy would require stronger assumptions for adaptive-submodularity guarantees; see [Golovin and Krause](https://arxiv.org/abs/1003.3967). Do not infer those assumptions from the static proof above.

## Optional training direction

If later evidence shows tool-use mistakes dominate retrieval errors, consider LoRA supervised training on authorized development trajectories. Define completion-only loss

\[
\mathcal L_{\mathrm{SFT}}(\theta)=-\sum_i\sum_{t\in A_i}\log p_\theta(y_{it}\mid y_{i,<t},x_i),
\]

where `A_i` contains assistant action/output tokens, excluding evaluator labels and protected reference solutions from inference input. Preserve task-level splits before generating trajectories. Include valid failure/recovery examples rather than only easy successes. Hold the retrieval intervention fixed when estimating the incremental effect of training.

A constrained RL objective could penalize execution cost and invalid actions, but it would introduce another causal variable and require substantially more rollouts. It is outside the default paper scope. Parameter-efficient training is not evidence of low total training memory or low experimentation cost.

## Planned implementation boundary

The later implementation should separate: snapshot/provenance loading; evidence candidates; reliability checks; bundle selection; fixed model execution; sandboxed patch validation; independent grading; and analysis. Use content hashes and explicit schemas between these stages. Never expose `patch`, `test_patch`, evaluator output, or future commits through the agent's filesystem or retrieval index.

Required early engineering checks include malformed graphs, stale source, nonpositive costs, duplicate candidate IDs, cycles, disconnected symbols, oversized bundles, tokenizer mismatch, exhausted budgets, invalid tool calls, and deterministic tie-breaking. Syntax validation alone is not correctness. Failed local tests remain evidence of failure even when the patch parses.

The retrieval stage should stop after its reserved allowance, emit selected source with provenance, and pass control to the editor. If selection yields no admissible bundle, use the declared lexical fallback and log the reason. If the fallback also fails, emit no-evidence status and let the unchanged editor policy decide within its remaining budget. Never manufacture a graph edge or silently grant extra model calls to rescue P.
