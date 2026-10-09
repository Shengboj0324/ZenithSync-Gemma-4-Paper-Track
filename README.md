# ZenithSync-Gemma-4-Paper-Track

Joint research and execution plan for the Google Gemma 4 Developer Agent Competition and Paper Track. Initially researched October 6; scope and code-track requirements updated October 7, 2026.

**Adopted direction:** build a complete, trainable Gemma-powered repository engineering agent first, using the competition's supported runtime. Measure its failure profile, train targeted adapters, and add specialist capabilities only when their benefit is demonstrated. The discarded debugging/product hypotheses no longer gate core implementation. Research novelty remains unproved; documents 15–18 are historical evidence, not the current product mandate.

**Status, October 8:** P0 is accepted within its recorded scope; P1 remains partially qualified. A corrected local Requests evaluation records 321 passing tests plus one failure before the generated patch and 322 passing tests after it, with two skips in both cases; hidden-grader parity and broad agent reliability remain unproven. The full Gemma checkpoint also passed one synthetic LoRA update and fresh adapter reload on the H100, with unchanged frozen state and zero reload logit difference. This is compatibility evidence, not a trained competition candidate or a coding-performance gain. Model/R2 recovery is verified. See the [training qualification](docs/32-full-checkpoint-gpu-qualification.md) and [P1 acceptance checklist](docs/26-p1-acceptance-checklist.md).

## Reading order

| Document | Purpose |
| --- | --- |
| [Pinned public data intake](docs/33-public-data-intake.md) | Acquired shard, measured metadata, conversion gaps and quarantine gates |
| [Full-checkpoint training qualification](docs/32-full-checkpoint-gpu-qualification.md) | Actual H100 update/reload evidence, memory measurements and remaining long-run gates |
| [P1 requirements audit](docs/28-p1-requirements-audit.md) | Published phase exit evidence, broader open obligations and measured resource limits |
| [H100 validation and content-fidelity finding](docs/30-p1-h100-validation.md) | Successful restored deployment; three repeated Unicode content failures in repository context |
| [P1 GPU session report](docs/27-p1-gpu-validation-report.md) | Actual inference, two repair attempts, corrected local grading, limits and cleanup |
| [P1 acceptance checklist](docs/26-p1-acceptance-checklist.md) | Gate-by-gate evidence and remaining failures |
| [P1 deployment handoff](docs/25-p1-deployment-handoff.md) | Corrected serving lock, durable recovery and future Pod procedure |
| [P1 implementation history](docs/24-p1-implementation-status.md) | Preserved development checkpoints and unsuccessful attempts |
| [Data requirements and acquisition](docs/23-data-requirements-and-acquisition-plan.md) | Specific source shortlist, schemas, 3×50M candidate mixtures, contamination controls and intake gates |
| [R0 implementation and correctness](docs/20-r0-foundation.md) | Contracts, CLI, schemas, mathematical ledger, offline checks and bounded integration acceptance |
| [Cloud preparation](docs/21-cloud-preparation.md) | Actions needed for Runpod, DigitalOcean, R2 and the model handoff |
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
2. Use the retrieved, hashed official harness; stage development tasks and audit their validity before baseline evaluation.
3. Reproduce and package the official baseline; measure full-run time and graph-tool functionality on target-equivalent hardware.
4. Freeze evaluation partitions before inspecting reference fixes for method development; complete the nearest-prior-art review before asserting novelty.
5. Use measured failures to choose between reasoning, retrieval, recovery, and tuning interventions; keep a stable code champion throughout.

Both submissions remain planned. The earlier reproduction pilot used hosted Codex inference; P1 subsequently used the user's existing Runpod GPU. Model training and competition submission have not started. Competition rule acceptance was confirmed in the authenticated Chrome session on October 7.

## Run the foundation checks

```sh
python3 -m unittest discover -s tests -v
python3 -m zenithsync --help
```

The original 26-test foundation used Python 3.13.7 and the standard library: [R0 validation](evidence/r0/local-004/receipt.json). The expanded suite passed 81 tests in the qualified tokenizer environment: [P1 validation](evidence/p1/local-006/receipt.json). Optional tokenizer checks require the pinned dependencies; do not interpret skipped checks as verified. These software tests are separate from inference and repair evidence.

The official starter and harness assets are now downloaded into ignored local storage. The unchanged starter compiled with ADK submission 0.2.12 and Google ADK 1.36.1. See the [official contract audit](docs/22-official-contract-audit.md) for source discrepancies, compiler tests and remaining runtime gates.

The [Linux integration receipt](evidence/r0/linux-002/receipt.json) records 25 checks using actual released tools; all 26 core tests also pass in the official sandbox image. This is local AMD64 emulation, not GPU qualification or official competition grading.
