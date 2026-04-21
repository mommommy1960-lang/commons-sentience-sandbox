# Reality Audit Stage 12 Template

Use this template to run Stage 12 IceCube diagnostics in exploratory and
confirmatory modes and fold robustness into cross-catalog interpretation.

---

## 1) Exploratory IceCube Diagnostics

```bash
python reality_audit/data_analysis/run_stage12_icecube_diagnostics.py \
  --input data/real/icecube_hese_events.csv \
  --output-dir outputs/stage12_icecube_diagnostics/stage12_icecube_diagnostics \
  --seed 42 \
  --axis-modes 24,48,96 \
  --leave-k-out 1 \
  --repeats 100 \
  --run-mode exploratory
```

Primary outputs:

- `stage12_icecube_diagnostics_summary.json`
- `stage12_icecube_diagnostics_memo.md`
- `stage12_metric_stability_table.csv`
- `stage12_axis_count_sensitivity.png`
- `stage12_leave_k_out_stability.png`

---

## 2) Confirmatory Diagnostics + Stage 8 Rerun

```bash
python reality_audit/data_analysis/run_stage12_icecube_diagnostics.py \
  --input data/real/icecube_hese_events.csv \
  --output-dir outputs/stage12_icecube_diagnostics/stage12_icecube_confirmatory \
  --seed 42 \
  --axis-modes 48,96,192 \
  --leave-k-out 1 \
  --repeats 100 \
  --preregistration configs/preregistered_anisotropy_plan.json \
  --run-mode preregistered_confirmatory
```

Confirmatory rerun outputs are written under:

- `confirmatory_rerun/stage12_icecube_confirmatory_rerun_summary.json`
- `confirmatory_rerun/stage12_icecube_confirmatory_rerun_memo.md`

---

## 3) Integrate Robustness Into Three-Catalog Comparison

```bash
python reality_audit/data_analysis/run_stage10_catalog_comparison.py \
  --require-three \
  --summary-a outputs/stage9_first_results/stage9_fermi_exposure_corrected/stage9_fermi_exposure_corrected_summary.json \
  --summary-b outputs/stage10_first_results/stage10_swift_first_results/stage10_swift_first_results_summary.json \
  --summary-c outputs/stage12_icecube_diagnostics/stage12_icecube_confirmatory/confirmatory_rerun/stage12_icecube_confirmatory_rerun_summary.json \
  --icecube-diagnostics outputs/stage12_icecube_diagnostics/stage12_icecube_diagnostics/stage12_icecube_diagnostics_summary.json \
  --name stage12_comparison_with_robustness
```

Expected output:

- `outputs/stage10_first_results/comparison/stage12_comparison_with_robustness.json`
- `outputs/stage10_first_results/comparison/stage12_comparison_with_robustness_memo.md`

---

## 4) Validation Tests

```bash
python -m pytest tests/test_stage12_icecube_diagnostics.py -v
python -m pytest tests/test_catalog_comparison.py -v
python -m pytest tests/test_stage8_first_results.py -v
```

---

## 5) Confirmatory Checklist

1. `run_mode` is `preregistered_confirmatory` in confirmatory rerun metadata.
2. Preregistration match block is present and reviewed for mismatches.
3. Diagnostics summary includes robustness label and supporting signals.
4. Three-catalog comparison includes `icecube_robustness` integration.
5. Reporting clearly distinguishes exploratory versus confirmatory interpretation.
