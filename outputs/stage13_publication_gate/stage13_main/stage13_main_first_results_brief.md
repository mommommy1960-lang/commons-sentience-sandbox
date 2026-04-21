# Internal First-Results Brief

> This is an internal pipeline decision document.
> It is not a scientific paper and does not constitute a publishable claim.

Generated: 2026-04-21T21:23:17.596695Z

---

## What Was Tested

The Reality Audit public anisotropy program tests whether high-energy astrophysical event arrival directions show a statistically significant sky-position anisotropy that persists across independent instrument catalogs, after correcting for known instrument acceptance geometry.

The primary null hypothesis is that event arrival directions are consistent with isotropic (or acceptance-corrected isotropic) sky coverage.

Two primary statistics are evaluated: hemisphere imbalance and preferred-axis score. Both are corrected for multiple testing using the Holm method.

---

## Current Evidence Status

Catalogs available: **3**

| Catalog | N | Null model | Hemi pct | Axis pct | Tier | Run mode |
|---|---|---|---|---|---|---|
| fermi_lat_grb_catalog | None | None | N/A | N/A | `None` | None |
| swift_bat3_grb_catalog | None | None | N/A | N/A | `None` | None |
| icecube_hese_events | None | None | N/A | N/A | `None` | None |

**Cross-catalog replication verdict: `PARTIAL_REPLICATION`**

### Interpretation

Two catalogs (fermi_lat_grb_catalog, icecube_hese_events) show anomaly-like deviation, while one (swift_bat3_grb_catalog) does not. This is mixed evidence and may indicate instrument/population effects rather than a universal sky anisotropy. Stage 12 diagnostics classify the IceCube signal as relatively stable under the tested perturbations, but this does not remove small-N limitations.

### Caveats

- Three-catalog consistency improves robustness but does not by itself prove a physical mechanism.
- Catalogs differ in selection function, energy band, and source population.
- Small catalogs (especially IceCube HESE) are underpowered for exclusion-level claims.
- Trial-factor correction and preregistration status should be checked in each input summary.
- IceCube robustness diagnostic label: relatively_stable (fragile=[], robust=['axis_density_stable', 'leave_k_out_stable']).

---

## Which Catalogs Support / Do Not Support Replication

- **fermi_lat_grb_catalog**: does NOT show anomaly-like deviation (`unknown`)
- **swift_bat3_grb_catalog**: does NOT show anomaly-like deviation (`unknown`)
- **icecube_hese_events**: does NOT show anomaly-like deviation (`unknown`)

---

## Is the Current State Publishable?

**Gate verdict: `NOT_READY`**

Publishable internally: **No** — the following required conditions are not yet met.

Failing required gates:

- `prereg_present`
- `prereg_locked`
- `trial_correction_applied`

---

## What Must Be Fixed Next

1. Lock the preregistration plan (_locked: true) before confirmatory reruns.
1. Apply Holm or Bonferroni trial-factor correction.
1. IceCube HESE is small-N; supplement with a larger independent catalog.
1. External scientific review is required before public circulation.
1. Resolve gate failure: prereg_present

---

This brief is generated automatically from pipeline outputs.
Do not circulate outside the immediate project team without external review.
