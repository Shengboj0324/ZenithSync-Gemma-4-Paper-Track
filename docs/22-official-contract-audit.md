# Official contract audit and compiler verification

October 7, 2026 local date (receipts use October 8 UTC). Kaggle CLI 2.2.4 authenticated with the existing local credential file. No credential contents were printed. All 524 competition file metadata entries were enumerated; only the harness guide, starter and Docker/setup assets were downloaded, not task solutions, snapshots or base model weights.

## Provenance and environment

- Competition source: [official competition data](https://www.kaggle.com/competitions/gemma-4-developer-agent/data). Local source under ignored `artifacts/official/gemma-4-developer-agent/`; [inventory](../evidence/r0/official-intake-001/gemma-4-developer-agent.manifest.json).
- Notebook source: [organizer getting-started notebook](https://www.kaggle.com/code/ryanholbrook/getting-started-gemma-4-developer-agent). Downloaded as data, not executed. [Inventory](../evidence/r0/official-intake-001/getting-started.manifest.json).
- Host wheels: [organizer wheelhouse](https://www.kaggle.com/datasets/metric/gemma-4-developer-agent-wheelhouse), identified by that notebook. Downloaded `swegemma 0.2.7`, `adk-submission 0.2.12`, `adk-eval-core 0.1.0`, and `google-adk 1.36.1`. [Wheel hashes](../evidence/r0/official-intake-001/wheelhouse.manifest.json).
- CPU compiler installed into ignored `.venv`; [resolved acquisition/compiler environment](../evidence/r0/official-intake-001/acquisition-environment.txt). `pip check` reported no broken requirements. This inventory predates the subsequent full host installation; the latest [host environment](../evidence/r0/linux-002/host-environment.txt) includes swegemma and its dependencies, with a clean `pip check`. No CUDA model server was executed. Core `zenithsync` still uses only the standard library.

Local SHA-256 inventories pin retrieved bytes. They are not publisher signatures or proof that mutable upstream releases will remain unchanged. Raw competition assets remain ignored and are not redistributed in the project documentation.

## Verified contracts and discrepancies

The official compiler compiled the **unchanged** starter into `LlmAgent`, with nine registered tool placeholders plus an `AgentTool`. It resolved its prompt/config includes and adapter names. The bindings are deliberately non-executable placeholders, and the registered model is a string alias; this demonstrates schema and tree construction only. That CPU-only receipt does not validate actual tool schemas, adapter tensors, inference, workspace behavior or repair performance. The subsequent Linux check below covers actual bound-tool compilation and workspace behavior.

The source-derived [nine tool signatures](../evidence/r0/official-intake-001/tool-signatures.json) include internal `ctx`; the runner binds this context rather than asking the model to supply it. These signatures are extracted from the released wheel and include source hashes. The compiler-exported [agent schema](../evidence/r0/compiler-004/agent-schema.json) is the pinned configuration reference.

| Finding | Consequence |
| --- | --- |
| Guide documents four root names; released discovery prefers `agent.yaml`/`root_agent.yaml`, and `.yml` aliases fail beside `eval_config.yaml` | Use `agent.yaml`; record alias probes as compatibility discrepancies, not passing full compatibility |
| Starter uses `../prompts/...` includes inside the submission boundary and compiles successfully | Do not reject all parent components for includes; enforce resolved containment using the official loader. ZIP member paths still reject parent traversal |
| Guide describes a strict `<3 GiB` cap; source/notebook checks permit the configured boundary | Remain strictly below the cap; do not rely on boundary equality for submission |
| Released schema requires `instruction` for LlmAgent | Invalid-field fixtures must include otherwise-valid required fields, so rejection tests exercise their intended cause |
| Graph similarity resolves known symbols to existing embeddings | Use symbol names; free-form natural-language retrieval is not established |
| Per-task agent timer starts after setup; aggregate competition allowance includes setup | Track these separately; never equate agent-session time with total charged runtime |
| Patch capture uses binary diff against `_swegemma_baseline` with fallback to HEAD | Later patch receipts must reflect the actual baseline and untracked-file intent behavior |

The official sample's one-minute/ten-call limits are demonstration settings, not an evidence-based production allocation. The notebook and guide differ on vLLM memory utilization and compaction interval; final deployment settings must be pinned to the actual scoring entry point rather than blended into an invented profile.

## Test evidence and limits

```sh
.venv/bin/python scripts/verify_official_r0.py --assets artifacts/official/gemma-4-developer-agent --output evidence/r0/new-compiler-run
python3 scripts/verify_r0.py --output evidence/r0/new-core-run
```

[Compiler receipt 004](../evidence/r0/compiler-004/receipt.json): unchanged starter compilation plus eight rejection checks passed. Wrong-model and multiple-root rejection are explicit project guards; the other six exercise actual compiler/loader failures. Rejection classes and messages are retained. Three alias probes separately record one success and two failures. Limits are transcribed from inspected `swegemma/config.py`; this script does not execute `build_submission_limits` through the full runtime.

[Core receipt 004](../evidence/r0/local-004/receipt.json): 26 tests and isolated offline zipapp success/rejection checks passed. The added test covers root filename handling and ambiguous roots. Structural preflight continues to say official compatibility is unverified.

Development failures are not hidden: the first compiler attempt stopped at the `.yml` discrepancy; compiler-002 incorrectly attributed unknown-tool and missing-adapter rejections because those fixtures omitted required `instruction`. Those two negative checks in compiler-002 are invalid evidence. The corrected attempt exposed the separate upstream `SubmissionError` hierarchy, then compiler-004 passed with exact intended rejection types. Empty failed-run directories were removed; compiler-002 is retained as superseded evidence. No early result is used as acceptance proof.

## Linux integration closeout

Docker became available after the earlier launch failures. Built the unchanged official `Dockerfile.sandbox` as Linux AMD64, pinned the resulting image ID in [Linux receipt 002](../evidence/r0/linux-002/receipt.json), and ran actual `swegemma 0.2.7` bound tools in containers with networking disabled, 4 GiB memory and two CPUs. The host is ARM64 macOS, so this is emulated Linux execution, not scoring-hardware performance evidence.

Twenty-five integration checks passed. The unchanged starter compiles with the actual nine bound functions and official `build_submission_limits`. Checks cover failing/passing synthetic tests, file operations, path containment, ambiguous-edit rejection without changing bytes, all three graph tools' missing-asset failures, timeout, budget exhaustion, free submission after call exhaustion, patch capture of added/modified/deleted files, and successful patch application in a fresh failing workspace. Graph success paths still require real task assets. The test script itself supplies the arithmetic edit; no model selected it.

[Linux audit](../evidence/r0/linux-002/audit.json) retains hashes, build log, host dependencies and the separate 26-test Linux core log. Core tests used only read-only mounts of project source and tests. Integration containers used no host mounts and were all removed. This does not invoke the official protected-test restoration/JUnit grading pipeline.

The first Linux run, retained as `linux-001`, failed because the assertion expected a trailing newline from `read_file`; the released tool returns joined lines without that newline. The corrected assertion checks the documented representation and independently checks raw file bytes through the sandbox. `linux-002` supersedes that failed run. No failed result is counted as passing evidence.

```sh
.venv/bin/python scripts/verify_linux_r0.py --image zenithsync-r0-sandbox:20261008 --output evidence/r0/new-linux-run
```

R0/P0 contracts and skeleton are accepted within this scope. P1 model intake/inference and P2 real-task execution remain pending. Full offline host installation, actual graph retrieval, adapter tensors and GPU behavior are unverified. No GPU or paid remote worker was created.
