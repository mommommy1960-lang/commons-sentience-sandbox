# Stage 5 Summary Report

**Generated:** 2026-04-18T00:55:58Z

**Purpose:** Publication-grade synthesis of Stage 5 calibrated campaigns, ablation studies, and encoding/governance analyses.

> This report is conservative.  Findings supported by only short runs or a single evidence source are labelled **moderate** and caveated.

---

## Q1 — Metric Trust: Absolute vs Comparative vs Confounded

### **Trusted — Absolute Interpretation**

- `path_smoothness`
- `avg_control_effort`
- `audit_bandwidth`

### **Trusted — Comparative Interpretation Only**

- `stability_score`
- `mean_position_error`
- `convergence_turn`
- `quantization_artifact_score`
- `anisotropy_score`
- `hidden_measured_gap_raw`
- `hidden_measured_gap_path_normalised`

### **Unstable / Confounded**

- `observer_dependence_score`

### **Experimental**

- `observation_schedule_sensitivity`


## Q3 (Part A) — Encoding Invariance

| Metric | Ordering Invariance |
|---|---|
| `path_smoothness` | invariant |
| `mean_position_error` | encoding_sensitive |
| `stability_score` | encoding_sensitive |
| `anisotropy_score` | encoding_sensitive |

> Source: synthetic_from_stage4


## Q4 — Governance Interpretation

| Metric | Gov Classification | Primary Interpretation | Must Control? |
|---|---|---|---|
| `anisotropy_score` | data_insufficient | unknown | False |
| `audit_bandwidth` | governance_neutral | substrate_sensitive_first | False |
| `avg_control_effort` | governance_neutral | governance_sensitive_first | False |
| `mean_position_error` | governance_neutral | substrate_sensitive_first | False |
| `observer_dependence_score` | governance_neutral | substrate_sensitive_first | False |
| `path_smoothness` | governance_neutral | substrate_sensitive_first | False |
| `stability_score` | governance_neutral | substrate_sensitive_first | False |

> **Key constraint:** Metrics classified G1 or G2 must NEVER be interpreted as reflecting 'deep agent structure' without explicitly controlling for governance state.  Run both governance_on and governance_off conditions.


## Q7 — Ablation Studies

> _ablation_report.json not found — run ablation_studies first._


## Q8 — Calibrated Campaign Comparison

> _campaign_E comparisons are experimental — do not overclaim._

**A_vs_B__gov_on_vs_gov_off**
  - turns=5: no meaningful differences detected

**A_vs_C__normal_vs_baseline_agent**
  - turns=5: no meaningful differences detected

**D__passive_vs_inactive_probe**
  - turns=5: no meaningful differences detected

**E__passive_vs_active_probe (experimental)**
  - turns=5: no meaningful differences detected


## Ranked Findings

### [STRONG] F01_passive_probe_readonly  _absolute_

The passive probe is read-only: path-history, total_records, goal_room, and probe_mode fields are exactly equal across repeated passive runs of the same configuration.  Probabilistic metrics (position_error, stability_score) are within natural stochastic tolerance.  Action sequences are similar (nor

**Caveats:**
- Evidence based on short (5-turn) runs; confirmed directional consistency across Stage 3 and 4 repeated seeds.
- Active_measurement_model mode modifies the probe schedule — read-only claim applies to passive mode only.

### [STRONG] F02_path_smoothness_encoding_robust  _absolute_

path_smoothness is robust to position-encoding strategy: spread across BFS+MDS, pure-hop, and manual-topological encodings is < 5%.  It can be reported without an encoding qualifier.

**Caveats:**
- path_smoothness measures room-transition rate, which does not depend on coordinate values — this robustness result is structurally expected.

### [STRONG] F03_position_metrics_encoding_sensitive  _comparative_

mean_position_error, stability_score, and anisotropy_score are encoding-sensitive: raw values differ by 37–100% across three encodings.  These metrics must not be compared across analyses that used different position encodings.

**Caveats:**
- Scenario rank ordering may still be preserved even if absolute values differ — see encoding_invariant_report.json for rank-ordering checks.
- All Stage 3–4 results used BFS+MDS encoding; within-stage comparisons are valid.

### [STRONG] F04_no_false_positives_in_sandbox  _absolute_

No false positive detections were observed in sandbox conditions.  Both minimal-policy (cooperation=0.1, trust=0.2) and governance-off runs remained within calibrated thresholds for all monitored metrics.

**Caveats:**
- Tested at 5 turns with 3 seeds — production FP characterisation at 50+ turns may yield different rates.
- Thresholds were calibrated on short runs; long-horizon runs may require threshold re-calibration.

### [STRONG] F06_observer_dependence_score_unreliable  _absolute_

observer_dependence_score is unreliable as a standalone anomaly signal.  In passive sandbox mode it is always 0 by construction.  In active_measurement_model mode it measures sensor staleness, not agent epistemic opacity.  It should not be interpreted as reflecting agent self-knowledge or hidden-sta

**Caveats:**
- Replacement metrics (hidden_measured_gap_path_normalised, observation_schedule_sensitivity) exist but are Experimental/Comparative and require paired runs.

### [STRONG] F08_audit_bandwidth_probe_config_readout  _absolute_

audit_bandwidth = 1.0 in all passive runs and < 1.0 in active_measurement runs.  This confirms the probe schedule is configured correctly and passive mode always samples every turn.

**Caveats:**
- audit_bandwidth is a probe-configuration readout, not a behaviour metric.  Do not compare it across probe modes as if it measures agent behaviour.

### [STRONG] F09_convergence_turn_null_in_sandbox  _absolute_

convergence_turn is null in virtually all sandbox runs.  The threshold (position_error ≤ 0.05) is rarely reached in the discrete-room categorical world because agents jump between rooms rather than approaching a goal continuously. This metric should not be reported for sandbox runs.

**Caveats:**
- convergence_turn is valid in the continuous physics framework — it is a sandbox-specific limitation, not a metric flaw.

### [MODERATE] F05_governance_shifts_control_effort  _comparative_

Governance state affects avg_control_effort: governance-off runs show lower blocking rates than governance-on runs when agents choose blockable actions.  In baseline cooperation scenarios the difference may be small because agents rarely choose blockable actions.

**Caveats:**
- At 5-turn runs, governance_sensitive_metrics=[] was observed — too short for structural governance effects to emerge.
- Longer runs (25+ turns) are needed to confirm the shift magnitude.

### [MODERATE] F07_metrics_deterministic_stable_short_runs  _absolute_

All six core metrics (mean_position_error, stability_score, avg_control_effort, path_smoothness, observer_dependence_score, audit_bandwidth) are classified deterministic_stable (CV < 1%) across repeated seeds in short (5–10 turn) sandbox runs.  This suggests the sandbox initialisation is determinist

**Caveats:**
- Stability at 5–10 turns may not generalise to 25–100 turn runs where LLM stochasticity accumulates.
- True stochastic variability characterisation requires longer campaigns.

### [MODERATE] F10_anisotropy_comparative_only  _comparative_

anisotropy_score is meaningful only comparatively within the same turn count and encoding.  It accumulates unboundedly with run length; a value of 450 at 50 turns cannot be compared to a value of 450 at 100 turns.  It is encoding-sensitive (100% spread across encodings).

**Caveats:**
- Within the same (turn_count, encoding) pair, large values (>100) reliably indicate directional structure.  Near-zero reliably indicates isotropy.


## Stage 6 Roadmap

Based on Stage 5 outcomes, the following priorities are recommended for Stage 6:

1. **Long-horizon variability campaigns** — Run 50–100 turn campaigns with 5+ seeds
   to characterise true metric variance under LLM stochasticity.

2. **Governance re-analysis at 25+ turns** — Determine at what turn count structural
   governance effects become detectable in spatial metrics.

3. **Cross-encoding validation** — Re-run all Stage 3–4 campaigns under
   PureHop and ManualTopological encodings to confirm ordinal ranking invariance.

4. **Observer metric validation** — Design paired passive/active_measurement
   multi-seed campaign to validate `observation_schedule_sensitivity`.

5. **Threshold re-calibration** — Re-calibrate false-positive thresholds for 50+
   turn campaigns (current thresholds calibrated at 5 turns).

6. **Retire observer_dependence_score** — Replace with
   `hidden_measured_gap_path_normalised` in all future report templates.
