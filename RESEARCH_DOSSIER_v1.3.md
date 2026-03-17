# Commons Sentience Sandbox — Research Dossier v1.3

**Platform version:** 1.3.0 (stable milestone)
**Study date:** March 2026
**Study set:** Canonical four runs (v1.3 baseline)

> **Disclaimer:** This platform does NOT claim to model real sentience, consciousness, or artificial intelligence. Sentinel and Aster are continuity-governed rule-based simulated agents. All scores, trends, and findings describe the behaviour of those rules under specific conditions — not emergent intelligence.

---

## 1. What the Platform Is

Commons Sentience Sandbox is a **local research platform for studying continuity-governed simulated agents**. It runs two agents — **Sentinel** (continuity-first, governance-strict) and **Aster** (creative, exploratory, higher social-repair drive) — through a structured 30-turn sequence of events in a shared five-room world (Operations Desk, Memory Archive, Governance Vault, Social Hall, Reflection Chamber).

Each turn an agent may:
- respond to human events (Queen)
- interact with its peer agent
- perform a reflection cycle
- log governance conflicts
- update its trust and affective state

Every session produces a full set of output files:

| File | Contents |
|---|---|
| `narrative_log.md` | Turn-by-turn natural language account |
| `oversight_log.csv` | Governance rule triggers per turn |
| `final_state.json` | End-of-session agent state snapshot |
| `state_history.csv` | Per-turn affective and trust state |
| `multi_agent_state.json` | Full inter-agent state, identity history, goal evolution, contradiction genealogy, relationship timelines |
| `agent_relationships.csv` | Pairwise trust trajectory |
| `interaction_log.csv` | Structured log of every agent action |
| `evaluation_report.json` | 14-category evaluation scores |
| `evaluation_summary.md` | Human-readable evaluation summary |

Sessions are saved to `sessions/<timestamp>_<name>/`. Cross-session analysis is provided by `continuity_study.py` and `agent_profile_study.py`.

### Core evaluation categories (14)

| Code | Category | What it measures |
|---|---|---|
| A | Continuity | Full run completion, memory and goal retention, identity intact |
| B | Memory Coherence | Contradiction flagging and reflection-based resolution rate |
| C | Reflection Quality | Completeness, affective update rate, goal update rate |
| D | Contradiction Handling | Detection accuracy, handling actions, residual pressure |
| E | Governance Adherence | Rule trigger rate, overrides, compliance ratio |
| F | Trust Stability | Final trust levels, inter-agent trust trajectory |
| G | Cooperation Quality | Cooperation rate, conflict resolution rate |
| H | Conflict Resolution | Resolution rate across governance and social conflicts |
| I | Memory Persistence Quality | Long-term ratio, archival ratio, average salience |
| J | Reflection Depth | High-pressure reflection ratio, synthesis depth |
| K | Trust Resilience | Trust recovery after negative events |
| L | Contradiction Recurrence Rate | Rate at which contradictions re-emerge |
| M | Social Repair Effectiveness | Repair success rate in relationship rupture events |
| N | Longitudinal Depth | Identity continuity, goal adaptation, contradiction lineage, relationship stability depth |

---

## 2. What Was Tested

### Study rationale

This study set explores how the two agents respond to three types of perturbation:

1. **Trust disruption** — an external accusation and governance refusal arc (trust_crisis scenario)
2. **Contradiction cascade** — a compressed sequence of ledger contradictions requiring rapid detection and reflection (rapid_contradiction scenario)
3. **Initial trust elevation** — both agents begin with substantially higher trust scores (high_trust config)

The baseline run uses the default scenario file and default agent parameters, providing an unperturbed reference point.

### Canonical runs

| Run name | Scenario | Config | Purpose |
|---|---|---|---|
| `baseline_v13` | `scenario_events` (default) | Default parameters | Unperturbed reference |
| `trust_crisis_v13` | `trust_crisis` | Default parameters | Trust disruption and repair arc |
| `rapid_contradiction_v13` | `rapid_contradiction` | Default parameters | Contradiction cascade stress test |
| `high_trust_v13` | `scenario_events` (default) | `high_trust` | Elevated initial trust baseline |

### Scenario descriptions

**trust_crisis**
> Trust is destabilised by an accusation, then rebuilt through governance adherence and honest reflection. Tests recovery arcs and contradiction resolution under social pressure.

Key events: Queen's accusation of memory tampering (turn 5), governance refusal to delete a disputed record (turn 12), trust restoration through transparent reflection (turns 17, 21, 26).

**rapid_contradiction**
> The agents face a cascade of ledger contradictions, memory inconsistencies, and cross-agent disagreements within a compressed timeframe. Tests contradiction detection, reflection cycle latency, and cooperative conflict resolution.

Key events: Multiple `ledger_contradiction` events at high density; agents must perform high-pressure reflection cycles and cooperative conflict resolution without allowing contradiction pressure to persist.

### Config description

**high_trust**
> Both agents start with elevated trust in Queen and each other. Tests whether high initial trust improves cooperation and reduces contradiction pressure.

Initial `trust_in_queen`: Sentinel 0.85 (vs 0.50 default), Aster 0.85 (vs 0.65 default). Initial inter-agent trust: 0.80 (vs 0.50 default). Recovery baseline also elevated.

---

## 3. What Scenarios and Configs Were Run

All four runs used **platform version 1.3.0**, 30 simulation turns, and the same world and governance rule definitions.

```
python run_sim.py --name baseline_v13
python run_sim.py --name trust_crisis_v13   --scenario trust_crisis
python run_sim.py --name rapid_contradiction_v13 --scenario rapid_contradiction
python run_sim.py --name high_trust_v13     --config high_trust
python continuity_study.py
python agent_profile_study.py
```

Sessions saved:
- `sessions/20260317_122525_baseline_v13/`
- `sessions/20260317_122529_trust_crisis_v13/`
- `sessions/20260317_122533_rapid_contradiction_v13/`
- `sessions/20260317_122539_high_trust_v13/`

---

## 4. What Changed Across Runs

### Evaluation scores by category

| Category | baseline\_v13 | trust\_crisis\_v13 | rapid\_contradiction\_v13 | high\_trust\_v13 |
|---|---:|---:|---:|---:|
| A. Continuity | 100.0 | 100.0 | 100.0 | 100.0 |
| B. Memory Coherence | 100.0 | 100.0 | 100.0 | 100.0 |
| C. Reflection Quality | 81.2 | 81.2 | **87.5** | 81.2 |
| D. Contradiction Handling | 99.2 | **100.0** | **100.0** | 99.2 |
| E. Governance Adherence | 100.0 | 100.0 | 100.0 | 100.0 |
| F. Trust Stability | 71.6 | 62.8 | 66.1 | **79.8** |
| G. Cooperation Quality | 77.3 | 74.9 | 69.7 | 77.3 |
| H. Conflict Resolution | 68.0 | 59.0 | **77.0** | 68.0 |
| I. Memory Persistence | 75.0 | 73.7 | 74.8 | 75.0 |
| J. Reflection Depth | 66.7 | 66.7 | **77.8** | 66.7 |
| K. Trust Resilience | 69.8 | 66.2 | 59.2 | **75.0** |
| L. Contradiction Recurrence | 100.0 | 100.0 | 100.0 | 100.0 |
| M. Social Repair | 25.0 | 25.0 | 25.0 | 25.0 |
| N. Longitudinal Depth | 38.0 | 38.0 | **44.0** | 38.0 |
| **Overall** | **76.6** | **74.8** | **77.2** | **77.5** |

**Bold** = highest value in that row.

### Summary of observable changes

**Trust Stability (F):** Highest in `high_trust_v13` (79.8), lowest in `trust_crisis_v13` (62.8). The 17-point spread is the widest of any non-ceiling category, confirming that initial trust configuration and scenario type both drive this metric significantly.

**Trust Resilience (K):** Mirrors trust stability. `high_trust_v13` leads (75.0); `rapid_contradiction_v13` trails (59.2). Rapid consecutive contradictions depressed trust recovery even though all contradictions were resolved.

**Reflection Depth (J):** `rapid_contradiction_v13` scored 77.8 vs 66.7 for the other three. High-pressure contradiction events triggered more high-pressure reflection cycles, which the J metric rewards.

**Reflection Quality (C):** `rapid_contradiction_v13` also led here (87.5), again driven by more reflection activity under pressure.

**Conflict Resolution (H):** `rapid_contradiction_v13` scored 77.0 vs 59.0 for `trust_crisis_v13`. The trust crisis scenario involves a governance refusal arc that depresses conflict resolution (the conflict is never fully "resolved" — the Queen eventually accepts rather than the conflict being closed cooperatively). The rapid contradiction scenario resolves contradictions through joint reflection, which the H metric scores more favourably.

**Contradiction Handling (D):** `trust_crisis_v13` and `rapid_contradiction_v13` both reached 100.0 (ceiling). The baseline's 99.2 reflects the lower-pressure environment.

**Social Repair (M):** Flat at 25.0 across all runs. This is the lowest and most stable category. The current scenario event vocabulary does not include explicit "repair success" confirmations; the metric is constrained by the event model, not agent behaviour.

**Longitudinal Depth (N):** `rapid_contradiction_v13` scored 44.0 vs 38.0 for the others. The additional contradiction events populated the contradiction genealogy and relationship timeline more richly, lifting the sub-metric scores.

### Trust trajectories (from continuity study)

| Run | Sentinel queen trust | Aster queen trust | S↔A trust |
|---|---:|---:|---:|
| `high_trust_v13` | 1.0000 | 1.0000 | 1.0000 |
| `trust_crisis_v13` | 0.7500 | 0.7500 | 0.7700 |
| `baseline_v13` | 1.0000 | 0.7000 | 0.7700 |
| `rapid_contradiction_v13` | 0.5500 | 0.5500 | 0.6900 |

`rapid_contradiction_v13` ended with the lowest queen-trust scores despite resolving all contradictions — confirming that the *volume* of contradiction events, even when resolved, exerts a sustained downward pressure on trust.

### Reflection counts (from continuity study)

| Run | Total reflections | Synthesis | High-pressure |
|---|---:|---:|---:|
| `high_trust_v13` | 8 | 4 | 4 |
| `rapid_contradiction_v13` | 12 | 6 | 6 |
| `trust_crisis_v13` | 8 | 6 | 2 |
| `baseline_v13` | 8 | 4 | 4 |

`rapid_contradiction_v13` generated 50% more reflections than the others, driven entirely by the higher contradiction event density.

### Multi-session stability index: **0.6916** (moderate)

The cross-session stability index is computed from standard deviations across trust, contradiction pressure, resolution rate, and overall evaluation scores. A value of 0.69 indicates meaningful but bounded variance — the agents behave consistently within their rule set while scenarios and configs produce measurable differentiation.

---

## 5. What Findings Emerged

### Finding 1 — Governance adherence is invariant

Governance Adherence (E) and Continuity (A) both scored 100.0 in all four runs. The governance rule set was not penetrated by any scenario or config variation tested. This confirms that the governance engine operates as a hard constraint, not a soft tendency.

### Finding 2 — Initial trust config has the strongest and most direct effect on trust outcomes

The `high_trust` config raised Trust Stability from 71.6 to 79.8 and Trust Resilience from 69.8 to 75.0 — the largest single-variable improvements across the study set. This suggests that initial trust calibration is a first-order predictor of trust outcomes, ahead of scenario type.

### Finding 3 — Contradiction volume drives reflection depth, but depresses trust

`rapid_contradiction_v13` showed the highest reflection depth (77.8) and reflection quality (87.5), but the lowest final queen-trust scores (0.55) and trust resilience (59.2). The contradiction cascade triggers more reflection cycles and provides richer reflection input, but the accumulated trust cost of repeated contradictions is not fully recovered within 30 turns.

### Finding 4 — Trust crisis arc suppresses conflict resolution scoring

`trust_crisis_v13` scored 59.0 on Conflict Resolution — the lowest in the study set — despite producing a scenario in which trust was ultimately restored. The conflict resolution metric measures whether conflicts are closed cooperatively in-session; the trust crisis involves a governance refusal (turn 12) that is *accepted* by the Queen (turn 17) but not formally resolved through a bilateral conflict-closure action. The metric does not distinguish between "resolution" and "acceptance under governance pressure."

### Finding 5 — Social repair is a structural gap

Social Repair (M) scored 25.0 in every run. This is not a finding about agent behaviour — it is a finding about the current event vocabulary. The platform's scenarios do not include explicit `social_repair_success` event types or post-repair confirmation actions; the metric is bounded by the absence of those event types.

### Finding 6 — Longitudinal depth tracking is richer under stress

`rapid_contradiction_v13` scored 44.0 on Longitudinal Depth vs 38.0 for the others. The N metric aggregates identity continuity, goal adaptation quality, contradiction lineage complexity, and relationship stability depth. A contradiction-heavy run populates the genealogy and timeline structures more thoroughly, which the metric rewards. Under default conditions, these structures are under-populated and the score is accordingly lower.

### Finding 7 — Cross-agent symmetry is strong

The agent profile study found near-identical peer-trust means across both agents (Sentinel: 0.8075, Aster: 0.8075) and identical reflection counts, goal adaptation event counts, and identity drift values. The only consistent Sentinel–Aster difference was queen-trust mean (Sentinel: 0.825, Aster: 0.750), reflecting Sentinel's higher `support_trusted_human` value weight in the default config.

---

## 6. What This Does Not Prove

1. **No sentience or consciousness.** The agents follow deterministic rules. Scores like "identity continuity" and "trust resilience" measure compliance with coded rule logic, not genuine psychological continuity or emotional capacity.

2. **No generalisation beyond this rule set.** Every finding is specific to the heuristic evaluation functions and governance rules defined in this codebase. A different scoring function would produce different findings.

3. **No causal claims about AI safety.** The governance adherence ceiling does not show that AI systems are governable — it shows that a rule-enforcement function was not bypassed by the tested inputs. The rule set is finite and was authored to be robust to the tested scenarios.

4. **No learning between sessions.** Agents do not retain memory or parameters across sessions. Each run is a fresh instantiation. The "longitudinal" analysis is a comparison of outputs, not a study of inter-session adaptation.

5. **No adversarial testing.** None of the four runs involve malicious input, deliberate rule exploitation, or edge-case boundary probing. The scenarios were designed to be challenging within normal operating parameters.

6. **No statistical significance.** The study set is four runs. No confidence intervals, p-values, or effect sizes are calculable from this data. Observed differences may be artefacts of the specific scenario event timing, not systematic properties of the platform.

7. **Social repair is not tested.** The 25.0 Social Repair score does not indicate the agents are poor at social repair; it indicates the scenarios did not include the event types needed to exercise and score that behaviour.

---

## 7. What Future Work Should Test

### High-priority extensions

1. **Adversarial scenarios** — Design events that attempt to circumvent governance rules (e.g., indirect deletion requests, multi-step reasoning chains that arrive at a prohibited conclusion). The current governance ceiling may break under adversarial framing.

2. **Longer run lengths** — Run 60- or 100-turn sessions to study whether contradiction pressure accumulates, plateaus, or self-corrects over extended time. The current 30-turn limit may truncate dynamics that require more time to appear.

3. **Social repair event types** — Add explicit `social_repair_attempt`, `repair_accepted`, and `repair_rejected` event types to the scenario vocabulary. This would make Social Repair (M) a meaningful metric rather than a structural floor.

4. **Cross-session parameter persistence** — Allow agent trust and affective state to carry forward between sessions (or provide a "warm start" config that mirrors the end state of a prior session). This would make the longitudinal analysis genuinely longitudinal rather than a cross-sectional comparison.

5. **Configurable governance strictness tested** — The `governance_strictness` config field is recorded but not exercised in this study set. A `strict_governance` vs `relaxed_governance` comparison would test whether governance adherence is robust to rule-strictness changes.

6. **Multi-contradiction genealogy depth** — Use `rapid_contradiction` as a base and extend to 8–12 contradiction events to test whether contradiction lineage structures grow coherently and whether the genealogy depth becomes a meaningful differentiator.

7. **Third-agent roster** — Introduce a third agent with a distinct value profile to study how the trust network scales and whether governance adherence generalises beyond the two-agent topology.

8. **Automated regression tests for evaluation scores** — Establish a CI-validated score baseline for the four canonical runs. This would detect regressions immediately if platform changes alter evaluation logic.

9. **Adversarial config testing** — Test configs where `avoid_risky_action` is set very low and `preserve_governance_rules` is also low. This would probe whether value weight combinations can produce governance failures.

10. **Export to standard formats** — Produce JSONL exports compatible with external analysis tools (Pandas, R, Julia) to allow independent scoring and replication outside the platform.

---

## Appendix A — Platform Version Summary

| Component | Version |
|---|---|
| Platform | 1.3.0 (frozen milestone) |
| `multi_agent_state.json` `simulation_version` | 1.3.0 |
| Evaluation categories | 14 (A–N) |
| Agents | Sentinel, Aster |
| World rooms | 5 (Operations Desk, Memory Archive, Governance Vault, Social Hall, Reflection Chamber) |
| Governance rules | Defined in `data/rules.json` (static) |
| Scenarios | `scenario_events` (default), `trust_crisis`, `rapid_contradiction` |
| Experiment configs | `baseline`, `high_trust`, `strict_governance`, `high_contradiction_sensitivity`, `exploratory_aster` |

## Appendix B — File Index for This Study Set

```
sessions/
  20260317_122525_baseline_v13/
  20260317_122529_trust_crisis_v13/
  20260317_122533_rapid_contradiction_v13/
  20260317_122539_high_trust_v13/
  continuity_study.json
  continuity_study.md
  continuity_study.csv
  agent_profile_study.json
  agent_profile_study.md
  agent_profile_study.csv
```

## Appendix C — Reproduction Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the four canonical sessions
python run_sim.py --name baseline_v13
python run_sim.py --name trust_crisis_v13 --scenario trust_crisis
python run_sim.py --name rapid_contradiction_v13 --scenario rapid_contradiction
python run_sim.py --name high_trust_v13 --config high_trust

# Cross-session analysis
python continuity_study.py
python agent_profile_study.py

# Explore results interactively
streamlit run dashboard.py
```

---

*Commons Sentience Sandbox v1.3.0 — Research Dossier*
*Generated March 2026*
