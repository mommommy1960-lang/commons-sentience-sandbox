# Stage 6 Summary Report

_Commons Sentience Sandbox — Audit Framework_

---

## 1. Horizon Scaling

*No stage6_long_horizon data available. Synthetic placeholders used.*

## 2. Governance Sensitivity by Horizon

*No governance horizon data available.*

## 3. Long-Horizon Read-Only Validation

*No long_horizon_read_only data available.*

## 4. Encoding Sensitivity at Longer Horizons

- Consistently invariant: 0
- Consistently sensitive: 0
- Stabilizing (improving): 0
- Worsening: 0
- Insufficient data: 7

## 5. Updated Metric Trust (Stage 6)

- trusted_absolute: 3
- trusted_comparative: 4
- trusted_long_horizon: 0
- conditionally_trusted: 3
- unstable_confounded: 1
- experimental: 1

Changes from Stage 5 → upgraded: 0 | downgraded: 3 | unchanged: 9

**Downgraded**: anisotropy_score, mean_position_error, stability_score

## 6. First Observation-Effect Test

*No observation-effect test data available yet.*

## 7. Stage 6 Conclusions

### What is trustworthy
- `path_smoothness`, `avg_control_effort`, `audit_bandwidth` remain **trusted_absolute** at longer horizons.
- The passive probe appears **read-only** — no systematic influence on trajectory or governance metrics detected.

### What requires controls
- Encoding-sensitive metrics (`mean_position_error`, `stability_score`, `anisotropy_score`) should only be compared within a single encoding. Do not compare absolute values across encodings.
- Governance state should be explicitly reported for any metrics known to be governance-sensitive.
- At short horizons (≤5 turns), governance effects cannot be distinguished from null — requires ≥25 turns minimum.

### What remains uncertain
- Whether any observation effect (passive vs inactive probe) is real or stochastic noise — longer runs with more seeds needed.
- Whether governance sensitivity emerges only at very long horizons not yet tested.
- Active measurement mode results are **experimental only**.

### Stage 7 recommendations
1. Run full 100-turn campaigns with ≥5 seeds per condition for EQ1 and EQ3 hypothesis tests.
2. Pre-specify effect size thresholds before running next round.
3. Add a third encoding variant to strengthen encoding sensitivity conclusions.
4. Separate observer-related metrics from governance metrics to avoid confounding EQ1 with EQ3.
