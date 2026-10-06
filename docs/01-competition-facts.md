# Competition facts and requirements

The Paper Track rewards a research argument supported by evidence. Use the paper-specific requirements for the submission and the companion competition only as an experimental environment. Research date: October 6, 2026. All proposed operational choices below are separate from official rules.

## Verified paper requirements

The [official overview](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/overview) establishes:

| Item | Requirement |
| --- | --- |
| Deadline | November 12, 2026, 23:59 UTC; 15:59 PST in Los Angeles |
| Submission | Join and submit a Kaggle Writeup; drafts do not qualify |
| Scope | Original, unpublished research; maximum 3,000 words; non-archival |
| Contents | Title, subtitle, abstract, introduction, methods/experiments, related work/citations |
| Optional assets | Public notebook or publicly accessible paper PDF |
| Scoring | Novelty, Quality, Relevance, Verifiability, Clarity; each 0–5; arithmetic mean |
| Quality emphasis | Generalization beyond this competition |
| Awards | Best Paper $15,000; New Resource $10,000; New Application $10,000 |
| Tie | Earlier submission wins; rubric scores are not returned |
| Listed judge | Elan Markowitz, Machine Learning Engineer, Google |
| Main track | Participation is optional |
| Attached private resources | May become public after the deadline |

## Rules affecting execution

The [rules](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/rules) specify a five-person team maximum, five submissions daily, and two final selections. One account and one team are permitted. Private competition-code sharing across teams is prohibited; public sharing must also reach the competition forum or notebooks. External resources must satisfy accessibility and cost conditions. Winner terms specify Apache 2.0, reproducible code and environment documentation, and prize paperwork.

Eligibility generally requires the older of 18 or local majority, unless the sponsor agrees and obtains guardian consent. Residency, sanctions, employer authorization, and competition-entity exclusions also apply. Check these conditions before committing resources; this package does not determine personal eligibility.

The data-use heading names Apache 2.0, but the data-security clause restricts redistribution to nonparticipants. Foundational rules state that they control conflicts. Do not infer unrestricted redistribution from the license heading. Preserve upstream rights separately from licenses on our original work.

## Organizer clarifications

| Topic | Verified answer and operational consequence |
| --- | --- |
| Award overlap | In [discussion 743255](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/discussion/743255), Elan confirms at most two writeups, one judging track, multiple-award consideration but at most one award per writeup, and the same criteria interpreted for each award. Build one strong paper first. |
| Regenerated graphs | The same reply provisionally accepts independently rebuilt graphs with attribution and links, but explicitly promises a rules check. Follow-up questions remained unanswered when read. Treat release permission as unresolved. |
| Word counting | References, captions, tables, and PDF counting were still open questions in that discussion. Keep all visible paper content within the limit until clarified. |
| Preprints | [Discussion 745872](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/discussion/745872) explicitly permits arXiv preprints and an arXiv submission link. |
| Parallel venues | [Discussion 743310](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/discussion/743310) permits parallel venue submission and confirms the non-archival event; check the other venue's policy independently. Only prize-winning papers were promised highlighting. |
| AI assistance | In [discussion 745712](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/discussion/745712), Elan allows coding assistants while keeping responsibility with the entrant and cautions against purely machine-generated prose. Ashley Oldacre confirms individual prize eligibility without a company and reasonable likeness accommodations. |
| Earlier pilot publication | [Discussion 745150](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/discussion/745150) accepts one specifically described substantially extended blog/benchmark pilot. This is not blanket permission for repackaging previously published research. |

## Companion environment

The [main competition overview](https://www.kaggle.com/competitions/gemma-4-developer-agent/overview) currently names `gemma-4-31b-it-qat-w4a16-ct` for every submitted agent, permits LoRA adapters, and uses an ADK configuration archive. Its issue-resolution score is a pass fraction, with a twelve-hour aggregate execution allowance including setup. L4x4 sessions offer 96 GB aggregate GPU memory, require offline operation, and consume quota at twice the older-machine rate. Its entry/merger deadline is November 25 and final deadline December 2. These are companion-track constraints, not replacement paper deadlines or proof that every paper experiment must use that harness.

The [data page](https://www.kaggle.com/competitions/gemma-4-developer-agent/data) describes 129 development tasks from FastAPI, Rich, Requests, and HTTPX; base-commit snapshots; reference patches and evaluator test patches; directed multigraphs; 256-dimensional embeddings; offline wheels; and a harness guide. It describes approximately 120 hidden tasks from private repositories. Development tasks therefore cannot establish performance on the hidden distribution.

The full `HARNESS_README.md` requires accepted competition access and was not inspected. Its availability is the first implementation gate. The data-page inventory is not enough to certify tool schemas, budgets, adapter compatibility, or reproducibility.

## Ambiguities to preserve

The overview describes three highest-scoring submissions while separately naming three award categories. Use the organizer's category clarification when planning; do not assume ordinary first/second/third placement. The rules also retain generic prediction-leaderboard language. If prize administration turns on that discrepancy, obtain written organizer clarification rather than resolving it ourselves.

The overview's prose start date is September 22, while the UI start indicator showed September 23. Neither changes the currently consistent final deadline. Use an internal November 9 submission target and manually recheck rules on October 20, November 2, and November 9. These are planned checks, not scheduled automations.
