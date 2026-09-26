# Corrected Engineering Edition

## Scope

This edition extracts the buildable AI-governance architecture from the source papers without adopting unsupported consciousness or quantum claims.

## System model

A consequential action is permitted only when all of the following are true:

1. a named issuer granted a specific subject a specific scope;
2. the grant has started and has not expired;
3. the grant has not been revoked;
4. the system is not frozen;
5. the requested action is no broader than the granted scope;
6. the software and policy versions match the recorded execution context;
7. any required human confirmation is present; and
8. the authorization decision and resulting action are recorded.

If any condition fails, the action is denied and the denial is logged. Missing information is a denial, not an invitation to infer permission.

## Four engineering components

### Consent grant

A consent grant contains an identifier, issuer, subject, permitted scopes, activation time, expiry time, and revocation state. It is a capability record, not proof that consent was informed or freely given; the surrounding human process must establish those facts.

### Tamper-evident audit

Each audit record commits to its sequence number, timestamp, event type, canonical payload, and previous record hash. Alteration becomes detectable during verification. A hash chain does not prevent deletion or guarantee truthful input, so independent witnesses, durable storage, access controls, and monitoring remain necessary.

### Safe de-elevation

Global freeze blocks normal authorization when integrity, policy, or operator confidence fails. Restoration requires a named reviewer and a recorded reason. Restoration does not revive expired or revoked grants.

### Bounded moral memory

Moral memory stores structured lessons tied to an incident, observed harm, corrective action, evidence references, retention limit, and review status. It must support correction, contest, lawful deletion, and bias review. It must never become a hidden reputation score.

## Meaningful human control

Human involvement is meaningful only when the person has time, information, authority, and a usable interface to understand, stop, change, or escalate the action. A confirmation button shown after an irreversible action is not meaningful control.

## Application map

| Project | Immediate integration |
|---|---|
| Maya Node and Aurora | Capability grants, runtime checks, revocation, freeze, restoration review, audit export |
| CARE emergency response | Consent-aware intake, provisional extraction, human dispatch confirmation, uncertainty display, override logging |
| SAGE | Owner-scoped capabilities, offline denial, recovery controls, memory correction |
| Reality Audit | Evidence-class labels, immutable run manifests, preserved null and failed results |
| Flux Drive | Experiment authority, calibration provenance, run manifests, non-claim enforcement |
| AquaShield and CHROMASKIN | Hazard decisions, configuration authority, safe states, test provenance |

