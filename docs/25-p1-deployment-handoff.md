# P1 deployment handoff

Updated October 8, 2026. This is the operational handoff for the existing stopped Pod. It does not authorize an automatic restart or claim that P1 is accepted. Evidence history remains in [document 24](24-p1-implementation-status.md).

## Current decision

Model, runtime, pilot, task dependencies, starter and deployment bundle publication/restoration checks have passed for their recorded manifests. The clean Linux/Python-3.12 serving installation, dependency checks and nine CPU imports have passed. The next model-validation step requires the user to restart the Pod; no automatic restart is authorized. GPU loading, memory behavior, generated tool calls and a real repair remain unverified. Training qualification is a separate P5 requirement; a successful P1 inference run cannot guarantee a training streak will be error-free.

The authenticated [Pod read](../evidence/p1/pod-read-20261008/configuration.json) returned `EXITED` for `ywpfgef6yvnr9m`, image `runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404`, one NVIDIA A100-SXM4-80GB, disk 80, and empty mounts. The API cost field was 1.59; recheck the live rate before the next paid run. An empty mounts field does not prove that a particular directory survives stopping or termination. Verify actual storage backing before putting working artifacts there. Do not use the API GPU object's `memory: 117` field as VRAM evidence; the named GPU is the 80GB model and device memory must be checked with the driver.

## Artifacts to stage

| Artifact | Exact size / identity source | Use |
|---|---|---|
| Complete Gemma checkpoint | 23,297,590,856 bytes; [model manifest](../evidence/p1/model-intake-001/model-manifest.json) | Base-model inference; eight files, outside Git |
| Serving wheels | 5,331,545,654 bytes; [250-wheel manifest](../evidence/p1/runtime-wheels-002/manifest.json) | Offline Python-3.12/Linux x86_64 installation |
| R2 bootstrap | 16,666,629 bytes; [bootstrap manifest](../evidence/p1/bootstrap-001/manifest.json) | Eight small client wheels plus hash-pinned requirements; bootstrap verification is tracked separately |
| Official starter | [manifest](../evidence/p1/starter-bundle-001/manifest.json) | Harness/compiler assets; placeholder adapters are not trained candidates |
| Reserved development pilot | [manifest](../evidence/p1/pilot-bundle-001/manifest.json) | Agent-visible task projection, snapshot, graph and embeddings |
| Task sandbox dependencies | [manifest](../evidence/p1/wheels-001/manifest.json) | Python-3.13 task executor; separate from Python-3.12 serving environment |
| Deployment code/configuration | [Bundle 002 qualification](../evidence/p1/deployment-bundle-002/qualification.json): 62 files / 19,806,746 bytes; [restored-copy qualification](../evidence/p1/deployment-restore-002/qualification.json), 72 tests passed | Restoration, integrity checks, launch planning, base candidate and inference probe; immutable snapshot, not all subsequent workspace edits |

Trust manifests from the local deployment handoff, not an unverified object fetched alongside arbitrary data. R2 credentials are supplied separately and never included in the code bundle, model directory, agent sandbox or submission. A successful publish receipt requires remote hash readback; a restore receipt separately proves reconstruction into a fresh destination. Check both before declaring recovery readiness.

## Execution order after the user restarts the Pod

1. Confirm the intended Pod identity, SSH access, Linux x86_64, Python 3.12 availability, NVIDIA driver/device visibility and actual free storage. The original PyTorch 2.8 environment must not be reused as the qualified serving environment. The candidate requires Torch 2.10.0 and the complete recorded dependency set.
2. Establish the verified persistent working directory and copy the small bootstrap/code bundle. Check its local manifest before execution. If the required interpreter is absent, provision and verify it before installing packages; do not silently use another Python version.
3. Create a dedicated bootstrap virtual environment. Install its requirements with `--no-index --find-links=<bootstrap-wheels> --require-hashes`, run dependency checks, then use the existing R2 restoration command with explicit byte limits and new destination directories.
4. Restore the model, serving wheels and required pilot assets. Reverify manifests. Reserve space for the extracted virtual environment, logs and runtime caches; model and wheel download sizes alone are not the disk requirement. Stop preparation if measured free space is insufficient, without deleting unrelated files.
5. Create a separate serving virtual environment. Install [the serving lock](../requirements/serving-linux-py312.lock.txt) with `--no-index --find-links=<restored-serving-wheels> --require-hashes`; run `pip check` and `scripts/probe_serving_runtime.py` against the retained resolver report. Do not use the acquisition URL lock for offline deployment. The three local version exceptions remain explicit and prevent a claim of exact official environment parity.
6. Re-run model structural/numerical/layout checks as appropriate to the restored bytes, then regenerate the launch plan with `scripts/plan_serving.py` using the Pod's interpreter and model path. Bind the server to loopback and use SSH forwarding for access. Start the base model without placeholder adapters, using the recorded context and memory limits.
7. Record startup logs, actual peak device memory, readiness and elapsed time. Execute `scripts/probe_inference.py`; preserve every response and any failure. Require an actual generated tool call, real disk read and correctly linked continuation. A successful health endpoint alone is insufficient.
8. Execute a real development repair through the agent/harness and retain its patch and checks. The current Requests evaluator has a verified source-shadowing problem: tests import the installed distribution instead of the checkout. Resolve that issue or qualify a legitimate alternative development environment before making repair-success claims. A local source-path override must remain labeled diagnostic.
9. Upload and verify new evidence, confirm that required artifacts are recoverable, then return control of the stopped/running decision to the user under the agreed compute limits. No unattended training starts in P1.

## GPU handoff conditions and remaining gates

- Artifact recovery gate passed: runtime independent restoration and subsequent resolver/hash/metadata verification passed for all 250 files. Model publication and fresh restoration passed for all eight files; the restored tokenizer passed six offline template checks. These checks do not establish GPU inference readiness.
- Use the qualified deployment bundle 002 and bootstrap path; regenerate the bundle if executable deployment inputs change before handoff. Later documentation edits are not retroactively part of that immutable snapshot.
- Confirm the paid-run limit before starting model validation. Verify persistence, free storage and SSH immediately after the user's restart; the current stopped-Pod API cannot establish actual filesystem behavior. Do not store the only copy of any artifact on unverified ephemeral storage.
- Preserve the official evaluator source-selection finding and a defensible plan for real repair validation.

GPU correctness, CUDA kernels and actual model behavior require a bounded GPU run. CPU preparation reduces avoidable setup failures; it cannot honestly guarantee those results in advance.

### Requests evaluator source-selection finding

The retained [Python path diagnostic](../evidence/p1/pilot-environment-002/python-path.log) puts `/usr/local/lib/python3.13/site-packages` before `/workspace/src`. The official `sandbox/setup.py` fast path writes plain path entries to `workspace_paths.pth`; it does not establish workspace-first precedence. A successful editable installation is therefore insufficient evidence that the checkout is the imported package. The [official evaluator probe](../evidence/p1/evaluator-source-002/receipt.json) confirms the consequence for this snapshot: its source-origin test fails because Requests resolves to the installed package. This explanation is consistent with the measured path order; it is not an exhaustive diagnosis of every task environment.

Before interpreting any real repair result, retain a source-origin check and a check that the tested behavior responds to a controlled source change in the evaluator environment. Keep evaluator-only diagnostics outside agent inputs. Preserve official results separately from any locally corrected evaluator run. The existing `PYTHONPATH` diagnostic demonstrates a possible local path correction, not an organizer-approved grading fix; no official files or benchmark reference patches have been changed to make the result pass.

## Transfer interruption and cleanup procedure

Run `scripts/audit_r2_multipart.py` with the exact model/runtime manifests and a secure environment-file path to record incomplete uploads. The auditor is read-only and bounded to `artifacts/v1/blobs/sha256/`. A matching hash identifies an artifact, not the owner or liveness of an upload. Age alone must never trigger an abort. The initial [audit](../evidence/p1/multipart-audit-001/receipt.json) found one incomplete runtime-wheel upload while publication was active; nothing was aborted.

If a transfer is interrupted, first determine whether the original process is actually terminal. Poll its existing handle; a timeout is not proof of termination. Do not launch a duplicate while it is alive. After a confirmed failure, retain its logs and rerun publication against the same immutable manifest with a new evidence directory. Completed objects are reused only after size/SHA-256 readback. An incomplete multipart object is not treated as a completed blob, and the current implementation restarts that object's upload rather than resuming old parts.

After transfers are terminal, repeat the audit. Investigate any remaining upload by its exact upload ID, object key, initiating process and initiation time. Abort only an upload attributable to a confirmed-dead attempt after ruling out another live writer. If attribution is uncertain, retain it for review. No bucket-wide lifecycle changes or blanket prefix aborts are authorized by this procedure. The read-only audit currently has no automatic-abort capability.

Two fault-injected tests prove bounded recovery properties: interruption after one complete remote object leaves no manifest commit and a fresh transport reuses that verified object; loss of the manifest acknowledgement after remote commit permits an idempotent retry without another manifest write. [Recovery test receipt](../evidence/p1/transport-recovery-001/receipt.json). These tests do not simulate a process killed inside a live multipart request. The original deployment bundle contains the earlier 70-test snapshot; regenerate the bundle to include subsequent auditor/test additions.
