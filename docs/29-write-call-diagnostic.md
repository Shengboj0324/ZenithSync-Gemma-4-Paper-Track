# Native write-call diagnostic

Status: prepared and locally preflighted; no diagnostic inference has run.

## Purpose and experimental scope

The first reserved development repair attempt repeatedly produced write calls
without a filepath. Its raw generations were not captured, so the cause remains
unknown. The second attempt and four small serialization probes succeeded.
This experiment distinguishes invalid native output, API parsing disagreement,
instruction mismatch, and output truncation. It cannot retrospectively identify
the first attempt's cause or estimate general agent reliability.

The fixed plan contains two string fixtures, two contexts, and three repeats
(12 requests). One fixture is a simple assignment; the other includes Unicode,
quotes, braces, an f-string, and a key resembling an argument name. The short
context retains the system message; the repository context retains the captured
24-message development history. Both end with the same explicit write request
and preserve the same nine tool schemas. Context order alternates by repeat.
Temperature is zero, seed is zero, and output is capped at 4,096 tokens.
Repeated requests are consistency checks, not independent statistical samples.
No returned file-writing tool is executed.

## Exact-input qualification

`scripts/prepare_write_diagnostic.py` verifies the four tokenizer/configuration
files against the model intake manifest. It reproduces all 11,537 recorded prompt
tokens from `repair-attempt-002/http/0012` exactly before preparing any fixture.
Two local serialization issues were found and corrected: Transformers returned a
mapping unless `return_dict=False` was explicit; vLLM's OpenAI content mode wraps
text in structured parts before rendering. The system-message list branch adds
one space, explaining the initial 11,536 versus 11,537 mismatch. No token was
manually inserted to force a match.

Evidence: `evidence/p1/write-diagnostic-prepare-001/receipt.json` and
`evidence/p1/write-diagnostic-preflight-001/preflight.json`. The preflight verifies
the artifact manifest and regenerates every case's token count and token hash.
The plan is in `artifacts/official/p1-write-diagnostic-001/plan.json`.

## Interpretation and isolation

`zenithsync/tool_diagnostic.py` implements a deliberately narrow independent
grammar for one native write_file call with two string arguments. Four focused
tests passed, including malformed delimiters and parser disagreement. Native
delimiter tokens inside literal file content are outside its grammar; this is
not a general replacement tool parser. Retain raw token IDs, decoded output,
API output, exact request, and classification for each live request.

These are synthetic diagnostic fixtures combined with a reserved development
context, not a training corpus. Do not promote them into training or independent
confirmation evaluation. A successful result would qualify only this small
experiment, not establish production readiness or mathematical correctness of
arbitrary model-generated code.

## Remaining work before GPU execution

The runner is preflight-only by default. A POSIX interval timer now interrupts
the request loop after 1,500 seconds, including blocked socket reads. A local
HTTP server test confirmed interruption during a stalled response body and
execution of cleanup; a second test confirmed an existing timer is preserved.
The 120-second urllib timeout remains a socket timeout, not a per-request
wall-clock deadline. The signal timer does not guarantee interruption of
arbitrary native code or stop Pod billing; the serving supervisor separately
enforces its session deadline. All 87 local tests passed after this change.
Package and publish/restore the required artifacts through R2 before live use.
Deployment bundle 005 does not include these new diagnostic files.

After local preparation is finished, pause for the user's Pod restart and a
fresh session limit. The prior four-hour session approval is not a new session
authorization. No training is involved in this diagnostic.
