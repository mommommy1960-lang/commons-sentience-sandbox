# How to Run the First Real Fermi-LAT Data Ingest

This document describes the exact sequence for ingesting a real Fermi-LAT GRB
event file into the blinded analysis pipeline for Experiment 1.

**Pre-condition:** The analysis registration is already frozen.
No framework changes should be made after this point unless required for
real-file compatibility.

---

## 1. Place the Real File

Drop your CSV file into:

```
data/real/
```

Do **not** rename or modify `synthetic_fermi_lat_grb_events.csv` — that file is
a pipeline rehearsal fixture and is **not** treated as real data.

---

## 2. Expected CSV Schema

| Column | Required | Accepted Aliases |
|---|---|---|
| `event_id` | ✅ | `id`, `row_id`, `index` |
| `grb_name` | ✅ | `source_id`, `source`, `grb_id`, `name`, `burst` |
| `energy_gev` | ✅ | `energy`, `photon_energy`, `energy_mev`, `e_gev` |
| `time_s` | ✅ | `photon_arrival_time_s`, `arrival_time_s`, `arrival_time`, `time`, `t`, `t_s` |
| `redshift` | ✅ | `z`, `z_spec`, `z_photo` |
| `grb_t90_s` | ✅ | `t90`, `t90_s` |

All columns are required. Any of the listed aliases will be auto-detected.
Energies may be in MeV (column name `energy_mev`) — the adapter converts to GeV.

---

## 3. Minimum Viable Thresholds

| Gate | Minimum |
|---|---|
| Total events | ≥ 30 |
| GRB sources with valid redshift | ≥ 5 |
| Duplicate event-ID fraction | < 0.1% |
| Energy range after conversion | 0.01–1000 GeV |

Files that do not meet these thresholds will receive a `REJECT` recommendation
and the blinded pipeline will not run.

---

## 4. Exact Command Sequence

### Step A — Pre-ingest package check

```bash
python reality_audit/data_analysis/check_fermi_lat_real_package.py \
  --input data/real/<your_file>.csv
```

Reads the file, validates schema and thresholds, and writes:
```
commons_sentience_sim/output/reality_audit/fermi_lat_real_package_check.json
```

Possible recommendations:
- `ACCEPT_FOR_BLINDED_RUN` — all gates pass; proceed to Step B
- `ACCEPT_WITH_WARNINGS` — review warnings before proceeding
- `REJECT` — fix the file or obtain a better dataset

### Step B — One-shot helper (recommended)

```bash
python reality_audit/data_analysis/run_first_real_ingest.py
```

This helper automatically:
1. Finds any non-synthetic CSV in `data/real/`
2. Runs the package check
3. If accepted, runs the blinded pipeline
4. Writes `first_real_ingest_manifest.json`
5. Stops safely and explains why if any gate fails

### Step C — Manual blinded run (alternative)

```bash
python reality_audit/data_analysis/run_fermi_lat_real_blinded.py \
  --source data/real/<your_file>.csv \
  --registration commons_sentience_sim/output/reality_audit/fermi_lat_real_analysis_registration.json
```

---

## 5. Output Files Written

| File | Contents |
|---|---|
| `commons_sentience_sim/output/reality_audit/fermi_lat_real_package_check.json` | Pre-ingest validation report |
| `.../fermi_lat_real_blinded_run/quality_control_report.json` | Full QC gate results |
| `.../fermi_lat_real_blinded_run/blinded_summary.json` | Analysis summary — signal keys BLINDED |
| `.../fermi_lat_real_blinded_run/run_manifest.json` | Run provenance and status |
| `.../first_real_ingest_manifest.json` | One-shot helper run record |

---

## 6. ⚠️ Critical Warnings

**DO NOT unblind without QC pass + explicit human approval.**

Unblinding requires ALL of the following:
- `ingest_complete: true` in the manifest
- All 9 QC gates passed (see `quality_control_report.json`)
- Registration hash verified
- Explicit human sign-off documented

See [docs/FERMI_LAT_REAL_DATA_QC_AND_UNBLINDING.md](FERMI_LAT_REAL_DATA_QC_AND_UNBLINDING.md)
for the complete list of 9 unblinding conditions.

The pipeline enforces `automatic_unblind=False` at the code level. Even if all
QC gates pass, statistical results remain `"BLINDED"` in all written files.

**DO NOT interpret the blinded summary.** The null-model statistics visible in
the blinded output (e.g. `null_mean_slope`) are NOT the result. The signal keys
(`p_value`, `z_score`, `observed_slope`, etc.) are hidden for a reason.

---

## 7. The Synthetic File Is NOT Real Data

`data/real/synthetic_fermi_lat_grb_events.csv` was generated programmatically
as a pipeline rehearsal fixture. It uses realistic column formats and
distributions, but contains **no real photon events**. It is excluded from
the real-data workflow by name. Any p-value or z-score computed from it has
no scientific standing.
