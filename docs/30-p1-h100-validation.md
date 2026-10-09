# P1 H100 validation and content-fidelity finding

The replacement Pod `609g4lt940xrxe` used an H100 80 GB HBM3, reporting 81,559
MiB and driver 580.126.09. Its 201 GB standard network volume is in US-MO-1.
The user approved four hours at the observed $3.99/hour rate. The recorded
session began October 8, 2026 at 7:35 p.m. Pacific, with an 11:35 p.m. deadline.
No training ran.

## Deployment evidence

The model (23,297,590,856 bytes) and 250 serving wheels (5,331,545,654 bytes)
were restored from R2 and fully hash-verified. Network-volume installation of
the small bootstrap environment was slow and was explicitly terminated. A
fresh local-disk bootstrap installed successfully. Models and wheels remain
persistent; virtual environments on the container disk require reconstruction
after a stop. The initial extraction reported ownership warnings; subsequent
byte verification passed after removing generated Python caches.

The corrected serving lock installed successfully. All 250 versions matched,
all nine import probes passed, and all four HTTP middleware checks passed.
Server startup took 128.94 seconds. Engine logs reported 19.63 GiB for loading
the model; this is not whole-run peak memory. The real generated file-read and
unpredictable-marker continuation probe passed.

## Diagnostic result

| Fixture | Short context | Repository context |
|---|---:|---:|
| Simple assignment | 3/3 exact | 3/3 exact |
| Structured Python with Unicode | 3/3 exact | 0/3 exact |

All 12 server prompt-token hashes matched the prepared inputs. All native
calls agreed with their API-parsed arguments. All three failures changed the
requested globe character into literal `\ud83c\udf0d` escapes in Python source.
AST literal extraction, without executing generated code, confirmed that this
creates two surrogate code points; encoding that string as UTF-8 raises
UnicodeEncodeError. The requested string is a valid Unicode scalar and is
UTF-8 encodable. This is a semantic content defect, not merely a different
textual spelling of equivalent code.

These are three fixed-seed repeats of one failing context/fixture combination,
not three independent tasks or an estimated population failure rate. No parser
disagreement occurred in this experiment. The result does not explain the
missing-filepath failures from the first A100 repair attempt. The prompt's JSON
serialization escapes non-ASCII characters, which is a candidate contributing
factor; a controlled literal-Unicode versus escaped-JSON comparison is needed
before claiming causality. Do not add blanket escape decoding to the executor:
literal backslashes can be intentional user content.

## Retained evidence and closeout

`evidence/p1/h100-validation-001/` retains raw requests, responses, decoded
tokens, classification records, runtime checks, restore receipts, and server
logs. All 70 remotely collected files matched their local hashes. The derived
`analysis.json` records the semantic checks. The 73-file evidence archive is
packaged under `artifacts/official/p1-h100-evidence-001`; publication and restore
receipts live separately under `evidence/p1/`.
Publication, independent restoration, and all 73 restored archive-member hashes
passed (`h100-evidence-publish-001` and `h100-evidence-restore-001`).

The server stopped with return code zero and the GPU reported 0 MiB afterward.
Temporary R2 credentials and the session SSH key entry were removed. The user
was asked to stop the Pod to end billing; this report does not claim the Pod was
stopped or that server shutdown ends compute charges.

P1 remains partially validated. This is no training-readiness, production
reliability, official-environment-parity, or universal correctness guarantee.

## Prepared follow-up: prompt representation

`scripts/prepare_unicode_comparison.py` prepares two representations of the same
structured-content request: JSON with escaped non-ASCII characters and JSON
with literal Unicode. Both are crossed with short and repository contexts,
with three fixed-seed repeats and alternating representation order (12 requests).
The intended decoded arguments are equal, the escaped control payloads are
identical to those measured above, and all other payload settings are retained.
Token counts are 1,726 versus 1,718 for short context and 9,800 versus 9,792 for
repository context. The eight-token change is part of the representation
intervention, not an independently controlled token-length effect.

The plan and unchanged qualified diagnostic runner are in the 14-file
`p1-unicode-comparison-bundle-001`, published to R2 and independently restored
as `restored-unicode-comparison-001`. Preparation and transfer evidence is under
`evidence/p1/unicode-comparison-*`. This remains a prepared experiment, not a
fix or measured improvement. A successful literal arm would support a narrow
prompt-representation effect on this fixture; it would not prove general
Unicode reliability or justify silently transforming arbitrary tool content.

Use the original per-request classifications and raw evidence. Retain failures,
do not change the expected content, and do not treat the repeats as independent
statistical samples. Run only after the user resumes the GPU session; retain
the existing 25-minute diagnostic deadline and separate session supervisor.

## Follow-up executed within the original approved window

The Pod was subsequently observed running with its direct SSH port changed to
11022 and the temporary serving environment absent. The model and code on the
network volume passed full hash verification after this apparent restart. The
serving environment was rebuilt offline; all 250 versions, nine imports, HTTP
checks and the real file-read continuation passed again. The original approved
deadline was preserved. Requiring another approval while this Pod remained
running inside the four-hour allowance was unnecessary; the comparison proceeded
under that existing authorization.

| Requested-argument spelling | Short context | Repository context |
|---|---:|---:|
| Escaped JSON | 3/3 exact | 0/3 exact |
| Literal Unicode JSON | 3/3 exact | 3/3 exact |

All 12 requests completed with matching prepared prompt-token hashes and
unchanged source and artifact identities. The three escaped repository failures
again create two surrogate code points that fail UTF-8 encoding. Literal Unicode
resolved this particular fixture in all observed repeats. This supports a narrow
representation effect, not general repair reliability; token length and cache
effects were not separately isolated, and repeats are not independent tasks.
No production serializer or file executor was changed based on this small test.

Evidence is under `evidence/p1/unicode-validation-001/`: all 69 remotely collected
files were independently hash-matched locally, with an AST-only semantic analysis
in `analysis.json`. The server stopped cleanly and reported 0 MiB afterward;
the temporary SSH key was removed. The agent did not stop the Pod. The model,
wheels, code, and experiment results remain on the persistent volume.
The 72-file follow-up evidence archive was published to R2, independently
restored, and every archive member hash verified. Receipts are under
`evidence/p1/unicode-evidence-publish-001` and `unicode-evidence-restore-001`.

## Production-boundary applicability check

The official SWE-gemma response helper uses `ensure_ascii=False`; its ADK
boundary parses that JSON into an object. ADK 1.36.1's `_safe_json_serialize`
also uses `ensure_ascii=False` when converting a function response into a tool
message. Thus the actual read-tool response path already preserves literal
Unicode. The escaped request in our failing comparison was deliberately
constructed inside the diagnostic's user-message text, not introduced by this
production adapter. Escapes in an outer HTTP JSON envelope alone do not imply
that the decoded text visible to the model contains escaped characters.

`scripts/verify_model_text_boundary.py` exercised those actual installed
functions, first matching their source bytes to the released wheels. Six
synthetic fixtures passed: non-BMP characters, multilingual text, combining
characters, literal backslashes, Python source, and control characters. JSON
round trips preserved exact UTF-8 bytes, non-ASCII scalars remained literal in
model-facing text, and tool-call linkage remained intact. Evidence:
`evidence/p1/text-boundary-001/receipt.json`. This tests adapters, not an actual
sandbox file read or another model generation.

Consequently no production serializer patch is warranted by the observed
fixture. Keep the measured model weakness as a development finding; do not
claim that a real agent defect was repaired or that this explains the original
missing-filepath failures. The next useful agent-quality evidence is broader
real-task behavior, not more repetitions of this one diagnostic.
