# Full-checkpoint GPU qualification

Status: the full-checkpoint worker and supervisor are implemented, and one
synthetic update/export/fresh-reload qualification passed on the H100. P1 and
long-run training acceptance remain open. Earlier preparation notes below are
historical; the latest measured result is recorded at the end. No GPU execution
is authorized merely by this document or profile. Use the user's applicable
session deadline; never restart a user-stopped Pod automatically.

## Runtime and inputs

Keep the qualified 250-package serving lock unchanged. The measured run added
only the hash-pinned PEFT 0.21.2 supplement, without dependencies, to the existing
qualified environment. All 251 package versions and dependency consistency were
then checked. This was not a separate isolated training environment; the base
lock remains unchanged, and the added package is recorded in the supplement.

Use the exact eight-file checkpoint manifest, native tokenizer/template,
and one explicitly synthetic short qualification conversation. This is a
mechanics test, not useful post-training or one of the three 50M-token runs.
Do not include evaluator reference patches or test outcomes in model input.
Keep the base checkpoint read-only and save adapters separately on the volume.

The [planned profile](../configs/p1-training-pilot.json) uses one sequence of
at most 64 tokens, one update, rank 4 on the 410 already qualified text
projections, and non-reentrant activation checkpointing. These small values
bound a compatibility test; they are not final training hyperparameters.
Do not run the vLLM service concurrently on the same GPU.

## Required execution order

1. Verify the immutable code/model/data manifests and Python/package versions.
   Check the expected CUDA device, available memory and volume mount. Refuse
   a busy GPU or an expired session. Record device and host-memory observations.
2. Start an external supervisor before importing the training worker. Its
   deadline is the earlier of the approved session deadline and 900 seconds.
   On timeout, terminate the entire owned worker process group, then kill it
   after a short grace period if necessary. A Python signal timer alone cannot
   guarantee interruption of a native CUDA operation. This does not stop Pod
   billing; retain that distinction in the final report.
3. Load Gemma4ForConditionalGeneration with explicit BF16 decompression,
   eager attention, offline files only, and no CPU/disk offload hidden from
   the measurements. Reset and record CUDA peak allocation/reservation through
   load, forward, backward, update and reload stages. Sample device-wide use
   separately; allocator counters do not represent all device memory.
4. Bind adapters to the exact text-projection names/shapes. Require the rank-4
   count of 30,607,360 trainable parameters. Freeze all base parameters and
   verify that only adapter tensors enter the optimizer. Record trainable
   dtypes rather than assuming PEFT keeps them in BF16.
5. Compute native assistant labels using the qualified mask implementation;
   record exact supervised next-token count. Check finite loss/gradients,
   nonzero learning signal and a real parameter update. Verify frozen-base
   contents before and after, using bounded chunks rather than cloning the
   full model in GPU memory. Empty or nonfinite gradients are failures.
6. Save adapter configuration/tensors and optimizer state with a manifest.
   Release the first model and optimizer completely before reloading the base.
   Verify that the saved adapter loads, has the same tensor identities/shapes,
   reproduces outputs within a predeclared numerical tolerance, and differs
   measurably from the disabled adapter. Record actual errors, not only a pass.
7. Retain failures and partial measurements. Publish completed evidence to R2
   with readback verification, then stop the worker and confirm GPU-process
   cleanup. Failed or timed-out runs must not generate a success receipt.

## Acceptance boundaries

Require successful full-checkpoint execution and measured memory headroom
before increasing sequence length or the number of updates. A 70 GiB free-memory
preflight threshold is only an admission check, not a fit guarantee. The
60.88 GiB dense-weight calculation excludes working memory and transient peaks.

Adapter export to PEFT does not qualify vLLM adapter execution or competition
submission compatibility. Those require their own loader checks. Stochastic
resume, distributed accumulation, packed attention, and a licensed/split-audited
training corpus also remain open. No success on this test approves a long
training streak, demonstrates repair improvement, or establishes universal
correctness.

## Supervisor evidence

[Implementation](../zenithsync/process_supervisor.py) launches an owned POSIX
process group, checks monotonic and absolute deadlines, handles a stop file,
and translates supervisor SIGINT/SIGTERM into cleanup. TERM is followed by
KILL when needed. Cleanup time is reserved before the session deadline;
insufficient allowance is rejected before launch. A timed-out worker that
returns zero during cleanup remains a timeout. Unverified group disappearance
cannot produce a success result.

Seven real-process tests cover normal/nonzero exits, ignored termination,
expired deadline, insufficient cleanup allowance, inherited-child cleanup,
stop request and supervisor interruption/handler restoration. Linux evidence
uses a read-only minimal source mount with networking disabled. Logs and source
hashes are under `evidence/p1/process-supervisor-001`.

Limitations: trusted workers must not detach from the process group. Uninterruptible
kernel waits and external SIGKILL of the supervisor cannot be made safe by Python
cleanup logic alone. Returned process success is not artifact acceptance or a
claim that Pod billing stopped. Runpod execution remains unperformed here.

## Bounded frozen-state verification

`zenithsync/training_state.py` hashes parameters and persistent buffers in
bounded byte chunks, without cloning complete tensors. Exact state-name
exclusions identify adapters; unknown, duplicate, or all-state exclusions fail.
Shape, dtype, byte count and SHA-256 are compared along with tensor identities.
Unsupported noncontiguous, sparse, quantized and meta representations fail
explicitly. The caller must ensure no concurrent writes during hashing.

Six CPU tests exercise independent byte agreement, chunk boundaries, scalar
and empty buffers, base and buffer mutation, exclusion validation, metadata
changes and unsupported representations. The reduced compressed Gemma probe
also checks these fingerprints across its actual adapter optimizer update.
This validates CPU behavior only; CUDA memory bounds and full-model runtime
remain to be measured. Hash equality is an integrity check, not a proof of
training quality. Nonpersistent buffers are outside state-dict coverage.

## Shared qualification engine

`zenithsync/training_pilot.py` now implements the update/export/reload portion.
It targets exact escaped module names and checks every expected LoRA tensor,
shape-derived parameter count, finite gradients and updated weights, nonzero
adapter change and output effect, frozen state hashes, saved adapter identity,
fresh-base identity and output agreement. The first model lives inside a
separate function scope; garbage collection runs before the second base load.
The reduced probe confirms this lifetime boundary using weak references.

`scripts/probe_training_pilot_cpu.py` exercises it on the reduced compressed
Gemma fixture with independently specified projection shapes. CPU evidence
shows zero reload error with both tolerances set to zero. Failure tests ensure
invalid target shapes, no supervised labels and a modified reloaded base leave
no success receipt, and existing output directories cannot be overwritten.

This engine assumes a validated caller-supplied batch and checkpoint loader.
It is not yet the full CUDA command: native masking, checkpoint/runtime/storage
admission, CUDA memory instrumentation and supervisor wiring remain required.
Optimizer export is not evidence of successful optimizer resume.

## Full-checkpoint command implementation (not GPU-executed)

`scripts/run_p1_training.py` supervises `scripts/run_p1_training_worker.py`
with a required absolute approved session deadline, a 900-second worker cap,
process-group cleanup and a STOP file. Success requires both process cleanup
and matching worker/qualification receipts and artifact identities. Neither
command changes Pod billing state.

The worker requires Linux/Python 3.12, pinned core training dependencies, an
independently supplied manifest hash, full checkpoint file verification,
exact 410-projection coverage, one visible GPU, no other reported compute
clients, and at least 70 GiB free device memory. Both model and output paths
must resolve onto the required mounted filesystem; path-prefix appearances
and escaping symlinks do not suffice. This mount check establishes filesystem
placement; the control-plane volume ID must still be checked separately.

The shared native fixture has 24 tokens and five supervised next-token targets,
verified using the actual pinned tokenizer. It is a minimal update diagnostic,
not training data or a measure of coding capability. The worker records
PyTorch allocator peaks, which exclude external driver allocations. Device-wide
sampling and source-bundle checks are implemented below; actual full CUDA
execution remains outstanding. CLI help and three storage-admission unit tests pass locally;
mocked filesystem tests do not establish a real Runpod mount.

Required invocation arguments are model path, trusted model-manifest path and
SHA-256, fresh output directory, volume root (default `/workspace`), and the
approved session deadline. Do not infer a new deadline from this document.

## Device-wide telemetry and source deployment

`zenithsync/gpu_memory.py` samples UUID, used memory and total memory through
bounded `nvidia-smi` queries. Initial, periodic and final samples are flushed
to persistent JSONL. Missing or invalid readings, identity/capacity changes,
reader failure and unsuccessful monitor shutdown prevent a successful worker
receipt. A worker exception retains priority over a secondary telemetry error.
Six tests include actual background-thread failure propagation.

These sampled maxima are lower bounds on true continuous peaks and include
other clients and driver allocations. All GPUs visible to `nvidia-smi` are
recorded, which may differ from Torch's visibility filter. GPU admission still
checks for competing compute clients separately; that check is not a lock.

`scripts/prepare_training_deployment.py` stages an explicit 19-file source,
lockfile, model-manifest and documentation bundle. It verifies copied bytes
and runs both CLI imports in isolated Python mode outside the repository.
The first bundle also passed both CLI import/help checks in a local Linux
container with network disabled and a read-only source mount. These checks
do not import the full training runtime or execute CUDA.

## First full-checkpoint attempt

The H100 environment passed 251 pinned package-version checks and dependency
validation after installing the verified PEFT wheel without dependencies.
The actual network-volume mount and idle GPU were checked. The full checkpoint
loaded and decompressed, but prolonged high CPU activity and low GPU use
prevented completing qualification before an operator-requested stop.
The default Torch intra-op and inter-op thread counts were both 104.
Oversubscription is a hypothesis, not a proven diagnosis of the exact stalled
stage, because this version lacked stage logs.

The supervisor recorded `stop_requested`, exit -15, no remaining process group,
and no KILL escalation after 278.84 seconds. A subsequent GPU query showed
zero MiB used. This is a failed/incomplete attempt, not training acceptance.
Evidence is retained under `evidence/p1/full-training-gpu-001`.

The next version caps intra-op threads at four and inter-op threads at one,
sets matching OMP/MKL limits, and emits flushed monotonic stage timestamps.
Its reduced-model regression probe passes; full-model outcome remains open.

## Successful full-checkpoint qualification

The revised H100 run completed in 216.195 seconds, with clean process-group
exit and zero GPU memory used in the follow-up query. It attached exactly
30,607,360 rank-four LoRA parameters, performed one update on a native-tokenized
24-token fixture with five supervised targets, and verified finite loss,
gradients and updated adapter parameters. Frozen parameters and persistent
buffers retained identical fingerprints. Freshly loaded base and adapter state
matched, and maximum reload logit error was exactly zero with zero tolerances.

Memory observations: 60.919 GiB peak Torch allocation, 71.961 GiB peak Torch
reservation, and 72.632 GiB maximum sampled device-wide use across 187 samples.
Sampling can miss transient peaks; these figures do not establish longer-context
or larger-batch capacity. The adapter changed logits by up to 1.509765625 relative
to the disabled adapter. No quality improvement is inferred from that change
or the single pre-update loss of 6.874505519866943.

The supervisor, worker, native fixture, state fingerprints, stage logs and
memory trace are retained under `evidence/p1/full-training-gpu-002`. The complete
368,793,146-byte result, including adapter and optimizer files, is retained in
`artifacts/official/p1-full-training-gpu-002` and verified against the remote
manifest after download. R2 publication has a separate receipt under
`evidence/p1/full-training-gpu-publish-002`; consult it before claiming backup.

Still unqualified: full-model optimizer resume, multi-step numerical stability,
long contexts, realistic batches, corpus readiness, coding gains, vLLM adapter
execution and competition target hardware. A synthetic update is not one of
the proposed 50M-token training candidates.

## Optimizer checkpoint audit and resume contract

The original H100 optimizer export contains 820 state entries covering
30,607,360 parameters. An offline audit verified finite moments, nonnegative
second moments, and step counter one. At the first update from zero moments,
`m=(1-beta1)g` and `v=(1-beta2)g²`; eliminating `g` gives
`v=m²(1-beta2)/(1-beta1)²`. All entries satisfy this relation under the declared
stored-dtype numerical tolerance. Maximum absolute residual was
5.542805548309354e-11. This is a consistency check, not proof of arbitrary
optimizer correctness. Evidence: `evidence/p1/exported-optimizer-audit-002`.

That original export lacks parameter names. Do not infer name binding from
matching shapes or claim it establishes safe full-model optimizer resume.
New exports use `zenithsync/optimizer_checkpoint.py`, which binds exact ordered
names, shapes and dtypes to states and completed steps. Restore rejects identity,
coverage, moment and hyperparameter mismatches before loading state. The current
worker captures this validated format; its change is CPU-tested, not yet rerun
on the full H100 model. The prior GPU source bundle remains immutable.

Five contract tests include bitwise equality of a resumed versus continuous
next update and moments, and rejection of same-shaped reordered parameters,
corrupted moments/counters, missing state and hyperparameter drift. The reduced
Gemma qualification passes with the new export. RNG, scheduler and data-cursor
recovery, stochastic training and full-checkpoint resume remain separate gates.
