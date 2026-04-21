# Reality Audit Stage 11 Template

Use this template to run the Stage 11 hardened workflow end-to-end.

---

## 1) Validate Preregistration Plan

```bash
python - << 'PY'
from reality_audit.data_analysis.preregistration import load_preregistration_plan, validate_preregistration_plan
plan = load_preregistration_plan('configs/preregistered_anisotropy_plan.json')
issues = validate_preregistration_plan(plan)
print('issues:', issues)
PY
```

If this is a confirmatory run, set `_locked: true` before execution.

---

## 2) Run Stage 8 First-Results Per Catalog (with prereg plan)

### Fermi GBM

```bash
python reality_audit/data_analysis/run_stage8_first_results.py \
  --input data/real/fermi_lat_grb_catalog.csv \
  --name stage11_fermi_confirmatory \
  --output-dir outputs/stage11_first_results/stage11_fermi_confirmatory \
  --null-mode exposure_corrected \
  --null-repeats 500 \
  --axis-count 192 \
  --seed 42 \
  --preregistration-plan configs/preregistered_anisotropy_plan.json
```

### Swift BAT

```bash
python reality_audit/data_analysis/run_stage8_first_results.py \
  --input data/real/swift_bat3_grb_catalog.csv \
  --name stage11_swift_confirmatory \
  --output-dir outputs/stage11_first_results/stage11_swift_confirmatory \
  --null-mode exposure_corrected \
  --null-repeats 500 \
  --axis-count 192 \
  --seed 42 \
  --preregistration-plan configs/preregistered_anisotropy_plan.json
```

### IceCube HESE

```bash
python reality_audit/data_analysis/run_stage8_first_results.py \
  --input data/real/icecube_hese_events.csv \
  --name stage11_icecube_confirmatory \
  --output-dir outputs/stage11_first_results/stage11_icecube_confirmatory \
  --null-mode isotropic \
  --null-repeats 500 \
  --axis-count 192 \
  --seed 42 \
  --preregistration-plan configs/preregistered_anisotropy_plan.json
```

---

## 3) Run Cross-Catalog Comparison

### Auto mode (uses A/B defaults and C if available)

```bash
python reality_audit/data_analysis/run_stage10_catalog_comparison.py \
  --name stage11_catalog_comparison_auto
```

### Require full three-catalog comparison

```bash
python reality_audit/data_analysis/run_stage10_catalog_comparison.py \
  --summary-a outputs/stage9_first_results/stage9_fermi_exposure_corrected/stage9_fermi_exposure_corrected_summary.json \
  --summary-b outputs/stage10_first_results/stage10_swift_first_results/stage10_swift_first_results_summary.json \
  --summary-c outputs/stage8_first_results/stage11_icecube_first_results/stage11_icecube_first_results_summary.json \
  --require-three \
  --name stage11_catalog_comparison_required
```

---

## 4) Trial-Factor Interpretation Key

| Corrected verdict | Meaning |
|---|---|
| `corrected_discovery` | At least one metric remains above discovery threshold after correction |
| `corrected_notable` | At least one metric remains above exclusion threshold after correction |
| `corrected_null` | No metric remains above exclusion threshold after correction |

Correction methods supported: `holm`, `bonferroni`, `none`.

---

## 5) Axis-Scan Modes

Stage 11 supports these axis planning modes in the anisotropy engine:

- `auto`: legacy 48-axis scan for small runs, dense deterministic grid for larger scans
- `coarse`: legacy deterministic 48-axis behavior
- `dense`: deterministic higher-resolution grid
- `healpix_plan`: planning hook; records intended HEALPix target and uses dense fallback

---

## 6) Confirmatory Checklist

1. Plan validated and `_locked: true` before run.
2. Plan hash recorded in output metadata.
3. Trial-factor correction present in summary JSON.
4. Three-catalog comparison completed.
5. Interpretation explicitly states exploratory vs confirmatory status.
