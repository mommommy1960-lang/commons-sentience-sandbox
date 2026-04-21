# Reality Audit — Stage 10 Template: Second-Catalog Replication

## What Stage 10 Is For

Stage 10 runs a second independent real catalog through the Stage 8/9
pipeline and produces a cross-catalog comparison memo.  The hypothesis
under test is narrow: does the Fermi GBM Stage 9 residual deviation
(weak anisotropy under exposure-corrected null) persist in an
independently-observed catalog?

If it does → warrants deeper investigation.
If it does not → most likely instrument-specific systematic.

---

## Run the Swift BAT pipeline (Stage 10)

```bash
python reality_audit/data_analysis/run_stage8_first_results.py \
    --input data/real/swift_bat3_grb_catalog.csv \
    --name stage10_swift_first_results \
    --output-dir outputs/stage10_first_results/stage10_swift_first_results \
    --null-mode exposure_corrected \
    --null-repeats 100 --axis-count 48 --seed 42 \
    --save-normalized
```

The `--null-mode` flag can be omitted; Swift BAT defaults to
`exposure_corrected` automatically.

---

## Run the cross-catalog comparison

```bash
python reality_audit/data_analysis/run_stage10_catalog_comparison.py
```

Default inputs (auto-located):
- Catalog A: `outputs/stage9_first_results/stage9_fermi_exposure_corrected/*_summary.json`
- Catalog B: `outputs/stage10_first_results/stage10_swift_first_results/*_summary.json`

Override with explicit paths:

```bash
python reality_audit/data_analysis/run_stage10_catalog_comparison.py \
    --summary-a outputs/stage9_first_results/stage9_fermi_exposure_corrected/stage9_fermi_exposure_corrected_summary.json \
    --summary-b outputs/stage10_first_results/stage10_swift_first_results/stage10_swift_first_results_summary.json \
    --output-dir outputs/stage10_first_results/comparison \
    --name stage10_catalog_comparison
```

---

## Convenience runner

```bash
python scripts/run_stage10_catalog_comparison.py
```

This produces:
- `outputs/stage10_first_results/comparison/stage10_catalog_comparison_memo.md`
- `outputs/stage10_first_results/comparison/stage10_catalog_comparison.json`

---

## How to obtain the Swift BAT catalog

The Swift BAT GRB catalog can be fetched programmatically from HEASARC TAP:

```python
import urllib.request, urllib.parse, xml.etree.ElementTree as ET
import base64, struct, csv, math

query = """SELECT name, ra, dec, bat_t90, bat_fluence, trigger_time
FROM swiftgrb WHERE ra IS NOT NULL AND dec IS NOT NULL ORDER BY name"""
url = ('https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync?REQUEST=doQuery'
       '&LANG=ADQL&FORMAT=votable&QUERY=' + urllib.parse.quote(query))
# ... (parse binary VOTable and write to data/real/swift_bat3_grb_catalog.csv)
```

See `data/real/README_public_catalog_ingest.md` for column requirements.

---

## Consistency verdict key

| Verdict | Meaning |
|---------|---------|
| `consistent_null` | Both catalogs: no anomaly. Corrected null absorbed any pattern. |
| `partial_agreement` | Both show some deviation. Investigate common systematics first. |
| `inconsistent` | Catalogs disagree. Most likely instrument-specific systematic. |

---

## What counts as "replication"

A result **replicates** across catalogs if:
1. Both catalogs show a deviation at the same interpretation tier.
2. The preferred axis (if applicable) points in the same direction (within error).
3. The deviation persists after per-catalog acceptance correction.
4. The cross-catalog comparison produces `partial_agreement` or better.

A result **does NOT replicate** if one catalog shows a deviation and the other does not,
especially when the non-deviating catalog has comparable statistical power.

---

## Current Stage 10 result summary

| Run | N events | Null | Hemi pct | Axis pct | Tier |
|-----|----------|------|----------|----------|------|
| Fermi GBM (Stage 9) | 3000 | exposure_corrected | 0.85 | 0.89 | `weak_anomaly_like_deviation` |
| Swift BAT (Stage 10) | 872 | exposure_corrected | 0.63 | 0.57 | `no_anomaly_detected` |
| **Verdict** | — | — | — | — | **INCONSISTENT** |

Cross-catalog disagreement: no evidence for a catalog-independent anisotropy.
The Fermi GBM residual is most likely instrument-specific.

---

*This template is part of the commons-sentience-sandbox Stage 10 artifact layer.
Internal guide only — not a scientific claim.*
