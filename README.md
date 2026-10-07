# ZenithSync-Gemma-4-Paper-Track

Joint research and execution plan for the Google Gemma 4 Developer Agent Competition and Paper Track. Initially researched October 6; scope and code-track requirements updated October 7, 2026.

**Recommended direction:** build a reliable, budget-compliant Gemma repair agent first; promote retrieval, reasoning, or training changes through matched experiments. Study graph reliability as one candidate contribution. Freeze the research version for the paper and continue improving the code entry afterward. The best paper method and best final agent need not be identical.

**Status:** planning only. The proposed method is unimplemented, novelty remains conditional on a deeper prior-art check, and there are no experimental results. Mathematical examples are illustrative. This round adds documentation only.

## Reading order

| Document | Purpose |
| --- | --- |
| [Joint strategy and code competition](docs/11-code-track-and-joint-strategy.md) | Start here: differences between tracks, aggregate runtime math, agent priorities, submission gates |
| [Competition facts](docs/01-competition-facts.md) | Verified requirements, deadlines, organizer clarifications, unresolved questions |
| [Judging strategy](docs/02-judging-strategy.md) | Criterion-by-criterion evidence and public judge information |
| [Research positioning](docs/03-research-positioning.md) | Prior art, public competition projects, choice of research question |
| [Technical proposal](docs/04-technical-proposal.md) | Mathematical formulation, assumptions, proofs, counterexamples |
| [Evaluation protocol](docs/05-evaluation-protocol.md) | Data isolation, baselines, ablations, statistics, claim gates |
| [Execution and resources](docs/06-execution-and-resources.md) | Dated milestones, compute scenarios, decision gates |
| [Paper and submission](docs/07-paper-and-submission.md) | Argument structure, word allocation, tables, final checks |
| [Risks and decisions](docs/08-risks-and-decisions.md) | Failure responses, open decisions, organizer questions |
| [Sources](docs/09-sources.md) | Linked source register with access and verification boundaries |
| [Planning validation](docs/10-planning-validation.md) | Arithmetic checks and logical review of this package |

Start with document 11, then documents 1–3. Documents 4–6 specify research and execution; document 7 governs the paper; document 11 governs the code artifact. Source IDs link to the source register or directly to primary pages.

## Two deliverables and deadlines

| Deliverable | Success criterion | Current deadline in Los Angeles |
| --- | --- | --- |
| Research paper | Five equally weighted research criteria | November 12, 2026, 15:59 PST |
| Agent entry and team merger | Rules accepted and team finalized | November 25, 2026, 15:59 PST |
| Agent archive | Private-test repair performance within the official runtime | December 2, 2026, 15:59 PST |

The code track currently allows one submission per day and two final selections. Its twelve-hour budget covers all tasks, including setup. The research plan's illustrative twelve-minute task cost is not a deployment allocation. See document 11 for sources and the corrected runtime model.

## First actions for the next round

1. Resolve eligibility, team availability, GPU access, and the cost ceiling.
2. Obtain the official harness through the user's authorized Kaggle access; freeze its version and audit development-task validity.
3. Reproduce and package the official baseline; measure full-run time and graph-tool functionality on target-equivalent hardware.
4. Freeze evaluation partitions before inspecting reference fixes for method development; complete the nearest-prior-art review before asserting novelty.
5. Use measured failures to choose between reasoning, retrieval, recovery, and tuning interventions; keep a stable code champion throughout.

The revised schedule starts October 7 and extends through December 2. Both submissions remain planned; no remote resources, model training, competition entry, or publication have been initiated.
