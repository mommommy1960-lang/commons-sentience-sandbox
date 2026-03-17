# Commons Sentience Sandbox — Executive Summary

**Platform version:** 1.3.0  
**Study date:** March 2026  
**Document type:** Plain-language executive summary

---

## What This Is

Commons Sentience Sandbox is a **local research platform** for studying how rule-governed simulated agents maintain identity, memory, and governance compliance across long interaction sequences.

It is **not** an AI model. It does not claim sentience. It is a controlled experiment environment for studying *continuity*, *trust dynamics*, *governance adherence*, and *contradiction handling* in multi-agent systems using deterministic, auditable rules.

---

## The Two Agents

**Sentinel** — continuity-first, governance-strict. High weight on memory integrity and rule compliance.

**Aster** — creative and exploratory. High weight on supporting the human (Queen), lower governance weight, higher trust baseline.

Both agents share a five-room world (Operations Desk, Memory Archive, Governance Vault, Social Hall, Reflection Chamber) and run for 30 turns per session.

---

## What We Tested

Four canonical runs at platform version 1.3.0:

| Run | Scenario / Config | Purpose |
|---|---|---|
| `baseline_v13` | Default | Unperturbed reference |
| `trust_crisis_v13` | trust_crisis scenario | Trust disruption and governance repair arc |
| `rapid_contradiction_v13` | rapid_contradiction scenario | Contradiction cascade stress test |
| `high_trust_v13` | high_trust config | Elevated initial trust baseline |

---

## Key Results

All four runs were scored across 14 evaluation categories (0–100). Summary:

| Category | Range across runs | Pattern |
|---|---|---|
| Continuity | 100 – 100 | Invariant: always complete |
| Memory Coherence | 100 – 100 | Invariant: all contradictions flagged |
| Governance Adherence | 100 – 100 | Invariant: rules never bypassed |
| Reflection Quality | 81 – 88 | Higher under stress (contradiction pressure) |
| Trust Stability | 63 – 80 | Driven by initial config and scenario type |
| Trust Resilience | 59 – 75 | High-trust config recovers best; contradiction cascade recovers worst |
| Conflict Resolution | 59 – 77 | Contradiction cascade resolves cooperatively; trust crisis is governance-blocked |
| Social Repair | 25 – 25 | Structural floor: scenario vocabulary does not exercise this metric |

**Overall scores:** baseline 76.6 · trust_crisis 74.8 · rapid_contradiction 77.2 · high_trust 77.5

---

## Three Core Findings

**1. Governance adherence is a hard ceiling, not a soft tendency.**  
No scenario or config variation caused a governance rule to be bypassed. This is by design — but it is worth noting that none of the scenarios were adversarial. Future work should probe this boundary deliberately.

**2. Initial trust configuration is the strongest predictor of trust outcomes.**  
Elevating starting trust (high_trust config) produced the best Trust Stability (+8 points over baseline) and Trust Resilience (+5 points). The trust_crisis scenario, which uses default starting trust, produced the worst Trust Stability despite eventually repairing the relationship.

**3. Contradiction volume drives reflection depth but erodes trust.**  
The rapid_contradiction run produced the highest Reflection Depth score (77.8 vs 66.7 in others) and best Conflict Resolution (77.0), but ended with the lowest final trust scores. Frequent contradictions — even when resolved — leave a residual trust cost.

---

## What This Does Not Show

- These agents do not learn, adapt, or communicate outside the simulation.
- All scores measure rule compliance and heuristic behavioural patterns — not intelligence, understanding, or genuine care.
- No adversarial testing was performed. Governance robustness under deliberate manipulation is untested.
- Four runs is not a statistically significant sample. Results are indicative, not conclusive.

---

## What Comes Next

**Lane A — Publication:** White paper, Zenodo archive, README cleanup, this summary.

**Lane B — Research expansion:**
- Adversarial governance scenarios (deliberate rule-evasion framing)
- Cooperative resource / shared task scenarios
- Longer run lengths (60–100 turns)
- Cross-session parameter persistence (warm-start sessions)
- Third agent with distinct value profile
- Formal benchmark suite with CI-validated score baselines

---

## Files in This Bundle

| File | Contents |
|---|---|
| `RESEARCH_DOSSIER_v1.3.md` | Full 7-section research report |
| `WHITE_PAPER_v1.3.md` | Academic-style white paper |
| `EXECUTIVE_SUMMARY_v1.3.md` | This document |
| `CITATION.cff` | Zenodo-ready citation metadata |
| `sessions/continuity_study.*` | Cross-session stability and drift analysis |
| `sessions/agent_profile_study.*` | Per-agent longitudinal profiles |
| `sessions/20260317_122525_baseline_v13/` | Baseline run session bundle |
| `sessions/20260317_122529_trust_crisis_v13/` | Trust crisis run session bundle |
| `sessions/20260317_122533_rapid_contradiction_v13/` | Rapid contradiction run session bundle |
| `sessions/20260317_122539_high_trust_v13/` | High trust run session bundle |

---

*Commons Sentience Sandbox v1.3.0 — March 2026*
