# ZenithSync-Gemma-4-Paper-Track

Research and execution plan for the Google Gemma 4 Developer Agent Paper Track, researched on October 6, 2026.

**Recommended direction:** study how the reliability of repository graphs changes the value of retrieved context under a fixed software-repair budget. Develop a narrowly scoped method, evaluate it against strong matched baselines, and make the evaluation procedure reusable. Aim for a defensible research contribution and award eligibility through one coherent paper.

**Status:** planning only. The proposed method is unimplemented, novelty remains conditional on a deeper prior-art check, and there are no experimental results. Mathematical examples are illustrative. This round adds documentation only.

## Reading order

| Document | Purpose |
| --- | --- |
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

Start with documents 1–3; use 4–6 to commission implementation in a later round. Documents 7–8 govern what can eventually be claimed and submitted. Source IDs throughout link to the source register or directly to primary pages.

## First actions for the next round

1. Resolve eligibility, team availability, GPU access, and the cost ceiling.
2. Obtain the official harness through the user's authorized Kaggle access; freeze its version and audit development-task validity.
3. Complete the nearest-prior-art review before treating the proposed method as novel.
4. Freeze evaluation partitions before inspecting reference fixes for method development.
5. Run the small pilot and use its measured runtime and failure modes to choose the execution tier.

The schedule assumes work begins October 6. It must be compressed if implementation begins later. No remote resources, model training, competition entry, or publication have been initiated.
