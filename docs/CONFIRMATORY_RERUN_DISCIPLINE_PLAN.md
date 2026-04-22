# Confirmatory Rerun Discipline Plan

## Purpose

This plan hardens confirmatory rerun discipline while preserving Stage 7-14
behavior. It defines compatibility-safe upgrades for locked configuration,
mode labeling, reproducibility notes, and artifact naming.

## Current Support (Already Present)

1. Preregistration plan loading, validation, and lock checks.
2. `run_mode` labeling in Stage 8 pathways (`exploratory` vs
   `preregistered_confirmatory`).
3. Preregistration match diagnostics in run metadata.
4. Stage 14 confirmatory orchestrators with fixed parameters and manifests.

## Current Gaps

1. Artifact naming conventions are mostly disciplined but not uniformly
   schema-enforced across all stages and scripts.
2. Exploratory/confirmatory distinction is present in metadata but not always
   surfaced prominently in every top-level summary artifact.
3. Reproducibility notes are generated but could be standardized into a single
   machine-readable contract.

## Stage 16 Compatibility-Safe Upgrade Targets

### Target 1: Naming contract

Define a shared naming schema for analysis outputs:

`<stage>_<mode>_<catalog>_<runid>_<artifact>`

Where:
- `mode` is one of `exploratory` or `confirmatory`
- `catalog` is normalized (`fermi`, `swift`, `icecube`, ...)
- `artifact` is `summary`, `memo`, `manifest`, etc.

Implementation note:
- Add helper utilities without changing existing file parsers.
- Keep legacy names accepted to avoid breaking downstream scripts.

### Target 2: Mode visibility in all summary surfaces

Ensure `run_mode`, `preregistration_locked`, and correction method appear in:
- summary JSON top-level normalized view,
- markdown summary headers,
- comparison manifests used by publication-gate workflows.

### Target 3: Reproducibility contract block

Add a standard block to manifests:
- code version/commit,
- input paths/checksums,
- seed,
- null model settings,
- axis settings,
- trial-correction method,
- prereg plan hash and lock state.

### Target 4: Confirmatory mismatch severity policy

When run mode is confirmatory but preregistration mismatch exists:
- mark run as `confirmatory_with_mismatch`,
- flag in publication gate as non-confirmatory evidence,
- require explicit reviewer note before inclusion in claims.

## Recommended Implementation Sequence

1. Introduce naming/reproducibility helper module (additive).
2. Wire helper into Stage 14/15+ runners first (lowest risk).
3. Backfill Stage 8/10 wrappers with compatibility adapters.
4. Add tests for naming contract and mode-label propagation.
5. Add gate-facing normalization tests for confirmatory metadata fields.

## Non-Goals for This Pass

- No rewrite of Stage 7-14 analysis logic.
- No breaking changes to existing artifact consumers.
- No claim-level behavior changes beyond clearer metadata discipline.

## Success Criteria

1. Confirmatory artifacts are machine-detectable and human-obvious.
2. Exploratory outputs cannot be mistaken for confirmatory outputs.
3. Rerun reproducibility metadata is complete enough for external reviewers.
4. Existing Stage 7-14 tests and workflows remain compatible.
