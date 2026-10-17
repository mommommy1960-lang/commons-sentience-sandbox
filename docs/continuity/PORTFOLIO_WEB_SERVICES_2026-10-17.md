# Civic Continuum software and web-service progress — October 17, 2026

Civic Continuum has a working owner-private web workshop with fifteen named software tools. This is a first web release of bounded functions, not fifteen finished inventions or generally available paid services. Mya P. Brown is the founder. The existing public Python repositories remain canonical for their own implementations; the private web workshop is a separate JavaScript implementation.

## Access and working capabilities

[Owner-private workshop](https://civic-continuum-services.myqueen1960.chatgpt.site) requires the owner's signed-in account. The links below are retained for owner review and authorized access; publishing a URL does not grant public access. The public [Maya text-file workflow](https://maya-working-workflow-lab.myqueen1960.chatgpt.site/) remains a separate free bounded service.

| Tool | Direct service page | Bounded capability |
|---|---|---|
| Maya Node | [Open page](https://civic-continuum-services.myqueen1960.chatgpt.site/service/maya) | Prepare exact text, approve it for five minutes, then create one downloadable file. Reuse and revoked permission are refused. |
| SAGE | [Open page](https://civic-continuum-services.myqueen1960.chatgpt.site/service/sage) | Save a note, correct it, freeze memory writes, and resume explicitly. Your notes persist for your signed-in account. |
| Maya–SAGE bridge | [Open page](https://civic-continuum-services.myqueen1960.chatgpt.site/service/bridge) | Choose a saved SAGE note, prepare an exact export, approve it, and create the file once. |
| CERL consent validator | [Open page](https://civic-continuum-services.myqueen1960.chatgpt.site/service/cerl) | Inspect a stored grant against an action, target and purpose. Revoke or wait for expiry and check again. |
| Consent Token | [Open page](https://civic-continuum-services.myqueen1960.chatgpt.site/service/consent) | Create a five-minute permission for a prepared file request, inspect its scope, and revoke it. |
| CUP / Phi | [Open page](https://civic-continuum-services.myqueen1960.chatgpt.site/service/cup) | Register a browser-generated Ed25519 public key, compose and sign a Phi envelope, then submit it to an approved inbox. |
| ATN | [Open page](https://civic-continuum-services.myqueen1960.chatgpt.site/service/atn) | Use the same CUP receiver to deliver node-a to node-b; replay, withdraw inbox consent, or revoke a key and retry. |
| Structural Illegality Block | [Open page](https://civic-continuum-services.myqueen1960.chatgpt.site/service/sib) | Try each of ten project-policy prohibitions or an allowed evidence inspection. Every decision produces a receipt. |
| Aurora core | [Open page](https://civic-continuum-services.myqueen1960.chatgpt.site/service/aurora) | Wake the simulation, grant or revoke planning suggestions, test a request and freeze it. |
| Continuum Archive | [Open page](https://civic-continuum-services.myqueen1960.chatgpt.site/service/archive) | Seal up to 100 files in one manifest, verify the complete bundle, and download a readable evidence report. Changed, missing and added files fail verification. |
| Reality Audit | [Open page](https://civic-continuum-services.myqueen1960.chatgpt.site/service/reality) | Compare two selected files using SHA-256 and byte counts. See unchanged or changed bytes with a downloadable report. |
| Commons Sentience Sandbox | [Open page](https://civic-continuum-services.myqueen1960.chatgpt.site/service/sandbox) | Run the source’s private-disclosure scenario. See two explainable refusals and different safe alternatives. |
| FOS | [Open page](https://civic-continuum-services.myqueen1960.chatgpt.site/service/fos) | Select an archive manifest and request inspection. The service checks its stored digest and your current grant before recording a decision. |
| HRF / Systemic Failure Index | [Open page](https://civic-continuum-services.myqueen1960.chatgpt.site/service/sfi) | Paste identified synthetic cases. Calculate mismatches and missing outcomes separately; empty observations return no rate. |
| CALEXS | [Open page](https://civic-continuum-services.myqueen1960.chatgpt.site/service/calexs) | Start the fictional museum, choose the garden or workshop, pause, resume explicitly or stop. |

## Verified work

- All fifteen direct hosted routes returned HTTP 200 with the expected named page content.
- Web release 0.2 passed 40 of 40 isolated hosted runtime/storage checks. Real D1 write/read and stale-write rejection were exercised; temporary probes were removed.
- The web suite passed 44 local engine/HTTP/SQLite tests, including owner isolation, concurrent single-use execution, multi-file integrity, report accuracy and safety controls at full capacity.
- Combined original-source and web testing passed 324 local tests, with additional pytest subtests reported separately. Shared suites are not counted again for each tool page.
- Production build and TypeScript checks passed. The two executable source demonstrations also passed.
- Archive now handles one to 100 files, up to one MiB combined, detects missing/added/changed files and provides a readable report distinguishing unperformed, successful and failed byte verification.
- Withdrawal controls remain available at capacity. If an additional receipt cannot fit, the response explicitly reports that fact while preserving existing history and applying the safety control.

Local results, hosted runtime results, GitHub CI, Android visual usability and independent users are distinct evidence. The private GitHub job failed before executing tests; replacing remaining tag references with pinned SHAs did not resolve it. A separate public workflow verifies only the six public source repositories without accessing or disclosing private implementation. Its actual result must be checked before reporting a hosted CI pass.

## What remains open

Live AI inference, original Maya Cloudflare editing recovery, the original Maya network adapter, customer payments and automatic fulfillment are not established by these tools. SAGE hardware, scientific/HRF validation, broader CUP network and encryption, the full CALEXS experience specification, independent security review and consenting independent user acceptance remain separate work. A deterministic simulation is not sentience evidence, and file hashes are not proof that document content is true or legally owned.

No customer checkout, renewal, model-provider spending, hardware purchase or new external message was activated by this release. Protected implementation, private correspondence, credentials, customer information and commercial planning remain private. Paused Flux research/watch tasks were not resumed.

## Original public sources

- [Maya Node](https://github.com/mommommy1960-lang/maya-node)
- [SAGE](https://github.com/mommommy1960-lang/sage-situated-companion)
- [CERL](https://github.com/mommommy1960-lang/CERL-Preemptive)
- [CUP / Phi / ATN](https://github.com/mommommy1960-lang/Commons-Unified-Protocol)
- [Aurora](https://github.com/mommommy1960-lang/aurora-sovereign-core)
- [Commons Sandbox](https://github.com/mommommy1960-lang/commons-sentience-sandbox)

See the [partner progress feed](PARTNER_LIVE_UPDATE_FEED.md) for the historical record. The older October 10 list of fifteen engineering directions is a different inventory; this page's fifteen software tracks do not replace the broader portfolio.
