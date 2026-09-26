# Commons AI Future Program

## External review entry point

This page organizes the Commons Initiative AI-governance research for external technical review, including the diligence priorities identified by Dr. Thomas Ainsworth: authority, revocation, auditability, meaningful human control, and accountable organizational structure.

This is not an endorsement by Dr. Ainsworth or the Human-Centered AI Governance Institute. The Commons Initiative's business-registration, domain-infrastructure, and organizational-accountability gates remain open and are tracked separately in the [organizational readiness meter](../DR_THOMAS_ORGANIZATIONAL_READINESS_METER.md).

## Central proposition

The program asks whether powerful AI can remain useful while every consequential capability is:

- explicitly granted and narrowly scoped;
- time-bounded and immediately revocable;
- unable to expand its own authority;
- forced into a safer mode when authorization or integrity fails;
- recorded in a tamper-evident audit trail;
- subject to meaningful human confirmation at irreversible decision points; and
- allowed to retain only bounded, reviewable lessons from prior decisions.

The present contribution is a governance architecture and test program. It is not evidence of machine consciousness, quantum communication, temporal control, or a new law of physics.

## Six-part evidence package

1. [Canonical volume index](01_CANONICAL_VOLUME_INDEX.md)
2. [Duplicate and missing-volume audit](02_ARCHIVE_AUDIT.md)
3. [Claim-evidence ledger](03_CLAIM_EVIDENCE_LEDGER.md)
4. [Corrected engineering edition](04_CORRECTED_ENGINEERING_EDITION.md)
5. [Speculative research edition](05_SPECULATIVE_RESEARCH_EDITION.md)
6. [Implementation and test program](06_IMPLEMENTATION_AND_TEST_PROGRAM.md)

## Working software

The repository now includes a small reference implementation in `commons_governance/` and tests in `tests/test_commons_governance.py`. The software covers:

- scoped consent grants;
- expiry and revocation;
- global freeze and reviewed restoration;
- hash-chained audit events;
- bounded moral-memory records; and
- fail-closed authorization decisions.

Run the reference checks with:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## What a reviewer can do

1. Inspect the claim-evidence ledger.
2. Reproduce the software tests.
3. Attempt unauthorized scope expansion, replay, expiry bypass, ledger tampering, and restoration without review.
4. Identify the most important missing control.
5. Treat every failed test as a preserved research result.

