# Research positioning and choice of contribution

The working title is **When to Trust Repository Graphs for Budgeted Software Repair**. ZenithSync is the project name, not evidence of novelty. The proposed contribution is a reliability-aware way to select compact bundles of source evidence, paired with experiments showing when structural evidence helps or harms repair.

## Closest work and novelty boundaries

This is a focused landscape review, not an exhaustive systematic review. Abstract-level evidence establishes broad overlap; detailed claims must be checked against full methods before implementation freezes.

| Primary source | Established overlap | Consequence for our contribution |
| --- | --- | --- |
| [RepoGraph](https://arxiv.org/abs/2410.14684), with [method text](https://arxiv.org/html/2410.14684v1) | Repository graph context integrated into repair systems | A repository graph or graph-enhanced agent is not sufficient novelty |
| [LocAgent](https://arxiv.org/html/2503.09089v1) | Heterogeneous code graph, controlled traversal, localization, consistency-based confidence, fine-tuning | “Confidence-aware graph search” is too broad a novelty claim; use it as a strong comparator |
| [SWE-Search](https://arxiv.org/abs/2410.20285) | Tree search and iterative refinement for software agents | Multi-agent search or retrying failed patches is established |
| [Repository Memory, ICLR 2026](https://proceedings.iclr.cc/paper_files/paper/2026/hash/b4c06f095368497f3ac19422efef8133-Abstract-Conference.html) | Historical commits and linked issues support localization | Repository memory is occupied territory and introduces temporal-leakage checks |
| [Tree-of-Traversals](https://aclanthology.org/2024.acl-long.665/) | LLM interaction with graphs and search over paths | A graph path and confidence heuristic alone are insufficient |
| [Lookahead-R](https://arxiv.org/abs/2609.35811) | Budgeted tool retrieval using predicted utility, latency, and uncertainty | Generic value-of-information planning is also occupied; this work concerns tools, so verify differences in task and evidence unit |

The proposed difference is the combination of **source-verifiable graph reliability, complementary evidence bundles, and matched interventions on graph structure under a repair budget**. This remains a hypothesis about a research gap. A literature search finding no exact title match would not prove priority. Before October 9, read the closest methods, follow their related work, and record a feature-by-feature comparison covering input signals, decision rule, budget, reliability model, and evaluation. If the same mechanism already exists, reposition around a genuinely new diagnostic finding or reject the design.

## Public competition landscape

Public projects show which narratives already compete for attention. These are author descriptions; their results and award status were not independently verified.

| Project | Public positioning | Strategic implication |
| --- | --- | --- |
| [GraphSWE-Gemma](https://github.com/nazarcoder123/Google---The-Gemma-4-Developer-Agent-Paper-Track-Kaggle-) | Graph navigation, context compaction, AST checks | “Smaller context plus structural navigation” needs a stronger distinction |
| [G-HRR](https://github.com/Tarekswd/g-hrr-gemma4) | Structural retrieval and minimum sufficient context | A compact-context efficiency story already has direct competition |
| [Gemma4 coding agent](https://github.com/Ashura-asura/gemma4-coding-agent) | Verified trajectories, supervised tuning, reinforcement learning | A generic SFT-to-RL pipeline faces both competition and substantial compute cost |
| [Codegraph localization discussion](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/discussion/746035) | Index announces an open graph generator and localization benchmark | Do not assume a graph audit or generator is an uncontested resource niche; inspect the artifact in the implementation-stage prior-art review |

Do not cite competitors' percentages as trusted comparative baselines. Reproduce eligible methods under common settings or compare conceptual scope without performance claims. The public sample is not a census of entrants and cannot estimate winning odds.

## Options considered

| Direction | Potential contribution | Principal risk | Decision |
| --- | --- | --- | --- |
| Broad SFT plus RL coding agent | Policy improvement and training insight | Expensive rollouts, reward validity, crowded contribution | Defer unless the pilot identifies a clear policy bottleneck and ample compute |
| Generic graph retrieval | Simple, feasible implementation | Weak novelty against existing systems | Baseline |
| Reliability-aware evidence selection | Explainable intervention on structure and cost | Utility proxy may not predict repair | Recommended, with explicit kill criteria |
| Graph diagnostic resource | Reusable stress tests and validity checks | Existing audits; weak relevance without downstream evaluation | Companion contribution or evidence-driven fallback |
| Novel application such as kernel synthesis | Distinct use case | New validation machinery and domain expertise | Do not pursue in the default schedule |

This choice favors technical depth through a falsifiable mechanism. A large agent architecture is not intrinsically more advanced. A result explaining precisely why a tempting graph heuristic fails can be a stronger contribution than another unablated stack.

## Three planned claims

**H1, utility:** At the same total task budget, verified graph evidence bundles improve repair outcomes over a tuned fixed graph retriever. Primary measurement: paired issue-resolution difference on frozen tasks. H1 fails if apparent gains disappear under matched budgets or external evaluation.

**H2, efficiency:** The selector achieves a useful cost reduction without exceeding a prespecified loss in repair success. This is a separate statistical claim requiring a noninferiority analysis, not an automatic interpretation of a nonsignificant H1 result.

**H3, mechanism:** Accounting for graph reliability reduces degradation under controlled missing or incorrect relations. This requires an interaction analysis against a reliability-blind variant. Merely winning on clean graphs does not establish H3.

Publish only supported claims. If H1 and H2 fail but the intervention protocol reveals a reproducible failure pattern, the paper may become a diagnostic study with a resource. That fallback needs its own novelty and usefulness; it is not a way to relabel an inconclusive experiment as success.

## Proposed resource

The resource would specify graph perturbations, preserve task and repository identity, record graph provenance, and produce comparable per-task outcome/cost records. Include synthetic fixtures with known structural truth, reconstruction instructions for authorized users, and permitted aggregate outputs. Include at least two independently implemented consumers or methods to establish reuse beyond the author's controller.

The resource should answer: does a method depend on correct graph relations, on node text, or just on the extra retrieval budget? It should not require redistributing competition graphs, embeddings, issue statements, or reference patches. Resolve the release questions in [risks and decisions](08-risks-and-decisions.md) before publishing any derived assets.
