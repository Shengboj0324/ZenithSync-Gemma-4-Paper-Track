# Failure task cards and source audit

**Subsequent evidence:** [R1](18-reproduction-cycle-results.md) records actual reproduction and three baseline trials for F03's Raft case. F01's repository/archives were inaccessible. The evidence labels below preserve the earlier literature audit; use R1 for current experimental status.

Inspected October 7, 2026. Companion to the [study](15-failure-first-research-study.md) and [replication protocol](17-replication-and-selection-protocol.md). No benchmark was executed locally. All cases whose solutions are discussed here are exposed development cases, never untouched holdouts.

## Evidence labels

- **Published aggregate:** author-reported performance; does not establish an individual failure mechanism.
- **Published case:** concrete task and attempt discussed by its authors; execution not independently inspected here.
- **Trace inspected:** attempt log opened and read in the browser; evaluator outcome remains externally reported.
- **Reproduced:** our pinned environment demonstrates the original failure and validates its oracle. No case presently has this label.
- **Confirmed improvement:** matched, independently evaluated comparison. No proposed method presently has this label.

## F01 — asynchronous form edits disappear

**Evidence: trace inspected.** [AB-9 task](https://web-debug-bench.replay.io/failures/56d9d255-2eec-4f37-9315-576f0607c30c) identifies stale React state in `FollowUp.tsx`. It lists repository [replayio/app-building](https://github.com/replayio/app-building), branch `app-building-mszga8`, failing abbreviated revision `ca9205be`, fixed revision `8806e9f8`, and test `tests/treatment-detail-followup.spec.ts`. Full hashes and runnable dependencies still need resolution. The dashboard contains mixed outcomes, including successes; this is not an impossible task for existing agents.

**Attempt inspected:** [April 27 run](https://web-debug-bench.replay.io/runs/e6bde79a-66fb-425d-9122-c3842fdbda5a), Codex attempt 1, 297 seconds, marked FAIL. Source/log inspection led to a date-format explanation, which the benchmark rejected. Setup also referenced missing skills, a harness confound. The exact model version was not established from this run. Other results include DISAGREE; the displayed 0% full-pass summary does not mean every diagnosis was entirely wrong. Billing fields displaying zero do not establish free execution.

**Our proposed reproduction:** edit a follow-up date and note, introduce a permitted background refresh, save, reload, and inspect persistence. First confirm what the test actually asserts. Independently distinguish a representation problem from overwrite caused by completion order; both could coexist. Do not treat the benchmark answer as an infallible oracle.

**Separating experiment:** hold returned date representation constant while changing refresh completion order; then hold order constant while changing date representation. Record local form state, outgoing PUT body, response, store update, and reloaded state. This is a proposed factorial experiment, not a test we ran or a demonstrated fix.

**Required advantage:** correct patch and retained edits across unseen legal event orders, at lower cost or higher success than a strong agent with identical tracing and scheduling controls. Root-location agreement alone is inadequate. Reject if the baseline can construct equivalent experiments and repairs reliably.

## F02 — native debugger crash after logging redirection

**Evidence: published company case.** Undo's experiment concerns a GDB crash involving `gdb.execute("set logging enabled on", to_string=True)` followed by disabling logging. A temporary output stream's lifetime is implicated. The report compares source-only and recording-assisted Claude Code/Sonnet 4.5 and GPT-5 Codex attempts: mistaken source-level explanations and weak fixes preceded better results with runtime recordings. Small and unclear trial denominators prevent a general success-rate claim. [Experiment report](https://undo.io/resources/ai-debug-gdb-crash-experiment-results/).

**Reproduction gap:** obtain the exact pre-fix revision, build options, Python/GDB compatibility, original trigger and independent regression oracle. Do not silently substitute a toy dangling-pointer example.

**Proposed explanation test:** observe pointer provenance and object destruction before the crash, then compare the lifetime explanation with alternate ownership explanations. Count recording setup in cost. A change that suppresses the symptom without repairing lifetime semantics fails acceptance.

**Decision:** a useful positive control for runtime evidence, but poor novelty territory because Undo already demonstrates the core benefit. A new method must add measurable value beyond the recording-equipped baseline.

## F03 — distributed corruption or shutdown failure

**Evidence: published paper cases.** DDBench's Dragonfly-6687 example places corruption in concurrent stream writing while the error appears at decoding. Its Raft-268 case concerns shutdown/channel deadlock. The paper also shows context harming an otherwise successful Dragonfly attempt. Some successful reasoning involved commit history, requiring a leakage audit. [DDBench, appendix G.6](https://arxiv.org/html/2608.14863v1).

**Reproduction gap:** acquire accessible task artifacts and exact revisions; verify licenses per repository, oracle determinism, schedules and crash recovery setup. Artifact-release language alone is not proof that every task can presently be downloaded and replayed. Do not infer license permissiveness across all included repositories.

**Proposed experiment:** for corruption, distinguish writer interleavings from decoder interpretation with controlled legal schedules and independently valid serialized inputs. For shutdown, expose whether a wait can complete under the specified lifecycle. These are different bug families and need separate oracles, not a single generic “race” label.

**Required advantage:** end-to-end repaired behavior under new schedules and inputs; compare directly with concurrency-aware tools where compatible. A stronger explanation or prettier causal graph without a successful repair does not pass.

## F04 — optimization misses the native bottleneck

**Evidence: published case.** PerfAgent's Figure 3 identifies `numpy__numpy-1b861a2`, optimizing `numpy.char.replace`. It describes Python-level work missing expensive per-element native scalar allocation. Profiling changes the optimization target. [PerfAgent case study](https://arxiv.org/html/2607.19653v1).

**Reproduction gap:** resolve the benchmark task record to full commits; pin compiler, NumPy build, hardware, input distributions, timing method and correctness tests. The identifier's suffix is not sufficient environment provenance.

**Proposed additional question:** does adaptive workload selection discover a semantic-preserving optimization that transfers to unseen string lengths, array sizes, layouts and replacement patterns? Benchmark-visible workload speed alone cannot establish this.

**Required comparisons:** native-aware profiler plus frontier agent; PerfAgent or faithful compatible reproduction; random workload sampling; an equal-budget experiment selector. Keep every failed or incorrect optimization in the denominator. Reject if the published method already achieves the proposed advantage.

## F05 — growing codebase loses prior functionality

**Evidence: benchmark-level, not a fully audited individual attempt.** SlopCodeBench contains sequential specification changes, including a `code_search` example. This study has not established a clean task/revision/agent trace/oracle bundle for that example. The independent audit creates additional evaluator concerns. [Paper](https://arxiv.org/html/2603.24755v1), [audit](https://github.com/kimjune01/slopcodebench-audit).

**Required first task:** one independently specified change sequence with clear cumulative acceptance tests, actual agent commits at each checkpoint, and no hidden requirements inconsistent with the prompt. A freshly generated anecdote is not a substitute.

**Control:** continuation versus fresh implementation with the same cumulative requirements, measured on subsequent changes. If quality worsens equally, growing task difficulty may explain the observation. This candidate does not yet satisfy our four-part task gate and should not receive a mechanism implementation cycle.

## F06 — scientific result passes superficial checks

**Evidence: incomplete case audit.** AInsteinBench references scientific implementation tasks, but the inspected HTML lacked the detailed appendix required for an attempt-level audit. InterFLOPBench is not an end-to-end repair benchmark. [AInsteinBench](https://arxiv.org/html/2512.21373v1), [InterFLOPBench](https://arxiv.org/html/2606.31308v1).

**Required task:** a real algorithm change with an explicit numerical specification and an independent oracle, such as a conservation law plus high-precision convergence checks. Record conditioning, tolerance, rounding model and admissible inputs. A residual bound does not automatically bound forward error in an ill-conditioned problem.

**Decision:** hold. No current-frontier failure receipt and no measured opportunity have been established here.

## Source reading ledger

“Body” means the relevant methods/results/discussion were read, not every line, reference, appendix or linked artifact. “Opened” alone does not support a technical conclusion. Publication versions and access dates must be pinned again for replication.

| Source | Reading depth | Role and limitation |
| --- | --- | --- |
| [DDBench](https://arxiv.org/html/2608.14863v1) | Body: design, evaluation, case studies, limitations | Distributed-task evidence; curated context and artifact availability need independent audit |
| [Replay Web Debug Bench](https://www.replay.io/blog/web-debug-bench) | Full technical blog and live task/run browser views | Diagnosis benchmark, not verified patch success; synthetic app construction and LLM judging limit interpretation |
| [Replay MCP tools](https://docs.replay.io/reference/replay-mcp/tools) | Tool descriptions | Existing runtime-inspection capability, not a superiority experiment |
| [Undo GDB experiment](https://undo.io/resources/ai-debug-gdb-crash-experiment-results/) | Technical case report | Vendor experiment with historical model configurations |
| [Undo AI](https://docs.undo.io/UndoAI.html) | Product documentation | Existing agent integration |
| [ConFixAgent](https://arxiv.org/html/2604.05753v1) | Body: mechanism and soundness discussion | Direct overlap with concurrency repair |
| [InspectCoder](https://arxiv.org/html/2510.18327v1) | Body: action space, runtime perturbation, patching and middleware | Active hypothesis testing already exists; self-repair setting differs from repositories |
| [DebugHarness](https://arxiv.org/html/2604.03610v1) | Body: motivating case and design, including algorithm | Live debugging and replay for native vulnerabilities; no independent replication here |
| [DoVer](https://arxiv.org/html/2512.06749v1) | Body: attribution ambiguity, intervention pipeline and evaluation | Agent-trajectory interventions; outcome improvement does not uniquely identify an original cause |
| [Debug2Fix](https://www.microsoft.com/en-us/research/wp-content/uploads/2026/02/cngtkgvhtjjshgbmtcqnsjddkdzdhvyr.pdf) | PDF located; targeted text retrieval failed | Additional baseline lead; detailed claims excluded |
| [Antithesis architecture](https://antithesis.com/docs/introduction/how_antithesis_works/) | Documentation | Deterministic simulation and guided state exploration |
| [Antithesis agent skills](https://antithesis.com/blog/2026/agent_skills/) | Technical blog | AI-assisted setup and testing already exist |
| [Antithesis AI overview](https://antithesis.com/docs/ai/overview/) | Documentation | Product comparison, not independent evaluation |
| [Dynamic partial-order reduction](https://escholarship.org/uc/item/47c9f29c) | Academic abstract/record | Established schedule-search idea; full proof not audited here |
| [PerfAgent](https://arxiv.org/html/2607.19653v1) | Body: workflow, tables, case and ablations | Direct competitor, historical model results |
| [GSO](https://gso-bench.github.io/) | Benchmark page and update notes | Prompt, budget and leakage controls changed between runs; freeze a version |
| [Performance-benchmark audit](https://arxiv.org/html/2607.01211v1) | Abstract and results/conclusion | Hardware/oracle sensitivity; not independently replicated |
| [PerfBench](https://www.microsoft.com/en-us/research/publication/perfbench-can-agents-resolve-real-world-performance-bugs/) | Official research summary | Additional lead; not an audited task receipt |
| [SlopCodeBench](https://arxiv.org/html/2603.24755v1) | Body: metrics, evaluation and prompts | Code-evolution hypothesis, not causal proof |
| [SlopCodeBench audit](https://raw.githubusercontent.com/kimjune01/slopcodebench-audit/main/AUDIT.md) | Full working audit | Counterevidence with pinned revisions; audit itself not reproduced |
| [Anthropic long-running harness design](https://www.anthropic.com/engineering/harness-design-long-running-apps) | Technical blog | Existing engineering responses to long-running work |
| [Anthropic effective harnesses](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) | Search excerpt | Discovery only; no decisive claim rests on it |
| [Cursor scaling agents](https://cursor.com/blog/scaling-agents) | Page opened | Contextual lead; no audited capability claim extracted |
| [InterFLOPBench](https://arxiv.org/html/2606.31308v1) | Body: methods and results | Classification scope and label/accuracy distinctions |
| [AInsteinBench](https://arxiv.org/html/2512.21373v1) | Rendered body; detailed appendix unavailable in HTML | Incomplete task-level audit; displayed dates also need version reconciliation |
| [Herbie](https://herbie.uwplse.org/) | Official overview excerpt | Established numerical-expression improvement; no source-code audit |
| [Traverse/Scout](https://arxiv.org/html/2609.17930v1) | Body: task, methods and reported results | Existing specialized trace-analysis approach |
| [Model Discovery Agent](https://arxiv.org/html/2608.09696v1) | Abstract and page overview | Adjacent experimental-design prior art; no coding-repair equivalence asserted |
| [Counterfact](https://github.com/counterfact-labs/counterfact) | README | Causal interventions for agent pipelines; adjacent rather than identical application domain |
| [SWE-Lancer](https://openai.com/index/swe-lancer/) | Official search excerpt | Historical benchmark lead; not evidence about current model limits |
| [TechRadar software-quality article](https://www.techradar.com/pro/what-ai-coding-benchmarks-still-miss-about-software-quality) | News article | Secondary interpretation; not counted as independent benchmark evidence |

### Social and video audit

Two firsthand-discussion leads concerned [persistent agent context](https://www.reddit.com/r/AI_Agents/comments/1ucqhpp/ai_coding_assistants_dont_have_an_intelligence/) and [automatic LLM debugging](https://www.reddit.com/r/aiagents/comments/1vm600d/has_anyone_built_automatic_debugging_for_llm/). Public excerpts were inspected. They lack task receipts and support discovery only. A [SWE-Race discussion](https://www.reddit.com/r/MachineLearning/comments/1wyw0my/swerace_a_codingagent_benchmark_of_188_real/) led to an inaccessible primary site; its benchmark claims were excluded from the ranking.

Direct X search for coding-agent debugging led to login. No authenticated X posts were reviewed; index snippets and mirrors are not substituted for firsthand evidence.

A final public-discussion search also surfaced [requests to prefer experiments over reasoning](https://www.reddit.com/r/ClaudeCode/comments/1tk9427/claudecode_likes_to_think_more_than_experiment/) and [discussion of a separate experiment selector](https://www.reddit.com/r/Agentic_AI_For_Devs/comments/1ww9xhc/do_agents_need_a_separate_system_for_actually/). These are anecdotal excerpts, not validated results. They reinforce the need for a simple instruction baseline and weaken any claim that hypothesis splitting itself is an original product idea.

The browser located [Replay's introduction](https://www.youtube.com/watch?v=RjCMldpjgSY), [Undo's demo](https://www.youtube.com/watch?v=p416JIurLiU), and [an independent debugging-workflow video](https://www.youtube.com/watch?v=rnFNwwwq1D8). Transcript export returned unavailable for all three. Page metadata was inspected, but the videos were not watched or transcribed. No technical conclusion relies on their contents. Platform-generated summaries or chapters are not treated as transcripts.

## Audit conclusions

The strongest evidence collected is sufficient to choose what to reproduce, not sufficient to claim product novelty or superiority. Published diagnosis scores, accepted patches, expert-matching speedups, checkpoint completion and trace-judge accuracy measure different outcomes; they must not be combined into one ranking of models. Public examples and their reference solutions are now exposed. All confirmatory evaluation needs separately frozen, unseen tasks.
