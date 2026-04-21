# Stage 8 First-Results Internal Memo

**Run name:** `stage11_icecube_final_validation`  
**Generated:** 2026-04-21T18:22:08.308345Z  
**Catalog:** `icecube_hese_events` (`data/real/icecube_hese_events.csv`)  
**Stage:** Stage 8 — First Real-Catalog Results Package  

---

## 1. What Was Run

The Stage 7 public-data anisotropy study was run on the catalog `icecube_hese_events` (37 events after normalisation). The pipeline tested four primary metrics against an isotropic null ensemble of 100 synthetic draws:

- Hemisphere imbalance (north–south event fraction difference)
- Preferred-axis score (max |mean cos-projection| over 192 trial axes)
- Energy–time Pearson correlation
- Temporal clustering score

Seed: `42`. Null model: **uniform isotropic sphere**.

**Why this null model:** A uniform isotropic null was used (events placed uniformly on the sphere). This does not account for instrument sky-coverage biases.

---

## 2. Catalog Coverage

| Field               | Value                |
|---------------------|----------------------|
| Events (total)      | 37        |
| Events with position| 37              |
| Instruments         | IceCube          |
| Time span           | N/A              |

---

## 3. Key Metrics

| Metric                    | Observed value | Percentile vs null |
|---------------------------|----------------|--------------------|
| Hemisphere imbalance      | -0.4595 | 0.9900 |
| Preferred-axis score      | 0.1706 | 0.6700 |
| Energy–time Pearson r     | N/A | 0.5000 |
| Temporal clustering score | 1.0000 | 0.0000 |

**Signal tier:** `strong_anomaly_like_deviation`  
**Maximum percentile:** 0.9900

## 4. Trial-Factor Correction

Method: **holm** over **2** tested metrics.
Corrected verdict: **corrected_notable**

| Metric | Corrected percentile | Flag |
|--------|----------------------|------|
| hemisphere_imbalance | 0.9800 | notable |
| preferred_axis_score | 0.6700 | null |
| energy_time_pearson_r | N/A | insufficient_data |
| clustering_score | N/A | insufficient_data |

---

## 5. Interpretation

One or more metrics fall in the top 3% of the isotropic null distribution. This is a strong anomaly-like deviation; its cause requires further investigation.

---

## 6. What This Result Does NOT Prove

A deviation from an isotropic null model — even a statistically significant one — does **not** establish any of the following:

- That the universe or physical reality is a simulation.
- That the signal is cosmological rather than instrumental.
- That any specific physical model is correct.
- That the result would survive a pre-registered replication with trial-factor correction.

Anomaly-like deviations from an isotropic null are hypothesis-generating results, not proof of any specific physical or cosmological cause. Systematic effects, selection biases, and incomplete modeling should be ruled out before drawing any scientific conclusion.

---

## 7. Current Limitations

- Single-catalog analysis with a simple isotropic null; no exposure-map correction.
- Trial-factor correction applied (holm) across 2 metrics; interpret corrected verdict as primary.
- Selection biases and instrument systematics not characterised.
- This run is an internal first-results package, not a publishable result.

---

## 8. Recommended Next Upgrades

- Add exposure-map / acceptance-weighted null model (Stage 9 priority).
- HEALPix-based axis scan (NSIDE ≥ 8) for finer preferred-axis sensitivity.
- Multi-catalog cross-matching for cross-instrument consistency check.
- Blinded pre-registration before any significance claim.
- Trial-factor correction across simultaneously tested metrics.

---

*This memo is an internal first-results artifact produced by the commons-sentience-sandbox Stage 8 pipeline. It is not a scientific publication or preprint.*
