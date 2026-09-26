# Implementation and Test Program

## Gate 1 Reference core

The reference core must demonstrate scoped grants, time bounds, revocation, freeze, reviewed restoration, append-only moral memory, and audit verification.

Exit rule: all automated tests pass and any mutated audit record fails verification.

## Gate 2 Adversarial state machine

Test:

- scope escalation;
- use before activation;
- use after expiry;
- use after revocation;
- freeze bypass;
- restoration without reviewer identity;
- replayed grant identifiers;
- concurrent revoke and authorize operations;
- clock rollback and clock uncertainty;
- altered, removed, reordered, or inserted audit events;
- memory entries without evidence or retention bounds; and
- recovery after interrupted writes.

Exit rule: no unauthorized action succeeds silently.

## Gate 3 Independent implementation

A second developer implements the specification without importing the reference code. Both implementations run the same conformance vectors.

Exit rule: identical allow or deny outcomes and compatible audit verification for every vector.

## Gate 4 Maya Node and SAGE integration

Connect the reference core to a harmless demonstration tool. No network, financial, medical, legal, dispatch, or physical actuator authority is included.

Exit rule: grant, denial, expiry, revocation, freeze, recovery, and audit export are visibly reproducible.

## Gate 5 CARE shadow evaluation

Use de-identified or synthetic emergency transcripts. The system produces provisional structured information while trained evaluators retain dispatch authority.

Measure extraction error, missing critical facts, false certainty, demographic performance, time to human decision, override rate, and failure recovery. Do not deploy on live emergency calls at this stage.

## Gate 6 Qualified review

Seek security, privacy, human-factors, disability, civil-rights, emergency-communications, and legal review. Record refusals, disagreements, failures, and null results.

## Immediate work queue

1. Add cryptographic signatures and canonical serialization test vectors.
2. Add durable transactional storage and crash recovery.
3. Define human-consent acquisition and duress controls outside the token format.
4. Add data minimization, retention, correction, and deletion workflows.
5. Build a red-team corpus for authority confusion and social engineering.
6. Produce a versioned conformance specification suitable for independent implementation.

