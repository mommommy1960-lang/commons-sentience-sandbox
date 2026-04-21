# Stage 10: Cross-Catalog Comparison Memo

**Internal first-results artifact — not a scientific publication.**
*Generated: 2026-04-21T16:37:44.424635Z*

---

## Verdict: INCONSISTENT — Catalogs disagree

---

## Catalog Comparison Table

| Field | fermi_lat_grb_catalog | swift_bat3_grb_catalog |
|-------|---------|---------|
| Event count | 3000 | 872 |
| Events with position | 3000 | 872 |
| Null model | exposure_corrected | exposure_corrected |
| Hemisphere imbalance (pct) | 0.8500 | 0.6300 |
| Preferred-axis score (pct) | 0.8900 | 0.5700 |
| Max percentile | 0.8900 | 0.6300 |
| Interpretation tier | `weak_anomaly_like_deviation` | `no_anomaly_detected` |

---

## Interpretation

fermi_lat_grb_catalog shows weak_anomaly_like_deviation while swift_bat3_grb_catalog shows no_anomaly_detected. Cross-catalog disagreement typically indicates an instrument-specific systematic rather than a genuine sky-position signal. The anomaly in fermi_lat_grb_catalog most likely reflects residual acceptance geometry not fully corrected by the empirical null, or a selection bias particular to that instrument. This result does NOT support a catalog-independent anisotropy claim.

---

## Does this support a catalog-independent anisotropy claim?

**No.** The catalogs disagree in interpretation tier. Cross-catalog disagreement is the expected signature of instrument-specific systematics, not a genuine sky signal.



**Current status:** These are internal first-results packages. No pre-registration has been filed. The results are **hypothesis-generating only** — they do not constitute evidence for or against any physical or metaphysical claim.

---

## Caveats

- Both runs use empirical exposure-proxy nulls built from the data under test: any real signal is partially absorbed, making these tests conservative.
- Different catalogs have different source populations, redshift distributions, energy ranges, and trigger thresholds. Non-detection in Swift BAT does not rule out a GRB-population-wide effect undetectable by BAT.
- The preferred-axis scan uses 48 trial axes without a trial-factor correction; a metric significant at 90th percentile is consistent with a fluctuation.
- No pre-registration was filed before these runs. These are exploratory first-results packages, not confirmatory tests.
- N_Fermi=3000 vs N_Swift=872: unequal statistical power. The Fermi result is not directly comparable in absolute significance.

---

## Next Steps

1. Obtain a proper instrument-response exposure map (e.g. Fermi GBM FSSC FITS file) for a
   model-based null rather than the empirical self-contaminating proxy.
2. Run IceCube HESE for a third independent test (different source class, neutrinos vs. gamma-rays).
3. Pre-register a specific, testable hypothesis with a defined axis and significance threshold
   before any unblinded confirmatory run.
4. Apply trial-factor correction (Bonferroni or simulation-based) across the four tested metrics.
5. Investigate galactic-plane avoidance and redshift-distribution differences between catalogs.

---

*This memo is part of the commons-sentience-sandbox Stage 10 artifact layer.
Internal guide only — not a scientific claim.*
