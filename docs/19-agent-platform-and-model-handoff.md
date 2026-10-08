# Gemma agent platform: implementation contract and model handoff

Updated October 7, 2026. Status: user-adopted direction; implementation plan, not an implemented or trained platform. This document supersedes earlier specialist product proposals for build scope. [Document 12](12-continuous-implementation-plan.md) remains the living cycle and acceptance register.

## Product and completion criteria

Build an autonomous repository engineering agent powered by the competition's Gemma checkpoint: accept a task, understand relevant code, execute tools, construct and revise a patch, run checks, and deliver the patch with evidence. Include a reproducible training/evaluation pipeline, a CLI/batch interface, persistent run records and inspectable artifacts. A web dashboard is optional after the core works. Initial scored scope is issue repair; feature implementation and broader workflows need their own evaluations.

“Fully capable” and “peak accuracy” are goals, not certification labels. Completion requires a working offline-compatible agent, an evaluated training candidate, and repeatable measurements; it does not imply universal correctness, superiority over frontier agents, or competition placement. A trained candidate may fail promotion while the untuned champion remains deployable. Do not claim training completion until a real run and reload succeed.

## Live verification and unresolved facts

The official [competition overview](https://www.kaggle.com/competitions/gemma-4-developer-agent/overview) was read from the rendered browser DOM on October 7 after the web text reader returned an empty body. It confirms:

- Every agent/subagent must use `gemma-4-31b-it-qat-w4a16-ct`.
- Submission is a ZIP with root `agent.yaml`, compiled into a restricted ADK agent. Optional PEFT LoRA folders contain configuration and safetensors weights, referenced by adapter name.
- Only harness tools and declared `agent_tool` subagents are available. Skill scripts run in the persistent Docker sandbox and consume the central budget. Includes must stay inside the submission root.
- The twelve-hour aggregate allowance includes sandbox setup and excludes patch validation; optional per-task settings are in `eval_config.yaml`.
- Patches receive pass/fail evaluation; score is the percentage of repaired repositories passing validation. `submit_patch` captures the workspace diff, including untracked-file intent.
- L4×4 provides 96 GB aggregate GPU memory; L4 notebook sessions have internet disabled. Aggregate memory is not a single contiguous 96 GB device.
- Entry/team merger: November 25; final code submission: December 2; optional paper: November 12, all 2026 at 23:59 UTC.

The user-supplied [model page](https://www.kaggle.com/models/google/gemma-4/other/gemma-4-31b-it-qat-w4a16-ct) was also read in the browser. The selected variation is Version 2, with 23.3 GB listed under Files. Its metadata says Fine-Tunable: No, and its README identifies compressed-tensors as an inference format. The user reports an approximately 18 GB download and access to it. Archive compression, revision or display units could explain the size difference, but that has not been established. Inspect actual files before deciding; size alone is not an integrity check.

The overview explicitly permits adapters. The model-page label is not proof that all LoRA workflows are impossible, nor does the adapter allowance prove that direct training on this packed file works. Resolve compatible training representation, target-module mapping, tokenizer/template identity and exact deployed quantized-base behavior through a small real pilot. Do not substitute another base model silently. A full-precision or other training representation is a separately versioned asset, if needed and permitted.

Not yet inspected in this revision: authenticated dataset assets, `HARNESS_README.md`, starter internals, installed loader versions, actual downloaded model bytes, runtime LoRA constraints, or current account competition entry. The browser was signed out. Public overview access does not verify the user's registration. Earlier rules findings remain dated in document 11; refresh gated details at P0.

## Architecture and boundaries

| Component | Design | Evidence required |
| --- | --- | --- |
| Model interface | Exact model/revision; pinned tokenizer, template and tool parser; bounded context/output; separate development serving adapter | Load plus real multi-turn tool-call continuation, memory and timing measurements |
| Agent controller | Explicit task state, observations versus hypotheses, action history, remaining budget and candidate patch | Legal transitions, termination, restore after interruption; no fabricated observations |
| Repository context | Start with file/search tools; use official graph/embedding tools when functional; maintain source paths and freshness | Relevant-code retrieval and repair outcome measured separately; empty-result fallbacks |
| Workspace execution | Isolated disposable task workspaces, bounded subprocesses, minimal environment, no provider credentials in task sandbox | Timeouts, child cleanup, filesystem boundaries, invalid calls, task isolation and actual builds/tests |
| Patch workflow | Edit, inspect diff, test, retain or revise, submit before expiry | New/deleted files captured correctly; tests tied to candidate hash; no stale passing status |
| Evaluation | Separate process/assets, immutable starting trees, independent validation, explicit infrastructure failures | Oracle controls, all attempted tasks counted, baseline/candidate paired runs |
| Training | Versioned datasets and split provenance; masked supervised tuning first; optional preference/RL later | Small gradient/loss tests, resume/reload, adapter export and target-loader qualification |
| Operations | CLI/batch entry point, resumable run records, model/data manifests, cancellation, artifact restore | Reproduce a run from pinned inputs and distinguish external side effects from replay |

Keep the platform's development coordinator separate from the competition agent. Features unavailable through the restricted ADK/tools must stay in training/evaluation infrastructure, or be redesigned as permitted sandbox skills. Do not assume arbitrary Python controllers can be embedded in `agent.yaml`. Subagents are optional experiments, not the default source of capability. Cloud plugins administer development resources; they are not tools secretly available to the scored agent.

## Mathematical and numerical requirements

Let Y_i be independent-evaluator patch acceptance for task i and C_i its charged runtime. The deployment objective is maximize expected accepted repairs under the real global time limit and per-device memory constraints. Action choice is a partially observed decision problem, not a claim that we know true success probabilities. Begin with transparent fixed policies and instrument them before fitting a learned controller.

For a proposed next action, estimated marginal repair value divided by incremental time can inform prioritization only when estimates are calibrated and uncertainty is reported. It is not a proven optimal scheduler: actions have dependencies, unknown outcomes and discontinuous costs. Budget logic must reserve measured time for patch capture and cleanup. Cross-task allocation requires supported harness information; never inspect hidden evaluation assets to obtain it.

Context selection must obey the actual tokenizer bound: selected context tokens plus reserved output and protocol overhead must not exceed the configured context limit. Any retrieval surrogate (coverage, relevance or graph connectivity) must be ablated against repair outcomes; proving a surrogate property does not prove repair improvement.

For supervised tuning, use the explicit masked objective

\[
L(\theta)=-\frac{\sum_{j,t}m_{jt}\log p_\theta(a_{jt}\mid h_{jt})}{\sum_{j,t}m_{jt}},
\]

where m selects intended assistant target tokens, excludes padding and tool/environment observations, and the denominator must be positive. Preserve tool-call structure and verify truncation/packing boundaries. This token-weighted definition differs from averaging per-trajectory losses; record which is used. Validate masks by hand on tiny examples and compare loss against an independent reference. This objective improves imitation, not necessarily repair success.

For each adapted matrix, specify Delta W=(alpha/r)BA, with A of shape r×d_in and B of shape d_out×r, or document the exact alternative scaling used by the implementation. Freeze intended base parameters, audit trainable counts and gradients, check finite values and checkpoint restore, and compare adapter-enabled/disabled outputs. Quantized deployment and training can differ numerically; measure the deployed artifact, not only the training model. No full-model fine-tuning or RL cluster is assumed necessary.

If preference or RL training is later introduced, define rewards from independent task outcomes, retain failed/time-limited trajectories, and audit reward hacking, test modification, environment exploitation and data leakage. Reduced training loss or increased reward alone cannot promote a checkpoint.

For comparison, define d_i as candidate mean acceptance over declared seeds minus baseline mean acceptance for the same task; report the task-average difference. Repeated seeds do not create independent repositories. Predeclare task/repository grouping, uncertainty method, meaningful improvement or noninferiority margin, time/cost limits and stopping rule. Keep development selection and untouched confirmation separate. No adaptive significance checking without a valid sequential design; small cohorts support feasibility, not broad superiority claims.

Every substantive mathematical claim needs assumptions, derivation, implementation pointer, independent checks, numerical tolerances and known counterexamples. Exhaustively check bounded toy scheduling/selection instances where applicable. Do not claim a theorem for an LLM's arbitrary generated patches. The standards in document 12 apply to every phase.

## Model handoff: when and where

**Needed at P1, before the first real inference smoke test. P0 contract/schema/packaging work can begin without weights.** The user will download the model; do not start another full download automatically.

1. Download the complete selected variation, preserving its version and files. Current listing includes `model.safetensors`, `config.json`, `generation_config.json`, `tokenizer.json`, `tokenizer_config.json`, `chat_template.jinja`, `processor_config.json` and `README.md`; trust the actual version's manifest if it differs.
2. Keep weights outside Git. Suggested local destination: `/Users/jiangshengbo/Models/gemma-4-31b-it-qat-w4a16-ct/v2/`. This is a proposed destination, not an existing or populated directory. An archive can remain in Downloads until intake; do not rename the checkpoint into another format.
3. At P1, confirm the actual downloaded archive/folder path and Kaggle version with the user. Record file sizes and SHA-256 hashes, parse configuration, validate safetensors metadata and tokenizer/template assets. Local hashes establish subsequent identity, not publisher authenticity unless compared to a trusted upstream checksum.
4. Check free disk space for archive plus extraction plus caches. The 23.3 GB file listing is not peak RAM/VRAM demand. Use a small configured context and concurrency, then measure GPU memory before scaling.
5. Select a GPU and quote its live price and bounded allocation; transfer only after the destination is concrete. Recheck hashes after transfer. Preserve the source archive and a rollback checkpoint.
6. Pin exact inference dependencies and run actual generation, tool calls, workspace edits, tests and submission. Do not mark synthetic fixtures or file inspection as model acceptance.

Training begins later at P5. Before that, prove the training/export/quantized-loader round trip; identify any additional training weights separately. The local model path must never be serialized into a portable submission. Use only model references/mounts allowed by the official harness; do not assume bundling base weights is required.

## Provider activation and live plugin audit

Read-only checks on October 7; no billable resource was created and no settings were changed. Account identifiers and credentials are intentionally omitted.

| Provider | Verified result | Activation point and remaining test |
| --- | --- | --- |
| Runpod | Authenticated pod listing succeeded; returned empty list, no further pages (cluster members excluded by the request default) | P1 inference; P5 training. Prefer an on-demand Secure Cloud pod for bounded experiments. Confirm GPU inventory/price, storage, SSH/file transfer and external endpoint access separately. Listing success does not verify provisioning or model serving |
| DigitalOcean | Authenticated account read succeeded; status active, email verified, droplet limit 100 | P0/P2 when an isolated Linux worker is needed. Reuse a suitable explicitly identified workspace where possible. CPU/RAM/disk based on task images and concurrency; Docker/SSH capabilities still untested |
| Cloudflare | No callable Cloudflare tool exposed; plugin-directory search for Cloudflare returned no matches | Artifact backup can initially remain local/Runpod. Before R2 is needed, inspect available connection options; absence here does not prove no Cloudflare integration exists. No account/bucket/API call succeeded because none was available |
| Render | Not needed in initial build; not connection-tested | Optional later dashboard/coordinator, not an additional required provider |

The user authorizes plugin verification now and coordination when services are required. Spending ceiling is still unset; plugin verification is not authorization for unlimited rentals. Before a billable run, specify resource, live rate, maximum runtime/cost, persistent storage charges, shutdown behavior and required artifact backups. Read-only planning and local work can continue meanwhile. Do not terminate pre-existing resources based only on their names.

## First cycle and update protocol

P0 deliverables: official starter/harness inventory; supported tool/config matrix; proposed package layout; task-state/event schema; offline dependency strategy; meaningful contract/failure fixtures; evaluation split manifest skeleton; model-intake manifest schema. Preserve existing R1 evidence. No fake repair rates or fabricated model traces.

Before calling P0 accepted, obtain the official harness or mark the dependent contract checks unresolved. Before P1, confirm the model handoff with the user. After every 8–14-hour cycle, update document 12 with actual hours, artifacts, tests, failure analysis, metrics, costs, mathematical claim status, acceptance/promotion decision and next scope. A phase can span multiple cycles; no promise of unattended execution is implied.

Readiness now: planning and read-only checks complete; model access user-reported, model bytes pending; official runtime integration pending; provider compute not allocated; Cloudflare unverified; no Gemma training or measured repair performance yet.
