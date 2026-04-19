# dry_run_fermi_lat — Methods Summary

**Generated:** 2026-04-19T23:38:37.225741Z
**Blinding status:** blinded

## Results

_Signal result channels are blinded. This summary is safe to share before unblinding._

- **experiment:** dry_run_fermi_lat
- **data_source:** /tmp/dry_run_grb.csv
- **n_events:** 75
- **n_sources:** 5
- **has_distance:** True
- **primary_statistic:** timing_slope_s_per_GeV_per_Mpc
- **observed_slope:** `<BLINDED>`
- **null_mean_slope:** 2.74352e-05
- **null_std_slope:** 4.35721e-05
- **p_value:** `<BLINDED>`
- **z_score:** `<BLINDED>`
- **detection_claimed:** `<BLINDED>`
- **null_retained:** `<BLINDED>`
- **n_permutations:** 500
- **recovery_test:**
  - injection_strength: 1.0
  - true_delay_slope: 0.0005
  - observed_slope_with_injection: 0.0005510132540898641
  - p_value: 0.0
  - recovered: True
- **seed:** 42
- **status:** real_data_run
- **metadata:**
  - n_events: 75
  - n_sources: 5
  - n_dropped: 0
  - energy_unit_in: GeV
  - time_unit_in: s
  - has_distance: True
  - source_file: /tmp/dry_run_grb.csv
  - schema_version: 1.0
- **_blinding_status:** blinded
- **_blind_keys:** ['p_value', 'z_score', 'detection_claimed', 'null_retained', 'observed_slope']

## Reproducibility

_Reproducibility metadata not present in this result dict._
