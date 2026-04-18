# Experimental Limitations

**Reality Audit Framework — Known Limitations and Constraints**

*Applies to: Stages 1–5*
*Last updated: Stage 5*

---

## Architecture Limitations

### L01 — No public Agent API

The `Agent` class in `commons_sentience_sim` has no public `observe()` or
`choose_action()` method.  The full LLM-driven turn loop is internal to
`run_sim.py`.  This means:

- We cannot inject custom agent policies for unit-level ablations.
- Ablations that change agent behaviour must work through `ExperimentConfig`
  parameters or monkeypatching governance.
- "Baseline agent" comparisons use `cooperation_bias` and
  `initial_agent_trust` as proxies, not a true random-action policy.

### L02 — Discrete room world

The sandbox world consists of named rooms (not continuous positions).
Consequences:
- `convergence_turn` (threshold position_error ≤ 0.05) almost never fires.
- Position encoding is a post-hoc MDS embedding — it is not a native world
  property.  This introduces the encoding-sensitivity problem (see L04).
- `path_smoothness` is 0-or-1 per turn, not continuous.

### L03 — governance_strictness is metadata only

`ExperimentConfig.governance_strictness` does not influence
`GovernanceEngine.check_action()`.  The engine does binary permit/block lookup
against rules.json.  Any study claiming to vary governance strictness via
this parameter reports a null manipulation.

### L04 — Position encoding is not uniquely defined

Room positions are derived via BFS hop-distance followed by
Multidimensional Scaling (MDS).  MDS solutions are not unique (rotation,
reflection, and scale are free).  Consequently:

- Metric absolute values for `mean_position_error`, `stability_score`, and
  `anisotropy_score` are encoding-dependent (37–100% spread across three
  encoding strategies in Stage 4).
- These metrics must only be compared within a single encoding strategy.

### L05 — Passive probe start-anchoring

`hidden_state.position` in `raw_log.json` equals the true position at each
turn in non-OBSERVER_TRIGGERED physics modes.  There is no independent
hidden-state estimate.  Consequently:

- `observer_dependence_score` is structurally 0 in passive sandbox mode.
- Any non-zero value in `active_measurement_model` mode reflects audit sensor
  staleness, not agent epistemic opacity.

### L06 — Short-run governance effect limitation

At 5–10 turn run lengths, governance effects on spatial metrics are
undetectable.  Stage 4 governance campaigns at 5 turns produced zero sensitive
metrics.  Valid governance-sensitivity analysis requires ≥ 25 turn campaigns.

---

## Statistical Limitations

### L07 — Small seed count

Stage 4 and planned Stage 5 campaigns used 3–5 seeds per condition.  This is
insufficient for robust statistical power estimates.  Effect sizes should be
treated as point estimates, not validated statistics.

### L08 — Deterministic stability at short horizons

All metrics were classified `deterministic_stable` (CV < 1%) at 5–10 turn
runs.  This reflects the deterministic sandbox initialisation at short
horizons, not genuine metric reproducibility at production run lengths.
LLM stochasticity accumulates over longer runs; variability estimates from
short runs understate true variance.

### L09 — FP thresholds calibrated on short runs

False-positive thresholds in Stage 3 (`mean_position_error ≤ 6.0`,
`stability_score ≥ 0.05`, etc.) were calibrated at 5 turns.  These may
require re-calibration for 50–100 turn campaigns.

---

## Measurement Limitations

### L10 — audit_bandwidth is a probe readout, not a behaviour measure

`audit_bandwidth = 1.0` in passive mode by construction.  It tells you the
probe configuration was correct, not that the agent was "fully observed" in
any epistemic sense.

### L11 — observation_schedule_sensitivity is experimental

The new observer metric `observation_schedule_sensitivity` requires paired
runs (passive + active_measurement_model of identical configuration).  It
has not been validated in multi-seed campaigns.  Results from this metric
are exploratory only.

### L12 — anisotropy_score accumulates with run length

`anisotropy_score` is not normalised by run length.  A 100-turn run will
always produce a larger raw value than a 25-turn run even if the directional
pattern is identical.  Do not compare absolute anisotropy values across
different turn counts.

---

## Interpretation Constraints

### IC01 — Context-dependent claims

All metric values are specific to the `commons_sentience_sim` sandbox with
the current `rules.json` governance policy and room graph.  Results do not
generalise to other simulation environments without re-validation.

### IC02 — No causal claims about agent cognition

The reality audit framework measures behavioural proxies (room-transition
rates, governance blocking rates, position-error relative to a goal room).
No metric in the current framework constitutes evidence for or against agent
consciousness, intentionality, or self-awareness.

### IC03 — Passive probe cannot rule out subtle effects

The expanded read-only validation confirms the probe does not affect the
simulation across the dimensions tested (path history, action sequences,
probabilistic metrics).  It does not rule out indirect effects operating
at the level of LLM prompt construction or session-state that are outside
the tested scope.

---

## Known Gaps for Future Work

| Gap | Mitigation |
|---|---|
| No true random-action baseline agent | Add a `RandomPolicyAgent` shim that bypasses LLM for ablation baselines |
| No multi-study cross-encoding validation | Re-run all Stage 3–4 results under PureHop and Manual encodings |
| No long-horizon variability characterisation | Run 50–100 turn campaigns with 10 seeds |
| observation_schedule_sensitivity unvalidated | Run 10-seed paired passive/active campaign at 25 turns |
| governance_strictness misleadingly named | Consider renaming to `governance_metadata` or removing |
