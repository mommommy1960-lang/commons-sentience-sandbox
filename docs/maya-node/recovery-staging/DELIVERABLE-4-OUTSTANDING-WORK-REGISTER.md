# Deliverable 4 — Outstanding Work Register

**As of:** October 31, 2026  
**Scope:** documentation, evidence review, and readiness tracking. This register does not authorize infrastructure changes or pilot launch.

| Gate / workstream | Task | Owner | Dependencies | Required evidence / exit criteria | Status |
|---|---|---|---|---|---|
| Evidence | Supply original sanitized HAR/network captures and raw response records | Jim / evidence operator | Existing original browser/session captures | Original files, redaction record, capture timestamps, provenance, hashes where available | BLOCKED — not included in supplied package |
| Evidence | Supply raw receipt, event, D1 readback, and row inventory exports | Jim / evidence operator | Read-only access to original evidence source | Raw exports with credentials/session data removed; exact environment provenance | BLOCKED — narrative excerpts only |
| Review | Review evidence package and reconcile each claim to a raw artifact | Mya / Bruce | Evidence artifacts above | Evidence index with verified/partial/unavailable disposition | PENDING |
| Provider | Obtain Cloudflare D1 backup/PITR answer for support case 17489131 | Jim / account owner | Provider support response | Written feature, retention, eligibility, restore semantics, and case status | PENDING |
| Recovery planning | Review revised isolated Phase 3 plan | Mya / Bruce / Jim | Provider capability confirmation | Approved plan with source/destination identity controls | PENDING |
| Recovery execution | Conduct native D1 recovery drill | Jim | Separate explicit written approval naming exact disposable UUIDs and operation | Test A/Test B logs and isolated readbacks | NOT AUTHORIZED |
| Security | Review auth middleware, token validation, roles, and owner isolation | Jim / security reviewer | Relevant code and raw negative-test evidence | Code review plus forged/expired/wrong-owner/wrong-role test results | PENDING |
| Integrity | Review receipt/audit guarantees and privileged D1 mutability | Jim / security reviewer | Schema, access model, raw receipt/event records | Documented threat model and honest integrity claims | PENDING |
| Accessibility | Run keyboard, focus, accessible-name, contrast, zoom/reflow, and screen-reader checks | Jim / accessibility reviewer | Test environment and supported browser/device list | Recorded results, defects, remediation, retest | PENDING |
| Privacy | Reconcile privacy notice with actual data flows, retention, and deletion behavior | Mya / privacy reviewer | Current policy and implementation inventory | Approved policy-to-implementation review | PENDING |
| Monitoring | Design runtime monitoring and alerting; keep webhook unbound | Jim | Log coverage and alert requirements | Design, ownership, retention, escalation; later test separately approved | PENDING |
| Demo | Prepare founder-guided synthetic demo checklist and limitations | Mya / Jim | Repeatable synthetic workflow and evidence | Step-by-step checklist, reset/retention rules, known limitations | PARTIALLY COMPLETE — one walkthrough reported |
| Partner pilot | Draft onboarding, scope, consent, support, and escalation documents | Mya / Jim | Legal/privacy review | Partner-approved scope and consent; no real data until gates pass | IN PROGRESS |
| Business/legal | Complete LLC, banking, insurance, licensing, and operating-readiness review | Mya | External filings and professional advice as appropriate | Verified filings and documented decisions/costs | PENDING |
| Billing | Stripe sandbox checkout evaluation | Jim | Separate scope review and explicit approval; test-mode controls | Test dashboard evidence and no live charge | OUT OF SCOPE — no approval in this issue |
| Production | Any production deployment, DNS/routing, secret/binding, or webhook change | Mya / authorized operator | Separate change plan, review, and explicit approval | Approved change record and rollback plan | OUT OF SCOPE |
| Data | Any pantry, partner, customer, or other real organizational data | Mya / organization | Legal/privacy/security readiness and explicit consent | Approved data-handling plan and authorization | NOT AUTHORIZED |

## Current decision gates

1. **Evidence gate:** raw source artifacts must be supplied; excerpts in a narrative are not equivalent to original captures.
2. **Provider gate:** Cloudflare's actual D1 recovery capabilities and support-case status must be documented.
3. **Review gate:** Mya/Bruce review the evidence, readiness matrix, and recovery plan.
4. **Execution gate:** Phase 3 remains unapproved until a separate written approval specifies exact disposable database UUIDs and permitted operations.
5. **Pilot/data gate:** external partner participation and real organizational data require separate scope, consent, legal/privacy/security review, and approval.

## Standing restrictions

No commands, database creation/writes/deletes/restores/migrations, secrets or bindings, deployments, DNS/routing, billing/checkout, webhook activation, live email, cleanup, or real organizational data are authorized by this register. Preserve every existing environment and test record.
