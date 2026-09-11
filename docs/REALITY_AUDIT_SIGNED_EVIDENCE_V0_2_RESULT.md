# Reality Audit signed evidence v0.2 result

## Decision

**FUNCTIONAL IDENTITY-AUTHENTICATED PROTOTYPE — NOT A TRUSTED PUBLIC INFRASTRUCTURE.**

Reality Audit evidence bundles can now be wrapped in Ed25519 signatures, checked against an explicit public-key record and revocation registry, and uniquely recorded in a local hash-chained transparency log.

The implementation authenticates possession of a private key. It does not independently establish a person's legal identity, supply a trusted timestamp, prevent deletion or rollback of the entire local log, or constitute certification.

## Implemented

- Ed25519 key generation;
- SHA-256-derived public-key identifiers;
- private/public key match enforcement;
- refusal to sign a bundle that fails existing integrity verification;
- signed statements binding bundle digest, key identifier, signer label, nonce, and local UTC time;
- unique nonce enforcement and replay rejection;
- hash-chained transparency receipts;
- exact envelope inclusion verification;
- explicit key revocation registry;
- fail-closed verification after revocation;
- private-key file mode `0600` in the CLI;
- tamper, replay, wrong-key, and revocation tests.

## End-to-end demonstration

The existing official Fermi 2FLGC `KILLED_BY_NULL` evidence bundle was used as the test payload.

1. Generated a fresh demonstration Ed25519 keypair.
2. Wrote the private-key file with mode `0600`.
3. Signed the verified bundle using nonce `fermi-2flgc-demo-20260911`.
4. Appended a unique receipt to a new transparency log.
5. Verified bundle integrity, digest binding, signature/key identity, active key state, log-chain integrity, and unique inclusion: **PASS**.
6. Attempted nonce reuse: **REJECTED**.
7. Altered the signed statement in the automated test: **REJECTED**.
8. Tested a mismatched private/public keypair: **REJECTED**.
9. Revoked the signing key and verified again: **FAIL-CLOSED**, CLI exit code `2`.

Focused automated validation: **8 tests passed** across signed evidence and the pre-existing bundle compiler/verifier.

No demonstration private key was committed.

## Files

- `reality_audit/product/signed_evidence.py`
- `scripts/reality_audit_claim.py`
- `tests/test_signed_evidence.py`
- `requirements.txt`

## Security boundary

This is accurately described as **tamper-evident where demonstrated**. It must not be described as tamper-proof, unhackable, a deployed global transparency network, proof of legal identity, or a trusted timestamp service.

The local JSON log detects entry mutation and nonce replay, but an attacker controlling storage could delete the whole log or replace it with an older internally valid copy. Closing that gap requires an independently witnessed append-only service, signed tree heads/checkpoints, consistency proofs, durable replication, and rollback monitoring.

Private keys still require a production key-management system, recovery procedure, rotation policy, compromise response, and separation between development, customer, and service keys.

## Product meaning

This closes one major gap identified in Reality Audit v0.1: evidence can now be attributed to a cryptographic key and invalidated after key compromise. It strengthens the sellable **Reality Audit Claim Stress Test** and supplies a concrete bridge to Maya Node's scoped-consent architecture.

It does not establish patent novelty, freedom to operate, regulatory compliance, or exclusivity.

## Highest-value next action

Bind a Maya Node authorization grant to the signed Reality Audit statement, require single-use grant consumption for signing, and place signed log checkpoints in an independently controlled witness location. Then test grant, denial, expiration, replay, revocation, freeze/restore, and log rollback end to end.
