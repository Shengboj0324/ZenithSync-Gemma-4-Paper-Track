# Paper structure and submission plan

Write the eventual paper after the results establish which claim survives. The current package is a research plan, not a paper ready for submission. The paper's central sentence should state a tested finding about graph reliability, context allocation, and software repair—not a list of components.

October 7 joint-track revision: freeze and identify the exact research artifact used in every paper result. The December code entry may improve after this freeze; do not retroactively attribute its later performance to the paper version. If graph selection does not produce a distinct finding, revise the title and argument around the strongest supported insight from the shared agent experiments. A Kaggle code submission and a paper Writeup remain separate deliverables, with separate status checks.

## Argument structure

The introduction should create a precise technical tension: graph context can expose dependencies, but unreliable or redundant structural evidence can spend scarce inference budget without helping a patch. The methods section should explain the intervention that resolves that tension. The results must then test it against simpler explanations.

| Section | Function in the argument | Planned words |
| --- | --- | ---: |
| Title and subtitle | Name the question and setting without announcing an unmeasured win | 25 |
| Abstract | Problem, intervention, measured result, boundary | 160 |
| Introduction | Explain why existing graph retrieval leaves this question open | 300 |
| Related work | Establish the closest overlap and exact distinction | 250 |
| Method | Define evidence reliability, bundles, objective, and limits | 520 |
| Experimental design | Establish fair budgets, data separation, and external testing | 420 |
| Results and analysis | Answer the primary question, explain mechanism, show failures | 470 |
| Limitations and reproducibility | Bound inference and locate reusable artifacts | 200 |
| Conclusion | State the supported contribution without new claims | 70 |
| Captions, tables, references | Make the paper self-contained and attributable | 335 |
| Total | Conservative draft ceiling | 2,750 |

The 250-word buffer protects against counting ambiguity, editorial changes, and equations/text handled differently by the platform. Count all displayed words, including references and captions, until organizers clarify otherwise. Do not use linked appendices to conceal essential methods or evade the limit. Artifact documentation can supply execution detail while the paper remains understandable on its own.

## Proposed opening templates

Use these as structural placeholders, not final prose.

**Question-led title:** “When to Trust Repository Graphs for Budgeted Software Repair.”

**If repair superiority is supported:** lead the abstract with the constrained repair problem, identify the reliability/bundle intervention, give the paired absolute improvement with cohort sizes and uncertainty, then identify the largest limitation.

**If only efficiency is supported:** lead with the validated quality margin and complete cost definition. State the noninferiority interval and savings together. Avoid “same accuracy” unless evidence justifies it.

**If the result is diagnostic:** name the reproducible failure condition and the intervention that established it. A negative result needs an explanation and a reusable test, not an apology or a disguised improvement claim.

Never write result-shaped placeholder percentages into a draft abstract. Use explicit `[pending experiment]` fields in working notes only, and remove every placeholder before submission.

## Planned tables and figures

| Artifact | Necessary contents | What it prevents |
| --- | --- | --- |
| Main comparison table | Cohort sizes, solved counts/rates, paired effect, intervals, all-task runtime/tokens, failures | Unsupported headline gains and shifting denominators |
| Budget curve | Prespecified budgets, observed means/uncertainty, preprocessing accounting | Cherry-picking one favorable token cap |
| Mechanism table | Reliability and bundle removals; graph corruption interactions if powered | Attributing gains to a component never isolated |
| One compact method diagram | Candidate evidence → reliability check → bundle selection → fixed editor → independent grader | Confusion about information boundaries |

Select two or three visual elements for the short paper rather than cramming in all analyses. Generate scientific figures from the frozen run table in a later round. This planning round does not include plots of invented performance.

## Rhetorical review

Each paragraph should do one job: establish a problem, define a mechanism, justify a comparison, interpret evidence, or bound a conclusion. A reader should be able to reconstruct the argument from the first sentence of each paragraph.

Replace broad claims such as “a novel framework for reliable autonomous coding” with an exact contribution and condition. Explain “reliability” once: source/graph provenance confidence is distinct from patch correctness. Use percentage points for absolute differences and percentages for relative changes. Specify whether cost includes failures and preprocessing.

The closest-work paragraph must name the strongest competing explanation, not just list citations. For example, if node-text retrieval explains the gain, do not attribute it to graph reasoning. If the controller is standard and the intervention dataset is the new contribution, say so.

The author should manually rewrite the introduction and interpretation after inspecting actual successes, failures, and uncertainty. Keep an AI-assistance record that identifies research support, code assistance, and editorial assistance; check venue/platform disclosure requirements. Every author must be able to defend the formulas and the source of each reported number.

## Reproducibility package for a later round

Prepare exact model/tokenizer/harness identifiers, environment lockfile or container digest, authorized asset reconstruction steps, split manifest, all configurations, evaluation commands, per-task result records, analysis procedure, failure taxonomy, and licenses. Include a small public synthetic example that exercises the method without protected competition data.

Document peak memory, device count, total inference time, training time if applicable, and the external-data origin. Explain deviations from official harness behavior and separate research runs from any leaderboard submission. Preserve raw logs privately where release is restricted; publish only assets whose rights and competition permissions support publication.

## Final submission checklist

- [ ] Personal and team eligibility resolved; relevant rules accepted by the user.
- [ ] Final claim matches frozen results and the scope of the tested cohorts.
- [ ] Closest prior work cited; no unsupported first-ever or state-of-the-art statement.
- [ ] Every required paper section is present and the conservative word count is within the limit.
- [ ] Figures, equations, tables, links, and citations are readable in the actual Kaggle presentation.
- [ ] Optional PDF/notebook links open without authentication or payment.
- [ ] Shared files contain no protected labels, private information, or accidentally attached private resources.
- [ ] Reproduction instructions were followed in a fresh environment by another person where available.
- [ ] The final Writeup is submitted, not merely saved as a draft; the user verifies its status.
- [ ] Final local copy, artifact hashes, submission URL, timestamp, and screenshots are retained.
- [ ] Team monitors the registered email for organizer correspondence and deadlines.

Publication and competition entry are later user actions. This round creates no Kaggle submission, accepts no rules, and does not publish the repository.
