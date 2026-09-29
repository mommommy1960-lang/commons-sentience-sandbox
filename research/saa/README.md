# Commons Open SAA: first independent comparison gate

Status: **crossing-map exploratory result; no radiation protection or product-superiority claim**. This is a research harness, not satellite flight software.

## What was actually checked (2026-09-29)

- NASA Fermi LAT weekly spacecraft FITS files `w899` and `w900` were downloaded from the [official HEASARC archive](https://heasarc.gsfc.nasa.gov/FTP/fermi/data/lat/weekly/spacecraft/). An older `w100` file was checked as well.
- The [`IN_SAA` column is documented by FSSC](https://fermi.gsfc.nasa.gov/ssc/data/access/lat/lat_data_columns.html) as a crossing flag. It was **false in all 17,305 intervals in w899, all 17,103 in w900, and all 17,033 in w100**. Thus those weekly files cannot supply positive examples for a crossing detection benchmark. Do not infer that Fermi never traversed the anomaly.
- `fermi_crossing_replay.py` rejects those LAT files instead of generating undefined scores.
- The [NASA Fermi GBM daily archive](https://heasarc.gsfc.nasa.gov/FTP/fermi/data/gbm/daily/) has usable position histories. The [GBM data tools](https://astro-gdt.readthedocs.io/projects/astro-gdt-fermi/en/latest/_modules/gdt/missions/fermi/gbm/poshist.html) specify `FLAGS & 0x02` as an operational SAA state. Files `glg_poshist_all_250101_v00.fit`, `...250102_v00.fit`, and `...250103_v00.fit` supplied the real crossing labels. Each was sampled every 30 seconds. Previous-day labels fit a simple fixed-circle radius and a 31-neighbor geographic map; both were tested on the following day after midnight overlap was discarded.
- The [NASA ACROSS public Fermi page](https://app.across.sciencecloud.nasa.gov/observatories/Fermi) provides another polygon snapshot. It was retrieved in September 2026 and may **not** be the operational contour used to set the January 2025 flags. It is an illustrative published comparator, not a fair head-to-head test against NASA's contemporaneous flight system.
- **2025 Jan 1 → Jan 2** (2,884 evaluation rows, 370 positive): circle 318 true positives / 52 misses / 87 false alerts; public polygon snapshot 370 / 0 / 53; previous-day map 369 / 1 / 7.
- **2025 Jan 2 → Jan 3** (2,885 evaluation rows, 365 positive): circle 315 / 50 / 91; public polygon snapshot 364 / 1 / 61; previous-day map 361 / 4 / 10.
- These figures show that a learned geographic map follows the *GBM operational boundary* better than a crude circle on these days. The published polygon snapshot caught slightly more crossings, and the learned map issued fewer false alerts. The comparison does **not** show more accurate radiation hazard prediction or a superior product. A boundary trained on one day's own SAA operational flags is especially close to the outcome it is asked to reproduce.
- `saa_benchmark.py` compares **predeclared** alerts against independently observed hazardous intervals. The test verifies arithmetic. No mission telemetry with both advance predictions and independent radiation/error outcomes has been supplied, so there is no head-to-head result yet.

## Claim gate

1. Obtain an independent particle-flux or instrument-upset series with positives and negatives, orbit positions, and data provenance. Confirm definitions and coverage with its data provider.
2. For an operational-benefit test, obtain independent time-tagged dose or instrument upset events. An `IN_SAA` map is not a substitute for those outcomes.
3. Freeze one existing method, one Commons candidate, threshold, lead time, and time interval before examining evaluation labels. Train on earlier periods and evaluate later periods, and repeat across another mission if possible.
4. Report recall, false-alarm rate, precision, actual lead time, runtime, and any scheduled observation time lost. Describe the data gaps. Never use test-time position as a claimed advance prediction.
5. Require independent mission-operations review before deploying alerts or selling a safety claim. Until then, market only the research prototype and its limitations.

From this directory, run `python -m unittest -v test_saa_benchmark.py`. To reproduce the GBM exploratory replay, install `numpy astropy scikit-learn matplotlib`, download the three exact GBM FITS files from the daily archive under `2025/01/{01,02,03}/current/`, and run `python fermi_crossing_replay.py glg_poshist_all_250101_v00.fit glg_poshist_all_250102_v00.fit` and likewise Jan 2 → Jan 3. Do not commit the FITS files. When a genuine independent hazard CSV is available, run `python saa_benchmark.py intervals.csv`; its header and semantics are specified in the script docstring.
