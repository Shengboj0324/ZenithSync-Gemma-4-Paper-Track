# R0 foundation implementation and acceptance

Updated October 7, 2026. R0 maps to **P0, Contracts and skeleton**, in document 12; historical reproduction R1 is unrelated. Local foundation code exists and passes its recorded checks. The official harness guide, starter and released compiler packages are now downloaded and inventoried. The unchanged starter compiles in a CPU-only check; synthetic Linux sandbox/tool integration now passes. This is infrastructure, not a running or trained Gemma agent.

## Implementation and usage

The `zenithsync` package uses Python's standard library only. The locally verified interpreter is Python 3.13.7 on macOS. The core checks need no third-party packages. A separate ignored `.venv` now contains the official Kaggle CLI and released swegemma/ADK host dependencies for acquisition and integration checks. No GPU resources, model weights or remote runtimes were provisioned. The core also passes in the official Linux AMD64 sandbox image under local emulation. Run from the repository root:

```sh
python3 -m unittest discover -s tests -v
python3 -m zenithsync check-splits examples/splits.draft.json
python3 -m zenithsync inventory /absolute/staged/model --kind model --source kaggle --revision v2 > /absolute/outside/model-manifest.json
python3 -m zenithsync verify /absolute/staged/model /absolute/outside/model-manifest.json
python3 -m zenithsync check-zip /absolute/submission.zip --max-bytes 100000000 --max-entries 1000
python3 scripts/verify_r0.py --output evidence/r0/new-run-id
```

Example paths and archive limits are illustrative development settings, not organizer limits. Write a generated manifest outside its input directory. Store credentials elsewhere; inventories include every file and do not filter secrets. Use an owned, quiescent staging directory, not a live model download. Local hashes establish byte identity, not publisher authenticity. No weights are included in this repository.

| Module | Implemented contract | Scope limit |
| --- | --- | --- |
| `contracts.py` | Exact integer nanosecond budget, token admission, immutable event/state reducer, replay, stale-check rejection | No subprocess watchdog, tokenizer, model or scheduling optimizer |
| `artifacts.py` | Streaming SHA-256 inventory; strict manifest validation and full file-set verification | Regular files only; directory metadata omitted; not safe against a concurrently malicious writer |
| `archive.py` | Read-only ZIP structural preflight with explicit resource limits and path/type checks | Does not parse YAML, resolve includes, validate adapters or compile ADK |
| `splits.py` | Task uniqueness and declared repository/family/input isolation | Cannot discover undeclared forks, semantic duplicates or model pretraining contamination |
| `__main__.py` | CLI inventory, verification, split validation, event replay and ZIP checks | Exit 0 means that command's limited check passed, not competition readiness |
| `scripts/verify_r0.py` | Fresh test logs, source hashes and isolated zipapp smoke receipt | Local test evidence; no hidden benchmark, model or provider execution |

Runtime files are under `zenithsync/`; synthetic tests under `tests/`; a deliberately empty draft split under `examples/`; immutable run receipts under `evidence/r0/`. Later inference, workspace execution, training and independent evaluation modules must preserve these boundaries. Development Python code is not automatically deployable through the restricted competition YAML.

## Event and manifest schemas

Version 1 events have `schema_version`, zero-based contiguous `sequence`, `kind`, and nullable `artifact_sha256`, `candidate_sha256`, `passed`. `replay` consumes a JSON array. All unknown fields, malformed digests and unsupported versions fail validation.

| Event | Required non-null payload | Transition |
| --- | --- | --- |
| `start` | None | Ready to working |
| `observation`, `hypothesis` | Artifact hash | Working; factual evidence and model conjecture stay distinct |
| `candidate` | Candidate hash | Working; clears previous check result even if the hash repeats |
| `check` | Receipt hash, current candidate hash, boolean result | Working; records latest local check |
| `submit` | Patch receipt hash, current candidate hash | Working to submitted; does not assert evaluator acceptance |
| `stop` | Reason artifact hash | Ready or working to stopped |

Submitted/stopped states reject further events. A candidate digest must identify the complete input bundle: source tree, tests, environment specification and relevant configuration. The runner must generate that bundle and retain referenced artifacts; R0 does not execute or attest those artifacts. A passing local check is never a repair acceptance flag. Restoring a state uses validated event replay; historical events describe past effects and must not re-execute external actions.

Artifact manifests have exactly `schema_version: 1`, `kind` (`model`, `harness`, `candidate`, `fixture`), nonempty `source` and `revision`, and a nonempty `files` array. Each file has canonical relative POSIX `path`, nonnegative integer `size_bytes`, and lowercase SHA-256 `sha256`. This is the model-intake identity schema. Actual model configuration, safetensors layout, tokenizer, loader and adapter compatibility belong to P1; an arbitrary directory labeled `model` does not pass those gates.

Split manifests have exactly `schema_version: 1`, `status` (`draft` or `frozen`), and `tasks`. Each task has `task_id`, `repository_group`, `leakage_group`, `split` (`train`, `development`, `confirmation`) and `input_sha256`. Repository/fork identity must be canonicalized by dataset intake before validation. Empty draft is valid scaffolding; empty frozen evaluation is rejected. No real cohort has been assigned or frozen.

## Mathematical claim ledger

| Property | Assumptions and derivation | Implementation and independent checks | Limit |
| --- | --- | --- | --- |
| Budget admission preserves the declared reserve | For nonnegative integer limit L, reserve R≤L, charged C and request A, admit iff C+R+A≤L. Therefore after an action charged at most A, at least R remains | `Budget.admits`; independent discrete-slot enumeration for L=0…11, R=0…L, C,A=0…14; exact boundary and 80-digit checks | Duration estimate is not an upper bound unless the later runner enforces one; overruns are retained, never clipped away |
| Charge composition | Integer addition gives charge(a) then charge(b) = charge(a+b); no float rounding | `Budget.charge`; exhaustive a,b=0…14 | No claim about which harness durations are chargeable until inspected |
| Context capacity | Exact tokenizer input I, output reserve O and protocol P fit iff I+O+P≤K | `context_fits`; independent finite-list length checks over bounded instances | Token counting itself is not implemented; disjoint accounting must be supplied |
| Current-check association | Initially no check; candidate events clear it; check events require current candidate. Induction over valid events preserves association | `TaskState.apply`; stale receipt, changed candidate, failed recheck, invalid restore and terminal-event tests | Hash collisions are assumed infeasible; a dishonest/incomplete runner bundle is outside this contract |
| Declared split disjointness | Each grouping key maps to exactly one split; a conflicting assignment is rejected | `validate_splits`; each grouping dimension challenged independently | Real independence and contamination are not established by string labels |

These are bounded tests plus stated algebraic/inductive arguments. They do not guarantee arbitrary agent-generated code, optimal repair decisions, generalization, or a competitive score. Statistical comparisons and advanced learned controllers require measured data in later phases.

## Official integration inventory

The [official data page](https://www.kaggle.com/competitions/gemma-4-developer-agent/data), read through the rendered browser on October 7, describes 129 public development tasks, repository snapshots, graphs, embeddings, offline wheels, Docker specifications, `sandbox/setup.py`, `sample_submission/`, and `HARNESS_README.md`. Public task rows include reference fixes and verification tests: those must be segregated from evaluation-time agent inputs. The page lists a Python 3.13 sandbox. These are public descriptions, not inspected downloaded assets. The in-app file viewer was signed out. The user subsequently confirmed joining and accepting rules, and authenticated Chrome visibly confirmed acceptance. Navigation to the Data page did not yield readable file contents during this attempt; no files were downloaded. A subsequent authenticated Kaggle CLI call succeeded using existing local credentials. The guide, starter, Docker specifications and setup script were downloaded into ignored `artifacts/official/`; the official getting-started notebook identified the separate host wheelhouse. Its core wheels were downloaded and hashed. See [official contract audit](22-official-contract-audit.md).

The public [overview](https://www.kaggle.com/competitions/gemma-4-developer-agent/overview) provides this preliminary integration matrix, recorded in document 19. The nine tool signatures have now been extracted from released source into [tool-signatures.json](../evidence/r0/official-intake-001/tool-signatures.json). All nine bound tools were invoked in the synthetic Linux integration:

| Surface | Publicly described capability | R0 integration status |
| --- | --- | --- |
| `run_command` | Shell command in task workspace | Actual bound tools exercised in Linux |
| `read_file`, `edit_file`, `write_file` | Read slices, replace text, write files | Actual bound tools exercised in Linux |
| `get_status`, `submit_patch` | Inspect state, capture patch | Status and patch capture exercised; project event translation remains later runner work |
| `get_code_neighbors`, `search_similar_code`, `get_code_subgraph` | Structural and semantic repository navigation | Missing-asset failures verified; successful graph retrieval awaits real assets |
| `agent.yaml` | Restricted ADK definition; optional declared subagents | Official schema exported; unchanged starter compiled |
| Includes, skills, adapters, `eval_config.yaml` | Optional packaged capabilities and evaluation controls | Source/compiler checked with actual tool bindings; model execution pending |

Offline strategy: R0 needs no third-party packages. The verification script builds a temporary zipapp from source, runs it with isolated Python outside the repository, checks both success and failure exits, then removes it. Once official libraries arrive, pin their versions, interpreter/ABI and wheel hashes; validate a clean Linux offline installation using only the authorized wheelhouse. No network installation may occur inside scored execution. The local smoke is not that target-runtime test.

## Acceptance audit and next action

**R0/P0 accepted for contracts and skeleton.** Its eight deliverables are present: official asset inventory, supported tool/config matrix, package layout, state/event schemas, offline dependency strategy, meaningful failure fixtures, draft split skeleton and model-intake schema. [Local receipt 004](../evidence/r0/local-004/receipt.json) records 26 passing tests and isolated zipapp checks. The same 26 tests pass in the official Linux sandbox image. [Linux receipt 002](../evidence/r0/linux-002/receipt.json) records 25 checks using real released tools, with the unchanged starter compiled using actual bound functions and `build_submission_limits`. All test containers were removed.

The synthetic patch includes modification, addition and deletion, and passes its test after transfer into a fresh container whose unmodified version fails. No-network, memory/CPU limits, ambiguous-edit rejection, path containment, missing graph assets, timeout and budget exhaustion were exercised. The test runner supplies the trivial edit: this is a tool contract fixture, not evidence of learned repair capability. See [audit](22-official-contract-audit.md) for failure history and scope.

P1 requires the user's complete downloaded model directory and exact revision, followed by loader/tokenizer/adapter checks and actual inference. Successful graph navigation, real development-task replay, official Phase 2 grading, clean offline host installation, GPU qualification and performance comparison remain later gates. The local Linux image runs through AMD64 emulation on an ARM64 host; no target-hardware latency claim follows. No paid remote worker or GPU has been provisioned.
