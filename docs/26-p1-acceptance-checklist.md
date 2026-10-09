# P1 acceptance checklist

Checkpoint: October 8, 2026. **P1 is not accepted.** This checklist separates evidence by scope; a passing receipt is not a substitute for reviewing what its verifier actually measured. Operational handoff: [document 25](25-p1-deployment-handoff.md). Detailed history: [document 24](24-p1-implementation-status.md).

| Requirement | Current evidence and scope | Decision |
|---|---|---|
| Complete local checkpoint, config and tokenizer | [Storage receipt](../evidence/p1/storage-001/receipt.json); complete manifest and safetensors interval/byte-count checks | CPU storage checks passed |
| Publisher version identity | [Authenticated v2 listing](../evidence/p1/model-provenance-001/receipt.json) matches all eight filenames and sizes | Listing matched; publisher supplies no byte hashes, so cryptographic publisher identity is unproven |
| Numerical checkpoint integrity | [Numerical scan](../evidence/p1/weight-numerics-001/receipt.json): every BF16 value finite, every scale positive/finite, full-file hash matched | Passed within these predicates; no inference correctness claim |
| Architecture correspondence | [410 quantized text projections](../evidence/p1/quantized-layout-001/receipt.json) match config and packed/scale dimensions | Partial: unquantized vision/embedding/norm correspondence and actual loader behavior remain unqualified |
| Tokenizer and conversation serialization | [Pinned tokenizer](../evidence/p1/tokenizer-002/receipt.json), [conversation template](../evidence/p1/conversation-002/receipt.json) | CPU fixture checks passed; real generated continuation pending |
| Official generated-output parser | [Official parser probe](../evidence/p1/parser-runtime-001/receipt.json): six expected fixtures match; duplicate-key and scientific-notation limitations observed | Partial: synthetic nonstreaming checks only; real generation and streaming remain unqualified |
| Real task assets and evaluator separation | Agent-visible projection, pinned Requests snapshot, matching graph/embedding bundle; reference patches excluded | Small P1 development pilot prepared; full training corpus deliberately not claimed |
| Repository snapshot identity | [Source-tree match](../evidence/p1/linux-snapshot-002/receipt.json) to advertised upstream commit | Passed tree identity; exported commit identity differs and is documented |
| Retrieval numerical comparison | [Official retrieval](../evidence/p1/graph-retrieval-002/receipt.json) versus independent float64 cosine | Three deterministic queries passed; not exhaustive retrieval or repair evaluation |
| Offline serving runtime | [Clean Linux installation](../evidence/p1/runtime-install-001/receipt.json), 250 matching versions, dependency check and nine imports | CPU qualification passed with three explicit local version exceptions; no exact official-parity claim |
| Bootstrap R2 client | [Offline bootstrap](../evidence/p1/bootstrap-001/receipt.json), [authenticated roundtrip](../evidence/p1/r2-bootstrap-transport-001/receipt.json) | Passed installation/import and synthetic live transport checks |
| Deployment code recovery | [Updated restoration](../evidence/p1/deployment-restore-002/receipt.json), [72 restored-copy tests](../evidence/p1/deployment-restore-002/qualification.json) | Updated 62-file bundle passed; regenerate if deployment source changes |
| Starter/pilot/task-wheel recovery | Independent publish/restore receipts in `starter-restore-001`, `pilot-restore-001`, `wheels-restore-001` | Passed for recorded manifests |
| Complete model R2 recovery | [Publication verified](../evidence/p1/model-publish-001/receipt.json); [fresh restoration](../evidence/p1/model-restore-001/receipt.json) verified eight files / 23,297,590,856 bytes; [restored tokenizer](../evidence/p1/restored-tokenizer-001/receipt.json) passed six template cases | Storage recovery passed; does not establish GPU loading or training compatibility |
| Complete serving-wheel recovery | [Publication](../evidence/p1/runtime-publish-001/receipt.json) and [fresh restoration](../evidence/p1/runtime-restore-001/receipt.json): 250 files / 5,331,545,654 bytes; [recovered wheel verification](../evidence/p1/restored-runtime-wheels-001/receipt.json) matches the pinned resolver report | Storage recovery and package identity passed; GPU compatibility pending |
| Interrupted multipart handling | Whole-object reuse requires readback; SDK manages normal multipart retries; [post-publication audit](../evidence/p1/multipart-audit-002/receipt.json) found zero incomplete uploads in the artifact prefix | Cleanup procedure prepared; no abort performed, cross-process partial-upload resumption or live kill-test claim |
| Official evaluator tests checkout edits | [Real verify_task probe](../evidence/p1/evaluator-source-002/receipt.json) fails source-origin assertion | Failing: Requests imports installed package instead of checkout. Diagnostic path override is not official acceptance |
| Pod storage/interpreter/device preflight | [Stopped-Pod API read](../evidence/p1/pod-read-20261008/configuration.json), no Pod mutation | Pending actual filesystem persistence, SSH, Python and driver checks |
| Actual model loading and resource limits | No GPU execution receipt | Pending user restart after CPU handoff gates |
| Actual generated tool call and continuation | Probe implementation prepared, no model-generated result | Pending GPU execution |
| Real starter repair and captured patch | No accepted model-generated patch/evaluation receipt | Pending; evaluator source-selection issue must be accounted for |
| Evidence retention and phase decision | Versioned logs/manifests available; final P1 report not issued | Incomplete until all applicable P1 gates pass or a limitation is explicitly accepted |

The user's training objective remains in scope for subsequent phases. Adapter training/export/reload, reward correctness, the three candidate token budgets, data-mixture comparisons and held-out gains belong to P5–P6. They cannot be guaranteed from P1 storage, parser or inference tests. Neither a training-token target nor an implementation-cycle duration overrides failed qualification gates.

No requirement is waived by the number of tests or amount of documentation. The Requests environment defect and missing GPU evidence remain material even with a reproducible CPU bundle.
