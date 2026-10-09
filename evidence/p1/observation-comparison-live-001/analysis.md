# Actual Gemma development comparison

Both candidates repaired the reserved Requests development task under the local
fixture-compatible grading setup. This is one repeatedly inspected development
task, not held-out evidence or a statistically meaningful model comparison.

| Observation | Base | Source-observation candidate |
| --- | ---: | ---: |
| Captured HTTP model requests | 42 | 34 |
| Summary-prompt matches | 2 | 1 |
| Prompt tokens (all captured requests) | 375,666 | 304,105 |
| Completion tokens | 9,031 | 7,903 |
| Total tokens | 384,697 | 312,008 |
| Skill calls | 0 | 0 |
| Patch bytes | 439 | 363 |
| Agent error | 40-turn limit | None |
| Local compatible evaluator resolved | True | True |

Both use the same base checkpoint, sampling config, official compaction settings,
40-turn/40-tool-call/10-minute attempt budgets, task and dependency inputs. Base
ran first; there is no randomization or replication. The candidate adds a skill,
its tool schemas, and a short instruction. This confounds any prompt-level
attribution, and the unused skill cannot explain a demonstrated recovery gain.
The candidate is not promoted. Actual learned skill adoption remains open.

The base submitted twice, including the final 439-byte patch. The harness still
reported a turn-limit error. Preserve that operational result separately from
patch quality. All captured HTTP requests returned 200; complete server usage
includes summaries omitted from some agent trace totals. Summary counts use
matches to the organizer's default summarization prompt.

Grade-001 failed before tests because this run mistakenly used the original
image with the compatibility dependency selection. No source-origin observation
was produced. Grade-002 repeats both unchanged patches using the previously
qualified compatibility image, source-path override, in-process source assertion
and bridge networking. Both imports resolve to /workspace/src/requests. JUnit
coverage is compared in ../observation-comparison-grade-002/paired-results.json.
These local corrections do not establish hidden-grader environment parity.

Server startup took 86.54 seconds; total supervised lifetime was 441.32 seconds.
It exited cleanly after a stop request, before the approved deadline. GPU memory
was observed at 0 MiB afterward. This is about $0.49 of elapsed compute at
$3.99/hour, not the full Pod bill: the Pod was already running beforehand and
continues charging until stopped. No training was performed. Temporary SSH key
access was removed, preserving the three existing keys; the tunnel was closed.
