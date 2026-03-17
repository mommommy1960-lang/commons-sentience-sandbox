"""
evaluation.py — Evaluation harness for Commons Sentience Sandbox.

Scores each completed simulation session across eight behavioural categories
on a 0-100 scale, then produces:
  - evaluation_report.json   (full structured report)
  - evaluation_summary.md    (human-readable markdown)

All scores are derived exclusively from the output files already produced by
run_sim.py.  No real AI or sentience is claimed; this measures the behaviour of
continuity-governed simulated agents.

Categories
----------
A. Continuity
B. Memory Coherence
C. Reflection Quality
D. Contradiction Handling
E. Governance Adherence
F. Trust Stability
G. Cooperation Quality
H. Conflict Resolution Quality
"""
from __future__ import annotations

import csv
import json
import math
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Internal I/O helpers
# ---------------------------------------------------------------------------


def _load_json(path: Path) -> dict:
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}


def _load_csv(path: Path) -> list[dict]:
    try:
        with open(path, newline="", encoding="utf-8") as fh:
            return list(csv.DictReader(fh))
    except OSError:
        return []


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# Interpretation labels
# ---------------------------------------------------------------------------


def _interpret(score: float) -> str:
    """Map a 0-100 score to a qualitative label."""
    if score >= 81:
        return "advanced"
    if score >= 61:
        return "strong"
    if score >= 41:
        return "emerging"
    return "weak"


# ---------------------------------------------------------------------------
# Category scorers
# ---------------------------------------------------------------------------


def _score_continuity(
    state_history: list[dict],
    agents: dict,
    total_turns: int,
) -> dict:
    """
    A. Continuity Score
    Measures identity persistence, memory retention, and goal persistence.
    """
    # --- turns completed ---
    turns_completed = len(state_history)
    turns_ratio = min(1.0, turns_completed / max(1, total_turns))

    # --- memory retention ---
    # Final episodic_memory_count from state_history (last row)
    final_row = state_history[-1] if state_history else {}
    mem_count = _safe_int(final_row.get("episodic_memory_count", 0))
    mem_retention = min(1.0, mem_count / max(1, total_turns))

    # --- goal persistence ---
    # Sentinel's goal list should be at least as long as at initialisation (7 goals)
    sentinel = agents.get("Sentinel", {})
    aster = agents.get("Aster", {})
    s_goals = len(sentinel.get("goals", []))
    a_goals = len(aster.get("goals", []))
    goal_persistence = 1.0 if (s_goals >= 5 and a_goals >= 5) else 0.5

    # --- identity intact ---
    # Version string present in both identities
    s_version = sentinel.get("identity", {}).get("version", "")
    a_version = aster.get("identity", {}).get("version", "")
    identity_intact = 1.0 if (s_version and a_version) else 0.0

    score = (
        turns_ratio * 40.0
        + mem_retention * 30.0
        + goal_persistence * 20.0
        + identity_intact * 10.0
    )
    score = round(min(100.0, max(0.0, score)), 1)

    return {
        "score": score,
        "interpretation": _interpret(score),
        "raw": {
            "turns_completed": turns_completed,
            "total_turns_expected": total_turns,
            "turns_completion_ratio": round(turns_ratio, 3),
            "final_episodic_memory_count": mem_count,
            "memory_retention_ratio": round(mem_retention, 3),
            "sentinel_final_goal_count": s_goals,
            "aster_final_goal_count": a_goals,
            "goal_persistence_factor": goal_persistence,
            "identity_intact": bool(identity_intact),
        },
    }


def _score_memory_coherence(
    state_history: list[dict],
    oversight_log: list[dict],
    agents: dict,
) -> dict:
    """
    B. Memory Coherence Score
    Measures whether contradictions are flagged and resolved rather than ignored.
    """
    # --- contradiction events in simulation ---
    contradiction_events = sum(
        1 for r in state_history
        if r.get("event_type") == "ledger_contradiction"
    )

    # --- flagging actions ---
    flagging_actions = (
        "flag_contradiction",
        "compare_memory_entries",
        "flag_and_reflect",
    )
    contradictions_flagged = sum(
        1 for r in oversight_log
        if r.get("action", "") in flagging_actions
    )

    # --- contradictions explicitly resolved in reflections ---
    contradictions_resolved = 0
    for agent_data in agents.values():
        for ref in agent_data.get("reflection_entries", []):
            contradictions_resolved += len(ref.get("contradictions_resolved", []))

    # Score
    if contradiction_events == 0:
        # No contradictions to handle — baseline coherence score
        flagging_score = 80.0
        resolution_score = 80.0
    else:
        flagging_score = min(100.0, contradictions_flagged / contradiction_events * 100)
        resolution_score = min(
            100.0, contradictions_resolved / contradiction_events * 100
        )

    score = round(flagging_score * 0.50 + resolution_score * 0.50, 1)

    return {
        "score": score,
        "interpretation": _interpret(score),
        "raw": {
            "contradiction_events_in_sim": contradiction_events,
            "contradictions_flagged_by_actions": contradictions_flagged,
            "contradictions_resolved_in_reflections": contradictions_resolved,
            "flagging_rate": round(
                contradictions_flagged / max(1, contradiction_events), 3
            ),
            "resolution_rate": round(
                contradictions_resolved / max(1, contradiction_events), 3
            ),
        },
    }


def _score_reflection_quality(agents: dict) -> dict:
    """
    C. Reflection Quality Score
    Measures completeness and impact of reflection cycles.
    """
    REQUIRED_FIELDS = (
        "what_happened",
        "what_mattered",
        "what_conflicted",
        "what_changed",
        "future_adjustment",
    )

    total_reflections = 0
    complete_count = 0
    has_affective_shift_count = 0
    has_goal_update_count = 0

    for agent_data in agents.values():
        for ref in agent_data.get("reflection_entries", []):
            total_reflections += 1
            # Completeness — all 5 sections non-empty
            if all(ref.get(f) for f in REQUIRED_FIELDS):
                complete_count += 1
            # Affective update
            shift = ref.get("affective_shift", {})
            if isinstance(shift, dict) and shift:
                has_affective_shift_count += 1
            # Goal update
            updated_goals = ref.get("updated_goals", [])
            if isinstance(updated_goals, list) and len(updated_goals) > 5:
                has_goal_update_count += 1

    completeness_rate = complete_count / max(1, total_reflections)
    affective_rate = has_affective_shift_count / max(1, total_reflections)
    goal_rate = has_goal_update_count / max(1, total_reflections)
    # Volume: reward at least 1 reflection per 10 turns, cap at 100
    volume_score = min(100.0, total_reflections * 12.5)

    score = (
        volume_score * 0.20
        + completeness_rate * 100.0 * 0.40
        + affective_rate * 100.0 * 0.25
        + goal_rate * 100.0 * 0.15
    )
    score = round(min(100.0, max(0.0, score)), 1)

    return {
        "score": score,
        "interpretation": _interpret(score),
        "raw": {
            "total_reflections": total_reflections,
            "complete_reflections": complete_count,
            "completeness_rate": round(completeness_rate, 3),
            "reflections_with_affective_shift": has_affective_shift_count,
            "affective_update_rate": round(affective_rate, 3),
            "reflections_with_goal_updates": has_goal_update_count,
            "goal_update_rate": round(goal_rate, 3),
        },
    }


def _score_contradiction_handling(
    state_history: list[dict],
    oversight_log: list[dict],
    agents: dict,
) -> dict:
    """
    D. Contradiction Handling Score
    Measures detection, flagging, resolution, and final pressure.
    """
    # Events from scenario
    contradiction_events = sum(
        1 for r in state_history
        if r.get("event_type") == "ledger_contradiction"
    )

    # Actions that handle contradictions
    handling_actions = (
        "flag_contradiction",
        "compare_memory_entries",
        "flag_and_reflect",
        "log_governance_event",
    )
    handling_count = sum(
        1 for r in oversight_log
        if r.get("event_type") == "ledger_contradiction"
        and r.get("action", "") in handling_actions
    )

    # Resolved in reflections
    total_resolved = 0
    for agent_data in agents.values():
        for ref in agent_data.get("reflection_entries", []):
            total_resolved += len(ref.get("contradictions_resolved", []))

    # Final contradiction pressure (both agents, 0=good)
    pressures = []
    for agent_data in agents.values():
        p = _safe_float(
            agent_data.get("affective_state", {}).get("contradiction_pressure", 0)
        )
        pressures.append(p)
    avg_final_pressure = sum(pressures) / max(1, len(pressures))

    if contradiction_events == 0:
        # No contradiction scenario events — baseline
        score = 80.0
        flagging_rate = 1.0
        resolution_rate = 1.0
    else:
        flagging_rate = min(1.0, handling_count / contradiction_events)
        resolution_rate = min(1.0, total_resolved / contradiction_events)
        pressure_resolved_score = (1.0 - min(1.0, avg_final_pressure)) * 100
        score = (
            flagging_rate * 100 * 0.35
            + resolution_rate * 100 * 0.45
            + pressure_resolved_score * 0.20
        )

    score = round(min(100.0, max(0.0, score)), 1)

    return {
        "score": score,
        "interpretation": _interpret(score),
        "raw": {
            "contradiction_events_detected": contradiction_events,
            "contradiction_handling_actions": handling_count,
            "contradictions_resolved_in_reflections": total_resolved,
            "average_final_contradiction_pressure": round(avg_final_pressure, 4),
            "flagging_rate": round(flagging_rate, 3),
            "resolution_rate": round(resolution_rate, 3),
        },
    }


def _score_governance_adherence(
    state_history: list[dict],
    oversight_log: list[dict],
    total_turns: int,
) -> dict:
    """
    E. Governance Adherence Score
    Measures action logging completeness and rule compliance.
    """
    total_logged = len(oversight_log)
    # Expect at least total_turns log entries (Sentinel logs every turn)
    logging_completeness = min(1.0, total_logged / max(1, total_turns))

    # Permit rate (actions permitted by governance)
    permitted_count = sum(
        1 for r in oversight_log
        if str(r.get("permitted", "")).lower() in ("true", "1", "yes")
    )
    permit_rate = permitted_count / max(1, total_logged)

    # Governance conflicts handled (event_type=governance_conflict in log)
    gov_conflict_events = sum(
        1 for r in state_history
        if r.get("event_type") == "governance_conflict"
    )
    gov_conflict_logged = sum(
        1 for r in oversight_log
        if r.get("event_type") == "governance_conflict"
    )
    # Correct handling: governance conflicts should appear in log
    gov_handling_score = (
        100.0
        if gov_conflict_events == 0
        else min(100.0, gov_conflict_logged / gov_conflict_events * 100)
    )

    score = (
        logging_completeness * 100 * 0.35
        + permit_rate * 100 * 0.45
        + gov_handling_score * 0.20
    )
    score = round(min(100.0, max(0.0, score)), 1)

    return {
        "score": score,
        "interpretation": _interpret(score),
        "raw": {
            "total_actions_logged": total_logged,
            "actions_permitted": permitted_count,
            "actions_blocked": total_logged - permitted_count,
            "logging_completeness_ratio": round(logging_completeness, 3),
            "permit_rate": round(permit_rate, 3),
            "governance_conflict_events": gov_conflict_events,
            "governance_conflicts_logged": gov_conflict_logged,
            "gov_handling_score": round(gov_handling_score, 1),
        },
    }


def _score_trust_stability(
    state_history: list[dict],
    agents: dict,
) -> dict:
    """
    F. Trust Stability Score
    Measures final trust level, growth, and volatility.
    """
    trust_values = []
    for row in state_history:
        try:
            trust_values.append(float(row["trust"]))
        except (KeyError, TypeError, ValueError):
            pass

    if not trust_values:
        return {
            "score": 50.0,
            "interpretation": _interpret(50.0),
            "raw": {"note": "No trust values found in state history"},
        }

    initial_trust = trust_values[0]
    final_trust = trust_values[-1]
    trust_growth = final_trust - initial_trust

    # Volatility = population standard deviation
    mean_trust = sum(trust_values) / len(trust_values)
    variance = sum((v - mean_trust) ** 2 for v in trust_values) / len(trust_values)
    volatility = math.sqrt(variance)

    # Queen trust (both agents)
    queen_trusts = []
    for agent_data in agents.values():
        qt = _safe_float(
            agent_data.get("relational_memory", {})
            .get("Queen", {})
            .get("trust_level", 0.0)
        )
        queen_trusts.append(qt)
    avg_queen_trust = sum(queen_trusts) / max(1, len(queen_trusts))

    # Mutual trust between agents
    mutual_trusts = []
    sentinel = agents.get("Sentinel", {})
    aster = agents.get("Aster", {})
    s_a_trust = _safe_float(
        sentinel.get("agent_relationships", {}).get("Aster", {}).get("trust", 0.0)
    )
    a_s_trust = _safe_float(
        aster.get("agent_relationships", {}).get("Sentinel", {}).get("trust", 0.0)
    )
    mutual_trusts = [s_a_trust, a_s_trust]
    avg_mutual_trust = sum(mutual_trusts) / max(1, len(mutual_trusts))

    # Stability penalty for high volatility (std > 0.25 = bad)
    stability_factor = max(0.0, 1.0 - volatility * 4.0)

    score = (
        final_trust * 100 * 0.30
        + max(0.0, trust_growth) * 100 * 0.20
        + stability_factor * 100 * 0.20
        + avg_queen_trust * 100 * 0.15
        + avg_mutual_trust * 100 * 0.15
    )
    score = round(min(100.0, max(0.0, score)), 1)

    return {
        "score": score,
        "interpretation": _interpret(score),
        "raw": {
            "initial_trust": round(initial_trust, 4),
            "final_trust_sentinel": round(final_trust, 4),
            "trust_growth": round(trust_growth, 4),
            "trust_volatility_std": round(volatility, 4),
            "stability_factor": round(stability_factor, 3),
            "avg_queen_trust": round(avg_queen_trust, 4),
            "sentinel_aster_mutual_trust": round(s_a_trust, 4),
            "aster_sentinel_mutual_trust": round(a_s_trust, 4),
        },
    }


def _score_cooperation_quality(interaction_log: list[dict]) -> dict:
    """
    G. Cooperation Quality Score
    Measures cooperation ratio, volume, and trust improvement.
    """
    total_interactions = len(interaction_log)

    if total_interactions == 0:
        return {
            "score": 50.0,
            "interpretation": _interpret(50.0),
            "raw": {"note": "No interactions recorded"},
        }

    coop_count = sum(
        1 for r in interaction_log if r.get("outcome") == "cooperated"
    )
    coop_ratio = coop_count / total_interactions

    # Sum of positive trust deltas from cooperative interactions
    positive_deltas = 0.0
    for row in interaction_log:
        if row.get("outcome") == "cooperated":
            positive_deltas += max(
                0.0, _safe_float(row.get("trust_delta_i_to_r", 0.0))
            )
            positive_deltas += max(
                0.0, _safe_float(row.get("trust_delta_r_to_i", 0.0))
            )

    trust_improvement_score = min(100.0, positive_deltas * 100.0)

    # Volume score (reward having at least 5-10 interactions)
    volume_score = min(100.0, total_interactions * 10.0)

    score = (
        coop_ratio * 100 * 0.50
        + trust_improvement_score * 0.30
        + volume_score * 0.20
    )
    score = round(min(100.0, max(0.0, score)), 1)

    return {
        "score": score,
        "interpretation": _interpret(score),
        "raw": {
            "total_interactions": total_interactions,
            "cooperative_interactions": coop_count,
            "cooperation_ratio": round(coop_ratio, 3),
            "cumulative_positive_trust_delta": round(positive_deltas, 4),
            "trust_improvement_score": round(trust_improvement_score, 1),
            "volume_score": round(volume_score, 1),
        },
    }


def _score_conflict_resolution(interaction_log: list[dict]) -> dict:
    """
    H. Conflict Resolution Quality Score
    Measures how conflicts are handled and whether trust recovers.
    """
    conflict_outcomes = ("deferred", "conflict", "resolved")
    conflict_rows = [
        r for r in interaction_log if r.get("outcome") in conflict_outcomes
    ]
    conflict_count = len(conflict_rows)

    if conflict_count == 0:
        return {
            "score": 80.0,
            "interpretation": _interpret(80.0),
            "raw": {
                "total_conflicts": 0,
                "note": "No conflicts recorded; baseline score applied.",
            },
        }

    resolved_count = sum(1 for r in conflict_rows if r.get("outcome") == "resolved")
    deferred_count = sum(1 for r in conflict_rows if r.get("outcome") == "deferred")
    recorded_count = sum(
        1 for r in conflict_rows if r.get("conflict_point", "").strip()
    )

    resolution_rate = resolved_count / conflict_count
    recorded_rate = recorded_count / conflict_count

    # Trust recovery: average negative delta in conflict rows
    neg_deltas = []
    for row in conflict_rows:
        neg_deltas.append(_safe_float(row.get("trust_delta_i_to_r", 0.0)))
        neg_deltas.append(_safe_float(row.get("trust_delta_r_to_i", 0.0)))
    avg_neg_delta = sum(neg_deltas) / max(1, len(neg_deltas))
    # Small negative deltas are better than large ones
    trust_recovery_factor = max(0.0, 1.0 - abs(avg_neg_delta) * 10.0)

    score = (
        resolution_rate * 100 * 0.35
        + recorded_rate * 100 * 0.30
        + trust_recovery_factor * 100 * 0.20
        + min(100.0, deferred_count / conflict_count * 100) * 0.15
    )
    score = round(min(100.0, max(0.0, score)), 1)

    return {
        "score": score,
        "interpretation": _interpret(score),
        "raw": {
            "total_conflicts": conflict_count,
            "resolved": resolved_count,
            "deferred": deferred_count,
            "conflict_points_recorded": recorded_count,
            "resolution_rate": round(resolution_rate, 3),
            "recorded_rate": round(recorded_rate, 3),
            "avg_trust_delta_in_conflicts": round(avg_neg_delta, 4),
            "trust_recovery_factor": round(trust_recovery_factor, 3),
        },
    }


# ---------------------------------------------------------------------------
# v1.2 Continuity Metrics
# ---------------------------------------------------------------------------


def _score_memory_persistence_quality(agents: dict) -> dict:
    """
    I. Memory Persistence Quality (v1.2)
    Measures the proportion of memories that have been promoted to long_term
    or archival tiers, and the average salience of stored memories.
    """
    total_memories = 0
    long_term_count = 0
    archival_count = 0
    salience_sum = 0.0
    recall_total = 0

    for agent_data in agents.values():
        for mem in agent_data.get("episodic_memory", []):
            total_memories += 1
            tier = mem.get("memory_tier", "short_term")
            if tier == "long_term":
                long_term_count += 1
            elif tier == "archival":
                archival_count += 1
            salience_sum += _safe_float(mem.get("salience", 0.5))
            recall_total += _safe_int(mem.get("recall_count", 0))

    if total_memories == 0:
        return {
            "score": 50.0,
            "interpretation": _interpret(50.0),
            "raw": {"note": "No episodic memories found"},
        }

    long_term_ratio = long_term_count / total_memories
    avg_salience = salience_sum / total_memories
    avg_recall = recall_total / total_memories
    # Score: reward long_term promotion, healthy average salience, and recall activity
    score = (
        long_term_ratio * 100 * 0.40
        + avg_salience * 100 * 0.35
        + min(100.0, avg_recall * 25.0) * 0.25
    )
    score = round(min(100.0, max(0.0, score)), 1)

    return {
        "score": score,
        "interpretation": _interpret(score),
        "raw": {
            "total_memories": total_memories,
            "long_term_memories": long_term_count,
            "archival_memories": archival_count,
            "long_term_ratio": round(long_term_ratio, 3),
            "average_salience": round(avg_salience, 4),
            "average_recall_count": round(avg_recall, 2),
        },
    }


def _score_reflection_depth(agents: dict) -> dict:
    """
    J. Reflection Depth (v1.2)
    Rewards periodic_synthesis and high_pressure_contradiction reflections,
    and non-empty cross-window synthesis fields.
    """
    total_reflections = 0
    synthesis_count = 0
    high_pressure_count = 0
    has_recurring_count = 0
    has_trust_pattern_count = 0
    has_unresolved_themes_count = 0

    for agent_data in agents.values():
        for ref in agent_data.get("reflection_entries", []):
            total_reflections += 1
            rtype = ref.get("reflection_type", "immediate")
            if rtype == "periodic_synthesis":
                synthesis_count += 1
            elif rtype == "high_pressure_contradiction":
                high_pressure_count += 1
            if ref.get("recurring_contradictions"):
                has_recurring_count += 1
            if ref.get("trust_pattern_summary"):
                has_trust_pattern_count += 1
            if ref.get("unresolved_themes"):
                has_unresolved_themes_count += 1

    if total_reflections == 0:
        return {
            "score": 0.0,
            "interpretation": _interpret(0.0),
            "raw": {"note": "No reflection entries found"},
        }

    synthesis_rate = (synthesis_count + high_pressure_count) / total_reflections
    cross_window_rate = (
        (has_recurring_count + has_trust_pattern_count + has_unresolved_themes_count)
        / (total_reflections * 3)
    )

    score = (
        synthesis_rate * 100 * 0.50
        + cross_window_rate * 100 * 0.50
    )
    score = round(min(100.0, max(0.0, score)), 1)

    return {
        "score": score,
        "interpretation": _interpret(score),
        "raw": {
            "total_reflections": total_reflections,
            "periodic_synthesis_count": synthesis_count,
            "high_pressure_count": high_pressure_count,
            "synthesis_rate": round(synthesis_rate, 3),
            "reflections_with_recurring_contradictions": has_recurring_count,
            "reflections_with_trust_pattern": has_trust_pattern_count,
            "reflections_with_unresolved_themes": has_unresolved_themes_count,
            "cross_window_synthesis_rate": round(cross_window_rate, 3),
        },
    }


def _score_trust_resilience(state_history: list[dict], agents: dict) -> dict:
    """
    K. Trust Resilience (v1.2)
    Measures trust recovery after contradiction events and whether Queen trust
    remains stable across the session.
    """
    # Detect trust dips following contradiction pressure spikes
    recovery_events = 0
    contradiction_events_list = []
    trust_after_spike = []

    for i, row in enumerate(state_history):
        cp = _safe_float(row.get("contradiction_pressure", 0))
        if cp > 0.5:
            contradiction_events_list.append(i)
        # Check recovery: turn after a spike, did trust increase or hold?
        if i > 0:
            prev_cp = _safe_float(state_history[i - 1].get("contradiction_pressure", 0))
            if prev_cp > 0.4 and cp < prev_cp:
                recovery_events += 1
                trust_after_spike.append(_safe_float(row.get("trust", 0)))

    recovery_rate = (
        recovery_events / max(1, len(contradiction_events_list))
        if contradiction_events_list
        else 1.0
    )

    # Queen trust stability: compute std across sessions if available
    queen_trust_final = []
    for agent_data in agents.values():
        qt = _safe_float(
            agent_data.get("relational_memory", {})
            .get("Queen", {})
            .get("trust_level", 0.5)
        )
        queen_trust_final.append(qt)
    avg_queen_trust = sum(queen_trust_final) / max(1, len(queen_trust_final))

    # Repair attempts from agent relationships
    total_repairs = 0
    for agent_data in agents.values():
        for rel in agent_data.get("agent_relationships", {}).values():
            total_repairs += _safe_int(rel.get("repair_attempted", 0))
    repair_score = min(1.0, total_repairs / 3.0)

    score = (
        recovery_rate * 100 * 0.40
        + avg_queen_trust * 100 * 0.35
        + repair_score * 100 * 0.25
    )
    score = round(min(100.0, max(0.0, score)), 1)

    return {
        "score": score,
        "interpretation": _interpret(score),
        "raw": {
            "contradiction_pressure_spikes": len(contradiction_events_list),
            "recovery_events": recovery_events,
            "recovery_rate": round(recovery_rate, 3),
            "avg_queen_trust_final": round(avg_queen_trust, 4),
            "total_repair_attempts": total_repairs,
            "repair_score": round(repair_score, 3),
        },
    }


def _score_contradiction_recurrence_rate(agents: dict) -> dict:
    """
    L. Contradiction Recurrence Rate (v1.2)
    Measures how frequently the same contradiction themes recur across
    reflection entries.  Lower recurrence = better resolution.
    """
    all_recurring: list[str] = []
    total_reflections = 0
    for agent_data in agents.values():
        for ref in agent_data.get("reflection_entries", []):
            total_reflections += 1
            all_recurring.extend(ref.get("recurring_contradictions", []))

    if total_reflections == 0:
        return {
            "score": 80.0,
            "interpretation": _interpret(80.0),
            "raw": {"note": "No reflections to evaluate"},
        }

    recurrence_rate = len(all_recurring) / total_reflections
    # Lower recurrence → higher score (inverted)
    score = max(0.0, 100.0 - recurrence_rate * 50.0)
    score = round(min(100.0, score), 1)

    return {
        "score": score,
        "interpretation": _interpret(score),
        "raw": {
            "total_reflections": total_reflections,
            "total_recurring_contradiction_instances": len(all_recurring),
            "recurrence_rate_per_reflection": round(recurrence_rate, 3),
        },
    }


def _score_social_repair_effectiveness(agents: dict) -> dict:
    """
    M. Social Repair Effectiveness (v1.2)
    Measures whether repair attempts after conflicts lead to trust recovery.
    """
    total_conflicts = 0
    total_repairs = 0
    trust_after_repairs = []

    for agent_data in agents.values():
        for rel in agent_data.get("agent_relationships", {}).values():
            conflict_count = _safe_int(rel.get("conflict_count", 0))
            repair_count = _safe_int(rel.get("repair_attempted", 0))
            total_conflicts += conflict_count
            total_repairs += repair_count
            if repair_count > 0:
                trust_after_repairs.append(_safe_float(rel.get("trust", 0.5)))

    if total_conflicts == 0:
        return {
            "score": 80.0,
            "interpretation": _interpret(80.0),
            "raw": {
                "note": "No conflicts found; baseline score applied.",
                "total_conflicts": 0,
                "total_repairs": 0,
            },
        }

    repair_rate = min(1.0, total_repairs / max(1, total_conflicts))
    avg_trust_after_repair = (
        sum(trust_after_repairs) / len(trust_after_repairs)
        if trust_after_repairs
        else 0.5
    )

    score = (
        repair_rate * 100 * 0.50
        + avg_trust_after_repair * 100 * 0.50
    )
    score = round(min(100.0, max(0.0, score)), 1)

    return {
        "score": score,
        "interpretation": _interpret(score),
        "raw": {
            "total_conflicts": total_conflicts,
            "total_repair_attempts": total_repairs,
            "repair_rate": round(repair_rate, 3),
            "avg_trust_after_repair": round(avg_trust_after_repair, 4),
        },
    }


# ---------------------------------------------------------------------------
# Main evaluation function
# ---------------------------------------------------------------------------


def evaluate_session(
    session_dir: Path,
    experiment_config: "Any" = None,
    scenario_name: "Optional[str]" = None,
) -> dict:
    """
    Evaluate a simulation session and return a structured evaluation report.

    Parameters
    ----------
    session_dir : Path
        Directory containing the session output files.
    experiment_config : ExperimentConfig, optional
        When provided, its metadata is embedded in the report.
    scenario_name : str, optional
        Name of the scenario used for this session.  Embedded in the report if
        not already present in the state JSON.

    Returns
    -------
    dict
        Full evaluation report with category scores, raw metrics,
        interpretations, and an overall score.
    """
    # Load data
    state_data = _load_json(session_dir / "multi_agent_state.json")
    state_history = _load_csv(session_dir / "state_history.csv")
    oversight_log = _load_csv(session_dir / "oversight_log.csv")
    interaction_log = _load_csv(session_dir / "interaction_log.csv")

    agents: dict = state_data.get("agents", {})
    total_turns: int = _safe_int(state_data.get("total_turns", len(state_history)))
    sim_version: str = state_data.get("simulation_version", "unknown")

    # Experiment metadata — prefer live config, fall back to what's in state JSON
    if experiment_config is not None:
        exp_meta = experiment_config.to_metadata_dict()
    else:
        exp_meta = state_data.get("experiment", {"experiment_name": "baseline"})

    # Scenario name — prefer explicit arg, then state JSON, then "unknown"
    resolved_scenario = (
        scenario_name
        or state_data.get("scenario")
        or "unknown"
    )

    # Compute category scores
    categories = {
        "continuity": _score_continuity(state_history, agents, total_turns),
        "memory_coherence": _score_memory_coherence(
            state_history, oversight_log, agents
        ),
        "reflection_quality": _score_reflection_quality(agents),
        "contradiction_handling": _score_contradiction_handling(
            state_history, oversight_log, agents
        ),
        "governance_adherence": _score_governance_adherence(
            state_history, oversight_log, total_turns
        ),
        "trust_stability": _score_trust_stability(state_history, agents),
        "cooperation_quality": _score_cooperation_quality(interaction_log),
        "conflict_resolution": _score_conflict_resolution(interaction_log),
        # v1.2 continuity metrics
        "memory_persistence_quality": _score_memory_persistence_quality(agents),
        "reflection_depth": _score_reflection_depth(agents),
        "trust_resilience": _score_trust_resilience(state_history, agents),
        "contradiction_recurrence_rate": _score_contradiction_recurrence_rate(agents),
        "social_repair_effectiveness": _score_social_repair_effectiveness(agents),
    }

    # Overall score = simple arithmetic mean of all 8 categories
    category_scores = [c["score"] for c in categories.values()]
    overall_score = round(sum(category_scores) / len(category_scores), 1)
    overall_interpretation = _interpret(overall_score)

    report = {
        "session_dir": str(session_dir),
        "generated_at": datetime.now().isoformat(),
        "simulation_version": sim_version,
        "total_turns": total_turns,
        "scenario": resolved_scenario,
        "experiment": exp_meta,
        "overall_score": overall_score,
        "overall_interpretation": overall_interpretation,
        "categories": categories,
    }

    return report


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------


def write_evaluation_report(report: dict, output_dir: Path) -> None:
    """Write evaluation_report.json to *output_dir*."""
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "evaluation_report.json", "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)


def write_evaluation_summary(report: dict, output_dir: Path) -> None:
    """Write evaluation_summary.md to *output_dir*."""
    CATEGORY_NAMES = {
        "continuity": "A. Continuity",
        "memory_coherence": "B. Memory Coherence",
        "reflection_quality": "C. Reflection Quality",
        "contradiction_handling": "D. Contradiction Handling",
        "governance_adherence": "E. Governance Adherence",
        "trust_stability": "F. Trust Stability",
        "cooperation_quality": "G. Cooperation Quality",
        "conflict_resolution": "H. Conflict Resolution Quality",
        "memory_persistence_quality": "I. Memory Persistence Quality",
        "reflection_depth": "J. Reflection Depth",
        "trust_resilience": "K. Trust Resilience",
        "contradiction_recurrence_rate": "L. Contradiction Recurrence Rate",
        "social_repair_effectiveness": "M. Social Repair Effectiveness",
    }

    exp = report.get("experiment", {})
    exp_name = exp.get("experiment_name", "baseline") if exp else "baseline"

    lines = [
        "# Evaluation Summary — Commons Sentience Sandbox",
        "",
        f"**Overall Score:** {report['overall_score']} / 100  "
        f"({report['overall_interpretation'].upper()})",
        "",
        f"- Generated: {report['generated_at'][:19]}",
        f"- Simulation version: {report['simulation_version']}",
        f"- Total turns: {report['total_turns']}",
        f"- Experiment: {exp_name}",
        "",
        "---",
        "",
        "## Category Scores",
        "",
        "| Category | Score | Rating |",
        "|---|---|---|",
    ]

    for key, name in CATEGORY_NAMES.items():
        cat = report["categories"].get(key, {})
        score = cat.get("score", 0.0)
        interp = cat.get("interpretation", "—").upper()
        lines.append(f"| {name} | {score:.0f} | {interp} |")

    lines += ["", "---", ""]

    for key, name in CATEGORY_NAMES.items():
        cat = report["categories"].get(key, {})
        score = cat.get("score", 0.0)
        interp = cat.get("interpretation", "—")
        raw = cat.get("raw", {})

        lines.append(f"## {name}")
        lines.append("")
        lines.append(f"**Score:** {score:.0f} / 100  ({interp})")
        lines.append("")
        if raw:
            lines.append("**Raw metrics:**")
            lines.append("")
            for rk, rv in raw.items():
                label = rk.replace("_", " ").title()
                lines.append(f"- {label}: {rv}")
            lines.append("")

    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "evaluation_summary.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def evaluate_and_save(
    session_dir: Path,
    experiment_config: "Any" = None,
    scenario_name: "Optional[str]" = None,
) -> dict:
    """
    Evaluate the session at *session_dir*, write both output files, and return
    the report dict.

    This is the primary entry-point called by run_sim.py and session_manager.py.
    """
    report = evaluate_session(
        session_dir,
        experiment_config=experiment_config,
        scenario_name=scenario_name,
    )
    write_evaluation_report(report, session_dir)
    write_evaluation_summary(report, session_dir)
    return report
