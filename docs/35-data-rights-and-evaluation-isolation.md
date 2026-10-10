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


## Nodebook material and expanded identity checks — 2026-10-09

Captured all 15 tracked Nodebook source files (78,891 bytes) from the qualified
snapshot and its Apache 2.0 LICENSE with Copyright 2017 Stitch Fix. Captured
installed notices for pytest-asyncio 0.24.0 (Apache 2.0), msgpack-python 0.5.6
(Apache 2.0 notice, INADA Naoki), and pytest 8.3.3 (MIT, Holger Krekel and others),
which appear in replay diagnostics. Source and dependency notice hashes are
retained in `swe-rebench-nodebook-rights-material-001`.

`nodebook-file-rights-001` (with the `swe-rebench-` prefix) matches all four direct
read spans against the captured base or the sequentially applied unique edit.
One read intentionally returns only lines 1–150 of a 349-line source file.
Tokenization is untruncated, but that tool observation is truncated; keep the
two properties distinct. All 22 native shell observations are inventoried;
three are directory-view adaptations. This is not exhaustive shell-content
rights clearance. The accompanying ATTRIBUTION.md preserves origin, notices,
transformations and unresolved scope without changing raw evidence.

The Apache 2.0 terms require preservation of applicable notices and notices of
modified files; the CC BY terms require attribution and identifying changes.
Sources rechecked: https://www.apache.org/licenses/LICENSE-2.0 and
https://creativecommons.org/licenses/by/4.0/. No public redistribution or final
rights approval is asserted by collecting these materials.

Expanded `audit_repository_lineage.py` to accept an explicit metadata-only
selection. `swe-rebench-budget-lineage-001` resolves all eight budget-cohort
repositories plus all four reserved repositories: no canonical-ID or declared
fork-network-root overlap. Reserved task bodies remain unread. Detached copies,
semantic duplicates, historical relationships and model pretraining exposure
are not excluded; a frozen split is still required.

The Nodebook token auditor can now export the actual token/label arrays under
`--export-tokens`. `swe-rebench-nodebook-token-candidate-001/tokens.json` is an
unapproved candidate, with pinned tokenizer hashes and linked history/tools.
Its token and label hashes exactly match the earlier independent count audit;
the training collator validates 17,353 input positions and 4,183 supervised
next-token targets with no truncation or label-count disagreement. The current
GPU worker still uses a synthetic qualification fixture; it has not yet been
converted into a full corpus trainer. Candidate export is a preparation step,
not evidence of a trained agent or a sufficient 150M-token campaign.


### Rights capture compatibility and restored corpus validation

Datetransform source capture preserves all nine tracked files and MIT license
(Copyright 2020 Brandon Schabell). The Python 3.7 metadata path now uses the
installed backport and compatible canonical path-containment checks. Selected
notices were captured for pandas 1.3.5, NumPy 1.21.6, python-dateutil
2.9.0.post0, pytz 2025.2 and six 1.17.0. Installed pytest 7.1.2 has no
discoverable notice. Default capture still rejects this absence; an explicit
inventory option preserves the missing-notice flag without approving rights.
Both initial failures and a fresh default-denial check are retained.

The matching pytest 7.1.2 upstream source archive was downloaded from PyPI,
verified against its published SHA-256, and its LICENSE preserved separately.
This supplements attribution evidence but does not prove installed Conda build
identity or complete all dependency/observation rights review.

The 83-file Datetransform replay archive was independently restored from R2.
The restored two-example corpus validates at the exact original manifest hash;
both the regenerated schedule and update stream match the original bytes.
Counts remain 31,479 input / 8,757 supervised tokens and two dry updates.
Training admission remains false. Evidence: `datetransform-replay-restore-001`,
`training-corpus-restored-inspect-001`, `training-corpus-restored-schedule-001`.

Current readiness is consolidated in document 39 and linked first from README.
The latest CPU suite remains 288 tests, 264 passed, 24 skipped. No GPU was used.
Next: complete attribution and split/admission evidence while expanding corpus
coverage; do not treat two quarantined examples as sufficient campaign data.


### Current repository identity and issue-duplicate audit

Live GitHub metadata resolves Nodebook and Datetransform plus the four reserved
repositories. No canonical-ID or declared fork-network-root overlap was found
(`current-corpus-lineage-001`). Reserved task bodies were not read.

New `audit_issue_duplicates.py` verifies the pinned candidate cohort and task
shards, validates source metadata before reading candidate issue text, and
records exact UTF-8 hashes separately from whitespace-normalized heuristics.
It covered all 1,575 candidate tasks and found two exact duplicate pairs:
Mobly 164/165 and Hidrokit 121/122. Whitespace screening found the same pairs.
Neither pair includes the current two assembled tasks. Source text equality
is a grouping/review signal, not proof of task equivalence; case and Unicode
forms are deliberately not conflated.

`current-corpus-split-review-001` binds the actual corpus, identity audit and
fingerprint evidence to a validated draft grouping using fork-network IDs and
exact issue hashes. No training admission or frozen split was created. This
review does not exclude detached copies, semantic/patch duplication, vendored
source, unknown hidden evaluation data or model-pretraining exposure. It cannot
be interpreted as a dataset-wide independence guarantee.

Four new tests cover exact-versus-whitespace equality, case/Unicode separation,
order independence and duplicate/empty input rejection. The final CPU suite
ran 292 tests: 268 passed, 24 skipped. Next: complete attribution and task
review while expanding the qualified corpus, and resolve the final split before
training. No GPU was used; P1 remains incomplete.


### Native observation audit and direct-source attribution

Added reusable replay observation inventory with exact text/result identities,
root and wrapped command exit codes, explicit truncation flags, and unknown
status when a flag is absent. It validates event ordering and charged-call
counts against the completed replay receipt. It does not equate successful
tool execution or printed test claims with correctness, and does not remove
failed observations from the training history.

Datetransform: 27 charged calls plus submission; 27 ok results and one error
(the empty no-match grep result, exit 1). No explicit truncation is reported;
20 responses have no truncation flag, including response types without file
content. Nodebook: 35 charged calls plus submission; all report ok, but one
source read is explicitly truncated and 31 responses have no truncation flag.
Do not conflate full token serialization with full underlying observations.
Evidence: `datetransform-observation-audit-001`, `nodebook-observation-audit-001`.

All five Datetransform direct read_file observations match preserved base
source or sequential unique edits under the native line rendering. Three
unique edits were checked, including two in a temporary diagnostic script.
The source attribution record and span hashes are in
`datetransform-file-rights-001`. This closes direct-read byte correspondence
for that trace, not arbitrary shell-output rights or semantic equivalence
to the original teacher's observations. Shell diagnostics and conditioning
fidelity remain explicit review obligations. No rights or training admission
was granted.

Six new tests cover missing versus explicit truncation flags, wrapped errors,
ambiguous/boolean exit codes, event ordering and changed observation hashes.
Final CPU suite: 298 tests, 274 passed, 24 skipped. The two-example corpus,
labels and schedules are unchanged; no GPU was used. Next: complete remaining
attribution and admission review, expand corpus coverage, and qualify GPU
execution only after the exact candidate bundle is ready.
