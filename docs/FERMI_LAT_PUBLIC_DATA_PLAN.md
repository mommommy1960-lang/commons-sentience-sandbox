# Fermi-LAT Public-Data Analysis Plan
## Experiment 1 — First Real Public-Dataset Analysis Target

> **Date drafted:** 2026-04-19  
> **Status:** PLANNING — no real public data ingested yet  
> **Companion-book experiment:** Year 2, Experiment 1 (data-analysis-only program)  
> **Responsible:** commons-sentience-sandbox project  
> **Review required before data access:** Yes

---

## 1. Why Fermi-LAT GRB Timing-Delay Is the First Target

The Fermi Large Area Telescope (LAT) has published high-quality, openly accessible catalogs of gamma-ray burst (GRB) photon events including reconstructed energies, arrival times, and host-galaxy redshifts. GRB timing-delay analysis is the field's most-cited test for Lorentz-Invariance Violation (LIV) via quantum-gravity energy-dependent photon speed corrections.

**Reasons for choosing this target:**

| Criterion | Assessment |
|---|---|
| Public availability | ✅ Fermi Science Support Center (FSSC) hosts all event data freely |
| Community-validated | ✅ Dozens of published analyses using identical method exist (Abdo+09, Vasileiou+13, Ellis+19) |
| Infrastructure alignment | ✅ Our adapter (`fermi_lat_grb_adapter.py`) already parses the required columns |
| Null model established | ✅ Permutation test on energy-shuffle is standard in field |
| Falsifiability | ✅ Discovery threshold and exclusion threshold are pre-definable |
| Not requiring hardware | ✅ Pure data analysis — Year 2 milestone |
| Manageable scale | ✅ ~10–100 events per GRB in LAT catalog; no HPC required |

No hardware is required. The analysis targets the linear LIV dispersion relation:
$$\Delta t_{\rm LIV} = \frac{1+n}{2H_0} \cdot \frac{E^n}{E_{\rm QG,n}^n} \cdot \int_0^z \frac{(1+z')^n \, dz'}{h(z')}$$
where $n=1$ (linear, leading-order) is tested first.

---

## 2. Specific Public Data Products Required

| Product | Source | Notes |
|---|---|---|
| LAT High-Energy (HE) GRB photon event files | Fermi FSSC (https://fermi.gsfc.nasa.gov/ssc/) | FITS format; event-level photon data |
| 2FLGC — Second Fermi-LAT GRB Catalog | Published table (Ajello+19) | Redshifts, fluences, spectral indices for ~186 GRBs |
| 1FLGC event tables | Abdo+09 supplementary | 8-year extension available online |
| GBM trigger times | Fermi-GBM Burst Catalog | Required to compute trigger-relative arrival times |

**Minimum required GRBs:** ≥5 with confirmed spectroscopic redshift.  
**Recommended starting set:** GRB080916C, GRB090902B, GRB090510, GRB130427A, GRB160509A (same GRBs as sample dataset; well-studied, all have published redshifts).

---

## 3. Fields That Must Be Present Per Event

| Field | Column name(s) in LAT files | Required? | Notes |
|---|---|---|---|
| Photon energy | `ENERGY` (MeV in LAT FITS) | ✅ | Convert MeV → GeV in adapter |
| Arrival time | `TIME` (MET seconds) | ✅ | Convert to trigger-relative seconds using GBM T0 |
| Source identifier | From filename or OBJECT keyword | ✅ | |
| Event class / event type | `EVENT_CLASS`, `EVENT_TYPE` | recommended | Use `SOURCE` class (evclass=128) minimum |
| Redshift | From 2FLGC/1FLGC cross-match | ✅ | Required for distance model |
| Reconstructed direction | `RA`, `DEC` | optional | Useful for position-dependent systematics |
| Zenith angle | `ZENITH_ANGLE` | optional | Cut at <100° to avoid Earth limb contamination |

---

## 4. Required Preprocessing

1. **Download event FITS files** for target GRBs from FSSC (read-only; P01).
2. **Apply standard LAT quality cuts:**
   - `DATA_QUAL > 0`
   - `LAT_CONFIG == 1`
   - `ZENITH_ANGLE < 100` degrees (Earth-limb cut)
   - `EVENT_CLASS == 128` (Source class) or stricter (Clean: 256)
3. **Compute trigger-relative time:**
   - Subtract GBM trigger time (T0) from LAT `TIME` column.
   - Result in seconds.
4. **Apply energy selection:**
   - Lower bound: 0.1 GeV (LAT trigger threshold for H.E. catalog)
   - Upper bound: no hard cut; flag events > 100 GeV for review
5. **Cross-match redshifts:**
   - Link each GRB to its spectroscopic redshift from 2FLGC / published value.
   - Flag GRBs with photometric-only z.
6. **Compute luminosity distance:**
   - Flat ΛCDM with H₀ = 67.4 km/s/Mpc (Planck 2018), ΩM = 0.315.
   - For exact computation: use numerical integration (upgrade from current approximation for z > 2).
7. **Inspect for pile-up and background:**
   - Visual light-curve check per GRB.
   - Flag if >50% of photons arrive in a single 0.1 s bin.
8. **Remove non-GRB photons:**
   - Select a time window around the burst (e.g. T0 − 10 s to T0 + 1000 s per GRB).

---

## 5. Null Model

**Null hypothesis (H₀):** Photon arrival time offsets are uncorrelated with photon energy at any distance.

**Null model implementation (already in repo):**
- Permutation of photon energies within each source, preserving the marginal energy distribution.
- 500 permutations minimum; 2000 for publication.
- Null statistic: OLS slope of `timing_offset_s ~ energy_GeV × distance_Mpc`.
- Null distribution: slope values from energy-permuted trials.
- Module: `reality_audit/data_analysis/mock_timing_pipeline.py` (`_permutation_null_distribution`)

**Why permutation (not parametric):**
- No assumption on energy spectrum shape required.
- Standard for Fermi-LAT LIV analyses (see Ellis+19, Chang+12).

---

## 6. Injected Signal Model

**Signal hypothesis (H₁, linear LIV):** leading-order ($n=1$) subluminal correction:
$$\Delta t = s \cdot \frac{E}{E_{\rm QG,1}} \cdot \frac{D_H}{c}$$
where $D_H = D_L / (1+z)^2$ (comoving distance), $E_{\rm QG,1}$ is the quantum-gravity energy scale.

**Implemented as slope injection in `signal_injection.py`:**
- `timing_delay_linear`: adds $s \times E \times D$ offset, slope $s$ in s/(GeV·Mpc).
- Current recovery test uses $s = 5\times10^{-4}$ s/(GeV·Mpc).
- Discovery-level injection: scale $s$ to produce exactly $p = 10^{-6}$ on expected sample.

**Conservative exclusion target:**
$$E_{\rm QG,1} > 10 \, E_{\rm Planck} \approx 1.22 \times 10^{20} \, \text{GeV}$$
for a detection with the chosen GRB sample — consistent with published Fermi constraints.

---

## 7. Blinding Policy

| Stage | Action |
|---|---|
| Analysis plan sign-off | Freeze plan in `experiment_registry.py` BEFORE loading real data |
| Data loading | `freeze_immediately=False` — blinding active from first data touch |
| Null-model tuning | Allowed using injection on synthetic data only |
| Real-data unblinding | Only after all checks pass (see §9); `freeze_immediately=True` |
| Post-unblind modifications | Not permitted — any change requires re-registration and re-blinding |

**Blinding module:** `reality_audit/data_analysis/blinding.py`  
**Experiment registry:** `reality_audit/data_analysis/experiment_registry.py`

---

## 8. Discovery and Exclusion Thresholds

| Threshold | Value | Rationale |
|---|---|---|
| Detection claim | $p < 3 \times 10^{-7}$ ($5\sigma$) | Standard physics discovery threshold |
| Interesting excess | $p < 1.35 \times 10^{-3}$ ($3\sigma$) | Report without claiming discovery |
| Null retained (exclusion) | $p > 0.05$ | Claim null consistent |
| Exclusion limit | 95% C.L. upper bound on slope $s$ | Report as $E_{\rm QG,1}$ lower bound |

**No look-elsewhere effect correction applied** for single-parameter linear LIV search.  
Document if multiple signal models are tested (subluminal + superluminal both).

---

## 9. Systematics and Failure Modes

| Systematic | Check required | Mitigation |
|---|---|---|
| Intrinsic GRB spectral evolution | Energy–time correlation in source frame | Apply time-of-emission correction; use leading-edge only |
| Redshift uncertainty | Photometric z > spectroscopic z | Flag and exclude photometric-only sources |
| LAT point spread function energy dependence | Higher-E photons better localized | PSF cut; check PSF model version |
| Background photon contamination | Non-GRB events in time window | Use shorter time windows; check background estimate |
| Pile-up at burst onset | High count rate → dropped events | Check pile-up fraction; flag bursts with >50% rate loss |
| Distance model approximation | Flat ΛCDM approx for z > 2 | Upgrade to numerical integration for z > 1.5 |
| Multiple energy bins | Testing multiple sub-bands → trial factor | Pre-specify energy ranges before unblinding |
| Small-sample statistics | N < 30 total events → non-Gaussian | Bootstrap CI in addition to permutation p-value |

---

## 10. Dry Run vs. Real Analysis

| Criterion | Dry run | Real analysis |
|---|---|---|
| Data source | Synthetic sample CSV or simulated events | Real Fermi-LAT FITS files from FSSC |
| Blinding | `freeze_immediately=True` acceptable | `freeze_immediately=False` required |
| Claimed results | None — infrastructure validation only | Only after 5σ or explicit exclusion |
| Reporting | `_dry_run_` prefix in output directory | `_real_` prefix in output directory |
| Registry entry | Optional | Mandatory before first data load |
| Code frozen | Not required | Required; commit hash recorded |

**Current state (2026-04-20):** Local dry-run complete. Registration and blinded ingest workflow implemented. Real FITS ingestion not yet started.

---

## 11. Phase 5 Transition: Local Dry-Run → Real-Data Ingest

> **Updated 2026-04-20 — Phase 5 preparation complete**

### 11.1 Transition Checklist

| Step | Status |
|---|---|
| Local sample dry-run complete | ✅ committed `3457f42` |
| Analysis registration frozen | ✅ `fermi_lat_real_analysis_registration.json` committed |
| Blinded ingest workflow built and tested | ✅ `run_fermi_lat_real_blinded.py` + 24 tests |
| QC/unblinding rules documented | ✅ `docs/FERMI_LAT_REAL_DATA_QC_AND_UNBLINDING.md` |
| Real public file downloaded | ❌ NOT YET |
| Pipeline run on real data | ❌ NOT YET |
| Unblinding approved | ❌ NOT YET |

### 11.2 Minimum Viable File Package

Before running the blinded analysis, the following files must be present locally:

```
data/real/
  <GRB_NAME>_events.csv   (or .json / .fits.csv)
  for each GRB in: GRB080916C, GRB090902B, GRB090510, GRB130427A, GRB160509A
  OR any ≥ 3 GRBs with known spectroscopic redshift
```

Required columns (any naming convention; adapter auto-maps or use `column_map`):
- `event_id`, `source_id`, `photon_energy`, `arrival_time`, `redshift`

Minimum: 20 events total across ≥ 3 GRBs with redshift.

### 11.3 Exact Blinding Sequence

```
Step A: python reality_audit/data_analysis/register_fermi_lat_real_analysis.py
        → writes fermi_lat_real_analysis_registration.json
        → COMMIT this file before touching any real data

Step B: [Download real Fermi-LAT event file(s) to data/real/]

Step C: python reality_audit/data_analysis/run_fermi_lat_real_blinded.py \
            --source data/real/grb_events.csv \
            --registration commons_sentience_sim/output/reality_audit/fermi_lat_real_analysis_registration.json \
            --output commons_sentience_sim/output/reality_audit/fermi_lat_real_blinded_run/
        → writes blinded_summary.json (signal keys = "BLINDED")
        → writes quality_control_report.json
        → writes run_manifest.json
        → does NOT unblind automatically

Step D: Review quality_control_report.json
        → Verify all QC gates in FERMI_LAT_REAL_DATA_QC_AND_UNBLINDING.md §3 pass

Step E: [Human sign-off documented in docs/UNBLINDING_APPROVAL.md]

Step F: [Run dedicated unblinding script — to be built in Phase 6]
```

### 11.4 Stopping Rules if Ingest Is Insufficient

| Condition | Runner behaviour |
|---|---|
| File not found | `FileNotFoundError` immediately |
| Registration not found | `BlindedRunError` immediately |
| Fewer than 20 events after QC | `blinded_summary["status"] = "BLOCKED"` |
| Fewer than 3 sources with redshift | `blinded_summary["status"] = "BLOCKED"` |
| Drop rate > 20% | `blinded_summary["status"] = "BLOCKED"` |
| Energy unit implausible | Stopping rule triggered; BLOCKED |

In all blocked cases: `run_ok=False`, `analysis_ran=False`, no signal values written.

### 11.5 Conditions Required Before Unblinding

See full checklist in [docs/FERMI_LAT_REAL_DATA_QC_AND_UNBLINDING.md](FERMI_LAT_REAL_DATA_QC_AND_UNBLINDING.md) §3.

Summary: all 9 unblinding gates (U1–U9) must pass AND explicit human approval must be documented before any signal statistics are examined.

---

## Appendix: Useful References

- Abdo et al. (2009) — *"A limit on the variation of the speed of light arising from quantum gravity effects"*, Nature 462, 331. DOI: 10.1038/nature08574
- Vasileiou et al. (2013) — *"Constraints on Lorentz invariance violation from Fermi-LAT observations of gamma-ray bursts"*, Phys. Rev. D 87, 122001.
- Ellis & Mavromatos (2013) — Review of LIV tests with GRBs.
- Fermi FSSC: https://fermi.gsfc.nasa.gov/ssc/data/access/
- 2FLGC: Ajello et al. (2019), ApJS 245, 17.
