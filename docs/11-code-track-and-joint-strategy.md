# Code competition and joint strategy

Updated October 7, 2026. The project now targets both the agent competition and the paper track. Build one reproducible agent platform, preserve a frozen research version for the paper, and continue improving a separate competition version afterward. A research idea earns a place in the final agent only if it improves the relevant repair performance under the real execution constraints.

## What changes strategically

The tracks share a problem domain, but not an objective. Code placement depends on private evaluation performance; paper selection depends on the quality of the research contribution. A conventional method can be an excellent code entry. A carefully explained negative result can be a useful paper while being inappropriate for the final agent. Do not manufacture a weighted average of leaderboard score and paper rubric: there is no official joint score.

The earlier graph-reliability proposal remains a candidate research study. It is no longer the mandatory architecture or the project's entire critical path. The code baseline must be allowed to win our internal comparisons. Prioritize correct packaging, working tool calls, bounded execution, and valid patches before adding new retrieval machinery or training.

## Verified code competition contract

The [official overview](https://www.kaggle.com/competitions/gemma-4-developer-agent/overview), [rules](https://www.kaggle.com/competitions/gemma-4-developer-agent/rules), and [data description](https://www.kaggle.com/competitions/gemma-4-developer-agent/data) were inspected on October 7.

| Item | Current requirement |
| --- | --- |
| Objective | Fraction of evaluated issues whose patches pass validation; final ranking uses the private leaderboard |
| Entry and team merger | November 25, 2026, 23:59 UTC / 15:59 PST |
| Final code deadline | December 2, 2026, 23:59 UTC / 15:59 PST |
| Submission limits | One per day; select up to two final submissions; maximum five team members |
| Prizes | $37,000 / $18,000 / $10,000 |
| Payload | `submission.zip`, with root `agent.yaml`; restricted ADK configuration |
| Base model | `gemma-4-31b-it-qat-w4a16-ct` for every agent and subagent |
| Adapters | Optional PEFT LoRA directories with configuration and safetensors weights |
| Execution allowance | Twelve hours across all tasks, including sandbox setup, excluding patch validation |
| Runtime | L4x4 access, 96 GB aggregate memory, offline sessions; documented doubled notebook quota usage |
| Winner obligations | Apache 2.0 terms and reproducible source/environment delivery |

The data page describes approximately 120 hidden tasks split evenly between public and private subsets. Use 120 for conservative planning, not as a guaranteed exact count. A [participant discussion](https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/746008) also interprets the allowance as covering both subsets; that statement is not a host clarification. Confirm exact task-count exposure and budget accounting in the authorized harness before implementing scheduling.

Paper deadlines and judging requirements remain in [competition facts](01-competition-facts.md). Joining one track does not establish that the other registration or submission is complete. Verify each separately.

## New operational evidence

| Source | What was observed | Planning implication |
| --- | --- | --- |
| [Participant experiment report 746250](https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/746250) | Author reports no gain for the tested graph integration, empty semantic searches, sensitivity to reasoning settings, and repeat-run variation. Hardware and time caps differ from hosted evaluation. | Test graph-tool functionality and actual L4 timing. Reproduce directions locally rather than adopting the reported settings or treating the results as universal. |
| [Staff rerun notice 743683](https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/743683) | Staff discusses resource failures and a paused rescore; confirms the notebook must first produce the ZIP for scoring. | Reserve calendar slack and preserve scored artifacts. Do not assume retries are immediate or that an invalid notebook consumes no submission opportunity. |
| [Staff distillation reply 742807](https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/742807) | External models are allowed subject to their licenses and compatibility with competition licensing. | Teacher-generated training is conditional; this does not authorize every provider, data upload, or deployed inference model. |

Do not adopt a participant's proposed runtime as an official cap. The overview excludes patch validation from the agent allowance; observed notebook wall time can include other overhead. Measure the distinct clocks and resolve inconsistencies with the current harness. The staff thread leaves hosted scoring's impact on personal GPU quota unanswered in the inspected replies.

## Optimize repairs under a shared deadline

For `n` tasks, let `Y_i∈{0,1}` denote accepted repair. The benchmark objective is

\[
\hat S=\frac1n\sum_{i=1}^nY_i.
\]

For planning, let `p_i(t_i)` be the chance of solving issue `i` with active allowance `t_i`, `s_i` setup/other charged overhead, `T_0` global charged startup, and `R` a reserve. A useful allocation model is

\[
\max_{t_i\ge0}\sum_i p_i(t_i)
\quad\text{subject to}\quad
T_0+\sum_i(s_i+t_i)+R\le43{,}200\text{ seconds}.
\]

This sum assumes sequential charged time. If concurrency is supported, measure the harness's actual accounting and throughput rather than substituting a presumed parallel speedup. Four GPUs used for tensor parallelism are not automatically four independent task workers.

If the `p_i` were known, differentiable, increasing, and concave, an interior optimum would equalize marginal returns `p_i'(t_i)=λ`. Those assumptions generally fail for repair: a long test or a two-step fix can produce discontinuous benefits. The equation motivates measured allocation; it does not prove a greedy scheduler is optimal. Use coarse development strata and capped rules rather than a high-dimensional estimator trained on a few dozen issues.

Under a planning case of 120 tasks, the raw budget averages six minutes per task **before setup and reserve**. Suppose `T_0=0`, setup averages 30 seconds, and the reserve is one hour. The remaining active budget is 300 seconds per task. A 270-second active cap leaves another 30 seconds per task for uncertainty: `120×(270+30)=36,000` seconds, plus a 3,600-second reserve totals 11 hours. This is an illustration, not a recommended production cap until measured. Six minutes active plus that setup totals 13 hours; twelve minutes active totals 24 hours even before setup.

The previous 12-minute run assumption estimates research compute only. It does not authorize that allocation in a scored run. Do not solve this mismatch by simply cutting tool calls in half: compare short reasoning, concise tool output, repeated-command detection, targeted testing, and patch preservation to find which reductions lose the fewest repairs.

If the harness exposes remaining time and remaining tasks and permits control, bound the next task's allocation using

\[
t_{\mathrm{next}}\le\max\left(0,\frac{B_{\mathrm{remaining}}-R}{n_{\mathrm{remaining}}}-\hat s\right),
\]

where remaining time already excludes consumed startup. Use a conservative setup estimate and a cap on any extra retry. This is a feasibility heuristic, not an optimal policy. If future-task information or cross-task control is unavailable, use supported fixed per-task caps. Do not invent a scheduler hook or inspect hidden evaluator files to obtain it.

## Reliability has direct score value

Separate per-task failures from whole-submission failures. As a planning example, a configuration with a 5% whole-run failure probability and a 45% conditional repair rate has expected utility `0.95×0.45=0.4275` if an invalid run is assigned zero utility. A stable 44% configuration is then preferable on this model. Invalid-run utility is our planning convention, not a claim about Kaggle's exact error-score display.

Use this argument to justify runtime reserve and early packaging tests. Do not assign empirical crash probabilities without repeated full-run evidence. With roughly 60 tasks in a scored public subset, one task is about 1.67 percentage points; small changes in public score are coarse and can reverse on the private subset. Rank changes are not scientific evidence of a causal improvement.

## Implementation sequence for the next round

| Stage | Deliverable | Promotion gate |
| --- | --- | --- |
| C0 | Reproduce official starter using authorized assets | Valid ZIP, model loads, declared tool calls work, grader controls pass |
| C1 | Reliable single-agent loop | Bounded calls/time, concise outputs, no repeated-command loops, patch captured before exit |
| C2 | Sampling and reasoning comparison | Same hardware and total budget; repeated development evidence; actual reasoning behavior verified |
| C3 | Lexical/semantic/graph retrieval comparison | Semantic tool returns meaningful results; provenance checks; incremental gain after cost |
| C4 | Targeted SFT/LoRA candidate | Compatible loader, licensed data, no holdout leakage, gain over untuned champion under identical inference budget |
| C5 | Selective analyzer or alternate repair attempt | Positive marginal repair value after all extra tokens and time are charged |
| C6 | Full-run qualification and final selection | Offline replay, stable memory/runtime, immutable artifacts, two deliberate final selections |

Training and graph retrieval are independent candidates; neither must wait for the other if resources and data permit, but neither displaces C0–C1. Full RL is optional and requires a functioning reward/evaluator and enough trajectory budget. Mathematical sophistication should solve an observed bottleneck rather than introduce unidentifiable components.

The core loop should inspect, localize, edit minimally, run targeted local checks, compare with the last retained candidate, and submit a patch within the limit. Retain candidates using allowed local evidence only; hidden acceptance tests cannot select patches. An apparent local pass does not establish independent correctness.

## Map the method to permitted capabilities

The overview lists `run_command`, `submit_patch`, `get_status`, file read/edit/write operations, code-neighbor lookup, semantic search, and induced-subgraph retrieval. It also describes sandboxed skills and declared `agent_tool` subagents. Every implementation must use the supported interfaces rather than an arbitrary replacement runtime.

| Planned component | Intended route | Verify before implementation |
| --- | --- | --- |
| Lexical search and syntax checks | Sandboxed command or skill script | Dependencies available offline; commands included in budget |
| Seed symbols and structural neighbors | Official semantic and neighbor tools | Empty-result behavior, symbol IDs, direction and caps |
| Evidence-bundle selector | Declared sandbox skill | Whether graph data can reach the script; allowed mounts and resource access |
| Budget checks | `get_status` and supported evaluation configuration | Scope of reported time, task limits, timeout/patch persistence behavior |
| Adapter specialization | Declared agent/adapters configuration | Quantized-base compatibility, routing, memory and load overhead |

Do not assume the skill process can access the host's graph objects. If it cannot, use permitted tool outputs or a simpler harness-compatible variant and identify it separately in the paper. Do not build a standalone graph system and postpone the integration question until submission week.

## Artifact and release checks

The eventual bundle should have a root `agent.yaml`; any prompts, sampling files, skill manifests/scripts/resources, subagent definitions, and adapters it references; and an `eval_config.yaml` only with verified supported fields. Include paths must resolve inside the archive. Do not package raw private data, credentials, reference patches, evaluation tests, or unused large assets.

Use a versioned Kaggle notebook or the current officially supported submission route to produce the exact payload. The staff reply confirms that saving/running the notebook to generate `submission.zip` precedes notebook-based scoring. The data description's generated `submission.parquet` is evaluator output, not a replacement for the specified agent archive. Exact current notebook paths and commands require the gated harness guide.

Before spending a submission opportunity, check:

1. Archive root and include paths; no escaping symlinks; parse/compile against the actual restricted configuration schema.
2. Supported base model for every agent; adapters and required libraries present offline.
3. Smoke tasks for read/edit/test/submit, no patch, invalid tool, exhausted budget, and new-file patch capture.
4. Clean-run replay with no cached secrets or gold artifacts; full cohort timing on target-equivalent hardware.
5. Task failure isolation, retained patch behavior, and final output existence under the actual timeout semantics.
6. Artifact checksum, notebook/version ID, harness version, intended hypothesis, local evidence, and submission result logged.

Use at most the allowed daily submission count. Every submission should answer a question that local evaluation could not answer—principally compatibility, target-runtime behavior, or distribution transfer. Do not optimize by reconstructing hidden tests or repeatedly tuning to a single public leaderboard fluctuation.

Preserve the paper holdout during qualification: before research freeze, simulate the full workload using development or separate authorized tasks. Repeated cold-start episodes can stress time and packaging but do not provide independent accuracy evidence or complete domain coverage. See the split protections in [evaluation protocol](05-evaluation-protocol.md).

## Protect the paper while improving the agent

Freeze a research configuration, data split, and run table before writing the paper. Preserve its hash and label all paper figures accordingly. The code champion may subsequently change prompts, adapters, or retrieval policy without rewriting historical paper results. Maintain two version labels, such as `paper-freeze-2026-11-02` and `code-candidate-YYYY-MM-DD`; these are planned labels, not existing tags.

After the paper freeze, using former paper holdout examples for training would contaminate future evaluations on those examples. If such reuse is permissible and chosen for the code entry, keep the historical frozen paper evidence intact, mark the changed training provenance, and establish a fresh development holdout for later claims. Never describe post-reuse evaluation as untouched.

For final code selection, prefer the strongest stable candidate supported by local and external evidence. Use the second permitted selection for a credible alternative with different failure behavior only if its own evidence is competitive. Two final selections are not an ensemble or permission to combine per-task successes using hidden labels. Finalize and verify selected submissions before December 2, with a November 29 internal target to absorb queues and failures.
