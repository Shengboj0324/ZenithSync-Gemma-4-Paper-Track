# P1 base-agent candidate

This is an untrained, single-agent development candidate using the exact permitted Gemma alias and nine official tools. It contains no adapters or task-specific solutions. Sampling and the ten-minute per-task budget are provisional P1 settings, not optimized values or a claim of reproducibility across GPU kernels.

The prompt emphasizes evidence-grounded repair, type-correct tool calls and honest treatment of source-selection failures. Prompt instructions do not enforce mathematical correctness or repair upstream parser behavior. Actual generated calls, an end-to-end repair, measured memory/latency and qualified evaluator results remain required.

Compile with the pinned official SDK/harness before running. Keep the stopped Pod stopped until the deployment handoff is ready and the user restarts it. This candidate is separate from the immutable official starter and its placeholder adapters.
