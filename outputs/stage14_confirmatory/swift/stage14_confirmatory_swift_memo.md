# Stage 8 First-Results Internal Memo

**Run name:** `stage14_confirmatory_swift`  
**Generated:** 2026-04-21T21:46:50.825662Z  
**Catalog:** `swift_bat3_grb_catalog` (`/workspaces/commons-sentience-sandbox/data/real/swift_bat3_grb_catalog.csv`)  
**Stage:** Stage 8 — First Real-Catalog Results Package  
**Run mode:** `preregistered_confirmatory`  

---

## 1. What Was Run

The Stage 7 public-data anisotropy study was run on the catalog `swift_bat3_grb_catalog` (872 events after normalisation). The pipeline tested four primary metrics against an isotropic null ensemble of 500 synthetic draws:

- Hemisphere imbalance (north–south event fraction difference)
- Preferred-axis score (max |mean cos-projection| over 192 trial axes)
- Energy–time Pearson correlation
- Temporal clustering score

Seed: `42`. Null model: **exposure-corrected empirical sky-acceptance proxy**.

**Why this null model:** The empirical exposure-corrected null was selected to account for the non-uniform sky coverage of the Fermi GBM detector. The null is built by histogramming the observed events and re-sampling from the resulting distribution; see docs/REALITY_AUDIT_STAGE9_STATUS.md.

---

## 2. Run Discipline (Exploratory vs Confirmatory)

This run was requested as preregistered confirmatory.
Plan match status: **MATCHED LOCKED PLAN**

---

## 3. Catalog Coverage

| Field               | Value                |
|---------------------|----------------------|
| Events (total)      | 872        |
| Events with position| 872              |
| Instruments         | Swift-BAT          |
| Time span           | N/A              |

---

## 4. Key Metrics

| Metric                    | Observed value | Percentile vs null |
|---------------------------|----------------|--------------------|
| Hemisphere imbalance      | 0.0482 | 0.5620 |
| Preferred-axis score      | 0.0694 | 0.5560 |
| Energy–time Pearson r     | N/A | 0.5000 |
| Temporal clustering score | 1.0000 | 0.0000 |

**Signal tier:** `no_anomaly_detected`  
**Maximum percentile:** 0.5620

## 5. Trial-Factor Correction

Method: **holm** over **2** tested metrics.
Corrected verdict: **corrected_null**

| Metric | Corrected percentile | Flag |
|--------|----------------------|------|
| hemisphere_imbalance | 0.1240 | null |
| preferred_axis_score | 0.1240 | null |
| energy_time_pearson_r | N/A | insufficient_data |
| clustering_score | N/A | insufficient_data |

---

## 6. Interpretation

All metrics are within the bulk of the exposure-corrected null distribution. No significant anomaly detected.

---

## 7. What This Result Does NOT Prove

A deviation from an isotropic null model — even a statistically significant one — does **not** establish any of the following:

- That the universe or physical reality is a simulation.
- That the signal is cosmological rather than instrumental.
- That any specific physical model is correct.
- That the result would survive a pre-registered replication with trial-factor correction.

Anomaly-like deviations from an isotropic null are hypothesis-generating results, not proof of any specific physical or cosmological cause. Systematic effects, selection biases, and incomplete modeling should be ruled out before drawing any scientific conclusion.

---

## 8. Current Limitations

- Exposure-corrected null is empirical and still approximates true instrument response.
- Trial-factor correction applied (holm) across 2 metrics; interpret corrected verdict as primary.
- Selection biases and instrument systematics not characterised.
- This run is an internal first-results package, not a publishable result.

---

## 9. Recommended Next Upgrades

- Add exposure-map / acceptance-weighted null model (Stage 9 priority).
- HEALPix-based axis scan (NSIDE ≥ 8) for finer preferred-axis sensitivity.
- Multi-catalog cross-matching for cross-instrument consistency check.
- Blinded pre-registration before any significance claim.
- Trial-factor correction across simultaneously tested metrics.

---

*This memo is an internal first-results artifact produced by the commons-sentience-sandbox Stage 8 pipeline. It is not a scientific publication or preprint.*
