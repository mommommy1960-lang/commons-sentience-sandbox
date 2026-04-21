# Reality Audit Stage 13 Template

Use this template to run Stage 13 publication gating on any set of pipeline outputs.

---

## 1) Quick Run (Default Paths)

```bash
python reality_audit/data_analysis/run_stage13_publication_gate.py
# or equivalently:
python scripts/run_stage13_publication_gate.py
```

Reads defaults:
- Fermi: `outputs/stage9_first_results/stage9_fermi_exposure_corrected/…_summary.json`
- Swift: `outputs/stage10_first_results/stage10_swift_first_results/…_summary.json`
- IceCube: `outputs/stage8_first_results/stage11_icecube_first_results/…_summary.json`
- Comparison: `outputs/stage10_first_results/comparison/stage12_comparison_with_robustness.json`
- Diagnostics: `outputs/stage12_icecube_diagnostics/stage12_icecube_diagnostics/…_summary.json`

---

## 2) Explicit Paths

```bash
python reality_audit/data_analysis/run_stage13_publication_gate.py \
  --fermi      outputs/stage9_first_results/stage9_fermi_exposure_corrected/stage9_fermi_exposure_corrected_summary.json \
  --swift      outputs/stage10_first_results/stage10_swift_first_results/stage10_swift_first_results_summary.json \
  --icecube    outputs/stage8_first_results/stage11_icecube_first_results/stage11_icecube_first_results_summary.json \
  --comparison outputs/stage10_first_results/comparison/stage12_comparison_with_robustness.json \
  --diagnostics outputs/stage12_icecube_diagnostics/stage12_icecube_diagnostics/stage12_icecube_diagnostics_summary.json \
  --output-dir outputs/stage13_publication_gate/stage13_main \
  --name       stage13_main
```

---

## 3) Understand the Gate Verdict

| Verdict | Meaning |
|---|---|
| `not_ready` | Required gates failing. Do not circulate. |
| `internally_reviewable` | All required gates pass. Internal team review only. |
| `candidate_first_results_note` | Required + recommended gates pass. Internal first-results note OK. |
| `ready_for_external_review` | All gates pass, external review initiated. |

---

## 4) Path to internally_reviewable

To move from `not_ready` to `internally_reviewable`:

### a) Lock the preregistration plan

```bash
# Edit configs/preregistered_anisotropy_plan.json
# Set "_locked": true
# Set "registration_date": "<today's date>"
```

### b) Rerun catalogs with preregistration and confirmatory mode

```bash
# Fermi
python reality_audit/data_analysis/run_stage8_first_results.py \
  --input data/real/fermi_lat_grb_catalog.csv \
  --name stage14_fermi_confirmatory \
  --output-dir outputs/stage14_first_results/stage14_fermi_confirmatory \
  --null-mode exposure_corrected \
  --null-repeats 500 \
  --axis-count 192 \
  --seed 42 \
  --preregistration-plan configs/preregistered_anisotropy_plan.json \
  --run-mode preregistered_confirmatory

# Swift
python reality_audit/data_analysis/run_stage8_first_results.py \
  --input data/real/swift_bat3_grb_catalog.csv \
  --name stage14_swift_confirmatory \
  --output-dir outputs/stage14_first_results/stage14_swift_confirmatory \
  --null-mode exposure_corrected \
  --null-repeats 500 \
  --axis-count 192 \
  --seed 42 \
  --preregistration-plan configs/preregistered_anisotropy_plan.json \
  --run-mode preregistered_confirmatory

# IceCube
python reality_audit/data_analysis/run_stage8_first_results.py \
  --input data/real/icecube_hese_events.csv \
  --name stage14_icecube_confirmatory \
  --output-dir outputs/stage14_first_results/stage14_icecube_confirmatory \
  --null-mode isotropic \
  --null-repeats 500 \
  --axis-count 192 \
  --seed 42 \
  --preregistration-plan configs/preregistered_anisotropy_plan.json \
  --run-mode preregistered_confirmatory
```

### c) Re-run comparison against new confirmatory outputs

```bash
python reality_audit/data_analysis/run_stage10_catalog_comparison.py \
  --summary-a outputs/stage14_first_results/stage14_fermi_confirmatory/stage14_fermi_confirmatory_summary.json \
  --summary-b outputs/stage14_first_results/stage14_swift_confirmatory/stage14_swift_confirmatory_summary.json \
  --summary-c outputs/stage14_first_results/stage14_icecube_confirmatory/stage14_icecube_confirmatory_summary.json \
  --require-three \
  --icecube-diagnostics outputs/stage12_icecube_diagnostics/stage12_icecube_diagnostics/stage12_icecube_diagnostics_summary.json \
  --name stage14_comparison_confirmatory
```

### d) Re-run Stage 13 gate against new outputs

```bash
python reality_audit/data_analysis/run_stage13_publication_gate.py \
  --fermi      outputs/stage14_first_results/stage14_fermi_confirmatory/stage14_fermi_confirmatory_summary.json \
  --swift      outputs/stage14_first_results/stage14_swift_confirmatory/stage14_swift_confirmatory_summary.json \
  --icecube    outputs/stage14_first_results/stage14_icecube_confirmatory/stage14_icecube_confirmatory_summary.json \
  --comparison outputs/stage10_first_results/comparison/stage14_comparison_confirmatory.json \
  --name       stage14_gate_check
```

---

## 5) Validation Tests

```bash
python -m pytest tests/test_stage13_publication_gate.py -v
```

---

## 6) Stage 13 Checklist

1. Gate config loaded from `configs/publication_gate_checklist.json`.
2. Required gates reviewed and explained to team.
3. Gate evaluation run against current outputs — verdict recorded.
4. First-results brief written to `outputs/stage13_publication_gate`.
5. Output hygiene report reviewed.
6. Next blocking items identified and assigned.
