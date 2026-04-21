# Public Catalog Ingest — README

This directory (`data/real/`) holds real public event catalog files for use with the Stage 7 public-data anisotropy analysis track.

The pipeline does **not** download data automatically. You must obtain catalog files through the public data portals listed below and place them here before running any real-data analysis.

---

## Expected file format

CSV or TSV with a header row. The pipeline auto-detects delimiters. Minimum required columns:

| Column (or alias) | Schema field | Notes |
|---|---|---|
| `ra` or `ra_deg` or `raj2000` | `ra` | Right Ascension, decimal degrees, J2000 |
| `dec` or `dec_deg` or `dej2000` | `dec` | Declination, decimal degrees, J2000 |
| `event_id` or `name` or `grb_name` | `event_id` | Unique row identifier (auto-assigned if absent) |
| `arrival_time` or `trigger_mjd` or `mjd` | `arrival_time` | MJD preferred; any float accepted |
| `energy` or `fluence` or `energy_gev` | `energy` | Any energy-like scalar; no unit conversion applied |
| `instrument` or `detector` or `telescope` | `instrument` | Observatory or detector label |
| `epoch` or `year` or `date` | `epoch` | Observation epoch label |

All columns except `ra` and `dec` are optional in the sense that missing values are recorded as `None`. However, the more columns you provide, the more metrics can be computed.

---

## Supported public catalog sources

### Fermi-LAT GRB Catalog

- **Source:** NASA HEASARC Fermi GRB Catalog
- **URL:** https://heasarc.gsfc.nasa.gov/db-perl/W3Browse/w3table.pl?tablehead=name%3Dfermilgrb
- **Minimum columns to export:** `name`, `ra_deg`, `dec_deg`, `trigger_mjd`
- **Save as:** `data/real/fermi_lat_grb_catalog.csv`

### Swift BAT3 GRB Catalog

- **Source:** Swift BAT3 GRB Catalog (Lien et al. 2016)
- **URL:** https://swift.gsfc.nasa.gov/results/batgrbcat/
- **Minimum columns to export:** `GRBname`, `RA`, `Dec`, `Trigger_time_MJD`, `Fluence`
- **Save as:** `data/real/swift_bat3_grb_catalog.csv`

### IceCube HESE Events

- **Source:** IceCube HESE public data release
- **URL:** https://icecube.wisc.edu/science/data/HE-nu-2010-2012
- **Minimum columns to export:** `event`, `ra`, `dec`, `energy_TeV`, `year`
- **Save as:** `data/real/icecube_hese_events.csv`

---

## How the pipeline normalizes your file

1. Column names are lowercased and stripped of whitespace.
2. Known aliases (e.g., `raj2000` → `ra`, `trigger_mjd` → `arrival_time`) are applied.
3. Numeric fields (`ra`, `dec`, `energy`, `arrival_time`) are coerced to `float`; unparseable values become `None`.
4. If `event_id` is absent, the pipeline generates identifiers of the form `<source_name>_000001`.
5. A `_b_proxy` field (= `|dec|`) is added as a rough galactic latitude proxy.

---

## Running the analysis after placing a file

Replace `<catalog_file>` with the actual filename:

```bash
python reality_audit/data_analysis/run_public_anisotropy_study.py \
    --input data/real/<catalog_file> \
    --name my_real_catalog_run \
    --output-dir outputs/public_anisotropy/real_catalog \
    --config configs/public_anisotropy_manual_ingest.json \
    --null-repeats 100 \
    --axis-count 48 \
    --seed 42 \
    --plots \
    --save-normalized
```

Or use the convenience runner (auto-detects any supported catalog in this directory):

```bash
python scripts/run_public_anisotropy_examples.py
```

---

## Output files

After running, the `output-dir` will contain:

| File | Description |
|---|---|
| `<name>_summary.json` | Full analysis results in structured JSON |
| `<name>_results.csv` | One-row CSV summary for logging |
| `<name>_summary.md` | Human-readable Markdown report |
| `<name>_sky_plot.png` | RA/Dec scatter plot of events |
| `<name>_null_comparison.png` | Bar chart of metric percentiles vs isotropic null |
| `<name>_axis_scan.png` | Line plot of axis scores across all trial axes |
| `<name>_manifest.json` | List of all artifact file paths |

---

## Statistical caveat

Any anomaly-like deviation reported by this pipeline is a **hypothesis-generating result**, not proof of any specific physical or metaphysical claim. Results should be interpreted in light of instrument systematics, selection biases, and the exploratory nature of the analysis.
