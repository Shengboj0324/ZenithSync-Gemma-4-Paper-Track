# Planning validation and logical back checks

This validation concerns the documentation and its calculations. It does not validate the proposed agent, benchmark assets, empirical novelty, or future competitive performance.

## Arithmetic checked on October 6

Calculations were independently recomputed with Python's standard library during this planning round. The temporary calculations were executed inline; no agent implementation or experiment code was added to the repository.

| Check | Recomputed value | Interpretation |
| --- | --- | --- |
| Official UTC cutoff converted with `America/Los_Angeles` | Nov 12, 2026, 15:59 PST | Accounts for the November daylight-saving transition |
| Calendar date difference | 37 days | Oct 6 to Nov 12, not an exact remaining-time clock |
| Score examples | 3.4 and 4.4 | Both average five hypothetical criteria |
| Paper section allocation | 2,750 words | Leaves a 250-word conservative buffer |
| Public split targets | `20+29+80=129` | Exact counts yield to duplicate-group integrity and eligibility audit |
| Standard run matrix | 656 runs | Includes reused development ablations |
| Expanded run matrix | 1,056 runs | Adds 240 robustness and 160 repeat-seed runs |
| Standard machine-hours | `656×12/60×1.25=164` | Conditional on assumed runtime and reserve |
| Expanded machine-hours | `1056×12/60×1.25=264` | Same assumptions |
| Idealized four-bit weight payload | 15.5 GB / 14.44 GiB | Does not include other inference/training memory |
| Toy bundle optimum | B+C, cost 150, value 0.80 | Enumerated every subset; only proves the toy case |
| Illustrative action utility | 0.022 | Unit-consistent weighted utility example |
| Illustrative Wilson intervals | 39/129: `[.229734,.386350]`; 52/129: `[.322442,.489364]` | Marginal uncertainty, not the paired difference interval |
| Illustrative exact McNemar | `b=23,c=10`: `p=.0350820` | Assumes independent paired units |
| Approximate power calculations | 227.623 → 228; 934.041 → 935 tasks | Rounded upward; not exact power or a sample guarantee |

## Logical checks and corrections

| Tempting but invalid inference | Correct boundary incorporated in the plan |
| --- | --- |
| A high leaderboard rank is required for a paper award | Independent research is permitted; leaderboard evidence is optional |
| Organizers named in the citation are all judges | Only the explicitly listed judge is treated as confirmed |
| An award category has separate hidden scoring weights | Public clarification applies the same criteria in the category's context |
| Every new graph-based agent is novel | Nearby methods and competitor positioning require a narrower distinction |
| Submodular evidence coverage guarantees better patches | The proof applies only to fixed surrogate values; a complementary-snippet counterexample disproves the general leap |
| Greedy with token costs inherits cardinality guarantees | The default knapsack heuristic carries no such guarantee in this plan |
| Minimum over robust scenarios preserves submodularity | A two-element counterexample shows that it need not |
| Static submodularity implies adaptive optimality | Sequential guarantees need additional assumptions, not established here |
| Graph reliability is patch confidence | Reliability weights describe structural/provenance evidence and are not calibrated correctness probabilities |
| A provenance checker detects every missing dependency | Missing-edge robustness is a separate hypothesis; lexical fallback and deletion tests are specified |
| Overlapping rate intervals rule out a paired difference | Paired discordances determine paired evidence |
| Nonsignificance proves equal quality | Efficiency requires a prespecified noninferiority margin and adequate interval |
| Multiple seeds multiply the number of independent issues | Seeds remain nested in tasks and repositories |
| A recent benchmark is uncontaminated | Pretraining exposure remains uncertain unless separately established |
| Faster successful runs imply lower total cost | The denominator includes failed runs and preprocessing |
| Apache label alone permits all asset redistribution | Restrictive clauses and provisional organizer answers remain explicit |
| A technically complete draft is a submitted entry | Final submission status must be checked on Kaggle |

## Document integrity

The initial repository package contained an index and ten planning documents. The October 7 joint-track revision adds document 11 and updates the original documents in place. Local Markdown links, math delimiters, whitespace, and the scope-sensitive outline were checked. Unrelated `.idea/` files were left unchanged. Sources are linked next to factual claims and indexed with access limits.

The package deliberately distinguishes requirements, organizer interpretations, planning assumptions, hypothetical calculations, proposed mechanisms, and unperformed experiments. It makes no empirical improvement, deployment, or prize-probability claim. The unresolved harness, budget, eligibility, and novelty checks are assigned explicit next steps rather than silently treated as completed.

## Next acceptance gate

Authorize a later implementation scope only after choosing the resource tier and obtaining permitted harness access. The first milestone should be a reproducible baseline and task-validity report. Do not begin with a fine-tuning run or a polished abstract containing expected results.

## October 7 joint-track revision

The user's scope expansion replaces the earlier paper-primary recommendation. Both tracks are planned; code implementation remains outside this revision. Main-track requirements were verified live, while prior paper findings retain their original research date.

| New calculation or consistency check | Result |
| --- | --- |
| Dates from Oct 7 | 36 days to paper; 49 to code entry/merger; 56 to final code submission |
| UTC to Los Angeles | Nov 25 and Dec 2 at 23:59 UTC become 15:59 PST |
| Raw task average | `43,200/120=360` seconds, including charged overhead |
| Active allowance illustration | `(43,200-3,600-120×30)/120=300` seconds |
| Conservative-cap illustration | `120×(270+30)+3,600=39,600` seconds = 11 hours |
| Unsafe cap illustration | `120×(360+30)=46,800` seconds = 13 hours |
| Old research timing is not deployment timing | `120×12 minutes=24 hours` before setup |
| Added local qualification envelope | `4×129×6/60×1.25=64.5` machine-hours |
| Combined standard local envelope | `164+64.5=228.5` machine-hours; four-device allocation = 914 device-hours |
| Eight hosted submissions | Up to 96 agent-hours under the published allowance, excluding validation/queue; quota billing unknown |
| Hypothetical reliability-adjusted utility | `.95×.45=.4275`, lower than a stable `.44` |
| Public score granularity example | `1/60≈1.67` percentage points, conditional on 60 public tasks |

The shared-runtime objective is distinct from the paper rubric. The allocation derivative argument is conditional on concavity and known success curves; neither is asserted for real repair. Early load tests preserve the paper holdout by using development/independent episodes. Two selected final submissions are not an oracle ensemble. The published graph experiment is participant evidence and does not validate either our proposed method or a universal negative claim.
