# Fermi-LAT 2FLGC official photon timing audit — 2026-09-11

## Decision

**NO PROMOTION.** The frozen primary statistic is consistent with its within-GRB permutation null: two-sided plus-one p = **0.5350946491** from 100,000 null catalogs (seed 20260911).

This is not a Eureka result and is not evidence for simulation ontology or Lorentz-invariance violation.

## What changed

- Replaced the rejected repository CSV with the official NASA HEASARC `FERMILGRB` catalog and official FSSC LAT event/spacecraft queries.
- Froze `configs/fermi_2flgc_photon_timing_v2.json` before inspecting selected-event counts or the candidate statistic.
- Added a deterministic analysis runner and tests.
- Preserved all official inputs, query identifiers embedded in filenames, SHA-256 checksums, cuts, seed, null count, and result.

## Provenance and baseline reproduction

Official catalog page: <https://heasarc.gsfc.nasa.gov/W3Browse/fermi/fermilgrb.html>

Catalog paper DOI: <https://doi.org/10.3847/1538-4357/ab1d4e>

HEASARC states that the table was obtained from the Fermi Science Support Center. The downloaded 2022 table has 231 rows because it appends later bursts. Applying the paper's exclusive end date of 2018-08-04 reproduces:

- 186 original-sample GRBs;
- 91 LLE detections;
- 169 LAT detections using positive `su_tsinput`.

The machine-readable table SHA-256 is `f91432de85ff5fb54fe0e12b890bdcb05d6e2bbe5b5bd5e4317eb67885c303c6`. The FITS table SHA-256 is `a7ea4db3623d828ea7f2c7f180c3780c19412a483ddfd69523831af50a80e536`.

## Frozen primary analysis

- Targets: GRB 080916C, 090510, 090902B, 130427A, 160509A.
- Acquisition: FSSC Extended event class, trigger ±600 s, 100 MeV–300 GeV, 12° query radius, matching spacecraft files.
- Primary selection: trigger +0 to +100 s, energy ≥1 GeV, angular separation ≤1°, zenith ≤100°.
- Statistic: pooled correlation of within-GRB-centered time ranks and log-energy ranks.
- Null: permute energy within each GRB, 100,000 catalogs, seed 20260911.
- Trial policy: one primary test. Alternative windows/apertures are diagnostic and require joint maximum-statistic calibration.

Four GRBs passed the frozen minimum of five selected events. The selected counts were 13, 30, 50, 39, and 2 respectively; the last source was excluded by the frozen rule. Total included events: 132.

Observed statistic: `0.0614104150`. Null exceedances: 53,509. Plus-one p: `0.5350946491`.

## Scientific limitation

The tight high-energy aperture and within-source permutation suppress obvious sky-exposure and source-to-source time-profile confounding, but this is not a full likelihood reproduction of the 2FLGC `gtsrcprob` association machinery. The official event and spacecraft products are preserved so a later run can add Fermitools IRFs, exposure, background models, injection recovery, and jointly calibrated systematic scans. The current null result does not justify that expensive work as an anomaly follow-up.

## Exact artifacts

- Frozen config: `configs/fermi_2flgc_photon_timing_v2.json`
- Runner: `scripts/run_fermi_2flgc_timing_v2.py`
- Result: `outputs/fermi_2flgc/fermi_2flgc_timing_v2_100k.json`
- Official catalog and query products: `data/real/fermi_2flgc_official/`
- Tests: `tests/test_fermi_2flgc_timing_v2.py`

Highest-value next action: add the official Fermitools response/likelihood layer as a product adapter and use this preserved null result as a signed negative-evidence bundle, not as an anomaly candidate.
