# Stage 12 IceCube Diagnostics Memo

Internal robustness diagnostic artifact. Not a publication.

## What was checked

- Catalog completeness and structural flags
- Small-N sensitivity across axis-count settings
- Leave-k-out influential event analysis
- Early/late epoch split persistence

## Catalog summary

- Event count: 37
- Flags: small_sample_catalog, spatial_concentration, time_missingness_high
- Position coverage: RA missing=0, Dec missing=0
- Energy missing: 0
- Time missing: 37

## Small-N sensitivity

- Trend rows (full-sample anomaly frequency proxy):
  - axes=48: fraction_ge_0.90=1.0, fraction_ge_0.97=1.0
  - axes=96: fraction_ge_0.90=1.0, fraction_ge_0.97=0.6933333333333334
  - axes=192: fraction_ge_0.90=1.0, fraction_ge_0.97=1.0

## Leave-k-out

- k=1 combinations evaluated: 37
- Fraction of tier drops vs baseline: 0.0
- Max percentile median: 0.9833333333333333

## Epoch split

- Not usable: Insufficient valid times for stable epoch split

## Robustness judgment

- Label: relatively_stable
- Fragile signals: none
- Robust signals: axis_density_stable, leave_k_out_stable

Interpretation: Treat anomaly-like deviations as exploratory unless they remain stable under these diagnostics and preregistered confirmatory reruns.
