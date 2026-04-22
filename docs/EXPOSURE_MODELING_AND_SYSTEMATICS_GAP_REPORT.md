# Exposure Modeling and Systematics Gap Report

## Purpose

This report documents the current defensibility level of exposure and
systematics handling in the real-data anisotropy pipeline and defines what must
improve before publication-grade claims.

## Code Areas Reviewed

- `reality_audit/data_analysis/exposure_corrected_nulls.py`
- `reality_audit/data_analysis/public_anisotropy_study.py`
- `reality_audit/data_analysis/stage8_first_results.py`
- `reality_audit/data_analysis/catalog_comparison.py`
- Stage 13/14 publication-gate and confirmatory outputs

## What Is Already Defensible

1. Explicit null-mode declaration (`isotropic` vs `exposure_corrected`) in run
   configuration and metadata.
2. Exposure-corrected null pathway exists and is documented with limitations.
3. Cross-catalog comparison includes caveats and disagreement interpretation.
4. Confirmatory-mode metadata records preregistration match/mismatch context.
5. Publication-gate structure prevents over-claiming when required controls are
   missing.
6. Exposure-model calibration metadata and time-coverage refinement diagnostics
   are now emitted in run metadata to make mission-grade promotion blockers
   explicit and machine-readable, including confirmatory readiness thresholds.

## What Is Still Simplistic

1. Exposure correction is empirical (histogram proxy from data under test), so
   it can absorb true signal and is not an instrument-response model.
2. Time-dependent detector orientation and trigger-efficiency effects are not
   fully modeled in null generation.
3. Cross-catalog comparability still relies on broad caveats rather than a
   harmonized sensitivity-adjusted framework.
4. Systematics logging is informative but not yet a formal uncertainty-budget
   ledger suitable for external review packets.
5. Current preferred-axis scan and null comparisons are useful for first-results
   discipline but still short of publication-grade all-sky inference rigor.

## Highest-Value Next Improvements

1. Introduce exposure model abstraction:
   - separate empirical proxy from response-informed models,
   - make model choice explicit and versioned in manifests.
2. Add structured systematics report schema per run:
   - detector assumptions,
   - known biases,
   - sensitivity caveats,
   - unresolved risks.
3. Standardize cross-catalog comparability metadata:
   - population differences,
   - coverage differences,
   - effective power/precision notes.
4. Couple map-based (HEALPix-ready) diagnostics to exposure handling for more
   robust spatial inference.

## Improvements Required Before Publication-Grade Claims

The following should be treated as mandatory for stronger claims:

1. Exposure handling beyond empirical proxy for key confirmatory claims.
2. Formalized systematics accounting with reproducible assumptions and bounds.
3. Map-aware multiple-testing control for spatial search space.
4. Clear claim-scope constraints tied to cross-catalog robustness.
5. External reviewer reproducibility bundle containing:
   - exact inputs,
   - code version,
   - seed/config manifests,
   - null-model rationale,
   - systematics documentation.

## Practical Stage 16 Recommendation

Keep current exposure-corrected pathway as a conservative baseline and
compatibility layer. Build response-informed and map-aware infrastructure in
parallel, then gate stronger claim language on those upgrades plus external
review completion.
