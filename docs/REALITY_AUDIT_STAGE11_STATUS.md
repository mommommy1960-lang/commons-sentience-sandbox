# Reality Audit Stage 11 Status

## Stage Goal

Stage 11 hardens the public anisotropy program for confirmatory work by adding:
1. third-catalog replication support (IceCube HESE),
2. preregistration scaffolding (locked analysis plan),
3. multiple-testing correction support,
4. higher-resolution axis-scan planning hooks,
5. three-catalog comparison outputs.

This follows the Operational Companion roadmap emphasis on validation,
systematics, replication, and analysis locking.

---

## Roadmap Alignment

### Data-analysis-first continuity
- Stage 7: public anisotropy pipeline
- Stage 8: first real-catalog orchestration and memo
- Stage 9: exposure-corrected null model
- Stage 10: second-catalog replication + cross-catalog comparison
- Stage 11: confirmatory hardening without changing core hypothesis

### What Stage 11 explicitly avoids
- no hardware work
- no metaphysical claims
- no unrelated feature expansion
- no re-architecture of working Stage 7–10 workflows

---

## Implemented Capabilities

| Capability | Status | Notes |
|---|---|---|
| IceCube HESE catalog support | COMPLETE | `data/real/icecube_hese_events.csv` added and supported as first-class catalog |
| IceCube schema validation | COMPLETE | `validate_icecube_hese_schema()` checks required fields and coordinate ranges |
| Preregistration template doc | COMPLETE | `docs/REALITY_AUDIT_PREREGISTRATION_TEMPLATE.md` |
| Machine-readable prereg plan | COMPLETE | `configs/preregistered_anisotropy_plan.json` |
| Run metadata prereg recording | COMPLETE | Stage 8 now records plan summary and hash |
| Trial-factor correction | COMPLETE | Holm / Bonferroni correction via `trial_factor_correction.py` |
| Corrected labels in memo/output | COMPLETE | Stage 8 memo includes corrected verdict and per-metric corrected labels |
| Higher-resolution axis scan abstraction | COMPLETE | Deterministic `dense` mode and `healpix_plan` hook |
| Three-catalog comparison | COMPLETE | 2-catalog and 3-catalog support in comparison CLI |

---

## Stage 11 Result Snapshot

### Catalog-level runs currently available

| Catalog | N | Null mode | Tier |
|---|---|---|---|
| Fermi GBM | 3000 | exposure_corrected | `weak_anomaly_like_deviation` |
| Swift BAT | 872 | exposure_corrected | `no_anomaly_detected` |
| IceCube HESE | 37 | isotropic | `strong_anomaly_like_deviation` |

### Three-catalog comparison

Current auto comparison verdict: `partial_replication`.

Interpretation: two catalogs show anomaly-like behavior (Fermi, IceCube) and
one does not (Swift), which is mixed evidence and does not support a clean
catalog-independent anisotropy claim.

---

## Why These Hardening Steps Matter

### Why preregistration matters now
Without locking analysis choices, exploratory flexibility can inflate apparent
significance and make replication ambiguous.

### Why third-catalog replication matters
A two-catalog disagreement can still be instrument-specific. A third,
independent catalog adds leverage on replication versus residual systematics.

### Why multiple-testing correction matters
The pipeline evaluates multiple metrics. Reporting only the strongest uncorrected
metric inflates false-positive risk.

### Why higher-resolution axis planning matters
A coarse 48-axis grid can miss or blur directional structure. Dense deterministic
scans and HEALPix planning are needed for defensible directional tests.

---

## What Still Blocks a Publishable First-Results Note

1. True instrument exposure maps (Fermi FSSC FITS) are still required.
2. IceCube HESE remains a small-N catalog and underpowered for exclusion-level inference.
3. Confirmatory reruns must use `_locked: true` preregistration with stable hash.
4. Cross-catalog systematics analysis remains incomplete.
5. Independent external review is still required.
