# Civic Continuum Execution Queue

## Operating rule

Advance one gate at a time. A gate is complete only when its artifact, test result, evidence record, and unresolved risks are visible. A failed gate is preserved and repaired before the next gate advances.

## Gate 1 — Controlled software demonstration

### Target

Consent Token/CERL demonstrator connected to a bounded Maya Node review workflow.

### Required behavior

- grant a narrowly scoped permission;
- deny an out-of-scope request;
- reject expired authority;
- revoke authority immediately;
- freeze execution;
- restore only with fresh authorization;
- record tamper-evident audit events;
- prevent replay of a single-use authorization;
- preserve a human correction path.

### Acceptance evidence

- executable demo;
- automated transition tests;
- replay and tamper tests;
- example audit record;
- short reviewer instructions;
- known-limitations document;
- no external action capability by default.

### Stop conditions

Stop before pilot if authority can silently expand, revocation fails, audit history can be altered without detection, or the demo cannot reproduce its own result.

## Gate 2 — Supervised software pilot

### Target

Three bounded Maya Node Founding Reviews using the documented human-delivered workflow.

### Required evidence

- consented intake;
- scope and claim-boundary record;
- one adversarial test per review;
- delivery record;
- customer correction/refund path;
- privacy-safe fulfillment ledger;
- post-review feedback.

### Stop conditions

Stop if the service is confused with certification, legal advice, penetration testing, production approval, or a safety guarantee.

## Gate 3 — Tabletop physical prototype

### Target

A conventional, low-risk prototype selected from the closest buildable lane: Crowned Coil tool or low-energy measurement-bench subsystem.

### Required evidence

- non-confidential design brief;
- materials and supplier assumptions;
- hazard review;
- safe-use instructions;
- acceptance measurements;
- failure-mode log;
- prototype photographs or diagrams only after disclosure review.

### Stop conditions

Stop for unsafe animal contact, uncontrolled energy, missing guarding, unknown materials, unverified claims, or inadequate supervision.

## Gate 4 — Measurement-bench qualification

### Target

A conventional measurement platform capable of recording electrical, magnetic, thermal, vibration, acoustic, and force/torque signals within stated ranges.

### Required evidence

- calibration references;
- known-input checks;
- uncertainty budget;
- power-off baseline;
- sham actuator;
- cable/feedthrough controls;
- orientation reversal;
- blind or frozen analysis plan;
- synchronized raw-data hash.

### Stop conditions

Stop if the instrument is uncalibrated, the environment is uncontrolled, the signal is below the measurement floor, or a claimed effect disappears under controls.

## Gate 5 — Independent technical review

### Target

A qualified external reviewer receives only the appropriate disclosure tier.

### Required evidence

- public non-confidential brief;
- private disclosure agreement where necessary;
- complete assumptions and equations;
- test protocol;
- risk register;
- questions requiring reviewer judgment;
- preserved disagreement record.

### Stop conditions

Do not fabricate or market the system if independent review identifies an unsafe, incoherent, unlawful, or untestable design.

## Gate 6 — Laboratory fabrication request

### Target

Send a bounded, conventional, reviewed build package to a qualified laboratory or supplier.

### Required handoff

- revision-controlled specification;
- approved drawings or software interfaces;
- bill of materials;
- quality requirements;
- calibration requirements;
- test fixtures;
- acceptance criteria;
- change-control procedure;
- delivery and support terms;
- documented exclusion of unverified end-state claims.

### Stop conditions

No fabrication request for propulsion, biomedical, high-energy, or other regulated work proceeds without qualified institutional review, appropriate safety controls, and lawful authorization.

## Current order of work

1. Consent Token software demonstrator.
2. Maya Node supervised service package.
3. SAGE private controlled demo.
4. One curriculum teaching run.
5. Low-energy measurement-bench subsystem.
6. Crowned Coil non-confidential prototype package.
7. Aurora/Flux measurement package.
8. Independent review.
9. Laboratory fabrication only after the relevant gate passes.

## Evidence record template

For every gate, record:

- date;
- commit or artifact identifier;
- operator;
- input conditions;
- expected result;
- observed result;
- pass/fail/blocked status;
- failure reason;
- corrective action;
- reviewer;
- next gate;
- claims that remain prohibited.

## Physical-world boundary

Software tests can establish software behavior. A tabletop prototype can establish limited mechanical or electrical behavior. Laboratory fabrication can establish that a specified apparatus was built. None of those steps alone establishes propulsion, medical efficacy, sentience, or civilization-scale impact.
