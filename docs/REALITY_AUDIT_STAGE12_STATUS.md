# Reality Audit Stage 12 Status

## Stage Goal

Stage 12 adds IceCube-focused robustness diagnostics and explicit run-discipline
tracking for exploratory versus preregistered confirmatory analyses.

This stage is designed to answer a narrow question:
Is the Stage 11 IceCube anomaly-like result stable under reasonable perturbations,
and is confirmatory rerun behavior auditable against the preregistration plan?

---

## What Stage 12 Adds

| Capability | Status | Notes |
|---|---|---|
| IceCube diagnostics module | COMPLETE | `reality_audit/data_analysis/icecube_diagnostics.py` |
| Small-N axis-density sensitivity | COMPLETE | Multiple axis-count modes summarized in diagnostics JSON |
| Leave-k-out influence analysis | COMPLETE | Stability labels derived from omission perturbations |
| Epoch-split persistence check | COMPLETE | Time-split consistency reported in diagnostics summary |
| Robustness memo + manifest outputs | COMPLETE | Memo and manifest written by Stage 12 runner |
| Stability table output | COMPLETE | `stage12_metric_stability_table.csv` |
| Diagnostic plots output | COMPLETE | axis-count and leave-k-out PNG plots |
| Explicit run mode in Stage 8 | COMPLETE | `exploratory` vs `preregistered_confirmatory` metadata |
| Preregistration plan-match auditing | COMPLETE | Confirmatory runs annotate match/mismatch details |
| Three-catalog robustness integration | COMPLETE | Stage 10/11 comparison includes IceCube robustness interpretation |

---

## Current Stage 12 Artifact Snapshot

### Exploratory diagnostics run

- Output dir:
  `outputs/stage12_icecube_diagnostics/stage12_icecube_diagnostics`
- Robustness label in summary:
  `relatively_stable`
- Key artifacts:
  - `stage12_icecube_diagnostics_summary.json`
  - `stage12_icecube_diagnostics_memo.md`
  - `stage12_metric_stability_table.csv`
  - `stage12_axis_count_sensitivity.png`
  - `stage12_leave_k_out_stability.png`

### Confirmatory diagnostics run (with rerun)

- Output dir:
  `outputs/stage12_icecube_diagnostics/stage12_icecube_confirmatory`
- Confirmatory rerun summary path:
  `outputs/stage12_icecube_diagnostics/stage12_icecube_confirmatory/confirmatory_rerun/stage12_icecube_confirmatory_rerun_summary.json`
- Run discipline is recorded in metadata (`run_mode` and preregistration match block).

### Cross-catalog interpretation integration

- Comparison JSON:
  `outputs/stage10_first_results/comparison/stage12_comparison_with_robustness.json`
- Includes an `icecube_robustness` block and interpretation caveat updates.

---

## Interpretation Guardrails

1. Stage 12 robustness labels are internal diagnostics, not external scientific proof.
2. IceCube HESE remains a small-N catalog; uncertainty is still high.
3. Confirmatory status requires a locked preregistration plan (`_locked: true`).
4. Mixed cross-catalog evidence remains possible even with a stable IceCube label.

---

## Remaining Publishability Blockers (Post-Stage 12)

1. Locked prereg confirmatory reruns across all catalogs with stable plan hash.
2. Better-powered independent replication datasets.
3. Full cross-instrument systematic controls and external review.

---

## Final Validation Snapshot

Validated during Stage 12 closeout:

- `python -m pytest tests/test_stage12_icecube_diagnostics.py -v`:
  7 passed
- `python -m pytest tests/test_catalog_comparison.py -v`:
  28 passed
- `python -m pytest tests/test_stage8_first_results.py -v`:
  23 passed

Cross-catalog robustness integration output:

- `outputs/stage10_first_results/comparison/stage12_comparison_with_robustness.json`
- comparison verdict: `partial_replication`
- IceCube robustness label: `relatively_stable`
