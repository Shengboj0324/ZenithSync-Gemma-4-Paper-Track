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


### Offline evaluator dependency diagnosis (2026-10-09)

The original-image base and reference controls in
`evidence/data/swe-rebench-evaluator-controls-001` each collected 93 tests:
93 setup failures, 93 successful teardowns, zero call-phase reports, and zero
collection errors. These observations do not measure repair correctness.
The task's module-scoped fixture invokes `Toolkit()`; the pinned checkout
loads Biolink 4.2.1 schema and predicate mappings from GitHub. Network-disabled
containers cannot retrieve those resources. Both disposable containers were
removed successfully.

`evidence/data/swe-rebench-resource-diagnosis-001` preserves the inspected
checkout sources. `evidence/data/swe-rebench-biolink-resources-001` now contains
the two external YAML resources, their SHA-256 identities, and release revision
`db265a8ffa0903b478a1c6232fb3a2aec4a5dff9`. Each tag-addressed download was
byte-compared with its commit-addressed download. This establishes current
release-resource identity, not proof of the publisher's historical fetched bytes.

Next: implement an explicit, allowlisted offline resource replay; preserve
unmodified test assertions; detect additional schema imports; rerun paired
controls and inspect full test identities before evaluator admission. These
new resources and diagnosis receipts have not yet been published to R2.
No agent or GPU ran, and no training-data admission follows from this work.


### Offline response replay and paired controls (2026-10-09)

Implemented `zenithsync/offline_resources.py`: exact-URL, SHA-256-checked
body replay for the task's urllib and requests GET calls. Unsupported URLs,
body mutations, and unsupported request options fail closed. TLS context is
explicitly bypassed and logged because no TLS connection occurs. The container
still has network disabled. This is an evaluator transport adaptation, not a
claim of identical historical publisher infrastructure.

Controls 003–006 preserve adapter compatibility failures (TLS context and
Python 3.9 response `mode` requirements). Control 002 records a Linux argv-size
failure; the disposable-container runner now stages the probe as a file.
Control 007 first reached assertions; an import-only script cleanup occurred
during that run, so control 008 was rerun against stable source and is the
preferred evidence. Both containers in each completed pair were removed.

`evidence/data/swe-rebench-evaluator-controls-008/paired-observations.json`
binds the full node-ID observations: 93 distinct tests in both roles, all setup
and teardown phases successful; base 92 passed / 1 failed, reference 93 passed.
The sole transition is `test_get_associations_gene_to_chemical`, the published
FAIL_TO_PASS test. Both fetched exactly the two allowlisted resources, and
tracked diffs were unchanged by tests. No agent ran.

Validation: pinned lightweight suite 210 tests, 188 passed and 22 skipped
(including six requests-dependent tests); those six adapter tests separately
passed in the requests-enabled local environment. No GPU validation follows.

Outstanding: audit the publisher's truncated PASS_TO_PASS identifiers, verify
sanitized-image equivalence, integrate qualified resource replay into the
source-task runtime, and assess rights/splits before any training admission.


### Sanitized-image evaluator equivalence (2026-10-09)

`evidence/data/swe-rebench-snapshot-controls-001` runs the same test/reference
patches and hashed resource replay on the sanitized image. The probe checks
snapshot HEAD, tree identity, and initially clean tracked source. Both control
containers completed and were removed; testing did not change tracked diffs.

`zenithsync/pytest_controls.py` retains full pytest identities and maps the
publisher's whitespace-truncated names to groups. Every member must match the
expected transition. Missing/duplicate phases, failed setup/teardown, skips,
collection errors, contradictory exits, conflicting expectations, and unequal
coverage fail closed. This is deliberately stricter than last-write-wins parsing.

`evidence/data/swe-rebench-control-comparison-001/comparison.json` binds both
runs: 93 full identities, 82 publisher names, five collision groups; all
transitions match. The original and sanitized controls have identical per-test
outcomes and resource events. Each base passes 92 tests and fails the intended
repair test; each reference passes all 93. This verifies task-specific evaluator
equivalence, not general image isolation or model performance. Snapshot lower
layers and unreviewed dependency content remain outside the isolation claim.

Tests: 215 discovered, 193 passed, 22 skipped in the lightweight pinned runtime.
Five new comparator tests exercise hidden collision-member failures, phase
integrity, setup/teardown errors, skips, exit consistency and coverage conflicts.
The six requests-dependent adapter tests passed separately in the preceding
cycle. Prior offline evaluator bundle R2 publication completed with remote
hash verification: 180 files, 8,510,129 bytes (`swe-rebench-offline-evaluator-publish-001`).

Next: integrate the resource replay and strict outcomes into source trajectory
execution/patch grading; source-specific rights and admission remain required.


### Candidate patch grading integration (2026-10-09)

Added `scripts/grade_swe_rebench_patch.py`, explicitly scoped to task 172.
It verifies the qualified control inputs, rechecks publisher transitions, runs
one candidate in the sanitized offline evaluator, checks environment/resource
identity and cleanup, then compares full test identities with the qualified
reference. Infrastructure errors do not become repair scores. Candidate runs
receive only the candidate and test patches, without a reference-patch payload.
This entry point grades bytes; it does not yet validate teacher/agent provenance.

Candidate source allowance is currently `bmt/toolkit.py`. Candidate patches are
applied to the Git index so newly added files are also included in the path
check. This restricts changes to the evaluated source surface; it is not a
security proof against malicious source code executing inside the sandbox.

Runtime acceptance evidence:
- `swe-rebench-empty-grade-002`: 93 cases, one disagreement, repair rejected.
- `swe-rebench-reference-grade-002`: 93 cases, zero disagreements.
- `swe-rebench-injection-grade-001`: adding `tests/injected.py` rejected before
  test execution; container removed. No successful grading report is emitted.

These are grader controls, not model-generated repairs. The source-control
suite ran 217 tests: 195 passed, 22 skipped. Two new candidate-comparison tests
check that actual repair failure is reported but missing coverage is rejected.

Three candidate teacher traces for task 172 are present in the verified full
join: `2cc9a006-de14-4fbb-ba13-8c17b59245c8`,
`e7d37fbd-fc5c-4102-a7bc-7a9972287d84`, and
`808755ac-3ab0-431d-9596-0929241ce8c0`. Their commands have not yet been reviewed
or replayed. Next: resolve and verify their source shards, review path/action
adaptation, integrate runtime resource availability, replay native actions,
and independently grade submitted patches. Training admission remains false.


### Three teacher traces verified and screened (2026-10-09)

`scripts/review_swe_rebench_teacher.py` verifies the census/reserved-repository
inputs, source dataset revision and shard hashes, selects each trace by exact
ID, validates source serialization, and exports actions for review without
executing them. `swe-rebench-teacher-review-003` completed for all three traces.
Earlier reads were rejected by the file-stability guard: shard 7 changed flags
and timestamps during hashing; shard 9 timed out and later changed flags/time.
Stable subsequent full hashes matched the pinned receipts. The guard was not
relaxed. Review directories 001/002 are incomplete, not successful batches.

Executable source-action counts (excluding think, including finish): first
trace 55, second 56, third 49. All exceed the current 40-call ceiling before
any native-tool expansion. No trace is admitted unchanged. The first trace
also attempts package installation and creates several debugging scripts;
those commands require offline replay accounting rather than silent omission.

Diagnostic source-edit projections in `swe-rebench-edit-projections-001` apply
only exact unique editor replacements to the captured original `bmt/toolkit.py`.
They omit shell effects and created files, so they are not replay submissions.
The first projection grades 92/93 passing (one repair disagreement); the third
projection grades 93/93 passing. The second cannot be projected sequentially:
its first replacement at message 86 has zero exact matches in the base source.
This does not prove its full trajectory fails; preceding command effects and
source-state differences still need investigation.

The third trace provides a promising repair target but not a budget-compliant
trajectory. Next: investigate second-trace state divergence; replay the third
with explicit resource/interpreter setup and fresh observations; independently
grade its submitted patch; then evaluate a separately generated shorter native
trajectory. Any shortened trace must be independently executed and validated,
not relabeled as the original teacher history. Failure traces may later support
preference/negative data only after the relevant provenance and quality gates.


### Native replay integration started (2026-10-09; result pending)

The inspected snapshot has no untracked installer and no initial `/workspace`;
its default Python points to conda base rather than the task environment.
`source_workspace.prepare_source_workspace` now accepts an explicitly empty
installer-leftover profile while preserving existing R2E defaults. The native
runner accepts explicitly pinned source shards, numeric issue identities,
reserved-repository exclusion before trajectory deserialization, and task-172
Python/resource setup. Source actions retain order and initial-root mapping.

`zenithsync/replay_resources.py` stages only the two pinned response bodies,
the transport adapter, and Python startup integration outside the repository.
Startup failure exits the Python process rather than silently continuing.
The profile selects `/opt/conda/envs/testbed/bin` and validates model-schema
version before native actions. No reference or evaluator-test patch is staged.

The third trace's 60-call compatibility profile is saved in
`swe-rebench-replay-profile-001`; it does not change the 40-call admission limit.
Replay process session 46435 (local PID 22902 when sampled) remains live in
host dependency import. A native process sample identified blocking reads;
open-file inspection showed a workspace `.venv` dependency bytecode file.
No replay container or successful replay receipt existed at this observation.
Do not restart based on absent output; poll this exact live process first.

Validation after changes: 219 tests, 197 passed, 22 skipped. Added numeric
identity validation and resource archive/tamper tests. These new integration
files and eventual runtime evidence still require R2 publication after the
replay completes or produces a concrete failure. Pod remains stopped.


### Second-trace mismatch isolated (2026-10-09)

`swe-rebench-teacher-state-mismatch-001` proves an exact static discrepancy:
at message 86, the entire teacher old-string differs from the pinned base
function by one line indented four spaces less. Changing only that indentation
in a diagnostic string makes the two strings equal. No trace or source patch
was altered to force compatibility; the historical cause remains unestablished.
This must be retained as source-state uncertainty, not automatically classified
as a failed repair or silently repaired training record.

The existing native replay session 46435 remains live. Repeated open-file
observations advanced through anyio, google-adk, docker, and cryptography
module bytecode reads in the workspace dependency environment. No duplicate
process has been started. Full replay and grading remain pending.


### Budget-first source environment selection (2026-10-09)

The original eight-image sample has only one trace fitting the estimated
40-call limit without currently known adapter flags. Continue its Biolink
replay as compatibility evidence, but use the corpus-wide audit for future
cost-prioritized selection.

`scripts/select_budget_rebench_tasks.py` joins hash-verified budget records to
the verified source-task join, rejects duplicate/mismatched identities, and
requires complete linkage. Of 2,643 budget-fit SWE-rebench traces, 2,621 have
publisher image references, spanning 1,575 issues in 902 repositories. The
remaining 22 are not silently treated as runnable. Outputs are in
`swe-rebench-budget-cohort-001`.

The existing deterministic per-repository resolver successfully pinned eight
images from that cohort in `swe-rebench-budget-images-001`: oasis-open/cti-taxii-server
44; stitchfix/nodebook 8; nylas/nylas-python 78; awdeorio/mailmerge 135;
dedupeio/dedupe 1062; inhumantsar/python-ec2-reaper 15; networkx/networkx 6471;
mikedh/trimesh 650. Compressed layer sizes range from 1,324,887,523 to
2,093,707,382 bytes. No new image layers were downloaded and no runtimes were
qualified by this metadata step. The cohort is deliberately cost-selected;
it cannot support an unbiased general agent success-rate claim.

Next choose additional replay tasks from this budget-fit cohort, then qualify
source state, dependencies, evaluator controls, and rights before admission.
The original native replay process remains live in host dependency imports.


### Native replay 001 terminated; controlled retry 002 started

Session 46435 completed with failure during offline resource staging:
`predicate_mapping.yaml` metadata changed during inventory (ctime/mtime and
flags). No source actions ran. The retained replay-001 receipt confirms the
owned container was removed with no cleanup errors. Subsequent stable full
hashes of both public YAML resources matched their pinned identities.
Replay-002 was then started in a fresh output directory (session 88472).
This is a retry after a terminal, diagnosed failure, not a duplicate live run.
The hash-stability guard remains unchanged. Its runtime result is pending.

The budget-fit cohort and eight pinned image metadata records are now R2
published with remote hash verification: 40 files, 2,221,152 bytes; receipt
`swe-rebench-budget-cohort-publish-001/receipt.json`.


### Native replay completed and independently graded (2026-10-09)

The workspace-linked runtime repeatedly blocked on local dependency bytecode
reads. A separate environment at `/tmp/zenithsync-native-isolated-p1` was built
with the captured dependency constraints and retained official package wheels.
Its 160 installed distributions have no changed versions among common original
dependencies (excluding packaging tools); `pip check` reports no broken
requirements. Core pins remain swegemma 0.2.10, adk-submission 0.2.13,
google-adk 1.36.1 and adk-eval-core 0.1.0. The import check took 10.16 seconds
and found no workspace `.venv` module imports. This is the native replay runtime;
it does not replace the separately pinned training/tokenizer runtimes.

After this independent check, replay-002 was intentionally interrupted with
SIGINT while still importing dependencies, before container creation. Its
terminal exit 130 and retirement reason are recorded; it was not duplicated.
Replay-003 used the isolated runtime and completed all source actions in order:
53 action events, 49 native invocations, 48 charged calls. Four think actions
were not executed; finish invokes submission but is not a charged call.
Fresh tool observations were retained. The submitted patch is 1,653 bytes,
SHA-256 `d7b778aa81b96d53e472a417de56c9ed5c8be844593eaae07d3587f960a00902`.
The owned replay container was removed with no cleanup errors.

`swe-rebench-native-grade-003` independently evaluates the exact submitted
patch: all 93 test outcomes match the qualified reference, zero disagreements,
tracked patch unchanged, evaluator container removed. Earlier grading attempts
were rejected on metadata changes while hashing saved control/input files;
stable subsequent hashes matched the original pins. Guards were not relaxed.

This is a successful teacher-action replay in an explicitly adapted native
environment, not a newly trained model result. At 48 charged calls it fails the
40-call admission limit; native context/mask audit and rights review are also
outstanding. Use the isolated environment for subsequent native replay commands,
and prefer the budget-fit cohort for additional examples. No GPU was used.


### Native history, masks and linked admission audit (2026-10-09)

`build_rebench_replay_history.py` reads only allowlisted task fields from the
pinned source shard, reconstructs the initial prompt, and binds all 49 native
exchanges to the captured replay. The 100-message history contains fresh tool
observations, not original teacher responses or reasoning. This is an action
supervision projection; it does not establish original teacher conditioning.

Using Transformers 5.13.1 / tokenizers 0.22.2 and the hash-verified external
Gemma tokenizer assets, the untruncated rendering contains 26,118 input tokens
and 5,530 supervised next-token labels. With the 8,192-token output reserve,
required context is 34,310, exceeding 32,768 by 1,542 tokens. The independent
48 charged calls also exceed the 40-call cap by eight.

The SWE-rebench grader now optionally binds its exact patch to a completed,
cleaned-up replay receipt. `swe-rebench-native-grade-bound-001` independently
repeated the 93/93 outcome match with that binding. The shared admission checker
accepts an explicit full-node-ID reference grading backend, rejects unknown
backends/task/attempt mismatches, and preserves existing R2E behavior.
`swe-rebench-native-admission-001` verifies the cross-artifact links and reports
both budget/context blockers; training approval remains false.

Validation: 221 tests, 199 passed, 22 skipped on the completed rerun. The first
suite attempt failed two existing checks because source-file metadata changed
during hashing; both failures and the successful rerun are retained. No guards
were weakened. A passing repair is not enough to admit this unchanged history.
Next prioritize budget-fit candidates and qualify native context on their fresh
replays rather than silently deleting observations or relaxing the policy.


### Budget-fit task triage — 2026-10-09

`review_budget_rebench_tasks.py` extracted eight issue/environment records from
both pinned full-task shards. It verifies source/intake hashes and revision,
checks repository identities against the reserved index before body extraction,
and reads neither solution patches nor test patches. Execution succeeded with
eight unique candidates in `swe-rebench-budget-review-001`.

| Task | Issue class | Publisher fail-to-pass / pass-to-pass | Eligible estimated calls |
| --- | --- | --- | --- |
| mailmerge-135 | UTF-8 BOM corrupts CSV header lookup | 1 / 26 | 37, 37 |
| dedupe-1062 | Inconsistent alphanumeric predicate | 1 / 13 | 34 |
| python-ec2-reaper-15 | Environment string interpreted as Boolean | 1 / 2 | 37, 40 |
| trimesh-650 | OBJ parser fails on one normal vector | 1 / 8 | 30, 38 |
| networkx-6471 | Backend decorator rejects keyword graph argument | 1 / 0 | 37, 38 |
| nylas-python-78 | Authentication state argument support | 1 / 9 | 33, 34 |
| cti-taxii-server-44 | Object-ID membership checked against objects | 1 / 26 | 40 |
| nodebook-8 | Python 3 AST function argument handling | 1 / 18 | 35 |

These are publisher test counts, not freshly observed outcomes. All eight list
zero fail-to-fail and pass-to-fail cases. Estimated calls exclude thinking and
submission; native context fit is still unmeasured. A mathematical package name
does not imply an algorithmically difficult task: the NetworkX issue is dispatch
argument handling and has particularly narrow listed regression coverage.

Next qualify nodebook-8 as an additional AST/semantic repair case, with mailmerge
as a contrasting encoding case. This is an infrastructure qualification order,
not a performance ranking or a change to the full training-corpus objective.
Nodebook has a 35-call candidate and 18 listed preserved tests, but replay,
license/lineage checks, source snapshot isolation, base/reference controls and
context masks must still pass. No candidate is training-approved by this review.
Local disk has approximately 12 GiB available; check Docker capacity before
pulling its 1.61 GB compressed image. No new image was downloaded in this step.


### Nodebook original-image controls — 2026-10-09

Downloaded only the selected immutable Nodebook image, digest
`f97d42c67e9108930c87640f0f5c3de050603b4e73e26771ff47108eba68fef4`.
The read-only image probe confirms the expected source HEAD, clean tracked
checkout and 36 reachable Git commits. Original-image history is not safe for
agent exposure yet. The isolated layout probe imports Nodebook from
`/testbed/nodebook/__init__.py` using the task Conda interpreter; both probe
containers were removed.

Added `extract_rebench_evaluator_input.py` for pinned, repository-checked
extraction of evaluator-only patches. Task identity is read and compared before
oracle fields; source/intake/resolution/index hashes are bound. Nodebook input
contains a 777-byte reference patch and 1,244-byte test patch. These files are
not agent inputs. `run_rebench_controls.py` now uses an explicit validated
execution profile and the shared control probe, with separate base/reference
containers, no network, complete pytest phase identities, source-import checks,
and tracked-diff checks. Base containers do not receive the reference patch.
The existing Biolink entrypoint supplies its prior configuration explicitly.

`nodebook-controls-002` (under the `swe-rebench-` evidence prefix) reproduces all
19 publisher transitions exactly: 18 base passes plus one failure, then 19
reference passes. No setup/teardown failures or identity collisions; both
containers were removed and tracked diffs stayed unchanged during tests.
`biolink-template-regression-002` independently preserves all 93 earlier
transitions (92 to 93 passing). These results qualify original-image evaluator
behavior only, not the sanitized environment or teacher trajectory.

The full suite rerun has 223 tests: 201 passed and 22 skipped. First-run failures
were metadata-change guards on existing `run_p1_server.py` and `model_intake.py`;
both logs are retained in `swe-rebench-nodebook-validation-001`. The first
Nodebook control launch likewise rejected changed metadata on
`compare_source_snapshot.py` before creating a container; the first Biolink
regression launch rejected changed metadata on `install-config.json`. Guards
remain unchanged. Final runs succeeded after stable rereads.

A sampled local extraction process stalled while PyArrow imported Pandas and
read a module file; it later completed successfully without a duplicate run.
A separate `/tmp/zenithsync-data-isolated-p1` environment now imports PyArrow
25.0.1 without loading Pandas and passes dependency checks. It is for future
local data work, not a change to the pinned tokenizer or GPU training stack.

Next: resolve source repair commit identity, sanitize Nodebook history, prove
base/reference parity in the snapshot, and replay the 35-call candidate before
measuring full native tokens and masks. No training admission or model gain is
claimed. Runpod remained stopped throughout.


### Nodebook sanitized snapshot and native replay — 2026-10-09

GitHub PR 8 metadata identifies head `d0cef3572048225cbfe0f93400c359c37dc0504b`
and merge `76e246e5089f1322c2c17fd9176ec365e7735aac`; the captured public API
response and its hash are in `swe-rebench-nodebook-pr-001`. The task metadata
specifies head-commit provenance. Snapshot construction verifies that declared
base `b6e1ec614fd39acb740b04e99ee7e97d99122420` is an ancestor of that head.

Added reusable `verify_source_snapshot.py` and snapshot selection to the explicit
control runner. Independent checks compare tracked bytes/modes against the
sanitizer manifest, require one parentless commit, reject remotes and old Git
objects, and check declared oracle paths. The first snapshot retained an
untracked `/testbed/issue.md`; native preparation correctly rejected it before
teacher actions and cleaned up. The builder now explicitly removes that path
only after checking it does not overlap tracked source. Both snapshot versions
and the failed replay are retained, not overwritten.

The accepted second snapshot is image
`sha256:a37b46e63ad2fd9e4a17f3a89858724d5b55085178871178e4ef46421b887abf`,
commit `e818b0a9a2298de03fb9a2c927ba1758b747a3c5`, tree
`7779c02fe5d673491d3dff50ffceb566f440931a`. It preserves 15 tracked files and
78,891 bytes exactly. Base, repair-head and merge objects are inaccessible;
known issue/environment files are absent. Inherited Docker layer bytes remain
outside the mounted-filesystem verification scope. Snapshot controls reproduce
all 19 full-node-ID transitions and match original-image base/reference outcomes
exactly (`swe-rebench-nodebook-snapshot-controls-002/comparison.json`).

Teacher review can now select an exact census-bound task/trajectory. The selected
trace is `cdd22e5e-c7cd-4a5f-aab8-2afb2064d0df`, source shard 13. Review found one
root-independent `python --version` command. Preflight permits only this exact
additional command; suffixes/options/root changes remain rejected. The explicit
`--conda-testbed` option sets the previously qualified interpreter path and
requires no unexplained untracked installer file. It does not disable workspace
checks. Recorded teacher reasoning remains omitted from replay actions.

`swe-rebench-nodebook-native-replay-002` completes all actions with fresh native
observations, 35 charged calls within the 40-call ceiling, and a 472-byte patch
SHA-256 `5a1b62926d0b536bedd3eaba6880591fd1c0d8e4db68a7a8c9b564453c8d14c4`.
The disposable container was removed without cleanup errors. Status is explicitly
`replayed_not_graded`; teacher tool success is not an independent repair score.
Next: grade this exact patch using the qualified snapshot controls, then render
native history and audit masks/context. No training approval or model gain is
claimed. Latest full suite: 224 tests, 202 passed, 22 skipped. No GPU used.


### Nodebook linked grading and context admission — 2026-10-09

Added `grade_rebench_replay.py` for exact replay-patch grading against qualified
profile/snapshot controls. It rechecks the full paired-control transitions,
requires identical execution profile/test inputs/snapshot artifacts, binds
replay task/repository/base/image and patch hashes, and verifies cleanup and
unchanged tracked diffs. Candidate containers receive only the candidate and
evaluator test patches, never the reference repair. Source-change permissions
are explicit; Nodebook permits only `nodebook/nodebookcore.py`.

`swe-rebench-nodebook-native-grade-002` matches all 19 qualified reference
outcomes with zero disagreements. Independent synthetic negative controls in
`swe-rebench-nodebook-negative-controls-001` establish that an empty candidate
fails the exact function-argument regression, while a new unauthorized source
file is rejected before tests start. Negative controls are evaluator fixtures,
not training trajectories or model attempts.

Generalized native history reconstruction to a provenance-verified task receipt
and the exact source shard. Task identity is checked before issue deserialization;
source/intake/index/protocol/event bindings are retained. History version 002
contains 74 messages and 36 native exchanges, including terminal submission.
Its content is byte-identical to version 001, so the existing content-addressed
token audit applies to both. Initial system/issue messages are reconstructed;
original teacher conditioning is not established and teacher reasoning is omitted.

The pinned Transformers 5.13.1/tokenizers 0.22.2 audit, using verified external
Gemma tokenizer assets, reports **17,353 input tokens and 4,183 supervised shifted
labels**, without truncation. Input plus the 8,192-token reserve equals 25,545,
leaving 7,223 tokens under 32,768. Native charged calls are 35/40. The linked
`swe-rebench-nodebook-native-admission-002` reports no mechanical blockers and
`mechanical_checks_passed: true`, but **training_approved remains false**.
Rights/attribution, frozen split and duplicate review, remaining source/image
qualification, and actual training-runtime memory gates still apply. These
checks establish one usable mechanical candidate, not corpus sufficiency,
GPU fit, new model performance, or a general correctness guarantee.

Validation: full local suite 226 tests, 204 passed and 22 skipped. An additional
focused two-test run passed after rejecting the ambiguous `.` source allowance;
the exact patch was independently regraded and admission relinked afterward.
Runpod stayed stopped. Next complete rights/isolation review and connect qualified
candidates to the existing training-corpus assembly gates without bypassing them.
# Mailmerge expansion candidate — 2026-10-09

Task `awdeorio__mailmerge-135` addresses a UTF-8 BOM being treated as part of the
first CSV header. The immutable image
`swerebench/sweb.eval.x86_64.awdeorio_1776_mailmerge-135@sha256:326983bf80d8a90dd17e6827d0ea95b6d70730501e79312a3c5ee9edfada26b8`
was downloaded locally. The probe confirmed base commit
`930bc506f0f8d0c9c057019c399a491c1641909c`, a clean tracked worktree and 906
reachable Git commits. Agent execution must therefore wait for source isolation.
The working environment is `/opt/miniconda3/envs/testbed/bin/python`, importing
`/testbed/mailmerge/__init__.py` from a `/testbed` working directory.

Identity-checked evaluator-only extraction is retained in
`evidence/data/swe-rebench-mailmerge-input-002`. The first attempt stopped when
the filesystem changed receipt metadata during hashing; the guard was retained
and the subsequent stable read succeeded. Base/reference controls ran offline
using `tests/test_main.py`, with both disposable containers cleaned up. Strict
full-node comparison establishes 27 publisher transitions: base 26 passed/1
failed, reference 27 passed, no skipped or unexpected outcomes. Evidence:
`evidence/data/swe-rebench-mailmerge-controls-001/comparison.json`.

The selected census-bound teacher trace
`3c169251-e0a7-46a9-b46d-32b8d4105d3d` contains 22 shell and 15 editor calls,
three thoughts and a finish action. This is a static 37-call count, not a native
execution result. Its actions still require reviewed adaptations (including a
recorded editable-install command) and fresh observations in an isolated source
snapshot. No replay, tokenizer audit, rights approval, frozen split or training
admission has been completed for this task. Evaluator patches remain separate
from agent inputs. This supplies a potential foundational training example, not
evidence of a novel agent capability or a difficult held-out benchmark result.

## Mailmerge isolated replay and context result

The public PR 135 API binds head `003436804d8e3a1982e716f37fb2c285c0ef9cd7`
and merge `3d3708038a790e0b5a698cee4a7b359d53e14501`; its response is retained in
`swe-rebench-mailmerge-pr-001`. Snapshot image
`sha256:aa71f97fb45c16270d061a987963c3a80f3fadb3b22cc46fd00261bb5f768ccb`
preserves all 28 tracked files / 161,797 bytes and source tree
`1e51ff974a65aaca7f01f64cdd435b9e106d74bd`. Independent verification finds exactly
one parentless commit and cannot access the former base, solution or merge.
Declared issue/oracle files were removed. Inherited image-layer bytes remain
outside this mounted-filesystem audit. All 27 paired control outcomes match the
original image exactly.

Replay `swe-rebench-mailmerge-native-replay-001` completed 37 shell/editor calls
with fresh observations, preserved action order and no teacher-thought execution.
The disposable container was removed. Its 536-byte patch SHA-256 is
`70a0953570c01462e79d3ea2b5eb4c6414128079eac6dbb45c1577f8e20c4e64`.
Independent grading matched the reference on all 27 tests. This reproduces a
teacher patch; it does not measure a newly trained agent.

Native history/token export contains 30,191 input tokens and 7,415 supervised
targets, with no truncation. Although the input fits 32,768, adding the existing
8,192 output reserve gives 38,383, exceeding the budget by 5,615. Mechanical
assessment in `swe-rebench-mailmerge-native-admission-001` therefore rejects the
trace under the current context policy. No training admission was created.

Replay now has mutually exclusive Conda/Miniconda runtime selectors. Inspection
showed `/opt/miniconda3/envs/testbed` resolves to `/opt/conda/envs/testbed`; these
are aliases, not different installed environments. Actual Python is 3.9.20 and
pytest is 8.3.3, distinct from the publisher's environment text. The paired tests
above establish the observed behavior. Notice capture now canonicalizes both
the runtime prefix and candidate notice path before checking containment; the
first failed capture is retained. The successful capture preserves source MIT
notice (Andrew DeOrio, 2016) and selected pytest/Jinja2/click notices, without
asserting exhaustive rights approval. Full regression suite after these changes:
277 tests, 230 passed, 47 skipped.


### Mailmerge alternate trace: independent replay and context rejection

Trace `8ac352d1-ec64-4e81-8999-778c27f6739c` was extracted from the pinned
SWE-Hero shard 011, reviewed, and replayed against the same verified offline
snapshot. All 37 charged shell/editor calls completed; the container was removed.
The submitted patch changes only the CSV reader encoding to `utf-8-sig`.
Independent grading matched all 27 reference outcomes, with zero disagreements.
This is teacher replay evidence, not learned Gemma performance.

The untruncated native history has 28,451 input tokens and 7,870 supervised
targets. With the unchanged 8,192-token output reserve, total demand is 36,643:
3,875 above the 32,768 limit. Assessment `swe-rebench-mailmerge-native-admission-002`
rejects training admission. Both reviewed Mailmerge traces fail this policy;
no reserve reduction or truncation was used. Rights and split admission remain
separate, unfinished requirements. No training corpus admission is implied.

This supersedes the earlier next-step note proposing the already completed
Mailmerge snapshot/replay. Next acquisition work should select a different
shorter candidate, preserving independent grading and the same context gate.
The Runpod Pod remains stopped; all this work ran locally.


### Complete source-token cost screening (local, no GPU)

Implemented `scripts/screen_source_token_cost.py` and
`scripts/merge_source_token_screens.py`. The screening binds census, cohort,
reserved repository index, intake receipts, source shards and exact model
tokenizer bytes before deserializing selected histories. All 14 shards now
cover exactly 2,621 image-present candidates (1,575 tasks, 902 repositories).
The merged result is `evidence/data/source-token-cost-full-001`.

Ranking uses the token count of canonical converted source-message JSON with
no truncation, padding or special tokens. This includes source observations
and reasoning. It is NOT native replay context, a bound on native length, a
quality score, or training admission. No token-fit threshold is inferred from
this proxy. Native replay, independent grading, actual token masking and
context admission remain mandatory. The sample remains cost-selected and
cannot estimate unbiased agent performance.

The eight shortest distinct repositories were bound to task records, their
Linux amd64 image metadata resolved (no layer download), and their issue and
environment records reviewed. Evidence: `source-token-shortlist-001`,
`source-token-images-002`, `source-token-task-review-001`. Shortness alone is
insufficient: dkey and mypy_extensions request version information/changes;
Narwhals requests documentation despite four published fail-to-pass tests,
which warrants inspecting evaluator relevance before use. Other candidates
include optional dataframe mutation, decorator return propagation, logger
optional arguments, debug-expression formatting and empty-file lint behavior.
These are potential bootstrap examples, not evidence of industrial capability.

Five selection tests cover reserved names and flags, linkage substitution,
duplicates and shard boundaries. A real incomplete cohort was rejected before
merge output. The first empty-shard run exposed an Arrow null-type issue;
explicit string typing fixed it, and all empty shards subsequently completed.
A source metadata change on first read stopped another attempt; the failure
was retained and a fresh run passed unchanged byte-identity guards. Final CPU
suite: 282 tests, 258 passed, 24 skipped in the isolated Torch environment.
No CUDA/full-model capability follows from those results.

Next: inspect task/evaluator relevance for a code-behavior candidate, then
qualify its clean-source controls and replay. Expand task diversity and
complexity alongside context feasibility; do not optimize training quality
solely for shortness. The Pod remains stopped; P1 and corpus admission remain
incomplete.


### Task/evaluator alignment requirement and corpus schema v2

The pinned task `narwhals-dev__narwhals-941` fails task-alignment review.
Its request asks for README media links, but the evaluator adds dataframe
column-selection assertions; all four published fail-to-pass cases exercise
that behavior. The reference patch contains both documentation and indexing
changes. Record `evidence/data/task-alignment-narwhals-001/review.json` binds
these inputs and rejects all three corresponding candidates in the screened
cohort. The oracle patches remain evaluator-only. This finding does not
establish a dataset-wide error rate.

Corpus schema v2 supersedes the earlier three-gate admission contract: it
requires `task_alignment`, `rights_and_attribution`, `split_isolation`, and
`runtime_qualification`. Alignment evidence must review the stated behavior,
reference change and evaluator relevance for every included task, including
incidental merge changes and missing test coverage. A green evaluator result
is insufficient. Generic receipt validation enforces content identity and
evidence presence; it does not automatically establish the semantic truth of
a review. No genuine passing alignment receipt has been created yet.

Schema v1 remains readable for inspection but cannot train, even if it carries
legacy passed receipts. New assembly emits v2. The real Nodebook candidate was
rebuilt as `artifacts/data/quarantine/training-corpus-002` and remains quarantine:
17,353 input tokens / 4,183 supervised targets, one example. Its manifest hash
is `f9b731e8af73f3e7597abc6c14dc4aeafaeee8e6cee0ffa94fe2de5b5d87fc5d`.
The schema change alters corpus content identity; schedules and admission
receipts must be regenerated and reviewed, never relabeled from v1.

Actual v1 and v2 candidate training denials are retained in
`evidence/p1/task-alignment-denial-001`. The current worker bundle passed all
six isolated CLI imports in `evidence/p1/task-alignment-source-001`. Final
CPU suite: 285 tests, 261 passed, 24 skipped. Tests include forged alignment
bindings, omitted alignment gates and an otherwise admitted legacy corpus.
These checks establish local enforcement, not semantic review accuracy or
full-model/CUDA qualification. P1 remains active; no GPU was used.

Next: select a substantive code-behavior candidate whose problem statement,
reference patch and tests agree; perform paired controls and native replay.
Continue rights, split and task review before any real admission or training.


### Shortlist alignment review and Datetransform base inspection

Reviewed the seven remaining shortlisted task/reference/test bundles; the
inputs and decisions are in `source-token-alignment-inputs-001` and
`task-alignment-shortlist-001`. Mypy_extensions task 57 is rejected for the
same class of issue/evaluator mismatch: its request is a version update, but
its added evaluator checks NoReturn deprecation. Three cohort traces are
affected. Dkey task 18 is held: its reference queries `VersionInfo('mgen')`
while exposing dkey version information, and its tests only assert attribute
existence. This is insufficient evidence of correct version provenance.

Pydbg, Ignite, flake8-fancy-header, easy-ptvsd and Datetransform have provisional
static alignment, with narrow coverage limits explicitly recorded. None has
received training approval. The findings are from a cost-selected eight-task
shortlist; they cannot estimate a dataset-wide error rate.

Datetransform task 2 was selected for further qualification: optional mutation
is a concrete behavioral contract, with tests for the default copy behavior
and explicit inplace=True. Its pinned image was pulled locally and probed
without running task tests. The image checkout is
`51571c772ad0939dd35f1e9788fbbabfd8117b88`, not the expected
`33b75b1948cad92aa4edf91850887f27562b0632`. Read-only Git inspection confirms
the expected commit exists and has tree
`696e971b020003634b90ffa249380b5bead8fc50`. The only tracked differences
between base and image HEAD are files `=1.0.0` and `=1.16.0`; the image HEAD
commit is titled Environment setup changes. The original full Git history
also contains the solution commits, so it is unsuitable as an agent workspace.

Evidence: `datetransform-probe-001`, `datetransform-base-audit-001`. Both owned
probe containers were removed. No repair score or environment compatibility
claim was produced. Next: derive an explicitly bound baseline at the requested
commit, verify the exact tree, then run base/reference controls and sanitize
solution history before replay. Preserve the original image and all identity
checks; do not reinterpret the setup commit as the official base.

This cycle changed data-quality evidence and candidate selection, not training
code. The Pod remains stopped; P1 is incomplete and no data was admitted.


### Datetransform exact-base normalization and paired controls

Implemented `zenithsync/source_base.py` and
`scripts/prepare_rebench_baseline.py` for disposable evaluator containers whose
image HEAD is an environment setup commit. The build requires a successful
probe bound to the immutable parent image, the observed initial HEAD and clean
tracked source. It performs a non-forced detached checkout, disables checkout
hooks, verifies the target tree, and hashes every tracked file against Git
blobs. Untracked files and solution history deliberately remain; the result
is explicitly not an agent-approved workspace. The parent image is unchanged.

Datetransform's derived baseline is
`sha256:e5c7fa51e8347815c94030d656efecb882773209da57a6c7fd3c708c7fb651cd`.
Readback preserves nine tracked files at commit
`33b75b1948cad92aa4edf91850887f27562b0632`, tree
`696e971b020003634b90ffa249380b5bead8fc50`. Evidence is in
`datetransform-baseline-001`, `datetransform-baseline-readback-001`,
`datetransform-baseline-input-001`, and `datetransform-controls-001`.

Paired evaluator controls import `datetransform.transform` from the checkout
and match all three published transitions by full test identity: base passes
one and fails two, reference passes all three. Test execution did not modify
the tracked diff, and owned control/readback containers were removed. This
qualifies the narrow three-test evaluator behavior, not broad correctness or
agent performance. No teacher replay or trained model ran in this cycle.

New tests cover wrong initial HEAD, tracked edits, checkout-hook suppression,
exact base restoration and preservation of unrelated untracked files. Final
CPU suite: 288 tests, 264 passed, 24 skipped. Runtime code for the normalizer
also executed successfully inside the real Linux baseline build.

Next: bind the solution commit, sanitize reachable history and known oracle
files while preserving the exact tree, independently verify the resulting
workspace, repeat paired controls to check parity, then replay and grade a
selected trajectory. Rights, split and semantic admission remain separate.
No GPU was used; keep the Pod stopped. P1 remains incomplete.


### Datetransform sanitized replay and two-example corpus integration

Bound PR 2 solution head `82085ef8e7f17cce30732a179cf5cf280eaa1754` and merge
`7331185d854f14734a33ee00a84367d33c2aada0` to the captured GitHub response.
Snapshot builds now accept an explicit successful probe of the same pinned
image to normalize a setup HEAD before sanitization. The original strict
base requirement remains the default. Independent verification also checks
that the former setup HEAD is inaccessible.

Datetransform snapshot
`sha256:5f0dad187211379bfa4e913571460b9ab47eb0264263b0d0472a35dced139d0c`
preserves the nine tracked base files and has one parentless commit. Base,
solution, merge and setup commits are inaccessible; declared oracle paths
are absent. This audits the mounted filesystem, not inherited Docker layers.
Paired controls on the snapshot match the qualified baseline exactly: one
base pass and two base failures, three reference passes.

Trace `2bd25bdd-8342-4fb7-99a8-6ef15a2ea5ff` was source-reviewed and replayed
with fresh native observations, 27 charged calls, no executed teacher thoughts
and successful disposable-container cleanup. Its submitted source-only patch
adds `inplace=False` and copies the dataframe when false. Independent grading
matched all three evaluator outcomes. These tests cover a narrow one-row date
example, not general dataframe aliasing correctness or learned model behavior.

The untruncated history contains 14,126 input tokens / 4,574 supervised targets.
Adding the unchanged 8,192 output reserve gives 22,318, leaving 10,450 tokens
under 32,768. `datetransform-native-admission-001` passes mechanical checks
without approving training. Evidence uses the `datetransform-*` directories
for source, snapshot, controls, replay, grade, history, tokens and admission.

Assembled schema-v2 `artifacts/data/quarantine/training-corpus-003`: two real
examples across two tasks/repositories, 31,479 input tokens and 8,757 supervised
targets. Manifest SHA-256:
`5c0fb2f37acf0d2b425f983c5db38316b15f97482231b4641371b4d8baf921ef`.
A seed-7401, one-epoch dry schedule with an 8,192-target per-update ceiling
produces two whole-example updates, zero target overshoot and no repetition.
The real corpus is still rejected for training. Rights, split isolation, task
alignment receipts and runtime admission remain unresolved. This tiny corpus
is pipeline qualification material, not sufficient campaign data.

Final CPU regression suite: 288 tests, 264 passed, 24 skipped; snapshot building,
verification, controls and replay also ran locally in Linux containers. No
GPU was used. Next: rights and complete admission review for these candidates,
continued diverse corpus expansion, then full-model runtime qualification when
local prerequisites justify restarting the Pod. P1 remains incomplete.
