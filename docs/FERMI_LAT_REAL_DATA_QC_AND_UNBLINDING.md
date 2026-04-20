# Fermi-LAT Real-Data QC and Unblinding Rules

> **Applies to:** `run_fermi_lat_real_blinded.py` and `fermi_lat_public_ingest.py`  
> **Companion section:** Experiment 1, Phase 5  
> **Status:** ACTIVE — governs the first true public-data analysis  
> **Date:** 2026-04-20

---

## 0. Governing Principle

**No interpretation of signal significance is permitted until all conditions in §3 (Unblinding Gates) are met AND explicit human approval is given.**

The analysis pipeline is designed to compute but not reveal signal statistics until these conditions are satisfied.

---

## 1. Pre-Ingest Quality Gates

These checks run in `fermi_lat_public_ingest.py` before any event data reaches the pipeline.

### 1.1 Minimum Viable Event Count

| Parameter | Threshold | Action if violated |
|---|---|---|
| Total events after all cuts | ≥ 20 | STOP — "insufficient data for analysis" |
| Events per source (GRB) | ≥ 5 | Source dropped from analysis |
| Sources with known redshift | ≥ 3 | STOP — "insufficient redshift coverage" |

### 1.2 Timestamp Consistency

| Check | Rule |
|---|---|
| All arrival times numeric | Non-numeric rows dropped; logged |
| Negative arrival times | Dropped; logged; if > 5% of rows, STOP |
| Time span per source | 0 – 86 400 s (0 – 1 day); warn if > 1 day |
| MJD → seconds conversion | Applied when `time_unit="MJD"` (× 86 400); must be declared before ingest |
| Trigger reference time | Must be subtracted before ingest; adapter computes relative time per source |

### 1.3 Energy-Unit Consistency

| Check | Rule |
|---|---|
| `energy_unit` declared at ingest | Must match actual column values; no guessing |
| Energy range plausibility | Warn if max energy > 1 × 10⁶ GeV (likely MeV/GeV confusion) |
| Energy range plausibility | Warn if min energy < 1 × 10⁻⁶ GeV (likely eV/GeV confusion) |
| Any MeV-scale ingested as GeV | Triggers `ENERGY_IMPLAUSIBLE` stopping rule → STOP |
| Expected LAT range | 0.02 – 500 GeV for reconstructed photons; flag outside this range |

### 1.4 Source Metadata Completeness

| Field | Rule |
|---|---|
| `source_id` | Must be non-empty for every row; rows without source dropped |
| `redshift` | Optional per row but ≥ 3 sources must have redshift |
| `distance_Mpc` | Derived from `redshift` via flat ΛCDM if absent; logged |
| Missing `event_id` | Row accepted with auto-generated ID (`row_N`); logged |

### 1.5 Duplicate Event Handling

| Check | Rule |
|---|---|
| Duplicate `event_id` within one file | Second occurrence dropped; logged |
| Cross-file duplicates | Detected by comparing event IDs across files; duplicates dropped |
| Duplicate fraction | > 0.1% of rows → STOP — "suspiciously high duplicate rate" |

### 1.6 Malformed Row Handling

| Condition | Action |
|---|---|
| Non-parseable energy | Drop row + log |
| Non-parseable time | Drop row + log |
| Missing required column | STOP for the entire file — schema violation |
| Extra unexpected columns | Ignored; logged |
| Row with all-null values | Drop row + log |
| Fraction dropped > 20% | STOP — "excessive data quality issues" |

### 1.7 Outlier Handling

| Check | Rule |
|---|---|
| Energy outlier (> Q3 + 10 × IQR) | Flag for review; NOT dropped automatically |
| Single source dominating (> 80% of events) | Warn; note in manifest |
| All events from single file | Acceptable; note in manifest |

---

## 2. Pre-Analysis QC Gates (run in `run_fermi_lat_real_blinded.py`)

These gates run after ingest and before the pipeline executes.

| Gate | Requirement |
|---|---|
| Registration exists | `fermi_lat_real_analysis_registration.json` must exist and `frozen=True` |
| Ingest manifest exists | Written by `ingest_public_file()`; must be present |
| No stopping rules triggered | `manifest["stopping_rules_triggered"]` must be empty |
| `ingest_complete=True` | Set only when all stopping rules pass |
| Recovery test passes | Synthetic signal injection must recover at p < 0.05 |

---

## 3. Conditions That Block Unblinding

**ALL of the following must be satisfied before any unblinding attempt:**

| # | Condition | Status after Phase 5 prep |
|---|---|---|
| U1 | `frozen=True` in registration JSON | ✅ set at registration |
| U2 | Registration committed to repo before data access | ✅ |
| U3 | Ingest manifest exists for the exact file version analysed | ✅ created by ingest step |
| U4 | No stopping rules triggered in ingest manifest | Depends on real data |
| U5 | QC report `proceed_to_analysis=True` | Depends on real data |
| U6 | Recovery test passed (p < 0.05 for slope = 5e-4) | Depends on real data |
| U7 | All robustness checks completed (jackknife, sign flip, energy threshold) | Not yet run |
| U8 | Explicit human sign-off documented | ❌ not yet |
| U9 | `automatic_unblind=False` verified in run manifest | ✅ enforced by runner |

**Any single failing condition BLOCKS unblinding.**

---

## 4. Explicit Rule: No Interpretation from Partial Ingest

> If any stopping rule was triggered during ingest, or if the ingest manifest is absent, or if `ingest_complete=False`, then **no interpretation of signal results is permitted**, regardless of what p-value was computed internally.

This rule applies even if the runner completed without raising an exception (dry-run mode). A p-value computed on an incomplete ingest is not scientifically meaningful and must not be reported.

---

## 5. Unblinding Procedure

When all gates in §3 are satisfied:

1. Confirm `git log --oneline -1` matches commit used for analysis.
2. Re-run `python reality_audit/data_analysis/register_fermi_lat_real_analysis.py` and verify JSON is byte-identical to the committed version.
3. Run `python reality_audit/data_analysis/run_fermi_lat_real_blinded.py --source <file>` one final time with the same parameters.
4. Document human approval in a new commit (e.g. `docs/UNBLINDING_APPROVAL.md`).
5. Only then run a dedicated unblinding script (to be built in Phase 6) that reads the approval and produces the unblinded summary.

**The blinded runner must never be modified to auto-unblind.**

---

## 6. What Counts as a Discovery vs. Null Result

| Outcome | Condition | Statement |
|---|---|---|
| **Detection** | p < 3 × 10⁻⁷ AND all U1–U9 met | "Significant evidence for LIV-compatible timing delay at 5σ." |
| **Excess** | p < 1.35 × 10⁻³ | "3σ excess; requires follow-up. Not a discovery." |
| **Null** | p > 0.05 | "No significant evidence for LIV; null hypothesis retained." |
| **Exclusion** | Null retained | Derive 95% C.L. upper bound on |slope|; report E_QG lower bound. |

---

## 7. What Does NOT Count as Evidence

- Any p-value from the **local sample dry-run** (synthetic data, 50 events).
- Any result from a run where `ingest_complete=False`.
- Any result from a run where robustness checks have not been completed.
- Any result from an unregistered analysis (registration must predate data access).

---

*Module: `reality_audit/adapters/fermi_lat_public_ingest.py`*  
*Module: `reality_audit/data_analysis/run_fermi_lat_real_blinded.py`*  
*Registration: `commons_sentience_sim/output/reality_audit/fermi_lat_real_analysis_registration.json`*
