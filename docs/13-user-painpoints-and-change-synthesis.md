# Developer pain points and coordinated change synthesis

Research snapshot: October 7, 2026. **Candidate direction, not an adopted architecture or measured result.** This brief responds to the request to start with developer problems and seek a substantive mathematical mechanism. Existing cycle gates remain in force. No implementation, interviews, or experiments were conducted.

## Evidence and limits

| Evidence | Finding relevant to product design | Boundary |
| --- | --- | --- |
| [Stack Overflow 2025 survey](https://survey.stackoverflow.co/2025/ai) | 66% of respondents to the frustration question selected almost-correct solutions; 45% selected time-consuming debugging | Historical self-report, not a current tool ranking or proof of cross-file causes; question had 31,476 responses |
| [Student interaction study](https://arxiv.org/abs/2507.22614) | Introductory and advanced students mostly tested/debugged prototypes; advanced students supplied more relevant context | Replit study, not representative of all novice Codex/Claude users |
| [Professional developer study](https://arxiv.org/html/2512.14012v2) | 13 observations and 99 survey responses show active supervision and concern for software quality | Experienced developer sample; fieldwork August–October 2025 |
| [Developer collaboration study](https://arxiv.org/html/2506.12347v3) | Observed 19 developers on 33 issues; contextual communication and debugging/testing collaboration remain difficult | Observational; incremental work's association with success is not a randomized causal estimate |
| [METR trial](https://metr.org/Early_2025_AI_Experienced_OS_Devs_Study-paper.pdf) | 16 experienced developers, 246 tasks, 19% longer completion time with early-2025 tools | Historical, narrow setting; not evidence that current AI generally slows developers |
| [Constraint Decay](https://arxiv.org/abs/2605.06445) | Controlled backend tasks expose difficulty satisfying functional and structural requirements jointly | Benchmark/preprint evidence, not user prevalence |
| [Needle in the Repo](https://arxiv.org/abs/2603.27745) | Functional success can coexist with structural failure in repository edits | Diagnostic benchmark; structural oracle validity and full method require audit |
| [ML-Dev-Bench](https://arxiv.org/html/2502.00964v3) | Separates dataset handling, training, model improvement, debugging and API integration | Relevant evaluation taxonomy; does not establish ML engineers' top complaint |

The 2026 Stack Overflow AI page appeared in search but repeatedly failed full-page retrieval. No unverified 2026 statistics are used. This is a focused literature review, not an exhaustive market study. ML-specific demand and current novice workflows need direct validation.

## Product opportunity

Working proposition: **complete the connected edits implied by a change, so developers spend less time repairing mismatches between components.** A novice could receive a coherent feature patch; a maintainer could evolve an API with its callers; an ML engineer could coordinate labels, model outputs, objectives, metrics and serving behavior. These segment benefits are hypotheses inferred from the evidence, not surveyed purchase intent.

| Alternative | Reason to defer as the main contribution |
| --- | --- |
| Persistent agent memory | Useful but occupied; reminders alone do not generate compatible edits |
| Another review or testing agent | Addresses an evidenced pain but repeats the previously rejected checker-centric direction |
| Automatic ML experiment optimization | Potentially valuable, but weak direct fit to the existing repository-repair competition |
| Coordinated change synthesis | Tangible complete-patch output; potential repair relevance; difficult representation and search problems worth testing |

Proposed product name for discussion: **Change Compiler**. It would accept a repository snapshot, intended change, and optionally a partial patch from an existing agent. It would return a coordinated patch, executable checks and a concise explanation of which interfaces required edits. Tool/MCP integration is a later product option; the competition entry must stay inside its permitted Gemma/harness interfaces.

## Mechanism

Represent a supported portion of the repository as a contract hypergraph. Nodes are editable regions and their interface states. Hyperedges express relationships involving several regions: schema/serializer/consumer agreement, optional-value handling, async call behavior, or supported tensor-shape relationships. File boundaries alone are not semantic boundaries.

Gemma proposes local implementation candidates and missing contract hypotheses. Static analysis and supported executable checks establish which relations can be enforced. Unverified inferred relations remain soft evidence, never silently become hard constraints. Preserve provenance and version hashes; invalidate affected relations after changes. Distinguish the desired new contract from old behavior that the requested change deliberately replaces.

Let x_i select one candidate from a finite local set D_i, including an unchanged candidate when permitted. Let h_e(x_e) encode a justified hard relation, phi_e(x_e) a soft compatibility penalty, and c_i(x_i) edit cost. A finite selection model is

\[
\min_{x\in\prod_iD_i}\sum_i u_i(x_i)+\lambda\sum_i c_i(x_i)+\sum_{e\in E_s}w_e\phi_e(x_e)
\quad\text{subject to}\quad h_e(x_e)=1\ (e\in E_h),\ I(x)=1.
\]

I represents the supported encoding of the requested change. u_i ranks proposals; model likelihood is not a calibrated correctness probability. Budget limits apply to the entire generation, extraction, solver and test process, not merely this optimization objective. A feasible assignment satisfies encoded relations only; it need not implement the full natural-language request or pass unseen tests.

The candidate invention is **conflict-directed expansion of local repair choices**. When the solver finds incompatible choices, derive a conflict explanation and request new candidates for the implicated interfaces. Preserve compatible work. A justified conflict over chosen literals yields a no-good clause

\[
\bigvee_{i\in S}(x_i\ne\bar x_i).
\]

This forbids that incompatible combination, not every local candidate within it. Solver unsatisfiability must not be inferred from an LLM failing to generate a patch. A failed test can reject the exact tested artifact; excluding all combinations sharing a partial edit requires additional justification. Broader cuts are valid only under their stated abstraction and snapshot assumptions.

The approach is inspired by decomposition and conflict learning. [Logic-based Benders decomposition](https://arxiv.org/abs/1910.11944) provides a framework for separating master decisions from subproblems, but our incomplete neural generator is not an exact subproblem solver and inherits no completeness theorem. For fixed finite domains, exact discrete inference can exploit sparse interaction structure; its complexity depends on induced width, not simply file count. Dense dependencies remain expensive. [Bucket elimination](https://www.sciencedirect.com/science/article/pii/S0004370299000594)

Train optional Gemma adapters on authorized, repository-disjoint examples of interface obligations, incompatible local edits and successful compatible completions. Include hard negative combinations whose local snippets appear valid. Training on ordinary diffs alone is not the proposed contribution. Do not train on protected competition evaluation artifacts.

## Demonstration and scope

Illustrative ML demo: convert a single-label classifier into a multi-label classifier. A coordinated change must account for target representation, output interpretation, suitable loss, prediction rule and metrics. Use explicit task assumptions and actual library semantics; these are not universally prescribed choices. Evaluate training and inference consistency on withheld examples, not just output shapes. This is an external product demo, not evidence that the competition contains ML tasks.

Competition pilot: supported Python interface changes such as missing-value propagation, serialization contracts or async callers. First audit development issues to estimate relevance. A graph generator that discovers contracts perfectly on handwritten demos but fails on real repositories does not qualify.

## Novelty audit

| Closest source | Already established | Remaining candidate distinction |
| --- | --- | --- |
| [CodePlan](https://arxiv.org/html/2309.12499v1) | Dependency analysis, change-impact analysis and adaptive multi-step repository edits | Joint selection of local alternatives and conflict-directed candidate expansion; needs full algorithm comparison |
| [Clean-PR](https://arxiv.org/abs/2602.07457) | Learning repository edits from pull requests | Training specifically on compatibility conflicts and their completions |
| [PaperCompiler](https://arxiv.org/abs/2609.02272) | Compiling specifications and cross-file requirements for generation | Executable joint synthesis, rather than assuming a specification document is followed |
| [Metamodel-guided generation](https://arxiv.org/abs/2510.25890) | Layered constraints and validation for structured artifacts | Inferred, partial repository contracts and incremental patch completion; substantial overlap needs examination |
| [LLM CEGIS repair](https://arxiv.org/abs/2502.07786) | Formal localization and counterexample-guided LLM repair | Joint repository alternatives and interface-level conflict learning; CEGIS itself is not new |

No first-of-kind claim is established. Sheaf theory, category theory, or topology should be added only if they provide a necessary operation or demonstrably better algorithm than the finite constraint model. Sophisticated terminology alone does not improve novelty. The discovery of closely overlapping work may invalidate this candidate.

## Evidence needed before adoption

1. Run a feasible extraction pilot on authorized development tasks; measure relation coverage, false hard constraints and runtime. Human-curated contracts are an upper-bound diagnostic, not the deployable condition.
2. Compare equal-budget Gemma baseline, strong dependency planner, checker-only variant, joint selector, and full conflict-directed generator. Compare against a monolithic global-patch generator to test whether decomposition is useful.
3. Freeze repository-level partitions and analyze paired repair outcomes, time to accepted patch, regression rate and total cost. Stratify genuinely coupled changes separately; report the entire eligible cohort as well.
4. Demonstrate source-edit fidelity and withholding of reference fixes. Test deliberate changes to old contracts, ambiguous requests, unsupported dynamic behavior, conflicting requirements, and solver timeouts.
5. For product value, run an opt-in comparative workflow study across novice, experienced and ML-engineering participants. Measure human corrective work and task completion, not satisfaction alone. This study is planned, not conducted or authorized outreach.
6. Adopt only if actual generated contracts support real improvements over strong baselines within the competition budget. Otherwise narrow the supported domain or reject the mechanism. A polished external demo cannot compensate for weaker scored repair performance.

Next research gate: inspect closest methods in full and specify one supported contract language, its extraction semantics and the exact conflict-to-candidate operation. Existing baseline and harness work remains necessary whichever research direction is selected.
