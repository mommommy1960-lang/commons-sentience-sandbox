# Stage 8 First-Results Internal Memo

**Run name:** `stage9_fermi_exposure_corrected`  
**Generated:** 2026-04-21T08:53:32.165782Z  
**Catalog:** `fermi_lat_grb_catalog` (`data/real/fermi_lat_grb_catalog.csv`)  
**Stage:** Stage 8 — First Real-Catalog Results Package  

---

## 1. What Was Run

The Stage 7 public-data anisotropy study was run on the catalog `fermi_lat_grb_catalog` (3000 events after normalisation). The pipeline tested four primary metrics against an isotropic null ensemble of 100 synthetic draws:

- Hemisphere imbalance (north–south event fraction difference)
- Preferred-axis score (max |mean cos-projection| over 48 trial axes)
- Energy–time Pearson correlation
- Temporal clustering score

Seed: `42`. Null model: **exposure-corrected empirical sky-acceptance proxy**.

**Why this null model:** The empirical exposure-corrected null was selected to account for the non-uniform sky coverage of the Fermi GBM detector. The null is built by histogramming the observed events and re-sampling from the resulting distribution; see docs/REALITY_AUDIT_STAGE9_STATUS.md.

---

## 2. Catalog Coverage

| Field               | Value                |
|---------------------|----------------------|
| Events (total)      | 3000        |
| Events with position| 3000              |
| Instruments         | Fermi-GBM          |
| Time span           | N/A              |

---

## 3. Key Metrics

| Metric                    | Observed value | Percentile vs null |
|---------------------------|----------------|--------------------|
| Hemisphere imbalance      | -0.4120 | 0.8500 |
| Preferred-axis score      | 0.2456 | 0.8900 |
| Energy–time Pearson r     | 0.0201 | 0.0000 |
| Temporal clustering score | 0.9699 | 0.0000 |

**Signal tier:** `weak_anomaly_like_deviation`  
**Maximum percentile:** 0.8900

---

## 4. Interpretation

One or more metrics fall in the top 25% of the exposure-corrected null distribution. Weak deviation; consistent with statistical fluctuation.

---

## 5. What This Result Does NOT Prove

A deviation from an isotropic null model — even a statistically significant one — does **not** establish any of the following:

- That the universe or physical reality is a simulation.
- That the signal is cosmological rather than instrumental.
- That any specific physical model is correct.
- That the result would survive a pre-registered replication with trial-factor correction.

Anomaly-like deviations from an isotropic null are hypothesis-generating results, not proof of any specific physical or cosmological cause. Systematic effects, selection biases, and incomplete modeling should be ruled out before drawing any scientific conclusion.

---

## 6. Current Limitations

- Single-catalog analysis with a simple isotropic null; no exposure-map correction.
- No trial-factor adjustment across the four tested metrics.
- Selection biases and instrument systematics not characterised.
- This run is an internal first-results package, not a publishable result.

---

## 7. Recommended Next Upgrades

- Add exposure-map / acceptance-weighted null model (Stage 9 priority).
- HEALPix-based axis scan (NSIDE ≥ 8) for finer preferred-axis sensitivity.
- Multi-catalog cross-matching for cross-instrument consistency check.
- Blinded pre-registration before any significance claim.
- Trial-factor correction across simultaneously tested metrics.

---

*This memo is an internal first-results artifact produced by the commons-sentience-sandbox Stage 8 pipeline. It is not a scientific publication or preprint.*
