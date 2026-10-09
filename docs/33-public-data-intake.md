# Public trajectory intake: pinned quarantine

## Complete native-context census

`scripts/census_trajectory_context.py` measured all 2,500 acquired histories using
the pinned native tokenizer and explicit pre-action projection, without truncation.
Evidence: `evidence/data/context-census-001`. All eight earlier native-mask cases
match exactly in projected-history hash, token-ID hash and length. Two count and
boundary tests pass; the core suite reports 127 passed and 15 Torch tests skipped.

The shard contains 120,914,948 serialized input-token occurrences, including
prompts and tool results. This is neither a deduplicated token total nor an
accepted training/assistant-target budget. Lengths range from 18,557 to 183,776;
nearest-rank median, p90, p95 and p99 are 44,981, 67,304, 76,710 and 105,933.
These are exact statistics for this nonrandom shard, not population estimates.

| Complete-history input limit | Histories within limit | Input tokens in those histories |
| --- | ---: | ---: |
| 8,192 | 0 | 0 |
| 16,384 | 0 | 0 |
| 32,768 | 250 | 7,329,112 |
| 65,536 | 2,215 | 97,660,228 |
| 131,072 | 2,486 | 118,751,749 |

No tool schemas or inference output reserve are included. A count within a limit
does not establish deployable context fit, GPU memory fit, valid masks or quality.
The 32,768 limit would exclude 90% of histories. NumPy and pandas contribute
205 of the 250 retained histories (82%), versus 64.48% before this filter.
Thus length-only selection changes repository composition and cannot be treated
as an unbiased reduction. The larger limits above are diagnostics, not qualified
runtime configurations.

Next admission work must evaluate the actual competition context policy and
match training inputs to it. Preserve the original histories; record every omitted or
compacted observation and the transformation identity. Do not admit naive tails
or fabricated summaries. Evaluate task replay and action quality after any
transformation, with per-repository retention and failure counts.

If action-level examples repeat earlier prefixes, assign each original target
token to one loss-bearing occurrence, or explicitly account for its multiplicity.
Repeated prefix tokens used solely as context remain masked. The proposed
token-mean objective is `sum(target losses) / number of assigned target tokens`;
averaging examples equally instead weights short actions more heavily. This
bookkeeping does not make changed contexts equivalent to the original history:
that separate semantic question requires replay. No context transformation or
training admission is claimed by this census.

## Competition compaction behavior and local-driver correction

The acquired `HARNESS_README.md` section 7.2 specifies ADK event compaction with
interval 5, overlap 2, token threshold 14,336 and raw event retention 5. Cache
settings are minimum 2,048 tokens, TTL 1,800 seconds and interval 10. These are
organizer documentation settings, not proof of hidden execution.

The local `run_p1_repair.py` previously omitted both settings. Released
`EvalConfig` defaults both to `None`; the harness passes them to ADK only when
supplied. The driver now supplies them through `zenithsync/harness_context.py`,
requires ADK 1.36.1, and records settings and helper identity in attempt receipts.
Existing attempts retain their recorded scope but did not exercise this policy.
Deployment bundle 006 includes the helper and passed archive identity checks
and isolated CLI import/help outside the repository.

`scripts/probe_harness_compaction.py` verifies installed summarizer bytes against
the pinned wheel and records its actual request with an offline recording model.
In the three-event fixture, task and assistant text reach the summary prompt;
structured tool-call arguments and tool-result content do not. The returned
compaction interval spans all three timestamps. This proves omission during
summary-input formatting, not actual runner deletion, real summary quality or
end-to-end loss of a repository fact. The output is explicitly synthetic test
data, never a generated training example. Evidence:
`evidence/p1/harness-compaction-002`; formatting-only probe 001 is retained.

ADK defines the interval in user-initiated invocations, not tool calls. Although
its config docstring describes a post-invocation token trigger, the pinned
request processor also invokes token compaction before model calls inside an
invocation. Do not model this as deleting every fifth exchange. Collect real summary/continuation
pairs and evaluate recovery of required tool observations. A custom Python
compactor is not an established declarative competition submission feature;
alternatives first require a supported deployment path.

### Actual runner integration probe

`scripts/probe_compaction_runner.py` uses the real ADK Runner, session service,
LlmAgent, six executed local observation-tool calls, and the documented settings.
Model responses and reported token usage are explicitly synthetic. Installed
runner, compaction, contents and summarizer sources match the pinned wheel.
Each case has one user invocation and seven agent requests.

| Case | Synthetic reported prompt tokens | Summary requests | First observation in final agent request |
| --- | ---: | ---: | --- |
| Enabled, below threshold | 14,335 | 0 | Yes |
| Enabled, at threshold | 14,336 | 5 | No |
| Disabled control | 14,336 | 0 | Yes |

In the threshold case, compaction begins before the fourth agent request; the
first observation disappears before the fifth. Final agent input retains
observations 4–6. No structured observation sentinel appears in any summary
request. All six original response events remain stored in the session: this
is active-context exclusion, not deletion of the stored record. Four summary
requests occur during the loop and one after it completes.

Evidence: `evidence/p1/compaction-runner-002`. The fixture intentionally reports
the threshold on every response, including synthetic summaries, so five summary
requests is a test result, not a forecast of production frequency or cost.
It neither measures actual token lengths nor tests real summary quality,
SWE-gemma integration, hidden grading or repair gains. The next collection must
capture actual compaction requests/responses and resulting agent inputs, and
test repository-backed observation recovery without leaking future outcomes.

### Experimental source-observation skill

`candidates/p1-observation-memory` is a separate, untrained candidate; the base
candidate remains unchanged. The official compiler supports Python scripts in
ADK skills, so this capability does not require an unsandboxed callback. Its
`source-observations` skill stores bounded exact source excerpts with whole-file
SHA-256 and inclusive line locations in temporary files outside the repository.
Recall checks record integrity, workspace identity, current file hash and exact
excerpt agreement. Any file change, including outside the excerpt, returns a
stale status without presenting the old excerpt as current. Missing files fail.
Hashes do not authenticate who created a record or establish semantic correctness.

Five tests cover Unicode/CRLF preservation, no repository writes, staleness,
corruption, workspace mismatch, traversal, symlinks, line bounds and size bounds.
The pinned compiler accepts the candidate; the actual ADK materialization wrapper
successfully snapshots and recalls across separate Python processes, then rejects
freshness after a source edit. Evidence: `evidence/p1/observation-skill-001`.
Registry bindings in this probe are nonexecuting fixtures; the production sandbox
executor, model skill selection, handle retention after compaction, tool costs,
patch exclusion and repair gains still need end-to-end qualification. This is
source recovery only, not automatic archival of every tool result or test outcome.

The first compiler probe stopped on a version mismatch: the general local
environment contains swegemma 0.2.7 and adk-submission 0.2.12. An isolated overlay
now uses 0.2.10 and 0.2.13 with ADK 1.36.1. A probe-only YAML parsing error was
also fixed by using the official include-aware loader. The earlier compaction
probe 002 used the correct ADK but the older harness for its EvalConfig check;
`evidence/p1/harness-compaction-003` revalidates that check and the formatting
result under all three pinned versions. Prior runner-only ADK evidence does not
depend on swegemma. These corrections do not establish complete runtime parity.

### Released Docker executor and patch-exclusion check

`scripts/probe_observation_sandbox.py` compiles the candidate with the actual
bound SWE-gemma tools and `AdkSandboxCodeExecutor`, then invokes ADK's actual
skill materialization/execution helper in an owned Linux container. The local
image is pinned, networking is disabled, there are no host mounts, and limits
are 4 GiB / two CPUs. The fixture contains only a synthetic source file.

Exact Unicode source recall succeeds across separate executor processes. The
record lives under `/tmp`; the repository is clean after snapshot and recall,
including untracked files. A source edit through the released `write_file` tool
invalidates the snapshot. Released `submit_patch` produces exactly one source
diff, with no memory record or executor-script artifact. Container cleanup is
verified separately. Evidence: `evidence/p1/observation-sandbox-001`.

This closes the Docker executor and patch-exclusion checks for this fixture.
Calls were deterministic and directly orchestrated, not chosen by a model. It
does not establish handle preservation through compaction, model skill use,
subprocess-backend parity, repair improvement or training readiness. Before any
comparative GPU trial, connect this recovery path to the pinned runner's actual
compaction flow and account separately for tool calls and summary requests.

### Integrated compaction/recovery and cost controls

`scripts/probe_observation_recovery.py` runs the compiled candidate with real
bound tools, actual ADK compaction and the released Docker executor. The source
contains a fresh per-case random marker; the scripted model receives it only
through actual tool responses. Before recall the probe asserts that this marker
is no longer in the active request. Recall arguments use only handles visible
in that request, not a separately retained fixture variable.

| Synthetic summary policy | Exact source recovered | Agent requests | Summary requests | Skill executions | Harness tool count |
| --- | --- | ---: | ---: | ---: | ---: |
| Copy visible handle | Yes | 10 | 8 | 2 | 9 |
| Drop handle | No | 9 | 7 | 1 | 8 |

Both cases also execute seven shell calls. Thus snapshot and recall each consume
one harness tool call through the executor's budget check; they are not free.
All observations remain outside the patch and the repository stays clean.
Both owned containers were removed. Evidence:
`evidence/p1/observation-recovery-001`.

This is a controlled integration result, not a statistical success-rate estimate.
The model policy and summaries are scripted; prompt usage is synthetically held
at the compaction threshold. Request counts are observed, but are not estimates
of real inference token usage or production frequency. Conditional mechanical
recovery works when a usable handle survives; the dropped-handle control shows
that storage alone does not solve memory loss. No evidence yet establishes that
Gemma will choose to record, retain, recall and correctly interpret observations.
The first model comparison must measure each of those outcomes, final repair
quality, tool costs and real token usage against the unchanged baseline. These
fixtures must never be admitted as model-generated training trajectories.

## Source tool-contract census and replay requirements

`scripts/audit_source_tool_contracts.py` audited all 2,500 acquired histories,
reading trajectory arguments but not `model_patch`. It preserves per-history
flags without copying command bodies into reports. Evidence:
`evidence/data/source-tool-contracts-001`.

| Observed source feature | Calls | Histories affected | Required treatment |
| --- | ---: | ---: | --- |
| Editor view of `/workspace` itself | 1,874 | 1,874 | Directory observation needs supported listing behavior, not `read_file` |
| Shell `is_input` argument | 231 | 122 | Qualify interactive-session semantics; do not rename to `run_command` |
| Shell `timeout` argument | 468 | 248 | Reconcile with the target's remaining-budget and command timeout rules |
| Empty shell command | 9 | 5 | Establish source waiting/input semantics before translation |
| Editor `undo_edit` | 6 | 6 | Requires original editor state; no native undo tool is registered |
| View range ending in `-1` | 298 | 245 | Explicit range conversion and observation truncation checks required |
| Editor `/testbed` paths | 10 | 4 | Verify source repository root before any path mapping |
| Editor temporary path | 1 | 1 | Target workspace file tools cannot silently substitute a different location |

The 231 `is_input` values are strings, not booleans. Editor actions total
36,692 views, 14,274 creates, 8,791 replacements and six undos. Source tools also
include 6,923 `think` calls and 2,500 `finish` calls. Pure reasoning and terminal
actions need a declared target representation; `finish` does not establish a
successful patch or equivalence to native `submit_patch`.

These flags are not an exhaustive semantic classifier. Absence of a flag does
not certify shell-state, filesystem, output, timeout or failure equivalence.
Source path classification explicitly distinguishes `/workspace` from descendants
and lookalikes such as `/workspace2`. A focused boundary test is included.

The [linked paper, version 1](https://arxiv.org/html/2604.01496v1), section 3.1,
states that its SWE-Hero set retains trajectories regardless of task resolution.
It describes 13.2k Hero trajectories, while the pinned dataset card reports
34,269. Therefore the paper's exact release composition must not be assumed to
match this revision. Neither a terminal call nor the collection's name supplies
a missing row-level success label. Repository-state joins and independent replay
remain necessary before any successful-trajectory SFT admission.

For any proposed action mapping, replay must compare resulting repository state,
exit/failure behavior and the observation available to the next action. Formally,
matching argument schemas alone does not show that mapped source state transitions
equal target transitions. If one source action expands into several target actions,
record the expansion, intermediate observations and added cost. Do not reuse the
old next-action supervision as if those observations had actually been generated
by the target runtime. Regeneration under native tools is required when fidelity
cannot be established. No translation or training admission was performed here.

Status: one real shard acquired and metadata-audited; **no training approval**.
This work uses no GPU and executes no dataset content. It supplements the
[data plan](23-data-requirements-and-acquisition-plan.md), not the completed
synthetic model qualification.

## Reproducible sources

| Source | Exact revision | Acquisition |
|---|---|---|
| [NVIDIA SWE-Hero](https://huggingface.co/datasets/nvidia/SWE-Hero-openhands-trajectories/tree/150bc119e52c647216fce285fd801f16b6fd745b) | `150bc119e52c647216fce285fd801f16b6fd745b` | Publisher metadata, card and first Parquet shard |
| [Nebius OpenHands trajectories](https://huggingface.co/datasets/nebius/SWE-rebench-openhands-trajectories/tree/35455389ab51bf5e2306bfd436ef72d0f98bf882) | `35455389ab51bf5e2306bfd436ef72d0f98bf882` | Publisher metadata, card and LICENSE; no trajectory shard |

Publisher metadata lists 14 SWE-Hero Parquet files totaling 2,402,012,417 bytes,
and one Nebius Parquet file of 2,079,503,354 bytes. These are listed file sizes,
not acquired amounts, validated row counts or usable token budgets.

The acquired SWE-Hero shard is `data/train-00000-of-00014.parquet`,
151,791,408 bytes, SHA-256
`5149ba06dc7bcfe2fc01a20036e35cd535fde91840253c15bc070d95cf217be6`.
Its bytes matched the pinned publisher LFS identity. Small card/license files
matched their Git blob identities. Intake rejects excessive, truncated or
changed bytes before promoting a completed file; partial failures remain
quarantined. Four focused download tests passed.

## Actual metadata findings

The audit reads only `repo`, `license`, `instance_id`, `trajectory_id`, and
`dataset`, plus the Parquet schema. It does not read trajectory or patch bodies.
The shard has 2,500 rows, 2,500 distinct repository/issue pairs, 2,500 distinct
trajectory IDs, and eight repositories. All rows identify R2E-Gym-Subset as their
upstream dataset. Reported repository license labels are BSD-3-Clause (1,770),
MIT (266), and Apache-2.0 (464). These labels are not an independent upstream
rights audit.

Pandas and NumPy account for 1,612 rows (64.48%). Repository row concentration
is `sum_r (n_r/N)^2 = 0.2454832`; its inverse is 4.0736. This describes row-mass
diversity, not statistical independence or an effective evaluation sample size.
The first shard was selected by filename, so its distribution must not be
generalized to the full dataset or used as a representative training mixture.

No case-insensitive exact repository ID overlaps were found against the four
repositories in the current official task index. This does not exclude forks,
renamed repositories, semantic duplicates, or other public benchmarks.

The actual message schema has `content`, `role` and `tool_calls`, but no explicit
`tool_call_id` field. Direct ingestion into the native history validator is not
qualified. Before conversion, inspect upstream serialization and establish
whether response linkage can be reconstructed unambiguously; reject ambiguous
cases rather than invent IDs or fabricate tool outcomes. Preserve original
records and transformation provenance. There is also no row-level `resolved`
field in this shard's schema, so no success rate has been measured here.

## Admission and next actions

1. Check applicable competition external-data/teacher clauses and retain source
   wording; registration acceptance alone is not source-specific evidence.
2. Audit repository-license attribution, teacher terms and dataset notices.
3. Reserve evaluation repository/fork families and detect issue/patch overlap
   before selecting train/development groups. Do not inspect confirmation bodies.
4. Inspect tool serialization and define a faithful converter; compare native
   token rendering/masks and reject ambiguous or unsupported actions.
5. Replay a stratified development subset in isolated, versioned environments.
   Publisher labels and parse success are not executable correctness evidence.
6. Expand acquisition only with measured diversity, accepted rights, duplicate
   controls and actual native-token accounting. Do not substitute bytes or row
   counts for the proposed three 50M processed-token budgets.

Raw files live under `artifacts/data/quarantine/`. R2 publication uses
`quarantine/v1`; a prefix is an organizational label, not an access-control
boundary. Training jobs must consume an explicitly accepted manifest, never
scan the quarantine tree. Intake and audit receipts are under
`evidence/data/swe-hero-intake-001`, `swe-hero-metadata-audit-001`, and
`swe-rebench-metadata-001`. Publication receipts are separate and must be
checked before claiming durable backup.

## Structural conversion audit

`zenithsync/trajectory_import.py` now accepts the inspected SWE-Hero message
schema and preserves the four source tool names (`think`, `str_replace_editor`,
`execute_bash`, `finish`). It normalizes JSON argument representation through
the existing strict history validator without translating tool semantics.
For a response missing an explicit ID, it records an inferred link only when
exactly one source call is pending. It rejects parallel ambiguity, orphans,
interrupted exchanges, reused IDs, unknown tools and malformed arguments.
Null assistant content becomes an empty string; no user/tool content is replaced.

Each source trace ends with an unanswered `finish` call. The converter retains
that existing call and its unresolved status; it never creates a tool response,
invents a call ID, or assigns a successful task outcome. Five focused tests
cover preservation and rejection behavior.

The actual shard audit processed all 2,500 histories: 296,414 messages and
144,457 uniquely pending response links. All histories passed the stated
structural contract. Tool calls comprised 6,923 `think`, 59,763 editor,
77,771 shell and 2,500 `finish` calls. These are observed counts, not evidence
that the commands executed correctly or that all tasks were solved.

Unlike the earlier metadata-only audit, this pass reads trajectory bodies
programmatically. It still does not read the separate `model_patch` column,
execute commands or display bodies in the audit output. Per-row records retain
source and normalized-history hashes, linkage-provenance hashes and counts;
no normalized training shard has been approved or published. Evidence:
`evidence/data/swe-hero-conversion-audit-001` and
`evidence/data/trajectory-conversion-001`.

The unresolved terminal call requires an explicitly qualified native training
mask path; the current default mask helper requires complete exchanges. OpenHands
tool names also require semantic compatibility with the agent runtime, not a
blind rename. These remain gates before native tokenization, replay and promotion.

## Native terminal supervision and real-context lengths

The mask helper now has an explicit `terminal_call_tools` option. Its default
still requires all tool results. Opt-in requires one final call to a declared
terminal tool; interrupted earlier calls remain rejected. It preserves native
rendering and token IDs and adds no result. The native template's trailing
`<|tool_response>` delimiter remains unsupervised. Four contract tests and six
positive/six negative actual-tokenizer fixtures passed.

Eight real trajectories were selected before tokenization, one per repository,
by minimum SHA-256 of revision, NUL and trajectory ID, with ID as the tie-breaker.
No difficult case was replaced, and no history was truncated. All eight passed
native render/token identity and span-mask consistency checks. They range from
32,376 to 114,224 input tokens; seven exceed 32,768 tokens. All exceed the tiny
24-token input used in the measured H100 update. This is diagnostic selection,
not an estimate of the corpus-wide length distribution or success rate.

Evidence: `evidence/data/native-trajectory-masks-001`,
`evidence/p1/training-masks-002`, and `evidence/data/terminal-mask-tests-001`.
Only hashes/counts of these tokenized cases are retained in the audit, not an
approved training shard. No executable tool schemas were supplied to this
serialization diagnostic; source tool semantics remain unqualified.

Context-length handling is now a concrete admission gap. Do not silently cut
these traces to fit. Any windowing, retrieval or compression policy must also
exist in the agent runtime, preserve action/result linkage and task context,
record omitted material, and pass replay/quality checks. A source trace that
parses correctly is not automatically usable on the current GPU configuration.

## Source chronology: additional import defect and projection

Native-format consistency alone does not establish source-chronology fidelity.
The supplied template renders tool calls, looks ahead to consecutive tool results,
and then renders assistant `content`. For this source's mixed text-plus-call
messages, naive conversion therefore places pre-action text after the result.
The original native-mask audit remains valid for its narrower predicates; it
must not be interpreted as a complete semantic conversion qualification.

The full shard has 106,407 nonempty assistant-text messages with calls, of which
104,196 are followed by a tool result. `zenithsync/gemma_trajectory.py` provides
an explicit projection for the inspected single-initial-user format: it moves
the exact original text into the native `reasoning` field, records source/destination
field and text hashes, and leaves call IDs, tool names, arguments and results
unchanged. This is a declared transport convention, not a claim that the source
originally stored a private reasoning channel. Multiple/later user turns and
pre-existing reasoning fields are rejected rather than silently losing text
through the native template's last-user reasoning guard.

A synthetic native-tokenizer fixture reproduces the naive ordering problem.
After projection, the pre-action text precedes the call, which precedes the
result. Both rendered text and token IDs preserve the prefix through the pending
response delimiter. Changing the future result leaves that earlier token prefix
unchanged, and future result content remains outside assistant labels. An early
probe compared a structured `BatchEncoding` instead of explicit token-ID lists;
that test error is retained separately and was corrected before the passing run.

All 2,500 histories satisfy the projection's stated structural preconditions,
with 106,407 recorded field mappings. The same predetermined eight traces also
pass native render/token identity and mask checks after projection. Their new
lengths are 32,475–114,391 tokens, totaling 393,999, still with seven over 32,768.
No easier examples were substituted. Four projection unit tests pass.

Evidence: `evidence/data/gemma-causal-native-001`,
`gemma-causal-native-failure-001`, `gemma-causal-projection-001`,
`swe-hero-conversion-audit-002`, and `native-trajectory-masks-002`.
These checks qualify a candidate import convention, not full runtime equivalence,
task replay or training approval. Use the causal projection before evaluating
context reduction; do not promote the naive mixed-content representation.

## Source task identity join

Acquired all eight `R2E-Gym/R2E-Gym-Subset` Parquet shards at revision
`2e8108ff942f24fcb5686badfaf7f9a8808566d5`: 4,578 tasks and 943,928,047
compressed shard bytes. Each file passed its publisher SHA-256 and byte-count
check. The card declares Apache-2.0; this does not independently clear all
repository, generated-content, or competition-use rights.

`scripts/audit_source_task_join.py` verifies intake identities, rejects duplicate
task/trajectory identities, and joins all 2,500 acquired Hero trajectories with
zero unmatched rows. This is an exact instance-ID plus repository-basename join;
publisher repository ownership and actual image contents remain unverified.

Crucially, `commit_hash` identifies the solution commit. All joined source
`old_commit_hash` fields are first-parent expressions (`solution_commit^`), not
resolved hashes. The projection records `base_ref` and leaves `base_commit` null.
Before execution, resolve that reference in a pinned repository, verify ancestry,
resolve the image to an immutable digest, and check its actual working-tree state.
Do not substitute the image tag or solution commit as the buggy starting state.

The allowlisted projection exports no reference diffs, generated test code,
source prompt, or problem text; it retains only a problem-text hash for later
identity checks. Raw source shards contain oracle material and must stay in
quarantine, outside agent-accessible storage. The current join is not a training
dataset or an executable replay manifest.

Primary implementation inspected at R2E-Gym repository revision
`0d94c4eb9431cd195c55a7ea3abd54006c9a1735`,
`src/r2egym/repo_analysis/repo_testextract.py`: image construction tags the new
commit while passing the old reference as a build argument. Source:
https://github.com/R2E-Gym/R2E-Gym/blob/0d94c4eb9431cd195c55a7ea3abd54006c9a1735/src/r2egym/repo_analysis/repo_testextract.py

Evidence: `evidence/data/source-task-join-001`; raw intake receipts
`evidence/data/r2e-gym-shard-000` through `007`. Four focused metadata tests
cover oracle exclusion, mismatched identities, duplicate JSON keys, and unresolved
parent references. Core suite: 152 run, 137 passed, 15 skipped. Replay, ownership,
privacy filtering, quality selection, and native-runtime conversion remain open.

Follow-up source inspection: the pinned pandas image recipe performs a normal
Git clone and checks out the old reference without stripping later Git objects;
it also copies generated grading tests into `/r2e_tests`. The pinned runtime moves
those tests and creates a workspace symlink back to them. This establishes an
isolation concern in the recipe, not a demonstrated leak in our agent runtime or
an assertion that every historical image has identical contents. Actual replay
must inspect image contents and separate evaluator-only files and solution Git
objects from the agent process. Relocating files alone is not access isolation.
References in the same pinned repository: `base_dockerfiles/Dockerfile.pandas`
under `src/r2egym/repo_analysis`, and
`src/r2egym/agenthub/runtime/docker.py` (environment setup).

### Registry resolution and first concrete isolation check

All eight raw task shards and associated metadata are now in R2 quarantine with
full remote checksum readback: 943,967,191 verified bytes across publication
receipts `r2e-gym-publish-000` through `007`. This is storage verification, not
training admission.

`resolve_source_environments.py` selects the first joined trajectory for each
repository, without replacing failures. All eight GitHub Git-object reads resolved
the first parent, and all eight Docker Hub tags resolved to digest-verified Linux
amd64 manifests/configs. The NumPy solution has two parents: using the first parent
is intentional and matches the source's `^` expression. Metadata resolution does
not validate image contents, signatures, dependencies, or task execution.

Compressed layer sizes range from 333,661,594 to 1,412,467,649 bytes. To limit local
storage use, only the first repository in sorted order, Pylons/pyramid, was pulled:
`namanjain12/pyramid_final@sha256:b2c2fb0d461558aacbdb7352ba1d064d5abf480cb47be7b6074e5a3357360481`.
`probe_source_image.py` inspected it locally with network disabled, a read-only
root filesystem, no host mounts, all capabilities dropped, and bounded resources.
The image default user is root. Both HEAD and the solution's first parent matched
`2ad426fdb01b445a52aebcbc879dced9ef7ba6bc`. However, `git cat-file -e` could access
the solution commit, `/r2e_tests` was readable/searchable, and `run_tests.sh` was
readable. No solution patch, generated test, or agent was executed. The owned
container was removed successfully.

This is direct evidence that this source image cannot be admitted unchanged to
our agent. It is not evidence that an existing trajectory exploited these paths.
Next create and verify an agent-visible snapshot without solution Git objects or
grading artifacts, and retain an independent evaluator environment. Revalidate
source imports and tests after sanitization; removing files is not sufficient
proof of correct execution.

Evidence: `source-environment-resolution-001` and `source-image-probe-001` under
`evidence/data`. The metadata resolver's digest, platform, and parent handling
tests pass; the core suite has 140 passed and 15 skipped. Join output `002` removes
redundant blank lines from JSONL while preserving the same 2,500 records; output
`001` remains historical evidence.

API references: https://docs.github.com/en/rest/git/commits and
https://distribution.github.io/distribution/spec/api/ .

### Sanitized snapshot and evaluator controls: Pyramid only

Built a local sanitized image from the pinned Pyramid source image. The builder
replaces `.git` with one new baseline commit, removes declared grading artifacts,
and rebuilds Git blobs/index/tree directly without content filters. All 891
tracked paths (6,024,509 bytes) retain the exact original tree identity
`8a23c23faec496b81df0517237d7ed8d77e03b59`. The new baseline commit is
`dee40c5a59ed5d457c7143d476c1b17263845777`; its fixed timestamp is deliberate
snapshot metadata, not an assertion about historical authorship. Fresh-container
checks reject access to the solution commit and find `/r2e_tests` absent.

Local image ID:
`sha256:397c5e0c8991ee3d2ab594052f66e9fd2cf2d9df45a67fd1a6445e00caf6fea1`.
Its exact build input is `artifacts/official/source-snapshot-build-001`, including
the qualified sanitizer copy. Subsequent source preflight hardening is tested
locally but does not retroactively change this built image's code identity.
The original image remains the independent evaluator source. Docker lower layers
still contain original data; isolation assumes no container-engine access, host
mounts, or network access from the agent. This is not a scrubbed public image
distribution and must not be described as one.

`compare_source_snapshot.py` ran all collected original repository tests in two
separate local containers: 2,470 case identities, 2,433 passed and 37 failed on
each side, zero changed outcomes. Both import Pyramid from `/testbed/pyramid`
and leave tracked source unchanged. The 37 shared failures remain unresolved;
paired equality demonstrates only observed preservation under this environment.
No generated grading tests or agent ran during that comparison.

`qualify_source_evaluator.py` then ran separate evaluator controls at the actual
base and solution commits. It collected 994 cases from the source grading suite:
base 911 passed/83 failed; reference 930 passed/64 failed. A blanket all-pass rule
would misclassify this dataset. The pinned publisher expects 924 passed and 64
failed under 988 shortened Class.method keys. Seven distinct module-qualified
tests share `Test_main.test_it`, accounting for the six-case difference.

`source_evaluator.py` keeps full case identities and requires every member of a
publisher group to equal its expected status, with exactly matching group sets.
This avoids last-write-wins masking of a failure. Under this stronger predicate,
the base has 19 disagreements and the reference has none. All seven colliding
cases pass. This qualifies the positive/negative controls for this single task;
it does not establish exact upstream log-parser parity, test completeness, or
agent success. Expected failures are preserved as part of the source contract,
never recoded as passing tests.

`audit_source_expectations.py` verifies all source shard hashes, finds exactly one
matching task, records shard/row provenance, and checks control source revisions
before comparison. Evidence directories: `source-snapshot-build-001`,
`source-snapshot-comparison-001`, `source-evaluator-controls-001`, and
`source-expectations-001`. All owned test containers were removed. No Runpod
compute was used. Next integrate native agent tools with the sanitized workspace
and evaluate exported patches only in the separate evaluator environment.
