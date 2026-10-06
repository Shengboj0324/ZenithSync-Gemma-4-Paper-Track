# Execution schedule and resource plan

The default plan assumes one researcher, approximately 25 focused hours per week, and access to a compatible GPU environment. Team size, available time, and spending limit remain unconfirmed. The dates below are targets for a later implementation round; no compute has been purchased or provisioned.

The central dependency is: valid environment → credible baseline → differentiated mechanism → frozen evaluation → supported paper. Protect that order. Training and presentation extras must not delay validation.

## Dated milestones

| Dates in 2026 | Work and artifact | Exit criterion | Response if missed |
| --- | --- | --- | --- |
| Oct 6–8 | Eligibility/access check, resource ceiling, harness and data manifest, nearest-work comparison | Authorized assets, runnable baseline plan, exact novelty question | Resolve blockers; choose a smaller resource study if GPU access is absent |
| Oct 9–12 | Implement baseline and provenance audit; small timing/validity pilot | Reproducible grader behavior and measured per-task costs | Fix environment before changing model strategy |
| Oct 13–17 | Implement evidence candidates, reliability checks, bundles, selector | End-to-end pilot with same-editor baselines and complete logs | Remove adaptive control; keep one selector intervention |
| Oct 18–22 | Tune on development only; inspect failure taxonomy; closest-work comparator | Mechanism survives basic ablation and has plausible practical benefit | Pivot to a specific diagnostic finding or stop adding method complexity |
| Oct 23–28 | Freeze method and cohorts; run untouched and external comparisons | Frozen per-task results, failure counts, primary effect and intervals | Shrink claims, not denominators; prioritize primary contrast |
| Oct 29–Nov 2 | Confirm critical ablation, robustness/seed checks as budget permits; fresh reproduction | Results trace to configs/logs and observed behavior matches claims | Drop unsupported claims; document unresolved reproducibility limits |
| Nov 3–6 | Write the paper around actual findings; prepare resource documentation | Complete argument, references, readable figures, conservative word count | Cut secondary contributions and decorative material |
| Nov 7–9 | Human technical review, asset-access check, first complete submission | Submitted-state confirmation and immutable local archive | Use November 10–12 only for necessary repairs |
| Nov 10–12 | Final checks and contingency | Submission remains valid before official cutoff | No new experiments that jeopardize the accepted artifact |

October 6 to November 12 is 37 calendar days between dates, about 5.3 weeks. At 25 hours per week, approximately 132 person-hours are available before accounting for other commitments. The standard tier likely consumes 100–140 focused hours depending on environment problems; it is a tight plan, not a comfortable one. If weekly availability is closer to ten hours, adopt the reduced tier immediately.

Internal deadline: November 9 at 15:00 Los Angeles time. The official local cutoff is recorded in [competition facts](01-competition-facts.md). Earlier entry can matter for ties, but the effect of editing a submitted writeup on its timestamp remains unverified. Submit a complete defensible version early; do not assume a placeholder preserves priority.

## Compute estimates

Measure setup, graph construction, retrieval, generation, tests, and grading separately on the pilot. Use

\[
H_{\mathrm{machine}}=\frac{N_{\mathrm{runs}}\bar t_{\mathrm{minutes}}}{60}(1+r),\qquad
H_{\mathrm{device}}=gH_{\mathrm{machine}},\qquad
\mathrm{cost}=pH_{\mathrm{machine}}+\mathrm{storage}+\mathrm{other\ charges}.
\]

Here `g` is the number of allocated GPUs per machine, `p` is a quoted hourly machine price, and `r` reserves retries/overhead. This does not assume perfect parallel scaling. If the pilot timing excludes setup or grading, add those terms explicitly rather than hiding them in a small reserve.

The following estimates assume **12 minutes per complete run and 25% reserve**, both unmeasured. No current cloud price or guaranteed Kaggle quota is assumed.

| Tier | Planned model runs | Machine-hours | Device-hours if four GPUs stay allocated | Scientific scope |
| --- | ---: | ---: | ---: | --- |
| Reduced | 180 | 45 | 180 | Two strong methods on small frozen cohorts; mainly estimation and feasibility |
| Standard | 656 | 164 | 656 | Three-method comparison, external cohort, exploratory ablations |
| Expanded | 1,056 | 264 | 1,056 | Adds a focused robustness matrix and extra seeds |

Standard run accounting: pilot `20×3=60`; development `29×4=116`; holdout `80×3=240`; external `60×3=180`; ablations on development `20×3=60`; total 656. The 20 ablation tasks are reused development tasks, not additional independent evidence. Task grouping and exclusions can change counts; publish the resulting manifest and recompute costs.

Expanded adds a separate corruption experiment `40×2×3=240` (P and reliability-blind, three corruption levels) and repeat-seed checks `40×2×2=160`; total 1,056. Choose the 40 tasks before viewing outcomes, and use consistent paired seeds. Any replication or tuning of B3 beyond the listed matrix is additional cost and must replace a lower-priority run or enlarge the approved budget.

Reduced accounting: pilot `10×3=30`; development `10×3=30`; holdout `40×2=80`; external `20×2=40`; total 180. Use separate groups for pilot, development, and holdout. This tier is unlikely to tightly establish small repair gains or a three-point noninferiority margin. Favor a clear diagnostic contribution, report uncertainty, and do not promise high-power superiority.

If measured average duration is 30 minutes, all estimates multiply by 2.5. If failures require major reconfiguration, a 25% reserve may be inadequate. Compute the next run batch's worst-case cap before launch; stop when the remaining budget cannot complete the primary comparison symmetrically.

## Hardware feasibility

At 31 billion parameters and four bits per parameter, the arithmetic weight payload is approximately `31e9×4/8=15.5e9` bytes, or 14.44 GiB. This is a lower-level weight estimate, not a memory-fit guarantee: scales, unquantized tensors, runtime workspaces, activations, and KV cache add memory.

For a conventional decoder with `L` layers, `h_kv` KV heads, head width `d`, sequence length `s`, batch size `b`, and cache element size `q` bytes, a simplified cache estimate is `2Lh_kvdsbq`. Exact architecture, sliding attention, cache implementation, and parallel sharding must come from the actual model/runtime. Do not fill unknown values from a different Gemma generation.

Measure peak memory on each device. Aggregate 96 GB does not mean a single contiguous device has 96 GB. Quantized inference compatibility also does not establish LoRA training compatibility. Inspect the supported loader and adapter targets before considering tuning.

Graph preprocessing needs CPU, RAM, storage, and time even when supplied assets make development convenient. Report cold-start graph creation and amortized inference separately. For external repositories, inability to reproduce the supplied embedding model is a design issue: use a disclosed alternative or a lexical-only transfer variant, without pretending the representations match.

## Person-hour priorities

Allocate approximately 20% to access, data validity, and harness work; 25% to the mechanism and baselines; 30% to experiments and analysis; 20% to writing and reproducibility; and 5% to submission checks. Treat these as an initial allocation and move time toward the current evidence bottleneck.

For a real team, use distinct human ownership: experiment/harness owner, method owner, and analysis/paper owner. A second person should independently reproduce the headline table and challenge the novelty statement. More people do not justify more contributions by default. No agents or human collaborators were delegated work in this planning round.

## Stop and simplify rules

- If the first pilot cannot reliably grade gold and no-fix controls, suspend model optimization.
- If the primary method takes more than 20% extra runtime before generation, test whether gains compensate; do not omit that overhead.
- If no differentiated mechanism survives development ablations by October 22, switch to a bounded diagnostic study or remove the unsupported method claim.
- If external data cannot be ready by October 23, reduce the external cohort before weakening audit requirements.
- If writing starts after November 6, stop optional experiments and use only frozen evidence.

These thresholds control scope. They are not performance findings or competition rules.
