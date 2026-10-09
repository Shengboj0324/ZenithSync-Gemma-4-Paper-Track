# Source-qualified local repair outcome

The unmodified baseline has 321 passed, one failed, and two skipped cases.
The unchanged 439-byte agent patch has 322 passed and two skipped cases.
JUnit represents one expected failure as skipped. All 324 identities pair;
only the target content-length regression changes from failure to pass.
The released verify_task returns resolved=false for baseline and true for patch.

This result uses a local diagnostic environment: explicit checkout import
precedence, Docker bridge networking, Flask 2.2.5, Werkzeug 2.2.3, pytest 9.1.1,
pytest-httpbin 2.1.0, and httpbin 0.10.2. No benchmark assertion, official test
patch, or captured agent patch was changed. The in-process source records match
those of the previous network comparison exactly, including source hashes.
This is not a Kaggle hidden-grader result or evidence of broad task success.

The pinned historical fixture preserves the malformed ASCII Location header.
Upstream implementation: https://raw.githubusercontent.com/pallets/werkzeug/2.2.3/src/werkzeug/urls.py
Downloaded wheel bytes matched PyPI metadata hashes. Image-only replacement
initially failed because the harness injects wheels. Replacing those wheels
still failed because the released harness uses a shared sp_base.tar cache
without a manifest identity. Fresh per-invocation temporary directories remove
that cross-run dependency contamination. Actual runtime versions were recorded
before pytest; the source gate executes inside pytest as well. Earlier failed
attempts are retained and are not relabeled as passes.

All 90 local unit tests passed. No GPU work or model training was performed.
The old HTTP stack is isolated evaluation infrastructure, not a production
service recommendation. Training readiness and official environment parity
remain separate, unproven requirements.
