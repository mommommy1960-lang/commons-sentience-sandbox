# Civic Continuum Demonstrator Runbook

## Purpose

This runbook packages the currently verified software foundation into a repeatable,
five-minute demonstrator. It is a simulation and safety-orchestration demo, not a
physical companion, autonomous agent, or evidence of consciousness.

## Current evidence state

- Feature branch: `feature/civic-continuum-job-queue`
- Latest verified workflow: CI run #146
- Verified commit: `44973e4c5b19bbe0f46dcd1ed4849987b3d2da5e`
- `main`: unchanged
- PR #30: open and unmerged

## Run locally

From the repository root:

```bash
python tools/civic_continuum_demo.py --output civic-continuum-demo.json
```

The output is deterministic JSON containing:

- the same request evaluated under Sentinel and Aster policies;
- refusal and safe-alternative decisions;
- explicit memory and authority-boundary evidence;
- a replay hash for comparison.

## Verify the software contract

```bash
python -m unittest discover -s tests -p 'test_civic_*.py' -v
python -m unittest discover -s tests -p 'test_*.py' -v
```

The workflow also compiles the repository sources and installs the test dependencies
before running both suites.

## Demonstrator script

The demonstrator is `tools/civic_continuum_demo.py`. It is dependency-free and
does not contact people, send messages, edit repositories, grant permissions, or
control hardware.

## Evidence labels

- Demonstrator scenario: implemented and CI-tested.
- Persistent phone-connected companion: not yet built.
- Hardware actuation: not implemented and requires a separate safety review.
- Independent replication: outstanding.
- Revenue: not established.

## Next gated milestone

The next product milestone is a supervised phone-connected prototype using the
existing permission, freeze, audit, and export requirements. Hardware selection,
personal-data handling, external publication, and any merge decision require Mya's
explicit approval before execution.
