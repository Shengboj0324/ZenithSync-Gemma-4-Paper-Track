# Risks and decisions

The plan succeeds only if it preserves enough time and budget to establish a defensible claim. The risks below are concrete dependencies of this proposal, not a generic compliance checklist.

## Risk register

| Risk | Evidence or trigger | Consequence | Mitigation and owner |
| --- | --- | --- | --- |
| Eligibility unresolved | Age, residency, employment, or sponsor-consent conditions not checked | Prize or participation risk | Entrant resolves before compute commitment; do not infer an age from prior context |
| Model/harness access missing | Full harness is gated; no local assets inspected | Architecture cannot yet be certified compatible | Implementation owner obtains authorized assets and pins versions |
| Weak novelty | Closest methods already implement graph confidence/budgeting | High implementation effort with weak paper contribution | Research owner completes feature comparison before Oct 9 |
| Invalid public tasks | Gold controls fail due to environment | Apparent method changes reflect harness problems | Evaluation owner audits controls and publishes exclusions |
| Reference leakage | Post-fix source, test patches, cached labels reach agent | Invalid scientific conclusions | Separate runtime/evaluator mounts and audit logs |
| Sparse evidence | Small untouched cohort and few repositories | Wide intervals; unsupported universal claims | Broaden external tasks within budget; report uncertainty |
| Surrogate mismatch | Coverage increases but repair does not | Mathematical objective lacks practical value | Test actual repair and remove ineffective mechanism |
| Misleading efficiency | Hard tasks dropped or setup ignored | False resource advantage | All-task denominators; cold and amortized costs |
| External graph mismatch | Supplied embedding generation cannot be reproduced | Transfer experiment changes representation | Disclose representation changes and include lexical-only control |
| Compute overrun | Pilot runtime exceeds assumptions | Cannot finish matched comparisons | Recompute the tier before large runs; prioritize primary contrast |
| Release restrictions | Organizer's graph-release answer remains provisional | Public resource cannot contain planned assets | Default to original code, synthetic fixtures, and permitted aggregates with authorized reconstruction |
| Late submission/UI issue | Saved draft mistaken for submitted writeup | Entry not judged | Internal Nov 9 deadline and actual-state verification |
| Whole-run timeout | Per-task settings exceed aggregate allowance | Code entry fails despite useful patches | Measure full workload, reserve overhead, retain qualified baseline |
| Registration mismatch | Paper entry assumed to cover code competition | Main-track deadline missed | Verify each competition's entry and team state independently |
| Public-score overfitting | Small leaderboard change drives repeated retuning | Private ranking reverses | Require local/external evidence and log every submission hypothesis |
| Paper/version drift | Later code results attributed to frozen paper version | Unreproducible claims | Preserve distinct research and code artifact hashes |
| Graph tool integration failure | Semantic queries empty or graph unavailable inside skill | Selector never receives intended evidence | Smoke-test official interfaces before selector investment |

## Decision log

| ID | Decision | Status and revision condition |
| --- | --- | --- |
| D1 | Pursue both paper and code competition with separate success criteria | Updated Oct 7 following user scope change; supersedes paper-only priority |
| D2 | One paper combines method and reusable evaluation contribution | Recommended; separate papers only for independently complete contributions |
| D3 | Start with the official compatible baseline; treat graph selector and targeted tuning as competing interventions | Updated Oct 7; promote by measured net repair value under budget |
| D4 | Main mathematical claim concerns the selection surrogate | Firm boundary; do not extend to patch correctness without new proof |
| D5 | Standard tier assumes one person at 25 hours/week | Unconfirmed planning assumption; adapt to actual availability |
| D6 | No results or performance claims this round | Confirmed scope |
| D7 | Core work remains in repository documentation | Implemented; no cloud document copies |
| D8 | Freeze paper artifact, then continue code optimization through Dec 2 | Planned; preserve historical evaluation provenance |

## Questions to resolve without stopping this planning round

| Question | Why it matters | Default until answered |
| --- | --- | --- |
| How many people and focused hours are available? | Determines feasible experiment and review coverage | Solo plan with reduced and standard tiers |
| What GPU access, storage, and cash ceiling are available? | Determines whether baseline and external experiments fit | No purchases; use measured pilot before commitments |
| Has the user joined and accepted the relevant rules? | Controls data access and eventual submission eligibility | No assumption of accepted access |
| Is sponsor consent needed for eligibility? | May require lead time | Entrant checks privately |
| Is there existing unpublished work to build upon? | Could improve feasibility or change novelty | Start from the empty research repository |

## Organizer questions to draft later

These questions are not sent by this task. Check for newer public answers before contacting anyone.

1. Does the 3,000-word limit include title, abstract, tables, captions, references, and an optional linked PDF? Which counter is authoritative?
2. Has permission to release independently regenerated graphs/embeddings been finalized? Which aggregate statistics or sanitized trajectories may be redistributed?
3. Does editing an already submitted Writeup alter the timestamp used for tie-breaking?
4. How are the generic leaderboard clauses in the foundational rules applied to this manually judged paper track?
5. Is the public Judges section complete, and are there additional paper-specific format or artifact review requirements?
6. Does the current main-track harness expose the exact task count and remaining aggregate time, and what control over per-task limits is supported?
7. Which startup/serialization clocks are charged, how are retained patches handled on timeout, and what differs between the agent allowance and notebook wall-time limit?
8. Does hosted scoring consume personal GPU quota, and what is the recovery policy for infrastructure failures under the daily limit?

If the answer to a release question is delayed, continue experimentation on authorized local data and use original synthetic fixtures for the public demonstration. If eligibility itself is unresolved, do not treat research progress as confirmation of prize eligibility.

## Red-team review before freeze

Try to disprove the headline result with the strongest simple alternatives: equal tokens; equal wall time; identical snippets without graph edges; reliability-blind selection; fixed versus adaptive stopping; cold graph construction; all failed runs restored to the denominator; and untouched repositories. If one check explains the entire gain, revise the contribution around what remains.

Review mathematical and rhetorical claims together. “Optimal context,” “causal graph,” “guaranteed reliability,” “contamination-free,” and “consumer-hardware ready” require evidence beyond the current proposal. Use bounded descriptions until those stronger meanings are independently established.
