# Frequently Asked Questions

---

### What is Reality Audit?

Reality Audit is a structured measurement layer attached to the
`commons_sentience_sim` sandbox.  It records quantitative metrics about
agent behaviour — room visits, blocked actions, trust dynamics, and
stability — on every simulation turn, then writes a summary report.  It is
designed to make sandbox results reproducible and comparable across
experimental conditions.

---

### Does the probe change the simulation?

No.  The production probe (`probe_mode = "passive"`) is strictly read-only.
It receives state snapshots from the simulation turn loop; it never calls
any method that modifies an agent, the world, or the governance engine.

We verify this with a control experiment (`control_experiments.py`) that
runs the same simulation twice — once with the probe enabled and once
without — and compares the final structural state of both agents (room,
affective state, memory count, trust scores).  The states match exactly on
deterministic fields.

The only fields that may legitimately differ between runs are LLM-generated
narrative text and reasoning strings, which vary even without the probe and
are explicitly excluded from the comparison.

---

### What do you mean by "observer effect" here?

In quantum physics, the observer effect refers to the fact that measuring a
system can change it.  In this project we use the term in two distinct senses:

1. **Empirical claim**: the production audit probe does *not* cause an
   observer effect.  It is read-only by construction and verified by
   control experiments.

2. **Methodological model**: in the `active_measurement_model` probe mode
   (an experimental, non-default mode) we *simulate* what a bandwidth-
   limited audit instrument would record if it could only sample the
   simulation periodically.  This is a model of hypothetical measurement
   intensity, not a change to the real simulation.

When we report `observer_dependence_score`, that number reflects whether
the audit's *recorded* view of agent positions diverged from the true
positions — a property of the audit instrument's sampling rate, not of the
simulation itself.

---

### Why translate continuous metrics into room-graph metrics?

The Reality Audit framework was originally designed for a continuous 2-D
physics simulation with positions, velocities, and forces.  The
`commons_sentience_sim` sandbox uses discrete rooms with no physical
coordinates.

Rather than building two completely separate metric systems, we bridge them:
BFS shortest-path distances between the five rooms are projected into a
stable 2-D plane using classical Multidimensional Scaling (MDS).  This
gives every room a unique (x, y) coordinate that preserves topological
neighbourhood, and allows all continuous metrics to be applied without
modification.

The tradeoff is that room-graph metrics are coarser than their continuous
equivalents.  See `docs/METRIC_MAPPING.md` for a complete mapping with
justifications and limitations.

---

### What counts as a null baseline?

A null baseline is a run where agent behaviour is essentially random or
uninformed — it establishes what audit metrics look like under "noise" rather
than intentional, goal-directed behaviour.

We provide two null baselines in `reality_audit/validation/baseline_agents.py`:

- **Random-walk**: control input is sampled uniformly at random at each step.
- **Uniform-policy**: always points toward the goal at half speed, with no
  correction or memory.

These run on the `RealityWorld` physics engine (not the full sandbox) so
they are fast, reproducible, and independent of LLM output.  Any sandbox
metric that falls within the range established by these baselines should be
treated as consistent with noise.

---

### What is currently validated vs still experimental?

| Component | Status |
|---|---|
| Room position encoder (MDS embedding) | ✅ Validated — deterministic, tested |
| SimProbe `passive` mode | ✅ Validated — read-only confirmed by control experiment |
| Toy scenarios A, B, C, D | ✅ Validated — metric directions match expectations |
| Null baselines (random-walk, uniform-policy) | ✅ Implemented and verified |
| Metric mapping to room-graph | ✅ Documented in `METRIC_MAPPING.md` |
| `active_measurement_model` probe mode | ⚠️ Experimental — models hypothetical bandwidth limits; conclusions limited to audit-layer sampling effects |
| Long-horizon (50–100 turn) runs | 🔬 Planned — not yet run at scale |
| Governance sensitivity analysis | 🔬 Planned |
| Cross-run carryover audit continuity | 🔬 Planned |

---

### How should collaborators interpret the results?

1. **Compare within, not between, graph versions.**  If the room graph
   changes (rooms added or removed), all MDS coordinates change and
   historical results are not comparable.

2. **Use the baseline as your noise floor.**  A metric value within the
   range of the random-walk baseline may reflect ordinary variance rather
   than a meaningful pattern.

3. **Check `probe_mode` in `summary.json`.**  Only results from `passive`
   mode carry the read-only guarantee.  Results from `active_measurement_model`
   describe a hypothetical measurement model.

4. **`observer_dependence_score` is always 0 in passive mode.**  A non-zero
   score in a report generated with `passive` mode is a bug, not a finding.

5. **Narrative text is not measured.**  The audit captures structural
   state — rooms, actions, affective values — not the quality or content
   of reasoning strings.  Narrative quality requires separate evaluation.

---

### Where is the source code?

| File | Purpose |
|---|---|
| `reality_audit/adapters/sim_probe.py` | Main probe class |
| `reality_audit/adapters/room_distance.py` | BFS + MDS room encoder |
| `reality_audit/validation/toy_experiments.py` | Reproducible benchmark scenarios |
| `reality_audit/validation/control_experiments.py` | Read-only proof framework |
| `reality_audit/validation/baseline_agents.py` | Null baseline runners |
| `reality_audit/analysis/plot_audit_results.py` | Visualisation utilities |
| `docs/METRIC_MAPPING.md` | Metric definitions and adaptations |
| `docs/ARCHITECTURE_OVERVIEW.md` | System diagram |
| `docs/PLAIN_LANGUAGE_SUMMARY.md` | Non-technical introduction |
| `run_sim.py` | Main simulation entrypoint (`--reality-audit` flag) |
