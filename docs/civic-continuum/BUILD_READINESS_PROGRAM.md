# Civic Continuum Build-Readiness Program

## Purpose

This document defines the minimum evidence package required before a Civic Continuum project is sent to a builder, supplier, reviewer, funder, or pilot participant.

A paper can prove that a model is internally coherent, dimensionally consistent, reproducible, and worth testing. It cannot prove a physical effect that has not been measured.

## Evidence standard

Every project package must include:

1. exact user problem and intended function;
2. system boundary and operating envelope;
3. established mechanisms versus hypotheses;
4. requirements with units and tolerances;
5. mathematical model with dimensional checks;
6. assumptions and sensitivity analysis;
7. materials, software, energy, cost, and supply constraints;
8. hazards, misuse cases, privacy, and regulatory boundaries;
9. failure-mode and effects analysis;
10. verification matrix;
11. instrumentation and calibration plan;
12. pass, fail, and stop criteria;
13. independent-review requirements;
14. prototype drawings or sanitized interfaces;
15. revision history and evidence log.

## Mathematical discipline

For every equation, the package must show:

- what each symbol means;
- units for every term;
- the valid operating range;
- known constants and their sources;
- uncertainty or tolerance;
- what observation would falsify the model.

For ordinary mechanics, the baseline must remain visible:

`F_net = m a`

For an alleged propulsion effect, the decisive balance is:

`Delta p_vehicle + Delta p_exhaust + Delta p_radiation + Delta p_environment = 0`

A claimed net force is not established until all relevant momentum channels are measured or bounded. A simulation result is evidence that the simulation behaves as coded, not evidence that an unmeasured physical device produces the same effect.

## First build-ready wave

### 1. Maya Node Founding Review

**Deliverable:** repeatable human-delivered design review.

**Paper package:** intake form, authority-boundary rubric, freshness and expiry checks, revocation questions, adversarial test template, report template, correction and refund policy.

**Verification:** two independent reviewers apply the same rubric to the same sanitized design and produce comparable findings.

**Market gate:** three supervised paid reviews with documented scope, delivery time, customer feedback, and no unsupported certification language.

### 2. Consent Token / CERL demonstrator

**Deliverable:** small software state machine.

**Required states:** requested, granted, denied, expired, revoked, frozen, restored, executed, audited.

**Required invariants:**

- denied authority cannot execute;
- expired authority cannot execute;
- revoked authority cannot execute;
- frozen authority cannot execute;
- restore requires an explicit authorized transition;
- each single-use token is spent at most once;
- audit records detect tampering;
- user preferences never expand authority.

**Verification:** exhaustive transition tests, replay tests, concurrent-write tests, rollback tests, tamper tests, and negative-path tests.

### 3. SAGE situated companion

**Deliverable:** private software demonstration.

**Paper package:** event schema, memory boundary, permission boundary, intervention policy, stop behavior, owner identity, audit trail, rollback behavior, and privacy minimization.

**Verification:** demonstrate that familiarity, learned preferences, or conversational pressure cannot silently expand permission scope.

**Release boundary:** no public always-on deployment until privacy, security, consent, interruption, and recovery review are complete.

### 4. Systems Accountability Engineering curriculum

**Deliverable:** one teachable module.

**Required contents:** learning objectives, plain-language lesson, worked case, exercise, answer key, assessment rubric, accessibility version, instructor notes, and revision log.

**Verification:** teach it to a small supervised group, record confusion points, revise, and preserve both successful and failed outcomes.

### 5. Low-energy measurement bench

**Deliverable:** conventional measurement platform for low-power electrical, magnetic, vibration, thermal, and force observations.

**Paper package:** block diagram, bill of materials, calibration references, grounding and shielding plan, sensor ranges, sampling plan, uncertainty budget, controls, and emergency shutdown.

**Verification:** known-input calibration, cable/feedthrough controls, sham actuator, orientation reversal, power-off baseline, and blind analysis where practical.

**Boundary:** the bench measures claims; it does not validate a claim merely because it was built.

### 6. Crowned Coil

**Deliverable:** safe non-confidential reptile-handling product brief and supplier-ready package.

**Paper package:** user need, animal-welfare constraints, ergonomic requirements, materials, cleaning requirements, failure modes, warnings, packaging, price target, and prototype acceptance checklist.

**Privacy boundary:** do not send protected drawings, unreleased mechanisms, or patent-sensitive details until NDA and supplier terms are reviewed.

**Verification:** controlled fit, grip, force, durability, cleaning, and safe-use tests with qualified reptile-handling oversight.

### 7. Aurora / Flux research package

**Deliverable:** measurement-grade experiment proposal, not a flight claim.

**Aurora boundary:** separate the low-power tabletop/lab vessel from the city-ship architecture. The city-ship remains requirements-level research.

**Flux boundary:** no propulsion claim without calibrated six-axis force/torque, electrical, thermal, vibration, acoustic, RF, magnetic, orientation, and environmental measurements.

**Decisive controls:** command-off, sham actuator, reversed orientation, perpendicular orientation, cable/feedthrough control, blind run order, frozen calibration, preregistered analysis, and independent replication.

**Stop condition:** if measured momentum does not close within the preregistered uncertainty budget, the propulsion hypothesis is not supported.

## Builder handoff packet

A builder receives only:

- non-confidential specification;
- required function and operating envelope;
- interface definitions;
- bill of materials or software dependencies;
- drawings appropriate to the disclosure stage;
- safety requirements;
- acceptance tests;
- change-control process;
- known unknowns;
- payment and delivery assumptions.

The builder does not receive credentials, private keys, unrelated portfolio material, confidential supplier information, or unreviewed patent-sensitive details.

## Funder handoff packet

A funder receives:

- bounded problem;
- proposed advantage;
- evidence already obtained;
- next decisive experiment;
- experiment-only budget;
- qualified reviewer;
- measurable success criteria;
- useful outcome if the bold hypothesis fails;
- stop condition.

The strongest investment case is not “everything works.” It is “the next uncertainty is identified, measurable, affordable, and worth resolving.”

## Completion rule

A project may advance only when its current gate is evidenced. If a test fails, the package is revised, the failure is preserved, and the status meter moves backward when appropriate.

That is how Civic Continuum gets to builders: with a precise specification, honest evidence, bounded risk, and a test that can prove us wrong.
