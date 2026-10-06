# Source register and verification boundaries

Research cutoff: October 6, 2026, America/Los_Angeles. Competition pages and discussion replies were read through the rendered Kaggle site because the web text extractor returned empty content for several pages. Publication and repository pages were read through web retrieval. No competition data files or model weights were downloaded.

The register distinguishes official requirements, organizer clarifications, published work, and competitors' descriptions. Sources can change; refresh the competition requirements at the schedule's review dates. The linked primary pages are the source of record, rather than search-result summaries or this paraphrase.

## Competition and organizer sources

| ID | Source | Used for and verification boundary |
| --- | --- | --- |
| S01 | [Paper overview](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/overview) | Rendered description, evaluation, timeline, submission requirements, awards, and Judges section read. Official paper requirements are centralized in document 1. |
| S02 | [Paper rules](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/rules) | Full rendered competition-specific and foundational rules read. Does not establish this entrant's eligibility. |
| S03 | [Award and release clarification](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/discussion/743255) | Elan Markowitz's host reply read, including provisional graph-release language and subsequent open word-count/release questions. |
| S04 | [Preprint clarification](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/discussion/745872) | Host explicitly permits arXiv. |
| S05 | [Venue and highlighting clarification](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/discussion/743310) | Host permits parallel submissions and limits the promise of highlighting to prize winners. |
| S06 | [AI assistance and individual entrants](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/discussion/745712) | Host and Kaggle Staff replies read. Supports assistance policy and author-responsibility discussion, not a score prediction. |
| S07 | [Earlier pilot publication](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/discussion/745150) | Host approves the particular extended pilot described by that entrant; retain that scope. |
| S08 | [Welcome](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/discussion/743012) | Host explains independent research and methodological scope. |
| S09 | [Paper discussion index](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/discussion) | All 14 visible topic entries on the single index page inspected; relevant clarification threads opened. Not every participant comment or linked artifact was audited. |
| S10 | [Companion competition overview](https://www.kaggle.com/competitions/gemma-4-developer-agent/overview) | Main-track model, budget, harness, and accelerator restrictions. Do not transfer them wholesale to independent paper research. |
| S11 | [Companion data page](https://www.kaggle.com/competitions/gemma-4-developer-agent/data) | Rendered schema and asset inventory read; the harness file itself was access-gated. Inventory descriptions are not tested guarantees. |
| S12 | [Official starter notebook inputs](https://www.kaggle.com/code/ryanholbrook/getting-started-gemma-4-developer-agent/input) | Discovery and corroborating inventory; notebook execution and implementation not audited. |
| S13 | [Ryan Holbrook discussion activity](https://www.kaggle.com/ryanholbrook/discussion) | Search retrieval exposed organizer comments about public environment validity and reasoning-token handling. Direct incident threads, patch deployment, and current harness behavior remain unverified. Used only to motivate environment checks. |

## Prior research

| ID | Primary source | Review depth and purpose |
| --- | --- | --- |
| R01 | Ouyang et al., [RepoGraph](https://arxiv.org/abs/2410.14684); [HTML methods](https://arxiv.org/html/2410.14684v1) | Abstract and method source retrieved; repository-graph context establishes broad prior art. A faithful baseline still needs implementation inspection. |
| R02 | Chen et al., [LocAgent](https://arxiv.org/abs/2503.09089); [HTML methods](https://arxiv.org/html/2503.09089v1) | Graph schema, traversal tools, localization flow, and consistency confidence read. Strongest directly examined methodological overlap. |
| R03 | [SWE-Search](https://arxiv.org/abs/2410.20285) | Abstract-level overlap in search and iterative refinement. No numerical result used as a baseline. |
| R04 | Wang et al., [Improving Code Localization with Repository Memory](https://proceedings.iclr.cc/paper_files/paper/2026/hash/b4c06f095368497f3ac19422efef8133-Abstract-Conference.html) | Official ICLR abstract read; supports memory/history overlap. Full implementation remains a next-round review item. |
| R05 | Markowitz et al., [Tree-of-Traversals](https://aclanthology.org/2024.acl-long.665/) | Official ACL abstract, authorship, and method description support graph-search overlap and public technical background. |
| R06 | Markowitz et al., [StATIK](https://aclanthology.org/2022.findings-naacl.46/) | Official ACL abstract and authorship support structure/text and inductive-generalization background. |
| R07 | Wu et al., [Lookahead-R](https://arxiv.org/abs/2609.35811) | Primary abstract and submission metadata checked; establishes budget-aware tool-retrieval overlap. No claim that its tool-retrieval results transfer to repair. |
| R08 | Sviridenko, [Submodular maximization under a knapsack constraint](https://www.sciencedirect.com/science/article/pii/S0167637703000622) | Publisher abstract establishes the classical approximation result. The plan does not claim that its simple greedy heuristic implements that algorithm. |
| R09 | Golovin and Krause, [Adaptive Submodularity](https://arxiv.org/abs/1003.3967) | Primary theory reference for the distinction between static and adaptive guarantees. Assumptions are not asserted for this repair system. |
| R10 | [SWE-bench-Live project](https://swe-bench-live.github.io/); [paper](https://arxiv.org/abs/2505.23419) | Candidate external evaluation source. Actual task access, licenses, split selection, and contamination audit remain outstanding. |

## Public competing projects

| ID | Source | Boundary |
| --- | --- | --- |
| C01 | [GraphSWE-Gemma](https://github.com/nazarcoder123/Google---The-Gemma-4-Developer-Agent-Paper-Track-Kaggle-) | Public README positioning inspected. Claimed improvements were not reproduced. |
| C02 | [G-HRR](https://github.com/Tarekswd/g-hrr-gemma4) | Public project description inspected; no comparative numbers accepted as verified. |
| C03 | [Gemma4 coding agent](https://github.com/Ashura-asura/gemma4-coding-agent) | Public status/architecture description retrieved; training and run artifacts not audited. |
| C04 | [Codegraph localization topic](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/discussion/746035) | Title and positioning observed in S09. Linked resource was not reviewed; a discovery item for the next-round novelty check. |

## Coverage and limits

This package covers the published paper rubric, submission rules, relevant public organizer answers, the currently listed judge, nearby research, publicly visible competing directions, and a concrete experiment/paper plan. It does not claim access to private judge deliberations, unpublished competitor work, hidden tasks, model-training data, or future rule changes.

The research-gap judgment is provisional. Before making a novelty assertion in a paper, inspect the full closest-work methods and their recent citations. Before implementing against the harness, inspect the actual authorized file. Before claiming any benefit, run the planned experiments. These are distinct evidence gates.
