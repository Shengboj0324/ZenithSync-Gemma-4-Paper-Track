# P1 requirements audit

October 8, 2026. This audit distinguishes the published P1 exit criteria from the broader quality objective. It does **not** declare the overall goal complete, waive failed checks or establish training readiness.

The [living phase plan](12-continuous-implementation-plan.md) defines P1 as model intake and inference: downloaded path/version, complete package inspection/hash, exact quantized model execution, multi-turn tool calls, memory/latency evidence, and a real starter task with captured patch. Complete agent recovery belongs to P2, broad independent evaluation to P3, and training/export/reload to P5. Earlier status updates mixed these categories; this table makes that distinction explicit without discarding their requirements.

| Requirement | Authoritative evidence | Finding |
|---|---|---|
| Identify and preserve the downloaded model | Eight-file intake manifest, authenticated publisher v2 listing, complete R2 publication and independent local/Pod restoration | Intake identity and recovery established. Publisher byte authenticity remains limited by the absence of publisher hashes |
| Inspect model structure and numerical values | Complete safetensors interval checks, BF16 finite-value scan, positive finite scales, 410 text projection dimensions | Recorded predicates passed. Exhaustive multimodal semantics are not established |
| Run the exact quantized checkpoint | Pod model-restore receipt, server argv naming the restored model directory, real checkpoint-loading log and actual model responses | Base-model inference demonstrated in the qualified local runtime |
| Generated call, actual tool result and continuation | Unpredictable on-disk marker probe; generated read call and exact returned marker | One real multi-turn smoke exchange passed |
| Real task, edits and submitted patch | Two retained attempts; second attempt submitted a 439-byte source-only patch with no runner error | Demonstrated. First attempt's turn-budget failure and malformed calls remain counted |
| Record memory and latency | [Extracted resource receipt](../evidence/p1/requirements-audit-001/resources.json), with hashes of original logs | Measurements now indexed; no whole-run peak or latency-distribution claim |
| Durable P1 assets and working code | Model/runtime/pilot/dependency recovery; bundle 005 independently restored and all 81 tests passed from it | Recovery established for named immutable bundles, not arbitrary future artifacts |
| Mathematical and statistical integrity | Exact artifact identity checks, dimension predicates, explicit measurement units and paired 324-case source-qualified comparison | No fabricated rates or universal correctness claim. One development task cannot establish general superiority |
| Reliable agent behavior across difficult tasks | Eleven malformed writes in attempt 001; valid calls and completion in attempt 002 | Incomplete. Recovery behavior and broader failure characterization remain required |
| Trustworthy independent repair grading | In-process source gate and snapshot-plus-patch hash match; target regression changes from fail to pass | Local source qualification established; five unchanged baseline failures prevent a clean aggregate solve |
| Official competition-runtime compatibility | Released SDK/harness used locally, with documented serving exceptions and a custom task image | Not established on the actual competition target. The local failures do not prove that the organizer's production environment has the same defects |
| Full training readiness and abundant training corpus | Data requirements and qualification gates documented; P1 development assets acquired | Not established. No training has started; compatibility, licensed corpus, gradients, resume/export/reload and trained evaluation remain later mandatory work |
| Resource control | Owned server stopped and cleaned up; authenticated Pod read returned `EXITED` | Pod confirmed stopped; no restart performed during this audit |

## Resource interpretation

The retained server log reports 19.63 GiB during model loading, 43.23 GiB available for KV cache, and a 47,216-token GPU cache capacity. It estimates 8.90 maximum concurrency for 32,768-token requests, while our actual profile permits only one sequence. The estimate is not an observed throughput result. The configured GPU-memory fraction is a serving parameter, not proof of peak total device use.

The two completion-request wall times were exactly 2.290692886 and 0.854144563 seconds in the recorded nanosecond measurements. Startup took approximately 84.03 seconds. These are individual observations. They do not justify p95 latency, sustained throughput, a smaller-GPU recommendation, or a training-time estimate.

## Acceptance decision and next work

The published intake/inference smoke requirements have substantive evidence. **The broader user-requested quality objective remains open**, particularly reproducible tool failure diagnosis, robust task execution, evaluation compatibility and training qualification. No change in phase labeling is permission to train or promote a competition candidate.

Do not repeatedly rebuild deployment archives just to restate these limits. The next implementation work must close a functional gap: resolve the task environment or create a bounded, fully instrumented failure-reproduction experiment. A new GPU session is justified only when its hypotheses, input versions, failure evidence and time cap are prepared locally. The current Pod remains stopped.

Audit inputs and identities: [inspected evidence](../evidence/p1/requirements-audit-001/inspected-evidence.json), [current model recheck](../evidence/p1/requirements-audit-001/current-model.json), [Pod state](../evidence/p1/requirements-audit-001/pod-state.json). This is a human-reviewed requirements assessment, not an automated certificate of universal correctness.
