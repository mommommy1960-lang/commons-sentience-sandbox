# Stage 6 — First Blinded Real Fermi-LAT GRB Timing-Delay Analysis

## Purpose

This stage executes the first true public-data analysis run for Experiment 1
of the Reality Audit project. The objective is to ingest a real Fermi-LAT GRB
event dataset, validate it through mandatory QC gates, and execute the blinded
timing-delay analysis — producing allowed artifacts while completely suppressing
all protected inference outputs.

No scientific claim may be made before unblinding approval has been granted and
all 9 unblinding conditions (documented in
[FERMI_LAT_REAL_DATA_QC_AND_UNBLINDING.md](FERMI_LAT_REAL_DATA_QC_AND_UNBLINDING.md))
have been verified in sequence.

---

## Prerequisites

| Requirement | Status |
|---|---|
| Analysis pre-registered and `frozen: true` | ✅ `fermi_lat_real_analysis_registration.json` |
| Adapter hardened for real-file column aliases | ✅ |
| Blinded runner enforces `automatic_unblind=False` | ✅ |
| All 9 QC unblinding conditions documented | ✅ |
| 967 existing tests passing | ✅ |
| Real CSV placed in `data/real/` (not named `synthetic*`) | Required before run |

---

## Required Input Schema

| Column | Required | Accepted Aliases |
|---|---|---|
| `event_id` | ✅ | `id`, `row_id`, `index` |
| `grb_name` | ✅ | `source_id`, `source`, `grb_id`, `name`, `burst` |
| `energy_gev` | ✅ | `energy`, `photon_energy`, `energy_mev`, `e_gev` |
| `time_s` | ✅ | `photon_arrival_time_s`, `arrival_time_s`, `arrival_time`, `time`, `t`, `t_s` |
| `redshift` | ✅ | `z`, `z_spec`, `z_photo` |
| `grb_t90_s` | ✅ | `t90`, `t90_s` |

Energies may be in MeV (column `energy_mev`) — the adapter converts to GeV.

---

## QC Gates Enforced

All gates are evaluated before analysis begins. Any hard failure aborts the run.

| Gate | Threshold | Failure type |
|---|---|---|
| Minimum total events | ≥ 30 | Hard — REJECT |
| Minimum sources with redshift | ≥ 5 | Hard — REJECT |
| Duplicate event-ID fraction | < 0.1% | Hard — REJECT |
| Missing required columns | 0 missing | Hard — REJECT |
| Energy plausibility | 0.01–1000 GeV | Soft — ACCEPT_WITH_WARNINGS |
| Schema type validity | All fields parseable | Hard — REJECT |
| Stopping rules (from registration) | None triggered | Hard — BLOCKED |

---

## Blinding Rules Enforced

- `automatic_unblind = False` is hardcoded in `run_fermi_lat_real_blinded.py`
- The following keys are replaced with the string `"BLINDED"` in all written files:
  - `observed_slope`
  - `p_value`
  - `z_score`
  - `detection_claimed`
  - `null_retained`
- `unblind_permitted = False` is written to every output file
- Unblinding requires ALL 9 conditions in `FERMI_LAT_REAL_DATA_QC_AND_UNBLINDING.md`

---

## Command to Run

```bash
python -m reality_audit.data_analysis.first_blinded_real_fermi_run
```

Optional overrides:

```bash
python -m reality_audit.data_analysis.first_blinded_real_fermi_run \
  --data-dir data/real/ \
  --registration commons_sentience_sim/output/reality_audit/fermi_lat_real_analysis_registration.json \
  --n-permutations 500 \
  --seed 42
```

The command will:
1. Scan `data/real/` for non-synthetic CSV files
2. Run pre-ingest package check — abort if not `ACCEPT_FOR_BLINDED_RUN`
3. Execute blinded timing-delay pipeline
4. Generate milestone completion report
5. Print allowed summary; never print protected values

---

## Generated Artifacts

```
commons_sentience_sim/output/reality_audit/
├── first_real_ingest_manifest.json          ← run status + provenance
├── fermi_lat_real_package_check.json        ← pre-ingest validation
├── milestone_completion_report.json         ← Stage 6 formal report
└── fermi_lat_real_blinded_run/
    ├── quality_control_report.json          ← QC gate results
    ├── blinded_summary.json                 ← analysis summary (signal BLINDED)
    ├── run_manifest.json                    ← pipeline provenance
    └── fermi_lat_public_ingest_manifest.json ← ingest metadata
```

All output files contain `"BLINDED"` for any signal key. None contain slope,
p-value, z-score, detection label, or any equivalent inference metric.

---

## Milestone Completion Report Fields

The milestone report (`milestone_completion_report.json`) contains:

| Field | Description |
|---|---|
| `milestone` | Stage identifier |
| `unblinding_status` | Always `"UNBLINDING NOT PERFORMED"` |
| `scientific_claim_status` | Explicit prohibition statement |
| `run_timestamp` | ISO 8601 UTC |
| `commit_hash` | Git short hash |
| `pipeline_status` | WAITING / BLOCKED / COMPLETE / ERROR |
| `dataset.dataset_name` | Source file name |
| `dataset.source_path` | Full path |
| `dataset.pre_ingest_check` | Schema validity + recommendation |
| `ingestion.n_events` | Total events ingested |
| `ingestion.n_dropped` | Dropped events |
| `ingestion.n_sources` | Total GRB sources |
| `ingestion.n_sources_with_redshift` | Sources with valid redshift |
| `ingestion.drop_reasons` | List of drop reasons |
| `qc_gates.*` | All QC gate outcomes |
| `blinding.blinding_enforced` | True |
| `blinding.signal_keys_confirmed_blinded` | True — verified at report generation time |
| `blinding.unblind_permitted` | False |
| `artifact_paths.*` | Paths to all output files |

---

## Explicit Statement

**No scientific claim is permitted before unblinding approval has been explicitly
granted by a human reviewer following verification of all 9 conditions in
[docs/FERMI_LAT_REAL_DATA_QC_AND_UNBLINDING.md](FERMI_LAT_REAL_DATA_QC_AND_UNBLINDING.md).**

The blinded summary file is not a result. The null-model statistics visible in
the blinded output are not the result. Any intermediate value produced by this
pipeline before unblinding carries no scientific weight.

---

## What This Stage Does NOT Do

- ❌ Does not expose slope, p-value, z-score, or detection status
- ❌ Does not perform unblinding
- ❌ Does not make a discovery or null-result claim
- ❌ Does not alter the pre-registered analysis plan
- ❌ Does not modify QC gate thresholds retroactively
- ❌ Does not treat synthetic or rehearsal data as real data

---

## Related Files

| File | Purpose |
|---|---|
| [HOW_TO_RUN_FIRST_REAL_INGEST.md](HOW_TO_RUN_FIRST_REAL_INGEST.md) | Step-by-step operator guide |
| [FERMI_LAT_REAL_DATA_QC_AND_UNBLINDING.md](FERMI_LAT_REAL_DATA_QC_AND_UNBLINDING.md) | 9 unblinding conditions |
| [FERMI_LAT_PUBLIC_DATA_PLAN.md](FERMI_LAT_PUBLIC_DATA_PLAN.md) | Full analysis plan |
| `data/real/README.md` | Dropzone requirements |
