# Data rights and evaluation isolation

Status: evidence collected, no training corpus approved. Checked 2026-10-09 UTC.
This records source terms and operational decisions; it is not a guarantee that
all rights, hidden-test overlap, or competition requirements have been cleared.

## Competition rules

The [official rules](https://www.kaggle.com/competitions/gemma-4-developer-agent/rules)
were read in the rendered Kaggle browser page. Section 2.6 permits external data
and models subject to public/equal access or the host's reasonable-access and
cost criteria, plus any host-specific prohibition. This supports investigating
freely available public trajectories; it does not authorize every derived asset.

Sections 2.5 and 2.8 require a reproducible winning solution and applicable code/
model licensing. The rules distinguish externally licensed input data/models
from the winner's own submission license. Section 3.4 prohibits incorporating
hand-labelled validation/test predictions. Keep reserved evaluation bodies and
reference patches out of training, and preserve source notices separately from
our own code license. Registration was already accepted by the user; no new
registration or submission action was performed during this check.

## Dataset and teacher evidence

The pinned NVIDIA SWE-Hero card at revision
`150bc119e52c647216fce285fd801f16b6fd745b` declares CC BY 4.0 and describes SFT
and distillation use. Preserve its attribution to NVIDIA and its paper citation:
Nikolai Ludwig, Wasi Uddin Ahmad, Somshubra Majumdar, Boris Ginsburg (2026),
*From SWE-ZERO to SWE-HERO: Execution-free to Execution-based Fine-tuning for
Software Engineering Agents*, [arXiv:2604.01496](https://arxiv.org/abs/2604.01496).
The acquired card remains under `artifacts/data/quarantine/swe-hero-001/README.md`.

[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) requires appropriate
attribution, a license link, and an indication of modifications; it does not
supply a blanket warranty covering all other rights. Our transformations include
serialization conversion, path/tool adaptation, fresh offline replay results,
omitted teacher reasoning, reconstructed initial prompts, and native token/mask
encoding. Preserve those changes in lineage and redistribution notices.

The card names Qwen3-Coder-480B-A35B-Instruct as the teacher. Its currently
published [model license](https://huggingface.co/Qwen/Qwen3-Coder-480B-A35B-Instruct/blob/main/LICENSE)
is Apache 2.0. The model's exact generation revision and any original service
terms are not recorded per acquired trajectory. Do not claim those were verified.
The pinned R2E task card declares Apache 2.0, which is a dataset-level declaration,
not a replacement for each repository's own notices.

## Exact source revision findings

| Source | Publisher row label | Inspected source notice | Admission action |
|---|---|---|---|
| Tornado, base `c9d2a3fa573987629ad576e991c2f3b65f4daab4` | Apache-2.0 | Tracked root LICENSE is Apache 2.0 | Preserve license and modification provenance; embedded-file/dependency review still open |
| Pyramid, base `0ea23784ba4c8af4ac0ae1a2d8a23b959e6acfa6` | MIT | Mixed terms in LICENSE.txt, with separate copyright holders and documentation terms | Do not admit as MIT-only; retain in quarantine pending file-level review |

Pyramid's [exact license file](https://raw.githubusercontent.com/Pylons/pyramid/0ea23784ba4c8af4ac0ae1a2d8a23b959e6acfa6/LICENSE.txt)
contains a majority-code license with a modification-notice requirement, ZPL 2.1
portions, other component licenses, and CC BY-NC-SA 3.0 US terms for rendered
documentation. The MIT dataset label cannot describe this whole tree. This is
not a finding that every Pyramid code snippet is prohibited. Before admission,
trace actual observed/modified files to applicable terms and preserve required
notices; exclude material whose intended use is not established. Do not silently
relicense raw observations or publish the source image as an MIT asset.

The [Tornado source license](https://raw.githubusercontent.com/tornadoweb/tornado/c9d2a3fa573987629ad576e991c2f3b65f4daab4/LICENSE)
requires preserving applicable notices and identifying modifications when
redistributing covered derivative source. Raw original evidence remains unchanged;
prepare attribution and modification notices in any derived distribution bundle.

`capture_snapshot_notices.py` exports tracked license/notice files from immutable
local snapshots using offline disposable containers. Captured files include
Pyramid LICENSE.txt, COPYRIGHT.txt and docs/copyright.rst, and Tornado LICENSE.
Evidence: `evidence/data/pyramid-notices-001` and `tornado-notices-001`. The filename
scan is not an exhaustive embedded-header or dependency-license audit.

## Repository isolation

`audit_repository_lineage.py` resolved current GitHub numerical IDs and declared
fork-network roots for eight source repositories and the four reserved official
repositories. No IDs or roots overlap. Only the existing official metadata index
was read; confirmation task bodies and patches were not inspected.

Evidence: `evidence/data/repository-lineage-001`. This closes the current
canonical-ID/declared-fork comparison for those named repositories only. It does
not exclude detached forks, vendored source, historical copies, semantic issue
or patch duplicates, model-pretraining exposure, or unknown hidden repositories.
The sampled source tasks were selected for replay cost and coverage, so their
successes cannot estimate a population repair rate.

## Remaining admission work

1. Map each distributed observation/patch fragment to preserved source notices;
   resolve the Pyramid label mismatch before moving it out of quarantine.
2. Define corpus-level train/development/confirmation families and duplicate
   controls. Existing repository disjointness alone is insufficient.
3. Distinguish action-only replay supervision from a teacher policy conditioned
   on those observations. Preserve native errors, transformation mappings and
   reconstructed-prompt labels; never fabricate conditioning or reasoning.
4. Build a sufficiently diverse accepted pilot corpus and test restore, packing,
   mask integrity and training memory. Two successful traces are mechanism
   checks, not the proposed training campaign's data supply.

## File-level follow-up: short Pyramid replay

`evidence/data/pyramid-file-rights-001/report.json` accounts for all 19 shell
observations and verifies three direct source reads against an offline export of
the immutable snapshot: README.rst (first 50 lines), src/pyramid/settings.py,
and tests/test_settings.py. Comparisons remove exactly one terminal LF to match
native read_file serialization. The final settings read also matches the recorded
unique replacement. The disposable export container exited successfully and was
removed. These are source-content comparisons, not licensing guarantees.

The complete README explicitly names the Repoze Public License; that notice is
outside the first 50 lines the replay observed. The inspected files have no ZPL
header or Paste marker. No rendered documentation body appears in the reviewed
native results; directory listings merely include documentation paths. Thus the
repository-wide documentation restriction does not by itself establish that this
particular trace contains rendered documentation. Still, the trace is not MIT-only.

Event 62 includes warning snippets from pyramid/asset.py and installed
pkg_resources, which require additional provenance coverage. Events 54 and 62
have visibly truncated test output. Event 38 prints a failed teacher-written test
but returns exit code zero: never treat a successful tool process as a passing
test suite. Independent publisher-expectation grading remains separate evidence.

The saved raw patch also lacks a prominent modification/date notice. Preserve it
as evidence; do not silently alter the replay to manufacture compliance. Any
derived redistribution package must separately handle attribution, applicable
modification notices and teacher-created material. Training approval remains false.

## Linked replay preflight

`python scripts/assess_replay_admission.py --attempt ... --history ... --grade ...
--tokens ... --output ...` checks the identity chain between the saved patch,
grading receipt, captured events, reconstructed history, schemas and token audit.
It reconstructs native exchanges and mapping, recounts charged calls, rejects
contradictory grading summaries and requires untruncated tokenization. It does
not rerun tokenization or independently authenticate arbitrary supplied receipts.
Rights, frozen split/duplicate review, source/evaluator qualification and GPU
memory/runtime acceptance remain explicit gates; this command never sets
`training_approved` to true.

With a 32,768-token context, 8,192-token output reserve and 40 charged calls:

| Replay | Native calls | Input + reserve | Linked mechanical checks |
|---|---:|---:|---|
| Short Tornado | 33 | 23,076 | Pass; not training approved |
| Short Pyramid | 29 | 27,116 | Pass; not training approved |
| Long Tornado | 58 | 37,125 | Blocked by both budgets |

Reports are in `evidence/data/{tornado-budget,pyramid-budget,tornado-long}-admission-001`.
The output reserve is a deployment policy, not a claim that the stored supervised
sequence includes those extra tokens or that this context fits training memory.
Four new tests exercise exact boundaries, overflow, changed patches/mappings,
contradictory grading and invalid boolean token counts. The local suite ran 190
tests: 175 passed, 15 skipped. Skipped runtime checks are not passes.
