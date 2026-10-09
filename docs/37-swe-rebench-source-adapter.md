# SWE-rebench source adapter

Status: filtered-table identity join implemented; environment and training
qualification incomplete. No GPU or third-party setup code was executed.

## Primary-source findings

The pinned [task card](https://huggingface.co/datasets/nebius/SWE-rebench/blob/89cdfbab4ab1bd8f5a658bb212d1b63624f4f881/README.md)
describes task base commits separately from environment setup commits and points
to an adapted SWE-bench evaluator. Its dataset license is CC BY 4.0, with repository
terms retained separately. Our projection keeps both commits and the original
license declaration; neither image presence nor a permissive-looking label
establishes executable correctness or rights clearance.

The [publisher-linked implementation](https://github.com/SWE-rebench/SWE-bench-fork/blob/980d0cca8aa4e73f1d9f894e906370bef8c4de8a/swebench/harness/test_spec/test_spec.py)
uses `install_config` when constructing environment and evaluation scripts. It
keeps FAIL_TO_PASS and PASS_TO_PASS sets and applies the task's test patch through
its evaluation-script construction. This is a different contract from the R2E
generated-test pipeline. Those installation instructions and test patches must
remain outside agent input. Before evaluating, pin the full harness and images,
inspect setup scripts, and qualify original/reference controls in isolated
containers. The linked commit is research evidence, not an installed harness.

## Local evidence

The 6,542-task filtered Parquet table was downloaded at revision
`89cdfbab4ab1bd8f5a658bb212d1b63624f4f881`, with publisher SHA-256 and byte-size
verification. Raw Parquet size is 33,886,640 bytes. Its metadata projection reads
only instance ID, repository, base commit, environment setup commit, declared
image fields and license name. Issue bodies, hints, patches and test columns are
not deserialized for this join. Raw quarantine storage does contain those columns;
never use the whole table as an agent prompt or unrestricted training input.

`audit_swe_rebench_task_join.py` links the table to the verified SWE-Hero census.
Reserved-repository exclusions run before source selection, and the index's
recorded exclusion flags must agree with the official repository list.

| Outcome | Count |
|---|---:|
| SWE-rebench trajectories selected after exclusions | 18,116 |
| Matched trajectories | 17,798 |
| Unique matched tasks | 6,125 |
| Unique matched repositories | 1,686 |
| Unmatched trajectories | 318 |
| Unique unmatched tasks | 111 |
| Matched rows missing image declarations | 0 |
| Matched rows missing license declarations | 9 |

All 73 reserved-repository matches in the full corpus are removed before this
selection. Image references are publisher strings, not resolved content digests.
The 111 unmatched tasks require investigation against the larger source release;
do not silently map them to similarly named tasks or invent environments.

The license declarations include 103 matched rows labelled Zope Public License
2.1 as well as combined and ambiguous BSD labels. Preserve exact source terms
and resolve file-level notices before admission; the trajectory dataset's small
set of SPDX labels is not sufficient. Missing declarations remain explicit nulls.

Evidence paths:

- `evidence/data/swe-rebench-filtered-001`: pinned intake and manifest.
- `evidence/data/swe-rebench-task-join-001`: joined metadata, unmatched rows and report.
- `artifacts/data/quarantine/swe-rebench-filtered-001`: raw task source.
- `swe-rebench-metadata-001` is an older intake of the separate **OpenHands
  trajectories** dataset; it is not this task table. The task-card intake uses
  `swe-rebench-tasks-metadata-001` to keep the distinction explicit.

Projection tests cover oracle-field exclusion, distinct base/setup commits,
missing declarations, conflicting image references, inconsistent instance IDs,
and source selection. Successful joins remain `training_approved: false`.

## Full-release identity resolution

The two larger source shards at the same pinned revision contain 21,336 tasks.
Their publisher split is called `test`; that name is source nomenclature, not a
new declaration that these tasks are our untouched confirmation set. The existing
reserved-repository exclusions still apply, and none of this data is training
approved. Both raw shards passed publisher size/SHA-256 checks.

`audit_swe_rebench_task_join.py --split test` now matches all 18,116 nonreserved
SWE-rebench trajectories to 6,236 task identities across 1,687 repositories.
The 318 traces previously unmatched represent 111 tasks that are present in this
larger table but have no published image reference. Thus task lookup is resolved;
container construction and runtime qualification remain open for that group.

The refactored `--split filtered` path reproduces the prior 17,798 matches. All
shared task metadata agrees between the filtered and full releases; added source
shard/row locators are preserved separately. `comparison.json` confirms that the
newly joined trajectory-ID set is exactly the earlier unmatched set, and that it
is also exactly the full join's missing-image set. This is a consistency check,
not a proof that a source image, patch, or evaluator is correct.

Evidence: `evidence/data/swe-rebench-task-join-full-001` and
`evidence/data/swe-rebench-task-join-filtered-002`. Each joined record now includes
the source task shard SHA-256 and row number for later allowlisted retrieval.
The full local suite ran 198 tests: 182 passed, 16 skipped.

## Registry and first local image qualification

`resolve_swe_rebench_images.py` selects eight distinct repositories by ordering
image-present task IDs with a fixed SHA-256 rule. All eight tags resolved to
immutable Linux/amd64 digests, with manifest/config digest verification and
recorded compressed layer sizes. Selection is reproducible but excludes tasks
without images and favors repositories with more tasks in the ordered pool; it
is not an unbiased sample for estimating corpus availability or repair quality.

The shared registry reader now supports explicitly tagged Docker Hub references.
The existing R2E wrapper still requires a 40-character commit tag. Untagged,
URL-shaped or malformed references are rejected before network access. A resolved
`:latest` reference is recorded only as an immutable digest for subsequent work.

The smallest sampled image belongs to `biolink/biolink-model-toolkit`, task 172:
1,274,279,744 compressed layer bytes. It was pulled once locally by digest, after
a disk-headroom check. A read-only, networkless, capped container inspection
confirmed checkout HEAD `e421af4ebb7e33ce43a7d9de2e5a6ab4b9e94e5c`, matching the
declared base, and no tracked modifications. Both candidate testbed Python paths
exist; interpreter/import/test compatibility was not exercised.

The repository retains 624 reachable commits, branches and tags. The root also
contains `/issue.md` and `/.env`; their contents were not read by this probe.
The selected known patch/evaluator paths were absent, but this is not an exhaustive
oracle audit. Do not expose the raw image as a clean agent workspace: construct
and verify a parentless source snapshot, inspect extra accessible files, and
qualify base/reference evaluator controls first. The probe container was removed.

Evidence: `swe-rebench-image-resolution-001`, `swe-rebench-image-pull-001`, and
`swe-rebench-image-probe-001` under `evidence/data`. No agent or task tests ran.
The local suite ran 200 tests: 184 passed, 16 skipped. New regressions cover
explicit mutable-tag resolution to digests and rejection before network access;
existing digest/platform checks remain in place. Runpod remains unused.

## Exact-tree snapshot for the first image

The first build rejected an incorrect assumption: PR merge commit
`aca0f5d563b792501464a87832575cebf6cc9a6a` does not have the declared task base as
its immediate parent. The pinned task metadata says `commit_name=head_commit`;
the GitHub PR identity read supplied head `9ccd5a016747842d5b9ad81db60c7537061eb0c5`.
Local Git inspection and the subsequent build verified ancestry from the declared
base. Neither the merge nor head is an immediate child of that base.

The sanitizer now accepts an explicit `ancestor` relationship for this
SWE-rebench path. The existing R2E default remains `first_parent`; its check was
not relaxed. Both modes require exact checkout HEAD, unchanged tracked content,
reconstructed identical tree/blobs/modes, deleted old Git storage and one new
parentless commit. Invalid ancestry must fail before oracle/history deletion.
The build driver now records failed build status explicitly for future failures.

Verified output:

- Image: `sha256:842aa0fa3d3a6f21a8c42e0922f3582d12e3a3fe71a415e572d105eacaf83439`.
- Snapshot commit: `5091df8d1e6c2046cc48ba2c82f5b282aaac4a62`.
- Exact source tree: `84432be06201642e7439bfa397d3f2b11355898f`.
- 30 tracked files, 290,019 bytes; independent runtime manifest comparison passed.
- One reachable commit; original base, PR head and merge commit inaccessible
  through the new repository's Git object store.
- `/issue.md` and `/.env` removed from the container filesystem view.

The verification container was removed. This does not remove original bytes from
Docker lower layers or certify all dependency files. Do not expose the Docker
engine/image layers to the agent or publish this image as a fully scrubbed source
archive. Runtime import compatibility, original/reference evaluator controls and
agent-tool workspace preparation remain open. No task tests or agent ran.

Evidence includes `swe-rebench-pr-identity-001`, commit-graph probes,
`swe-rebench-biolink-snapshot-001` (rejected attempt),
`swe-rebench-biolink-snapshot-002` and `swe-rebench-snapshot-verify-001`.
The publisher's selected-task quality metadata includes `test_score: 0`; preserve
that observation for later quality review rather than infer admission from image
availability or a successful snapshot build.

The first local suite attempt hit two source-hashing mutation guards. Subsequent
runs passed; the latest ran 204 tests, 188 passed and 16 skipped. The hashing
utility now reports changed stat fields and before/after values when rejecting a
mutation; it does not retry automatically or ignore metadata changes. A dedicated
regression confirms even a ctime-only change remains rejected. The cause of the
intermittent local metadata changes is still unestablished.
