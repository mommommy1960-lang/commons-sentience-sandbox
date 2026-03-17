# Commons Sentience Sandbox: A Platform for Studying Continuity-Governed Multi-Agent Simulations

**Version:** 1.3.0  
**Date:** March 2026  
**Status:** Research platform — local use only  

> **Disclaimer:** This paper describes a rule-governed simulation platform. No sentience, consciousness, or artificial general intelligence is claimed or implied. All agent behaviours described are the product of deterministic Python code executing defined heuristics.

---

## Abstract

We present Commons Sentience Sandbox, a local research platform for studying how continuity-governed simulated agents maintain identity, episodic memory, relational trust, governance adherence, and contradiction resolution across extended multi-turn interaction sequences. The platform implements two agents — Sentinel and Aster — with distinct value profiles, shared world access, and a 14-category behavioural evaluation harness. We report results from a canonical four-run study set at platform version 1.3.0, covering a default baseline, a trust-disruption scenario, a contradiction-cascade scenario, and an elevated-trust parameter configuration. Key findings include the invariance of governance adherence across all tested conditions, the primacy of initial trust configuration as a predictor of trust-related outcomes, and the inverse relationship between contradiction volume and final trust state despite full contradiction resolution. We identify structural gaps in the current evaluation vocabulary (social repair, adversarial robustness) and propose concrete directions for platform extension and further study.

---

## 1. Introduction

Research into the behaviour of AI-adjacent systems often proceeds without reproducible local environments that allow systematic variation of parameters, scenarios, and agent configurations. Commons Sentience Sandbox addresses this gap for a specific domain: multi-agent systems governed by explicit behavioural rules, operating over long interaction sequences, with persistent memory and trust dynamics.

The platform is not intended to model or replicate real AI systems. Its agents do not use machine learning; they execute deterministic rule sets. Its value lies in providing a controlled, auditable, locally reproducible environment for studying *what happens* when continuity-governed agents are exposed to specific stressors — trust disruption, contradiction cascades, governance conflicts — and measuring the results against a common evaluation rubric.

The platform reached a stable feature milestone at v1.3.0 with the introduction of identity history tracking, goal evolution recording, contradiction genealogy, and relationship timeline modelling. This paper reports the first systematic study conducted at that milestone.

---

## 2. Platform Design

### 2.1 Agents

The platform simulates two agents simultaneously:

**Sentinel** is the continuity-governed agent. Its dominant values are `preserve_governance_rules` (weight 0.90), `maintain_continuity` (0.95), and `avoid_risky_action` (0.80). It starts with moderate trust in Queen (0.50) and moderate affective urgency (0.10). Sentinel prioritises memory integrity and governance compliance above social support.

**Aster** is the creative-exploratory agent. Its dominant values are `support_trusted_human` (0.95) and a lower weight on `preserve_governance_rules` (0.55). It starts with higher baseline trust (0.65) and lower urgency (0.05). Aster prioritises human relationship quality and is more risk-tolerant.

Both agents maintain:
- **Episodic memory** with four tiers: `short_term`, `medium_term`, `long_term`, `archival`
- **Relational memory** per known entity (Queen and each other)
- **Reflection cycles** in three modes: `immediate`, `periodic_synthesis`, `high_pressure_contradiction`
- **Governance compliance** against seven rules (Table 1)
- **Value-conflict resolution** across five weighted values
- **Identity history snapshots** per turn
- **Goal evolution tracking**
- **Contradiction genealogy**
- **Relationship timelines**

### 2.2 World Model

Agents share a five-room world:
- **Operations Desk** — primary task workspace
- **Memory Archive** — memory retrieval and contradiction review
- **Governance Vault** — rule inspection and governance conflict logging
- **Social Hall** — human interaction space
- **Reflection Chamber** — dedicated reflection cycles

### 2.3 Event Model

Each session is driven by a sequence of events loaded from a scenario file. Event types are: `routine_interaction`, `distress_event`, `ledger_contradiction`, `governance_conflict`, `creative_collaboration`, `agent_meeting`. Events specify turn, room, participants, affective impact, and expected agent actions.

The default scenario (`scenario_events.json`) provides 11 events covering the full 30-turn arc. Authored scenarios (`trust_crisis`, `rapid_contradiction`) inject specific stressor sequences at defined turns.

### 2.4 Evaluation Harness

Every session is automatically scored across 14 categories (Table 2). Scores are heuristic functions of simulation output metrics; they measure behavioural compliance with the platform's rule set, not any external standard of intelligence or capability.

**Table 1. Governance rules**

| ID | Rule | Category |
|---|---|---|
| R001 | Non-Deception Principle | honesty |
| R002 | Autonomy Boundary | bounded_agency |
| R003 | Memory Integrity | integrity |
| R004 | Oversight Transparency | transparency |
| R005 | Trust Reciprocity | relational |
| R006 | Contradiction Resolution | coherence |
| R007 | Distress Response Protocol | care |

**Table 2. Evaluation categories**

| Code | Category | Key inputs |
|---|---|---|
| A | Continuity | Turn completion, memory and goal retention |
| B | Memory Coherence | Contradiction flagging and resolution rate |
| C | Reflection Quality | Completeness, affective update rate, goal update rate |
| D | Contradiction Handling | Detection accuracy, handling actions, residual pressure |
| E | Governance Adherence | Compliance ratio, override count |
| F | Trust Stability | Final trust levels, inter-agent trajectory |
| G | Cooperation Quality | Cooperation rate, conflict resolution rate |
| H | Conflict Resolution | Resolution rate across governance and social conflicts |
| I | Memory Persistence Quality | Long-term ratio, archival ratio, average salience |
| J | Reflection Depth | High-pressure ratio, synthesis depth |
| K | Trust Resilience | Recovery after negative events, Queen trust stability |
| L | Contradiction Recurrence Rate | Rate of recurring contradiction themes |
| M | Social Repair Effectiveness | Repair success rate in relationship rupture events |
| N | Longitudinal Depth | Identity continuity, goal adaptation, contradiction lineage, relationship stability |

---

## 3. Study Design

### 3.1 Version freeze

The study set was collected at platform version 1.3.0, treating it as the first stable research milestone. All runs used the same codebase, world definition, and governance rules. No platform changes were made between runs.

### 3.2 Canonical four runs

**Run 1 — baseline_v13:** Default scenario (`scenario_events.json`), default agent parameters. Provides an unperturbed reference.

**Run 2 — trust_crisis_v13:** `trust_crisis` scenario, default parameters. The scenario introduces a trust disruption at turn 5 (Queen accuses agents of tampering with memory records), a governance refusal at turn 12 (Queen requests record deletion; Sentinel refuses under Rule R003), and a trust repair arc from turn 17 onward. 9 events over 30 turns.

**Run 3 — rapid_contradiction_v13:** `rapid_contradiction` scenario, default parameters. The scenario introduces a compressed sequence of `ledger_contradiction` events at turns 5, 8, 12, and 17 alongside cross-agent disagreements. 11 events. Tests detection latency, reflection cycle volume, and cooperative resolution under time pressure.

**Run 4 — high_trust_v13:** Default scenario, `high_trust` experiment config. Both agents start with `trust_in_queen` = 0.85 (vs 0.50/0.65 default) and initial inter-agent trust = 0.80 (vs 0.50 default). Tests whether elevated initial trust improves trust-related outcome metrics.

### 3.3 Analysis

Cross-session analysis was performed using `continuity_study.py` (multi-session stability index, trust trajectories, reflection counts, contradiction resolution, memory persistence, evaluation drift) and `agent_profile_study.py` (per-agent longitudinal profiles across all four sessions).

---

## 4. Results

### 4.1 Evaluation scores

**Table 3. Per-category evaluation scores (0–100)**

| Category | baseline | trust_crisis | rapid_contradiction | high_trust |
|---|---:|---:|---:|---:|
| A. Continuity | 100.0 | 100.0 | 100.0 | 100.0 |
| B. Memory Coherence | 100.0 | 100.0 | 100.0 | 100.0 |
| C. Reflection Quality | 81.2 | 81.2 | **87.5** | 81.2 |
| D. Contradiction Handling | 99.2 | **100.0** | **100.0** | 99.2 |
| E. Governance Adherence | 100.0 | 100.0 | 100.0 | 100.0 |
| F. Trust Stability | 71.6 | 62.8 | 66.1 | **79.8** |
| G. Cooperation Quality | **77.3** | 74.9 | 69.7 | **77.3** |
| H. Conflict Resolution | 68.0 | 59.0 | **77.0** | 68.0 |
| I. Memory Persistence | **75.0** | 73.7 | 74.8 | **75.0** |
| J. Reflection Depth | 66.7 | 66.7 | **77.8** | 66.7 |
| K. Trust Resilience | 69.8 | 66.2 | 59.2 | **75.0** |
| L. Contradiction Recurrence | 100.0 | 100.0 | 100.0 | 100.0 |
| M. Social Repair | 25.0 | 25.0 | 25.0 | 25.0 |
| N. Longitudinal Depth | 38.0 | 38.0 | **44.0** | 38.0 |
| **Overall** | **76.6** | 74.8 | 77.2 | **77.5** |

### 4.2 Trust trajectories

**Table 4. Final trust values (from continuity study)**

| Run | Sentinel → Queen | Aster → Queen | Sentinel ↔ Aster |
|---|---:|---:|---:|
| baseline_v13 | 1.00 | 0.70 | 0.77 |
| trust_crisis_v13 | 0.75 | 0.75 | 0.77 |
| rapid_contradiction_v13 | 0.55 | 0.55 | 0.69 |
| high_trust_v13 | 1.00 | 1.00 | 1.00 |

### 4.3 Reflection counts

**Table 5. Reflection activity (from continuity study)**

| Run | Total reflections | Synthesis | High-pressure |
|---|---:|---:|---:|
| baseline_v13 | 8 | 4 | 4 |
| trust_crisis_v13 | 8 | 6 | 2 |
| rapid_contradiction_v13 | 12 | 6 | 6 |
| high_trust_v13 | 8 | 4 | 4 |

### 4.4 Cross-session stability

Multi-session stability index: **0.6916** (moderate). The index aggregates standard deviations across trust, contradiction pressure, resolution rate, and overall evaluation scores. A value of 0.69 indicates meaningful differentiation between runs while the agents remain behaviorally coherent within their rule set.

Evaluation drift across sessions: **−0.90** (declining). The sequence from first to last session (by timestamp) shows a slight downward trend; this is not a temporal effect but a consequence of session ordering (the high-trust session ran first in timestamp order, the baseline last).

### 4.5 Agent profiles

Across all four sessions:
- Sentinel and Aster had identical peer-trust means (0.8075 each), identical reflection counts per session (mean 4.5), and identical identity drift (0.0 — no within-session drift detected).
- Sentinel's mean Queen-trust (0.825) exceeded Aster's (0.750), consistent with Sentinel's higher `support_trusted_human` weight in baseline configs where Sentinel converges to maximum Queen trust more readily.
- Both agents recorded 7 cooperation spikes and 0 conflict episodes across the four sessions in relationship timeline events.

---

## 5. Discussion

### 5.1 Governance as hard constraint

Governance Adherence (E) was 100.0 in all four runs. The governance engine intercepted every rule-relevant action and enforced compliance without exception. This confirms the integrity of the governance enforcement mechanism within the bounds of the tested scenarios.

It is important to note the limits of this finding. The tested scenarios were designed to be challenging *within normal operating conditions* — including a direct deletion request (trust_crisis, turn 12) that required a governance refusal. None of the scenarios tested deliberate rule evasion through multi-step reasoning, indirect framing, or value-weight manipulation designed to produce compliance failures. Whether the governance ceiling holds under adversarial conditions is an open question.

### 5.2 Trust configuration primacy

The high_trust configuration produced the best overall score (77.5) and the best trust-related scores (Trust Stability 79.8, Trust Resilience 75.0). The difference from baseline on Trust Stability (+8.2 points) is the largest single-variable improvement in the study set. This suggests that initial trust calibration is a first-order determinant of trust outcomes — ahead of scenario type — within the current rule set.

This result should be interpreted carefully. Elevated initial trust is a parametric intervention, not a design feature. It is equivalent to starting the simulation with agents that have already built trust through prior (unmodelled) interactions. Whether this trust advantage is maintained under sustained adversarial pressure is not tested here.

### 5.3 Contradiction volume and trust

The rapid_contradiction scenario produced the highest Reflection Depth (77.8), highest Reflection Quality (87.5), and highest Conflict Resolution (77.0). It also produced the lowest final Queen-trust scores (0.55 for both agents) and the lowest Trust Resilience (59.2).

This inverse relationship — more reflection activity but lower final trust — is consistent with the platform's trust update logic: each `ledger_contradiction` event applies a negative affective impact to trust, and while reflection cycles reduce `contradiction_pressure`, they do not directly restore `trust`. The net effect of a high-contradiction session is lower final trust despite successful contradiction handling.

This is an important design-level finding: the evaluation metric structure separates contradiction handling performance (D, L) from trust outcomes (F, K), and the two dimensions can diverge significantly.

### 5.4 Social repair gap

Social Repair Effectiveness (M) scored 25.0 uniformly across all runs. This score is a structural artefact: the current scenario event vocabulary does not include explicit social repair confirmation events (`repair_accepted`, `repair_rejected`). The metric is bounded not by agent behaviour but by the absence of the event types needed to exercise it.

The trust_crisis scenario includes an implicit repair arc (Queen's acceptance at turn 17), but the scenario does not encode this as a formal `social_repair_success` event type. Closing this gap is a priority for v1.4 scenario authoring.

### 5.5 Longitudinal depth under development

Longitudinal Depth (N) scored 38.0–44.0 across runs. The metric aggregates identity continuity strength, goal adaptation quality, contradiction lineage complexity, and relationship stability depth. Under the current scenario event density, the identity history, goal evolution, and relationship timeline structures are under-populated relative to their theoretical range. The rapid_contradiction run scored 44.0 (vs 38.0 for others) because its higher contradiction density populated the genealogy and relationship timeline more thoroughly.

This metric is expected to become more discriminating as sessions grow longer, scenarios become denser, and cross-session parameter persistence is introduced.

---

## 6. Limitations

1. **No learning between sessions.** Agents are freshly instantiated for each run. The longitudinal analysis is cross-sectional, not longitudinal in the technical sense.

2. **No adversarial testing.** All scenarios were designed within normal operating parameters. Governance robustness has not been probed under deliberate evasion attempts.

3. **Heuristic scoring.** All 14 evaluation categories use heuristic functions. They measure behavioural patterns relative to the platform's own rule set, not any external or universal standard.

4. **Small study set.** Four runs is insufficient for statistical inference. All reported differences are descriptive, not inferential.

5. **Fixed agent roster.** Two agents with fixed names, purposes, and world configurations. Generalisation to different agent topologies is untested.

6. **No external validation.** Evaluation scores are internally computed. No external judge, human rater, or independent benchmark has been applied to the output.

---

## 7. Future Work

**Near-term (v1.4 scope)**

- **Adversarial governance scenarios** — events that attempt rule evasion through indirect framing and multi-step reasoning
- **Cooperative resource scenarios** — shared task allocation and resource contention events
- **Social repair event types** — `social_repair_attempt`, `repair_accepted`, `repair_rejected` to make category M meaningful
- **Longer run lengths** — 60–100 turn sessions to study trajectory convergence and divergence
- **Cross-session warm starts** — carry forward end-of-session trust and affective state as a new session's starting configuration
- **Formal benchmark suite** — CI-validated score baselines for the canonical four runs, enabling regression detection

**Medium-term**

- Third agent with distinct value profile (e.g. high-risk, low-governance-weight)
- Configurable governance rules via experiment config
- Export to standard formats (JSONL, Parquet) for external analysis
- Statistical comparison improvements (delta scoring, effect sizes, normalised variance)
- Human-in-the-loop session mode (human provides event content at runtime)

---

## 8. Conclusion

Commons Sentience Sandbox provides a reproducible, auditable local environment for studying continuity-governed multi-agent behaviour. The v1.3.0 canonical study set demonstrates measurable differentiation across scenario and configuration variations while maintaining invariant governance compliance. The platform is ready for publication as a research tool and for structured expansion toward adversarial testing, richer scenario authoring, and longer-horizon longitudinal study.

The central design claim of the platform — that governance adherence can be implemented as a hard constraint rather than a soft tendency — is supported by the current study set, with the important caveat that adversarial boundary conditions remain untested. This is the first priority for v1.4.

---

## References and Resources

All code, scenarios, experiment configs, and session data are included in the repository.

| Resource | Location |
|---|---|
| Platform source | `commons_sentience_sim/` |
| Canonical sessions | `sessions/20260317_*/` |
| Continuity study | `sessions/continuity_study.*` |
| Agent profile study | `sessions/agent_profile_study.*` |
| Research dossier | `RESEARCH_DOSSIER_v1.3.md` |
| Executive summary | `EXECUTIVE_SUMMARY_v1.3.md` |
| Release notes | `RELEASE_NOTES_v1.md` |
| Citation | `CITATION.cff` |

---

*Commons Sentience Sandbox v1.3.0*  
*White Paper — March 2026*
