# Commons Open SAA: first independent comparison gate

Status: **no performance claim**. This is a research harness, not satellite flight software.

## What was actually checked (2026-09-29)

- NASA Fermi LAT weekly spacecraft FITS files `w899` and `w900` were downloaded from the [official HEASARC archive](https://heasarc.gsfc.nasa.gov/FTP/fermi/data/lat/weekly/spacecraft/). An older `w100` file was checked as well.
- The [`IN_SAA` column is documented by FSSC](https://fermi.gsfc.nasa.gov/ssc/data/access/lat/lat_data_columns.html) as a crossing flag. It was **false in all 17,305 intervals in w899, all 17,103 in w900, and all 17,033 in w100**. Thus those weekly files cannot supply positive examples for a crossing detection benchmark. Do not infer that Fermi never traversed the anomaly.
- `fermi_crossing_replay.py` now rejects this input instead of generating undefined scores. It contains a fixed-circle baseline and a prior-week geographic map for when a usable, documented event label is available. It estimates crossing classification only; it is not a 0–6 hour forecast and says nothing about dose or satellite failures.
- `saa_benchmark.py` compares **predeclared** alerts against independently observed hazardous intervals. The test verifies arithmetic. No mission telemetry with both advance predictions and independent radiation/error outcomes has been supplied, so there is no head-to-head result yet.

## Claim gate

1. Obtain an official time-tagged SAA crossing or particle-flux series with positives and negatives, orbit positions, and data provenance. Confirm definitions and coverage with its data provider.
2. For an operational-benefit test, obtain independent time-tagged dose or instrument upset events. An `IN_SAA` map is not a substitute for those outcomes.
3. Freeze one existing method, one Commons candidate, threshold, lead time, and time interval before examining evaluation labels. Train on earlier periods and evaluate later periods, and repeat across another mission if possible.
4. Report recall, false-alarm rate, precision, actual lead time, runtime, and any scheduled observation time lost. Describe the data gaps. Never use test-time position as a claimed advance prediction.
5. Require independent mission-operations review before deploying alerts or selling a safety claim. Until then, market only the research prototype and its limitations.

From this directory, run `python -m unittest -v test_saa_benchmark.py`. When a genuine labeled CSV is available, run `python saa_benchmark.py intervals.csv`; its header and semantics are specified in the script docstring.
