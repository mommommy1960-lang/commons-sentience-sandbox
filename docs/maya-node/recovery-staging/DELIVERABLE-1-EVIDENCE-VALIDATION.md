# Deliverable 1 — Evidence Validation Package

**Review state:** assembled from the founder-supplied October 31, 2026 report; not independently replayed or authenticated by this repository commit.  
**Environment described by report:** Maya Node Recovery Staging.  
**Data classification:** synthetic test evidence only.  
**Safety:** documentation only; no environment was accessed or changed for this document.

## Evidence index

| ID | Evidence described | Source/status | What it supports | Limitation |
|---|---|---|---|---|
| E1 | `POST /api/signin` request/response; HTTP 200 | Founder-supplied sanitized text excerpt; original HAR/network export not attached | Sign-in endpoint reportedly accepted the test credentials and returned a token | Not an original browser capture in this repository; token omitted entirely |
| E2 | Synthetic execution receipt; success; `synthetic_workflow_submission`; `2026-10-31T08:34:40Z`; parser `schema_v1_strict` | Founder-supplied report excerpt | A synthetic workflow reportedly completed and produced a receipt | Raw response body/export and integrity metadata not attached |
| E3 | D1 readback for synthetic message | Founder-supplied query and sanitized record excerpt | A corresponding synthetic row reportedly existed in `recovery_messages` | No raw CLI/API output, query session metadata, or independently verified database identity attached |
| E4 | Session revocation sequence: request reportedly 200 before sign-out and 401 afterward using the same session | Founder-supplied before/after narrative | Session invalidation behavior for that test session | Original request/response captures, sign-out response, and token-correlation proof not attached |
| E5 | Event log / event record | Mentioned in prior supplied project report; no raw event export in this package | Potential audit/event trace | Not independently inspectable; do not treat as verified evidence here |
| E6 | Table/row inventory | Report identifies `recovery_sessions` and `recovery_messages`, with one test session and one test message | Reported footprint of walkthrough | Needs a timestamped read-only inventory export to confirm completeness |

## Sanitized excerpts as reported

The supplied report identifies the sign-in request as:

```http
POST /api/signin
Host: [staging Worker host omitted from this public evidence summary]
Origin: [Workflow Lab origin omitted from this public evidence summary]
Content-Type: application/json

{"email":"[TEST ACCOUNT REDACTED]","accessSecret":"[REDACTED]"}
```

The response was reported as HTTP 200 with a JSON token field. **The token value and all token fragments are intentionally excluded.** The test-account email, exact host/origin, database UUID, session token, and other operational identifiers are not repeated in this public-facing summary.

The receipt was reported to contain:
- status: `success`
- action: `synthetic_workflow_submission`
- timestamp: `2026-10-31T08:34:40Z`
- parser: `schema_v1_strict`
- a synthetic record reference (redacted here)

The reported readback query selected the test row by its synthetic record identifier from `recovery_messages`. The row content was described as a synthetic administrative-boundary test prompt. No session token, token hash, account email, or full row payload is reproduced here.

## Revocation sequence — reported, not independently verified

1. A request using the active test session reportedly returned HTTP 200.
2. A sign-out request reportedly deleted that session from `recovery_sessions`.
3. A subsequent request using the same session reportedly returned HTTP 401.

This is evidence of the reported revocation test only. It does not establish that all authorization boundaries, token-forgery defenses, role checks, or cross-owner isolation have been tested.

## Required raw artifacts still outstanding

- Original sanitized browser HAR/network capture for sign-in, synthetic submission, sign-out, and post-revocation rejection.
- Exact sanitized response headers and bodies for each step, with all credentials and reusable tokens removed.
- Raw receipt and event-log exports, preserving timestamps and stable synthetic IDs while redacting account/session data.
- Raw read-only D1 query output plus command/query context sufficient to identify the environment without publishing credentials.
- Read-only table/row inventory before and after the walkthrough, including any rows created or modified.
- Evidence provenance: capture tool, capture time, operator, environment, and cryptographic file hashes where available.

**Do not reconstruct missing raw captures from this narrative.** Mark unavailable items as unavailable until original artifacts are supplied. No cleanup or deletion is authorized.
