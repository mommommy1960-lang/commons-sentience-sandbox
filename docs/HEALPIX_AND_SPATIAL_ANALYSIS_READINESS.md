# HEALPix and Spatial Analysis Readiness Audit

## Purpose

This audit evaluates current sky-mapping readiness for the Reality Audit
real-data pipeline and identifies what must be in place before serious
confirmatory sky analysis.

## Current Status

### What exists now

1. Deterministic axis-grid scanning for preferred-axis metrics in
   [reality_audit/data_analysis/public_anisotropy_study.py](reality_audit/data_analysis/public_anisotropy_study.py).
2. Configurable axis modes (`coarse`, `dense`, `auto`) and a planning-mode hook
   called `healpix_plan`.
3. The `healpix_plan` mode currently records intended NSIDE/npix metadata but
   explicitly uses deterministic dense-grid fallback.

### What does not exist yet

1. No HEALPix-native map object abstraction in the analysis pipeline.
2. No dependency-integrated HEALPix backend (`healpy`) currently wired in.
3. No per-pixel exposure-weighted significance map outputs.
4. No map-domain trial-correction framework for all-sky scanning.

## Missing Dependencies and Abstractions

### Dependencies (optional but recommended)

- `healpy` for HEALPix pixelization and map-domain operations.
- Optional map I/O tooling if FITS-based interoperability is required.

### Required abstractions

1. `SkyMap` interface:
   - pixelization schema,
   - coordinate transforms,
   - masking support,
   - serialization.
2. `ExposureModel` interface:
   - query exposure at sky coordinates/pixels,
   - support instrument-specific response surfaces.
3. `NullSampler` map-aware adapters:
   - isotropic map sampling,
   - exposure-weighted sampling,
   - reproducible seeded generation with manifest logging.
4. `MapStatistic` layer:
   - per-pixel excess/deficit metrics,
   - smoothed map statistics,
   - map-level p-value workflows.

## Exposure-Modeling Implications

Current exposure correction is empirical and catalog-derived, which is useful
for robustness but insufficient for publication-grade map inference.

For HEALPix-grade confirmatory analysis, exposure handling should support:

1. instrument-response-informed sky weights,
2. time/energy-aware selection effects (or explicit documentation if omitted),
3. exposure-map versioning in run manifests,
4. comparability notes across catalogs with differing sensitivities.

## What Must Be Built Before Serious Confirmatory Sky Analysis

### Minimum preconditions

1. HEALPix-native map representation integrated into analysis runners.
2. Exposure-model abstraction with at least one instrument-response-informed
   implementation beyond empirical-proxy histograms.
3. Map-level trial-factor correction strategy defined and tested.
4. Reproducible map artifacts:
   - observed map,
   - null map ensemble summaries,
   - significance map,
   - masks and metadata.
5. Cross-catalog map comparability protocol:
   - common coordinate/pixelization policy,
   - harmonized masking logic,
   - explicit caveats for population differences.

### Recommended first implementation slice

1. Add optional `healpy` backend behind a feature flag.
2. Keep current axis-scan path as compatibility fallback.
3. Emit sidecar map diagnostics in exploratory mode first.
4. Promote map outputs to confirmatory pathways only after regression and
   publication-gate integration tests pass.

## Readiness Verdict

Current state: **planning-ready, implementation-incomplete**.

The repository has a useful planning hook and deterministic spatial scan
infrastructure, but is not yet HEALPix-confirmatory-ready. The next step is a
small, compatibility-safe map abstraction layer plus optional backend wiring.
