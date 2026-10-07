# Judging strategy and public judge information

Scope updated October 7: this document concerns paper judging. The code competition is scored by validated repairs and private leaderboard rank, not these five criteria. Use [the joint strategy](11-code-track-and-joint-strategy.md) for code-selection decisions; judge-background analysis should not determine which agent is deployed.

The strongest controllable strategy is to make each score easy to justify from a specific piece of evidence. More architectural components are useful only if they establish an additional claim. No available evidence supports a numerical probability of winning or a guaranteed score threshold.

## Equal weights and marginal effort

Using the official criterion names in [competition facts](01-competition-facts.md), let

\[
S=(N+Q+R+V+C)/5,\qquad N,Q,R,V,C\in[0,5].
\]

A one-point improvement in any category changes the average by 0.2. A technically elaborate paper with illustrative scores `(5, 2, 5, 2, 3)` averages 3.4; a consistently supported paper with `(4, 4, 5, 5, 4)` averages 4.4. These are arithmetic examples, not predictions about judges.

Equal weights do not mathematically imply that the weakest category should always receive the next hour. If a work item takes time `t` and is expected to change scores by `Δs_j`, its planning value is `sum(Δs_j)/(5t)`, subject to feasibility and evidence dependencies. Estimates are subjective. Use them to compare concrete tasks, not to manufacture precise expected awards. An independent reproduction can improve verifiability and reveal a quality problem; extra dashboard polish usually cannot fix either.

## Evidence needed for a strong internal review

The following anchors are our preparation standard. They are not additional official scoring definitions.

| Criterion | Evidence we want a reviewer to find | What would weaken the case | Highest-value action |
| --- | --- | --- | --- |
| Novelty | A precise distinction from the closest methods; a new mechanism or reproducible explanatory finding | Renaming graph retrieval, test feedback, or a standard optimizer | Closest-work comparison and a decisive removal experiment |
| Quality | Frozen settings on external repositories; sound comparisons; limits matching sample size | Tuning on evaluation tasks, one repository, hidden exclusions | Independent benchmark and repository-level breakdown |
| Relevance | Changes to issue resolution or useful cost/reliability behavior | Better retrieval metric with no downstream check | Link localization, context cost, and actual repair outcomes |
| Verifiability | Data lineage, model/harness versions, exact configurations, per-task outcomes, reconstruction instructions | Only an aggregate percentage or a screenshot | A fresh-environment reproduction of a frozen subset |
| Clarity | One central question, three bounded claims, readable figures, precise definitions | Unexplained notation, unsupported superlatives, architectural sprawl | Rewrite the paper around the decisive result and strongest limitation |

An internal readiness target is at least 4 in each category under a skeptical human review. There is no evidence that 4.0, 4.5, or any other score guarantees an award. Record a justification and uncertainty for each internal score; do not average invented precision.

## What is actually known about the judge

Only Elan Markowitz appeared in the official Judges section when inspected. The longer competition citation lists organizers/authors; it does not establish a ten-person judging panel. Do not assign judge status or preferences to Bryan Perozzi, Benedek Rózemberczki, Glenn Cameron, Hadi Hemmati, Yuchen Li, Michael Galkin, Majid Farhadi, Ryan Holbrook, or Ashley Oldacre merely because they appear there. Panel membership may change.

Two relevant primary publications establish technical background:

| Work | Supported connection | Preparation implication, explicitly an inference |
| --- | --- | --- |
| [Tree-of-Traversals, ACL 2024](https://aclanthology.org/2024.acl-long.665/) | Markowitz coauthored a method giving language models graph-interface actions and tree search over reasoning paths | Expect a technically literate challenge to claims that graph traversal itself is new. Explain what the controller adds beyond search. |
| [StATIK, Findings of NAACL 2022](https://aclanthology.org/2022.findings-naacl.46/) | Markowitz coauthored a method combining textual and structural information for inductive knowledge-graph completion | Prepare separate text-only and structure-dependent analyses, and test unfamiliar repositories. |

These publications establish expertise, not secret preferences. The paper should cite them only where intellectually relevant. The [organizer's public advice on AI assistance](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/discussion/745712) is stronger evidence about writing expectations than speculation from a biography: the entrant must exercise editorial judgment and own the claims.

## Questions the paper must withstand

1. What would remain new if the words “Gemma,” “graph,” and “agent” were removed from the title?
2. Why does the method need graph structure rather than the same source snippets obtained with lexical search?
3. Are cost gains coming from less work, or from abandoning difficult issues?
4. Does the controller still help when all alternatives receive identical compute and source access?
5. What fails when the graph omits a dynamic call or contains an obsolete relation?
6. How much tuning happened on these tasks, and what information reached the agent?
7. Can another person rebuild the table from released configurations and permitted assets?
8. What exact mathematical claim is proven, and what remains empirical?

Answer these questions in methods, results, and limitations rather than saving them for a potential presentation. Use one representative success and one failure, selected by a written rule, to show how the mechanism behaves. A visually impressive success is supporting evidence, not the primary experiment.

## Award positioning

Prioritize the overall paper case. Package the graph-intervention protocol as a resource only if it is independently reusable, documented, and evaluated. One coherent submission may then support both kinds of consideration under the organizer clarification. A resource label does not compensate for missing experiments.

Do not add an unrelated application to pursue all three awards. The alternative application route would require a new task and its own evaluation, consuming the same scarce calendar. A second writeup is justified only if it has a distinct contribution, evidence, and ownership without weakening the main paper.
