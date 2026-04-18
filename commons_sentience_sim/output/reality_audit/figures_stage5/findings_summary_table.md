# Stage 5 Findings Summary

| ID | Trust | A/C | Key Metrics | Finding (truncated) |
|---|---|---|---|---|
| F01_passive_probe_readonly | strong | absolute | audit_bandwidth, path_smoothness, avg_control_effort | The passive probe is read-only: path-history, total_records, goal_room, and probe_mode fields are exactly equal across r... |
| F02_path_smoothness_encoding_robust | strong | absolute | path_smoothness | path_smoothness is robust to position-encoding strategy: spread across BFS+MDS, pure-hop, and manual-topological encodin... |
| F03_position_metrics_encoding_sensitive | strong | comparative | mean_position_error, stability_score, anisotropy_score | mean_position_error, stability_score, and anisotropy_score are encoding-sensitive: raw values differ by 37–100% across t... |
| F04_no_false_positives_in_sandbox | strong | absolute | mean_position_error, stability_score, avg_control_effort, observer_dependence_score | No false positive detections were observed in sandbox conditions.  Both minimal-policy (cooperation=0.1, trust=0.2) and ... |
| F06_observer_dependence_score_unreliable | strong | absolute | observer_dependence_score | observer_dependence_score is unreliable as a standalone anomaly signal.  In passive sandbox mode it is always 0 by const... |
| F08_audit_bandwidth_probe_config_readout | strong | absolute | audit_bandwidth | audit_bandwidth = 1.0 in all passive runs and < 1.0 in active_measurement runs.  This confirms the probe schedule is con... |
| F09_convergence_turn_null_in_sandbox | strong | absolute | convergence_turn | convergence_turn is null in virtually all sandbox runs.  The threshold (position_error ≤ 0.05) is rarely reached in the ... |
| F05_governance_shifts_control_effort | moderate | comparative | avg_control_effort | Governance state affects avg_control_effort: governance-off runs show lower blocking rates than governance-on runs when ... |
| F07_metrics_deterministic_stable_short_runs | moderate | absolute | mean_position_error, stability_score, avg_control_effort, path_smoothness, observer_dependence_score, audit_bandwidth | All six core metrics (mean_position_error, stability_score, avg_control_effort, path_smoothness, observer_dependence_sco... |
| F10_anisotropy_comparative_only | moderate | comparative | anisotropy_score | anisotropy_score is meaningful only comparatively within the same turn count and encoding.  It accumulates unboundedly w... |
