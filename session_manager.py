"""
session_manager.py — Session storage and management for Commons Sentience Sandbox.

Provides helpers to:
- Save a simulation run as a named, timestamped session
- List all saved sessions
- Load a session's output directory
- Compute session summary metrics
- Run the evaluation harness and store evaluation outputs
- Compare two sessions and generate comparison_report.json / markdown
"""
from __future__ import annotations

import csv
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from evaluation import evaluate_and_save, _load_json as _eval_load_json  # noqa: F401

ROOT = Path(__file__).parent
SESSIONS_DIR = ROOT / "sessions"
OUTPUT_DIR = ROOT / "commons_sentience_sim" / "output"

# All output files that are copied into a session folder
OUTPUT_FILES = [
    "multi_agent_state.json",
    "final_state.json",
    "state_history.csv",
    "oversight_log.csv",
    "agent_relationships.csv",
    "interaction_log.csv",
    "narrative_log.md",
    "trust_plot.png",
    "urgency_plot.png",
    "contradiction_plot.png",
    "agent_trust_plot.png",
    "queen_trust_plot.png",
    "interactions_plot.png",
    "evaluation_report.json",
    "evaluation_summary.md",
    # v1.6 persistent world state
    "world_state.json",
]

# Continuity study outputs included in bundles when present
CONTINUITY_STUDY_FILES = [
    "continuity_study.json",
    "continuity_study.md",
    "continuity_study.csv",
]

# Agent profile study outputs included in bundles when present
AGENT_PROFILE_STUDY_FILES = [
    "agent_profile_study.json",
    "agent_profile_study.md",
    "agent_profile_study.csv",
]


# ---------------------------------------------------------------------------
# Internal helpers
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


def _compute_summary(session_dir: Path, state_data: dict, interaction_log: list[dict]) -> dict:
    """Compute high-level summary metrics for a session."""
    agents = state_data.get("agents", {})
    sentinel = agents.get("Sentinel", {})
    aster = agents.get("Aster", {})

    # Trust in Queen
    s_queen_trust = (
        sentinel.get("relational_memory", {})
        .get("Queen", {})
        .get("trust_level", 0.0)
    )
    a_queen_trust = (
        aster.get("relational_memory", {})
        .get("Queen", {})
        .get("trust_level", 0.0)
    )

    # Mutual agent trust
    s_aster_trust = (
        sentinel.get("agent_relationships", {})
        .get("Aster", {})
        .get("trust", 0.0)
    )
    a_sentinel_trust = (
        aster.get("agent_relationships", {})
        .get("Sentinel", {})
        .get("trust", 0.0)
    )

    # Reflections
    s_reflections = len(sentinel.get("reflection_entries", []))
    a_reflections = len(aster.get("reflection_entries", []))

    # Interactions
    coop = sum(1 for r in interaction_log if r.get("outcome") == "cooperated")
    conflict = sum(
        1 for r in interaction_log
        if r.get("outcome") in ("deferred", "conflict", "resolved")
    )

    # Final contradiction pressure
    s_cp = sentinel.get("affective_state", {}).get("contradiction_pressure", 0.0)
    a_cp = aster.get("affective_state", {}).get("contradiction_pressure", 0.0)

    return {
        "sentinel_trust_in_queen": round(float(s_queen_trust), 4),
        "aster_trust_in_queen": round(float(a_queen_trust), 4),
        "mutual_trust_sentinel_aster": round(float(s_aster_trust), 4),
        "mutual_trust_aster_sentinel": round(float(a_sentinel_trust), 4),
        "sentinel_reflections": s_reflections,
        "aster_reflections": a_reflections,
        "cooperation_events": coop,
        "conflict_events": conflict,
        "sentinel_final_contradiction_pressure": round(float(s_cp), 4),
        "aster_final_contradiction_pressure": round(float(a_cp), 4),
    }


def _update_sessions_index(session_id: str, metadata: dict) -> None:
    """Append/update the sessions/index.json entry for this session."""
    index_path = SESSIONS_DIR / "index.json"
    try:
        with open(index_path, encoding="utf-8") as fh:
            index = json.load(fh)
    except (OSError, json.JSONDecodeError):
        index = {"sessions": []}

    # Remove stale entry for this session_id if present
    index["sessions"] = [
        s for s in index["sessions"] if s.get("session_id") != session_id
    ]

    # Lightweight entry (no full episodic memory, etc.)
    entry = {
        "session_id": session_id,
        "created_at": metadata["created_at"],
        "simulation_version": metadata["simulation_version"],
        "total_turns": metadata["total_turns"],
        "agent_names": metadata["agent_names"],
        "summary": metadata["summary"],
    }
    # Include experiment metadata if present
    if "experiment" in metadata and metadata["experiment"]:
        entry["experiment"] = metadata["experiment"]
    # Include scenario name if present
    if "scenario" in metadata and metadata["scenario"]:
        entry["scenario"] = metadata["scenario"]
    # Include evaluation scores if present
    if "evaluation" in metadata:
        entry["evaluation"] = metadata["evaluation"]

    index["sessions"].append(entry)

    # Most recent first
    index["sessions"].sort(
        key=lambda s: s.get("created_at", ""), reverse=True
    )

    with open(index_path, "w", encoding="utf-8") as fh:
        json.dump(index, fh, indent=2)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def save_session(
    session_name: Optional[str] = None,
    source_dir: Optional[Path] = None,
    experiment_config: Optional[object] = None,
    scenario_name: Optional[str] = None,
) -> Path:
    """
    Copy all output files into a timestamped session folder under sessions/.

    Parameters
    ----------
    session_name : str, optional
        A human-readable slug appended to the timestamp (e.g. "run1").
        Defaults to "default".
    source_dir : Path, optional
        Directory to copy outputs from.  Defaults to OUTPUT_DIR.
    experiment_config : ExperimentConfig, optional
        When provided, its metadata dict is stored in session_metadata.json.
    scenario_name : str, optional
        Name of the scenario used (e.g. "trust_crisis").  Stored in metadata.

    Returns
    -------
    Path
        The new session directory.
    """
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    if source_dir is None:
        source_dir = OUTPUT_DIR

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = session_name.replace(" ", "_").lower() if session_name else "default"
    session_id = f"{ts}_{slug}"
    session_dir = SESSIONS_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    # Copy output files (includes evaluation_report.json if already generated)
    for fname in OUTPUT_FILES:
        src = source_dir / fname
        if src.exists():
            shutil.copy2(src, session_dir / fname)

    # Also copy continuity study files if they exist in SESSIONS_DIR
    for fname in CONTINUITY_STUDY_FILES:
        src = SESSIONS_DIR / fname
        if src.exists():
            shutil.copy2(src, session_dir / fname)

    # Also copy agent profile study files if they exist in SESSIONS_DIR
    for fname in AGENT_PROFILE_STUDY_FILES:
        src = SESSIONS_DIR / fname
        if src.exists():
            shutil.copy2(src, session_dir / fname)

    # If evaluation_report.json was not in source_dir, generate it now
    eval_report_path = session_dir / "evaluation_report.json"
    if not eval_report_path.exists():
        try:
            eval_report = evaluate_and_save(
                session_dir,
                experiment_config=experiment_config,
                scenario_name=scenario_name,
            )
        except Exception:
            eval_report = {}
    else:
        eval_report = _load_json(eval_report_path)

    # Compute summary from copied files
    state_data = _load_json(session_dir / "multi_agent_state.json")
    interaction_log = _load_csv(session_dir / "interaction_log.csv")

    # Build compact evaluation summary for the index (scores only)
    eval_scores: dict = {}
    if eval_report:
        eval_scores = {
            "overall_score": eval_report.get("overall_score", 0),
            "overall_interpretation": eval_report.get("overall_interpretation", ""),
            "category_scores": {
                k: v.get("score", 0)
                for k, v in eval_report.get("categories", {}).items()
            },
        }

    # Experiment metadata for the index
    exp_meta_compact: dict = {}
    if experiment_config is not None:
        try:
            exp_meta_compact = {
                "experiment_name": experiment_config.name,
                "description": experiment_config.description,
                "governance_strictness": experiment_config.governance_strictness,
                "cooperation_bias": experiment_config.cooperation_bias,
                "initial_agent_trust": experiment_config.initial_agent_trust,
            }
        except AttributeError:
            pass
    else:
        # Fall back to whatever is stored in the state JSON
        exp_in_state = state_data.get("experiment", {})
        if exp_in_state:
            exp_meta_compact = {
                "experiment_name": exp_in_state.get("experiment_name", "baseline"),
            }

    # Scenario name: prefer explicit arg, then what's in state JSON
    resolved_scenario = (
        scenario_name
        or state_data.get("scenario")
        or "scenario_events"
    )

    metadata = {
        "session_id": session_id,
        "created_at": datetime.now().isoformat(),
        "simulation_version": state_data.get("simulation_version", "unknown"),
        "total_turns": state_data.get("total_turns", 0),
        "agent_names": list(state_data.get("agents", {}).keys()),
        "scenario": resolved_scenario,
        "experiment": exp_meta_compact,
        "summary": _compute_summary(session_dir, state_data, interaction_log),
        "evaluation": eval_scores,
        "longitudinal_artifacts": {
            name: {
                "identity_history_entries": len(agent_data.get("identity_history", [])),
                "goal_evolution_events": len(agent_data.get("goal_evolution", [])),
                "contradiction_genealogy_entries": len(agent_data.get("contradiction_genealogy", [])),
                "relationship_timeline_events": sum(
                    len(v) for v in agent_data.get("relationship_timelines", {}).values()
                ),
            }
            for name, agent_data in state_data.get("agents", {}).items()
        },
    }

    with open(session_dir / "session_metadata.json", "w", encoding="utf-8") as fh:
        json.dump(metadata, fh, indent=2)

    # Write per-session session_summary.json with consistent schema
    session_summary = {
        "session_id": session_id,
        "created_at": metadata["created_at"],
        "simulation_version": metadata["simulation_version"],
        "scenario": resolved_scenario,
        "experiment": exp_meta_compact.get("experiment_name", "baseline") if exp_meta_compact else "baseline",
        "agents": metadata["agent_names"],
        "metrics": metadata["summary"],
        "evaluation": {
            "overall_score": eval_scores.get("overall_score", 0),
            "overall_interpretation": eval_scores.get("overall_interpretation", ""),
        } if eval_scores else {},
    }
    with open(session_dir / "session_summary.json", "w", encoding="utf-8") as fh:
        json.dump(session_summary, fh, indent=2)

    _update_sessions_index(session_id, metadata)

    return session_dir


def list_sessions() -> list[dict]:
    """Return all saved sessions (most recent first) from the index."""
    index_path = SESSIONS_DIR / "index.json"
    try:
        with open(index_path, encoding="utf-8") as fh:
            index = json.load(fh)
        return index.get("sessions", [])
    except (OSError, json.JSONDecodeError):
        return []


def get_session_dir(session_id: str) -> Optional[Path]:
    """Return the Path for a session, or None if it does not exist."""
    d = SESSIONS_DIR / session_id
    return d if d.exists() else None


def load_session_metadata(session_id: str) -> dict:
    """Load session_metadata.json for the given session."""
    d = get_session_dir(session_id)
    if d is None:
        return {}
    return _load_json(d / "session_metadata.json")


def compare_sessions(session_a_id: str, session_b_id: str) -> dict:
    """
    Compare two sessions and return a structured comparison dict.

    Also writes comparison_report.json to sessions/ directory.
    """
    dir_a = get_session_dir(session_a_id)
    dir_b = get_session_dir(session_b_id)

    meta_a = load_session_metadata(session_a_id)
    meta_b = load_session_metadata(session_b_id)

    summary_a = meta_a.get("summary", {})
    summary_b = meta_b.get("summary", {})

    def _diff_float(key: str) -> dict:
        va = float(summary_a.get(key, 0.0))
        vb = float(summary_b.get(key, 0.0))
        return {"session_a": va, "session_b": vb, "delta": round(vb - va, 4)}

    def _diff_int(key: str) -> dict:
        va = int(summary_a.get(key, 0))
        vb = int(summary_b.get(key, 0))
        return {"session_a": va, "session_b": vb, "delta": vb - va}

    trust_final = {
        k: _diff_float(k)
        for k in (
            "sentinel_trust_in_queen",
            "aster_trust_in_queen",
            "mutual_trust_sentinel_aster",
            "mutual_trust_aster_sentinel",
        )
    }

    reflections = {
        k: _diff_int(k)
        for k in ("sentinel_reflections", "aster_reflections")
    }

    interactions = {
        k: _diff_int(k)
        for k in ("cooperation_events", "conflict_events")
    }

    contradiction_pressure = {
        k: _diff_float(k)
        for k in (
            "sentinel_final_contradiction_pressure",
            "aster_final_contradiction_pressure",
        )
    }

    # State history comparison (Sentinel per-turn CSV)
    state_history: dict = {}
    if dir_a and dir_b:
        hist_a = _load_csv(dir_a / "state_history.csv")
        hist_b = _load_csv(dir_b / "state_history.csv")
        if hist_a and hist_b:
            state_history["turns_a"] = len(hist_a)
            state_history["turns_b"] = len(hist_b)
            last_a = hist_a[-1]
            last_b = hist_b[-1]
            for col in ("urgency", "trust", "contradiction_pressure", "trust_in_Aster"):
                try:
                    va = float(last_a.get(col, 0))
                    vb = float(last_b.get(col, 0))
                    state_history[f"sentinel_final_{col}"] = {
                        "session_a": va,
                        "session_b": vb,
                        "delta": round(vb - va, 4),
                    }
                except (ValueError, TypeError):
                    pass

    # Evaluation score comparison
    eval_comparison: dict = {}
    if dir_a and dir_b:
        eval_a = _load_json(dir_a / "evaluation_report.json")
        eval_b = _load_json(dir_b / "evaluation_report.json")
        if eval_a and eval_b:
            oa = float(eval_a.get("overall_score", 0))
            ob = float(eval_b.get("overall_score", 0))
            eval_comparison["overall"] = {
                "session_a": oa,
                "session_b": ob,
                "delta": round(ob - oa, 1),
                "better": "session_b" if ob > oa else ("session_a" if oa > ob else "tie"),
            }
            cats_a = eval_a.get("categories", {})
            cats_b = eval_b.get("categories", {})
            category_diffs = {}
            for cat in cats_a:
                sa = float(cats_a[cat].get("score", 0))
                sb = float(cats_b.get(cat, {}).get("score", 0))
                category_diffs[cat] = {
                    "session_a": sa,
                    "session_b": sb,
                    "delta": round(sb - sa, 1),
                    "better": (
                        "session_b" if sb > sa else ("session_a" if sa > sb else "tie")
                    ),
                }
            eval_comparison["categories"] = category_diffs
            # Largest gap
            if category_diffs:
                largest_gap_cat = max(
                    category_diffs, key=lambda k: abs(category_diffs[k]["delta"])
                )
                eval_comparison["largest_gap_category"] = largest_gap_cat
                eval_comparison["largest_gap_delta"] = category_diffs[largest_gap_cat][
                    "delta"
                ]

    # Experiment config comparison
    exp_a = meta_a.get("experiment", {})
    exp_b = meta_b.get("experiment", {})
    config_comparison: dict = {
        "session_a_experiment": exp_a.get("experiment_name", "baseline") if exp_a else "baseline",
        "session_b_experiment": exp_b.get("experiment_name", "baseline") if exp_b else "baseline",
        "same_config": (
            exp_a.get("experiment_name") == exp_b.get("experiment_name")
            if exp_a and exp_b else False
        ),
    }
    # Note key parameter differences
    param_diffs = {}
    if exp_a and exp_b:
        for key in ("governance_strictness", "cooperation_bias", "initial_agent_trust"):
            va = exp_a.get(key)
            vb = exp_b.get(key)
            if va is not None and vb is not None and va != vb:
                param_diffs[key] = {"session_a": va, "session_b": vb}
    if param_diffs:
        config_comparison["parameter_differences"] = param_diffs

    report = {
        "session_a": session_a_id,
        "session_b": session_b_id,
        "generated_at": datetime.now().isoformat(),
        "session_a_version": meta_a.get("simulation_version", "unknown"),
        "session_b_version": meta_b.get("simulation_version", "unknown"),
        "comparison": {
            "config": config_comparison,
            "trust_final": trust_final,
            "reflections": reflections,
            "interactions": interactions,
            "contradiction_pressure": contradiction_pressure,
            "state_history": state_history,
            "evaluation": eval_comparison,
        },
    }

    # Write comparison_report.json to sessions/
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = (
        SESSIONS_DIR / f"comparison_{session_a_id}_vs_{session_b_id}.json"
    )
    with open(report_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)

    return report
