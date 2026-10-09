# Full trajectory corpus intake

Status: pinned raw acquisition and metadata census complete; training admission
incomplete. Runpod was not used. This supersedes conclusions drawn from the first
2,500-row shard alone, while preserving that earlier evidence.

## Acquired material

All 14 Parquet shards of `nvidia/SWE-Hero-openhands-trajectories` at revision
`150bc119e52c647216fce285fd801f16b6fd745b` were acquired. Each download matched
the publisher's pinned byte size and SHA-256. Cards and publisher metadata are
retained alongside raw shards under `artifacts/data/quarantine`. Later shard
requests now explicitly pin the metadata revision as well as download URLs.

The metadata-only census reports:

| Measure | Count |
|---|---:|
| Trajectory rows | 34,269 |
| Unique trajectory IDs | 34,269 |
| Duplicate trajectory-ID rows | 0 |
| Case-folded repository names | 1,695 |
| Repository–issue pairs | 11,766 |
| Extra trajectories for repeated issues | 22,503 |
| Rows with exact reserved repository match | 73 |

There are 329 issues with one trajectory, 371 with two, and 11,066 with three.
These satisfy `329 + 371 + 11066 = 11766` and
`329 + 2*371 + 3*11066 = 34269`. Multiple attempts for one issue can provide
useful training variation, but must stay together when splitting data and cannot
be counted as independent evaluation tasks. Repository and related-code families
need additional grouping beyond issue identity.

| Declared underlying source | Trajectories |
|---|---:|
| R2E-Gym/R2E-Gym-Subset | 10,221 |
| SWE-Gym/SWE-Gym | 1,869 |
| SWE-Gym/SWE-Gym-Raw | 3,990 |
| nebius/SWE-rebench | 18,189 |

The existing R2E environment-resolution and grading pipeline does not establish
compatibility for the other three sources. Their source task data, environment
contracts and evaluators need separate qualification. Repository breadth alone
does not establish usable or licensed training coverage.

## Evaluation isolation

The 73 exact-name overlaps are `encode/httpx`, which is reserved by the official
index. Every affected row is marked `reserved_repository_exact_match: true` in
the metadata index and must be excluded from training. No trajectory bodies,
patches or reserved task bodies were read by this census. This is not complete
contamination clearance: repository aliases, forks, copied code and semantic
issue/patch overlap still require review. Do not train the remaining rows merely
because their exact repository names differ.

## Evidence and operational status

- `evidence/data/swe-hero-corpus-001/sources.json` identifies every input.
- `evidence/data/swe-hero-corpus-001/census/report.json` binds the input receipts,
  shard identities, index and counting implementation.
- `index.jsonl` contains only source metadata and shard/row locations.
- Shard 0 uses the original `swe-hero-intake-001` receipt; shards 1–13 use
  `swe-hero-shard-NNN` receipts.
- New R2 uploads use separate `swe-hero-shard-NNN-publish` receipts. A shard is
  remotely verified only when its publish receipt reports `status: verified`.
  Bulk upload jobs were still running when this document was first written;
  local acquisition must not be confused with completed remote storage.

`census_trajectory_corpus.py` was exercised with a two-shard synthetic metadata
fixture containing repeated issues, a duplicate trace ID and a reserved repository
in mixed case. It also rejects resubmitting the same shard. This fixture tests the
inventory logic; it is not part of the training corpus.

Next: finish and verify R2 transfers, perform cross-source task joins and evaluator
qualification, enforce exclusion/split families, measure native supervised tokens,
and expand replay qualification. The 3 × 50M-token training plan remains a target,
not a corpus quantity established by this metadata audit.

## Completed storage and R2E join follow-up

All 14 shard publish jobs subsequently completed. Each receipt reports remote
checksum readback success and matches its intake manifest. Aggregate raw bundle
size including cards/metadata is 2,402,170,043 bytes; Parquet alone is
2,402,012,417 bytes. `evidence/data/swe-hero-corpus-storage-001/report.json` links
all 14 receipts. The census evidence bundle is also verified in R2.

Shard 1 was independently restored from R2 into a separate local directory:
3 files, 151,559,597 bytes, destination checksums verified. The first restore
attempt failed because the local parent directory did not exist; after creating
that parent, `swe-hero-shard-001-restore-002` succeeded. No partial destination was
promoted on the failed attempt. This is a one-shard recovery check, not a complete
restore of all 14 shards.

The expanded `audit_source_task_join.py --census-directory ...` checks the census
index hash and reserved-index identity, rejects duplicate trajectory IDs and
contradictory exclusion flags, excludes the 73 reserved rows first, then selects
only the declared R2E source. All 10,221 selected traces match 3,442 source tasks
across the original eight R2E repositories, with zero unmatched rows. The 23,975
remaining nonreserved rows from other datasets are not joined by this adapter.
Source commit expressions, environments and evaluation contracts still require
qualification; a successful identity join is not executable replay validation.

Evidence: `evidence/data/source-task-join-full-001`. Three additional exclusion
regressions pass, and the full suite ran 194 tests: 178 passed, 16 skipped. The
standalone Parquet census test passed separately in the PyArrow environment.
An initial join attempt stopped at the file-change hashing guard; a follow-up
stat diagnostic found all eight shards stable. A later attempt exposed a relative
path handling bug, which was fixed by resolving and bounding the census directory
to this repository. The successful complete join rechecked every input shard.
The earlier intermittent metadata-change cause remains unestablished; the strict
hashing guard has not been weakened.
