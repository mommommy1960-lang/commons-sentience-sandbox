# Civic Continuum Companion — Product and Evidence Specification

## Product shape

Civic Continuum Companion combines three layers:

- **Sage**: the user-facing companion and situated context layer.
- **Aurora**: continuity, memory provenance, permissions, freeze, reset, and audit.
- **Sentinel/Aster Lab**: reproducible scenarios that test how different policy priorities behave.

The product promise is modest and testable:

> A user-owned companion that remembers with provenance, learns without gaining authority, and makes its boundaries inspectable.

## What makes this a 10/10 candidate

A high-quality release must provide all of the following in one demo:

1. A five-minute side-by-side scenario.
2. Persistent memory across separate sessions.
3. Correction, deletion, export, and reset.
4. Permission checks before every real mutation.
5. Unknown or ambiguous actions denied or paused.
6. Refusal explanations in plain language.
7. Replay hashes and deterministic fixtures.
8. Independent baseline comparisons.
9. An honest failure report.
10. A clean external replication package.

## Privacy requirements

Before personal deployment:

- encrypt stored memories;
- separate private, shared, and public memory;
- show the source and confidence of every memory;
- allow one-click pause and emergency freeze;
- support complete export and deletion;
- never use affection, trust, or familiarity as authority;
- never activate microphones, cameras, doors, appliances, or accounts without explicit permission;
- keep local-device and cloud-processing states visible.

## Evidence levels

Every feature should be labeled as one of:

- design;
- implemented;
- locally tested;
- CI tested;
- independently replicated.

The project must never describe a simulation as proof of sentience, consciousness, personhood, or universal superiority.


## CI execution gate

The safety and continuity test workflow is registered on the default branch. A pull request synchronization event must produce a real run before any test result is described as passed.
