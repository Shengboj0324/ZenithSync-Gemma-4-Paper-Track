# Execution schedule and resource plan

Codex owns implementation and verification under the [living cycle plan](12-continuous-implementation-plan.md), using 8–14-hour engineering cycles with mandatory acceptance and closeout. The earlier one-researcher, 25-hours-per-week scenario below remains an illustrative capacity estimate, not the current execution commitment. Actual cycle throughput, human review availability, GPU access and spending limit remain unconfirmed. Reforecast milestones after each cycle; no compute has been purchased or provisioned.

Updated October 7 for both tracks. The central dependency is: valid environment → packaged baseline → reliable budgeted agent → measured improvements → frozen paper evidence → continued code optimization. Research novelty governs the paper; repair performance and full-run feasibility govern the code champion. [Document 11](11-code-track-and-joint-strategy.md) defines the code gates.

## Dated milestones

| Dates in 2026 | Work and artifact | Exit criterion | Response if missed |
| --- | --- | --- | --- |
| Oct 7–8 | Eligibility/access check for both tracks, resource ceiling, harness/data manifest, nearest-work comparison | Authorized assets and exact submission contract | Resolve access before GPU work; narrow research scope if resources are scarce |
| Oct 9–12 | Reproduce starter, validate controls, generate ZIP, measure target runtime and graph-tool health | Working local archive and safe full-run configuration | Fix environment and packaging before model strategy |
| Oct 13–17 | Qualify baseline for an early hosted submission; compare reasoning, concise outputs, recovery and retrieval | Scored baseline when queues permit; stable local champion and logs | Retain simple champion; do not force graph component |
| Oct 18–22 | Promote one or two high-value interventions; consider targeted LoRA if justified | Matched development evidence and plausible paper question | Choose a diagnostic paper if novelty gains fail; continue code optimization |
| Oct 23–28 | Freeze method and cohorts; run untouched and external comparisons | Frozen per-task results, failure counts, primary effect and intervals | Shrink claims, not denominators; prioritize primary contrast |
| Oct 29–Nov 2 | Confirm critical ablation, robustness/seed checks as budget permits; fresh reproduction | Results trace to configs/logs and observed behavior matches claims | Drop unsupported claims; document unresolved reproducibility limits |
| Nov 3–6 | Write the paper around actual findings; prepare resource documentation | Complete argument, references, readable figures, conservative word count | Cut secondary contributions and decorative material |
| Nov 7–9 | Human technical review, asset-access check, first complete submission | Submitted-state confirmation and immutable local archive | Use November 10–12 only for necessary repairs |
| Nov 10–12 | Final checks and contingency | Submission remains valid before official cutoff | No new experiments that jeopardize the accepted artifact |
| Nov 13–20 | Continue code-only tuning from frozen research version; evaluate adapters/retries and time allocation | Candidate beats stable champion on fresh or honestly labeled development evidence | Keep champion; reject extra complexity without net gain |
| Nov 21–24 | Verify main-track entry/team state; audit licenses and release artifacts | Entry and intended team complete before Nov 25 cutoff | Resolve immediately; do not rely on paper registration |
| Nov 25–28 | Full-run stress tests, offline replay, final candidate qualification | At least one reliable scored candidate; second selection justified independently | Prefer stable qualified candidate over late untested gain |
| Nov 29 | Internal code final-selection deadline | Correct submission IDs and hashes selected | Reserve remaining days for queue/platform corrections |
| Nov 30–Dec 2 | Final status and deadline contingency | Final code selections verified before official cutoff | No last-minute architecture or training changes |

From October 7 there are 36 calendar days to the paper deadline and 56 to the code deadline. At 25 hours per week that is approximately 129 person-hours before the paper and 200 through the code deadline; only about 71 additional hours remain after the paper. The original standard research tier alone likely consumes 100–140 hours, so both tracks require shared experiments and selective scope. If availability is closer to ten hours weekly, prioritize a valid code baseline and a narrowly scoped paper instead of assuming both full programs fit.

Internal deadline: November 9 at 15:00 Los Angeles time. The official local cutoff is recorded in [competition facts](01-competition-facts.md). Earlier entry can matter for ties, but the effect of editing a submitted writeup on its timestamp remains unverified. Submit a complete defensible version early; do not assume a placeholder preserves priority.

## Compute estimates

Measure setup, graph construction, retrieval, generation, tests, and grading separately on the pilot. Use

\[
H_{\mathrm{machine}}=\frac{N_{\mathrm{runs}}\bar t_{\mathrm{minutes}}}{60}(1+r),\qquad
H_{\mathrm{device}}=gH_{\mathrm{machine}},\qquad
\mathrm{cost}=pH_{\mathrm{machine}}+\mathrm{storage}+\mathrm{other\ charges}.
\]

Here `g` is the number of allocated GPUs per machine, `p` is a quoted hourly machine price, and `r` reserves retries/overhead. This does not assume perfect parallel scaling. If the pilot timing excludes setup or grading, add those terms explicitly rather than hiding them in a small reserve.

The following **research-only** estimates assume **12 minutes per complete run and 25% reserve**, both unmeasured. They are not valid per-task allowances for hosted competition inference. Additional code qualification and training are excluded from this table and budgeted below. No current cloud price or guaranteed Kaggle quota is assumed.

| Tier | Planned model runs | Machine-hours | Device-hours if four GPUs stay allocated | Scientific scope |
| --- | ---: | ---: | ---: | --- |
| Reduced | 180 | 45 | 180 | Two strong methods on small frozen cohorts; mainly estimation and feasibility |
| Standard | 656 | 164 | 656 | Three-method comparison, external cohort, exploratory ablations |
| Expanded | 1,056 | 264 | 1,056 | Adds a focused robustness matrix and extra seeds |

Standard run accounting: pilot `20×3=60`; development `29×4=116`; holdout `80×3=240`; external `60×3=180`; ablations on development `20×3=60`; total 656. The 20 ablation tasks are reused development tasks, not additional independent evidence. Task grouping and exclusions can change counts; publish the resulting manifest and recompute costs.

Expanded adds a separate corruption experiment `40×2×3=240` (P and reliability-blind, three corruption levels) and repeat-seed checks `40×2×2=160`; total 1,056. Choose the 40 tasks before viewing outcomes, and use consistent paired seeds. Any replication or tuning of B3 beyond the listed matrix is additional cost and must replace a lower-priority run or enlarge the approved budget.

Reduced accounting: pilot `10×3=30`; development `10×3=30`; holdout `40×2=80`; external `20×2=40`; total 180. Use separate groups for pilot, development, and holdout. This tier is unlikely to tightly establish small repair gains or a three-point noninferiority margin. Favor a clear diagnostic contribution, report uncertainty, and do not promise high-power superiority.

If measured average duration is 30 minutes, all estimates multiply by 2.5. If failures require major reconfiguration, a 25% reserve may be inadequate. Compute the next run batch's worst-case cap before launch; stop when the remaining budget cannot complete the primary comparison symmetrically.

## Added code-track resource envelope

Plan four additional local full-workload replays: baseline qualification, candidate qualification, stress/repeat qualification, and final artifact replay. At 129 task episodes each, an illustrative six-minute complete local run and 25% reserve add `4×129×6/60×1.25=64.5` machine-hours. Before the paper freeze, use only development/independent tasks, repeating cold episodes if necessary; these are timing simulations, not new independent accuracy observations. Do not inspect the protected holdout to qualify an early submission. That six-minute local estimate includes grading for cost estimation; it is not an active-time cap. The standard research tier plus these replays totals 228.5 machine-hours, or 914 allocated device-hours on four GPUs. Update this after measuring and avoid charging the same run twice if it genuinely satisfies both protocols.

Reserve calendar opportunities for approximately eight purposeful hosted submissions across the project rather than automatically submitting every day. At the official twelve-hour agent allowance, eight runs represent up to 96 charged agent-hours, excluding validation and queue time. This is not a statement of billing or personal quota consumption: those details remain unconfirmed. Start early because a daily submission limit and queues make last-week recovery difficult.

Training requires its own estimate: trajectory generation, failed trajectories, data verification, training device-hours, checkpoint evaluation, and adapter load overhead. Do not squeeze it into the 25% retry reserve. Prefer targeted SFT when measured failure modes and compatible rights justify it; expand to RL only with an explicit budget and stable rewards. No spending is authorized by these hypothetical quantities.

## Hardware feasibility

At 31 billion parameters and four bits per parameter, the arithmetic weight payload is approximately `31e9×4/8=15.5e9` bytes, or 14.44 GiB. This is a lower-level weight estimate, not a memory-fit guarantee: scales, unquantized tensors, runtime workspaces, activations, and KV cache add memory.

For a conventional decoder with `L` layers, `h_kv` KV heads, head width `d`, sequence length `s`, batch size `b`, and cache element size `q` bytes, a simplified cache estimate is `2Lh_kvdsbq`. Exact architecture, sliding attention, cache implementation, and parallel sharding must come from the actual model/runtime. Do not fill unknown values from a different Gemma generation.

Measure peak memory on each device. Aggregate 96 GB does not mean a single contiguous device has 96 GB. Quantized inference compatibility also does not establish LoRA training compatibility. Inspect the supported loader and adapter targets before considering tuning.

Graph preprocessing needs CPU, RAM, storage, and time even when supplied assets make development convenient. Report cold-start graph creation and amortized inference separately. For external repositories, inability to reproduce the supplied embedding model is a design issue: use a disclosed alternative or a lexical-only transfer variant, without pretending the representations match.

## Effort priorities

Before the paper deadline, allocate approximately 25% to harness and baseline reliability, 25% to candidate improvements, 25% to evaluation, 20% to the paper/reproducibility, and 5% to submission checks. After the paper freezes, shift the majority to code evaluation, runtime qualification, and final selection. These are planning allocations; actual availability and pilot failures may force a smaller research matrix.

Codex owns harness, method, analysis and evidence preparation. Human review availability is a separate resource; independent reproduction and mathematical review strengthen assurance when available. Codex self-review must not be labeled independent human validation. More people do not justify more contributions by default. No agents or human collaborators were delegated work in this planning round.

## Stop and simplify rules

- If the first pilot cannot reliably grade gold and no-fix controls, suspend model optimization.
- If the primary method takes more than 20% extra runtime before generation, test whether gains compensate; do not omit that overhead.
- If no differentiated mechanism survives development ablations by October 22, switch the paper to a bounded diagnostic study or remove its unsupported method claim. Continue improving the code champion independently.
- If external data cannot be ready by October 23, reduce the external cohort before weakening audit requirements.
- If writing starts after November 6, stop optional pre-paper experiments and use only frozen evidence; resume code-only exploration after securing the paper submission.
- If a candidate fails full-run qualification, retain the last qualified code artifact regardless of its best small-cohort score.

These thresholds control scope. They are not performance findings or competition rules.
