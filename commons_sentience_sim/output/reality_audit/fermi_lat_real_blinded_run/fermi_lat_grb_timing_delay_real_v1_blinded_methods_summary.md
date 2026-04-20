# fermi_lat_grb_timing_delay_real_v1 — Methods Summary

**Generated:** 2026-04-20T00:37:09.947952Z
**Blinding status:** blinded

## Results

_Signal result channels are blinded. This summary is safe to share before unblinding._

- **experiment:** fermi_lat_grb_timing_delay_real_v1
- **data_source:** /workspaces/commons-sentience-sandbox/data/real/synthetic_fermi_lat_grb_events.csv
- **n_events:** 104
- **n_sources:** 7
- **has_distance:** True
- **primary_statistic:** timing_slope_s_per_GeV_per_Mpc
- **observed_slope:** `<BLINDED>`
- **null_mean_slope:** 4.0373e-05
- **null_std_slope:** 4.13124e-05
- **p_value:** `<BLINDED>`
- **z_score:** `<BLINDED>`
- **detection_claimed:** `<BLINDED>`
- **null_retained:** `<BLINDED>`
- **n_permutations:** 500
- **recovery_test:**
  - injection_strength: 1.0
  - true_delay_slope: 0.0005
  - observed_slope_with_injection: 0.0005127334411714173
  - p_value: 0.0
  - recovered: True
- **seed:** 42
- **status:** real_data_run
- **metadata:**
  - n_events: 104
  - n_sources: 7
  - n_dropped: 0
  - energy_unit_in: GeV
  - time_unit_in: s
  - has_distance: True
  - source_file: /workspaces/commons-sentience-sandbox/data/real/synthetic_fermi_lat_grb_events.csv
  - schema_version: 1.0
- **_blinding_status:** blinded
- **_blind_keys:** ['p_value', 'z_score', 'detection_claimed', 'null_retained', 'observed_slope']

## Reproducibility

_Reproducibility metadata not present in this result dict._
