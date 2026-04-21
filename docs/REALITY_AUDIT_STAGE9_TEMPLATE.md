# Reality Audit — Stage 9 Template: Exposure-Corrected Null Model

## What Stage 9 Is For

Stage 9 upgrades the anisotropy null model from a naive uniform isotropic
sphere to an empirical sky-acceptance proxy built from the observed catalog.

This corrects for the dominant systematic in Stage 8: the Fermi GBM
(and similar wide-field detectors) do not observe the sky uniformly, so
comparing against a uniform null almost always produces a spurious
"strong anomaly" that is actually just the detector acceptance pattern.

---

## How to Run the Fermi GBM Catalog with Stage 9

### Exposure-corrected null (Stage 9 default):

```bash
python reality_audit/data_analysis/run_stage8_first_results.py \
    --input data/real/fermi_lat_grb_catalog.csv \
    --name stage9_fermi_exposure_corrected \
    --output-dir outputs/stage9_first_results/stage9_fermi_exposure_corrected \
    --null-mode exposure_corrected \
    --null-repeats 100 \
    --axis-count 48 \
    --seed 42 \
    --plots \
    --save-normalized
```

### Isotropic null comparison (for side-by-side):

```bash
python reality_audit/data_analysis/run_stage8_first_results.py \
    --input data/real/fermi_lat_grb_catalog.csv \
    --name stage9_fermi_isotropic_compare \
    --output-dir outputs/stage9_first_results/stage9_fermi_isotropic_compare \
    --null-mode isotropic \
    --null-repeats 100 \
    --axis-count 48 \
    --seed 42 \
    --plots \
    --save-normalized
```

---

## How to Compare Isotropic vs Exposure-Corrected Results

After both runs, compare the two summary JSONs:

```python
import json

for run in ["stage9_fermi_isotropic_compare", "stage9_fermi_exposure_corrected"]:
    with open(f"outputs/stage9_first_results/{run}/{run}_summary.json") as f:
        d = json.load(f)
    r  = d["results"]
    nc = r["null_comparison"]
    sig = r["signal_evaluation"]
    print(f"\n{run}")
    print(f"  null_mode:        {nc['null_mode']}")
    print(f"  hemi_percentile:  {nc['hemi_percentile']:.4f}")
    print(f"  axis_percentile:  {nc['axis_percentile']:.4f}")
    print(f"  tier:             {sig['tier']}")
```

**Interpretation guide:**
- If isotropic shows `strong_anomaly` but exposure-corrected shows `no_anomaly`:
  the Stage 8 result was acceptance-driven. The corrected null absorbed the pattern.
- If exposure-corrected still shows a moderate or strong anomaly:
  the signal cannot be fully explained by the observed sky coverage.
  Investigate further with a proper instrument-response-weighted null.

---

## What Collaborators Should Look For in the Revised Memo

The Stage 9 memo (`<name>_memo.md`) will include:

- **Null model section** — which null was used and why
- **Key metrics table** — same four metrics, now vs the exposure-corrected null
- **Interpretation** — tier classification with null-model context
- **Limitations** — explicit statement that the empirical correction absorbs signal

If the preferred-axis percentile drops below 0.75 vs the corrected null,
the Stage 8 "strong anomaly" was not a meaningful signal — it was an artefact
of a poorly matched null.

If the preferred-axis percentile remains above 0.90+ even after correction,
that warrants:
1. Checking with a proper exposure FITS map
2. Running a second catalog
3. Filing a pre-registration before unblinding

---

## Current Known Outputs (Stage 9)

Located in:
- `outputs/stage9_first_results/stage9_fermi_exposure_corrected/`
- `outputs/stage9_first_results/stage9_fermi_isotropic_compare/`

Each folder contains the same artifact set as Stage 8:
normalized CSV, summary JSON, summary Markdown, sky plot, null comparison
plot, axis scan plot, Stage 8 memo, Stage 8 manifest, Stage 7 manifest.

---

*This template is part of the commons-sentience-sandbox Stage 9 artifact layer.
Internal guide only — not a scientific claim.*
