# Current P1 readiness

Updated October 9, 2026. P1 is incomplete. This document is the concise current
state; documents 12, 35, 37 and 38 retain detailed development history.

| Requirement | Current evidence | Remaining work |
| --- | --- | --- |
| Corpus supply | Twelve quarantined examples across eleven repository groups; 222,446 input / 71,444 supervised tokens | Abundant, diverse, approved corpus; the 3×50M plan is not supplied |
| Repair fidelity | Nodebook excluded; Datetransform has added semantic probes; Werkzeug portable replay matches reference on 12/12 publisher tests and 55/55 additional semantic cases | Broader tasks and stronger coverage; teacher replay is not learned performance |
| Task quality | Narwhals and mypy_extensions mismatches recorded; Dkey held; pipdeptree teacher held for a reproduced type-override regression | Task-by-task alignment evidence for every admitted task |
| Rights | Exact repository notices and selected dependency notices captured; pytest upstream 7.1.2 notice recovered | Complete observation/dependency attribution review; installed Conda build equivalence is not established |
| Evaluation isolation | Prior repository ID/fork audit covers eight source projects and aliases; statsmodels and Numkit identity resolution remains incomplete; final grouping review pending | Frozen complete splits, semantic and detached-copy review for the final corpus |
| Local training implementation | CPU loss/gradient, optimizer, checkpoint, RNG and scheduling tests; latest suite 361 passed / 33 skipped, plus seven focused Session replay tests passed in the requests-enabled environment | GPU/full-model corroboration and long-running stability |
| Remote ingestion | Corpus 015 published and restored from R2; twelve examples validate; schedule and updates match original bytes | Repeat on the actual Runpod volume with the final admitted bundle |
| GPU qualification | Earlier single synthetic full-model update/reload only | Real-corpus long-sequence memory, checkpoint/resume, throughput and bounded failure handling |
| Product performance | No demonstrated learned held-out gain | Train, evaluate and compare against the frozen baseline |

## Current artifacts

- [Current eleven-example quarantine assembly](../evidence/data/training-corpus-assembly-014/receipt.json)
- [Semantic probe results](../evidence/data/current-corpus-semantic-probes-001/report.json)
- [Candidate review and exclusion](../evidence/data/current-corpus-semantic-probes-001/review.json)
- [Current R2 restore receipt](../evidence/data/training-corpus-restore-014/receipt.json)
- [Restored corpus inspection](../evidence/data/training-corpus-restored-inspection-014/report.json)
- [Byte-identical restored schedule](../evidence/data/training-corpus-restored-schedule-013/comparison.json)
- [Werkzeug independent semantic probes](../evidence/data/werkzeug-v2-semantic-probes-001/report.json)
- [Werkzeug computational AST comparison and notice capture](../evidence/data/werkzeug-v2-source-review-001/report.json)
- [Werkzeug V2 mechanical assessment](../evidence/data/werkzeug-v2-admission-002/report.json)
- [Quarantined corpus training denial](../evidence/data/training-corpus-denial-013/report.json)
- [Datetransform mechanical assessment](../evidence/data/datetransform-native-admission-001/report.json)
- [Selected dependency notices and explicit gaps](../evidence/data/datetransform-rights-material-003/report.json)
- [Matching upstream pytest release notice](../evidence/data/datetransform-pytest-upstream-notice-001/receipt.json)
- [Earlier two-repository identity check](../evidence/data/current-corpus-lineage-001/report.json)
- [Candidate issue duplicate audit](../evidence/data/candidate-issue-duplicates-001/report.json)
- [Draft corpus split review](../evidence/data/current-corpus-split-review-001/report.json)
- [Datetransform observation audit](../evidence/data/datetransform-observation-audit-001/report.json)
- [Nodebook observation audit](../evidence/data/nodebook-observation-audit-001/report.json)
- [Datetransform direct file attribution](../evidence/data/datetransform-file-rights-001/report.json)

Corpus schema v2 requires rights/attribution, split-isolation, runtime and
task-alignment receipts bound to the exact content. All four remain unresolved
for the assembled real corpus. No passing real admission receipt was fabricated.
Receipt integrity checks do not establish the truth of semantic or rights review.

## Next implementation cycle

Complete observation-level attribution and task review for the current candidates,
continue diverse data qualification, and freeze the intended evaluation split.
Keep admission and GPU-fit claims separate: actual GPU fit cannot be guaranteed
by CPU tests. Prepare the exact restored corpus, source bundle, budget and resume
checks before requesting a user-initiated Pod restart. Do not start a campaign
based on the earlier short synthetic update.

An earlier local regression run completed 305 tests: 281 passed, 24 skipped.
The Python 3.7 notice-capture path was additionally exercised in the actual
Datetransform container. Missing notices still fail by default; the explicitly
requested inventory mode records gaps and never approves training.

## Task alignment coverage enforcement

The v2 loader now requires versioned task-review evidence with exact coverage of
every distinct `(task_id, repository_group)` pair. Each review must include an
`accepted` decision and nonempty rationale. Missing, duplicate, foreign and
unresolved reviews fail admission, including hash-valid receipts. Multiple
traces of the same task share one issue-level review. Every evidence document
under this gate must contain `schema_version: 1` and nonempty `task_reviews`;
review entries have exactly `task_id`, `repository_group`, `decision`, `rationale`.
This enforces coverage, not semantic truth or per-trace correctness.

The real two-example corpus was re-inspected unchanged and remains quarantined.
The refreshed worker is `artifacts/official/p1-task-coverage-worker-001`; isolated
CLI import verification passed. No GPU was used.

## Semantic counterexample review

Additional evaluator-only probes were run on the exact local snapshot images,
with networking disabled, in disposable containers. Nodebook improves four
argument cases but loses the `External` dependency in `def f(a:External)` and
incorrectly suppresses the module-level dependency in `def f(a): return a; z=a`
(with the final assignment outside the function). The original 19-case evaluator
does not expose these defects. The trace is excluded from selection 003 and
assembly 004. Older artifacts remain immutable historical evidence.

Datetransform passed 18/18 added cases (base: 0/18), covering 0/1/3 rows, time
fields enabled/disabled and default/false/true inplace. These are constructed
regression cases, not an independent statistical sample or general guarantee.
All real admission gates remain unresolved. The older two-example restore and
schedule evidence does not certify the new one-example assembly or its schedule.


### Easy-ptvsd evaluator qualification — 2026-10-09

Pinned image matches declared base commit. Original image retains seven Git
commits and is evaluator-only pending sanitization. Base/reference controls
match all four publisher outcomes: base 3 pass / 1 fail, reference 4 pass.
Nineteen additional mocked-debugger checks give base 4/19 and reference 19/19;
these cover return identity, forwarding, class/static methods, call order and
exception identity. They test the publisher reference, not a teacher or model.
Evidence: `evidence/data/easyptvsd-review-001/review.json`. Next: sanitize and
replay shortest eligible trajectory, then grade, tokenize and review rights.
Current assembled corpus remains one quarantined Datetransform example. No GPU.


### Easy-ptvsd sanitized replay and integration — 2026-10-09

Verified ten tracked files in an exact-tree snapshot with one parentless commit,
no remotes, known oracle paths absent, and old base/head/merge commits inaccessible.
Verification concerns the mounted filesystem, not inherited Docker layer bytes.
Snapshot base/reference outcomes match original controls for all four test IDs.

Shortest trace `a148d74a-1367-4d52-8c47-a73008f73e7e` replayed but failed the
source-path restriction because its submitted patch retains `reproduce_issue.py`.
Retained the failure and did not edit its patch. The alternate trace
`40eb374a-0850-4770-8b29-61e6905e5c55` performs its own cleanup, submits only
`easy_ptvsd.py`, and passes 4/4 independent evaluator outcomes and 19/19 added
semantic probes. Replayed observations are fresh; original teacher conditioning
on those observations is not established.

Alternate history: 15,297 input / 4,527 supervised tokens; plus 8,192 reserve is
23,489, below 32,768 by 9,279 tokens. Mechanical admission passes; training remains
unapproved. Selection 004 and corpus 005 combine this trace with Datetransform:
29,423 input / 9,101 supervised tokens. All four real admission gates remain
unresolved. Next: attribution/rights, observation review, broader supply, updated
split isolation and scheduling. No GPU used.


### Easy-ptvsd attribution and restore cycle — 2026-10-09

R2 replay archive restored (91 files); corpus 005 validates through indexed
scheduling. Local and restored schedule/updates bytes match exactly: two
whole-example updates, 9,101 supervised tokens, zero overshoot, one epoch.
This is an inspection schedule, not training approval or GPU-fit evidence.

Captured ten repository files including MIT LICENSE.md and pytest 8.3.3 notice.
ptvsd 3.0.0 has no installed/archive standalone notice; captured its source
headers and referenced Apache 2.0 text. All seven installed Python source files
match the hash-verified PyPI archive. This does not certify the whole environment
or exhaustive rights. Attribution review: evidence/data/easyptvsd-rights-review-001.

Replay observation audit found five errors (missing issue reads, direct test
import failure, grep no matches, reversed classmethod reproduction). None were
concealed. Twenty-three calls have unspecified truncation status. Continue
observation consistency/attribution and broader qualification; no GPU used.


### Fancy-header branch counterexamples — 2026-10-09

Pinned image matches declared base; publisher base/reference controls match
13 expected outcomes (base 12 pass / 1 fail, reference 13 pass). Additional
12-case source branch probes pass 8/12 on base, 12/12 on reference, and 11/12
on each of three teacher source-edit reconstructions. Two traces suppress
missing-header errors on nonempty inputs; the third suppresses invalid-header
validation for docstring-only input with an empty body. All three are held.

The separate docstring/body branch was tested with its explicit object contract,
not a native newer-Python AST. These probes do not establish cross-version
compatibility or reproduce teacher shell execution. Evidence and exact edits
are retained at evidence/data/fancyheader-semantic-review-001 and
evidence/data/fancyheader-branch-probes-001. Do not equate publisher Python 3.6
passes with branch-complete repair quality. No new example added; corpus stays
at two quarantined examples, 9,101 supervised tokens. Next: qualify another
repository and continue corpus review. No GPU used.


### Supply feasibility and broader qualification batch — 2026-10-09

Verified census: 34,269 raw traces. Current cost-screened, image-present cohort:
2,621 traces, 1,575 tasks, 902 repositories. These counts are not admission.
Corpus 005 remains 9,101 supervised tokens, quarantine only. Under the current
32,768 context cap and 8,192 output reserve, a complete example has at most
24,576 input tokens and at most 24,575 causal supervised targets. Thus even
before prompt/tool masks and quality losses, one trace per task in this cohort
has a single-pass ceiling of 1,575 × 24,575 = 38,705,625 targets. All 2,621 traces
have ceiling 64,411,075. Neither number is available training supply.

A 50M-token candidate therefore requires expanding this cohort, multiple
trajectories per task, repeated exposure, or some combination. Three candidates
may reuse the same corpus; 150M processed targets are not 150M unique targets.
Do not interpret repetitions as independent tasks or evidence. No acceptance
rate is extrapolated from the deliberately chosen small reviewed subset.

Added a deterministic 32-repository review batch: choose each unreviewed
repository's shortest source-proxy trace, divide repositories into four cost
rank strata, select eight per stratum by seeded hash ranking. This widens cost
and repository coverage; it is not an unbiased coding benchmark or proof of
native token fit. All 32 issue descriptions are extracted with pinned task
shard identities. Evidence: evidence/data/qualification-batch-001. Next: review
those tasks and qualify their runtime/trajectory evidence.

Full CPU regression: 305 tests, 281 passed, 24 skipped. No GPU used.


### Broad batch triage and NumPyro mathematical check — 2026-10-09

Read all 32 issue descriptions; extracted identity-checked evaluator-only
patches for all 32 and reviewed reference/test patches for ten. Reviews record
specific missing tests and distinguish issue-only from patch-reviewed tasks.
Priority batch: CRC, NumPyro, Verde, civisml-extensions, geomet, pandas-vet,
hyp3-sdk, litecli. This adds state, tensor-rank, numerical, CV-alignment and
parsing coverage; no examples are approved merely by selection.

For NumPyro composition ranks, derived the minimum feasible input rank as
max(0, max_i[d_i - sum_{j<i}(c_j-d_j)]). The reference's backward recurrence
starts at the final domain rank and visits preceding transforms only. Exact
source/reference functions were checked against forward feasibility and the
closed form for 69,904 bounded abstract sequences: reference 0 disagreements,
base 17,942. This is not JAX or full-task runtime validation.

Held broad reference approval for sktime due to formula documentation/edge
contract gaps and decode due to version/specification and coverage mismatch.
Uvicorn trusted-proxy semantics and magnivore rounding require clarification
from source/contracts before qualification. Corpus remains two quarantined
examples, 9,101 supervised tokens. Evidence: qualification-batch-review-001
and numpyro-compose-math-001. Next: runtime and teacher review for priority tasks.
No GPU used.


### CRC runtime and provenance qualification — 2026-10-09

Resolved Nicoretti__crc-153 against the benchmark's merged solution commit
7ac98da2c6df6bbb91e2793ac69fcf796f9dba14, rather than the unavailable PR head.
The new snapshot independently preserves all 56 tracked files, has one
parentless commit, and removes checked old commits and known oracle paths
from its mounted filesystem. Inherited image layers remain outside this audit.

Original controls could not import crc: its installed editable-path file points
to /crc/src instead of /testbed/src. A diagnostic runner verifies the exact old
path bytes, records their hashes, and applies the same path-only correction in
four disposable offline containers. Original/snapshot base outcomes match
exactly (11 passed, 6 failed); both reference runs pass all 17 cases. Source
imports resolve to the checkout and tests leave tracked diffs unchanged.
Evidence: evidence/data/crc-runtime-controls-002 and crc-snapshot-verify-002.
Earlier failed attempts are retained. No teacher replay or corpus admission is
claimed. Next: integrate the explicit runtime correction into the replay image,
then test digest state preservation and updates interleaved with digest reads.
Corpus remains two quarantined examples, 9,101 supervised tokens; Pod stopped.


### CRC deep checks and native replay — 2026-10-09

Added an independent bit-feedback CRC oracle over GF(2), cross-checked CRC32
against zlib, and checked every 8-bit register state plus all split points of
five bounded messages across 16 configurations and two implementations.
Reference: 4,965 passed; base: 3,433 passed, 1,532 failed. These are dependent
within-task checks, not independent performance samples. Continuation after
reads is explicitly a stronger engineering invariant than the abstract single
final-digest workflow. Scope and derivation: crc-semantic-probes-001/DERIVATION.md.

Packaged the editable-path repair into a local derived image; independently
verified unchanged source snapshot and reproduced all 17 publisher transitions.
Build 003 failed because Docker interpreted the bare image ID as a registry
name; retained that failure. Build 004 uses a local tag with parent identity
checks before and after build; final runtime is pinned by content ID.

Native replay of trace 888c60d0-0a64-4816-aa3b-6c0aaacbf89a completed with
36 charged calls and fresh observations. Its patch retains final_verification.py
and reproduce_issue.py outside the source allowance, so grading stopped before
tests. No artificial cleanup, trimmed patch, training admission or candidate
semantic pass is claimed. Evidence: crc-replay-001, crc-replay-grade-001,
crc-qualification-review-001. The other reviewed CRC traces exceed the current
40-call source-proxy budget. Move to the next priority task rather than change
these acceptance rules for a preferred example. Corpus remains two quarantined
examples / 9,101 supervised tokens. No GPU used; P1 remains incomplete.


### NumPyro teacher mathematical screening — 2026-10-09

Reviewed all three extracted NumPyro-1894 teacher source edits before downloading
the 2.53 GB compressed image. Each adds a singleton special case while retaining
the incorrect multi-transform recurrence. Exact edited functions disagree with
independent forward feasibility and the closed-form rank oracle on 17,936 of
69,904 bounded sequences per trace, despite zero singleton disagreements.
For CorrCholeskyTransform followed by its inverse, all return input rank 2 where
rank 1 is sufficient and minimal. The shortest trace changes its diagnostic
assertion from 1 to 2; preserve that contradiction instead of training on its
success claim. No native replay, JAX evaluation, tensor-value or Jacobian test
is claimed. All three held for positive training; image metadata resolved but
layers not downloaded. Evidence: numpyro-teacher-001, numpyro-teacher-math-001,
numpyro-image-001. Next priority: Verde or civisml task qualification. Current
corpus remains two quarantined examples / 9,101 targets, not training-approved.
Pod remains stopped; P1 is incomplete.


### Verde contract audit and civisml intake — 2026-10-09

Verde-255 has an issue/evaluator API mismatch: the issue asks for `copy`; all
three teachers implement it; reference/tests call `copy_jacobian`. Signature
binding confirms each teacher rejects the evaluator keyword. After parameter
normalization and docstring removal, all three executable function ASTs match
the reference. Hold benchmark alignment, not mathematical correctness; no
renaming, evaluator modification or invented successful replay. Numerical
change-of-variable derivation and limitations are in verde-contract-review-001.

Reviewed civisml-extensions-22 source edits, which cache CV splits to keep
prediction rows aligned with target labels. Selected trajectory
101cfa89-3239-48d5-a2bc-abbbaf09929d for the next native qualification: 40 source
proxy actions and explicit cleanup of five diagnostic files. This is selection,
not acceptance. Resolve deterministic changing-fold negative controls, unequal
fold sizes and sample-weight indexing before admission. Image digest is pinned;
1,432,048,066 compressed bytes, layers not downloaded. Evidence: civisml-review-001,
civisml-teacher-001, civisml-image-001. Corpus unchanged; Pod stopped; P1 incomplete.


### civisml runtime, deterministic controls and replay preflight — 2026-10-09

Pinned runtime downloaded; Python 3.6.13 / sklearn 0.19.2 imports the task from
/testbed. Sanitized snapshot independently preserves 22 tracked files, removes
checked old commits and known oracle paths, and has one parentless commit.
Original and snapshot controls match every publisher transition: base 53/54,
reference 54/54. This one stochastic publisher regression is supplemented by a
deterministic changing-fold mechanism check: base 0/12 aligned, reference and
all three editor variants 12/12. Checks cover unequal folds, estimator column
order, training weights, row coverage and meta parameters using real NumPy but
controlled fitting/job doubles. No model-performance or independence claim.

Cloud-offloaded local files blocked reads. Two owned processes were terminated
only after identifying blocked reads and dataless files; source_snapshot.py and
image metadata were restored byte-identically from manifest-verified archives.
Other hydration races were rejected by inventory checks; successful retries use
fresh paths. No integrity check was weakened. Evidence includes local restoration
receipt and retained partial snapshot context; failed extraction attempts created
no output directories. Successful inputs: civisml-input-004; snapshot build and
verification: civisml-snapshot-002 / civisml-snapshot-verify-002; controls:
civisml-controls-001 / civisml-snapshot-controls-002.

Selected teacher replay stopped before container creation: action 8 uses an
absolute-path grep invocation outside the adapter's reviewed shell form. Next:
implement/test a narrow command mapping, then native replay, actual-patch grading,
context audit and rights checks. No training example admitted. P1 remains
incomplete; Pod stayed stopped. See civisml-replay-preflight-001 and
civisml-alignment-probes-001 for explicit limitations.


### Source grep adapter and civisml native replay — 2026-10-09

Added a narrow standalone `grep -n` mapping for one literal identifier and one
repository file. It accepts reviewed quoting forms and uses source_path plus
shell-safe argument rendering; shell operators, extra files, traversal, metadata
paths and unreviewed patterns reject. Tests compare actual match/no-match
stdout, stderr and exits. Full CPU suite: 307 tests, 283 passed, 24 skipped.
Initial suite had two hydration-related inventory rejections; both logs retained.

Civisml replay 002 completed with 40 charged calls, fresh observations and only
civismlext/stacking.py in the submitted patch. Actual patch passes 54/54 evaluator
cases and 12/12 deterministic method-alignment cases (controlled estimator/job
doubles, not concurrent fitting validation). Observation audit records two
errors, one explicitly truncated output and 31 unspecified truncation statuses;
these are preserved rather than relabeled successful.

Untruncated native history has 84 messages / 41 exchanges, 40,688 input tokens
and 10,867 supervised targets. With the 8,192 output reserve this needs 48,880
context tokens, exceeding the current 32,768 limit by 16,112. Token export
rejected; no tokens were silently dropped. Admission 004 holds this otherwise
passing candidate for context fit; it is not added to the corpus. Next: assess
an explicit, generally applicable observation-budget policy or select fitting
trajectories; any changed replay needs fresh observations and requalification.
Evidence: civisml-replay-002, civisml-grade-002, civisml-candidate-alignment-002,
civisml-history-003, civisml-tokens-004, civisml-admission-004 and
source-grep-regression-001. Corpus unchanged; P1 incomplete; Pod stopped.


### Civisml context-policy analysis — 2026-10-09

Verified swegemma 0.2.10's command cap (5,000 characters per stream), separate
file limits, missing explicit command-truncation flags and duplicated error
stream payloads. Counterfactual tokenization leaves all actions intact and caps
tool payloads only in memory; no altered history/tokens were emitted for training.
Command cap 1,024 plus file cap 2,000 still needs 33,681 tokens including reserve.
Only the tested 512/2,000 policy fits (30,911 total), but information sufficiency
and adaptive repair quality are unverified. Do not lower limits solely to admit
this case. Current policy and corpus remain unchanged.

A future generally applicable observation policy must preserve recoverable full
outputs, explicitly report truncation, be checked against harness compatibility,
and pass multi-task information/repair evaluation using fresh executions. Long
assistant diagnostic scripts also contribute to cost. Evidence and decision:
civisml-context-analysis-001. Continue independent fitting-data qualification;
this is not a Runpod blocker. P1 remains incomplete; Pod remains stopped.


### Geomet native qualification and context gate — 2026-10-09

Reviewed three geomet-101 teacher repairs. All follow the issue's suggested
truthiness-based SRID override. Bounded extracted-function probes cover six
geometry types, five metadata conditions and omitted/None/positive overrides:
base 60/90, reference and each teacher 90/90. Coordinates and input nonmutation
are checked. Separate explicit-zero probes expose a difference: reference 30/30,
teachers 0/30. Do not equate this with a valid-CRS claim; zero-domain contract
remains unresolved. No projection/reprojection validity is asserted.

Pinned image and sanitized snapshot qualify: 36 tracked files, one parentless
commit, old commits/known oracle paths inaccessible in the mounted filesystem.
Original/snapshot publisher controls agree: base 19/23, reference 23/23.
Trace 8f942217-d0bf-4856-9387-3151dcc1df24 replays with 39 charged calls and
explicit diagnostic cleanup. Submitted patch contains only geomet/esri.py,
passes 23/23 tests, and yields exactly the source bytes used in semantic probes.
Observation audit: two errors, two explicit truncations, 29 unspecified statuses.

History: 82 messages / 40 exchanges; 34,811 input tokens, 8,494 targets.
With reserve, context need is 43,003, so mechanical admission rejects it. No
training token export or corpus addition. Evidence: geomet-precedence-probes-001,
geomet-snapshot-verify-001, geomet-snapshot-controls-001, geomet-replay-001,
geomet-grade-001, geomet-candidate-source-001, geomet-tokens-001, geomet-admission-001.

Repeated context failures motivate an explicit turn-level SFT investigation:
keep the full causal prefix through a selected assistant action, supervise only
that action, and exclude later observations/outcomes. Such examples must be
labeled partial trajectories, not complete successful episodes. Qualification
must verify valid exchange boundaries, token/label identity, no duplicated target
counting across overlapping prefixes, task-level split grouping and complete
coverage accounting for omitted long-prefix actions. No observation cropping or
teacher-action rewriting is authorized by this proposal. Compare usefulness
before replacing the full-trajectory corpus format. Current corpus remains two
quarantined examples / 9,101 targets; P1 incomplete; Pod stayed stopped.

### Experimental action supervision audit — 2026-10-09

Implemented `zenithsync/action_training.py` and `scripts/audit_action_training.py`.
Each selected action receives its complete causal prefix, with every earlier
assistant label masked. Future outcomes are excluded. Complete source histories
must validate first; partial examples explicitly end at a pending tool call.
The pinned native tokenizer verifies unchanged serialization, token identities,
assistant spans and context boundaries. The audit additionally requires action
labels to partition the full-history target positions exactly, without overlap.
No token arrays are exported and no training admission is granted.

| History | Fitting / all actions | Fitting / all unique targets | Repeated input tokens for fitting prefixes |
| --- | ---: | ---: | ---: |
| geomet | 24 / 40 | 4,921 / 8,494 | 344,145 |
| civisml | 27 / 41 | 7,448 / 10,867 | 296,504 |
| easyptvsd | 31 / 31 | 4,527 / 4,527 | 257,667 |
| datetransform | 28 / 28 | 4,574 / 4,574 | 220,178 |

All prefixes use input + 8,192 <= 32,768; no observation cropping. Evidence is
`evidence/data/{geomet,civisml,easyptvsd,datetransform}-action-audit-002/report.json`.
These are four source histories, not 140 independent tasks. Prefixes must retain
the source task/repository split. Aggregate token counts do not create new unique
data. All 140 actions partition 28,462 original targets; fitting prefixes cover
110 actions / 21,470 targets. Late supervision remains missing from long cases.

For the two already-fitting histories, 477,845 prefix input tokens replace
29,423 full-history input tokens (about 16.24 times), with the same 9,101 targets.
This is token-processing overhead, not a measured runtime multiplier. Do not
replace full trajectories with this format by default. Conditional mathematical
identity: if each shared position has identical causal model computation, the
sum of per-action target losses equals the full-history target-loss sum when all
actions are included. A token-weighted denominator is required; averaging action
means changes the objective. Dropout, position-dependent kernels, sequence-length
scaling and floating-point effects mean gradient equivalence has not been proved
for the deployed model. Excluding long prefixes also changes the training set.

CPU suite: 312 tests, 288 passed, 24 skipped. Five focused tests cover selection,
causality, mutation isolation, masking and rejection boundaries; real-tokenizer
checks cover the four histories above. The first datetransform audit rejected a
file changed during cloud hydration; the unchanged stable receipt-bound retry
passed. This check was not relaxed. Earlier audit-001 reports remain historical.
Current corpus remains two quarantined examples / 9,101 targets. No GPU training
or learned-gain claim. Pod remains stopped; P1 incomplete. Next work must address
corpus supply and integration without treating partial coverage as completion.

### Additional corpus pilot — 2026-10-09

Pinned NVIDIA [Open-SWE-Traces](https://huggingface.co/datasets/nvidia/Open-SWE-Traces/tree/e192b26a43b8d09f156eeee781aef8e6bd5108ba)
at `e192b26a43b8d09f156eeee781aef8e6bd5108ba`. The current card declares
CC BY 4.0 and reports removal of Git-exploit trajectories from its earlier
release. This is publisher evidence, not our independent exploit/rights audit.
The [paper](https://arxiv.org/html/2606.16038v1) describes multilingual,
multi-teacher distillation; its older corpus totals cannot stand in for the
current pinned revision. Its reported 65,244 successes divided by 207,489 total
trajectories is about 31.45%, not the nearby claimed 40.6%; the denominator for
that rate is unclear. We will use row-level measured counts and preserve unknown
outcomes rather than inherit that aggregate percentage.

Acquired two bounded shards, each matched to publisher size and SHA-256:
OpenHands/Qwen3.5-122B tail shard 16/17 (43,048,099 bytes) and
mini-swe-agent/Qwen3.6-27B tail shard 21/22 (40,259,778 bytes), both SWE-rebench-V2.
Cards and publisher inventories are preserved. Selection was the smallest file
within each chosen framework/teacher/source, not random sampling. No population
success or usability estimate follows from these samples.

| Pilot | Rows | Repositories | Publisher resolved / unresolved / unknown | Python rows |
| --- | ---: | ---: | --- | ---: |
| OpenHands | 463 | 343 | 90 / 251 / 122 | 76 |
| mini-swe-agent | 1,035 | 669 | 360 / 593 / 82 | 224 |

Metadata projection reads no trajectory or patch bodies. Both shards contain one
exact `Textualize/rich` row, reserved by the official task index. Exact reserved
repository exclusion happens before subsequent body projection. No fork or
semantic-duplicate clearance is claimed. The new schema still omits explicit
tool-response IDs; do not silently treat it as native Gemma history.

Inspected only publisher-positive Python histories outside exact reserved repos:
26 OpenHands, 109 mini-swe-agent. All 26 OpenHands histories pass the existing
single-pending response-link diagnostic after explicit projection excluding the
reasoning field (zero reasoning characters in these inspected rows). None fit
40 source shell/editor calls; the shortest has 54. For mini-swe-agent, 28 of 109
have <=40 source bash calls; the shortest has 18. These proxies do not establish
native charged calls, context fit, independent repair correctness or replay.
No source commands were executed, no reference/model patches were read, and no
training examples were admitted. These counts are not new independent tasks
across all existing datasets; cross-source overlap remains to be measured.

Extended the metadata auditor with an explicit Open-SWE-Traces schema branch.
Two isolated-data-runtime tests cover both schemas, projection behavior, unknown
labels and rejection of boolean/out-of-range/null outcomes. Evidence:
`open-swe-{openhands,mini}-metadata-001`, `open-swe-pilot-screen-001`.

Decision: investigate mini-swe-agent terminal/bash semantics and the pinned V2
task/runtime join before bulk download. Do not expand the demonstrated expensive
OpenHands tail-shard route without a broader metadata/token screen. Preserve the
same replay, quality, attribution and split requirements. Current approved
training supply has not increased; corpus 005 remains two quarantined examples.
Pod remains stopped and P1 remains incomplete.

Regression: 314 tests, 288 passed, 26 skipped in the CPU environment; the two
new PyArrow-dependent tests separately passed in the isolated data runtime.

### Mini-swe-agent serialization and V2 task join — 2026-10-09

Added `zenithsync/mini_source_history.py`, a separate source serializer. It accepts
only the inspected four-field message schema and single bash calls, validates
command argument shape, preserves assistant text/reasoning and observation text,
and infers response IDs only with one outstanding call. Parallel, orphan,
interrupted and duplicate exchanges reject. Unknown fields and malformed
arguments reject. A final unanswered bash call remains explicitly unanswered;
its text is not proof of execution, submission or successful repair. No commands
are run or rewritten by the converter.

Pinned [SWE-rebench-V2](https://huggingface.co/datasets/nebius/SWE-rebench-V2/tree/10483de0f50fe5da545942705a76c6150171af7f)
at `10483de0f50fe5da545942705a76c6150171af7f`. Acquired its 428,839,266-byte
Parquet shard with publisher hash/size verification, plus card and LICENSE.
Only task ID, repository, base commit, image tag, language and license metadata
were projected for this join. No task problem bodies or reference patches were
read during this operation. All 28 selected source histories joined uniquely by
task ID with matching casefold repository names, excluding exact reserved repos.
Image tags are source metadata, not verified runtime digests or executable tests.

All 28 converted source histories pass the exact pinned Gemma rendering,
token-identity and assistant-span checks. Sixteen fit input + 8,192 <= 32,768,
with 99,359 source assistant targets in total. The other twelve are retained as
context exclusions. All source assistant text is counted, including source
reasoning embedded in content. The single bash schema, source prompts and
observations differ from our native nine-tool interface, so these are not native
training-token counts or new corpus admissions. No token arrays exported.
Evidence: `evidence/data/mini-source-qualification-001/{receipt,token-report}.json`.

The shortest fitting histories are werkzeug-2971 (11,198 input / 3,853 targets)
and dbt-snowflake-716 (12,216 / 3,068). Select runtime/replay work by clear issue
contracts and practical environment requirements, not length alone. Next:
inspect source shell/session/terminal behavior against the native executor,
pin candidate container digests, verify pristine source and independent grading,
then replay with fresh observations and measure native token costs. Larger data
acquisition remains conditional on this compatibility result.

Four focused converter tests passed. Full CPU suite: 318 tests, 292 passed,
26 skipped. The first source-token run failed because the evidence script name
`tokenize.py` shadowed Python's standard library; it was renamed to
`measure_source_tokens.py`, and all 28 real-history checks then completed.
Failure and passing logs are retained. Current admitted supply has not increased;
corpus 005 still contains two quarantined examples. Pod stayed stopped; P1 remains
incomplete and no learned gain or GPU-fit claim is made.

### Submission contract reconciliation — 2026-10-09

Inspected source command sequences for fitting mini candidates, including
werkzeug-2971, dbt-snowflake-716 and brutils-python-116. Their source finish reads
an exported path-selected patch file. The pinned native submit_patch instead
stages intent-to-add untracked files, captures a baseline diff, then strips
protected files. Thus a source patch export and native submission are not
interchangeable: scratch artifacts can enter the native diff.

Added `zenithsync/submission_reconciliation.py`. The planner supports an explicit
tracked-repair/untracked-scratch profile: the current tracked binary diff must
already equal the intended patch byte-for-byte; the complete nonignored
untracked inventory must exactly match individually reviewed scratch paths.
It rejects staged changes, path traversal, duplicate paths, symlinks and changed
repair bytes. Returned scratch records contain content hashes and sizes. It
performs no cleanup, executes no source commands and grants no training approval.
Scratch designation remains a semantic review responsibility, not a filename
heuristic. The planner is a point-in-time check, not concurrent-writer protection.

Four disposable-Git tests establish the artifact mismatch, exact patch equality
after explicit fixture cleanup, mutation-free planning, and rejection boundaries.
This is not a real task replay. Before integration, any cleanup must appear as
an adapter-authored native action, with file identities rechecked immediately
before deletion and actual post-cleanup native submitted patch equality checked.
Do not call this source-teacher-authored behavior or silently change its repair.
New-source-file and staged-change reconciliation remain unsupported.

Pinned werkzeug-2971 registry metadata to
`swerebenchv2/pallets-werkzeug@sha256:6ccc246ac36fe305dd00e85767d1a0d2ec1216d82792a6eac208c573dd7d5439`:
Linux amd64, 781,021,260 compressed layer bytes. No layers downloaded or runtime
verified. Evidence: `werkzeug-v2-image-001`, `submission-reconciliation-001`.
Next: pristine V2 runtime/control qualification and actual native replay with
explicit submission adaptation; do not accept source labels as repair proof.

Full CPU retry: 322 tests, 296 passed, 26 skipped. Initial run had one failure
and one error when macOS hydration changed inventory metadata for run_p1_server.py
and model_intake.py. Stable rereads and the unchanged test suite then passed.
Both logs retained; integrity checks were not relaxed. P1 remains incomplete,
corpus 005 unchanged and quarantined, Pod stopped.

### Werkzeug V2 original-image controls — 2026-10-09

Pulled the pinned werkzeug-2971 image. Read-only offline inspection verifies
HEAD `2139fa0b2cad96053f807384a6d04d8d09717802`, clean tracked/untracked status,
Python 3.10.19 at `/usr/local/bin/python`, and package origin
`/werkzeug/src/werkzeug/__init__.py`. The image contains 5,684 reachable commits;
it is evaluator-only until sanitization. Registry digest remains
`sha256:6ccc246ac36fe305dd00e85767d1a0d2ec1216d82792a6eac208c573dd7d5439`.

Selected V2 task extraction is evaluator-only. Its problem requests increasing
the PBKDF2 default to 1,000,000 iterations. Reference changes the constant and
changelog; the test patch changes the expected default hash prefix. This is a
historical task contract, not current password-storage guidance or a claim of
cryptographic security. Source-teacher correctness still requires actual replay
and additional relevant compatibility checks.

Added `scripts/qualify_rebench_v2.py` with an explicit src-layout Python profile,
exact task/registry bindings, reserved-repository exclusion and full test-node
comparison. The shared disposable-container runner now accepts a validated
absolute interpreter path; its default remains /usr/bin/python3. Existing
source-bound historical receipts retain their old helper identity; any future
requalification must use a correspondingly pinned implementation bundle.

Original-image controls (final script, controls-002): base 11/12; reference 12/12;
all 12 publisher outcome transitions match, no node-ID collisions. Both runs
import from the declared source and leave their patched tracked diff unchanged.
Containers were offline and cleanup succeeded. No sanitized image, teacher
candidate grade or trained model result is claimed.

Three profile/entrypoint tests pass. An initial negative test caught acceptance
of an absolute test path; validation now rejects absolute, repeated-separator,
traversal and ambiguous target lists before execution. Full CPU suite: 325 tests,
299 passed, 26 skipped. Initial and final control directories are retained.

The cloud-backed local V2 Parquet read timed out. Restored the previously
published 53-file / 431,730,739-byte bundle from R2 into a local /tmp directory;
restore completed with byte verification. Extraction then used that verified
copy. This is an additional recovery check, not permission to delete originals.
Evidence: mini-source-restore-001, werkzeug-v2-{probe,evaluator,profile}-001,
werkzeug-v2-controls-002 and werkzeug-v2-source-001.

Next: sanitize the V2 root layout, verify exact tree preservation and old-history
removal, repeat paired controls, then replay the source actions and explicitly
reconcile submission artifacts. P1 incomplete; current corpus unchanged and
quarantined; Pod remains stopped.

### Werkzeug V2 exact-tree snapshot — 2026-10-09

Snapshot build/verification supports explicit source roots and interpreter paths;
legacy /testbed and /usr/bin/python3 defaults remain. The first Werkzeug build
rejected the ancestry precondition: both PR head and merge objects are absent in
the publisher image, despite older history being retained. No check was disabled
silently. Added explicit `already_absent` solution mode, requiring Git's quiet
commit lookup to return exactly missing-object status with no output. Existing
commits reject that mode; default ancestry behavior remains. Receipts explicitly
set `solution_ancestry_verified: false`. Exact declared base and tracked tree
verification still apply. Absence is not ancestry evidence.

Build 002 produced local image
`sha256:00b4cc4b5bdbc142374db2ea14e6387094e4fca157e3c50392f7dcb0c1ed1854`.
Independent offline verification checks all 311 tracked files, their content,
modes and aggregate manifest against the preserved base tree; one parentless
commit remains, no remotes, no tracked changes. Original base, PR head and merge
commits are inaccessible. Declared oracle paths at both /testbed and /werkzeug
are absent. This covers the mounted filesystem, not arbitrary inherited layers
or a universal absence-of-oracles claim.

Re-ran original and sanitized-image controls with the same current evaluator:
base 11/12 and reference 12/12 on each. Exact full-node-ID outcome maps agree
between images in both roles. Sanitization has not changed these evaluator
outcomes. This does not grade the teacher patch or establish learned performance.
Evidence: werkzeug-v2-snapshot-002, werkzeug-v2-snapshot-verify-002,
werkzeug-v2-controls-003, werkzeug-v2-snapshot-controls-001/original-parity.json.
Failed build 001 remains preserved.

Six source-snapshot tests pass, including rejection of present solutions in the
new absence mode and preservation of exact source bytes. Full CPU suite:
326 tests, 300 passed, 26 skipped. Next: qualify moving /werkzeug into native
/workspace with dependency and /testbed aliases, replay the selected source
commands, and test explicit scratch cleanup plus native patch equality. Source
and native observations must remain distinguished. P1 incomplete; corpus still
quarantined; Pod remained stopped.


### P1 continuation: native V2 replay and independently graded candidate

The selected Werkzeug mini-source trace completed offline native replay in
werkzeug-v2-replay-001. Its 23 nonterminal source commands remained unchanged;
the adapter then issued explicit scratch cleanup and native submit_patch.
There were 24 charged commands and one submission. Four reviewed untracked
scratch files were removed only after tracked diff and complete untracked-set
checks. The submitted 1,103-byte patch exactly equals the source-exported patch
(SHA-256 534f7a271cf231bb692cf9eda4dcff925c8eed7ee55629776a6d51dc7e74da4b).
The owned container was removed. No model executed, and source observations
were not reused. /werkzeug and /testbed resolve to native /workspace; the
preexisting runtime cache was explicitly moved outside the source tree.

Fresh isolated evaluation in werkzeug-v2-candidate-grade-002 verifies base
11/12, reference 12/12, and candidate 12/12, with identical complete test-node
coverage and no candidate/reference disagreements. Candidate execution receives
only its patch and the evaluator test patch, not the reference solution. The
allowance restricts candidate changes to src/werkzeug/security.py. Patch, replay,
task and sanitized-image identities are bound and checked. This is one repair
qualification result, not learned model performance or an independent statistical
estimate. The initial grader preflight compared the replay snapshot receipt hash
to the wrong snapshot file; it rejected before starting a container. That binding
was corrected to receipt.json and both subsequent grading runs completed.

Source command 11 attempts an editable reinstall in a shell pipeline. pip fails
to fetch build dependencies offline, while the final tail command returns zero.
The full failure text is retained in fresh observations. Neither the pipeline's
zero status nor the passing final patch proves installation succeeded. Existing
source imports remain qualified by independent evaluator origin checks.

Latest CPU suite: 327 tests, 301 passed, 26 skipped. Candidate allowance tests
reject traversal, metadata, test-file and duplicate allowances. These checks do
not establish GPU readiness, semantic correctness beyond tested cases, or
training admission. Native prompt reconstruction, token-budget audit, semantic
compatibility probes and admission gates remain pending. The corpus remains
quarantine-only. Keep Runpod stopped; no GPU training was started this cycle.


### P1 continuation: portable adapted history and measured token candidate

A portability audit found replay 001's cleanup depended on a support module
installed only in its disposable container. It remains useful grading evidence,
but is not the selected training-history replay. The new standalone cleanup
command embeds the inspected planner and file-identity routine, requires only
Python standard library and Git, reads the native baseline tag and patch export
at execution time, and exposes deletion as an adapter-authored native action.
No helper package is installed or imported on the replay target. Disposable Git
tests confirm exact patch preservation without an installed project and rejection
of unknown scratch files before deletion. Point-in-time checks still do not
protect against concurrent malicious filesystem writers.

Replay 002 completes 24 charged commands plus submission, with fresh tool
observations and exact intended/native patch equality. Its independent grade 003
again gives base 11/12, reference and candidate 12/12. The source offline install
failure remains visible; no source observations or teacher reasoning are copied.

build_mini_replay_history.py produces 52 messages / 25 exchanges. It verifies
source command order and exact arguments, explicitly maps the two adapter-authored
suffix actions, requires the reviewed standalone cleanup command, checks task,
profile and patch identities, and excludes reserved repositories. History 002
has identical history, mapping and tool bytes to history 001; its receipt adds
explicit cleanup-profile validation. This is reconstructed conditioning, not an
original teacher rollout or a newly generated independent example.

Pinned Gemma token audit 002 exports quarantined token/label arrays after native
nine-tool rendering and collator validation: 12,199 input tokens, 4,607 supervised
tokens. With the planned 8,192 output reserve, 12,377 tokens remain below 32,768.
The audit now checks history input identities again after encoding. A retained
history-validation report binds the identical projection bytes and token report.
No truncation, GPU fit claim, corpus admission, or learned gain is implied.

Full CPU suite: 331 tests, 305 passed, 26 skipped. Two new history tests cover
source-response exclusion, provenance and rejection of dropped, changed,
reordered, misattributed or failed terminal actions. Two additional standalone
cleanup tests use actual disposable Git repositories. The first history build
rejected a cloud-backed protocol file whose metadata changed during hydration;
a stable reread succeeded without relaxing file identity checks.

Next: integrate V2 evidence with mechanical admission, independently probe task
semantics and compatibility, resolve rights/split/runtime gates, and expand
qualified task diversity. Three token candidates would still be radically
insufficient for the planned training scale; this new candidate is not yet in
the existing two-example quarantined corpus. Keep Runpod stopped. P1 incomplete.


### P1 continuation: V2 consistency assessment and corpus 006 round trip

Added a separate V2 mechanical assessment for portable mini-source replays. It
reconstructs every native exchange and provenance mapping; binds task, profile,
replay and grading inputs; verifies intended/submitted patch equality; recomputes
full test-node comparisons from base, reference and candidate outcomes; checks
execution cleanup and test exit statuses; and checks token/label hashes, causal
label constraints, exact shifted-target counts and context/call budgets. It does
not authenticate arbitrary receipts, rerun tokenization, or approve training.
Five disposable-fixture tests exercise valid-but-unapproved evidence, exceeded
budgets, patch mutation, concealed candidate failure and changed token labels.
Werkzeug assessment 002 passes its mechanical checks with remaining gates intact.

Assembled corpus 006 from the two prior exact candidates plus the portable
Werkzeug candidate: three examples/tasks, 41,622 input and 13,708 supervised
tokens. All four schema-v2 admission gates remain null. A direct training-purpose
load fails with "Quarantine corpus cannot train" before any GPU work.
Manifest SHA-256: 016a17c1d590600f85f9f132dfeb1ae1496a8e8578c1b369e5b83344ae189cf3.
Content SHA-256: 9fcf14059899acd24d5dd00a3bfc894d793f21649d8dd4ac891acade8df9c318.

The explicit dry-run schedule uses seed 7401, one epoch, 13,708 target tokens,
and an 8,192-target update cap: three whole-example updates, zero overshoot.
Published all seven corpus files (460,221 bytes) to R2 and restored them into a
fresh /tmp directory. The restored loader reports the identical content hash,
and schedule.json plus updates.jsonl are byte-identical to the local originals.
This verifies the local R2 ingestion round trip, not execution on Runpod's volume.

Initial candidate inspection and schedule 004 rejected cloud-hydration metadata
changes. The failed schedule artifacts remain retained; stable rereads and fresh
schedule 005 succeeded without weakened integrity checks. Latest CPU suite:
336 tests, 310 passed, 26 skipped. Pod remains stopped. This is still a tiny
quarantine corpus, far short of abundant approved data or the 3×50M-token plan.
Next: independent Werkzeug semantic/compatibility checks, V2 rights and split
review, and systematic expansion to additional source tasks. P1 incomplete.


### P1 continuation: independent Werkzeug semantics and source review

The issue's historical contract is a PBKDF2 default of 1,000,000 iterations.
An evaluator-only probe independently checks that requirement and preserves
explicit-parameter behavior, legacy 600,000-iteration hash verification, rejection
of wrong passwords, and the unchanged scrypt default. Inputs include empty,
ordinary, Unicode and embedded-NUL passwords. Low explicit counts are test cases,
not recommended password settings.

The small-count oracle implements the HMAC recurrence from
[RFC 8018 section 5.2](https://www.rfc-editor.org/rfc/rfc8018.html#section-5.2):
U1 = HMAC(P, S || BE32(i)); Uj = HMAC(P, U(j-1)); each output block is the XOR
of all c values, and concatenated blocks are truncated to the requested byte
length. It does not call the standard-library PBKDF2 function internally.
Two known-answer vectors from [RFC 6070](https://www.rfc-editor.org/rfc/rfc6070.txt)
and 324 matrix comparisons with hashlib calibrate the oracle, including multi-
block output and truncation boundaries. Expensive historical/default checks use
hashlib directly. Shared primitive implementations limit independence; this is
not a cryptographic security proof.

All three fresh offline runtimes pass 326 oracle-calibration checks. On 55 task
semantic cases, base passes 48 and fails exactly the seven requested-default
checks; reference and candidate pass all 55 with identical case outcomes.
Calibration counts are separate from task-case counts. The deterministic cases
are not independent statistical samples, and the result is not a learned agent
success-rate gain. Probe execution leaves tracked source unchanged and owned
containers are removed. Evidence: werkzeug-v2-semantic-probes-001.

A separate exact-snapshot source capture compares candidate and reference ASTs
for security.py, excluding only docstrings and source locations. They match;
base and reference do not. The sole changed function docstring is
 generate_password_hash, reflecting the new default. This equivalence excludes
introspection and traceback/source-location behavior and does not establish the
reference is universally correct. The reference also updates CHANGES.rst;
the candidate patch does not claim to reproduce that changelog edit.
Evidence: werkzeug-v2-source-review-001.

Captured the snapshot's tracked LICENSE.txt and copied pinned Open-SWE-Traces
and SWE-rebench-V2 cards plus the task dataset license into attribution evidence.
Both dataset cards declare CC BY 4.0; repository notices remain separate. The
attribution record lists all trajectory transformations and unresolved review
items. No rights, split, runtime or task-alignment corpus gate is automatically
approved. No product/training code changed in this cycle, so the previous full
CPU result remains 310 passed / 26 skipped; the new evaluator probes are reported
separately. Corpus 006 remains three quarantined examples. Pod stays stopped.


### P1 continuation: pipdeptree candidate held after pinned type checks

Reviewed mini-source candidate 168469d9-e93e-438b-9f73-120b2f6f6088 for
 tox-dev__pipdeptree-310. The issue asks for consistent unconstrained dependency
version serialization. Resolved the source image to immutable digest
07746f257fa029380050e8b395ac372c3fd938a598fc05267f1f4dcf0d4c7e2d, acquired it
locally, and verified its clean declared base
06c2f9d518f8bd7d8fa7f3520e231cdf15f0cd7f (410 commits, expected src import).
PR head and merge objects are absent. This image has not been sanitized for
agent execution; no native teacher replay or publisher test grading occurred.

The trace changes ReqPackage.as_dict to return dict[str, str] but leaves its
abstract Package method returning dict[str, str | None]. Repository tox.ini
pins mypy 1.7.1 and pyproject.toml enables strict checking. Prepared exact
Linux/Python-3.10 mypy wheels (with explicitly pinned supporting packages),
hash-checked them, and installed them only in an offline disposable evaluator.
The original image and training/runtime environments were not modified.

Full-source checks under the same checker and installed dependency environment:
base and reference each have three existing errors; the source-observed teacher
patch has those plus two new diagnostics: an incompatible override and an unused
ignore in dag.py. To separate the override from preexisting dependency/type
issues, extracted only the three relevant class method signatures from each
patched source and checked them independently: base and reference pass; the
teacher signature fails with the same override. This is a source-patch screen,
not a fresh model-generated failure or proof the full reference CI passes.

The type distinction is substantive: mutable dict value parameters are invariant,
so dict[str, str] is not a subtype of dict[str, str | None] for this override.
See the [mypy variance explanation](https://mypy.readthedocs.io/en/stable/common_issues.html#invariance-vs-covariance);
the actual experiment used the repository's 1.7.1 pin, not current documentation's
release. Runtime success on the reported JSON case would not remove this static
contract regression. Evidence and decision: pipdeptree-v2-review-001/report.json.
The candidate remains excluded from positive training data. Corpus 006 is
unchanged at three quarantined examples / 13,708 supervised tokens.

Added static_controls.py: bounded noncolored mypy output parsing, exact diagnostic
multiplicity, path/code/message comparison across base/reference/candidate, and
strict summary/exit-code consistency. Source line movements and diagnostic order
do not count as new errors. Unknown output and checker infrastructure failures
reject. Four tests cover new errors amid old ones, line/order invariance,
duplicate multiplicity, and malformed/fatal/contradictory output. This comparison
requires independently qualified equal environments and does not grant admission.

Next: move to the next candidate and reuse the source/runtime checks; do not
silently repair this teacher using the evaluator reference or relabel its
publisher status as verified correctness. Preserve this counterexample for
future negative-example or repair-recovery research with explicit provenance.
Pod remains stopped; no GPU training started. P1 remains incomplete.


Static-control cycle validation: full CPU suite 340 tests, 314 passed, 26 skipped.
The initial run retained one error and one failure caused by cloud hydration
changing run_p1_server.py and model_intake.py metadata during integrity reads.
No checker was relaxed; after that run terminated, a fresh complete run passed.
Both logs are retained in the archived evidence package.


### Dynaconf recursive-equality screen (local, pre-admission)

Pinned original image `sha256:d25a589823a03ab10900ae43aeda1c3845b78d97921702ad91138189ef0d0ad6`
was tested offline at task base `b389b2bbb07b2abb92577e81384f7f939b05c5f5`.
Compared base, publisher reference, and the exact source-observed teacher patch
from message 51. This is evaluator screening, not native agent replay.

Enumerated 202 distinct ordered expression trees of depth at most two using
AND/OR and required-name leaves A/B. Across 40,804 ordered pairs per role,
structural equality mismatches were base 39,800, reference 448, teacher 0.
Registering two independently constructed copies of each tree retained 3, 74,
and 202 entries respectively. Ordered structure is a deliberately conservative
screening oracle; Boolean-equivalent trees need not be structurally equal.
These are exhaustive finite cases, not independent statistical trials.

A concrete reference collision is A AND (A AND B) versus A AND (A OR B).
With A present and B absent, real Dynaconf validation rejects the first and
accepts the second, yet the reference treats them as equal. All four truth-table
rows were checked against those Boolean predicates. The teacher distinguishes
them. This exposes a reference limitation; it does not establish universal
correctness of the teacher or permission to train from evaluator information.

Evidence: `evidence/data/dynaconf-v2-semantic-screen-001`, reproducible drivers in
`evidence/data/dynaconf-v2-semantic-source-001`. All roles imported the repository
package, left tracked source unchanged, and the owned offline container was
removed. Native replay, publisher tests, lineage/snapshot qualification, token
admission, and corpus gates remain pending. No training infrastructure changed.
Corpus 006 remains three quarantined examples / 13,708 supervised tokens.
Runpod stays stopped. P1 remains incomplete.


### Dynaconf native qualification and historical evidence support

Resolved the task's upstream pull request at https://github.com/dynaconf/dynaconf/pull/413.
The old owner path now redirects to a different mirror repository, whose PR 413
returns 404. Canonical upstream validator.py at the task base matches the pinned
image byte-for-byte; this is file-level corroboration, not whole-repository proof.
The original image is clean at the expected base, with 457 reachable commits;
PR head and merge objects are absent. Two failed diagnostic runs are retained:
the diagnostic used the same dictionary key for repository HEAD and PR head.
Run 003 separates these fields and verifies the expected base correctly.

Built and independently verified sanitized snapshot
`sha256:4ddee414e4597204acde8b3ebca8cfb550ff1d0bfcafbba95c2b5d17f90acd5a`:
511 tracked files preserved, one parentless commit, old base/head/merge objects
inaccessible, known oracle files absent. This verifies the mounted filesystem,
not inherited Docker layer contents. Original and snapshot publisher outcome
maps match exactly: base 24/26, reference 26/26.

Native replay 001 completed 26 charged tool calls plus submit_patch, yielding
the exact source-observed patch. Candidate grading passed 26/26 publisher cases.
History 001 contains 56 messages / 27 exchanges. Token audit 001 exported
20,299 input and 6,870 supervised tokens; input plus 8,192 reserve is 28,491,
below 32,768. Mechanical admission 001 passes without granting training approval.
One broad source test command fails collection because optional dependencies
are absent; this error is retained, not transformed into successful verification.
Native replay is teacher trajectory reproduction, not a newly trained agent result.

The qualifier now explicitly supports src and flat package layouts. Exact
repository import origin and package-scoped candidate source allowances remain
required. Historical evidence can explicitly map implementation files to an
archived source copy with the original hash; mapping data, patches, or receipts
is prohibited, and unused mappings reject. Existing Werkzeug evidence was
successfully reassessed with its original archived qualifier in admission 005.
Two prior attempts stopped on macOS cloud hydration metadata changes; after
reading the files locally, the unchanged integrity checks passed. The archived
code is checked as historical evidence; current reconstruction checks still run.

Validation: 13 focused tests pass; complete CPU suite 344 tests, 318 passed,
26 skipped. No GPU checks ran. Source lineage, snapshot, controls, replay,
history, token, and admission evidence are under evidence/data/dynaconf-v2-*.
Dynaconf remains pending final attribution/split/semantic review and assembly;
corpus 006 is unchanged at three quarantined examples / 13,708 supervised tokens.
P1 is incomplete; Runpod remains stopped.


### Corpus 007: four-task quarantine integration

Added the native Dynaconf replay to the quarantine assembly; preserved MIT
repository notice, pinned CC-BY-4.0 dataset cards/license and transformation
notes in dynaconf-v2-attribution-002. Dependency/observation rights and teacher
service-term coverage remain unapproved. Attribution attempt 001 stopped on a
cloud-file metadata change; checks were preserved and attempt 002 succeeded.

Current assembly: four examples and four tasks, 61,921 input tokens and 20,578
supervised tokens. Manifest SHA-256:
`24b6b11a8a111174eac74631043d2804a32bb83b7584a152fc489a6dbcdd0610`.
Content SHA-256: `0a0ac1667b6b6e4096f3aabc0a0c932f7da960d4fcc01e61b7e00f4ad4eb3f7c`.
All four admission gates remain null. Direct purpose=training loading rejects
with `Quarantine corpus cannot train`; no training ran.

Fresh GitHub metadata resolves four source projects, the old Dynaconf mirror,
and all four named reserved repositories. No repository-ID or declared
fork-network overlap is found. The old URL resolves to dynaconf-mirror with fork=false; this metadata alone
cannot establish historical independence.
Dynaconf is explicitly grouped under canonical dynaconf/dynaconf in the corpus.
Final semantic duplicate review, historical/detached-copy grouping, and frozen
splits remain pending; reserved task bodies were not opened.

Published all nine corpus files (684,444 bytes) to R2 and restored to an empty
/tmp directory with verified hashes. Restored loader counts and content hash
match. A one-epoch schedule, seed 7401, target 20,578 supervised tokens and
8,192-token update cap produces four whole-example updates, zero overshoot.
Schedule and updates files from restored data match original bytes exactly.
Schedule attempt 006 stopped on cloud hydration of training_corpus.py; attempt
007 completed with unchanged integrity checks. No optimizer or GPU ran.

Evidence: training-corpus-assembly-007, publish-007, restore-007,
restored-inspection-007, schedule-007, restored-schedule-006, denial-005, and
current-corpus-lineage-002. Code was unchanged this cycle; integration was
verified by actual assembly, rejection, transfer, restore and schedule replay.
The latest code suite remains 318 passed / 26 skipped. Four quarantined examples
are not sufficient for the planned 3x50M candidates; repeated exposure would
not create additional independent tasks. Continue corpus qualification and
admission review locally. Keep Runpod stopped. P1 remains incomplete.


### Workalendar qualification and corpus 008

Qualified peopledoc__workalendar-493, canonical workalendar/workalendar. Original
image digest sha256:3837c3917cae0f429c4540fe570a3d9b68d70615e86995b9a2fc9ea62abebb41
has clean task base 3fd9b831b308f1b0f7e1ca8fffc456ab6bdce56a, 1,008 reachable
commits and no local PR head/merge objects. Sanitized snapshot
sha256:5125f7b3193618806b0a734412dd43486b88fed20d94d49c6cc7467e4735076f
preserves 177 tracked files exactly, one parentless commit, no old base/head/merge
objects or declared oracle paths. Verification concerns the mounted filesystem,
not inherited image layers. Original/snapshot publisher outcomes match exactly:
base 8/11; reference 11/11.

Native replay 002 completed 29 charged calls plus submit_patch; submitted bytes
match the separately screened teacher patch. Candidate passed 11/11 publisher
tests. Independent finite checks: base 0/18, reference 18/18, candidate 18/18.
These cover exact registered/unknown lookups, warning category/count, registry
nonmutation, subclass delegation and exception propagation, not calendar-date
correctness or statistical generalization. An unmatched grep and nonexistent
source-requested pytest node remain errors in the fresh native history. Pipelines
that truncate test output are not treated as independent full-suite evidence.

History 002 has 62 messages / 30 exchanges. Token audit 001: 20,149 input and
7,312 supervised tokens; with 8,192 output reserve, 28,341 fits 32,768.
Mechanical admission 002 passes, without training authorization. Captured the
MIT repository notice and pinned dataset notices; dependency/observation rights
and teacher service terms remain pending.

Local Desktop cloud offloading delayed the existing runtime/profile processes.
Explicit macOS materialization requests allowed them to resume; runtime 001
then correctly rejected a metadata-changing integrity read. Fresh runtime 002
passed. Similar integrity rejections preceded successful semantic-screen 002,
replay 002, history 002, admission 002 and corpus-denial 007. No integrity check
was relaxed; prior outputs/scripts are retained where written.

Corpus 008: five tasks, 82,070 input / 27,890 supervised tokens. All admission
gates remain null and purpose=training is rejected. Manifest SHA-256:
4ced40b5cb89e799a845cd833ae7d34a0c291b170a6a8988f4a028f7e411bf45.
Content SHA-256: b9b1451ea77f89f9a19d50dbc218976af0a8a456bc65f47cf6fcd6d731f626b9.
Published 11 files / 905,531 bytes through publish-009; restored and validated
through restore-008 / restored-inspection-008. One epoch, seed 7401, 8,192-target
update cap: five whole-example updates, zero overshoot. Original schedule-008
and restored-schedule-007 schedule/update bytes match exactly.

Metadata-only lineage audit 003 resolves all five source projects, aliases and
four reserved repositories without known ID/fork-network overlap. This excludes
neither detached copies nor semantic duplicates. No held-out issue bodies read.
No shared implementation changes this cycle; the prior 318-passed/26-skipped
suite is unchanged, not newly rerun. Five quarantined examples remain far below
the planned training supply. Continue local corpus expansion and gate review;
Runpod remains stopped and P1 remains incomplete.


### PennyLane 5716: independent numerical screen, interface gate still closed

Selected the batched StronglyEntanglingLayers issue from 16 source-context-fitting
candidates; mini-candidate-priorities-002 records current status and qualitative
selection rationale. This task adds tensor-shape and quantum-circuit numerical
coverage. It is not yet a sixth corpus example.

Pinned original image sha256:b41317e4fdf7780cc28d1e5eed4a65e69159331091f6749fde7a92f29c5f4a94
runs PennyLane 0.37.0-dev on Python 3.10.19 at clean base
85ff62b9c9218f523ef7ff0535cde7cbf55ebb7b; 4,180 reachable commits,
PR head/merge absent. Verified sanitized snapshot
sha256:e60eb0ef6d062901bedc874d4c731c438b7182d707f06704c0382f8c62800f23
preserves all 1,353 tracked files, one parentless commit, no accessible old
base/head/merge objects or declared oracle paths. Mounted filesystem only;
this does not audit inherited image layers.

Independent dense-state oracle constructs RZ(omega) RY(theta) RZ(phi), Kronecker
operators and explicit computational-basis CNOT permutations, without reusing
the template/decomposition. Rotation convention follows
https://docs.pennylane.ai/en/stable/code/api/pennylane.Rot.html; that current
reference is not a claim about the installed version. Primitive gate calibration
against the pinned runtime establishes matching conventions before comparison.
Seed 5716; batch sizes absent/1/2/4, layer counts 1/2/3, wire counts 1/2/3:
36 cases per version. Reference and source-observed teacher pass 36/36; base
passes 15/36. Candidate maximum absolute state error is 3.554447978966673e-16,
with required atol 1e-11 and rtol 0. Norms also checked. These are finite NumPy
calculations, not independent statistical trials or universal correctness proof.

Screen 002 initially supplied explicit zero ranges for one-wire circuits, which
this constructor rejects. It therefore recorded 12 probe-input failures for
both fixes. Screen 003 uses the supported default in these cases; both runs
are preserved. Other failed attempts stopped on cloud-hydration metadata drift;
none of the integrity checks was relaxed. Runtime 002 is the completed bound run.

Full publisher-module controls collect 44 tests. Base: 29 pass, 12 fail,
3 skip; reference: 41 pass, 3 skip. The strict grader rejects skipped controls.
The skipped tests exercise JAX, TensorFlow, and Torch interfaces, including
gradients; dependencies are absent. Dependency metadata, repository requirements,
test source, and skip mechanism captured under pennylane5716-v2-dependencies-001.
Do not drop these tests or equate 41 passing calls with fully qualified controls.
Next: derive compatible pinned backend dependencies, install in a separately
qualified offline runtime, and rerun complete controls and snapshot parity.
Native source replay, token assessment, attribution and split review remain.

Evidence: pennylane5716-v2-review-001, semantic-screen-003, controls-original-002,
runtime-002, snapshot-verify-001. Shared implementation unchanged this cycle;
prior code suite remains 318 passed / 26 skipped, not newly rerun. Corpus 008
remains five quarantined tasks / 27,890 supervised tokens, all gates pending.
Runpod stays stopped. P1 remains incomplete.


### PennyLane backend qualification follow-up

A separately built offline dependency image now passes pip check and imports
PennyLane, Torch 2.3.0+cpu, JAX 0.4.23, TensorFlow 2.16.1, tf-keras 2.16.0,
and cvxpy 1.4.2. SciPy is 1.12.0, following source CI; cvxpy was adjusted
for compatibility. Original wrapt 1.12.1 remains installed. This is an
explicitly changed runtime, not a claim about the publisher image unchanged.
Image: sha256:5269b39ab665401139db6d6953893c831f1f5ae1cae7eecce6366472e8b71051.

Supplementary paired publisher tests: base 32 passed / 12 failed; reference
44 passed; zero skips. Tracked source remained unchanged during each test run.
Task recovered from the previously hash-verified source shard; recovery checks
its complete SHA-256 again. Four independent dense-state finite-difference
checks cover 72 Torch gradient components, batch sizes 1/3 and depths 1/2
on two wires. Maximum gradient discrepancy: 6.66134231108728e-11; repeated
fresh-tensor gradients agree exactly. These finite cases are not a proof for
arbitrary circuits, framework versions, or training behavior.

Evidence: evidence/data/pennylane5716-v2-backend-summary-001. The 1.005 GB
wheel/build/evidence bundle is being published through the existing verified
R2 transfer path; only its terminal verified receipt establishes archival.
Strict admission integration, sanitized snapshot parity, native replay,
token-fit assessment and attribution remain pending. Corpus 008 is unchanged,
Runpod remains stopped, and P1 is not complete.


Backend snapshot follow-up: independent verification passed for all 1,353
tracked files. The original and expanded snapshots have the same source tree,
tracked-file manifest digest and byte counts. The expanded snapshot has one
parentless commit, no accessible original base/merge commits, and no known
oracle files in its mounted filesystem. Inherited image layers are outside
this isolation claim. Both 44-test publisher runs have exactly the same
per-test outcomes before and after sanitization (32/12 base; 44/0 reference;
no skips/errors). See backend-snapshot-verify-001/source-parity.json and
backend-snapshot-paired-001/parity.json under evidence/data/pennylane5716-v2-.
Native replay and admission integration remain pending; corpus unchanged.

R2 backend bundle publish-002 completed with verified receipt: 107 files,
1,005,376,281 bytes. This archive covers the backend build and initial
controls/gradient evidence; the later snapshot verification and parity
evidence require a subsequent archive. Publish-001 failed before completion
and is not treated as a backup.


PennyLane native replay now completed (35 charged calls plus native submission;
36 exchanges / 74 messages). Candidate-grade-003 passes all 44 cases;
admission-001 recomputes the full evidence with no mechanical blockers.
Native-tokens-003 records 21,157 input / 7,139 supervised tokens, untruncated.
Corpus 008 remains unchanged pending attribution and repository split review.
Source patch body is identical; Git index abbreviations differ (8 versus 7
characters). Stable Git patch IDs agree. The unsupported double-batch example
and no-match grep error remain visible in the native history.

Evaluator profiles now optionally declare supplemental pass-to-pass tests and
an explicit repository pytest root. For this task, 41 publisher expectations
remain unchanged; three backend tests are separately declared and must pass
both controls. Exact complete coverage, setup/teardown success and no-skips
requirements remain enforced. Admission rechecks a hash-bound supplemental
profile. Focused suite: 25 tests passed. Full suite is running; no full-suite
success claimed yet. Snapshot/CI archive verified: 69 files / 227,052 bytes.

Full CPU suite rerun completed: 349 tests, 323 passed and 26 skipped.
The initial run had two source-hydration integrity failures; both logs are
retained. No integrity check was relaxed. This does not prove GPU readiness.


### Corpus 009: PennyLane integration, still quarantined

Six tasks now total 103,227 input / 35,029 supervised tokens. Manifest SHA-256:
`066260151fe14e4778837b124235a25e013d650a3b542915daae79a5f52dd5b0`.
Content SHA-256: `23531344ea84e04f3feb260d5ef9b0155f413974088a761837206f807a6a2b58`.
All four admission gates remain null. Training-denial-008 confirms refusal.

Publish-010 and restore-009 verified 13 files / 1,143,461 bytes. Restored
inspection-009 validates all six examples. Schedule-010 and restored-schedule-008
are byte-identical: seed 7401, one epoch, 35,029 supervised tokens, six
whole-example updates, 8,192-target update cap, zero overshoot. No optimizer or
GPU execution is implied. Failed schedule-009 stopped on cloud-hydration drift.

PennyLane attribution-001 captures Apache-2.0 repository license, observed-file
header and pinned dataset notices. Complete rights review remains pending.
Lineage-004 resolves current canonical repository IDs and declared fork roots
for six source projects, aliases and reserved evaluation repositories, with no
overlap. Detached copies, semantic duplicates and historical forks remain outside
that metadata screen. Native qualification archive verified: 341 files /
1,988,275 bytes. Earlier backend wheel bundle and snapshot archive are also verified.

Current suite: 323 passed / 26 skipped (349 total); focused control/admission
suite: 25 passed. Real-corpus GPU training, held-out learned improvement, final
rights/split approval, and abundant data supply remain unfulfilled. Pod remains
stopped. Next: archive corpus integration evidence, then expand the qualified
candidate pool without treating repeated exposure as new data.


### Linkding 691 candidate qualification

Pinned clean base edd958fff61a640cf02c7640b717e78f10322b8b; sanitized
296-file snapshot verified with exact publisher-control parity. Native replay
completed 27 charged calls plus submit; patch matches its fresh intended export.
Candidate and reference pass 6/6 publisher tests; base passes 5/6. Independent
real child-process argv and gzip checks: base 2/77, reference/source candidate
77/77. No browser, website-access or network success is claimed.

Native history: 18,910 input / 8,540 supervised tokens, untruncated; mechanical
admission passes. The 8,192-update target cap rejects this whole example as
intended; a metadata-only 9,000-cap probe preserves it in one update. Neither
probe establishes GPU fit. Corpus 009 stays unchanged. Source mock-test claims
and a permissive exception check require explicit quality review; attribution,
split review and integration remain pending. See linkding691-v2-review-001.


### Two additional positive-supervision exclusions

Linkding 691 remains outside corpus 009 despite passing mechanical grading.
Supervision-review-001 binds two exact unsupported claims to assistant tool-call
commands, which the current loss mask labels: a mock-only test asserts external
website access, and a permissive exception test claims success without proving
its requirement. Preserve original evidence; do not silently sanitize the trace.
A replacement trajectory or separately specified selective-supervision policy
must be qualified before reconsideration. Its initial qualification archive is
verified in R2: 147 files / 712,237 bytes.

Scrapy 6897 is held for a reproduced source-candidate type regression. The pinned
source tox.ini requires mypy 1.14.0 and Python 3.9. Exact extracted constructor
bodies (with explicit external types) pass for base/reference; candidate fails
with `Attribute "path" already defined [no-redef]`. Checker executed on local
Python 3.13 with target 3.9; this is not a full repository or native CI run.
The source command calls this edit a type-annotation fix, so it is unsuitable
positive supervision without replacement. No native replay or publisher tests
were performed for this candidate. See scrapy6897-v2-review-001 and the saved
checker inputs/results. Priority review 003 records both exclusions. Corpus 009
remains six quarantined examples / 35,029 supervised tokens; no GPU work started.


### Kubernetes client 247: source test acceptance counterexample

The source trace's index-28 integration-test function claims successful URL
conversion whenever an exception lacks the substring "hostname is invalid".
An isolated run of its exact class/function definitions accepts both a substitute
that raises an unrelated RuntimeError and a no-op substitute. A negative control
with the expected error substring is rejected. No network or repository code
was executed; this establishes unsound test acceptance, not a broken URL fix.

The candidate is held out of positive supervision because its success-printing
code would become assistant-call training targets under unchanged replay policy.
No native history or token arrays have been produced. Preserve the original
trace and the executable counterexample; do not rewrite it to look successful.
The evidence can support future error-analysis work, but is not automatically
approved as negative training data or a preference pair. Priority review 004
records the hold. Corpus 009 remains unchanged and Runpod remains stopped.

### Brutils 116: verification accepts a broken formatter

The exact source index-48 verification script exits zero and prints that all
requirements are verified when run against an explicit substitute returning
`WRONG_FORMAT` without calling validation. Its own output reports that the
validation-call requirement is false. This is an isolated acceptance-logic
counterexample, not an execution of the repository or proof that its patch is
wrong. The trace is held out of positive supervision; source evidence is retained.
See `brutils116-v2-review-001` and priority review 005. No native replay or
publisher tests were run for this candidate.

`scripts/review_python_test_source.py` now records hash-bound, non-executing
review hints for explicitly selected Python snippets. On the saved Brutils and
Kubernetes snippets it locates the known success message and broad exception
handler. Findings never decide admission; absent findings never prove quality.
Literal matching misses aliases and computed messages, and legitimate checks can
precede a flagged message. Executable counterexamples and contextual review remain
necessary. Seven focused tests cover the hints, non-execution, source identities
and preservation of existing reports. Corpus 009 and its unresolved admission
gates remain unchanged.

The source-test review integration regression run completed 356 tests: 330 passed
and 26 skipped. This local suite does not validate GPU training readiness.

### Online-judge-tools 445: repair supported, environment qualification pending

The base, reference and source-candidate versions pass 12/18, 18/18 and 18/18
local HTML cases respectively. The probe executes the exact extracted
`_parse_start_time`, `_load_details` and `get_name` methods with a real HTML parser
and a substituted HTTP boundary. It checks penalty values, duration and cached
name reads. The six base failures concern singular English `minute`. These are
generated fixtures, not historical website responses, and this screen is not a
full repository test or native replay.

The pinned original image imports the correct base repository under Python
3.7.17. Its original `test_load_details` fails offline with a DNS-derived
connection error. No conftest or HTML/YAML/HAR fixtures were found in the recorded
search. The publisher tests need further reproducible environment work; they
must not be reported as passing based on the separate semantic screen. Source
supervision review also remains open because its scenario script tests a copied
regex rather than calling repository `get_name`.

See `onlinejudge445-v2-review-001` and priority review 006. The task remains
pending, not rejected as a faulty repair and not admitted to training. Authentic
attributable response fixtures, or an explicitly separate supplemental offline
evaluator, are the next investigation. Corpus 009 is unchanged.

### Online-judge-tools 445: current recorded-response controls

Five current public AtCoder pages were captured with exact URLs, retrieval times,
HTTP status and body hashes. The reported contest still displays singular
`minute`. Replaying those exact bodies at the requests Session transport boundary
in the pinned offline image yields base 7/8, reference 8/8 and candidate 8/8 for
the publisher assertions. Complete collected identities and setup/call/teardown
phases pass the strict transition comparator. No publisher assertion was changed.
The earlier unchanged offline environment failure remains valid and preserved.

Seven separate transport checks pass: exact body bytes, response metadata,
unknown URL rejection, unrecorded-language rejection, POST rejection, GET-body
rejection and restoration of the original transport. This experimental adapter
is task-specific qualification code, not yet shared native replay support.

See `onlinejudge445-v2-response-replay-002/comparison.json`,
`onlinejudge445-v2-transport-check-001/checks.json` and review 002. Current pages
are not proven identical to the 2019 responses. Access to public HTML does not
establish redistribution or training rights; that review remains unresolved.
Source isolation, native replay, resource integration and supervision review also
remain pending. No examples were added to Corpus 009 and no GPU work started.

### Reusable Session response adapter

`zenithsync/session_resource_replay.py` validates the complete response mapping
before installing an exact prepared-URL GET adapter in a disposable process.
It rejects authentication/cookies, conditional reads, POST or GET bodies,
unrecorded URLs, response hooks and unsupported transport settings. Response
bytes and content type are retained; text decoding uses the documented UTF-8
convention. It does not reproduce the general HTTP protocol or TLS behavior.
Restoration is explicit and the adapter is not safe for concurrent installation.

Seven focused tests pass in the requests-enabled environment, including
no-network byte replay, invalid-record atomicity and rejection paths. The full
local discovery run completes 363 tests: 330 passed, 33 skipped. Seven of those
skips are these new tests because that suite's environment lacks requests; their
separate successful run is retained rather than counted as full-suite passes.
In the pinned Python 3.7 task image, the shared adapter independently reproduces
the eight expected publisher transitions (base 7/8, both repairs 8/8); see
`onlinejudge445-v2-response-replay-003/comparison.json`.

This is reusable transport code with an exercised task integration. The shared
native replay CLI and qualification/admission bindings still need resource
support before the task can enter the native corpus pipeline. Training remains
unapproved and the six-example corpus remains unchanged.

### Bound response bundles and native staging

`session_resource_bundle.py` now requires complete capture coverage, an exact
capture-receipt hash, matching body identities/content types, unique response
URLs and local filenames, and an explicit cumulative byte budget. Redirects,
failed responses, changed files and symlink bodies are rejected. The five-page
AtCoder bundle contains 103,669 response bytes and remains unapproved for training.
Capture metadata links evidence; it does not prove authenticity or grant rights.

`replay_mini_source.py --session-resources` requires a reviewed profile containing
the exact bundle receipt identity and byte budget. It stages only body data,
the transport module and startup code, records their identities, and explicitly
marks injected support modules. Existing admission rejects that flag; no new
training-admission path has been enabled. The previous replay implementation is
preserved under `artifacts/official/mini-replay-before-session-resources-001` for
historical hash-bound evidence.

The real native ContainerManager staging probe in the pinned Python 3.7 image
served the captured singular-minute page and rejected an unknown URL. Deliberate
hash corruption caused the next Python process to exit 78 before its user code
ran. Owned-container removal was confirmed. This tests staging/startup, not a
full teacher trajectory or protection against a malicious process bypassing
Python startup. See `session-bundle-native-staging-001/receipt.json`.

Fourteen focused bundle/transport tests pass in the requests-enabled environment.
Full discovery completes 370 tests: 337 passed, 33 skipped. Shared qualifier
resource bindings, native trajectory qualification and resource-aware admission
review remain outstanding. Corpus 009 and all training gates are unchanged.

### Shared qualifier resource integration

The V2 qualifier now accepts an explicitly profile-bound Session response bundle,
records its receipt, capture and body identities in qualification inputs, and
checks that a candidate replay used the same bundle and adapter as its grader.
Missing resources or a mismatched receipt are rejected before container startup;
the preflight denial probes recorded zero container calls and no output directory.

An explicit `publisher_nodes_only: true` profile option selects every declared
FAIL_TO_PASS and PASS_TO_PASS node within the reviewed test files. This avoids
implicitly running unrelated website-dependent tests. Duplicate/foreign nodes
are rejected and the existing strict comparator still requires exact outcome
coverage. Reports retain the scope of current recorded-response transport.

The shared qualifier, exercised in two separate base/reference containers, passes
all eight expected publisher transitions for online-judge-tools 445: base 7/8,
reference 8/8. The final source-bound result is
`onlinejudge445-v2-bound-controls-002/report.json`. No native candidate was supplied
to this run. Twenty-four focused tests pass; full discovery completes 372 tests,
339 passed and 33 skipped. Previous shared implementations and the first control
run's implementation are retained in `artifacts/official` for evidence integrity.

Remaining work for this task includes sanitized source isolation, full teacher
replay, grading its submitted patch, and resource-aware admission and supervision
review. The current admission rejection for injected support modules remains in
force; corpus size and training approval are unchanged.

### Online-judge-tools snapshot and native workspace preflight

The first snapshot build exposed a Python 3.7 incompatibility in the containment
check (`Path.is_relative_to`). The replacement uses component-aware `relative_to`
with a ValueError boundary, retaining the containment policy. Seven snapshot
tests pass, including prefix-confusion rejection; full discovery completes 373
tests, 340 passed and 33 skipped. The earlier implementation and failed build
remain preserved.

Snapshot build 002 and verification 001 preserve all 89 tracked files and the
exact source tree. One parentless commit is reachable; the old base, PR head and
merge commits are inaccessible, and the declared oracle paths are absent. This
is mounted-filesystem evidence, not an audit of inherited Docker layer bytes.
The same eight recorded-response publisher transitions pass on the sanitized
image, with base 7/8 and reference 8/8.

Native replay attempt 001 terminated at workspace preparation, before any source
trajectory command. Traced diagnosis identifies six untracked
`online_judge_tools.egg-info` metadata files and one `__about__.cpython-37.pyc`
cache file. The owned container was removed. No broad cleanup or allowlist
exception was added. These exact leftovers require reviewed handling and another
native replay attempt; do not describe this attempt as a successful trajectory.
See `onlinejudge445-v2-workspace-diagnostic-001/report.json` and the retained
native replay receipt. Training remains unapproved.

### Online-judge-tools native replay and graded patch

The exact six installer metadata files were relocated byte-for-byte outside the
source workspace in an owned derived image. A path-only site-packages entry
preserves distribution discovery. Version 6.3.0, metadata location, source import
and the console entry point were checked. Only the reviewed bytecode cache was
removed. The tracked tree and snapshot isolation were independently reverified.
The strict workspace preparation policy was not relaxed.

Replay 002 reached cleanup and exposed Python 3.7 incompatibilities in the
standalone cleanup code (assignment expression and `Path.is_relative_to`). The
replacement preserves file-identity and path checks. The failed attempt and
previous shared implementations are retained. Six cleanup tests pass and full
discovery remains 373 tests: 340 passed, 33 skipped.

Replay 003 completes with 29 charged calls plus native submission (30 recorded
exchanges), all tool outcomes successful, intended/submitted patch bytes equal,
and confirmed container removal. The resource-bound native grade matches all
eight reference outcomes; base is 7/8, reference and native candidate are 8/8.
See `onlinejudge445-v2-native-replay-003/receipt.json` and
`onlinejudge445-v2-native-grade-001/report.json`. This is teacher replay evidence,
not model inference or learned improvement.

History construction was attempted and rejected by the existing portable-replay
gate for injected support modules. No history or token arrays were produced.
Resource-aware history/admission contracts and supervision/rights review remain
required; the gate has not been bypassed and no training example was admitted.

### Resource-aware history reconstruction and context audit

The history builder now accepts an explicit Session bundle only after verifying
its capture/body identities, reviewed receipt and budget, replay producer hashes,
adapter bytes, startup hash and exact PYTHONPATH. All resource inputs and the
binding verifier are included in the history receipt. Missing bundles, altered
producer/configuration bindings and changed response bytes reject. This proves
configuration and byte consistency, not training permission or semantic quality.

The final history 003 contains 62 messages / 30 exchanges. Token audit 002 exports
19,438 untruncated input tokens and 7,151 supervised tokens. It fits the 32,768
input cap and leaves room for the configured 8,192-token reserve; it also fits
the 8,192-supervised-token update limit. No model weights or GPU were used.

Six focused binding/history tests pass. Full discovery completes 377 tests:
344 passed, 33 skipped. A real admission attempt still rejects the resource-backed
replay under the unchanged portable-replay gate; its failure log is retained.
Resource-aware admission, supervision quality, rights and final corpus gates
remain unresolved. These exported arrays are unapproved candidates, not part of
the assembled training corpus. The prior history-builder implementations remain
archived for hash-bound evidence.

### Resource-aware mechanical assessment; online-judge-tools supervision hold

Assessment now verifies the replay/history/grader resource chain, bound grader
profile, actual cached response bytes and adapter in each control container,
and the recorded transport events. It recomputes tests, histories and token
budgets as before. Four copied-evidence attacks (body, adapter, denied transport
event and claimed bundle metadata) reject. Orphaned resource claims on a portable
replay also reject. Full discovery completes 378 tests: 345 passed, 33 skipped.

Online-judge-tools 445 passes this mechanical assessment with 19,438 input and
7,151 supervised tokens. The result explicitly does not approve training.
Substantive supervision review instead holds the trajectory: its unmodified
source-index-50 scenario script exits successfully and claims to test `get_name`
on the actual broken base, while calling the real repository `get_name` with the
captured contest page raises AssertionError. The copied regex test does not
exercise the claimed repository behavior. This does not invalidate the repaired
patch, which passes eight graded cases; it invalidates the unchanged test claim
as positive command supervision.

See `onlinejudge445-v2-admission-001`, `resource-admission-negative-001`,
`onlinejudge445-v2-supervision-screen-001`, supervision review 001 and priority
review 009. Preserve the trace and counterexample. Reconsider only with qualified
replacement supervision or a separately specified selective-supervision policy.
Corpus 009 remains six quarantined examples / 35,029 supervised tokens.

### dbt–Snowflake 716: method contract screened, native replay pending

The task was extracted from the hash-verified SWE-rebench V2 shard. Source and
Apache-2.0 notice were retrieved at its exact base commit. The initial capture
used the wrong license filename and remains recorded as failed; capture 002
uses the actual `LICENSE.md` path.

The candidate patch produces the same connections file and cancellation-method
AST as the publisher reference. Eleven constructed method-level cases execute
that exact AST with observable adapter/cursor boundaries: base 2/11, candidate
11/11, reference 11/11. They cover session-ID SQL construction, one result fetch,
return behavior, and propagation of query/fetch errors. These probes do not
import the full repository or test Ctrl+C dispatch or live Snowflake queries.

Source supervision review does not reject a static check merely for being
static: the source script labels database behavior as expected, while its
actual checks inspect source text. Its orphan-query explanation is an issue
report, not a verified universal database rule. Native publisher controls,
trajectory replay, rights review and token audit remain pending. See
`dbtsnowflake716-v2-review-001` and `dbtsnowflake716-v2-semantic-001`.
The candidate is not added to Corpus 009 and remains unapproved for training.

### dbt–Snowflake 716: native replay and mechanical assessment completed

The digest-pinned original image and independently verified source snapshot both
produce the expected 38-node publisher result: base 37/38, reference 38/38.
The submitted native candidate passes 38/38 with no reference disagreements.
The snapshot preserves 152 tracked files, has one parentless commit, and makes
the prior base, PR head and merge commits inaccessible in its mounted filesystem.
Inherited image layers have not been audited for recoverable history.

Native replay 001 retains fresh observations for 18 charged calls plus submission.
Its `diff` command returns the expected exit 1 for a changed file; the native
CommandError and difference output remain intact in the history. The initial
`find /testbed` returns no results because that path is a workspace alias; later
direct file reads succeed. Neither observation was replaced with source output.
Reviewed cleanup removes the source-created backup and patch export before
native submission. Submitted and intended patch bytes match, and container
cleanup is confirmed.

History 001 has 40 messages / 19 exchanges. Token audit 001 exports 12,307 input
tokens and 4,125 supervised tokens without truncation. Mechanical assessment
001 passes; it does not approve training. Complete observation/dependency rights,
final split isolation and corpus admission remain pending. No live Snowflake
service or GPU/model execution occurred. Corpus 009 remains unchanged.

### Corpus 010 integration supersedes the six-example current assembly

The new quarantine assembly adds dbt–Snowflake and contains seven examples,
115,534 input tokens and 39,154 supervised tokens. All four admission gates
remain null. Publication 011 and restore 010 verify 15 files / 1,280,267 bytes;
restored inspection validates all records. Original schedule 011 and restored
schedule 009 are byte-identical: seven whole-example updates, one epoch,
seed 7401, 8,192 supervised-token update ceiling and zero target overshoot.
Training denial 009 rejects this exact real corpus. Nineteen focused corpus
and scheduling tests pass. Lineage review 005 finds no known repository-ID or
fork-network overlap with the four reserved projects; broader isolation remains
unproven. Earlier Corpus 009 statements above are historical results.

### PennyLane 5831 controls and publisher parameter selection

The next candidate preserves `Exp.num_steps` during simplification. The pinned
original environment collects 345 whole-file cases, of which 176 skip; that run
is retained and fails strict qualification. Directly selecting all publisher
keys also fails because six parameter labels were truncated at whitespace in
the publisher metadata.

The qualifier now widens an incomplete parameter identity to the whole test
function and deduplicates overlapping selectors. This only controls execution;
the existing comparison still demands exact publisher-group coverage, all
phases, no skips and correct transitions. A regression test confirms that an
extra, unlisted parameter rejects. The previous qualifier bytes are archived in
`artifacts/official/qualifier-before-truncated-publisher-001` for historical
receipt verification. No old receipt was rebound to changed producer code.

Controls 003 execute all 169 required publisher cases: base 168/169, reference
169/169. Additional actual-repository numerical probes compare explicit 4x4
Pauli-generator exponentials against SciPy, checking step counts and repeated
simplification with absolute tolerance 1e-12. Base passes 8/24; reference and
source candidate pass 24/24. NumPy-only probes do not certify optional backends,
differentiation or arbitrary operators. Native trajectory replay remains pending.

Source review also identifies errors in the dataset's added interface paragraph
(an extra imaginary factor and incorrect `num_steps=None` semantics). The
existing history builder conditions on the original task problem statement,
excluding that paragraph; inspect the actual generated history before assembly.
No candidate has been added to Corpus 010 in this cycle. Twenty-one focused
tests pass; full discovery completes 380 tests: 347 passed, 33 skipped.

### PennyLane 5831 native qualification

The source snapshot preserves all 1,366 tracked files and has one parentless
commit. Independent verification finds the old base, PR head and merge commits
inaccessible and known oracle paths absent in the mounted filesystem. Inherited
image layers are outside that verification scope.

Native replay 001 completes 30 charged calls plus submission. Two original
trajectory mistakes remain as actual failed observations: source index 18 calls
a NumPy matrix as a function, and index 32 specifies an incorrect pytest class.
Subsequent corrections and final checks succeed. Cleanup removes only the six
reviewed scratch files; submitted and intended patch bytes match.

Native grade 001 covers all 169 publisher cases: base 168/169, reference and
candidate 169/169. Mechanical assessment 001 passes without approving training.
History 001 has 64 messages / 31 exchanges; token audit 001 exports 17,691 input
tokens and 6,993 supervised tokens without truncation. Conditioning review 001
verifies that the original issue is preserved and the inaccurate added-interface
paragraph is absent from the actual generated user prompt.

Whole-file optional-backend skips remain unresolved; these results do not
certify all PennyLane backends. Rights, final split review and corpus integration
remain pending. Corpus 010 is unchanged and no GPU was used.

### Corpus 011: eight tasks across seven repositories

Selection 010 and assembly 011 add the qualified PennyLane 5831 token history to
quarantine: 133,225 input tokens / 46,147 supervised tokens. Both PennyLane tasks
remain in the same `train` repository group; this is not an eighth independent
repository. Four admission gates remain null, and denial 010 confirms training
is rejected for the actual new bundle.

Publication 012 and restore 011 verify 17 files / 1,479,218 bytes. Restored
inspection 011 validates all eight records. Schedule 012 and restored schedule
010 are byte-identical: seed 7401, one epoch, eight updates, an 8,192-token
supervised-update ceiling, and zero overshoot of the 46,147-token target.

Composition report 001 computes exact rational repository token shares. The
two PennyLane tasks account for 30.62% of supervised tokens. Inverse squared-share
concentration is approximately 5.604 repository equivalents out of seven; this
describes token concentration, not statistical independence or effective sample
size. Prioritize additional projects rather than treating same-project examples
as independent evidence. Corpus 011 remains far short of the 3×50M plan.

### PySyft 250: operational checks pass; documentation defects hold the trace

The hash-verified V2 task and digest-pinned Python 3.7 image reproduce publisher
controls: base 128/132, reference 132/132. Twenty additional actual-repository
cases cover integer, float, nonfinite, scalar, complex, empty and broadcast
equality, copy/in-place behavior, failed broadcasts and encrypted-left-operand
short-circuiting. Scalar comparisons provide the expected values. Base passes
0/20; reference and source candidate pass 20/20. This does not prove arbitrary
tensor behavior or encrypted computation correctness.

However, Python doctest executes seven examples in the candidate's added method
docstrings and finds two failures. `eq` shows `TensorBase([...])` instead of the
actual `BaseTensor: array([...])`. The `eq_` example expects no display although
the method returns the tensor. The source verification checks documentation
presence and keywords, so it does not catch these incorrect examples.

Review 001 holds this unchanged trajectory out of positive corpus selection.
The executable equality code is not invalidated by these documentation defects.
A corrected, explicitly new trajectory can be qualified later; do not silently
rewrite historical supervision. Snapshot build 001 completed, but independent
snapshot verification and native replay were not performed after discovering
the defect. Corpus 011 remains unchanged; no GPU was used.

### PySyft 250: verified documentation correction, not a new trajectory

Correction 001 is a separately labeled assistant-authored derivative. It changes
the `eq` example's displayed result to the actual representation and assigns
the `eq_` return to `_` so that the example correctly expects no display.
The original candidate and all original observations remain untouched.

The executable AST, excluding documentation strings, is identical before and
after correction. Actual pinned-runtime checks pass 132/132 publisher cases,
20/20 operational cases and 7/7 doctest examples. The correction report binds
the source inputs, derived patch and exact documentation-only difference.
This verifies a patch artifact; it is not a model-generated trajectory or
training-admission receipt.

To recover this task as training material, record an explicit new correction
trajectory with fresh native observations of the failing examples, the edit
and the successful rerun. Preserve the source trace's identity and label new
commands as assistant-authored extensions. Verify the final submitted patch,
reconstruct the extended history, audit tokens and retain all admission gates.
Do not relabel historical source messages or invent intermediate observations.
Corpus 011 remains unchanged pending that work.

### Explicit correction replay support and PySyft fresh history

The replay path now accepts an optional reviewed correction plan with separate
source/corrected patch identities, assistant authorship, rationale, exact commands
and expected process exits. Native command failures must match their explicit
exit codes; timeout/infrastructure errors cannot substitute. History projection
maps correction indices and authorship separately, preserves fresh failure
observations and rejects undeclared or misattributed actions. Assessment verifies
the correction provenance and adds a distinct supervision-review gate.

Previous implementations are retained under
`artifacts/official/before-correction-replay-001`. Original traces and receipts
are not rewritten. Four new tests cover plan/schema rejection, actual-exit
requirements, patch-provenance mismatches and history attribution. Fifteen focused
tests pass; final full discovery completes 384 tests: 351 passed, 33 skipped.

PySyft corrected replay 001 reached cleanup but was rejected because a manually
formatted diff differed from canonical Git output. The failed attempt remains
intact. Profile 002 binds a canonical diff generated from the verified correction.
Replay 002 completes 34 charged calls plus submission, with four explicit
correction commands: failing doctests, the edit, successful doctests and patch
export. Cleanup is confirmed and submitted bytes equal the corrected export,
explicitly not the original teacher export. Native grade passes 132/132 cases.

Corrected history 001 has 72 messages / 35 exchanges and passes mechanical
assessment with 22,706 input / 8,218 supervised tokens. The context plus reserve
fits, but the example exceeds the current 8,192 supervised-token update cap by
26 tokens. Budget review 001 records this without truncation or silently raising
the cap. Correction-supervision review, budget/runtime qualification and all
ordinary admission gates remain pending. Corpus 011 is unchanged; no GPU was used.

## Corpus 012: preserved correction history and restored schedule

The current assembly contains nine examples across eight repository groups,
155,931 input tokens and 54,365 supervised targets. The added PySyft trajectory
preserves the observed doctest failure and explicitly assistant-authored correction;
the unchanged original trace remains excluded. Mechanical replay is not evidence
of a trained model producing this fix. All admission gates remain unresolved.

The inspection update cap is now 9,216 supervised targets, explicitly replacing
8,192 for this plan because the complete correction example has 8,218 targets.
This changes example grouping and optimizer-update frequency; it is not claimed
equivalent to the earlier schedule or validated GPU capacity. With seed 7,401,
one epoch consumes all 54,365 targets in eight planned updates with zero overshoot.
No tokens were truncated to meet the earlier cap.

R2 publish and independent restore verified 19 files totaling 1,731,152 bytes.
Restored corpus inspection passed, and both schedule and update files are byte
identical to the original 9,216-cap plan. Training-purpose loading still rejects
the quarantine corpus. Repository identity/fork screening found no overlap with
the four reserved projects; detached copies and semantic overlap remain unexcluded.

Evidence: [assembly](../evidence/data/training-corpus-assembly-012/receipt.json),
[selection rationale](../evidence/data/training-corpus-selection-011/rationale.json),
[restore](../evidence/data/training-corpus-restore-012/receipt.json),
[schedule comparison](../evidence/data/training-corpus-restored-schedule-011/comparison.json),
[training denial](../evidence/data/training-corpus-denial-011/report.json), and
[lineage screen](../evidence/data/current-corpus-lineage-006/report.json).

This small qualification corpus does not supply the planned 3×50M campaigns.
Continue diverse task acquisition, attribution and split review locally; keep
the Pod stopped until a bounded GPU qualification bundle is ready.

## Explicit-input qualification batch planning

The batch planner now requires the corpus path and expected manifest SHA-256,
source screen, census and evaluation metadata as explicit inputs. Seed and
per-stratum sample size are configurable. It automatically adds current corpus
repository groups and reserved evaluation repository names to exclusions.
Source/census integrity, deterministic selection and input-drift checks remain.
The prior implementation is preserved under
`artifacts/official/qualification-planner-before-explicit-inputs-001`.

`evidence/data/qualification-batch-current-001` records a 32-repository batch
against Corpus 012 from 2,621 screened traces, 1,575 tasks and 902 repositories.
Three sampling tests pass; a live negative check rejects an incorrect corpus
manifest hash without creating output. Selected repository names are distinct
and do not overlap explicit exclusions. These are exact-name checks only.
Before new replay, reconcile this batch with historical task reviews and canonical
repository aliases; selection alone does not establish that every task is new.

The optimistic one-trace-per-task ceiling is 38,705,625 supervised targets
before masks, quality rejection and admission review. It is not acquired usable
training supply. No new example is admitted and no GPU work is started.

## Batch reconciliation and new repository coverage

Exact trajectory reconciliation found all 32 entries in current-batch-001 were
already in qualification-batch-001. They are not new data. The planner now
accepts repeatable `--previous-batch` files, binds their hashes, and excludes
their repository names before stratification. Current-batch-002 contains
32 distinct repositories with zero case-normalized name overlap with batch001.
All 32 issue descriptions were extracted from identity-checked pinned shards.
Three deterministic sampling tests still pass. No task has been accepted.

The new live lineage check resolved five of 36 requested source/reserved names;
31 returned HTTP 403. Its identity screen is incomplete and cannot support
admission. Do not interpret this as evidence of repository independence or
retry the entire batch blindly. Local issue/patch review can continue meanwhile.

Next review priority: statsmodels-8339 (penalized autocorrelation lag selection),
numkit-8 (smoothing boundary indices) and emcee-295 (compatibility axis order).
These are issue-only priorities, not verified fixes or mathematical claims.
Inspect pinned source, reference tests and teacher actions before defining
independent boundary/property tests or spending runtime resources.

Evidence: `qualification-batch-reconciliation-001`,
`qualification-batch-current-002/issue-extraction.json`, and
`qualification-batch-current-lineage-002/report.json`. Pod remains stopped.

## Statsmodels 8339: reference defect and teacher distinction

Pinned source and evaluator patches were extracted and retained. The reference
patch uses `max(1, np.argmax(scores))` for scores indexed by lags 1 through
n-1; this omits the index-to-lag +1 conversion. An isolated execution of its
actual patched auto-lag block disagrees with rational score maximization in
322 of 1,452 cases (all nonconstant ternary length-six series, both statistics).
For [-1,-1,-1,0,0,-1], Ljung-Box penalized scores have their maximum at lag 2
(-33/20), while the reference selects lag 1 (-26/15). The test patch only
requires a positive lag count and leaves exact lag validation as a TODO.

The extracted teacher edit instead initializes the original helper with lag 1
and negative infinity. Its actual helper agrees with all 1,452 rational-score
cases, versus 1,138 disagreements for the base helper. These are constructed
algorithm probes of the 2p penalty branch, not full-package tests, mathematical
proof over all inputs, or validation of the teacher's recorded test claims.
The pinned full source also includes lag zero in its threshold metric; broader
theoretical conformity needs a separate source/paper audit before any such claim.

Hold the reference as a correctness oracle; retain the teacher for independent
runtime and supervision review. No corpus admission or GPU use. Evidence:
`statsmodels8339-{task,evaluator,source,math,teacher-math}-001` and
`statsmodels8339-teacher-002`. Probe sources are retained alongside results.

## Statsmodels full-package runtime corroboration and control mismatch

The pinned local evaluator image downloaded successfully; its /testbed checkout
matched the exact base commit and source bytes. Actual package calls reproduce
the mathematical probe results on all 1,452 cases: base raises 1,138 errors;
reference returns 322 wrong lags; teacher has neither errors nor wrong lags.
NumPy is 1.24.4. This is direct runtime evidence, not agent replay or training.

With publisher test additions applied, all 131 diagnostic-file tests pass in
all three roles, including all setup/call/teardown phases and unchanged tracked
source during tests. The publisher-declared failing white-noise case already
passes on the base. Therefore benchmark-control qualification is held; do not
write a passing baseline receipt or call these tests discriminating evidence.
The independent cases remain useful but do not silently override this mismatch.

Teacher verification also includes a universal p>0.05 expectation for a random
white-noise sample and catches failures without failing process exits. Audit
actual observations before any native history can be admitted. Disposable
containers were removed. Evidence: `statsmodels8339-runtime-math-001`,
`statsmodels8339-controls-001`, and retained runtime-source-001 scripts.
The earlier import hydration wait completed; no duplicate run or Pod start.

## Statsmodels random-state diagnosis and explicit control configuration

The pinned fixture resets NumPy's global state to seed 1. A paired direct-call
sweep (seeds 0..31, normal and uniform length-1000 inputs) produced 49 base
errors and zero candidate errors, with identical input hashes across roles.
Two candidate samples have first-lag p-values below 0.05; the teacher's universal
white-noise p-value expectation is invalid. These fixed-cohort counts are not
population failure-rate estimates.

Repeating the full diagnostic file with the explicit pytest option
`-p no:randomly` restored the publisher distinction: base 130/131, reference
131/131, candidate 131/131. The base fails exactly the declared white-noise
FAIL_TO_PASS node; all other setup/call/teardown outcomes meet expectations.
This intervention identifies pytest-randomly interaction as the cause of the
observed default-plugin mismatch. Preserve both configurations and require the
explicit override for this task's qualification. No default-runtime parity claim.
The separate reference lag-index defect remains and blocks its use as an
unqualified correctness oracle. Native history and supervision review remain.

Evidence: `statsmodels8339-randomstate-001/comparison.json` and
`statsmodels8339-controls-002/comparison.json`; scripts and prior runs retained.
No training admission, learned-performance claim or Pod start.

## Statsmodels native replay preparation

Source-action preflight passed: 18 shell calls, eight views, three creates and
one source replacement; two reasoning entries are excluded from execution and
one finish becomes submission. The three scratch verification scripts require
explicit reconciliation before submission. Actual failure observations and
unsupported blanket claims require review, not silent removal.

GitHub API PR metadata still returns 403. Public Git ref resolution succeeded:
refs/pull/8339/head advertises 0dd88024badd563190f8000f06ec003506215df2. This is
a PR head, not an asserted merge commit. The snapshot build uses this identity
and checks its local relationship to the pinned base. Build and independent
verification must finish before native replay. Evidence:
`statsmodels8339-snapshot-resolution-002` and `statsmodels8339-replay-preflight-001`.
No native replay, data admission or Pod restart has occurred in this step.

## Snapshot verification and exact blob-hash optimization

Statsmodels snapshot build001 and independent verify001 completed: 2,131
tracked files match the original manifest, one parentless commit remains,
base/PR-head commits are inaccessible and declared oracle paths are absent.
This covers the mounted filesystem, not inherited Docker layer bytes.

Future snapshot verification now computes Git SHA-1 blob identities directly
from `blob <byte length>\0` followed by the original bytes, rejecting non-40-hex
index identities under the existing SHA-1 snapshot contract. Symlinks use link
text. This removes one Git process per file without dropping byte/mode checks.
Eight focused tests pass, including independent `git hash-object` comparisons
for binary, empty, Unicode/CRLF, executable and symlink content and rejection
of modified content. The previous implementation is retained in
`artifacts/official/source-snapshot-before-local-blob-hash-001`.

On the actual 2,131-file statsmodels snapshot, the new verifier produced the
identical full tracked manifest hash as the old Git-backed implementation.
Observed verification time was about 0.254 seconds in one run, not a general
performance guarantee. Evidence: `snapshot-blob-hash-runtime-001`. The full
regression run remains pending local test-file hydration; no all-suite pass
is claimed. Native replay and training admission remain pending; Pod stopped.

## Snapshot optimization regression complete

The pending full local suite completed: 385 tests, 352 passed, 33 skipped,
zero failures. Evidence: `evidence/p1/snapshot-blob-hash-regression-001`.
Skipped coverage and GPU behavior remain unqualified. Statsmodels native replay
attempt001 stopped before execution on shard-hydration metadata drift; after
confirmed termination, attempt002 started against the verified source snapshot.

## Statsmodels native replay result and hold

Attempt002 completed with 30 charged tool calls plus native submission, fresh
observations and confirmed container removal. The original error appears in
pre-edit stdout despite exit zero; after the repair the same reproduction
succeeds. The actual diagnostic run reports 130 passed (original tests, without
publisher additions). Reconstructed history has 64 messages and 31 exchanges.

Pinned tokenizer measurement: 17,227 input and 4,057 supervised tokens; adding
8,192 output reserve gives 25,419, within 32,768. No tokens were exported for
training. Submitted patch includes final_verification.py and reproduce_issue.py
as well as the intended diagnostic.py edit. Hold this attempt pending explicit
scratch reconciliation and supervision correction; do not silently strip files
or relabel the attempt as accepted. See `statsmodels8339-native-review-001`.

## Explicit pre-submission completion support

The SWE-Hero replay path accepts an optional assistant-authored completion plan
bound to the exact adapted source actions and expected final patch. One to
eight declared commands run before the original terminal submission. Every
native outcome is retained, including an explicitly expected nonzero process
exit; infrastructure errors do not count as that expected failure. Source and
completion actions remain separately attributed in reconstructed history.
Plan, source-action and final patch mismatches reject; tool budgets still apply.
Original traces and earlier replay artifacts are unchanged.

Four focused tests exercise authorship, ordering, altered commands, failure
provenance and terminal validation. Full local suite: 389 tests, 356 passed,
33 skipped. Evidence: `evidence/p1/replay-completion-regression-001`.
Previous scripts are preserved under
`artifacts/official/source-replay-before-completion-001`.

Statsmodels completion-plan-001 declares an expected failing p-value assertion,
a correction plus independent lag check, and hash-verified scratch cleanup.
Native attempt003 is the integration test; do not infer success from unit tests
or plan preparation. Training approval remains false and the Pod stays stopped.

## Statsmodels corrected native replay and completion integration

Attempt003 completed with 33 charged calls plus native submission and confirmed
container removal. Three separately attributed completion actions preserve the
observed p-value counterexample (native CommandError exit1), correct the
verification assumption, check the independent lag case, and remove three
hash-verified scratch scripts. Final native patch matches the declared hash
and modifies only diagnostic.py. Applying it and the control candidate to the
same pinned source produces identical bytes; prior 131-test controls apply to
that exact source change, not to an invented new test run.

Reconstructed history: 70 messages, 34 exchanges; all three added actions have
null original source indices and explicit adapter authorship. Complete native
tokenization yields 19,994 input / 6,446 supervised tokens, 28,186 including the
8,192 output reserve. Token arrays were exported as an unapproved candidate.
Source failures and corrective observations are retained. No Gemma model ran.

Evidence: native-replay-003, native-history-003, native-tokens-002 and
native-alignment-001 under the statsmodels8339 prefix. Next: task-level review,
canonical repository isolation, rights/observation attribution and corpus
integration. The reference's lag-index defect remains documented; no general
mathematical correctness or training readiness is claimed. Pod remains stopped.

## Corpus 013: corrected statsmodels quarantine integration

Ten examples across nine repository groups now total 175,925 input tokens and
60,811 supervised targets. The corrected statsmodels history has a distinct
completion-plan-derived example ID; the earlier scratch-containing submission
remains excluded. All four training admission gates remain null. New repository
identity and observation/rights checks remain open; no lineage pass is invented.

R2 publish and independent restore verified 21 files, 1,957,026 bytes. Restored
inspection passed and schedule/update files are byte-identical. Seed7401, one
epoch and cap9216 yield nine planned updates with zero target overshoot. This
is an inspection plan only. Training-purpose load rejects the new manifest.

Evidence: selection012, assembly013, publish014, restore013, restored-inspection013,
schedule014, restored-schedule012 and denial012 under their training-corpus
prefixes. P1 remains incomplete: this small qualification corpus does not
supply three 50M-token campaigns. Next local work should expand repository/task
coverage and close attribution and isolation gaps, without repeating the current
small corpus and describing that as additional unique data. Pod remains stopped.

## Numkit 8 mathematical/source screening

Selected exact teacher trace 9157adb5-0648-4a1d-8ab6-c58fdc6394d2 from the
new repository batch. Pinned source, evaluator patches, teacher actions and
LICENSE were captured; old COPYING and alternative notice URLs returned 404.
The teacher smooth function AST equals the reference's smooth function AST.
Reference changes elsewhere are not asserted equivalent.

An independent scalar convolution calculation matched the extracted teacher
function in 1,620 constructed cases: lengths3..20, supported odd window sizes,
six window types including asymmetric custom weights, and ramp/constant/
oscillatory inputs. Base raises TypeError on all those cases under Python3.
Even-window rejection and unit-window identity were checked. This is isolated
function execution, not full-package qualification or native replay.

For odd w>=3, n>=w: padded length n+2(w-1), valid convolution length n+w-1,
then trimming w-1 entries yields n. Nonfinite/zero-sum weights and Python2
behavior are outside this check. Next: pinned runtime controls and source
observation review. Evidence: numkit8-{source002,evaluator002,teacher002,math001,
review001} directories (hyphens retained in actual filenames). Corpus remains
013, training unapproved, Pod stopped.

### Numkit pinned runtime controls

The first control attempts did not execute tests: the publisher image had the
wrong checkout, and neither Conda interpreter imported the source package.
Those failures are retained. The normalized, isolated snapshot preserves all
39 tracked files. A derived image explicitly binds `/testbed/src` into the
existing Python 3.6 environment using a `.pth` file; it downloads no packages.
The installed versions are NumPy 1.19.2, SciPy 1.5.2 and pytest 7.0.1.

The repaired image reproduces exactly the publisher's five smoothing failures
on the original code and 48 passes. Reference and teacher fixes each pass all
53 cases. Every setup, call and teardown result, collection membership,
unchanged tracked source and container cleanup is checked by
`numkit8-runtime-source-001/assess_controls.py`; the bound report is
`evidence/data/numkit8-runtime-assessment-001/report.json`.
Isolation was reverified after the import repair: one parentless commit,
matching tracked manifest, old commits inaccessible, declared oracle paths
absent. This checks the mounted filesystem, not inherited image layers.

These results qualify this test file only. Native action replay, observation
quality, rights and final corpus admission remain separate requirements.
Corpus 013 remains unchanged and unapproved for training. No Runpod compute
was used for these controls.

Numkit native replay subsequently completed 28 charged actions plus submission
(29 exchanges), removing its own three scratch scripts. The submitted patch
changes only the slice division and produces exactly the source bytes tested
above. History projection preserves fresh observations and four command
failures, including full-suite collection failure from the missing
`scipy.integrate.quadrature` module. A NumPy binary-compatibility warning also
remains visible. Neither is treated as a passing full-suite result.
The reconstructed history tokenizes to 17,967 input and 3,973 supervised tokens;
with an 8,192-token output reserve, the total is 26,159, below 32,768.
Evidence: `numkit8-native-{replay,history,tokens,assessment}-001`.
This candidate is not added to Corpus 013 pending observation and attribution
review. Native teacher replay demonstrates tool execution, not Gemma ability.


## Corpus 014: Numkit numerical-verification integration

Eleven examples across ten repository groups total 195,042 input tokens and
65,769 supervised targets. The Numkit example uses a completion-plan-derived ID
and explicitly attributes one added numerical verification command to the
assistant. The earlier original-only replay remains archived, not duplicated
in this assembly. Native numerical verification matched an independent scalar
convolution oracle in 1,620 cases, with maximum absolute error
7.105427357601002e-15; zero-output and reversed-custom-weight mutations were
rejected in 1,620 and 180 cases respectively. This is bounded numerical evidence,
not a universal proof. Full-suite collection failure, compatibility warnings
and original command failures remain in the observations.

R2 publish and independent restore verified 23 files / 2,169,563 bytes. Restored
corpus validation passed. With seed 7401, one epoch and a 9,216 supervised-token
update cap, the inspection schedule has ten updates and zero token overshoot.
Original and restored schedule/update files match byte for byte. No optimizer
steps occurred; training-purpose loading correctly rejects the quarantine
manifest. All four admission gates remain null. Repository identity and rights
review remain open, including the newly added Numkit group.

Evidence: selection013, assembly014, publish015, restore014,
restored-inspection014, schedule015, restored-schedule013 and denial013, under
the training-corpus evidence prefixes. Numerical evidence and content review:
numkit8-native-replay-002, numkit8-native-history-002, numkit8-native-tokens-002,
and numkit8-observation-review-001. Corpus manifest SHA256:
`ccca52a2abb0b9bf856390dc33349357e2d2b95b1eb3396c14a513b6d78dd78d`.

Next: scale diverse task qualification and complete attribution and repository
isolation review. This small corpus still does not supply the planned 3×50M
campaigns. P1 remains incomplete and the Pod stays stopped.


## Explicit source timeout support and emcee runtime controls

The replay adapter now accepts an explicitly specified integer 30-second source
command timeout because it equals the native runner limit. The original timeout
is retained in the adapted action. Other limits, boolean/float/string values and
unknown argument fields reject. The same constant controls the recorded limit
and native context configuration. Fourteen focused tests pass; the full local
suite reports 391 tests, 358 passed and 33 skipped. The initial broad run had two
source-hydration inventory failures; those logs are retained, and no integrity
check was relaxed to obtain the subsequent passing run.

Emcee task 295 has a pinned 124-file source snapshot. Its original image lacked
h5py, silently omitting ten HDF backend tests. An explicitly recorded offline
addition of the hash-verified h5py 3.12.1 CPython 3.9 Linux wheel restores that
coverage while retaining NumPy 2.0.2. This is an environment repair, not a claim
of historical environment equivalence. Source isolation was reverified after
installation. All 21 publisher test transitions match: base 11 passes / 10
failures, reference and candidate 19 passes / 2 failures. Both persistent
failures are publisher-declared FAIL_TO_FAIL cases; they are not counted as
successful tests or silently omitted. Candidate and reference agree on every
case, including setup and teardown validation.

Evidence: `evidence/p1/explicit-source-timeout-regression-001`,
`evidence/data/emcee295-h5py-verify-001`,
`evidence/data/emcee295-controls-002`, and `qualification-triage-publish-002`.
Emcee native replay and observation review are still separate requirements.
Corpus 014 remains unchanged and quarantine-only. The Pod remains stopped.


The first completed emcee native replay executes 39 charged actions with the
explicit 30-second source timeout preserved. Its disposable container was
removed. The submitted patch still contains `reproduce_issue.py` alongside the
intended source fix; it is held and is not part of Corpus 014. Next work must
review the observations, verify numerical axis mapping inside the native
package, and remove only identity-verified scratch files through an explicitly
attributed completion. The initial pre-container attempt failed source-shard
hydration checks and its log is retained. Evidence: emcee295-native-replay-002
and emcee295-native-preflight-failure-001.

### Completed emcee replay and bounded observation review

The later `emcee295-native-replay-004` completes 40 charged actions and submission,
with container cleanup verified. Its 415-byte source-only patch produces exactly
the same source bytes as the candidate tested in controls-002. The separately
attributed completion checks 224 stored log-probability values across memory and
HDF5 storage, legacy/modern axis correspondence and flatten order, with observed
maximum absolute error zero. It removes four hash-verified scratch files.

`emcee295-native-history-003` reconstructs 84 messages and 41 exchanges.
`emcee295-tokens-001` measures **27,404 input / 5,675 supervised tokens**, without
truncation, using the pinned model tokenizer. This establishes context-cap fit,
not GPU-memory fit. `emcee295-observation-review-001` verifies patch alignment,
completion observations, history attribution and preserved error indices
16, 18, 62 and 72. Native test output is tool-truncated; no full-suite totals are
inferred from it. The independent publisher controls retain both FAIL_TO_FAIL
cases and verify all 21 cases (base 11 passes; reference and candidate 19).

This candidate is eligible for quarantine selection review only. It has **not**
been assembled into Corpus 014, which remains unchanged. Training approval,
repository identity, observation attribution and dependency notices remain open.
Finite checks do not establish MCMC convergence or universal correctness.
The new history, token audit and observation review still require R2 archival.


## Corpus 015: emcee completion integration

The current quarantine assembly contains 12 examples from 12 tasks and 11 declared
repository groups: **222,446 input / 71,444 supervised tokens**. The added emcee
history includes a separately attributed completion with actual memory/HDF5
sampler assertions and verified scratch cleanup. Its source patch yields the
same bytes as the independently tested candidate. Original failures remain in
the history; no full-suite pass or universal numerical guarantee is asserted.

Corpus manifest SHA-256:
`57e8f47b47f79dee03ed97980aa66c9c93a274f9894c0f36e1bc8e122ef22427`.
Content SHA-256:
`ba775fc6f5eed1ea729e104ab678c6d877faed16c6e8f8a538e5538371a98048`.

Publish-016 and restore-015 verify 25 files / 2,476,074 bytes. Inspection-015
validates the restored examples. Schedule-016 and restored-schedule-014 match
byte for byte: seed 7401, one epoch, 11 planned updates, 71,444 supervised tokens,
zero target overshoot, and a 9,216-supervised-token update cap. These are planned
exposures, not executed optimizer updates or new unique data. Denial-014 confirms
`Quarantine corpus cannot train`; all four admission gates remain null.

Evidence: `training-corpus-selection-014`, `training-corpus-assembly-015`,
`training-corpus-publish-016`, `training-corpus-restore-015`,
`training-corpus-inspection-015`, and `corpus015-integration-check-001` under
`evidence/data`. Earlier Corpus 014 entries above describe the previous assembly.

Next: finish archival of the runtime evidence, expand diverse qualified supply,
and resolve attribution, repository identity and admission. The corpus remains
far below the planned training scale. GPU memory fit and learned coding gains
remain unproven. Keep the Pod stopped during this local work.


## Optuna 3545: isolated runtime qualification

The digest-pinned source image matches base
`f00abac7d53bb29e53e7c8bd13e9b4be9e0f9d44`. Its original Git history exposes
19,230 commits. Snapshot verification preserves all 402 tracked files, leaves
one parentless commit, and confirms that the base and PR-head objects plus
listed oracle paths are inaccessible in the mounted filesystem. Inherited image
layers are not audited.

Paired controls execute the full GridSampler test file with the publisher test
patch: baseline 8/9 pass; reference and teacher candidate 9/9 pass, with zero
candidate/reference outcome disagreements. Import origin is the task checkout;
tests leave the tracked patch unchanged; all three containers are removed.
The teacher changes unsupported-value rejection into UserWarning and differs
from the reference in warning type-name formatting. The nine tests do not
establish universal semantic equivalence.

The static action audit accepts 27 source actions and holds source indices
14, 18, 26, 30 and 32: standalone find/grep forms outside the reviewed adapter.
No command is silently skipped or repaired. Native replay, token measurement,
observation review, admission and corpus integration remain pending. Corpus 015
is unchanged. Evidence prefixes: `optuna3545-base-probe-001`,
`optuna3545-snapshot-build-001`, `optuna3545-snapshot-verify-001`,
`optuna3545-controls-001`, and `optuna3545-action-audit-001`.

Next: implement and test faithful, bounded adaptation of these search forms,
then replay against the isolated runtime. The Pod remains stopped.


## Reviewed standalone searches and first Optuna native replay

The source adapter now supports bounded quoted grep phrases, BRE alternation
with context, recursive grep on a source file, find/name with a grep/head
pipeline, and find/name with grep execution. Only the captured repository path
changes; pattern bytes, quoting, options, pipes and escaped terminators remain
unchanged. Unknown forms continue to reject. This compatibility grammar is not
a general shell security boundary; replay remains offline and disposable.

Actual shell parity tests cover matching and nonmatching fixtures, exit codes,
stdout/stderr, timeout metadata and unsafe extensions/paths. The full regression
suite reports **394 tests: 361 passed, 33 skipped, zero failures**. Evidence:
`evidence/p1/source-search-regression-001`. The previous adapter is retained at
`artifacts/official/source-replay-before-search-001/scripts/replay_source_teacher.py`.

`optuna3545-native-replay-001` completes 29 charged calls plus submission and
verifies container cleanup. Its 809-byte source-only patch changes rejection to
UserWarning. The trace retains source errors at 32 (grep no match) and 46 (the
original test still expects ValueError). The independent publisher controls
already verify corrected expectations; do not call the native old test a pass.

`optuna3545-native-history-001` and `optuna3545-tokens-001` measure **18,723 input /
4,509 supervised tokens** without truncation. These are candidate tokens, not
Corpus 015 additions. Next: review source observations and add explicitly
attributed assertions where printed checks are insufficient, then verify patch
alignment and decide quarantine assembly. No training admission or GPU fit is
established; the Pod remains stopped.
