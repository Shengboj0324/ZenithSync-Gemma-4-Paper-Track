# ZenithSync-Gemma-4-Paper-Track

Joint research and execution plan for the Google Gemma 4 Developer Agent Competition and Paper Track. Initially researched October 6; scope and code-track requirements updated October 7, 2026.

**Adopted direction:** build a complete, trainable Gemma-powered repository engineering agent first, using the competition's supported runtime. Measure its failure profile, train targeted adapters, and add specialist capabilities only when their benefit is demonstrated. The discarded debugging/product hypotheses no longer gate core implementation. Research novelty remains unproved; documents 15–18 are historical evidence, not the current product mandate.

**Status:** foundation-first implementation plan adopted; Gemma execution and training have not started. The earlier reproduction pilot remains complete with no demonstrated mechanism advantage. The user reports model download access. Live checks confirmed Runpod authentication and an active DigitalOcean account; Cloudflare connection is unverified. See document 19 for the model handoff, exact verification scope, and service activation gates.

## Reading order

| Document | Purpose |
| --- | --- |
| [Platform implementation and model handoff](docs/19-agent-platform-and-model-handoff.md) | Current architecture, staged implementation gates, mathematical specification, model intake, and live plugin verification |
| [Reproduction cycle results](docs/18-reproduction-cycle-results.md) | Latest evidence: real defect, three baseline repairs, detailed performance analysis, and no product promotion |
| [Failure-first research study](docs/15-failure-first-research-study.md) | Current conclusion: ranked failure families, competing systems, mathematical hypotheses, and rejection conditions |
| [Task cards and source audit](docs/16-failure-evidence-and-source-ledger.md) | Concrete published attempts, reproduction gaps, source reading depth, and media access limitations |
| [Replication and selection protocol](docs/17-replication-and-selection-protocol.md) | Next 8–14-hour cycles, fair baselines, statistical design, and the product adoption gate |
| [Novelty audit and alternatives](docs/14-novelty-audit-and-alternative-directions.md) | Historical audit rejecting Change Compiler; alternatives are not adopted |
| [Developer pain points and change synthesis](docs/13-user-painpoints-and-change-synthesis.md) | Historical candidate; novelty assessment superseded by document 14 |
| [Continuous implementation plan](docs/12-continuous-implementation-plan.md) | Living 8–14-hour cycles, phase gates, mathematical and statistical assurance, mandatory cycle closeout |
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

Start with documents 19 and 12 for the adopted build, then document 11 for competition constraints. Documents 13–18 preserve prior investigations; their no-go decisions do not block the core agent. Update document 12 after every implementation cycle. Source IDs link to the source register or directly to primary pages.

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

The revised schedule starts October 7 and extends through December 2. Both submissions remain planned. The reproduction pilot used hosted Codex inference; no GPU provisioning, model training, competition entry, or publication has been initiated.
