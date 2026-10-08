# Change Compiler: novelty audit and replacement proposals

Research date: October 7, 2026. Status: **the candidate in document 13 does not pass the requested low-overlap gate. No replacement is adopted.** This audit supersedes document 13's provisional novelty assessment, not the repository's implementation plans. No application code, experiments, or model comparisons were executed for this audit.

## Decision

Do not promote Change Compiler into the README or implementation roadmap as a differentiated core contribution. There is substantial prior work on its central operations: combining incomplete candidates under constraints, extracting conflicts to prune synthesis, using deduction to train a generator, and propagating edits through repository dependencies. Their combination could still be useful engineering or publishable with a specific new result, but the present proposal does not establish that result.

This is **conceptual overlap**, not an allegation of copying or a finding that one existing product implements precisely the proposed pipeline. An exact end-to-end duplicate was not established. Absence of an exact duplicate in this search is not evidence of zero duplication. Adding Gemma, repository graphs, an MCP interface, or different mathematical terminology does not establish an algorithmic contribution.

The earlier assessment underweighted conflict-driven program synthesis. Neo and Concord materially weaken the proposed conflict-to-generation distinction; AbsCon additionally weakens the candidate-recombination distinction.

## Scope and method

The search covered primary research papers, author-hosted manuscripts, public implementation READMEs, vendor documentation, and publicly discoverable competition repositories/writeups. Queries included conflict-driven synthesis, deduction-guided reinforcement learning, constraint-aware candidate combination, repository change planning, constrained decoding, repair synthesis, semantic undo, checkpoint migration, and semantic tensor transformations.

Reading depth varies and is stated below. Public product descriptions establish documented capabilities, not undisclosed implementation details. Source repositories were inspected at documentation level; this was not a source-code equivalence audit. Search snippets were used to locate leads, not to establish decisive technical claims. No paid/private submissions, proprietary model internals, exhaustive patent search, or participant interviews were available. This is a technical positioning audit, not a legal novelty opinion.

The Kaggle paper-track writeup page returned no usable body text through the research interface. Therefore, the competition sample below is not a census. Entries from the separate Gemma 4 Good hackathon were excluded. Competition rules and judge weights were not newly verified in this audit; retain the existing rule-verification records and unresolved questions.

## Mechanism comparison

| Source and inspected evidence | Established mechanism | Overlap with document 13 | Remaining distinction and verdict |
| --- | --- | --- | --- |
| [Neo: Program Synthesis using Conflict-Driven Learning](https://www.cs.utexas.edu/~isil/pldi18-neo.pdf), PLDI 2018; author paper, especially conflict learning; [repository README](https://github.com/utopia-group/neo) | Derives conflicts from infeasible partial programs and generalizes them to prune synthesis search | Conflict explanations and justified exclusion of related candidate programs | Repository patch domains and a Gemma proposer differ; conflict-directed synthesis is already established. High mechanism overlap |
| [Concord: Program Synthesis using Deduction-Guided Reinforcement Learning](https://fredfeng.github.io/papers/cav20.pdf), CAV 2020; author paper | Combines a learned synthesis policy with deductive feasibility feedback and learns from failures | Using deductive conflicts to improve generation, rather than only reject final outputs | Different grammar and task setting; a conflict-completion adapter alone is an insufficient novelty claim. High mechanism overlap |
| [AbsCon: Accurate and Consistent Graph Model Generation from Text with Large Language Models](https://arxiv.org/html/2508.00255v1), 2025; sections III–IV | Aggregates multiple LLM graph outputs into a probabilistic partial model and solves a constrained selection problem | Recombining locally useful pieces into a globally consistent artifact | Uses graph models, including executable program graphs, rather than repository patches; substantial representation work remains, but the central selection idea is occupied. High mechanism overlap |
| [CodePlan](https://arxiv.org/html/2309.12499v1), 2023; method and running example | Incremental dependency analysis, change-impact analysis, derived edit obligations, adaptive LLM editing and validation | Coordinated repository changes and propagating a changed interface to dependents | Does not establish the same joint local-candidate solver; strong problem/architecture overlap |
| [LLM CEGIS repair](https://arxiv.org/html/2502.07786v1), 2025; method | MaxSAT-based localization, program sketches, LLM completion, counterexample-guided repair | Formal feedback actively steers generated edits | Joint repository repair differs, but CEGIS plus an LLM is not new |
| [Repilot](https://arxiv.org/abs/2309.00608), 2023; abstract | Uses code completion feedback to rule out infeasible generation and complete valid continuations | Feasibility changes generation itself | Token-level rather than repository-level; relevant against a broad claim that others merely check results |
| [Synchromesh](https://www.microsoft.com/en-us/research/publication/synchromesh-reliable-code-generation-from-pre-trained-language-models/), 2022; official research description | Constrained semantic decoding with contextual requirements | Symbolic constraints guide neural output | Application and granularity differ; constrained generation is an established component |
| [Metamodel-Guided Model Generation with Layered Constraints](https://arxiv.org/html/2510.25890), inspected current HTML | Source-traceable constraints guide structured generation, validation and bounded repair | Constraint compilation and generation/repair loop | Structured modeling rather than general repository edits; reinforces overlap, not decisive alone |
| [PaperCompiler](https://arxiv.org/html/2609.02272), inspected HTML | Compiles specifications and cross-file implementation obligations | Compiler framing, provenance and coordinated obligations | Different output mechanism; changing the name or packaging would not distinguish our contribution |

### Mathematical back-check

The finite optimization in document 13 is a constrained discrete selection model. Unary proposal scores, edit costs and compatibility factors are standard ingredients. Its no-good clause excludes a conflicting assignment; neither the clause nor using an unsatisfiable core constitutes a new algorithm. Exactness is relative to the supplied finite candidate sets and encoded constraints. It does not make natural-language intent extraction complete or prove arbitrary program correctness.

AbsCon is particularly relevant because it also selects compatible elements from multiple imperfect outputs. Neo supplies precedent for generalizing conflicts; Concord supplies precedent for feeding deduction into a learned policy. These precedents do not prove that the complete proposed combination has been published. They do mean that the presently stated contribution is explainable largely as a combination of known operations.

A defensible new contribution would require a precise operation, theorem under meaningful assumptions, or replicated empirical result beyond those combinations. A different application can be valuable without being sufficiently distinctive for this user's chosen standard.

## Existing agents and public competition work

| Primary public source inspected | What the inspection can establish | What it cannot establish |
| --- | --- | --- |
| [Codex repository](https://github.com/openai/codex), README | Public coding-agent product and implementation entry point | That proprietary models or other deployments lack an analogous mechanism |
| [Claude Code overview](https://code.claude.com/docs/en/overview) | Documented coding-agent scope | Internal search/inference algorithms or superiority relative to Gemma |
| [Cursor agent overview](https://cursor.com/docs/agent/overview) | Documented repository coding workflow | Absence of unpublished planning or constraint methods |
| [OpenHands repository](https://github.com/OpenHands/OpenHands), README | Existing agent platform and development workflow | Exhaustive behavior of every extension or version |
| [Aider repository map](https://aider.chat/docs/repomap.html) and [architect/editor design](https://aider.chat/2024/09/26/architect.html) | Graph-based repository context and separation of reasoning from editing | The proposed exact joint solver; lack of such documentation is not proof of absence |
| [Amp diagnostic-driven completions](https://ampcode.com/news/diagnostic-driven-completions) | Diagnostics can drive dependent follow-up edits | Formal global optimality or the specific conflict-learning design |

The product surface—read repository, coordinate changes, use tools, test and repair—is already crowded. There is no live evidence here that a proposed Gemma system outperforms any current commercial model. A fair eventual evaluation must distinguish model capability from harness/tool advantage and report both matched-harness and end-to-end comparisons when permitted.

Sampled public competition-related descriptions:

- [G-HRR](https://github.com/Tarekswd/g-hrr-gemma4): graph-guided hierarchical retrieval.
- [Graph reasoning/self-correction submission repository](https://github.com/nazarcoder123/Google---The-Gemma-4-Developer-Agent-Paper-Track-Kaggle-).
- [Gemma code graph localization](https://github.com/aghasalim/gemma4-code-graph-localization): graph localization and retrieval comparisons.
- [Gemma SWE agent](https://github.com/happyc0der/gemma-swe-agent).
- [Gemma developer agent](https://github.com/biswalprince/gemma4-developer-agent).
- [Gemma coding agent](https://github.com/Ashura-asura/gemma4-coding-agent).
- [From Issue to Verified Patch](https://pilkwangkim.github.io/posts/Gemma-4-Developer-Agent-From-Issue-to-Verified-Patch/): public development writeup.

These sampled descriptions did not establish an exact Change Compiler duplicate. Their claimed results were not reproduced and are not treated as verified scores. Graph context, self-correction, ordinary agent loops and adapter training alone are weak differentiation claims. Dynamic pages, private entries and later revisions remain blind spots.

## Replacement proposal A: joint code-and-state migration

**Product promise:** change the meaning or arrangement of data in an application without silently stranding its saved state. For an ML engineer, update code and an existing checkpoint together so training can continue correctly. For a general developer, the analogous outcome is coordinated code and persisted-data migration. These are potential expansion markets, not a claim that one initial implementation supports both.

Start with a narrow ML capability: semantic permutations of class labels or input feature coordinates across source, model parameters, optimizer state, metrics and serving mappings. A concrete demo changes a class-index convention after training has begun. The system produces both the code patch and the checkpoint transformation; a held-out continuation checks that class meaning and subsequent updates agree after mapping.

### Mathematical object

Let F_C(s,x)=(s_next,y) describe a stateful program with code C. Synthesize new code C' and explicit state/input/output maps T_s, T_x, T_y such that, on the declared supported domain,

\[
F_{C'}(T_s(s),T_x(x))=(T_s(s_{next}),T_y(y)).
\]

This is a commuting state-transition relation. If it holds for every reachable state and admissible input and the initial states are related, induction gives related finite trajectories. Random state and external effects must be modeled or excluded. Numerical tests provide bounded evidence, not this universal premise.

For a class permutation matrix Q and logits z=Wh+b, set W'=QW and b'=Qb, with corresponding target/label transformations. Because coordinate permutations commute with elementwise multiplication, square root and coordinatewise division, the same permutation applied to Adam's first and second moments preserves the abstract Adam update when hyperparameters, step counters and parameter groups correspond. Upstream gradients agree when the loss and targets are permuted consistently. This argument does **not** extend to arbitrary dense basis changes: Adam's elementwise second moments are not a general covariance tensor. Floating-point implementation order, fused kernels, stochastic layers and state outside the modeled transition require separate checks; no bitwise claim follows automatically.

The difficult research operation is inferring semantic correspondences across source and persisted artifacts, then synthesizing a coordinated migration under those correspondences. Gemma would propose correspondence hypotheses and code edits; a restricted transformation engine would materialize supported mappings and expose ambiguity. A manually supplied permutation applied to a tensor is only a baseline, not the invention.

### Prior art and open risk

- [Cambria](https://www.inkandswitch.com/cambria/) already explores schema evolution with bidirectional transformations. Do not claim migration or lens laws as new.
- [Git Re-Basin](https://arxiv.org/abs/2209.04836) and its [implementation](https://github.com/samuela/git-re-basin) establish parameter-permutation alignment. Do not claim permutation symmetry as new.
- [Named tensors](https://docs.pytorch.org/tutorials/intermediate/named_tensor_tutorial.html) and [jaxtyping](https://docs.kidger.site/jaxtyping/api/array/) occupy named-axis and shape/type checking.
- [NVIDIA checkpoint documentation](https://docs.nvidia.com/megatron-core/developer-guide/latest/api-guide/core/dist_checkpointing.html) documents optimizer-state compatibility and conversion concerns. Migration is a real engineering task, not an invented category.
- Tensormorph search results describe semantic tensor/checkpoint transformations. Its [v1 page](https://tensormorph.ai/blog/tensormorph-v1) could not be retrieved successfully. **Unresolved potentially close competitor: no low-overlap clearance.**

Candidate distinction to investigate: inferred task-semantic migration spanning source, checkpoint and optimizer continuation, rather than format conversion, shape checking or weight alignment alone. Neither the commuting relation nor this integration has been established here as a first-of-kind contribution.

**Gate:** obtain real, authorized migration histories with independently specified mappings. Hold out repositories and transformation compositions. Compare manual/reference converters, Gemma-only, a stronger-model agent, and the proposed system; give model baselines equivalent artifact readers and execution access. Evaluate semantic recovery, multiple-step continuation error, time/cost and human corrective work. Test tied weights, optimizer parameter groups, ambiguous labels and unsupported transformations. A hand-coded class-permutation demonstration alone fails the gate.

**Tradeoff:** strongest tangible mathematical/product direction of these alternatives, but narrower developer audience and uncertain competition-task coverage. Do not redirect a repository-repair competition around it without measuring relevant development-task prevalence.

## Replacement proposal B: dependency-preserving intent removal

**Product promise:** “Remove the caching feature the agent added, but keep the validation and bug fixes written afterward—even where they share code.” The output is a new coherent patch that reconstructs later functionality when it depended on the removed implementation.

The target is not restoring a snapshot or reverting selected lines. Given initial program P, change A and later change B, the current program is B(A(P)). Seek a residual implementation B_minus_A that realizes B's retained obligations directly on P while excluding A's specified effects. Changes generally do not commute: B(A(P)) need not equal A(B(P)); B may not even apply to P. A residual may be nonunique or nonexistent.

The research problem is learning and synthesizing these residual transformations from change histories plus executable intent witnesses. Formally, choose a candidate P* close to the current program, subject to explicit retained-behavior obligations and explicit removal obligations. Do not identify feature removal with the Boolean negation of an entire old specification: violating one clause does not remove a feature. Do not infer the true counterfactual program uniquely from a Git history. Incompatible intents require a reported conflict, not a fabricated successful residual.

Gemma's possible role is generating residual implementations from dependency structure and witnesses, with training on controlled noncommuting edit compositions. The synthesis operation must outperform ordinary revert-plus-agent-repair; generic constraints and another repair loop are insufficient novelty.

### Prior art and open risk

- [Modeling dependencies for selective undo](https://cs.union.edu/~fernandc/pub/ifip05.pdf) establishes that dependency-aware selective undo is old work.
- [Program merge research](https://www.microsoft.com/en-us/research/project/future-of-program-merge/publications/) and [LLM merge-conflict work](https://www.microsoft.com/en-us/research/wp-content/uploads/2022/07/issta22-merge-conflicts-llm.pdf) occupy semantic reconciliation.
- [LingCode documentation](https://lingcode.dev/support.html) describes semantic time-travel/undo capabilities at product level.
- [EvoUndo](https://arxiv.org/abs/2608.28363), inspected abstract, is a recent adjacent recovery-synthesis direction. It must be compared in detail before making any claim about synthesized undo.

Candidate distinction: synthesizing replacements that preserve later intent after removing its earlier implementation dependency. This is a hypothesis to audit, not a cleared novelty claim. Generic semantic undo should be rejected immediately as the differentiator.

**Gate:** evaluate genuine interleaved histories with independent before/after intent tests, including impossible combinations. Baselines must include selective restore, Git revert plus conflict resolution, effect-scoped restoration where applicable, and a strong agent with complete history. Measure retained-intent success, removal success, regressions and corrective work together. Never award a win for deleting the downstream feature. Hold out histories, repositories and edit families; avoid benchmark leakage through generated reference residuals.

**Tradeoff:** broader everyday developer story, but greater prior-art risk than proposal A. History-dependent tasks may also be absent from the scored competition environment. This is a secondary research option, not the recommended adopted target.

## Recommendation and next decision gate

Investigate A first as a product research hypothesis; keep B as an alternative only if its residual-synthesis mechanism survives a deeper undo/merge audit. Neither presently meets a zero-duplication claim, and neither warrants silently replacing the accepted implementation roadmap.

A bounded 8–12 hour research cycle, before a major implementation commitment:

1. Audit nearest systems and available artifacts, especially Tensormorph, checkpoint converters and parameter-alignment methods; record exact input/output and synthesis capability. Stop if the proposed distinguishing operation is already supported.
2. Audit authorized competition development tasks for stateful migration relevance. Treat low coverage as a competition-fit failure even if the standalone product is attractive.
3. Obtain several independently specified real cases and write the supported transition model and proof assumptions. Distinguish known mathematical facts from a proposed contribution. Do not infer prevalence from this small feasibility sample.
4. Define the incremental contribution in one falsifiable sentence and specify an equal-budget baseline capable of performing the same task. Plan a separate powered evaluation after a pilot estimates variance; do not invent a sample-size guarantee now.
5. Return an adoption/rejection record with unresolved risks. Only an adopted, differentiated proposal should update the README and cycle plan. Subsequent implementation cycles should revise the plan from actual results, not preserve a failing novelty narrative.

## Claim and validation policy

- No assertion that Gemma exceeds current frontier models without paired measurements on a declared task distribution.
- No universal correctness guarantee from tests, inferred contracts or incomplete search.
- No unsupported “first,” “unique,” “zero duplication,” production readiness, or expected competition rank.
- Mathematical transformations and benchmark-independent semantics are legitimate implementation rules. Hard-coded task answers, reference-fix leakage and cherry-picked demonstrations are not.
- For eventual comparisons, predeclare a primary joint success endpoint, include failures/timeouts, account for repository clustering, report paired uncertainty, and separate exploratory subgroup results from confirmatory findings. Compare quality at matched resource budgets and costs at matched quality where feasible.
- A candidate that wins only with manually supplied correspondences or specifications has established an oracle upper bound, not an autonomous product.

This document records research and proposals only. The audit adds no implementation or performance evidence and intentionally leaves the prior README and implementation-plan content unpromoted.
