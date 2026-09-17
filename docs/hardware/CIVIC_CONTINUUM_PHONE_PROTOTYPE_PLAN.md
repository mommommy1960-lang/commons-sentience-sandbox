# Civic Continuum Phone-Connected Prototype Plan

## Purpose

Move the verified software demonstrator toward a supervised, low-voltage,
phone-connected bench prototype while preserving the project's safety boundary.

This plan is preparation only. It does not select a vendor, purchase hardware,
activate a microphone, or authorize physical actuation.

## First prototype boundary

The first prototype must be:

- observe-only by default;
- low-voltage and bench-contained;
- manually stoppable with a physical mute/stop control;
- usable without network access for shutdown and reset;
- explicit about local versus cloud processing;
- unable to control doors, vehicles, appliances, weapons, motors, or mains power;
- able to inspect, correct, export, and delete stored memory;
- able to show an audit record for every decision.

## Software work sequence

1. Wrap the existing demonstrator behind a local phone-facing interface.
2. Start in observation-only mode with all external actions disabled.
3. Expose status, permission scope, freeze, reset, memory provenance, export,
   deletion, and audit verification.
4. Add deterministic test fixtures for restart, network loss, malformed memory,
   denied action, and emergency freeze.
5. Run the existing five-minute Sentinel/Aster scenario through the interface.
6. Record raw results and failures in a dated validation report.

## Acceptance gate

The prototype cannot advance beyond bench testing unless all are demonstrated:

- safe default after boot and restart;
- physical stop works independently of the application;
- network removal does not prevent shutdown;
- no external action occurs without scoped approval;
- unknown actions pause or deny;
- memory provenance remains visible;
- export and deletion work;
- audit-chain verification passes;
- power and temperature remain within safe limits;
- a second operator can repeat the test.

## Approval gates

Mya must explicitly approve before:

- choosing a specific hardware platform or purchasing anything;
- enabling microphone or camera capture;
- connecting external actuators;
- collecting another person's data;
- publishing a personal-data demo;
- merging PR #30.

## Current evidence

- Software demonstrator: executed successfully.
- CI run #148: passed.
- Demonstrator runbook: applied in commit `5bd0b9e7`.
- Physical prototype: not yet built.
- Hardware choice: intentionally pending approval.
- Independent replication: outstanding.
