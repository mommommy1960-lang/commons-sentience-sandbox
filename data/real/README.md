# data/real/ — Real Public-Data Dropzone

Place real Fermi-LAT GRB event CSV files here before running the blinded
analysis pipeline.

---

## Required Columns

| Column | Accepted Aliases | Description |
|---|---|---|
| `event_id` | `id`, `row_id`, `index` | Unique identifier per photon event |
| `grb_name` | `source_id`, `source`, `grb_id`, `name`, `burst` | GRB source name (e.g. `GRB090902B`) |
| `energy_gev` | `energy`, `photon_energy`, `energy_mev`, `e_gev` | Photon energy in GeV (or MeV — unit auto-detected) |
| `time_s` | `photon_arrival_time_s`, `arrival_time_s`, `time`, `t`, `t_s` | Arrival time in seconds since trigger |
| `redshift` | `z`, `z_spec`, `z_photo` | Source redshift |
| `grb_t90_s` | `t90`, `t90_s` | GRB T90 duration in seconds |

---

## Minimum Acceptance Requirements

- ≥ 30 total events
- ≥ 5 GRBs with valid (non-null, non-negative) redshift
- Duplicate fraction < 0.1% (`duplicate_ids / total_events`)
- Energies plausible (0.01–1000 GeV after unit conversion)
- No malformed rows (schema errors block ingest)

---

## Validation Before Running

Run the pre-ingest package check first:

```bash
python reality_audit/data_analysis/check_fermi_lat_real_package.py \
  --input data/real/<your_file>.csv
```

This writes a JSON report to:
`commons_sentience_sim/output/reality_audit/fermi_lat_real_package_check.json`

Recommendation values:
- `ACCEPT_FOR_BLINDED_RUN` — all gates pass, proceed
- `ACCEPT_WITH_WARNINGS` — soft issues present, review before proceeding
- `REJECT` — hard stopping rule violated, do not proceed

---

## Running the Blinded Pipeline

After package check returns `ACCEPT_FOR_BLINDED_RUN`:

```bash
python reality_audit/data_analysis/run_fermi_lat_real_blinded.py \
  --source data/real/<your_file>.csv \
  --registration commons_sentience_sim/output/reality_audit/fermi_lat_real_analysis_registration.json
```

---

## ⚠️ Critical Warnings

- **DO NOT unblind automatically.** The pipeline enforces `automatic_unblind=False`.
  Unblinding requires explicit human approval after all 9 QC gates pass.
  See [docs/FERMI_LAT_REAL_DATA_QC_AND_UNBLINDING.md](../../docs/FERMI_LAT_REAL_DATA_QC_AND_UNBLINDING.md).

- **DO NOT interpret results prematurely.** A blinded summary file will be written
  with signal keys replaced by `"BLINDED"`. Do not attempt to infer the result
  from null-model statistics alone.

- **DO NOT treat the synthetic file as real data.** `synthetic_fermi_lat_grb_events.csv`
  is a pipeline rehearsal fixture and must not be used as a scientific input.

---

## Current Contents

| File | Type | Status |
|---|---|---|
| `synthetic_fermi_lat_grb_events.csv` | Synthetic rehearsal fixture | Pipeline validation only — NOT real data |

Real data files will appear here once downloaded from a public Fermi-LAT archive
(e.g. Fermi FSSC, HEASARC). No real data has been ingested yet.
