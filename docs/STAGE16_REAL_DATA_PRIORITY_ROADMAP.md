# Stage 16 Real-Data Priority Roadmap

## Purpose

This document recenters Stage 16 readiness around the primary mission:
real-data analysis infrastructure and defensible scientific inference.

Benchmark/simulation modules (including double-slit) remain important but
secondary. They validate methods; they do not define discovery claims.

## Current Real-Data Capabilities

1. Public-catalog ingestion and normalization for Fermi, Swift, and IceCube.
2. Reproducible anisotropy metrics (hemisphere imbalance, preferred axis,
   clustering, energy-time correlation).
3. Isotropic and exposure-corrected null modes.
4. Cross-catalog comparison (two-catalog and three-catalog workflows).
5. Trial-factor correction support (Holm pathway integrated in Stage 8/11+).
6. Preregistration plan parsing, locking checks, and confirmatory metadata.
7. Confirmatory rerun orchestration (Stage 14 runners).
8. Publication gate evaluation with required/recommended checks and reports.

## Current Weaknesses

1. Exposure correction is still an empirical proxy, not mission-grade
   instrument-response modeling.
2. Sky mapping is not HEALPix-native yet; current axis scans are deterministic
   grids with a HEALPix planning hook.
3. Cross-catalog comparability still depends on differing population sizes and
   instrument-selection effects.
4. Systematics reporting is present but not yet standardized into a full
   publication-grade uncertainty budget.
5. External review artifacts (replication packets, reviewer checklists,
   independent rerun scripts) are not yet fully productized.

## Immediate Infrastructure Priorities (Ordered)

1. Exposure/systematics hardening:
   - move from empirical exposure proxy toward response-weighted nulls,
   - formalize systematics logging schema across catalogs.
2. HEALPix-grade spatial layer:
   - add a clear abstraction for spherical maps and map operations,
   - migrate preferred-axis/anisotropy summaries to map-aware diagnostics.
3. Cross-catalog comparability upgrades:
   - harmonized quality filters,
   - catalog-specific sensitivity notes tracked in machine-readable metadata.
4. Confirmatory-discipline hardening:
   - stronger output naming conventions (exploratory vs confirmatory),
   - immutable run manifests and rerun reproducibility notes.
5. External-review package readiness:
   - reviewer-oriented artifact bundles,
   - reproducibility scripts and audit checklists.

## Recommended Implementation Order

### Phase 16A (Now)
- Publish Stage 16 gap reports (exposure/systematics, HEALPix readiness,
  confirmatory discipline plan, external review checklist).
- Freeze wording discipline: benchmark != discovery.

### Phase 16B
- Implement map abstraction + HEALPix optional backend.
- Add exposure model interfaces decoupled from empirical proxy implementation.

### Phase 16C
- Integrate upgraded exposure + map layer into Stage 8/10/14 paths behind
  compatibility-safe flags.
- Add regression tests for null comparability and map-level statistics.

### Phase 16D
- Prepare external-review package with locked confirmatory reruns and complete
  assumptions/systematics documentation.

## Alignment with Operational Companion Strategy

This roadmap is aligned with the stated sequence:

1. data-analysis-first,
2. stronger anisotropy/propagation analysis,
3. improved exposure modeling,
4. HEALPix-grade spatial analysis,
5. larger independent datasets,
6. confirmatory reruns under locked preregistration,
7. external review,
8. only then consider owned-lab precision expansion.

## What Qualifies as Publishable Readiness

Minimum conditions before publication-grade claims:

1. Required publication gates pass with confirmatory artifacts.
2. Exposure/systematics model is documented and not solely empirical-proxy
   dependent for key claims.
3. Trial-factor corrections are explicit, reproducible, and reviewer-auditable.
4. Cross-catalog robustness supports claim scope (no overreach beyond evidence).
5. Reproducibility packet is complete (code version, seeds, inputs, manifests,
   rerun instructions, caveats).
6. Independent external scientific review is completed and documented.

## Exploratory vs Confirmatory Modes

### Exploratory
- hypothesis-generating,
- allows method tuning,
- not sufficient for publication claims,
- must be labeled clearly in artifacts and memos.

### Confirmatory
- preregistered/locked configuration,
- no post-hoc parameter drift,
- outputs interpreted under declared thresholds and corrections,
- suitable for publication-gate evaluation and external review prep.

## Stage 16 Decision Rule

Treat Stage 16 as infrastructure-hardening stage. Do not escalate claim strength
faster than exposure/systematics and cross-catalog robustness maturity.
