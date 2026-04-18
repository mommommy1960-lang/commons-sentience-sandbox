# Metric Mapping Table

This document explains how each Reality Audit metric — originally designed
for a continuous 2-D physics simulation — is adapted to the
turn-based, room-graph sandbox of `commons_sentience_sim`.

The sandbox has no physical coordinates, no velocities, and no forces.
All positional reasoning is performed via a **graph-spectral embedding**:
BFS shortest-path distances between the five rooms are projected into a
stable 2-D plane using classical Multidimensional Scaling (MDS), then
normalised to \([-1, 1]^2\).  This gives every room a unique, reproducible
(x, y) coordinate that preserves topological neighbourhood.

---

## Room coordinates (MDS embedding)

| Room | x | y |
|---|---|---|
| Memory Archive | ~−0.77 | ~−0.77 |
| Reflection Chamber | ~−0.77 | ~+0.77 |
| Operations Desk | ~+0.77 | ~−0.77 |
| Social Hall | ~+0.77 | ~+0.77 |
| Governance Vault | ~+0.38 | ~+0.38 |

Exact values depend on the BFS distance matrix and are recomputed at
runtime.  They are saved to `reality_audit/config.json` on every run.

---

## Metric reference table

| Metric name | Original continuous meaning | Sandbox interpretation | Implementation proxy | Justification | Limitations |
|---|---|---|---|---|---|
| **position_error** | Mean Euclidean distance of measured trajectory from goal position | Mean Euclidean distance of agent's measured room-embedding position from the goal room embedding, averaged over all turns | `mean( dist(measured_pos, goal_pos) )` for each agent-turn record | Room topology is preserved by MDS; closer rooms map to nearer coordinates | MDS embedding is 2-D; high-dimensional room relationships may not compress perfectly into two axes |
| **convergence_time** | Simulated time (seconds) until position error first falls below tolerance | Turn number at which the agent's measured position first enters a threshold radius of the goal room embedding | First turn where `position_error ≤ 0.05` (approx. same-room distance); `None` if never reached | Agents following a scripted circuit will visit every room; if they never reach the goal room the score is `None` | Threshold is arbitrary (0.05 in MDS space ≈ same-room); tune if rooms are added or the graph changes |
| **stability_score** | `1 / (1 + variance(position_errors))` — higher is more stable | Same formula applied to per-turn position errors derived from room embeddings | `1 / (1 + Var(position_error[t]))` | Variance of a room-visit sequence captures how consistently an agent stays near or away from its goal | Room visits are discrete; an agent cycling a regular circuit will show low variance regardless of goal relationship |
| **observer_dependence_score** | Mean divergence between hidden (true) position and measured position when observations are sparse | Mean Euclidean gap between the true current room embedding (`hidden_state["position"]`) and the measured position (which may be stale in `active_measurement_model` mode) | `mean( dist(hidden_pos[t], measured_pos[t]) )` | In `passive` mode this is always 0 (true read-only baseline).  In `active_measurement_model` mode the audit sensor is intentionally made sparse so the gap becomes the signal | Only non-zero in `active_measurement_model` mode; in production passive mode this metric is always 0, serving as a sanity-check that the probe is read-only |
| **path_smoothness** | Sum of squared velocity changes (jerk) — lower is smoother | Room-change rate: fraction of agent-turns where the agent moved to a different room compared to the previous turn | `room_changes / total_records` | Frequent room changes correspond to high positional jerk in the continuous analogy | Categorical — only 0 or 1 per turn, no gradient.  Circuit agents always move, so baseline is always ~1.0 |
| **control_effort** | Integral of control force magnitude | Fraction of turns where an agent's action was *blocked* by the governance engine | `blocked_actions / total_records` | In the continuous world, blocked actions are equivalent to an agent requesting a large control input that is rejected | Governance blocks also serve legitimate safety purposes; high control_effort is not always bad |
| **anisotropy_score** | Ratio of x-axis to y-axis displacement — higher means directional bias | Same formula applied to the MDS room coordinates visited by agents | `abs(sum_x - sum_y) / max(sum_x, sum_y)` | If the room graph is symmetric the embedding will be approximately isotropic; an asymmetric circuit biases visits to one quadrant | The MDS embedding may introduce its own axis asymmetry; interpret relative to the baseline scenario, not in isolation |
| **bandwidth / staleness** (audit_bandwidth) | Fraction of timesteps where a sensor update was received (`actual_updates / expected_updates`) | Fraction of audit turns where the probe recorded a live measurement vs a stale cached value | `audit_observed_count / total_records` | Tracks how "information-complete" the audit transcript is; 1.0 = fully sampled, < 1.0 = some turns used stale data | Only meaningful in `active_measurement_model` mode.  In `passive` mode this is always 1.0 |
| **hidden-state divergence** | Difference between the true (physics) position and what the sensor reported | Mean Euclidean distance between `hidden_state["position"]` and `measured_position` in the audit log | Same as `observer_dependence_score` above | When audit bandwidth < 1, the cached measurement lags the true room, and this divergence becomes the hidden-state gap | Categorical rooms mean the divergence is either 0 (same room) or a fixed MDS distance (different room), not a continuous signal |

---

## Notes on validity

1. **All metrics are relative, not absolute.**  A position_error of 0.4 in
   MDS space for one room graph may correspond to a completely different
   absolute position error in a different graph layout.  Always compare
   scenarios within the same set of rooms.

2. **`passive` probe mode is the only production mode.**  Observer-dependence
   and hidden-state divergence metrics are 0.0 in passive mode by design.
   They are intended as signals in `active_measurement_model` mode for
   methodological comparison only.

3. **Baseline normalisation.**  All scenarios should be compared against
   `Scenario A (straight-path baseline)` from `toy_experiments.py` before
   drawing conclusions.

4. **Room-graph changes invalidate historical comparisons.**  Adding or
   removing rooms changes the BFS distances and thus the MDS coordinates.
   Any saved audit logs are not comparable across graph versions.
