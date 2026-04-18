# Metric Trust Ranking

**Reality Audit Framework — Stage 4 Validated Trust Rankings**

This document classifies all reality-audit metrics by trustworthiness based
on empirical evidence from Stages 1–4.  Use this table to decide which metrics
to report, which to use with caution, and which require a comparison baseline.

---

## Trust Tiers

| Tier | Meaning |
|---|---|
| **High** | Validated in both physics framework and sandbox; consistent across runs; interpreted without a reference baseline |
| **Medium** | Validated in physics framework; usable in sandbox with caveats |
| **Low** | Produces values in all modes but has known confounds that limit standalone interpretation |
| **Comparative** | Meaningful only when compared between two runs of identical configuration |
| **Experimental** | Exploratory; not yet validated; use for hypothesis generation only |

---

## Metric Rankings

| Metric | Tier | Intended Meaning | Validated Where | Major Confounds | Recommended Interpretation |
|---|---|---|---|---|---|
| `path_smoothness` | **High** | Fraction of turns where agent changed room; measures room-transition rate | Physics framework (all 6 modes), Sandbox (Stage 3 control), Governance campaigns | None significant; categorical world means 0/1 per turn | Use directly; compare across configs to detect movement-pattern shifts |
| `avg_control_effort` | **High** | Fraction of agent actions blocked by governance; direct governance adherence proxy | Physics framework, Sandbox (governance campaigns verified real blocking effect) | Depends on action distribution; agents rarely choose blockable actions → score anchored near 0 in low-conflict runs | Interpret as "governance load"; high values (>0.3) are meaningful; near-0 values are expected baseline |
| `audit_bandwidth` | **High** | Fraction of turns where the audit sensor actually observed; reflects probe schedule, not agent behaviour | All probe modes (by design); passive=1.0 always; active_measurement < 1.0 | Not a behaviour metric — purely a probe configuration readout | In passive mode: always 1.0 (confirms probe is active). In active mode: tells you how many turns were actually sampled |
| `stability_score` | **Medium** | Inverse of variance of position-error across the run; high = consistent relationship to goal | Physics framework (full validation), Sandbox (Stage 3 long-horizon) | Depends on position encoding; MDS coordinate spread affects absolute error values; not comparable across encodings | Compare within same encoding. Values > 0.3 indicate stable goal relationship; < 0.1 indicates high variance |
| `mean_position_error` | **Medium** | Mean Euclidean distance from measured position to goal in MDS 2-D space | Physics framework, Sandbox (Stage 3, 50-turn runs) | Units depend on MDS coordinate scale (normalised to ~[-1,1]); not interpretable in absolute terms; ~0.97 for structured runs, ~11.6 for random walk | Compare within-framework only. Use for ordinal ranking (random walk >> structured >> goal-seeking) not for absolute claims |
| `convergence_turn` | **Medium** | First turn where position_error ≤ 0.05; proxy for goal-approach speed | Physics framework (convergence verified), Sandbox (rarely achieved due to categorical discrete rooms) | In categorical world, `None` is the typical value; this metric was designed for continuous physics and rarely fires in sandbox | Report as `null` in sandbox and note it is physics-framework-specific |
| `quantization_artifact_score` | **Medium** | Variance in measured-vs-true position gaps; detects systematic measurement errors | Physics framework (NOISY_QUANTIZED mode), Sandbox (passive mode → always 0) | In passive mode always 0 (passive probe has no quantization); only meaningful in active_measurement mode | Useful in `active_measurement_model` mode to detect sensor staleness patterns; ignore in passive mode |
| `observer_dependence_score` | **Low** | Mean L2 gap between hidden-state position and measured position | Physics framework (simulated), Sandbox (Stage 3 calibrated threshold=15.0) | **Start-anchored artefact**: in non-OBSERVER_TRIGGERED physics modes, `hidden_state.position` in raw_log always equals the true current position (not an independent hidden-state estimate). In passive sandbox probe, this score is always 0. In active_measurement, it measures sensor staleness, not agent epistemic opacity. | Do NOT interpret as a measure of agent self-awareness or opacity. Use `hidden_measured_gap_path_normalised` (observer_metrics module) instead for comparative staleness |
| `anisotropy_score` | **Comparative** | \|x_sum − y_sum\| / max, across all positions; measures directional movement bias in the 2-D MDS space | Physics framework (validated: near-0 for symmetric random walk, ~450 for x-directed structured runs) | Accumulates unboundedly over turns (longer runs → higher scores); sensitive to MDS axis alignment which may vary across runs; not comparable across different turn counts | Compare only within same turn count. Large value (>100) indicates strong directional structure. Near-0 indicates isotropic travel. Never compare absolute values across different run lengths |
| `hidden_measured_gap_raw` | **Comparative** | Mean L2 gap between true and audit-measured positions (same formula as observer_dependence_score) | Observer metrics module (Stage 4) | Same start-anchoring confound as observer_dependence_score; adds std and max which improve interpretability | Always 0 in passive mode. Compare passive vs active runs to isolate sensor staleness effect |
| `hidden_measured_gap_path_normalised` | **Comparative** | Gap normalised by agent total path length; corrects for run length and movement magnitude | Observer metrics module (Stage 4); comparative design validation | Returns `None` if agent barely moved (path_length ≈ 0) | Preferred replacement for `observer_dependence_score` when comparing across run lengths. Requires path_length > 0 |
| `observation_schedule_sensitivity` | **Comparative** | Ratio of active-measurement gap to passive gap; quantifies how much audit schedule inflates apparent opacity | Observer metrics module (Stage 4) | Requires paired runs (same config, different probe mode) | Use when deciding whether to deploy active_measurement vs passive mode. Ratio > 5 means active mode is highly misleading |

---

## Quick Reference: Use in Reports

**For governance adherence analysis:**
→ `avg_control_effort`, `path_smoothness`

**For audit infrastructure validation:**
→ `audit_bandwidth`, `hidden_measured_gap_path_normalised`, `observation_schedule_sensitivity`

**For exploratory agent behaviour comparison:**
→ `stability_score`, `mean_position_error` (ordinal only), `anisotropy_score` (within same turn count)

**Do not use as standalone anomaly signals:**
→ `observer_dependence_score`, `anisotropy_score`, `convergence_turn` (in sandbox)

---

## Confound Summary

### 1. MDS coordinate dependency
Metrics `mean_position_error`, `stability_score`, and `anisotropy_score` are
all derived from MDS 2-D coordinates.  The coordinate axes are determined by
the topology of the room graph and may not align intuitively with semantic
room relationships.  Encoding robustness analysis (Stage 4) shows that while
MDS and manual topological encoding agree on ordinal rankings, absolute values
differ by up to 20%.

### 2. Categorical world discreteness
The commons_sentience_sim sandbox uses discrete room transitions, not
continuous position updates.  All metrics designed for continuous physics
(e.g., `convergence_turn`) fire rarely or never in sandbox conditions.

### 3. Governance strictness as metadata
The `governance_strictness` field in ExperimentConfig is recorded as
metadata only.  It does NOT change GovernanceEngine behaviour.  Generating
real governance-off conditions requires monkeypatching `check_action`
(see `governance_campaigns.py`).

### 4. LLM stochasticity
Real sandbox runs (with LLM-driven action selection) will produce different
action sequences per seed even with identical config.  All metrics except
`audit_bandwidth` and `probe_mode` will vary across seeds.  Use 3–5 seeds
and report mean ± std.

---

*Generated: Stage 4 | Commons Sentience Sandbox — Reality Audit Framework*
