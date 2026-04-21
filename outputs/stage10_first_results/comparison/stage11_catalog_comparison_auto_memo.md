# Stage 11: Three-Catalog Comparison Memo

**Internal first-results artifact — not a scientific publication.**
*Generated: 2026-04-21T18:17:54.252416Z*

---

## Verdict: PARTIAL_REPLICATION

---

## Catalog Table

| Catalog | N | Null mode | Hemi pct | Axis pct | Tier |
|---------|---|-----------|----------|----------|------|
| fermi_lat_grb_catalog | 3000 | exposure_corrected | 0.8500 | 0.8900 | `weak_anomaly_like_deviation` |
| swift_bat3_grb_catalog | 872 | exposure_corrected | 0.6300 | 0.5700 | `no_anomaly_detected` |
| icecube_hese_events | 37 | isotropic | 0.9900 | 0.6700 | `strong_anomaly_like_deviation` |

---

## Replication Pattern

- Anomaly-like catalogs: fermi_lat_grb_catalog, icecube_hese_events
- Null-like catalogs: swift_bat3_grb_catalog
- Instrument-specific residual pattern likely: False
- Supports catalog-independent claim: False

---

## Interpretation

Two catalogs (fermi_lat_grb_catalog, icecube_hese_events) show anomaly-like deviation, while one (swift_bat3_grb_catalog) does not. This is mixed evidence and may indicate instrument/population effects rather than a universal sky anisotropy.

---

## Pairwise Context

- A/B verdict: inconsistent
- A/C verdict: partial_agreement
- B/C verdict: inconsistent

---

## Caveats

- Three-catalog consistency improves robustness but does not by itself prove a physical mechanism.
- Catalogs differ in selection function, energy band, and source population.
- Small catalogs (especially IceCube HESE) are underpowered for exclusion-level claims.
- Trial-factor correction and preregistration status should be checked in each input summary.

---

*This comparison is exploratory unless all inputs were run under a locked preregistration plan.*
