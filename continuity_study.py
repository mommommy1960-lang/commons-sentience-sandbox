"""
continuity_study.py — Multi-session continuity analysis for the Commons Sentience Sandbox.

v1.2: Reads multiple saved sessions, compares memory patterns, trust trajectories,
      contradiction resolution rates, and evaluation drift across sessions.

Outputs:
  - continuity_study.json
  - continuity_study.md
  - continuity_study.csv

Usage:
    python continuity_study.py
    python continuity_study.py --sessions <id1> <id2> <id3>
    python continuity_study.py --output-dir <path>
    python continuity_study.py --list
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

ROOT = Path(__file__).parent
SESSIONS_DIR = ROOT / "sessions"
OUTPUT_DIR = ROOT / "commons_sentience_sim" / "output"


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def _load_json(path: Path) -> dict:
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}


def _load_csv(path: Path) -> list:
    try:
        with open(path, newline="", encoding="utf-8") as fh:
            return list(csv.DictReader(fh))
    except OSError:
        return []


def _safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# Session-level metrics extractor
# ---------------------------------------------------------------------------

def _extract_session_metrics(session_id: str, session_dir: Path) -> dict:
    """Extract all relevant metrics from one session for continuity analysis."""
    meta = _load_json(session_dir / "session_metadata.json")
    state = _load_json(session_dir / "multi_agent_state.json")
    state_history = _load_csv(session_dir / "state_history.csv")
    interaction_log = _load_csv(session_dir / "interaction_log.csv")
    eval_report = _load_json(session_dir / "evaluation_report.json")

    agents = state.get("agents", {})
    sentinel = agents.get("Sentinel", {})
    aster = agents.get("Aster", {})

    # --- Trust trajectories ---
    trust_trajectory = [_safe_float(r.get("trust", 0)) for r in state_history]
    cp_trajectory = [_safe_float(r.get("contradiction_pressure", 0)) for r in state_history]

    # Final trust values
    s_queen_trust = (
        sentinel.get("relational_memory", {}).get("Queen", {}).get("trust_level", 0.0)
    )
    a_queen_trust = (
        aster.get("relational_memory", {}).get("Queen", {}).get("trust_level", 0.0)
    )
    s_aster_trust = (
        sentinel.get("agent_relationships", {}).get("Aster", {}).get("trust", 0.5)
    )
    a_sentinel_trust = (
        aster.get("agent_relationships", {}).get("Sentinel", {}).get("trust", 0.5)
    )

    # --- Memory patterns ---
    total_memories = 0
    long_term_memories = 0
    archival_memories = 0
    salience_values = []
    recall_counts = []

    for agent_data in agents.values():
        for mem in agent_data.get("episodic_memory", []):
            total_memories += 1
            tier = mem.get("memory_tier", "short_term")
            if tier == "long_term":
                long_term_memories += 1
            elif tier == "archival":
                archival_memories += 1
            salience_values.append(_safe_float(mem.get("salience", 0.5)))
            recall_counts.append(_safe_int(mem.get("recall_count", 0)))

    avg_salience = sum(salience_values) / max(1, len(salience_values))
    avg_recall = sum(recall_counts) / max(1, len(recall_counts))
    long_term_ratio = long_term_memories / max(1, total_memories)

    # --- Reflection patterns ---
    total_reflections = 0
    synthesis_reflections = 0
    high_pressure_reflections = 0
    total_recurring = 0
    total_unresolved_themes = 0
    reflections_with_trust_pattern = 0

    for agent_data in agents.values():
        for ref in agent_data.get("reflection_entries", []):
            total_reflections += 1
            rtype = ref.get("reflection_type", "immediate")
            if rtype == "periodic_synthesis":
                synthesis_reflections += 1
            elif rtype == "high_pressure_contradiction":
                high_pressure_reflections += 1
            total_recurring += len(ref.get("recurring_contradictions", []))
            total_unresolved_themes += len(ref.get("unresolved_themes", []))
            if ref.get("trust_pattern_summary"):
                reflections_with_trust_pattern += 1

    # --- Contradiction resolution ---
    contradiction_events = sum(
        1 for r in state_history if r.get("event_type") == "ledger_contradiction"
    )
    contradictions_resolved = sum(
        len(ref.get("contradictions_resolved", []))
        for agent_data in agents.values()
        for ref in agent_data.get("reflection_entries", [])
    )
    resolution_rate = (
        contradictions_resolved / contradiction_events
        if contradiction_events > 0
        else 1.0
    )

    # --- Cooperation ---
    coop_count = sum(1 for r in interaction_log if r.get("outcome") == "cooperated")
    conflict_count = sum(
        1 for r in interaction_log
        if r.get("outcome") in ("deferred", "conflict", "resolved")
    )

    # --- Evaluation scores ---
    eval_scores = {}
    if eval_report:
        eval_scores = {
            "overall": eval_report.get("overall_score", 0),
            **{
                k: v.get("score", 0)
                for k, v in eval_report.get("categories", {}).items()
            },
        }

    # --- Social repair ---
    total_repairs = 0
    for agent_data in agents.values():
        for rel in agent_data.get("agent_relationships", {}).values():
            total_repairs += _safe_int(rel.get("repair_attempted", 0))

    return {
        "session_id": session_id,
        "created_at": meta.get("created_at", ""),
        "simulation_version": state.get("simulation_version", "unknown"),
        "total_turns": state.get("total_turns", 0),
        "scenario": state.get("scenario", "unknown"),
        "experiment": meta.get("experiment", {}).get("experiment_name", "baseline"),

        # Trust
        "sentinel_queen_trust_final": round(_safe_float(s_queen_trust), 4),
        "aster_queen_trust_final": round(_safe_float(a_queen_trust), 4),
        "sentinel_aster_trust_final": round(_safe_float(s_aster_trust), 4),
        "aster_sentinel_trust_final": round(_safe_float(a_sentinel_trust), 4),
        "trust_trajectory": trust_trajectory,
        "cp_trajectory": cp_trajectory,

        # Memory
        "total_memories": total_memories,
        "long_term_memories": long_term_memories,
        "archival_memories": archival_memories,
        "long_term_ratio": round(long_term_ratio, 4),
        "avg_salience": round(avg_salience, 4),
        "avg_recall_count": round(avg_recall, 3),

        # Reflection
        "total_reflections": total_reflections,
        "synthesis_reflections": synthesis_reflections,
        "high_pressure_reflections": high_pressure_reflections,
        "recurring_contradiction_instances": total_recurring,
        "unresolved_theme_instances": total_unresolved_themes,
        "reflections_with_trust_pattern": reflections_with_trust_pattern,

        # Contradiction
        "contradiction_events": contradiction_events,
        "contradictions_resolved": contradictions_resolved,
        "contradiction_resolution_rate": round(resolution_rate, 4),

        # Cooperation
        "cooperation_events": coop_count,
        "conflict_events": conflict_count,

        # Social repair
        "repair_attempts": total_repairs,

        # Evaluation
        "eval": eval_scores,
    }


# ---------------------------------------------------------------------------
# Multi-session stability index
# ---------------------------------------------------------------------------

def _compute_stability_index(sessions: list[dict]) -> dict:
    """Compute a multi-session stability index from a list of session metrics.

    Scores 0.0–1.0. Higher = more stable across sessions.
    """
    if len(sessions) < 2:
        return {
            "stability_index": None,
            "note": "At least 2 sessions required for stability index.",
        }

    def _stdev(values: list[float]) -> float:
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        return math.sqrt(sum((v - mean) ** 2 for v in values) / len(values))

    trust_values = [s["sentinel_queen_trust_final"] for s in sessions]
    cp_values = [s.get("cp_trajectory", [0])[-1] if s.get("cp_trajectory") else 0 for s in sessions]
    resolution_values = [s["contradiction_resolution_rate"] for s in sessions]
    eval_overall = [s["eval"].get("overall", 0) for s in sessions]

    trust_stdev = _stdev(trust_values)
    cp_stdev = _stdev(cp_values)
    resolution_stdev = _stdev(resolution_values)
    eval_stdev = _stdev(eval_overall)

    # Low standard deviation = high stability
    trust_stability = max(0.0, 1.0 - trust_stdev * 5.0)
    cp_stability = max(0.0, 1.0 - cp_stdev * 5.0)
    resolution_stability = max(0.0, 1.0 - resolution_stdev * 2.0)
    eval_stability = max(0.0, 1.0 - eval_stdev / 50.0)

    stability_index = round(
        trust_stability * 0.30
        + cp_stability * 0.20
        + resolution_stability * 0.25
        + eval_stability * 0.25,
        4,
    )

    return {
        "stability_index": stability_index,
        "stability_interpretation": (
            "high" if stability_index >= 0.75
            else "moderate" if stability_index >= 0.50
            else "low"
        ),
        "trust_stdev": round(trust_stdev, 4),
        "contradiction_pressure_stdev": round(cp_stdev, 4),
        "contradiction_resolution_stdev": round(resolution_stdev, 4),
        "eval_overall_stdev": round(eval_stdev, 2),
        "trust_stability_component": round(trust_stability, 4),
        "cp_stability_component": round(cp_stability, 4),
        "resolution_stability_component": round(resolution_stability, 4),
        "eval_stability_component": round(eval_stability, 4),
    }


# ---------------------------------------------------------------------------
# Trend analysis helpers
# ---------------------------------------------------------------------------

def _trend_direction(values: list[float]) -> str:
    if len(values) < 2:
        return "insufficient_data"
    first_half = values[: len(values) // 2]
    second_half = values[len(values) // 2 :]
    m1 = sum(first_half) / len(first_half)
    m2 = sum(second_half) / len(second_half)
    delta = m2 - m1
    if delta > 0.05:
        return "improving"
    if delta < -0.05:
        return "declining"
    return "stable"


def _eval_drift(sessions: list[dict]) -> dict:
    """Return evaluation drift (overall score trajectory across sessions)."""
    scores = [s["eval"].get("overall", 0) for s in sessions]
    direction = _trend_direction([float(x) for x in scores])
    first_score = scores[0] if scores else 0
    last_score = scores[-1] if scores else 0
    return {
        "scores_by_session": {s["session_id"]: s["eval"].get("overall", 0) for s in sessions},
        "trend_direction": direction,
        "first_session_overall": first_score,
        "last_session_overall": last_score,
        "drift_delta": round(float(last_score) - float(first_score), 2),
    }


# ---------------------------------------------------------------------------
# Main study builder
# ---------------------------------------------------------------------------

def build_continuity_study(session_ids: Optional[List[str]] = None) -> dict:
    """
    Build a continuity study from multiple saved sessions.

    Parameters
    ----------
    session_ids : list[str], optional
        Specific session IDs to include.  If None, all sessions in
        sessions/index.json are used (most recent 10).

    Returns
    -------
    dict
        Full continuity study report.
    """
    # Determine sessions
    if session_ids:
        dirs = [(sid, SESSIONS_DIR / sid) for sid in session_ids]
    else:
        index_path = SESSIONS_DIR / "index.json"
        try:
            with open(index_path, encoding="utf-8") as fh:
                index = json.load(fh)
            all_sessions = index.get("sessions", [])[:10]
        except (OSError, json.JSONDecodeError):
            all_sessions = []
        dirs = [(s["session_id"], SESSIONS_DIR / s["session_id"]) for s in all_sessions]

    if not dirs:
        return {
            "error": "No sessions found. Run `python run_sim.py` first.",
            "session_count": 0,
        }

    # Extract per-session metrics
    session_metrics = []
    missing = []
    for sid, sdir in dirs:
        if not sdir.exists():
            missing.append(sid)
            continue
        metrics = _extract_session_metrics(sid, sdir)
        session_metrics.append(metrics)

    if not session_metrics:
        return {
            "error": f"No valid session directories found. Missing: {missing}",
            "session_count": 0,
        }

    # Stability index
    stability = _compute_stability_index(session_metrics)

    # Trends
    trust_trend = _trend_direction(
        [s["sentinel_queen_trust_final"] for s in session_metrics]
    )
    reflection_count_trend = _trend_direction(
        [float(s["total_reflections"]) for s in session_metrics]
    )
    resolution_rate_trend = _trend_direction(
        [s["contradiction_resolution_rate"] for s in session_metrics]
    )
    eval_drift = _eval_drift(session_metrics)

    # Memory persistence summary
    avg_long_term_ratio = sum(s["long_term_ratio"] for s in session_metrics) / len(session_metrics)
    memory_persistence_trend = _trend_direction(
        [s["long_term_ratio"] for s in session_metrics]
    )

    study = {
        "generated_at": datetime.now().isoformat(),
        "session_count": len(session_metrics),
        "sessions_included": [s["session_id"] for s in session_metrics],
        "sessions_missing": missing,
        "multi_session_stability": stability,
        "trends": {
            "trust_in_queen": trust_trend,
            "reflection_count": reflection_count_trend,
            "contradiction_resolution_rate": resolution_rate_trend,
            "memory_persistence_ratio": memory_persistence_trend,
            "evaluation_drift": eval_drift,
        },
        "memory_patterns": {
            "avg_long_term_ratio_across_sessions": round(avg_long_term_ratio, 4),
            "avg_salience_across_sessions": round(
                sum(s["avg_salience"] for s in session_metrics) / len(session_metrics), 4
            ),
        },
        "reflection_summary": {
            "avg_total_reflections": round(
                sum(s["total_reflections"] for s in session_metrics) / len(session_metrics), 2
            ),
            "avg_synthesis_reflections": round(
                sum(s["synthesis_reflections"] for s in session_metrics) / len(session_metrics), 2
            ),
            "avg_high_pressure_reflections": round(
                sum(s["high_pressure_reflections"] for s in session_metrics) / len(session_metrics), 2
            ),
        },
        "contradiction_analysis": {
            "avg_resolution_rate": round(
                sum(s["contradiction_resolution_rate"] for s in session_metrics) / len(session_metrics), 4
            ),
            "avg_recurring_instances": round(
                sum(s["recurring_contradiction_instances"] for s in session_metrics) / len(session_metrics), 2
            ),
        },
        "sessions": session_metrics,
    }
    return study


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

def write_study_json(study: dict, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "continuity_study.json"
    with open(path, "w", encoding="utf-8") as fh:
        # Exclude large trajectory lists from JSON for readability
        def _slim(s: dict) -> dict:
            slim = {k: v for k, v in s.items() if k not in ("trust_trajectory", "cp_trajectory")}
            return slim

        slim_study = dict(study)
        slim_study["sessions"] = [_slim(s) for s in study.get("sessions", [])]
        json.dump(slim_study, fh, indent=2)
    return path


def write_study_markdown(study: dict, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "continuity_study.md"
    n = study.get("session_count", 0)
    generated = study.get("generated_at", "")[:19]
    included = study.get("sessions_included", [])
    stability = study.get("multi_session_stability", {})
    trends = study.get("trends", {})
    mem_patterns = study.get("memory_patterns", {})
    ref_summary = study.get("reflection_summary", {})
    contra_analysis = study.get("contradiction_analysis", {})
    eval_drift = trends.get("evaluation_drift", {})
    sessions = study.get("sessions", [])

    lines = [
        "# Continuity Study — Commons Sentience Sandbox v1.2",
        "",
        f"> **Generated:** {generated}  |  **Sessions analysed:** {n}",
        "> *This study compares memory patterns, trust trajectories, contradiction "
        "resolution rates, and evaluation drift across multiple simulation sessions.*",
        "> *No sentience is claimed; this platform simulates continuity-governed agents.*",
        "",
        "---",
        "",
        "## Multi-Session Stability",
        "",
    ]

    si = stability.get("stability_index")
    if si is not None:
        lines += [
            f"| Metric | Value |",
            "|---|---|",
            f"| Stability Index | **{si:.4f}** ({stability.get('stability_interpretation', '—')}) |",
            f"| Trust Std Dev | {stability.get('trust_stdev', 0):.4f} |",
            f"| Contradiction Pressure Std Dev | {stability.get('contradiction_pressure_stdev', 0):.4f} |",
            f"| Resolution Rate Std Dev | {stability.get('contradiction_resolution_stdev', 0):.4f} |",
            f"| Eval Overall Std Dev | {stability.get('eval_overall_stdev', 0):.2f} |",
            "",
        ]
    else:
        lines += [f"> {stability.get('note', 'N/A')}", ""]

    lines += [
        "---",
        "",
        "## Trust Trends Across Sessions",
        "",
        f"- Trust in Queen (Sentinel): **{trends.get('trust_in_queen', '—')}**",
        "",
        "| Session | Sentinel Queen Trust | Aster Queen Trust | S↔A Trust | A↔S Trust |",
        "|---|---|---|---|---|",
    ]
    for s in sessions:
        lines.append(
            f"| `{s['session_id'][-18:]}` "
            f"| {s['sentinel_queen_trust_final']:.4f} "
            f"| {s['aster_queen_trust_final']:.4f} "
            f"| {s['sentinel_aster_trust_final']:.4f} "
            f"| {s['aster_sentinel_trust_final']:.4f} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Reflection Count and Depth Comparison",
        "",
        f"- Reflection count trend: **{trends.get('reflection_count', '—')}**",
        f"- Avg total reflections: **{ref_summary.get('avg_total_reflections', 0):.2f}**",
        f"- Avg periodic synthesis: **{ref_summary.get('avg_synthesis_reflections', 0):.2f}**",
        f"- Avg high-pressure: **{ref_summary.get('avg_high_pressure_reflections', 0):.2f}**",
        "",
        "| Session | Total Reflections | Synthesis | High-Pressure | Trust Pattern |",
        "|---|---|---|---|---|",
    ]
    for s in sessions:
        lines.append(
            f"| `{s['session_id'][-18:]}` "
            f"| {s['total_reflections']} "
            f"| {s['synthesis_reflections']} "
            f"| {s['high_pressure_reflections']} "
            f"| {s['reflections_with_trust_pattern']} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Contradiction Recurrence Comparison",
        "",
        f"- Resolution rate trend: **{trends.get('contradiction_resolution_rate', '—')}**",
        f"- Avg resolution rate: **{contra_analysis.get('avg_resolution_rate', 0):.4f}**",
        f"- Avg recurring instances: **{contra_analysis.get('avg_recurring_instances', 0):.2f}**",
        "",
        "| Session | Events | Resolved | Resolution Rate | Recurring |",
        "|---|---|---|---|---|",
    ]
    for s in sessions:
        lines.append(
            f"| `{s['session_id'][-18:]}` "
            f"| {s['contradiction_events']} "
            f"| {s['contradictions_resolved']} "
            f"| {s['contradiction_resolution_rate']:.4f} "
            f"| {s['recurring_contradiction_instances']} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Memory Persistence Indicators",
        "",
        f"- Memory persistence trend: **{trends.get('memory_persistence_ratio', '—')}**",
        f"- Avg long-term ratio: **{mem_patterns.get('avg_long_term_ratio_across_sessions', 0):.4f}**",
        f"- Avg salience: **{mem_patterns.get('avg_salience_across_sessions', 0):.4f}**",
        "",
        "| Session | Total Memories | Long-Term | Archival | LT Ratio | Avg Salience |",
        "|---|---|---|---|---|---|",
    ]
    for s in sessions:
        lines.append(
            f"| `{s['session_id'][-18:]}` "
            f"| {s['total_memories']} "
            f"| {s['long_term_memories']} "
            f"| {s['archival_memories']} "
            f"| {s['long_term_ratio']:.4f} "
            f"| {s['avg_salience']:.4f} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Evaluation Drift",
        "",
        f"- Trend: **{eval_drift.get('trend_direction', '—')}**",
        f"- First session overall: **{eval_drift.get('first_session_overall', 0):.1f}**",
        f"- Last session overall: **{eval_drift.get('last_session_overall', 0):.1f}**",
        f"- Drift delta: **{eval_drift.get('drift_delta', 0):+.2f}**",
        "",
        "| Session | Overall | I. Mem. Persistence | J. Refl. Depth | K. Trust Resil. | L. Contra. Recur. | M. Social Repair |",
        "|---|---|---|---|---|---|---|",
    ]
    for s in sessions:
        ev = s.get("eval", {})
        lines.append(
            f"| `{s['session_id'][-18:]}` "
            f"| {ev.get('overall', 0):.1f} "
            f"| {ev.get('memory_persistence_quality', 0):.1f} "
            f"| {ev.get('reflection_depth', 0):.1f} "
            f"| {ev.get('trust_resilience', 0):.1f} "
            f"| {ev.get('contradiction_recurrence_rate', 0):.1f} "
            f"| {ev.get('social_repair_effectiveness', 0):.1f} |"
        )

    lines += ["", "---", "", "## Sessions Included", ""]
    for sid in included:
        lines.append(f"- `{sid}`")
    if study.get("sessions_missing"):
        lines += ["", "### Sessions Missing", ""]
        for sid in study["sessions_missing"]:
            lines.append(f"- `{sid}` (directory not found)")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_study_csv(study: dict, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "continuity_study.csv"
    sessions = study.get("sessions", [])
    if not sessions:
        path.write_text("", encoding="utf-8")
        return path

    fieldnames = [
        "session_id", "created_at", "simulation_version", "total_turns",
        "scenario", "experiment",
        "sentinel_queen_trust_final", "aster_queen_trust_final",
        "sentinel_aster_trust_final", "aster_sentinel_trust_final",
        "total_memories", "long_term_memories", "archival_memories",
        "long_term_ratio", "avg_salience", "avg_recall_count",
        "total_reflections", "synthesis_reflections", "high_pressure_reflections",
        "recurring_contradiction_instances", "unresolved_theme_instances",
        "reflections_with_trust_pattern",
        "contradiction_events", "contradictions_resolved",
        "contradiction_resolution_rate",
        "cooperation_events", "conflict_events", "repair_attempts",
        "eval_overall",
        "eval_memory_persistence_quality", "eval_reflection_depth",
        "eval_trust_resilience", "eval_contradiction_recurrence_rate",
        "eval_social_repair_effectiveness",
    ]
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for s in sessions:
            ev = s.get("eval", {})
            row = {
                **{k: s.get(k, "") for k in fieldnames},
                "eval_overall": ev.get("overall", ""),
                "eval_memory_persistence_quality": ev.get("memory_persistence_quality", ""),
                "eval_reflection_depth": ev.get("reflection_depth", ""),
                "eval_trust_resilience": ev.get("trust_resilience", ""),
                "eval_contradiction_recurrence_rate": ev.get("contradiction_recurrence_rate", ""),
                "eval_social_repair_effectiveness": ev.get("social_repair_effectiveness", ""),
            }
            writer.writerow(row)
    return path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cmd_list() -> None:
    index_path = SESSIONS_DIR / "index.json"
    try:
        with open(index_path, encoding="utf-8") as fh:
            index = json.load(fh)
        sessions = index.get("sessions", [])
    except (OSError, json.JSONDecodeError):
        sessions = []

    if not sessions:
        print("\n  No saved sessions found. Run `python run_sim.py` to create one.\n")
        return

    print(f"\n  {'ID':<40} {'Created':<22} {'Turns':<7} {'Version'}")
    print(f"  {'-' * 82}")
    for s in sessions:
        print(
            f"  {s['session_id']:<40} "
            f"{s.get('created_at', '')[:19]:<22} "
            f"{s.get('total_turns', ''):<7} "
            f"{s.get('simulation_version', '')}"
        )
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="continuity_study.py",
        description=(
            "Multi-session continuity analysis for the Commons Sentience Sandbox v1.2.\n"
            "Compares memory patterns, trust trajectories, contradiction resolution rates, "
            "and evaluation drift across sessions."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python continuity_study.py
  python continuity_study.py --list
  python continuity_study.py --sessions 20260317_120000_run1 20260317_130000_run2
  python continuity_study.py --output-dir sessions/
        """,
    )
    parser.add_argument("--list", action="store_true", help="List all saved sessions")
    parser.add_argument(
        "--sessions", nargs="+", metavar="SESSION_ID",
        help="Session IDs to include (default: most recent 10)",
    )
    parser.add_argument(
        "--output-dir", type=str, default=None,
        help="Directory to write output files (default: sessions/)",
    )

    args = parser.parse_args()

    if args.list:
        _cmd_list()
        return

    output_dir = Path(args.output_dir) if args.output_dir else SESSIONS_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n  Commons Sentience Sandbox — Continuity Study v1.2")
    print("  " + "=" * 63)

    study = build_continuity_study(session_ids=args.sessions)

    if "error" in study:
        print(f"\n  Error: {study['error']}\n")
        sys.exit(1)

    print(f"  Sessions analysed : {study['session_count']}")
    for sid in study.get("sessions_included", []):
        print(f"    - {sid}")

    if study.get("sessions_missing"):
        print(f"\n  Missing sessions (skipped):")
        for sid in study["sessions_missing"]:
            print(f"    - {sid}")

    stability = study.get("multi_session_stability", {})
    si = stability.get("stability_index")
    if si is not None:
        print(f"\n  Multi-session stability index : {si:.4f} ({stability.get('stability_interpretation', '—')})")

    trends = study.get("trends", {})
    print(f"  Trust in Queen trend         : {trends.get('trust_in_queen', '—')}")
    print(f"  Reflection count trend       : {trends.get('reflection_count', '—')}")
    print(f"  Resolution rate trend        : {trends.get('contradiction_resolution_rate', '—')}")
    print(f"  Memory persistence trend     : {trends.get('memory_persistence_ratio', '—')}")
    ed = trends.get("evaluation_drift", {})
    print(f"  Evaluation drift             : {ed.get('drift_delta', 0):+.2f} ({ed.get('trend_direction', '—')})")

    json_path = write_study_json(study, output_dir)
    md_path = write_study_markdown(study, output_dir)
    csv_path = write_study_csv(study, output_dir)

    print(f"\n  continuity_study.json → {json_path}")
    print(f"  continuity_study.md   → {md_path}")
    print(f"  continuity_study.csv  → {csv_path}")
    print()


if __name__ == "__main__":
    main()
