# Stage 3 Scientific Report: Reality Audit

**Generated**: 2026-04-17 23:39 UTC
**Status**: Stage 3 — Real Experimental Execution & Statistical Validation

---


## 1. Experiment Setup

### Framework
- **Physics engine**: `RealityWorld` (continuous 2-D, seed-reproducible)
- **Adapter**: `SimProbe` passive mode → room-graph MDS embedding
- **Controller**: proportional (real-agent scenarios); random-walk (null baselines)

### Run Configuration
| Parameter | Value |
|---|---|
| Turn counts | 50, 75, 100 (dt=0.5 s → 25/37.5/50 s duration) |
| Seeds per configuration | 5 (42–46) |
| Scenarios | 6 |
| Total configurations | 90 |

### Scenarios Run
- `baseline`
- `anisotropy`
- `observer_divergence`
- `bandwidth_limited`
- `random_baseline_agent`
- `normal_agent`

## 2. Key Aggregated Results

| Scenario | pos_error (mean) | stability (mean) | anisotropy (mean) | bandwidth (mean) | N |
|---|---|---|---|---|---|

| anisotropy_t50 | 0.3342 | 0.3725 | 486.6458 | 1.0000 | 5 |
| bandwidth_limited_t50 | 4.2944 | 0.0813 | 445.2778 | 0.1000 | 5 |
| baseline_t50 | 0.9753 | 0.1578 | 451.4444 | 1.0000 | 5 |
| normal_agent_t50 | 0.9753 | 0.1578 | 451.4444 | 1.0000 | 5 |
| observer_divergence_t50 | 2.0944 | 0.1281 | 429.9405 | 0.2000 | 5 |
| random_baseline_agent_t50 | 11.6318 | 0.3140 | 0.6367 | 1.0000 | 5 |

## 3. Metric Stability

Stability flags are based on `consistency_score = 1 - std / (|mean| + ε)` across seeds.

- **Stable** (cs ≥ 0.8): position_error, velocity_error, stability_score, anisotropy_score, observer_dependence_score, bandwidth_bottleneck_score, quantization_artifact_score, control_effort, path_smoothness, convergence_time
- **Moderate** (0.5–0.8): none
- **Unstable** (< 0.5): none


## 4. Probe Read-Only Verification

**Stage 2 basic check**: ✅ PASS  (3 turns)
**Stage 3 detailed check**: ✅ PASS  (3 turns)
  - Sentinel: 2 exact matches, 0 acceptable variations
  - Aster: 2 exact matches, 0 acceptable variations
  - Unexpected divergences: Sentinel=[], Aster=[]

**Documented non-deterministic fields** (excluded from both comparisons):
  - narrative text (LLM output)
  - reasoning strings (LLM output)
  - log file timestamps
  - episodic_memory_count (depends on LLM-selected store_memory actions)
  - pending_contradictions_count (depends on LLM contradiction flagging)
  - trust_in_other (accumulates from LLM-driven interaction quality)
  - affective_state (drifts based on LLM action choices)


## 5. False-Positive Analysis

**Overall**: ✅ ALL PASSED
**Seeds tested**: 5

| Metric | Value | Threshold | Direction | Status |
|---|---|---|---|---|
| anisotropy_score | 0.7268 | 210.0 | below | ✅ |
| observer_dependence_score | 3.7559 | 15.0 | below | ✅ |
| quantization_artifact_score | 0.0000 | 5.0 | below | ✅ |
| bandwidth_bottleneck_score | 1.0000 | 0.95 | above | ✅ |

No false positives detected. All metrics behave correctly on random input.


## 6. Governance Sensitivity

_Governance sensitivity analysis. governance_on = continuous baseline (normal rules). governance_off = noisy quantized measurement (models erratic, unconstrained decisions). This is a model-level approximation._

| Metric | Gov-ON mean | Gov-OFF mean | Δ | Sensitive? |
|---|---|---|---|---|
| stability_score | 0.1578 | 0.1542 | -0.0036 | – |
| path_smoothness | 1.1696 | 1.7500 | 0.5804 | ★ |
| observer_dependence_score | 9.0289 | 9.0100 | -0.0189 | – |
| quantization_artifact_score | 0.0000 | 39.0000 | 39.0000 | ★ |
| control_effort | 58.7642 | 59.5000 | 0.7358 | ★ |
| anisotropy_score | 451.4444 | 450.5000 | -0.9444 | ★ |


## 7. Unexpected Patterns

This section is populated from anomalies found during the full experimental run.



## 8. Validated vs Experimental

| Component | Status |
|---|---|
| `SimProbe` passive mode read-only | ✅ Confirmed (Stage 2 + Stage 3) |
| Long-horizon runs (50/75/100 turns) | ✅ Implemented; results in `long_runs/` |
| Multi-run aggregation | ✅ Implemented in `aggregate_experiments.py` |
| Cross-run consistency scores | ✅ Computed per metric |
| False-positive detection | ✅ Threshold checks against random baseline |
| Governance sensitivity analysis | ✅ Implemented (model-level approximation) |
| Detailed path-history comparison | ⚠️ Final-room comparison only; per-turn history requires sandbox hook |
| `active_measurement_model` probe mode | ⚠️ Experimental; not the production default |
| Long-horizon sandbox runs (50+ LLM turns) | 🔬 Not yet run at scale (computationally expensive) |
| True governance ON/OFF sandbox comparison | 🔬 Planned; requires sandbox modification |

