# Reality Audit — Stage 10 Status

## What Stage 10 Is For

Stage 10 implements **second-catalog replication and cross-catalog comparison**
for the public anisotropy pipeline.  It addresses a fundamental requirement of
the program: a pattern seen in a single catalog is hypothesis-generating at
best.  A genuine sky-position anisotropy must persist across independent
instruments and source populations.

---

## Alignment with the Operational Companion Roadmap

The Operational Companion requires:

1. **Data-analysis-first**: no hardware or metaphysical rabbit holes.
2. **Narrow hypothesis testing**: preferred-axis / hemisphere anisotropy only.
3. **Systematic-effects validation first**: instrument acceptance, sky coverage,
   selection biases must be checked before any signal interpretation.
4. **Replication across catalogs**: a signal that appears only in one instrument
   is almost certainly instrumental, not physical.

Stage 10 directly fulfills requirements 3 and 4:

- Stage 9 showed the Fermi GBM Stage 8 "strong anomaly" was an acceptance
  artefact, dropping to `weak_anomaly_like_deviation` under the corrected null.
- Stage 10 runs Swift BAT (independent instrument, independent GRB sample)
  through the same corrected-null pipeline.
- The cross-catalog comparison provides an explicit consistency check.

---

## Current Results (completed)

### Fermi GBM (Stage 9 corrected null, N=3000)

| Metric | Value | Percentile vs null |
|--------|-------|--------------------|
| Hemisphere imbalance | −0.412 | 85th pct |
| Preferred-axis score | 0.246 | 89th pct |
| Interpretation tier | `weak_anomaly_like_deviation` | — |

### Swift BAT (Stage 10 corrected null, N=872)

| Metric | Value | Percentile vs null |
|--------|-------|--------------------|
| Hemisphere imbalance | +0.048 | 63rd pct |
| Preferred-axis score | 0.068 | 57th pct |
| Interpretation tier | `no_anomaly_detected` | — |

### Cross-catalog verdict: **INCONSISTENT**

The catalogs disagree in interpretation tier.  This is the expected signature
of an **instrument-specific systematic**, not a genuine sky-position signal.

The Fermi GBM residual deviation (Stage 9, 89th percentile) is most likely:
1. Residual acceptance geometry not fully corrected by the empirical
   self-contaminating null.
2. A selection bias in the Fermi GBM trigger algorithm.
3. A statistical fluctuation (89th percentile → consistent with chance at ~10%).

**There is no evidence of a catalog-independent sky-position anisotropy.**

---

## Capability Checklist

| Capability | Status |
|------------|--------|
| Swift BAT fetch + ingest (`data/real/swift_bat3_grb_catalog.csv`) | COMPLETE |
| Per-catalog null defaults (Fermi/Swift → `exposure_corrected`) | COMPLETE |
| Stage 10 Swift pipeline run | COMPLETE |
| `catalog_comparison.py` module | COMPLETE |
| `run_stage10_catalog_comparison.py` CLI | COMPLETE |
| `scripts/run_stage10_catalog_comparison.py` convenience runner | COMPLETE |
| Comparison memo + JSON in `outputs/stage10_first_results/comparison/` | COMPLETE |
| `tests/test_catalog_comparison.py` (28 tests) | COMPLETE |
| `docs/REALITY_AUDIT_STAGE10_STATUS.md` | COMPLETE |
| `docs/REALITY_AUDIT_STAGE10_TEMPLATE.md` | COMPLETE |
| README Stage 10 section | COMPLETE |

---

## Explicit Limitations

| # | Limitation |
|---|-----------|
| 1 | Fermi vs Swift is not fully independent: both observe GRBs. Ideally cross different source classes (e.g., GRBs vs IceCube neutrinos). |
| 2 | Swift BAT N=872 gives weaker statistical power than Fermi N=3000; non-detection in Swift does not rule out a Fermi-detectable effect. |
| 3 | Empirical exposure-proxy nulls absorb any real signal → tests are conservative. |
| 4 | No pre-registration before these runs; results are exploratory. |
| 5 | 48-axis scan carries a trial factor not corrected here. |

---

## Why Cross-Catalog Disagreement Points to Systematics

If a sky anisotropy were truly present at cosmological or astrophysical scales,
it would appear in **all** unbiased wide-field catalogs of the same sky region.
Fermi GBM and Swift BAT observe large GRB samples with overlapping sky coverage.
A genuine preferred axis would produce correlated deviations in both.

When one instrument shows a deviation and the other does not — particularly after
correcting for sky acceptance — the most parsimonious explanation is:

1. Residual detector geometry in the instrument that shows the deviation.
2. Selection-function differences (trigger thresholds, spectral sensitivity).
3. Statistical fluctuation in the finite sample.

This is standard practice in multi-messenger and survey astronomy.

---

## Next Stage (Stage 11) Priorities

1. **True independent null**: Use the Fermi GBM FSSC detection efficiency maps
   (available as FITS files) as a model-based null instead of the empirical proxy.
2. **Third catalog (IceCube HESE)**: Neutrinos vs gamma-rays; completely different
   source population and detector physics.
3. **Pre-registration**: File a specific prediction (axis direction, expected
   percentile threshold) before running any new catalog, to convert from
   exploratory to confirmatory.
4. **HEALPix-based axis scan** (NSIDE ≥ 8, ~3072 axes) for finer angular resolution.
5. **Trial-factor correction** (Bonferroni or simulation-based) over all tested metrics.
