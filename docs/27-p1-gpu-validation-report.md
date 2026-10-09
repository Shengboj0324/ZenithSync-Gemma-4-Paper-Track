# P1: first GPU validation session

October 8, 2026, Pacific time. **P1 remains partially qualified, not fully accepted. No training ran.** The untrained Gemma checkpoint now has real inference, tool execution and submitted-patch evidence. Official grading compatibility and general tool reliability remain open.

## What actually ran

The user authorized four hours on the existing Pod at its observed $1.79/hour rate. The session began at 2026-10-09 01:01:47 UTC. Remote cleanup completed at 01:43:25 UTC, roughly 42 minutes later. This is an engineering-session interval, not a billing record: the agent stopped its server but did not stop the Pod. The user was notified to stop the Pod. The temporary remote R2 credentials and session SSH key were removed, while existing keys were preserved. [Cleanup evidence](../evidence/p1/pod-session-closeout-001/cleanup.json).

The device was an A100-SXM4-80GB reporting 81,920 MiB, with driver 570.172.08 and Python 3.12.3. The serving environment used vLLM 0.19.1, Torch 2.10.0 and Transformers 5.13.1. The original Pod's Torch 2.8 environment was not used. `/workspace` was container-overlay storage; R2 holds the recoverable source artifacts.

The first load succeeded but HTTP failed because FastAPI 0.141.1 and the retained metrics middleware were incompatible. FastAPI 0.136.3 corrected this without changing the other 249 resolved versions. The corrected full lock, offline dependency check, HTTP regression probe, and all nine import/version probes passed. This is a qualified local environment with explicit exceptions, not exact official runtime parity. [Correction evidence](../evidence/p1/http-stack-fix-001/httpfix-change.json); [final runtime probe](../evidence/p1/pod-session-closeout-001/runtime-probe-corrected/receipt.json).

The corrected server became ready after approximately 84 seconds. Its profile used 32,768 context tokens, one concurrent sequence, BF16 activations and 0.8 GPU memory utilization. vLLM reported 19.63 GiB during weight loading. Separate device samples observed 67,071 and 67,231 MiB allocated, including serving reservations; neither is a whole-run peak. After shutdown the device reported 0 MiB. [Server lifecycle](../evidence/p1/pod-session-closeout-001/server-002/status.json).

## Inference and repair evidence

| Experiment | Observed outcome | Limit |
|---|---|---|
| Real file-read continuation | Gemma requested a file, the client read a newly generated unpredictable marker, and the continuation reproduced it exactly | One actual exchange, not an estimate of general accuracy |
| Four generated-write cases | Simple text, multiline quotes, Unicode/f-string content and reversed argument order all matched requested arguments | Generated argument probe; it did not execute file writes |
| Repository attempt 001 | Captured a 914-byte patch, but exhausted 40 turns; 11 malformed `write_file` calls lacked `filepath` | Failed completion; retained unchanged |
| Repository attempt 002 | Completed in approximately 200 seconds including setup, submitted a 439-byte source-only patch, no runner error | Same development task and candidate; not independent confirmation |
| Raw capture for attempt 002 | 30 completions; 29 tool calls matched their actual request schemas: 14 commands, 12 reads, one write, one edit and one submission | No schema errors in this run does not explain attempt 001 or prove semantic correctness |

Evidence: [tool continuation](../evidence/p1/pod-inference-002/inference-002/receipt.json), [generated writes](../evidence/p1/generated-write-002/remote/receipt.json), [attempt 001](../evidence/p1/repair-attempt-001/receipt.json), [attempt 002](../evidence/p1/repair-attempt-002/receipt.json), [schema audit](../evidence/p1/repair-capture-analysis-001/schema-validation.json).

The candidate received the issue, repository and base-commit fields, source snapshot and navigation assets. It did not receive the evaluator test patch or reference implementation. The evaluator input was frozen separately and contains no reference implementation. Attempt 002's only inference-request change was `return_token_ids=true` for observation; original and forwarded requests are retained. Raw tokens were decoded with the pinned tokenizer. No generated patch was manually repaired.

Attempt 001 recorded 498,019 prompt and 8,212 completion tokens. Attempt 002 recorded 380,465 prompt and 6,855 completion tokens, with zero reported cached tokens. These include repeatedly processed context, not unique training tokens. Temperature zero did not produce identical trajectories across the two runs; deterministic replay has not been established. Do not discard attempt 001 when assessing reliability.

## Independent evaluation and correctness boundary

The stock local evaluator imported an installed Requests package instead of the edited checkout. Its missing `pytest-httpbin` provider also caused 187 fixture errors. These were infrastructure defects, not evidence that the patch failed its intended behavior.

A separately labeled local image adds real loopback HTTP fixtures and explicitly selects `/workspace/src`. The plugin was updated to 2.1.0 because [upstream documents Python 3.13 certificate support](https://github.com/kevin1024/pytest-httpbin#changelog). Flasgger 0.9.7.1 was built offline from its [hash-verified PyPI source archive](https://pypi.org/project/flasgger/0.9.7.1/) after the older available wheel failed to import Flask 3. The image passed offline hash-enforced installation, dependency checks and plugin imports. Its Python/pytest/plugin versions differ from the historical repository requirements, so this is not an official grading fix.

Fresh corrected evaluations use the official test patch, unchanged assertions, network isolation and measured checkout imports:

| Input | Passed | Failed | Skipped | Expected failure | Official `resolved` field |
|---|---:|---:|---:|---:|---|
| Unchanged baseline | 316 | 6 | 1 | 1 | false |
| Attempt 001 patch | 317 | 5 | 1 | 1 | false |
| Submitted attempt 002 patch | 317 | 5 | 1 | 1 | false |

The [paired JUnit comparison](../evidence/p1/repair-comparison-001/receipt.json) verifies an identical 324-case cohort and exactly one changed outcome. The target string-content-length regression fails before the patch (`47` instead of `51`) and passes after it. The same four connect-timeout cases and one invalid-redirect-URL case fail in both states. The timeout tests attempt an external unroutable address inside the network-isolated sandbox. The invalid-URL failure remains a baseline compatibility issue requiring investigation; it has not been silently excluded. No clean aggregate solve or competition score is claimed. Full logs and per-case comparisons remain evaluator-only evidence.

For ordinary valid Unicode strings, the intended length is the number of UTF-8 bytes, rather than the number of Unicode code points. The patch directly computes that quantity. The passing regression establishes the observed example, not correctness for every input type, dependency version, string subclass or future transport implementation. Formal properties of artifact hashing and schema validation likewise do not prove agent repair accuracy.

## Assessment and remaining work

- **Software:** 77 local tests passed, including real-process deadline tests and capture transparency/rejection tests. Actual GPU probes and repository evaluations are separate evidence. Newly extended JUnit capture is checked by actual evaluations, not by claiming coverage from the earlier unit run.
- **Mathematical:** exact byte-length reasoning applies within its stated input/encoding domain. No new mathematical theorem or universal model-correctness guarantee is claimed in P1.
- **Statistical:** one development task, repeated twice, cannot estimate repository-general repair rate or demonstrate superiority. No confidence interval or winner claim is appropriate for these selected runs.
- **Fair comparison:** local baseline and patched runs use the same image, task, official test patch and source override. Original uncorrected failures are preserved. Repository tasks remain excluded from later confirmatory evaluation.
- **Engineering:** live serving uncovered a dependency failure invisible to installation checks; the corrected lock and runtime probe now record it. Durable model recovery passed before use. The new code/evidence bundle needs its own publication and independent restoration receipt.
- **Evidence:** raw outputs, patches, source identities, versions, baseline failures and cleanup are retained. Missing full-run peak telemetry, unresolved malformed-call causality and official parity are explicitly open.

Next steps are local evaluator qualification and diagnostic tooling before another bounded GPU session. Full P1 acceptance requires a defensible remaining-gate decision; training/export/reload and large-corpus readiness belong to P5–P6. A successful P1 smoke test is not permission to start the proposed three 50M-token candidates.
