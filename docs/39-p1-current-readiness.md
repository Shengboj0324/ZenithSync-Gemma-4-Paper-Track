# Current P1 readiness

Updated October 9, 2026. **P1 is incomplete. Keep the Runpod GPU stopped.**
No real training corpus is admitted and no learned coding-performance gain has
been demonstrated. The latest completed local integration is corpus 018.

This file is the current acceptance summary. Cycle details, failed attempts and
superseded results are preserved in the [implementation journal](40-p1-implementation-journal.md).
The [implementation plan](12-continuous-implementation-plan.md) retains the phase
scope and campaign assumptions. Update this summary and the journal after each
cycle; do not append historical logs to this summary.

## Acceptance status

| Requirement | Verified evidence | Remaining acceptance work |
| --- | --- | --- |
| Data supply | 15 quarantined examples, 15 tasks, 14 declared repository groups; 289,750 input and 90,869 supervised tokens | Abundant, diverse, approved data; the 3×50M processed-target-token plan is not supplied |
| Task alignment | Publisher controls and bounded semantic checks for selected candidates; Boltons derivative repairs the reproduced compatibility failure | Final content-bound review for every admitted task; passing finite cases is not universal correctness |
| Attribution | Selected exact repository and dependency notices retained; teacher and assistant-derived actions distinguished | Complete source, observation, dependency and teacher-term review |
| Split isolation | Lineage audit 008 resolves 14 declared groups, two historical names and four reserved names; no cross-boundary ID/network-root overlap | Freeze splits and review semantic duplicates, detached copies and historical lineage; current IDs do not prove independence |
| Local training code | Latest CPU suite: 400 tests, 367 passed, 33 skipped | Skipped environments, full-model GPU corroboration and long-running stability |
| Artifact ingestion | Corpus 018 uploaded to R2, restored into an empty directory and validated; schedules match byte-for-byte | Repeat with the final admitted bundle on the actual Runpod volume |
| GPU validation | Earlier single synthetic full-model update/reload only | Real-corpus long-sequence memory, throughput, checkpoint/resume and bounded failure handling |
| Product performance | No demonstrated learned held-out gain | Train and compare against a frozen baseline on uncontaminated held-out tasks |

## Current corpus and evidence

- [Assembly receipt](../evidence/data/training-corpus-assembly-018/receipt.json)
- [R2 publish receipt](../evidence/data/training-corpus-publish-019/receipt.json)
- [R2 restore receipt](../evidence/data/training-corpus-restore-018/receipt.json)
- [Restored corpus inspection](../evidence/data/training-corpus-inspection-018/report.json)
- [Integration and schedule equality check](../evidence/data/corpus018-integration-check-001/report.json)
- [Explicit training rejection](../evidence/data/training-corpus-denial-017/report.json)
- [Current repository lineage screen](../evidence/data/current-corpus-lineage-008/report.json)
- [Latest CPU regression](../evidence/p1/replay-credential-screen-001/regression.json)
- [Boltons derivative review](../evidence/data/boltons205-compat-review-001/report.json)
- [Corpus integration evidence archived in R2](../evidence/data/corpus018-integration-publish-001/receipt.json)

Manifest SHA-256:
`3c26a771de1a2d2f5a5f98b75d5a3cb6d5adcadb426754f89a6ca3a98f7f4109`.
Content SHA-256:
`cda219ef9998fe0b138c6cbe4f86b843b1daaea24f420a1e5597d8c69c17f01d`.
The restored bundle has 31 files and 3,216,759 bytes. Its one-epoch schedule uses
seed 7401, 14 planned updates and a 9,216-supervised-token update cap. It consumes
90,869 target tokens with zero overshoot. No optimizer steps are implied.

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
