# STAGE6_EXPERIMENT_SPEC.md
# Pre-Registration-Style Experiment Specification
# Commons Sentience Sandbox — Stage 6 Audit Framework

**Version**: 1.0  
**Date**: 2026-04-18  
**Status**: Specification (not a claim of real-world simulation detection)

---

## 0. Objective Statement

This specification describes Stage 6 experiments for the Commons Sentience Sandbox audit framework.

**We are NOT claiming**: that the real universe is a simulated system, that any evidence here constitutes proof of simulation, or that sandbox results generalize to physical reality.

**We ARE testing**: whether the sandbox simulation exhibits signatures that our audit framework can detect, whether those signatures survive controls and longer horizons, and which metrics are trustworthy enough to inform future experimental design.

---

## 1. Experiment Questions

| ID | Question |
|----|----------|
| EQ1 | Does passive probe observation differ from inactive probe at horizons ≥25 turns? |
| EQ2 | Does active measurement mode create a meaningful, reproducible shift relative to passive probe? |
| EQ3 | Does governance state affect simulation trajectories, and if so, at what horizon does the effect first appear? |
| EQ4 | Which metrics are stable (consistent magnitude and variance) across 5, 25, 50, and 100 turns? |
| EQ5 | Does encoding sensitivity worsen, stabilize, or resolve at longer horizons? |
| EQ6 | Does baseline-agent behavior differ from normal-agent behavior in a horizon-stable way? |

---

## 2. Hypotheses

All hypotheses are stated conservatively and are designed to be falsifiable within this sandbox. None are claims about physical reality.

### H1 — Observer Effect at Long Horizon
**Null** (H1₀): Passive probe produces no detectable difference in any primary metric relative to inactive probe, across all tested horizons.  
**Alternative** (H1ₐ): At least one primary metric shows a consistent, reproducible directional difference between passive-probe and inactive-probe runs at horizons ≥25 turns.  
**Conservative default**: Assume H1₀ unless effect size exceeds sandbox variability (Cohen's d ≥ 0.5).

### H2 — Active Measurement Mode Shift
**Null** (H2₀): Active-measurement mode produces no additional shift beyond passive probe.  
**Alternative** (H2ₐ): Active-measurement mode shifts at least one observer-related metric by more than the passive vs. inactive difference.  
**Note**: Active measurement results are always labeled *experimental*; H2 is exploratory only.

### H3 — Governance Neutral at Short, Sensitive at Long
**Null** (H3₀): Governance state (on/off) produces no metric shift at any tested horizon.  
**Alternative** (H3ₐ): Governance sensitivity emerges at a specific horizon threshold (≥25, ≥50, or ≥100 turns) not present at 5 turns.  
**Conservative default**: Assume H3₀ unless governance delta exceeds false-positive threshold at a given horizon.

### H4 — Horizon Stability of Trusted Metrics
**Null** (H4₀): All Stage 5 trusted metrics show consistent magnitude and classification across horizons.  
**Alternative** (H4ₐ): At least one Stage 5 trusted metric changes classification (e.g., variability doubles) at longer horizons.

### H5 — Encoding Sensitivity Persistence
**Null** (H5₀): Encoding-sensitive metrics remain consistently sensitive regardless of horizon.  
**Alternative** (H5ₐ): Some encoding-sensitive metrics stabilize (become invariant) at longer horizons due to law-of-large-numbers averaging.

---

## 3. Primary Metrics

These metrics are used as the primary dependent variables for hypothesis testing.

| Metric | Trust Level | Comparative Only | Encoding Confound | Governance Confound |
|--------|-------------|-----------------|-------------------|---------------------|
| `path_smoothness` | trusted_absolute | No | None | None |
| `avg_control_effort` | trusted_absolute | No | None | None |
| `audit_bandwidth` | trusted_absolute | No | None | None |
| `stability_score` | trusted_comparative | **Yes** | Strong | None |
| `observer_dependence_score` | trusted_comparative | **Yes** | None | None |

**Primary outcome for EQ1–EQ2**: `observer_dependence_score`, `stability_score`  
**Primary outcome for EQ3**: `avg_control_effort`, `path_smoothness`, `audit_bandwidth`  
**Primary outcome for EQ4**: All five primary metrics  

---

## 4. Secondary Metrics

Used for exploratory analysis and cross-validation.

| Metric | Trust Level | Notes |
|--------|-------------|-------|
| `mean_position_error` | trusted_comparative | encoding-sensitive; comparative only |
| `anisotropy_score` | trusted_comparative | encoding-sensitive; do not compare absolute values across encodings |
| `bandwidth_bottleneck_score` | trusted_comparative | comparative only |
| `trajectory_entropy` | trusted_comparative | encoding-sensitive |
| `constraint_violation_rate` | trusted_comparative | governance-sensitive; interpret relative to governance state |

---

## 5. Excluded / Low-Trust Metrics

These metrics are excluded from hypothesis testing in this stage:

| Metric | Reason for Exclusion |
|--------|----------------------|
| `goal_proximity_score` | unstable_confounded: both encoding and governance sensitive |
| `dimensionality_estimate` | experimental: interpretation unclear; not yet validated |
| Any raw LLM text similarity | not deterministic; cannot be meaningfully compared |

---

## 6. Horizon Lengths

| Horizon | Role | Notes |
|---------|------|-------|
| 5 turns | Short reference (Stage 5 baseline) | Not a primary experimental condition; used for reference only |
| 25 turns | Minimum meaningful horizon | First test of horizon effects |
| 50 turns | Standard horizon | Primary horizon for EQ1–EQ5 |
| 100 turns | Extended horizon | Tests whether effects persist or amplify |

Minimum repetitions per condition per horizon: **3 seeds** (5 preferred where compute allows).

---

## 7. Comparison Conditions

| Label | Description | vs. Condition |
|-------|-------------|---------------|
| lh_A | governance ON, passive probe, normal agent | Reference baseline |
| lh_B | governance OFF/reduced, passive probe, normal agent | vs. lh_A → EQ3 (H3) |
| lh_C | governance ON, **inactive probe**, normal agent | vs. lh_A → EQ1 (H1) |
| lh_D | governance ON, **active measurement**, normal agent | vs. lh_A + lh_C → EQ2 (H2) [experimental] |
| lh_E | governance ON, passive probe, **baseline agent** | vs. lh_A → EQ6 |

---

## 8. Interpretation Rules

### 8.1 What counts as a detectable effect
- Effect size Cohen's d ≥ 0.5 relative to within-condition variability
- Effect must be directionally consistent across ≥ 2/3 of repeated seeds
- Effect must exceed the false-positive threshold documented in `governance_interpretation_report.json`

### 8.2 What counts as a null result
- Effect size Cohen's d < 0.2 at all tested horizons
- No directional consistency across seeds
- Effect within sandbox run-to-run variability (CV < 0.15 at that horizon)

### 8.3 Encoding-sensitive metrics
- Never compare absolute values of encoding-sensitive metrics across experiments with different encodings
- For encoding-sensitive metrics, only directional ordering (higher/lower) within the same encoding is interpretable
- If encoding changes the direction of an effect, the finding is **not robust** and must be noted

### 8.4 Governance confounds
- For experiments comparing governance-on vs. governance-off: explicitly report which metrics are governance-sensitive
- Do not attribute governance effects to observer dynamics unless governance sensitivity is controlled

### 8.5 LLM stochasticity
- LLM-driven fields cannot be expected to be exactly reproducible
- Path similarity is distributional (edit distance), not exact equality
- Any result that only holds for one specific LLM run is not generalizable

---

## 9. What Counts as Support vs. Null Result

### 9.1 EQ1 — Observation effect
| Outcome | Interpretation |
|---------|----------------|
| Cohen's d ≥ 0.5 on `observer_dependence_score`, consistent at ≥2 horizons | **Supports H1ₐ**: detectable observation effect |
| Cohen's d 0.2–0.5 at any horizon | **Inconclusive**: possible effect, requires replication |
| Cohen's d < 0.2 at all horizons | **Null result**: no detectable observation effect |

### 9.2 EQ2 — Active measurement
| Outcome | Interpretation |
|---------|----------------|
| Additional shift beyond passive-vs-inactive on any observer metric | **Exploratory positive**: warrants further study but clearly experimental |
| No additional shift | **Null result**: active mode not distinguishable from passive in this framework |

### 9.3 EQ3 — Governance horizon
| Outcome | Interpretation |
|---------|----------------|
| Governance effect emerges at specific horizon (appears at H but not H-1) | **Supports H3ₐ**: governance sensitivity requires minimum horizon |
| Governance effect present at all horizons | **Governance dominated**: note in interpretation |
| No governance effect at any horizon ≥100 turns | **Null result EQ3**: governance neutral at all tested scales |

---

## 10. What Findings Remain Exploratory Only

The following will **always** be interpreted as exploratory, regardless of effect size:

1. **Active measurement mode (lh_D)**: Results are marked experimental in all outputs. Effect of active mode is not a primary hypothesis.

2. **Anisotropy score at any horizon**: Remains encoding-sensitive; absolute values not interpretable.

3. **Any single-horizon finding**: A finding at only one horizon (e.g., only at 100 turns) requires replication at multiple horizons before being considered more than exploratory.

4. **Any result with fewer than 3 seeds**: Minimum replication threshold is 3 seeds.

5. **Governance effects at exactly 5 turns**: Stage 5 null result at 5 turns does not generalize to longer horizons; conversely, a positive result at 5 turns would be treated as exploratory until confirmed at longer horizons.

6. **Any metric not in the primary or secondary list above**: Even if a metric shows a strong effect, if it is not pre-specified above it is exploratory.

---

## 11. Stage 6 Analysis Pipeline

The following analysis files implement this specification:

| File | Purpose |
|------|---------|
| `reality_audit/experiments/stage6_long_horizon_campaigns.py` | Runs real sandbox campaigns at 25, 50, 100 turns |
| `reality_audit/analysis/horizon_scaling.py` | EQ4: classifies metric stability across horizons |
| `reality_audit/analysis/governance_horizon_effects.py` | EQ3: governance sensitivity per horizon |
| `reality_audit/validation/long_horizon_read_only.py` | Verifies passive probe is read-only at longer runs |
| `reality_audit/analysis/encoding_horizon_interactions.py` | EQ5: encoding sensitivity × horizon |
| `reality_audit/analysis/update_metric_trust.py` | Part 6: integrates all evidence into updated trust |
| `reality_audit/analysis/plot_stage6.py` | Part 8: generates all Stage 6 figures |
| `reality_audit/reports/generate_stage6_summary.py` | Part 9: generates stage6_summary.md |

---

## 12. Known Limitations

| ID | Limitation |
|----|------------|
| L-S6-01 | All agents are LLM-driven; results are not deterministic and may vary by model version |
| L-S6-02 | "Governance off" is implemented via mock patch; fully removing governance in the real sandbox would require deeper architectural change |
| L-S6-03 | The sandbox uses a fixed room graph; position encoding results may not generalize to continuous or non-graph environments |
| L-S6-04 | 100-turn runs require significant compute; some conditions may only be run at 25 turns with fewer seeds |
| L-S6-05 | All findings are descriptive of this sandbox only; no inference to external systems is warranted |

---

*This specification is a planning and documentation artifact, not a peer-reviewed document.*
