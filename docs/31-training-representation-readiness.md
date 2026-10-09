# Training representation and memory readiness

Status: static and reduced-model checks are complete, and the full checkpoint
passed one synthetic CUDA LoRA update and fresh reload on the H100. This is
one-step compatibility evidence; long-run training and quality remain unqualified.

## What the pinned implementation does

The inspected Transformers 5.13.1 quantizer declares PEFT trainability and
supports decompression via `run_compressed=False`. Its compressed-tensors
0.15.0.1 dependency registers a model-level first-forward decompression hook.
Therefore packed on-disk size is not the steady-state training footprint of
this path. A trainability flag alone proves neither Gemma adapter attachment
nor useful gradients. The current main documentation describes newer loading
flags; do not copy them into our pinned runtime without version qualification.
[Official overview](https://huggingface.co/docs/transformers/main/quantization/compressed_tensors).
Exact inspected wheel and module hashes are recorded in
[the audit receipt](../evidence/p1/training-representation-001/receipt.json).

## Checkpoint-derived accounting

The audit validates the header against prior intake, checks all 410 original
projection shapes, and accounts for remaining BF16 tensors. Reconstructed dense
weights total **65,364,750,040 bytes (60.8757 GiB)**. This includes stored
unquantized components; it is not a measured CUDA allocation. Quantization
metadata retained by the loader, activations, temporary decompression buffers,
CUDA workspaces, and allocator overhead are additional. No full weight-payload
rehash was performed in this static audit.

For a projection of shape (output, input), standard LoRA adds
`r * (input + output)` parameters via A of shape (r, input) and B of shape
(output, r). The frozen base plus `(alpha/r) B A` defines the effective matrix.
No biases, DoRA parameters, or extra modules are included in these counts.

| Targets | Rank | Adapter parameters | FP32 weights + gradients + two Adam moments |
|---|---:|---:|---:|
| Attention projections | 16 | 45,015,040 | 720,240,640 bytes |
| All text projections | 16 | 122,429,440 | 1,958,871,040 bytes |
| Attention projections | 64 | 180,060,160 | 2,880,962,560 bytes |
| All text projections | 64 | 489,717,760 | 7,835,484,160 bytes |

The 16-byte state estimate assumes four FP32 arrays per trainable parameter;
it excludes implementation temporaries. BF16 weights and gradients with FP32
moments instead account for 12 bytes, without an additional master copy.
Neither scenario estimates activation memory or establishes H100 fit.

## Next executable qualification

1. In an isolated CPU environment, exercise the pinned quantizer on a small
   representative module: unpacking, frozen-base gradients, LoRA gradients,
   save/reload, and explicit nonzero adapter effect. A synthetic module result
   cannot qualify the 31B architecture.
2. Audit actual Gemma module names and shared key/value behavior before adapter
   attachment. Verify nonempty trainable tensors and exact parameter counts.
3. Prepare a bounded H100 experiment with the exact checkpoint, short sequences,
   batch size one, activation checkpointing, and explicitly frozen base weights.
   Do not run vLLM concurrently with the training model on the same GPU.
4. Measure peak device memory, finite masked loss and gradients, optimizer update,
   frozen-weight integrity, checkpoint resume, and adapter-only save/reload.
   Check target-loader attachment and adapter-enabled/disabled outputs separately.
5. Scale sequence length and batch size only from observed peaks. A successful
   tiny run does not approve any of the three 50M-token candidate budgets.

No alternate base model is authorized or required by this audit. Additional
weights are a fallback only if the exact-checkpoint path fails qualification.
Data must pass license, provenance, split, token-mask, and evaluator-separation
gates before training. Synthetic qualification inputs are not a training corpus.

## Synthetic CPU result

The [executed probe](../scripts/probe_adapter_cpu.py) tested a small 8-by-64
projection with W4 symmetric group-32 packing, BF16 scales and exactly
representable test weights. The released codec round-tripped these values
exactly. PEFT attached 288 rank-4 adapter parameters; FP64 gradients matched
independently evaluated matrix derivatives (maximum absolute difference
2.220446049250313e-16). Frozen base weights were bitwise unchanged and had no
gradients. The trained adapter changed outputs (maximum absolute effect
0.0441940493), and adapter-only save/reload reproduced outputs exactly.

For squared-error mean loss, `D = 2 (Y - T) / numel(Y)`; with scale `s`,
`grad_B = s D^T (X A^T)` and `grad_A = s (D B)^T X`. The first A gradient
is correctly zero when B starts at zero; the second update must produce
a nonzero A gradient. The probe checks both steps instead of incorrectly
requiring all gradients to be nonzero at initialization.

[Receipt](../evidence/p1/adapter-cpu-002/receipt.json). Runtime: CPU Torch
2.14.1, Transformers 5.13.1, compressed-tensors 0.15.0.1, PEFT 0.21.2.
This differs from the Torch 2.10.0 CUDA serving environment. The test explicitly
decompresses the synthetic projection before attaching PEFT; it does not
exercise full-model loader hooks, Gemma attention, BF16 backward, loss masking,
optimizer resume, or adapter loading in vLLM. No training corpus was used.

## Reduced Gemma architecture result

The [architecture probe](../scripts/probe_gemma_training_cpu.py) constructs a
random two-layer Gemma4 text model using the pinned implementation, with one
sliding-attention layer and one full-attention layer with shared key/value
projection behavior. All 13 intended attention/MLP projections receive LoRA;
actual trainable parameters match the dimension formula exactly (7,808).
Non-reentrant gradient checkpointing is enabled and the base stays frozen.

Four synthetic next-token targets contribute to the loss. The implementation's
loss matches an independent log-sum-exp calculation. Its logit gradients match
`(softmax(logits) - one_hot(target)) / active_target_count`; prompt, padding,
and final-position logits receive exactly zero direct loss gradient. Masking
the loss does not remove the prompt's role as context, nor its indirect effect
on later predictions. These are hand-constructed masks, not native Gemma chat
template/assistant-span qualification.

After one update, adapter weights and AdamW state are saved. A fresh model with
the same base state loads both, and its next update matches the uninterrupted
run: identical loss, bitwise-equal adapter tensors, and bitwise-equal optimizer
steps/moments. Base parameters remain unchanged with no accumulated gradients.
Dropout is zero; stochastic RNG and distributed resume are not tested.

[Final receipt](../evidence/p1/gemma-training-cpu-002/receipt.json): first loss
4.167759418487549; second and resumed losses 4.014125347137451. These tiny
synthetic losses are software checks, not a claim of useful model improvement.
CPU Torch 2.14.1/FP32 remains distinct from the full Gemma checkpoint,
multimodal wrapper, packed loader, CUDA/BF16, and production adapter loader.
Next qualify native conversation masks and the full-model loader path before
any long training run.

## Native template loss-mask qualification

The downloaded template lacks generation annotations and embeds tool responses
inside the assistant turn. The [mask implementation](../zenithsync/training_masks.py)
adds generation annotations only around reasoning/calls, assistant content, and
assistant terminal markers. It first validates history linkage and the trusted
template hash. Every call must preserve the native rendered string and exact
token IDs. Character offsets independently check that each supervised token
is wholly inside a generated span; boundary-crossing tokens are rejected, not
approximated. System/user text, tool schemas/results and model headers are
excluded. No truncation, padding or packing is performed.

[Actual-tokenizer evidence](../evidence/p1/training-masks-001/receipt.json) covers
four fixtures: Unicode text, multiple user/assistant turns, tool continuation,
and reasoning plus a tool call. The supervised decoded text must exactly match
an independently specified expected string. A tool result containing apparent
model-turn markers remains excluded from supervision. All-user examples,
orphaned tool results and an incorrect template hash are rejected.

This verifies the supported text/tool template layout on these fixtures, not
a general corpus acceptance claim. Multimodal examples, truncation, packing,
parallel-tool coverage and combining these masks with a full-checkpoint gradient
run remain unqualified. Any template update must be explicitly requalified.

## Native-token batching and accumulation

The [collator](../zenithsync/training_batch.py) preserves example boundaries and
right-pads them. Attention masks depend on sequence length, not token value,
so a real token equal to the padding ID remains visible. Added padding always
has ignored labels. Invalid IDs, mismatched or altered labels, empty target
sets, missing causal predecessors and over-length examples are rejected.
Inputs are copied rather than mutated; no silent truncation or sequence packing
is performed.

For examples with supervised counts n_i and mean losses L_i, the token-mean
objective is `L = sum(n_i L_i) / sum(n_i)`. A microbatch therefore contributes
`n_i / sum(n_i)` times its mean loss. Averaging microbatch means equally changes
the objective when target counts differ. With optimizer updates only after all
microbatches, this weighting should reproduce the full batch gradient, subject
to floating-point reduction differences and equivalent stochastic behavior.
Distributed scaling and nonzero dropout require separate qualification.

The [integrated CPU probe](../scripts/probe_native_training_batch.py) uses actual
Gemma token IDs, the full 262,144-token vocabulary, native tool-history masks,
and a random reduced Gemma model with LoRA. The examples contain 5 and 15
supervised targets. Full-batch loss is 12.5221042633 versus 12.5221023560 for
token-weighted microbatches; maximum adapter-gradient difference is
1.4901161193847656e-7. Altering only masked padding IDs leaves loss exactly
unchanged. See [receipt](../evidence/p1/native-training-batch-001/receipt.json).
All 92 local unit tests passed, including collator rejection and padding checks.
This is numerical integration evidence, not language-quality or training-fit
evidence. Cross-example packed attention, full-checkpoint loading, CUDA/BF16
and distributed accumulation remain unqualified.

## Compressed checkpoint loader qualification

The [loader probe](../scripts/probe_compressed_gemma_loader.py) now exercises
a saved, reduced Gemma BF16 checkpoint through the real Transformers
`from_pretrained` path with `CompressedTensorsConfig(run_compressed=False)`.
The checkpoint uses W4 symmetric group-32 packing for all 13 text projections.
Synthetic group scales are explicitly a test construction, not a calibration
recipe for the downloaded QAT checkpoint.

After loading, all packed projection parameters are decompressed. Every
loaded state tensor matches the independently retained in-memory decompressed
reference exactly. PEFT attaches 7,808 parameters across 26 adapter tensors;
masked loss and gradients are finite and at least one gradient is nonzero.
A real AdamW update leaves base weights unchanged with no base gradients.
The adapter changes output logits (maximum absolute difference 0.51171875),
and adapter save/reload on a freshly loaded compressed base reproduces logits
exactly. See [receipt](../evidence/p1/compressed-gemma-loader-001/receipt.json)
and retained runtime log.

This qualifies the reduced BF16 CPU text-model loader path, not the 31B
checkpoint, multimodal wrapper, CUDA kernels, training memory peak, or vLLM
adapter loading. The serving runtime uses Torch 2.10.0; these CPU checks use
2.14.1. Next prepare an immutable bounded GPU qualification bundle with
full-model restore/hash checks, memory measurement, gradient/frozen-base checks,
adapter export/reload and a deadline. Long training remains gated on that
result and separately qualified data.

## Full-checkpoint H100 result

The actual downloaded checkpoint passed the shared qualification engine with
30,607,360 rank-four adapter parameters across all 410 text projections.
One native-tokenized synthetic example used 24 input tokens and five supervised
targets. Loss before the update was 6.874505519866943. Finite gradients and
updated adapter parameters were checked; persistent frozen-state fingerprints
matched before/after. A fresh base-plus-adapter load matched state identities
and produced zero maximum absolute logit difference with zero tolerances.
The adapter changed logits relative to its disabled state by up to 1.509765625;
this is an effect measurement, not improvement.

Allocator peaks were 60.919 GiB allocated and 71.961 GiB reserved. Device-wide
samples reached 72.632 GiB; sampling does not bound missed transient peaks.
The run completed in 216.195 seconds, including extensive hashing, loading,
export and reload. This duration is not a training-throughput estimate.
Evidence: `evidence/p1/full-training-gpu-002`. The full model, adapter and
optimizer outputs were stored on the network volume; the verified local
artifact copy is `artifacts/official/p1-full-training-gpu-002`.

Still open: longer contexts/batches, optimizer resume on the full checkpoint,
multi-step stability, training-corpus qualification, held-out coding gains,
quantized/serving adapter execution and competition target hardware behavior.
