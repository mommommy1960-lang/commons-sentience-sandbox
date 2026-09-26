# Sage–Aurora Integration Contract

## Purpose

This contract defines how the user-facing Sage companion should call Aurora's bounded continuity core. It is an interface boundary, not a claim that the two repositories are already integrated.

## Responsibilities

### Sage

Sage owns:
- conversation and situated context;
- presentation of memories and decisions;
- user-facing explanations;
- collecting explicit user consent;
- sending a proposed operation to Aurora.

Sage must not directly mutate protected memory, permissions, identity, or external devices.

### Aurora

Aurora owns:
- permission evaluation;
- memory provenance and correction state;
- freeze and shutdown state;
- rollback fencing;
- audit-chain generation and verification;
- final allow, deny, or pause decision.

Aurora must not treat trust, affection, familiarity, urgency, memory, or identity as permission expansion.

## Operation envelope

Every requested operation should carry:
- operation_id;
- actor;
- requested_level;
- purpose;
- target;
- consent_reference;
- provenance;
- replay_key.

Aurora returns:
- decision: allow, deny, or pause;
- reason;
- audit_hash;
- required_next_step;
- state_version.

Missing or ambiguous fields must produce pause or deny, never implicit approval.

## Memory lifecycle

1. Sage proposes a memory with source and confidence.
2. Aurora validates the record.
3. The user can accept, correct, export, or delete it.
4. Corrections preserve the prior record as history rather than silently overwriting it.
5. Retrieval must not grant authority.
6. Restore requires schema validation, duplicate detection, and rollback authorization.

## External-world boundary

No physical device, account, message, purchase, microphone, camera, door, or appliance may be controlled merely because a conversational request sounds trusted. Such operations require a separately configured permission and an explicit approval path.

## Evidence status

This contract is a design artifact. It does not prove cross-repository integration, device control, production security, or continuous background operation. The next implementation step is a small adapter with contract tests and no external side effects.
