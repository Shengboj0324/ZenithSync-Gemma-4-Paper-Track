# Data requirements and acquisition plan

Research date: October 8, 2026. Proposed intake and experiment design, not an acquired or approved training corpus. P0 remains accepted; this document specifies P1–P6 data work. The user's preferred envelope is three candidates with up to 50 million processed tokens each. No GPU training, bulk corpus download, teacher API generation or R2 upload is initiated by this study.

## Decision

Prioritize executable repository tasks, audited multi-turn tool trajectories, and native Gemma experience collected through the competition tool interface. Do not start with a giant raw-code dump or fill a token quota by repeating a small number of solutions. Independent evaluators, provenance and reliable environments are as necessary as training examples.

The first corpus should be Python-focused because the inspected official runner and grading path use Python/pytest. Inspect task language metadata before finalizing the mixture; this is not a claim that hidden tasks are exclusively Python. Multilingual transfer is a later bounded experiment, not a reason to substitute incompatible runtime tasks.

## What we need and who may see it

| Asset | Required contents | Consumer and phase |
| --- | --- | --- |
| Model identity | Complete checkpoint, config, tokenizer, chat template, revision evidence, hashes; separate training representation if needed | P1 serving and P5 training; weights outside Git |
| Task inputs | Task ID, issue text, repository identity, immutable base commit, source snapshot, original tests available at that commit | Agent-visible P1–P6 |
| Environments | Image digest, architecture, dependency locks/wheels, setup recipe, test commands, resource caps, logs | Isolated executor; P1–P6 |
| Evaluator assets | Reference patch, verification test patch, required test IDs, baseline/reference receipts, protected-file policy | Evaluator-only; never mounted in evaluation-time agent workspace |
| Repository navigation | Graphs, embeddings, node map, generator version, source hash and base commit | Agent where supported; must match current task snapshot |
| Demonstrations | Ordered observations/actions, tool arguments/results, final patch, replay result, model and scaffold versions | SFT after conversion and validation |
| Native experience | Gemma trajectories including failures, timeouts, recovery, token counts and actual tool results | Failure analysis; selected successes/recoveries for SFT |
| Comparison data | Candidate identity, task outcome, budget, seed, latency, peak memory, setup failures and rejection reasons | Development and independently controlled confirmation |
| Governance | Source revision, licenses, notices, lineage, split assignment, transformation history, deletion/exclusion log | All phases |

Original repository tests and tests the agent writes are distinct from evaluator-only verification patches. Both can be useful, but passing the agent's own test is not sufficient acceptance. Gold patches are legitimate evaluator references and may support separately labeled training-only patch demonstrations; they must not be inserted into held-out prompts or used to fabricate a trajectory that appears unguided.

## Official package: exact inventory available now

The saved authenticated Kaggle listing, `artifacts/official/gemma-4-developer-agent/listing.json`, contains 524 entries. These are listed download sizes, not unpacked disk requirements or a fresh remote listing:

| Group | Files | Bytes |
| --- | ---: | ---: |
| tasks.jsonl | 1 | 1,984,455 |
| snapshots | 129 | 21,496,844,379 |
| graphs | 127 | 422,050,109 |
| embeddings | 127 | 467,546,088 |
| task wheels | 124 | 27,810,465 |

Those five groups total 22,416,235,496 bytes, approximately 22.42 GB decimal. The separately acquired host wheelhouse, model, expanded snapshots, environments and logs are additional. Guide/starter/Docker/setup assets are already acquired. Full task assets are not yet staged. Check the two fewer graph/embedding entries against task IDs and snapshots; do not infer which tasks lack coverage merely from counts.

First acquire task metadata into evaluator-controlled intake, expose only input fields to the agent, assign development/confirmation groups, then download a small authorized development subset of snapshots and matching dependencies. Never browse reference patches while selecting a supposedly untouched confirmation cohort.

## Ranked external sources

Counts and licenses below are publisher/card observations, not our validation results. Pin dataset commit SHA and count the actual selected files before ingestion. All sources require competition-use and upstream-rights review.

| Source | Evidence checked | Proposed role | Main qualification issue |
| --- | --- | --- | --- |
| [Nebius OpenHands trajectories](https://huggingface.co/datasets/nebius/SWE-rebench-openhands-trajectories/blob/main/README.md) | Card reports 67,074 traces, 32,161 successful; CC BY 4.0; Qwen3-Coder teacher | Primary candidate for real-issue demonstrations and failed-attempt analysis | Several trajectories per issue; OpenHands tool semantics differ; success labels need local replay |
| [NVIDIA SWE-Hero](https://huggingface.co/datasets/nvidia/SWE-Hero-openhands-trajectories) | 34,269 trajectories over 11,766 issues; CC BY 4.0 and repository-license metadata | Secondary source for diverse real-task traces | Derived from SWE-Gym, R2E-Gym and SWE-rebench; overlap is expected, not independent additional task diversity |
| [SWE-smith Python](https://huggingface.co/datasets/SWE-bench/SWE-smith-py) | 50,908 tasks, 131 repositories; MIT card; executable environments | Controlled synthetic bugs and replayable task generation | Synthetic bug/issue distributions can differ from real work; audit trivial mutants and answer-revealing issue text |
| [SWE-smith trajectories](https://huggingface.co/datasets/SWE-bench/SWE-smith-trajectories/raw/main/README.md) | MIT card; tool/XML/ticks representations; prose and metadata disagree on counts | Supplement after joining tasks and choosing a representation | Do not count serialization variants as independent trajectories; teacher-use terms and compatibility require review |
| [SWE-rebench V2](https://huggingface.co/datasets/nebius/SWE-rebench-V2/blob/main/README.md) | 32,079 tasks across 20 languages; CC BY 4.0 plus per-repository license | Broad environment pool for new native rollouts; Python subset first | Card explicitly warns other benchmark overlaps were not removed; do not assume older trajectory IDs join to V2 |
| [SWE-Gym](https://huggingface.co/datasets/SWE-Gym/SWE-Gym) | Paper describes 2,438 executable tasks over 11 repositories | Small environment-validation and recovery pilot | Narrow repository coverage and overlap with aggregate sources; verify current asset licenses before use |
| [R2E-Gym SFT](https://huggingface.co/datasets/R2E-Gym/R2EGym-SFT-Trajectories) | Viewer lists 3,231 rows; dataset README is empty | Defer direct ingestion | Insufficient card-level provenance/licensing/join documentation in the inspected page |

The [older SWE-smith monolithic card](https://huggingface.co/datasets/SWE-bench/SWE-smith/blob/main/README.md) recommends language-specific replacements and has conflicting prose/metadata counts. Use the Python-specific source for new task intake, while verifying compatibility of historical trajectories individually.

Research basis: [SWE-smith paper, collection/validation and experiments](https://arxiv.org/html/2504.21798v1) constructs executable bug tasks and filters with real tests. Its results motivate repository and bug diversity, not a promise of Gemma performance. [SWE-Gym paper, sections 2–3](https://arxiv.org/html/2412.21139v1) describes executable environments and success-filtered imitation. It reports a 6 TB full image collection, which is why our first intake uses a bounded image cache rather than every environment. These papers support the workflow; they do not validate our datasets or adapted agent.

## Native data that external corpora do not replace

Collect through the exact permitted tools and actual model chat template:

- Navigation: find definitions/callers, disambiguate similar symbols, recover when graph assets are missing, combine text search and graph evidence.
- Editing: exact replacement, ambiguous replacement recovery, multi-file consistency, imports, public API compatibility, new-file capture and cleanup.
- Verification: reproduce a behavioral failure, select relevant tests, handle dependency failures separately, interpret regressions, and submit the actual captured diff.
- Recovery: wrong hypothesis followed by observed failure and correction; timeout, truncation, unavailable tool, exhausted budget and checkpoint resume.
- Difficult behavior: numerical boundary conditions, shapes/dtypes, serialization compatibility, async behavior, caches, and cross-module contracts where runnable oracles exist.
- Evidence integrity: inability to run a test, partial validation, and honest status reporting; no fabricated command output or success assertions.

Use synthetic fixtures for exact protocol boundaries and security failures, with synthetic labels. Use real issues for capability measurement. Generate graph retrieval examples only from the correct snapshot; never manufacture an embedding score or fake a graph tool response. Train performance optimizations only where measured latency/resource evidence supports their labels.

Failures are valuable diagnostics and possible preference negatives, but do not blindly imitate every unsuccessful assistant action. For recovery SFT, preserve the causal context and real failure observations while selecting appropriate corrected actions as targets. A successful final patch does not establish that every preceding action was good.

## Canonical records and conversion

A task record needs: schema version, source dataset/revision, source row ID, canonical repository/fork family, base commit, issue timestamp, language, licenses/notices, task family, input hashes, environment digest, oracle references, split and exclusion status.

A trajectory record additionally needs: task ID, trace ID, parent trace if transformed, actor model/revision, scaffold/tool versions, generation settings, ordered messages, tool-call IDs/arguments/results, exit status, patch hash, evaluator receipt, processed/target/padding token counts, truncation/compaction events, timing and resource totals.

Keep raw immutable data and normalized examples separately. Never modify upstream records in place. Unsupported tool calls are not fixed by simply renaming their function: paths, argument semantics, shell state, persistent processes and output conventions can differ. Translate only operations with demonstrated equivalence, then replay. Regenerate traces where semantics cannot be preserved. Do not manufacture a reasoning narrative from a known patch and label it an actual run.

Tokenize with the exact deployed Gemma tokenizer/template. Supervise intended assistant tokens only; mask user/system/tool text and padding. Audit tool delimiters, call/result pairing, thinking-channel serialization, EOS and truncation. Masking a token from the loss does not remove its forward-pass cost. Do not cut the action away from the observation that justified it. Any converted, regenerated or compacted trajectory has a new identity and must pass its own checks.

For packed examples, block cross-example attention or use separate sequences; inserting EOS alone is not proof of isolation. Avoid repeatedly charging identical conversation prefixes without tracking the duplication. Match training examples to the maximum supported 32,768-token context; choose a shorter pilot length based on measured memory rather than assuming every example fits at maximum length.

## Quantity and the three-candidate experiment

Start with a qualification sample of approximately 500 traces spanning at least 100 distinct tasks and 20 repositories, where available after exclusions. Inspect a stratified manual sample and replay every example admitted to the initial high-assurance training set. This is a proposed intake target, not a statistical sufficiency claim. Scale only after conversion, oracle and licensing gates pass.

For the main campaign, aim for a pool with thousands of distinct tasks and at least 100 repository families; report achieved diversity rather than filling quotas with duplicates. A practical initial selection target is 5,000–15,000 vetted trajectories, but actual token lengths and replay yield determine the needed count. Reject unusable data even if the resulting corpus is smaller.

Distinguish:

- Unique raw tokens: material before repetition, with duplicate policy stated.
- Unique normalized examples: distinct examples after serialization and filtering.
- Processed tokens: all input tokens processed over epochs and repeated prefixes.
- Supervised target tokens: assistant tokens contributing to loss.
- Padding tokens and physical compute: report separately; kernels may still process padding.

For example, 50M processed tokens at 16,000 tokens per example presentation is about 3,125 presentations, not 50M distinct facts or 3,125 independent tasks. If each conversation becomes many overlapping windows, the unique task count is lower. Three runs may reuse a shared corpus: 150M processed tokens does not require 150M unique source tokens.

Provisional controlled campaign (millions of processed tokens; each column totals 50):

| Component | A: broad repair | B: recovery emphasis | C: difficult cross-module work |
| --- | ---: | ---: | ---: |
| Vetted real-issue public traces | 30 | 20 | 20 |
| Executable synthetic repair traces | 10 | 10 | 10 |
| Native successful routine repairs | 5 | 0 | 0 |
| Native failure-to-recovery traces | 0 | 15 | 0 |
| Native difficult multi-file traces | 0 | 0 | 15 |
| Native tool/protocol and testing examples | 5 | 5 | 5 |
| Total | 50 | 50 | 50 |

Use a shared, immutable 30M core comprising 20M real issues, 5M synthetic repair and 5M protocol/testing, if sufficient qualified material exists. The other 20M changes by candidate. Start all three from the same base/adapter initialization and hold optimizer, target modules and inference conditions fixed where possible. These are mixture comparisons, not isolated causal proof of one feature or three random-seed replicates. The 15M native components may be expensive to collect; do not silently replace them with unverified synthetic conversations. Adjust the experiment and record the reason if quality or budget limits prevent this plan.

Sampling must cap repeated traces per task and repository dominance; provisional maximum 5% of processed tokens per repository family. Review effects on rare tasks rather than enforcing a percentage mechanically. Select difficulty using training/development baseline outcomes, never confirmation outcomes. Keep failed/timeout attempts in the acquisition ledger so success filtering does not conceal collection cost or easy-task bias.

## Contamination and evaluation design

Split by connected groups BEFORE training-data transformations: repository/fork identity, issue family, duplicate/backported fix, normalized patch/source hashes, and near-duplicate text/code candidates. Exact hashes miss renamed copies; similarity flags require review. Every trajectory, generated sibling, graph, preference pair and augmented variant inherits the task's split. Deduplicate across source datasets, not just within each one.

Reserve the official 129 tasks for local development/confirmation initially; do not add them to SFT merely because a file is called training data. Existing document 5 proposes 20 pilot + 29 development + 80 confirmation, conditional on grouping and validity. Counts must change if related tasks cannot be separated safely. This split is not frozen yet. Any confirmation example viewed in detail, inspected via a dataset preview, or used to change a configuration must be excluded from the untouched claim or reassigned to development. Public reference solutions cannot establish base-model pretraining independence.

Build a separate external repository-disjoint confirmation cohort, initially targeting 200–500 valid tasks across at least 30 families if affordable. This is a breadth target, not guaranteed power. Include independently authored or recent licensed tasks when available, but timestamp alone does not prove absence of contamination. Store evaluation assets with separate access from training jobs; a bucket prefix alone is not an access-control boundary.

Use paired task outcomes with the same compute policy. If d_i = success(candidate,i) - success(baseline,i), report mean(d_i), discordant outcomes and repository-aware uncertainty. For illustration only, an independent Bernoulli rate near 0.5 has approximate 95% margin 1.96*sqrt(0.25/n): about 11 percentage points at n=80 and 4.4 at n=500. Paired differences have a different variance; repository clustering can widen uncertainty further. Do not advertise small gains from 80 tasks as conclusive.

Use development data to select the three candidates, then freeze the selected configuration before confirmation. If reporting all three confirmatory superiority tests, predeclare multiplicity correction or a valid simultaneous analysis. Seeds are repeated measurements, not new independent tasks. Keep all eligible tasks in the denominator and report infrastructure failures separately under a predeclared retry policy.

External benchmark scores are supplementary. [OpenAI's coding-evaluation audit](https://openai.com/index/separating-signal-from-noise-coding-evaluations/) describes problems even in widely used benchmarks; audited local tasks remain necessary. [BFCL](https://gorilla.cs.berkeley.edu/leaderboard.html) can provide tool-call regression checks and [Terminal-Bench](https://www.tbench.ai/news) broader terminal transfer checks, but neither substitutes for competition repair evaluation. Pin the exact release, verify licenses and overlap, and never train on their reserved evaluation tasks. Public leaderboard feedback is development evidence.

## Acceptance gates for every training shard

1. Provenance/license and competition-use status recorded; unresolved rights excluded. Dataset license, repository code license, teacher-model/output terms and redistribution rules are distinct checks. Preserve attribution and notices. An open model does not automatically license all generated output under every downstream condition.
2. Required task fields and immutable source/environment references complete. Agent inputs exclude gold patch, future commits, post-fix documents and evaluator-only tests. Audit caches and indexes too.
3. Baseline fails for the intended behavior; reference passes; required tests actually execute. Dependency failures, skipped tests and absent JUnit reports do not count as valid negatives/positives.
4. Replays verify the actual final patch in a clean environment. Reject grader tampering and placeholder fixes. Retain invalid tasks in a quarantine ledger, not silently removed statistics.
5. At least targeted regression tests plus relevant boundary/property tests for selected difficult tasks. More tests can improve evidence, not prove arbitrary correctness. Mutation checks on a sample assess whether tests reject plausible wrong fixes.
6. Tokenization, masks, packing, role order and tool schemas pass independent checks. Target-token denominator is positive; no padding loss; split groups remain disjoint.
7. Restore a sampled shard and its environment from retained artifacts; hashes match. No secrets, local .env contents or unnecessary personal data in traces/checkpoints.

The public Kaggle rules and staff-discussion pages returned no readable body in this research session. Prior document 11 records conditional permission for teacher distillation, but it is not blanket clearance for these sources. Before ingestion, recheck authenticated external-data/teacher/license clauses and archive the exact applicable wording. This is an unresolved source check, not a request to reaccept rules or a claim that external data is forbidden.

## Storage, acquisition order and remaining work

R2 layout proposal: `manifests/`, `sources/<source>/<revision>/`, `tasks/`, `trajectories/raw/`, `trajectories/normalized/`, `splits/`, `training-shards/`, `runs/`, `checkpoints/`. Keep evaluator-only material under separately restricted credentials or a separate private bucket. Never mount a bucket containing gold solutions wholesale into the agent. Save durable blobs and content hashes in R2; keep Git to code, schemas, small manifests and audit summaries. R2 read/list connection has passed; writes and restoration are not yet tested.

The 200GB Pod volume is a working cache, not a guarantee of space for all datasets. Our local model is approximately 23.30GB; official task downloads add approximately 22.42GB before expansion. Public compressed trajectory cards suggest GB-scale files, while executable images can require TB-scale storage. Download only needed image families and evict reproducible caches after confirming durable artifacts. Measure disk high-water marks during the intake pilot before choosing 500GB or more.

1. P1: finish model/version verification; stage a few development task inputs, snapshots, graph assets and dependencies; verify R2 write/read/restore and persistent storage.
2. P2–P3: validate real task environments and grading, generate untuned Gemma traces, freeze allowed source revisions and split groups. Keep Pod stopped during CPU-only intake where practical.
3. P4–P5: acquire small public trace samples, qualify licenses and conversion, replay them; create the training pilot with verified masks and adapter reload.
4. P6: construct the selected 50M mixtures from approved shards, benchmark actual throughput, then authorize the measured campaign cost. No token quota overrides data quality.

This research reviewed primary cards, the SWE-smith and SWE-Gym methodological sections, current publisher releases, and the locally inspected competition harness/inventory. It did not audit every corpus row, reproduce published performance, establish complete legal clearance, or prove zero contamination. Those remain intake evidence gates. No private user repositories or paid teacher services are required for the initial plan.
