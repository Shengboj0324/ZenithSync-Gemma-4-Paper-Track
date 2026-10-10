# Training corpus integration

Status: quarantine assembly and CPU integrity loader implemented. Full corpus
optimization and GPU memory qualification remain incomplete. Deterministic update
scheduling and a CPU-tested token-weighted optimizer primitive are implemented.
Updated 2026-10-09.

## Portable corpus contract

`assemble_training_corpus.py` accepts an explicit JSON selection of token
candidate directories, example/task identifiers, repository/duplicate families,
and intended splits. It copies only the token candidate and tokenizer audit,
checks source stability and produces `corpus.json`. Assembly always emits
`status: quarantine` with unresolved admission gates. It never upgrades a replay
because its tests passed or because its token arrays are valid.

`zenithsync.training_corpus.load_corpus` requires an independently supplied
manifest SHA-256 and explicit aggregate byte/example ceilings. It checks file
identities before/after decoding, canonical relative paths, symlinks, token-audit
lineage, tokenizer asset identities, vocabulary/padding consistency, integer
bounds, array hashes, label alignment and exact supervised counts. It rejects
silent truncation, duplicate example IDs, aliased example files, exact duplicate
token sequences and declared cross-split repository/issue/duplicate families.
Repository grouping is case-normalized. These checks do not find unknown
semantic duplicates or verify that a human-supplied grouping is truthful.

For example i, the number of trainable next-token targets is

    n_i = sum_{t=1}^{L_i-1} 1[labels_i[t] != -100].

Position zero has no predecessor and must be ignored. All other labels must be
either the corresponding input token or -100. The corpus supervised count is
exactly sum_i n_i. Input-token totals, supervised-target totals, unique tasks and
returned example counts are reported separately. Corpus inspection does not
establish loss or gradient correctness for a future training loop.

The materializing `load_corpus` API retains validated token arrays. The new
`IndexedCorpus` API instead validates every example and all split/admission
invariants before exposing an index; it retains metadata and file references,
then rehashes token files when fetching individual examples. Its memory scales
with manifest metadata plus the largest decoded example, rather than total token
arrays. Manifest size (16 MiB), example count, aggregate bytes and per-file bytes
(16 MiB default) are explicitly bounded. JSON decoding and collation still
create multiple representations of an individual example; the byte limit is
not a bound on process RSS. Callers must also bound prefetched batches.

The scheduling CLI now uses the indexed API. No tensor packing, sequence
concatenation or task truncation is performed. This remains a local-file reader;
large-corpus throughput and direct remote/sharded streaming are unqualified.

## Admission boundary

Training-purpose loads reject quarantine manifests. An admitted manifest must
carry separate passed rights/attribution, split-isolation and runtime-qualification
receipts, each bound to the exact content identity and nonempty hash-verified
JSON evidence. Content identity covers examples, tokenizer assets and maximum
length, so changing corpus content invalidates earlier receipts. Receipt hashes
provide consistency, not cryptographic authenticity or proof that a review was
correct. No actual passed admission receipts have been generated for Nodebook.

All splits are validated before a training-purpose load returns only `train`
examples; development/confirmation examples must not enter optimization. The
existing split validator checks declared families; corpus-wide duplicate
research, lineage coverage and a frozen split still need to be completed.

`inspect_training_corpus.py` performs the same checks without importing Torch,
starting a model or allocating a GPU. It is included in the deployment source
bundle and its CLI import is tested in an isolated directory. A successful
inspection cannot restart a Pod or authorize an optimizer update.

## Actual candidate and verification

`artifacts/data/quarantine/training-corpus-001` contains Nodebook trajectory
`cdd22e5e-c7cd-4a5f-aab8-2afb2064d0df`, one task with 17,353 input tokens and
4,183 supervised targets. Its tokenizer audit and candidate arrays are preserved
byte-for-byte. Corpus manifest SHA-256:
`ff26b101c917debb85a0eba7a25be1d9aad007137dedea583a0a5d369821f285`.
Content SHA-256:
`fac42e4b7ac4919b4453e43191b670e2fa0daffce1936322db24d4433829558c`.
The intended train label is a draft allocation, not a frozen or approved split.

Eight focused loader tests cover valid quarantine loading, denied training,
missing and content-mismatched receipts, symlinks/path escape, tampering, count
mismatches, byte ceilings, repeated IDs and case-varied repository overlap.
Synthetic passed receipts in one unit test exercise structure only; they are
not dataset approvals. Full local suite: 234 tests, 212 passed, 22 skipped.

The existing full-checkpoint GPU worker still performs its synthetic one-update
qualification. Remaining work includes integration of indexed fetching,
batch scheduling and supervised-token-weighted accumulation, actual corpus
optimizer steps/checkpoint resume, data admission completion, and long-sequence
GPU validation. Do not launch a training campaign on the strength of this loader.

## Indexed loading verification

Four added tests cover equality to materialized loading, absence of retained
token arrays, defensive metadata copies, changed token/manifest rejection,
training-admission enforcement, per-file byte ceilings and audit validation
before the index becomes available. All twelve corpus tests pass. The latest
repository suite ran 247 tests: 220 passed and 27 skipped.

The actual quarantined Nodebook corpus was read by both APIs. Every fetched token
and label array agreed exactly. The new indexed CLI produced byte-identical
schedule and update files to the preceding materialized CLI. Evidence is in
`evidence/data/training-corpus-indexed-schedule-001/equivalence.json`.
No training occurred. Admission receipts describe a snapshot validated at index
construction; this reader is not a live revocation service. It assumes an owned,
quiescent corpus directory, and detects changed token bytes at fetch time.

## Update scheduling and objective

`training_schedule.py` orders examples deterministically by a seeded per-epoch
hash. It preserves complete examples, caps supervised targets per update and
requires an explicit epoch allowance. Repeated epochs count as repeated
exposures, not additional unique data. The last example may exceed the overall
target; the overshoot is strictly less than the largest example's target count.
The planner never truncates a trajectory to hit an arbitrary exact total.

A resume cursor binds the schedule identity, completed update count, cumulative
input/target counts and a hash of the consumed update history. Resume regenerates
that history and rejects mismatches. This verifies the data cursor, not the
model/optimizer/RNG checkpoint by itself. Four scheduler tests verify coverage,
limits, every update-boundary resume, and corruption rejection.

For microbatch j containing n_j supervised next-token targets, let L_j be its
mean causal cross-entropy. `corpus_optimization.token_weighted_step` differentiates

    L = sum_j (n_j / sum_k n_k) L_j.

This is the per-target mean over an update. Averaging microbatch means without
these weights would overweight short or sparsely supervised examples. Each
microbatch uses separate attention; examples are not concatenated. The helper
requires the backend loss to have precisely this normalization and no auxiliary
loss. Equivalence to a single padded batch also requires consistent model
behavior (for example, no differing dropout draws or batch-coupled layers).

Four CPU numerical tests passed: unequal-target full/split losses, gradients and
AdamW moments agree to 1e-12 in a float64 toy model; invalid padding and nonfinite
loss cannot initiate an update; saved optimizer plus data-cursor resume matches
uninterrupted deterministic execution bit-for-bit. These are local numerical
tests, not full-model GPU or stochastic-resume evidence. An optimizer exception
can occur after mutation: callers must discard that state and restore a complete
checkpoint. No rollback guarantee is made.

The actual quarantined Nodebook corpus has a dry schedule at
`evidence/data/training-corpus-schedule-001`: one epoch, one update, 17,353 input
tokens and 4,183 supervised targets. No optimizer update on that candidate has
been authorized or performed. Long-sequence memory, bounded batch integration,
RNG checkpointing, and full worker integration remain outstanding.

The reduced Gemma4ForCausalLM backend test also passed in an isolated CPU
environment (Torch 2.14.1, Transformers 5.13.1). It independently recomputes
causal cross-entropy from logits and compares padded-batch versus 4:1-target
microbatch loss, gradients, updated parameters and AdamW moments. Loss agreement
is checked to six decimal places; tensor comparisons use rtol=2e-5, atol=2e-7,
because the backend computes cross-entropy in float32 even for float64 weights.
This exercises sliding and full attention, right padding and masked prompts.
It does not establish 31B, BF16, LoRA or GPU equivalence.

Before indexed loading, the repository suite ran 243 tests: 216 passed and 27 skipped. Eight focused
scheduler/optimizer tests and the separate reduced-Gemma test passed in the
explicit CPU runtime. The deployment bundle now includes the schedule CLI and
optimizer primitive; four isolated CLI imports passed. Numerical test logs are
retained under `evidence/p1/corpus-optimization-001`.

## Streamed corpus update integration

`corpus_training.train_corpus_update` now bridges an admitted training-purpose
`IndexedCorpus` to the optimizer. It checks every scheduled example against the
index, rejects duplicate IDs, non-training splits, wrong counts and sequences
exceeding the caller's capacity, then fetches and transfers one complete example
at a time. It does not silently truncate or concatenate examples. The caller must
bind the update to the verified schedule and publish the completed cursor only
after checkpoint success; the bridge is not yet the complete training worker.

`streamed_token_weighted_step` uses the declared supervised-target total for
normalization, checks the actual total, and delays `optimizer.step()` until the
stream has ended successfully. An overrun, underrun or late read failure clears
accumulated gradients and prevents a step. Forward passes may mutate buffers or
consume RNG, so callers must restore complete state after a failed update.
Post-step failures may have mutated optimizer state. No automatic rollback is
claimed. No mixed precision scaler, distributed training or LR schedule is added.

Tests cover a complete indexed synthetic-admission update matching the eager
update, changed-file/count/capacity rejection, late-stream failures, and weak
references proving that the previous microbatch tensors are released before the
next batch is requested. Twenty-four focused tests passed including the reduced
Gemma backend; a subsequently added tensor-lifetime test passed with all four
stream integration tests. The full suite at that point ran 250 tests: 220 passed,
30 skipped. Evidence is retained in `evidence/p1/streamed-corpus-001`.

The one-example approach bounds batch tensor residency but does not establish
that a single long Gemma trajectory fits GPU memory. Checkpoint/RNG integration,
31B BF16/LoRA numerical and memory qualification, admitted data expansion and
held-out repair gains remain required. No real-corpus training occurred.

## Random-state recovery

`training_rng.py` captures Python global randomness, NumPy's legacy global
generator and Torch CPU/global CUDA generators. It records Python, NumPy and
Torch versions, initialized CUDA device names, deterministic-algorithm flags,
cuDNN settings and float32 matmul precision. Restore rejects runtime mismatch
and validates each state with a private generator before changing global state.
The payload round-trips through `torch.load(weights_only=True)`.

The CPU dropout test saves model, AdamW, cursor and RNG after the second update,
reconstructs the model and optimizer, restores RNG last, and finishes the same
schedule. Remaining losses, final weights and AdamW moments agree bit-for-bit
with uninterrupted training. Other tests verify all three CPU random streams
and rejection of invalid Torch state without partially resetting Python/NumPy.
Eleven focused RNG/stream/optimizer tests pass; the deployment bundle includes
the RNG helper and all four CLI import checks pass.

Scope: quiescent single-process training using the captured global generators.
Custom generators, NumPy `Generator` objects, data-loader workers and MPS are not
covered. CUDA capture/restore is implemented but not tested on GPU. Equal runtime
metadata is necessary, not sufficient, for cross-device or cross-version
reproducibility. GPU nondeterministic operations can still prevent exact resume.
Atomic checkpoint publication and full worker wiring remain outstanding; the
in-memory test is not evidence of durable checkpoint recovery after process loss.

## Durable checkpoint storage

`checkpoint_storage.py` now writes checkpoints to a temporary file in an owned
POSIX directory with an enforced serialized-byte limit, flushes/fsyncs the file,
publishes via a no-overwrite hard link, and fsyncs the directory. Readers require
an independently supplied SHA-256 and byte count, reject symlinks/nonregular
files, and hash and deserialize through the same descriptor with
`weights_only=True` and CPU mapping. Incomplete writes do not publish the final
name; a post-publication fsync failure may leave a complete artifact and still
raise. Caller recovery must inspect rather than overwrite that artifact.

A separate Python process loaded a checkpoint containing synthetic model,
AdamW and RNG state and reproduced the next dropout update exactly: loss,
parameters and optimizer tensors. Tests also cover over-budget serialization,
injected write failure, truncation, same-size tampering, overwrite attempts,
FIFOs and symlinks. Fifteen focused storage/RNG/stream/optimizer tests pass. The
preceding repository suite ran 257 tests: 220 passed and 37 skipped; the FIFO
test was added afterward and passed in the focused run. Four staged CLI imports
pass. Evidence: `evidence/p1/checkpoint-storage-001`.

This is a storage primitive, not yet the complete adapter checkpoint contract.
It does not by itself bind frozen base weights, schedule/cursor, corpus admission
or worker configuration. Serialized size is not a hostile-deserialization memory
limit. Files are trusted local training artifacts in quiescent owned directories.
Actual power-loss durability and filesystem behavior on the Runpod network volume
remain untested. No full-model tensors or real training data were updated here.

## Bound adapter checkpoint contract

`adapter_checkpoint.py` now joins the existing primitives. A payload contains
only trainable parameter tensors (CPU copies), AdamW state, RNG state, verified
data cursor, frozen-state fingerprints, per-module training/evaluation modes,
and exact base-manifest/corpus-manifest/corpus-content/schedule/worker-config
hash bindings. The external schedule is replayed through the consumed prefix;
optimizer step counts must match the cursor. Training aliases and a model with
no separate persistent frozen state are rejected.

Capture checks that frozen state still matches the independently recorded base
fingerprints. Restore validates all bindings, module modes, frozen bytes,
parameter names/shapes/dtypes/finiteness, optimizer ownership/hyperparameters,
cursor and RNG before applying adapter tensors. Optimizer state follows, then
RNG last. A failure during application (for example a device allocation failure)
requires discarding the partially changed instance. Validation rejects mismatch
before mutation; this is not an automatic rollback mechanism.

The CPU disk-roundtrip test restores adapter/optimizer/RNG/cursor together and
reproduces the remaining dropout schedule exactly. Negative tests cover changed
base/config/module mode, corrupted cursor, optimizer step/hyperparameter drift,
invalid RNG and nonfinite adapter tensors. Capture clones are independent of
later training. Eighteen focused contract/RNG/storage/stream/optimizer tests pass;
the repository suite ran 261 tests (220 passed, 41 skipped), and four deployment
CLI imports passed. Evidence: `evidence/p1/adapter-contract-001`.

The worker must independently verify the artifacts identified by these hashes;
hash strings are not authorization or proof of provenance. Nonpersistent buffers
must be deterministically reconstructed by the worker. The current fingerprint
check scans frozen state at capture/restore: memory is chunk-bounded, but full
31B scan latency has not been qualified. Actual PEFT/full-model GPU restore and
the complete training worker remain unverified. No real-data update occurred.

## Budgeted corpus training session

`training_session.run_training_session` integrates indexed admitted data,
deterministic updates, streamed token-weighted training, adapter checkpoints and
resume. It verifies corpus/schedule bindings and exact training-example coverage,
checks sequence capacity, and reserves the full per-checkpoint byte cap before
executing an update. Every successful update is checkpointed; only successful
publication advances the returned committed cursor. Checkpoints are explicitly
identified by path and hash on resume; no directory scan guesses the latest one.

The caller sets update, elapsed-time, sequence, individual-checkpoint and total
checkpoint-byte limits. Elapsed time is checked between updates, not during a
forward/backward pass or filesystem write: a hard deadline supervisor remains
mandatory on Runpod. Directory reuse and symlink ancestry are rejected. On any
update/publication error the caller must discard mutable model/optimizer state;
earlier checkpoint files remain recoverable. Session metadata is returned to the
caller and still needs durable worker-level reporting.

Five synthetic-admission integration tests verify full versus interrupted/resumed
training, preserved prior checkpoint after a simulated write failure, rejected
artifact/capacity mismatch before training, checkpoint-space reservation, and
elapsed-time refusal before the first update. Twenty-three focused training and
checkpoint tests pass. Full suite: 266 tests, 220 passed, 46 skipped. Four staged
CLI imports pass. Evidence: `evidence/p1/training-session-001`.

This is the reusable training loop; the existing full-model worker still runs its
one-update qualification fixture. Gemma loading, PEFT configuration, runtime and
volume checks, session reporting, the external supervisor and real data admission
must still be connected to this loop. Checkpoint-every-update and full frozen
fingerprinting prioritize validation but their 31B throughput is not established.

## Full-model worker wiring

The new `scripts/run_corpus_training.py` supervisor launches
`scripts/run_corpus_training_worker.py` with an absolute timezone-aware deadline,
process-group cleanup and a STOP-file path. It verifies the worker receipt and
every committed checkpoint file identity. The supervisor's configured wall cap
includes worker setup and model loading; the loop's separate clock starts later.
Deadline termination can preserve earlier checkpoint files without producing a
successful session receipt. Neither script changes Pod billing state.

CPU preflight validates exact config/schedule identities, positive resource
limits, complete schedule coverage, admission and sequence capacity. Before
model loading the worker verifies model files, tokenizer asset agreement,
410-projection/30,607,360-LoRA-parameter accounting, pinned Linux runtime,
persistent mount placement, resume-file identity and exclusive GPU availability.
It then loads the local compressed-tensors checkpoint decompressed to BF16,
attaches exact-shape rank-4/alpha-8 LoRA, enables non-reentrant gradient
checkpointing, records frozen state and invokes the budgeted training session.
Resume binds the settings, implementation file identities and runtime versions
through the execution-config digest. Final reports include memory measurements
and checkpoint identities; they do not establish repair quality.

`configs/p1-corpus-qualification.json` is a proposed one-update, 900-second
qualification configuration, not an approved training campaign or a GPU-fit
claim. The 32,768-token ceiling prevents truncation but does not prove that a
sequence of that length fits the H100. A real quarantined Nodebook preflight was
correctly denied before model loading (`evidence/p1/corpus-worker-001`).

Four CPU preflight tests pass. The reduced real Gemma + PEFT test passes exact
adapter attachment, update, bound restore and identical subsequent update using
the new attachment helper. Fourteen focused tests pass; the repository suite
ran 271 tests (224 passed, 47 skipped). Six staged CLI imports pass. The full
31B/BF16/GPU worker and supervisor path is implemented but has not been executed;
volume behavior, large-sequence memory, throughput and full-model resume still
require qualification. Data admission and corpus expansion are still required.

## Independent session-report reconciliation

`session_report.py` now replays the scheduled update prefix independently of the
worker report. It checks exact checkpoint order/names, cursor progression,
supervised-target/microbatch counts, finite nonnegative loss, file identities,
checkpoint byte reservations and final byte totals. It loads each hash-bound
checkpoint and compares its stored artifact bindings, cursor and optimizer step
to the report. The claimed completion or budget stop must follow from the
remaining schedule and configured limits. These checks detect inconsistent
evidence; they do not independently recompute loss or establish repair quality.

The supervisor computes execution bindings before launching the worker, rejects
incompatible resume bindings early and compares the returned execution identity.
The resume cursor comes from the supplied hash-bound checkpoint, not a worker
claim. After successful process cleanup, report reconciliation is required before
the supervisor writes an acceptance receipt. A zero process exit alone is
insufficient.

Five report tests cover complete/resumed schedules, false stop reasons, count
and byte corruption, Boolean-as-integer cursor changes, altered files, wrong
paths and payload/report disagreement. The actual synthetic-admission session's
three Torch checkpoint files also pass the independent verifier. Thirteen focused
tests pass. Full suite: 276 tests, 229 passed, 47 skipped. Six staged CLI imports
pass. Evidence: `evidence/p1/session-report-001`. No GPU or real-data training was
performed. Full worker/GPU lifecycle and corpus admission remain outstanding.


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

## Corpus 010: dbt–Snowflake integration

Selection 009 adds the mechanically qualified dbt–Snowflake 716 replay to the
quarantine assembly. The seven examples total 115,534 input tokens and 39,154
supervised tokens. Manifest SHA-256:
`84a7251b4bfbb0d2b0f9fbf90ca777442f7a3fa3e6f2ffd559e8b947ae696998`.
All four admission gates remain null. Training denial 009 confirms that the
real seven-example bundle cannot start training.

Publication 011 and restore 010 verify all 15 files / 1,280,267 bytes. Restored
inspection 010 validates all seven records. Schedule 011, with seed 7401,
one epoch and an 8,192 supervised-token update ceiling, yields seven updates
and exactly 39,154 supervised tokens with zero target overshoot. Restored
schedule 009 reproduces the schedule and update bytes exactly. These are data
integration checks, not optimizer execution or full-model memory qualification.

Repository lineage review 005 resolves the seven projects and recorded aliases
against all four reserved repository identities with no known fork-network
overlap. Detached copies, semantic duplication and pretraining overlap remain
outside this check. Nineteen corpus-loader/scheduling regression tests pass.
No GPU was used; abundant data supply and all final admission gates remain open.

## Corpus 011: second PennyLane task, same repository split

Selection 010 adds PennyLane 5831, with 17,691 input / 6,993 supervised tokens,
to the existing quarantine candidates. Assembly 011 contains eight tasks across
seven repositories: 133,225 input / 46,147 supervised tokens. Both PennyLane tasks
remain in `train`; no extra repository diversity is inferred. Corpus manifest:
`1d71e5203b7c7110d9b5dae5b1e1436bfcac2ad2284a95c42ddb2ff5dab4644b`.

Publication 012 and restore 011 verify all 17 files / 1,479,218 bytes. Inspection
011 validates the restored corpus; original schedule 012 and restored schedule
010 produce identical schedule/update bytes. Seed 7401, one epoch and an
8,192-token supervised-update ceiling produce eight updates with zero target
overshoot. Training denial 010 confirms that the four null admission gates
prevent training. No optimizer or GPU execution is claimed.

`corpus011-composition-001` records exact rational token shares by declared
repository group: PennyLane contributes 30.62%. Inverse concentration
`1 / sum(p_r**2)` is about 5.604; this is a descriptive diversity measure, not
an effective sample size or proof that tasks are independent. Additional
repository coverage, final rights/split reviews and abundant data remain needed.

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


## Corpus 016: Optuna completion integration

The current quarantine assembly contains **13 tasks across 12 declared repository
groups, 243,213 input tokens and 77,114 supervised tokens**. The Optuna history
uses a completion-derived identity and explicitly attributes the added assertions.
Its final patch remains byte-identical to the original native submission and
produces the independently tested candidate source. Errors 32 and 46 remain
visible; the obsolete ValueError test is not relabeled as passing.

Actual package checks verify 12 supported values without warnings and 8
unsupported values with UserWarning. An in-memory study visits all six members
of `{1,2} × {-1,0,1}` once and attains the independently enumerated minimum of
`x²+y² = 1`. This is finite exhaustive coverage of that grid, not a proof of
persistent storage, distributed optimization or arbitrary Python types.
Four source-created scratch files are verified absent. The completed history
contains 20,767 input and 5,670 supervised tokens, without truncation.

Corpus manifest SHA-256:
`480acac8206c6b68355799ba1bfef71e87f89f9c2fa642c2659a3298050f3709`.
Content SHA-256:
`17d76bdaaa3dbfb2f7da81e454bf10b445aea3a416a0770a4b77368351e41de0`.
Publish-017 and restore-016 verify **27 files / 2,705,581 bytes**. Inspection-016
validates the restored corpus. Schedule-017 and restored-schedule-015 are
byte-identical: seed 7401, one epoch, 12 planned updates, 77,114 supervised tokens,
zero overshoot and a 9,216-target update cap. No optimizer update was executed.
Denial-015 retains `Quarantine corpus cannot train`; all admission gates are null.

Evidence: `optuna3545-observation-review-001`, `optuna3545-native-replay-002`,
`optuna3545-native-history-002`, `optuna3545-tokens-002`,
`training-corpus-selection-015`, `training-corpus-assembly-016` and
`corpus016-integration-check-001`, under `evidence/data`.
Earlier Corpus 015 entries describe the previous assembly.

Next: expand diverse qualified supply and resolve identity, attribution,
dependency notices and admission. These 77,114 targets do not supply the planned
50M-token candidates. Full-model GPU readiness and learned coding gains remain
unproven. The Pod stays stopped.


## Corpus 017: CloudEvents finite-relation completion integration

The current quarantine assembly contains **14 tasks across 13 declared repository
groups, 270,026 input tokens and 84,503 supervised tokens**. The CloudEvents
history explicitly attributes the added completion; the source-only patch is
unchanged and produces the independently tested candidate bytes. Source errors
16, 18 and 36 remain visible, including the failed offline installer.

The actual constructor creates 32 events with explicit IDs/timestamps across
both spec versions and a subclass without a comparison override. All 1,024
ordered pairs match independently assigned equivalence classes. Exhaustive
checking of 32,768 triples covers 512 true transitivity antecedents; 512 ordinary
non-event directional comparisons also pass. A foreign class override produces
asymmetric cross-type equality, explicitly refuting a universal symmetry claim.
The source's untested transitivity heading and nonexistent `__req__` terminology
are corrected in the separately attributed completion. These finite results do
not prove equality axioms for arbitrary payloads or overrides.

Completed history: **26,813 input / 7,389 supervised tokens**, no truncation,
39 charged calls plus submission, six scratch files verified absent.
Corpus manifest SHA-256:
`c56ec783fae55397de271abb64312ecc40513e2e586b4b51a1eb64f6baec9a36`.
Content SHA-256:
`495829aa7bdb97d64afdd994bac06d76978e7402e5e7fbd3201fce13d26de754`.
Publish-018 and restore-017 verify **29 files / 2,998,210 bytes**. Inspection-017
validates the restored corpus. Schedule-019 and restored-schedule-016 are
byte-identical: seed 7401, one epoch, 13 planned updates, 84,503 supervised tokens,
zero overshoot and a 9,216-target update cap. Failed schedule-018 is retained;
it stopped on source-file hydration metadata drift. No optimizer update ran.
Denial-016 preserves `Quarantine corpus cannot train`; all four gates remain null.

Evidence: `cloudevents172-observation-review-001`,
`cloudevents172-native-replay-002`, `cloudevents172-native-history-004`,
`cloudevents172-tokens-004`, `training-corpus-selection-016`,
`training-corpus-assembly-017`, and `corpus017-integration-check-001`.
Earlier Corpus 016 entries describe the previous assembly.

Next: expand diverse qualified supply and resolve identity, attribution,
dependency notices and admission. The corpus is still far below the planned
training scale; repeated exposure does not add unique evidence. Full-model GPU
readiness and learned coding gains remain unproven. Keep the Pod stopped.


### Corpus 018: fifteen-task quarantine integration

Added only the explicitly attributed Boltons compatibility derivative. Current
assembly: **15 examples, 15 tasks, 14 repository groups, 289,750 input tokens and
90,869 supervised tokens**. Manifest SHA-256:
`3c26a771de1a2d2f5a5f98b75d5a3cb6d5adcadb426754f89a6ca3a98f7f4109`.
Content SHA-256:
`cda219ef9998fe0b138c6cbe4f86b843b1daaea24f420a1e5597d8c69c17f01d`.
All four admission gates remain null; training-purpose loading explicitly rejects
with `Quarantine corpus cannot train`.

Published and restored 31 files / 3,216,759 bytes through R2. Restored token and
content identities match. Original and restored schedule/update files are
byte-identical: seed 7401, one epoch, 14 planned updates, 9,216 target-token update
cap, 90,869 targets and zero overshoot. This is a schedule, not optimizer execution.
Lineage audit 008 resolves all 14 declared repository groups, two historical
names and four reserved names, with no cross-boundary ID/network-root overlap.
Detached copies, semantic duplication and hidden evaluation independence remain
unproven; the Dynaconf mirror distinction remains explicit. No evaluation bodies
were read. Evidence binding: `corpus018-integration-check-001/report.json`.

The 3x50M processed-target-token campaigns are still not supplied by an abundant,
approved corpus. No training or GPU use occurred. Continue diverse qualification,
attribution and split review; keep the Pod stopped.
