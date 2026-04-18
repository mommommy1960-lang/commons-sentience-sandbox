# Stage 5 Findings

**Reality Audit Framework — Calibrated Experimental Results**

*Stage 5: Calibrated Experimental Campaigns + Ablations + Publication-Grade Synthesis*
*Status: Completed*

---

## Overview

Stage 5 moves from framework validation into interpretable scientific use.
All findings are grounded in cumulative evidence from Stages 1–4 and the
Stage 5 calibrated campaign matrix.  This document uses conservative language
throughout: findings supported by only one source or short run counts are
explicitly marked as **moderate** or **weak**.

---

## Section 1 — What Metrics Are Trustworthy

### Trusted for Absolute Interpretation

These three metrics can be reported without a comparison baseline and without
an encoding qualifier.  They have been validated in both the physics framework
and real (LLM-driven) sandbox campaigns.

| Metric | Why Trustworthy |
|---|---|
| `path_smoothness` | Invariant to encoding (< 5% spread); deterministic-stable in sandbox; correctly distinguishes movement patterns. |
| `avg_control_effort` | Direct measure of GovernanceEngine blocking rate; reproducible and monotonic under governance toggles. |
| `audit_bandwidth` | Probe-schedule readout; always 1.0 in passive mode by construction; perfectly reliable as a configuration check. |

### Trusted for Comparative Interpretation

These metrics produce valid *relative* comparisons within the same encoding
and run configuration.  They must not be compared across analyses that used
different position encodings.

| Metric | Caveat |
|---|---|
| `stability_score` | 49.8% spread across encodings; compare only within BFS+MDS |
| `mean_position_error` | 37.3% spread; ordinal ranking is valid (random walk >> structured) but absolute values are not |
| `convergence_turn` | Returns null in sandbox; use only in physics-framework analyses |
| `quantization_artifact_score` | Always 0 in passive mode; meaningful only in `active_measurement_model` |
| `anisotropy_score` | 100% encoding-sensitive; compare only within same (turn_count, encoding) pair |
| `hidden_measured_gap_raw` | Always 0 in passive mode; valid only as passive-vs-active difference |
| `hidden_measured_gap_path_normalised` | Preferred replacement for `observer_dependence_score` in cross-run comparisons |

---

## Section 2 — What Metrics Are Comparative Only

The following metrics **must never be interpreted absolutely**.  Report them
only as differences between paired conditions:

- `stability_score` — encoding-sensitive; 49.8% spread
- `mean_position_error` — encoding-sensitive; 37.3% spread; ordinal claim valid
- `anisotropy_score` — 100% encoding-sensitive; accumulates with turns
- `hidden_measured_gap_raw` — confounded by passive-mode = 0 baseline
- `observation_schedule_sensitivity` — requires paired passive + active runs; experimental

---

## Section 3 — What Remains Confounded or Encoding-Sensitive

### Confounded Metrics

| Metric | Confound | Recommendation |
|---|---|---|
| `observer_dependence_score` | In passive mode always 0 (no hidden-state divergence exists); in active mode measures sensor staleness, not agent opacity | Retire as standalone signal; use `hidden_measured_gap_path_normalised` |
| `convergence_turn` | Rarely fires in discrete-room sandbox (threshold for continuous world) | Do not report for sandbox; note null result explicitly |
| `quantization_artifact_score` | By design zero in passive mode | Only use in `active_measurement_model` mode |

### Encoding-Sensitive Metrics

These produce different absolute values depending on whether BFS+MDS,
pure-hop-distance, or manual-topological encoding is used:

- `mean_position_error`: ENCODING-SENSITIVE (37.3% spread)
- `stability_score`: ENCODING-SENSITIVE (49.8% spread)
- `anisotropy_score`: ENCODING-SENSITIVE (100% spread)

**All Stage 3–4 results used BFS+MDS encoding.** Within-stage comparisons
are internally consistent; cross-study comparisons with different encodings
are not valid.

---

## Section 4 — What Governance Changes Do to Interpretation

### A. avg_control_effort

`avg_control_effort` **is a direct governance-load measure**, not an agent
behaviour measure.  A high value means governance blocked many of the agent's
chosen actions.  At baseline (cooperative agent, standard rules), the value
anchors near 0 because agents rarely choose blockable actions.

**Causal claim constraint:** Do not interpret a high `avg_control_effort`
as indicating unusual agent intent without confirming that the governance
rules were not unusually restrictive for the observed action distribution.

### B. Structural vs metadata governance

`governance_strictness` in `ExperimentConfig` is **metadata only**.
`GovernanceEngine.check_action()` is binary (permit/block via rules.json
lookup) and does not use this parameter.  True governance-off state requires
structural monkeypatching:

```python
mock.patch.object(GovernanceEngine, "check_action", lambda self, a: (True, "disabled"))
```

### C. Short-run governance effects

Stage 4 governance campaigns at 5 turns showed `governance_sensitive_metrics = []`.
This is expected: at short run lengths, agents rarely explore enough rooms to
encounter blockable actions at a rate that produces detectable metric shifts.
Campaigns at 25+ turns are required for structural governance effects to emerge.

### D. Governance-neutral metrics

`mean_position_error`, `stability_score`, `path_smoothness`, `audit_bandwidth`,
and `observer_dependence_score` showed no detectable shift under the governance
toggle in Stage 4.  This does not mean governance never affects agent spatial
behaviour — it means the effect was below detection threshold at the tested run
lengths.

---

## Section 5 — What Passive Probe Evidence Supports

### Confirmed by Stage 4 expanded read-only validation:

1. **Exact invariance**: `probe_mode`, `goal_room`, `total_records` are
   identical across paired passive runs of the same configuration.
2. **Statistical invariance**: Probabilistic metrics (position_error,
   stability_score, avg_control_effort, path_smoothness, audit_bandwidth)
   are within natural stochastic tolerance.
3. **Action sequence similarity**: Normalised Levenshtein edit distance
   between paired action sequences < 0.20.
4. **No false positives**: Short-run campaigns with minimal-policy and
   governance-off conditions produced `no_false_positives = True`.

### Architecture constraint:

The passive probe claim is specific to `PROBE_MODE_PASSIVE`.
The `active_measurement_model` mode modifies only the audit layer's
observation schedule model — it does not mutate agent or world state —
but its outputs should be clearly labelled as modelling a constrained
audit instrument, not observing a different agent behaviour.

---

## Section 6 — What Conclusions Are Currently Justified

### Justified

1. **The passive probe is read-only** on deterministic and probabilistic
   path-history fields (short-run evidence; directionally consistent through
   Stage 3–4).

2. **path_smoothness reliably distinguishes movement patterns** and is
   robust to encoding choice.

3. **avg_control_effort reliably reflects governance load** — high values
   mean governance blocked more actions.

4. **Encoding choice materially affects position-error magnitude** (37–100%
   spread); position-based metrics should not be compared across analyses
   that used different encodings.

5. **Scenario rank-ordering by path_smoothness is encoding-invariant.**
   Rank-ordering by position-error metrics is encoding-sensitive.

6. **No false positives were observed** in the tested sandbox conditions.

---

## Section 7 — What Conclusions Are NOT Justified

### Not Currently Justified

1. **observer_dependence_score is NOT a measure of agent opacity or
self-awareness.** In passive sandbox mode it is structurally zero; in
active_measurement mode it measures audit sensor staleness.

2. **Absolute values of mean_position_error, stability_score, and
anisotropy_score cannot be compared across different encoding strategies**
or across different studies that may have used different encodings.

3. **governance_strictness config parameter does not affect real governance
behaviour.** Claims that increasing `governance_strictness` changes metric
outcomes are false — GovernanceEngine ignores this parameter.

4. **Short-run governance campaigns do not establish governance-neutrality
of spatial metrics.** 5-turn campaigns are insufficient to observe
governance-induced spatial effects.

5. **Metrics validated in the continuous physics framework may not apply
directly to the discrete-room sandbox.** `convergence_turn` is the primary
example: it fires reliably in the physics framework but is almost never
observed in sandbox runs.

6. **Observation schedule sensitivity (new observer metric) is experimental.**
It requires paired runs and has not been validated in multi-seed campaigns.

---

## Stage 6 Recommendations

1. **Run 25–100 turn calibrated campaigns** with 5 seeds to characterise
   true metric variability under LLM stochasticity.
2. **Re-run governance ablation at 25+ turns** to determine when structural
   governance effects become detectable.
3. **Validate observation_schedule_sensitivity** with paired passive/active
   multi-seed campaigns before reporting comparatively.
4. **Consider replacing observer_dependence_score** entirely with
   `hidden_measured_gap_path_normalised` in future reports.
5. **Cross-encode all Stage 3–4 results** to verify that directional findings
   hold under PureHop and ManualTopological encodings.
