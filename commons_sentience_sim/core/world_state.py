"""
world_state.py — Persistent world-state layer for Commons Sentience Sandbox v1.6.

Tracks cross-run world conditions that survive between simulation runs:
  - room conditions
  - unresolved contradictions
  - environmental tensions
  - pending tasks
  - relationship climate
  - prior major events

Used by the --continue-from feature to restore world context to a new run.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


WORLD_STATE_FILENAME = "world_state.json"

# Room condition labels (can be layered)
ROOM_CONDITIONS = [
    "normal",
    "high_tension",
    "contradicted",
    "under_repair",
    "disrupted",
    "restored",
]


def build_world_state(
    world: Any,
    sentinel: Any,
    aster: Any,
    turn: int,
    run_label: str = "",
) -> dict:
    """Build a serialisable world-state snapshot from the current simulation.

    Parameters
    ----------
    world :
        The ``World`` instance from the simulation.
    sentinel :
        The Sentinel ``Agent`` instance.
    aster :
        The Aster ``Agent`` instance.
    turn :
        The final turn number of the simulation run.
    run_label :
        Optional human-readable label for this run (e.g. a session name or timestamp).

    Returns
    -------
    dict
        A fully JSON-serialisable world-state dict.
    """
    # ── Room conditions ──────────────────────────────────────────────────────
    room_conditions: Dict[str, dict] = {}
    for room_name, room in world.rooms.items():
        # Pull any stored condition from room metadata; default to "normal"
        condition = getattr(room, "condition", "normal")
        tension = getattr(room, "tension_level", 0.0)
        room_conditions[room_name] = {
            "condition": condition,
            "tension_level": round(tension, 4),
            "objects": {
                obj_name: obj.state
                for obj_name, obj in room.objects.items()
            },
        }

    # ── Unresolved contradictions (union across both agents) ─────────────────
    all_contradictions: List[str] = list(
        dict.fromkeys(
            sentinel.pending_contradictions + aster.pending_contradictions
        )
    )

    # Contradiction genealogy lineages
    contradiction_lineages: List[dict] = list(
        {
            entry["text"]: entry
            for entry in (
                sentinel.contradiction_genealogy + aster.contradiction_genealogy
            )
        }.values()
    )

    # ── Environmental tensions ────────────────────────────────────────────────
    # Derived from the union of unresolved contradiction pressures and high
    # affective urgency signals across both agents.
    s_urgency = sentinel.affective_state.get("urgency", 0.0)
    a_urgency = aster.affective_state.get("urgency", 0.0)
    s_cp = sentinel.affective_state.get("contradiction_pressure", 0.0)
    a_cp = aster.affective_state.get("contradiction_pressure", 0.0)
    environmental_tensions: Dict[str, float] = {
        "sentinel_urgency": round(s_urgency, 4),
        "aster_urgency": round(a_urgency, 4),
        "sentinel_contradiction_pressure": round(s_cp, 4),
        "aster_contradiction_pressure": round(a_cp, 4),
        "combined_tension": round(
            (s_urgency + a_urgency + s_cp + a_cp) / 4.0, 4
        ),
    }

    # ── Pending tasks ────────────────────────────────────────────────────────
    pending_tasks: List[str] = []
    for t in sentinel.task_planner.tasks:
        if not getattr(t, "completed", False):
            pending_tasks.append(
                f"[Sentinel] {getattr(t, 'name', str(t))}"
            )
    for t in aster.task_planner.tasks:
        if not getattr(t, "completed", False):
            pending_tasks.append(
                f"[Aster] {getattr(t, 'name', str(t))}"
            )

    # ── Relationship climate ─────────────────────────────────────────────────
    s_a_trust = sentinel.get_agent_trust("Aster")
    a_s_trust = aster.get_agent_trust("Sentinel")
    queen_s_trust = (
        sentinel.relational_memory.get("Queen", None)
    )
    queen_a_trust = (
        aster.relational_memory.get("Queen", None)
    )
    relationship_climate: dict = {
        "sentinel_trust_in_aster": round(s_a_trust, 4),
        "aster_trust_in_sentinel": round(a_s_trust, 4),
        "sentinel_trust_in_queen": round(
            queen_s_trust.trust_level if queen_s_trust else 0.0, 4
        ),
        "aster_trust_in_queen": round(
            queen_a_trust.trust_level if queen_a_trust else 0.0, 4
        ),
        "relationship_timelines": {
            k: v[-1] if v else {}
            for k, v in sentinel.relationship_timelines.items()
        },
        "sentinel_human_relationships": {
            name: {
                "trust_level": round(rm.trust_level, 4),
                "interaction_count": rm.interaction_count,
                "last_seen_turn": rm.last_seen_turn,
            }
            for name, rm in sentinel.relational_memory.items()
        },
        "aster_human_relationships": {
            name: {
                "trust_level": round(rm.trust_level, 4),
                "interaction_count": rm.interaction_count,
                "last_seen_turn": rm.last_seen_turn,
            }
            for name, rm in aster.relational_memory.items()
        },
    }

    # ── Prior major events (top-salience episodic memories) ─────────────────
    top_n = 10
    sentinel_top = sorted(
        sentinel.episodic_memory,
        key=lambda m: m.salience,
        reverse=True,
    )[:top_n]
    aster_top = sorted(
        aster.episodic_memory,
        key=lambda m: m.salience,
        reverse=True,
    )[:top_n]

    prior_major_events: List[dict] = []
    for mem in sentinel_top:
        prior_major_events.append({
            "agent": "Sentinel",
            "turn": mem.turn,
            "room": mem.room,
            "event_type": mem.event_type,
            "summary": mem.summary,
            "salience": round(mem.salience, 4),
            "emotional_resonance": mem.emotional_resonance,
            "tags": mem.tags,
        })
    for mem in aster_top:
        prior_major_events.append({
            "agent": "Aster",
            "turn": mem.turn,
            "room": mem.room,
            "event_type": mem.event_type,
            "summary": mem.summary,
            "salience": round(mem.salience, 4),
            "emotional_resonance": mem.emotional_resonance,
            "tags": mem.tags,
        })
    # Sort by salience descending
    prior_major_events.sort(key=lambda e: e["salience"], reverse=True)

    # ── Agent self-model summaries ───────────────────────────────────────────
    self_model_summaries: dict = {
        "Sentinel": _summarise_self_model(sentinel),
        "Aster": _summarise_self_model(aster),
    }

    # ── Unresolved themes (from recent reflections) ──────────────────────────
    unresolved_themes: List[str] = list(
        dict.fromkeys(
            _collect_unresolved_themes(sentinel)
            + _collect_unresolved_themes(aster)
        )
    )

    # ── v1.7 Active counterfactual plans ────────────────────────────────────
    active_plans: Dict[str, List[dict]] = {}
    for agent_ref in (sentinel, aster):
        planner = getattr(agent_ref, "counterfactual_planner", None)
        if planner is not None:
            agent_plans = [
                p.to_dict()
                for p in planner.future_plans
                if p.status == "active"
            ]
            if agent_plans:
                active_plans[agent_ref.identity.get("name", "unknown")] = agent_plans

    # ── v1.8 Uncertainty summaries ───────────────────────────────────────────
    # getattr with None default is used for all optional v1.x subsystems so
    # that world-state building remains backward-compatible with older agent
    # objects that may not yet have a given attribute.
    uncertainty_summaries: Dict[str, dict] = {}
    for agent_ref in (sentinel, aster):
        monitor = getattr(agent_ref, "uncertainty_monitor", None)
        if monitor is not None:
            agent_name = agent_ref.identity.get("name", "unknown")
            uncertainty_summaries[agent_name] = {
                "uncertainty_levels": dict(monitor.register.levels),
                "mean_uncertainty": round(monitor.register.mean, 4),
                "highest_domain": monitor.register.highest_domain[0],
                "epistemic_stability": round(monitor.epistemic_stability, 4),
                "total_questions_generated": len(monitor.question_log),
                "unanswered_questions": [
                    q.to_dict() for q in monitor.question_log
                    if not q.answered
                ][-5:],  # carry last 5 unanswered
            }

    # ── v1.9 Identity pressure + narrative summaries ─────────────────────────
    identity_summaries: Dict[str, dict] = {}
    unresolved_value_tensions: List[dict] = []
    for agent_ref in (sentinel, aster):
        ips = getattr(agent_ref, "identity_pressure_system", None)
        ns = getattr(agent_ref, "narrative_self", None)
        sj_log = getattr(agent_ref, "self_judgment_log", [])
        agent_name = agent_ref.identity.get("name", "unknown")
        if ips is not None:
            identity_summaries[agent_name] = {
                "deviation_score": ips.deviation_score,
                "realignment_pressure": ips.realignment_pressure,
                "is_destabilising": ips.is_destabilising,
                "chronic_tensions": len(ips.chronic_tensions()),
                "unresolved_tensions": len(ips.unresolved_tensions()),
                "narrative_summary": ns.current_summary if ns else "",
                "stability_trajectory": ns.stability_trajectory if ns else "unknown",
                "becoming": ns.becoming if ns else "",
                "recent_self_judgment": (
                    sj_log[-1].to_dict() if sj_log else {}
                ),
                "mean_self_judgment_score": (
                    round(
                        sum(j.composite_score for j in sj_log) / len(sj_log), 4
                    ) if sj_log else 0.0
                ),
            }
            # Collect unresolved tensions from both agents
            for t in ips.unresolved_tensions():
                td = t.to_dict()
                td["agent"] = agent_name
                unresolved_value_tensions.append(td)

    return {
        "schema_version": "1.9.0",
        "run_label": run_label,
        "saved_at": datetime.now().isoformat(),
        "total_turns_at_save": turn,
        "room_conditions": room_conditions,
        "unresolved_contradictions": all_contradictions,
        "contradiction_lineages": contradiction_lineages,
        "environmental_tensions": environmental_tensions,
        "pending_tasks": pending_tasks,
        "relationship_climate": relationship_climate,
        "prior_major_events": prior_major_events,
        "self_model_summaries": self_model_summaries,
        "unresolved_themes": unresolved_themes,
        "active_plans": active_plans,
        "uncertainty_summaries": uncertainty_summaries,
        # v1.9
        "identity_summaries": identity_summaries,
        "unresolved_value_tensions": unresolved_value_tensions,
    }


def save_world_state(state: dict, output_dir: Path) -> Path:
    """Write *state* to ``world_state.json`` inside *output_dir*.

    Parameters
    ----------
    state :
        Dict returned by :func:`build_world_state`.
    output_dir :
        Directory where ``world_state.json`` should be written.

    Returns
    -------
    Path
        The path of the written file.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / WORLD_STATE_FILENAME
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2)
    return path


def load_world_state(session_dir: Path) -> Optional[dict]:
    """Load the world-state snapshot from a prior session directory.

    Parameters
    ----------
    session_dir :
        Path to a session directory (must contain ``world_state.json``).

    Returns
    -------
    dict or None
        The loaded world-state dict, or ``None`` if the file is absent or
        cannot be parsed.
    """
    path = Path(session_dir) / WORLD_STATE_FILENAME
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _summarise_self_model(agent: Any) -> dict:
    """Return a compact summary of an agent's self-model."""
    sm = getattr(agent, "self_model", {})
    return {
        "self_consistency_score": round(
            sm.get("self_consistency_score", 0.0), 4
        ),
        "dominant_value": sm.get("dominant_value", ""),
        "recent_goal_alignment": sm.get("recent_goal_alignment", "unknown"),
        "prediction_accuracy_recent": round(
            sm.get("prediction_accuracy_recent", 0.0), 4
        ),
        "affective_summary": sm.get("affective_summary", ""),
    }


def _collect_unresolved_themes(agent: Any) -> List[str]:
    """Collect unresolved theme strings from an agent's recent reflections."""
    themes: List[str] = []
    for ref in getattr(agent, "reflection_entries", [])[-5:]:
        raw = getattr(ref, "unresolved_themes", None)
        if isinstance(raw, list):
            themes.extend(str(t) for t in raw[:3])
        elif isinstance(raw, str) and raw:
            themes.append(raw)
    return themes
