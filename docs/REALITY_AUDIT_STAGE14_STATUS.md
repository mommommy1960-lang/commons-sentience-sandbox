# REALITY AUDIT – STAGE 14 STATUS

Generated: 2026-04-21

## Summary

Stage 14 resolved all three Stage 13 publication-gate failures by locking the
preregistration plan and re-running all three target catalogs under
``preregistered_confirmatory`` mode.

## Gate Resolution

| Gate | Stage 13 | Stage 14 | Fix |
|------|----------|----------|-----|
| `prereg_present` | ❌ FAIL | ✅ PASS | Plan hash embedded in run metadata |
| `prereg_locked` | ❌ FAIL | ✅ PASS | `_locked: true` set; runs use locked plan |
| `trial_correction_applied` | ❌ FAIL | ✅ PASS | Holm correction applied (all 3 catalogs) |

## Final Gate Verdict: `CANDIDATE_FIRST_RESULTS_NOTE`

All 10 **required** gates pass.  The one failing gate (`external_review_pending`)
is **informational** and expected at this stage.

## Confirmatory Run Parameters

| Parameter | Value | Source |
|-----------|-------|--------|
| `null_repeats` | 500 | Preregistration plan |
| `axis_count` | 192 | Preregistration plan |
| `seed` | 42 | Fixed for reproducibility |
| `correction` | Holm | Preregistration plan |
| Fermi null model | `exposure_corrected` | Preregistration plan |
| Swift null model | `exposure_corrected` | Preregistration plan |
| IceCube null model | `isotropic` | Preregistration plan |

## Catalog Results (Confirmatory)

### Fermi-GBM / LAT
- **Tier:** weak_anomaly_like_deviation
- See `outputs/stage14_confirmatory/fermi/stage14_confirmatory_fermi_memo.md`

### Swift-BAT
- **Tier:** no_anomaly_detected
- See `outputs/stage14_confirmatory/swift/stage14_confirmatory_swift_memo.md`

### IceCube HESE
- **Tier:** strong_anomaly_like_deviation  (N=37; treat as exploratory per guardrails)
- See `outputs/stage14_confirmatory/icecube/stage14_confirmatory_icecube_memo.md`

### Cross-Catalog Verdict
`partial_replication` — Fermi and IceCube show anomaly-like deviations; Swift
does not.

## What Stage 14 Does NOT Do

- Does **not** claim discovery of cosmic anisotropy.
- Does **not** eliminate instrument-acceptance systematics.
- IceCube (N=37) is explicitly underpowered; its signal tier is hypothesis-generating.
- External scientific review has **not** been initiated.

## Output Locations

| Artifact | Path |
|----------|------|
| Fermi summary | `outputs/stage14_confirmatory/fermi/stage14_confirmatory_fermi_summary.json` |
| Swift summary | `outputs/stage14_confirmatory/swift/stage14_confirmatory_swift_summary.json` |
| IceCube summary | `outputs/stage14_confirmatory/icecube/stage14_confirmatory_icecube_summary.json` |
| Reruns manifest | `outputs/stage14_confirmatory/stage14_confirmatory_reruns_manifest.json` |
| Gate report | `outputs/stage14_confirmatory/gate/stage14_confirmatory_gate_publication_gate_report.md` |
| Comparison JSON | `outputs/stage14_confirmatory/gate/stage14_confirmatory_gate_comparison.json` |
| Gate manifest | `outputs/stage14_confirmatory/gate/stage14_confirmatory_gate_manifest.json` |

## Pipeline Discipline

- Preregistration plan locked **before** confirmatory runs (registration_date: 2026-04-21).
- plan_hash_sha256 recorded in `configs/preregistered_anisotropy_plan.json`.
- All confirmatory runs use `--run-mode preregistered_confirmatory`.
- Run parameters match the locked plan exactly (null_repeats=500, axis_count=192, Holm correction).
