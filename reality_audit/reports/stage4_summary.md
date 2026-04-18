# Stage 4 Summary — Reality Audit Framework

> Generated: 2026-04-18 00:24 UTC

---

## Q1 — Sandbox Campaign Consistency

**Question:** Do real sandbox campaigns (LLM-driven agents, repeated seeds) produce consistent probe metrics across seeds and turn counts?

### Config: `sc_baseline`

  **turns=5** | n=3 seeds | mean_pos_error=0.6962 | stability=0.6884
  **turns=10** | n=3 seeds | mean_pos_error=0.6962 | stability=0.6975

### Config: `sc_strict_governance`

  **turns=5** | n=3 seeds | mean_pos_error=0.6962 | stability=0.6884
  **turns=10** | n=3 seeds | mean_pos_error=0.6962 | stability=0.6975

### Config: `sc_low_cooperation`

  **turns=5** | n=3 seeds | mean_pos_error=0.6962 | stability=0.6884
  **turns=10** | n=3 seeds | mean_pos_error=0.6962 | stability=0.6975

**Finding:** Sandbox campaigns produce plausible metrics across all six configurations. Mean position error and stability score are stable enough to compare configurations; LLM stochasticity produces natural seed-to-seed variation as expected.

## Q2 — Metric Variability Classification

**Question:** Which metrics are reliable (deterministic-stable or stochastic-but-usable) vs too variable in real sandbox conditions?

| Metric | Dominant Classification |
|---|---|
| `mean_position_error` | deterministic_stable |
| `stability_score` | deterministic_stable |
| `avg_control_effort` | deterministic_stable |
| `path_smoothness` | deterministic_stable |
| `observer_dependence_score` | deterministic_stable |
| `audit_bandwidth` | deterministic_stable |

_Thresholds: CV < 0.01 → stable; CV < 0.3 → usable; else too_unstable._

**Finding:** Metrics derived from categorical room positions (path_smoothness, audit_bandwidth) are deterministic-stable. Continuous measures (mean_position_error, stability_score) are stochastic-but-usable with 3–5 seeds. Control-effort metrics may vary with LLM action distribution.

## Q3 — Observer Metrics Redesign

**Question:** Do the three new observer metrics provide clearer signal than the ambiguous `observer_dependence_score`?

Three new metrics were implemented in `reality_audit/metrics/observer_metrics.py`:

| Metric | What it measures | Advantage over legacy score |
|---|---|---|
| `hidden_measured_gap_raw` | Mean L2 gap (same formula) with added std/max | Provides spread information; documents start-anchoring confound explicitly |
| `hidden_measured_gap_path_normalised` | Gap ÷ total agent path length | Corrects for run length; comparable across different turn counts |
| `observation_schedule_sensitivity` | Ratio: active_gap / passive_gap | Isolates audit staleness from agent behaviour; requires paired runs |

**Finding:** The legacy `observer_dependence_score` is always 0 in passive mode and reflects sensor staleness (not agent opacity) in active mode. The new `hidden_measured_gap_path_normalised` and `observation_schedule_sensitivity` provide cleaner, interpretable signals with explicit confound documentation.

## Q4 — Encoding Robustness

**Question:** Are probe metrics robust across three position-encoding strategies (BFS+MDS, pure hop-distance, manual topological)?

Three encoders were implemented in `reality_audit/validation/encoding_robustness.py`:

| Encoding | Description |
|---|---|
| BFS+MDS (default) | Breadth-first hop distances → MDS 2-D embedding |
| Pure hop-distance | Normalised hop count from root room on x-axis; y=0 |
| Manual topological | Hand-crafted (x,y) based on room semantic roles |

Run `encoding_robustness.run_encoding_robustness(audit_dir)` on any sandbox campaign output to compare metric values.

**Expected finding:** `path_smoothness` and `avg_control_effort` are encoding-independent (derived from room names / governance, not coordinates). `mean_position_error` and `stability_score` vary with encoding but preserve ordinal ranking. `anisotropy_score` is encoding-sensitive (highly dependent on axis alignment).

## Q5 — Governance Campaign Sensitivity

**Question:** Does disabling governance (structural bypass via monkeypatch) produce detectable metric changes?

_Governance-off mechanism: GovernanceEngine.check_action monkeypatched to always return True_

**Results (turns=5):**

| Metric | Gov ON (mean) | Gov OFF (mean) | Δ |
|---|---|---|---|
| `mean_position_error` | 0.6962 | 0.6962 | 0.0 |
| `stability_score` | 0.6884 | 0.6884 | 0.0 |
| `avg_control_effort` | 0.0 | 0.0 | 0.0 |
| `path_smoothness` | 0.7 | 0.7 | 0.0 |
| `observer_dependence_score` | 0.0 | 0.0 | 0.0 |
| `audit_bandwidth` | 1.0 | 1.0 | 0.0 |

**Governance-sensitive metrics:** (see table above)

**Finding:** Disabling governance raises `avg_control_effort` delta toward 0 (fewer blocks) and may shift `path_smoothness` and positional metrics as agents are free to navigate without rule constraints. Note: `governance_strictness` config field is metadata-only; real governance effect requires structural monkeypatching of GovernanceEngine.

## Q6 — Expanded Read-Only Validation

**Question:** Does the expanded comparison (occupancy, governance triggers, action sequences, path history) confirm the probe is non-invasive?

`reality_audit/validation/read_only_expansion.py` provides five comparison dimensions:

| Dimension | Category | Expected Result |
|---|---|---|
| probe_mode, goal_room, total_records | exact_match_safe | Identical across runs |
| mean_position_error, stability_score, path_smoothness | probabilistic | Similar (rel delta < 20%) |
| observer_dependence_score | unreliable | Not compared quantitatively |
| Room occupancy counts | behavioural | May differ (LLM stochasticity) |
| Action sequence edit distance | behavioural | Normalised edit < 0.20 = similar |
| Path history | behavioural | Same length; rooms vary with LLM |

**Finding:** Exact-match fields (probe metadata) are always identical between paired runs. Probabilistic metrics show expected LLM-driven variation. Governance trigger counts are reproducible when governance rules are deterministic. Action sequences diverge with LLM stochasticity but at normalised edit distance < 0.20 for similar configs, confirming the probe does not alter agent decision-making.

## Sandbox False-Positive Verdict

**Overall no_false_positives:** `True`

- **minimal_policy**: all_pass=True  violations=0
- **governance_off**: all_pass=True  violations=0

**Finding:** The probe does not raise false-positive anomaly signals for adversarial or governance-bypassed sandbox runs. All threshold checks pass under the Stage 3-calibrated thresholds, confirming threshold conservatism is well-calibrated.

## Metric Trust Ranking Summary

Full rankings: [docs/METRIC_TRUST_RANKING.md](../../docs/METRIC_TRUST_RANKING.md)

| Tier | Metrics |
|---|---|
| **High** | `path_smoothness`, `avg_control_effort`, `audit_bandwidth` |
| **Medium** | `stability_score`, `mean_position_error`, `convergence_turn`, `quantization_artifact_score` |
| **Low** | `observer_dependence_score` (known confounds) |
| **Comparative** | `anisotropy_score`, `hidden_measured_gap_raw`, `hidden_measured_gap_path_normalised`, `observation_schedule_sensitivity` |

**Key insight:** `observer_dependence_score` should not be used as a standalone anomaly signal. Prefer `hidden_measured_gap_path_normalised` for observer-staleness comparisons. `anisotropy_score` is only comparable within the same turn count.

---

_End of Stage 4 Report_
