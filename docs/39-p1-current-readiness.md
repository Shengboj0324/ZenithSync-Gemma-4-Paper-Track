# Current P1 readiness

Updated October 9, 2026. **P1 is incomplete. Keep the Runpod GPU stopped.**
No real training corpus is admitted and no learned coding-performance gain has
been demonstrated. The latest completed local integration is corpus 019.

This file is the current acceptance summary. Cycle details, failed attempts and
superseded results are preserved in the [implementation journal](40-p1-implementation-journal.md).
The [implementation plan](12-continuous-implementation-plan.md) retains the phase
scope and campaign assumptions. Update this summary and the journal after each
cycle; do not append historical logs to this summary.

## Acceptance status

| Requirement | Verified evidence | Remaining acceptance work |
| --- | --- | --- |
| Data supply | 16 quarantined examples, 16 tasks, 15 declared repository groups; 314,028 input and 97,254 supervised tokens | Abundant, diverse, approved data; the 3×50M processed-target-token plan is not supplied |
| Task alignment | Publisher controls and bounded semantic checks for selected candidates; Boltons derivative repairs the reproduced compatibility failure | Final content-bound review for every admitted task; passing finite cases is not universal correctness |
| Attribution | Selected exact repository and dependency notices retained; teacher and assistant-derived actions distinguished | Complete source, observation, dependency and teacher-term review |
| Split isolation | Lineage refresh 009 is incomplete: six HTTP 403 responses; audit 008 is historical evidence | Freeze splits and review semantic duplicates, detached copies and historical lineage; current IDs do not prove independence |
| Local training code | Latest CPU suite: 400 tests, 367 passed, 33 skipped | Skipped environments, full-model GPU corroboration and long-running stability |
| Artifact ingestion | Corpus 019 uploaded to R2, restored into an empty directory and validated; schedules match byte-for-byte | Repeat with the final admitted bundle on the actual Runpod volume |
| GPU validation | Earlier single synthetic full-model update/reload only | Real-corpus long-sequence memory, throughput, checkpoint/resume and bounded failure handling |
| Product performance | No demonstrated learned held-out gain | Train and compare against a frozen baseline on uncontaminated held-out tasks |

## Current corpus and evidence

- [Assembly receipt](../evidence/data/training-corpus-assembly-019/receipt.json)
- [R2 publish receipt](../evidence/data/training-corpus-publish-020/receipt.json)
- [R2 restore receipt](../evidence/data/training-corpus-restore-019/receipt.json)
- [Restored corpus inspection](../evidence/data/training-corpus-inspection-019/report.json)
- [Integration and schedule equality check](../evidence/data/corpus019-integration-check-001/report.json)
- [Explicit training rejection](../evidence/data/training-corpus-denial-018/report.json)
- [Current repository lineage screen](../evidence/data/current-corpus-lineage-009/report.json)
- [Latest CPU regression](../evidence/p1/signac-search-regression-001/regression.json)
- [Boltons derivative review](../evidence/data/boltons205-compat-review-001/report.json)
- [Corpus integration evidence archived in R2](../evidence/data/corpus019-integration-publish-001/receipt.json)

Manifest SHA-256:
`9b9e31e7f98557d67d687c6328bf076f7c080e0ee6ad50e8767e497e102379c1`.
Content SHA-256:
`aaf4774bfa87b3fa978a1f5c656441b7ce83e3bac187951e574b76cba9edad9a`.
The restored bundle has 33 files and 3,484,675 bytes. Its one-epoch schedule uses
seed 7401, 16 planned updates and a 9,216-supervised-token update cap. It consumes
97,254 target tokens with zero overshoot. No optimizer steps are implied.

All four admission fields remain null: rights/attribution, split isolation,
runtime qualification and task alignment. Training-purpose loading rejects with
`Quarantine corpus cannot train`. Receipt integrity verifies bytes and bindings;
it does not prove the truth or completeness of the underlying reviews.

## Next local cycle

1. Expand diverse task supply from the pinned source cohort, preserving failed
   candidates and explicit source-versus-derived authorship. Keep source credential
   screening ahead of replay; flagged material requires review.
2. Complete observation-level attribution and task acceptance, then bind reviews
   to the final corpus. Preserve the Dynaconf mirror distinction and investigate
   semantic overlap before freezing evaluation splits.
3. Reassemble, publish, restore and compare token accounting and deterministic
   schedules after each admitted-to-quarantine data change. Quarantine eligibility
   must not be promoted to training approval by a successful transfer.
4. Prepare the exact worker, admitted data bundle, resume checks, GPU validation
   commands and cost cap before asking the user to restart Runpod.

## GPU restart boundary

Request a restart only when a concrete next validation requires the GPU and its
inputs and local checks are ready. CPU checks cannot guarantee full-model GPU fit
or absence of errors. The next GPU session must first measure real-corpus memory,
throughput and checkpoint/resume behavior; it must not launch a long campaign
based on the earlier synthetic update. Obtain the session budget and preserve
checkpoints and evidence on persistent storage. Do not restart a user-stopped Pod
automatically.

The three 50M-token candidates are a changeable experimental plan, not evidence
of sufficient unique data. Repeated exposure is not new data or independent
statistical evidence. Learned gains and industrial readiness remain unproven.
