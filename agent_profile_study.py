"""
agent_profile_study.py — Cross-session longitudinal agent profile study.

v1.3: Reads multiple saved sessions, builds a longitudinal profile for each
agent, and compares trust behaviour, reflection style, contradiction patterns,
memory persistence, and goal adaptation across sessions.

Outputs:
  - agent_profile_study.json
  - agent_profile_study.md
  - agent_profile_study.csv

Usage:
    python agent_profile_study.py
    python agent_profile_study.py --sessions <id1> <id2> <id3>
    python agent_profile_study.py --output-dir <path>
    python agent_profile_study.py --list
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


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def _load_json(path: Path) -> dict:
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}


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


def _mean(values: list) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _std(values: list) -> float:
    if len(values) < 2:
        return 0.0
    m = _mean(values)
    variance = sum((v - m) ** 2 for v in values) / len(values)
    return math.sqrt(variance)


# ---------------------------------------------------------------------------
# Per-agent profile extraction from a single session
# ---------------------------------------------------------------------------

def _extract_agent_session_data(agent_name: str, session_id: str, session_dir: Path) -> Optional[dict]:
    """Extract per-agent longitudinal data from one session directory."""
    state_path = session_dir / "multi_agent_state.json"
    if not state_path.exists():
        return None

    state_data = _load_json(state_path)
    agent_data = state_data.get("agents", {}).get(agent_name)
    if agent_data is None:
        return None

    total_turns = _safe_int(state_data.get("total_turns", 0))
    sim_version = state_data.get("simulation_version", "unknown")
    created_at = state_data.get("created_at", "")

    # Trust behaviour
    agent_rels = agent_data.get("agent_relationships", {})
    peer_name = "Aster" if agent_name == "Sentinel" else "Sentinel"
    peer_rel = agent_rels.get(peer_name, {})
    peer_trust_final = _safe_float(peer_rel.get("trust", 0.5))

    rel_mem = agent_data.get("relational_memory", {})
    queen_trust_values = [
        _safe_float(rm.get("trust_level", 0.5))
        for rm in rel_mem.values()
    ]
    queen_trust_mean = _mean(queen_trust_values) if queen_trust_values else 0.5

    # Reflection style
    reflection_entries = agent_data.get("reflection_entries", [])
    reflection_types: dict = {}
    for r in reflection_entries:
        rtype = r.get("reflection_type", "immediate") if isinstance(r, dict) else "immediate"
        reflection_types[rtype] = reflection_types.get(rtype, 0) + 1

    # Contradiction patterns
    pending_contradictions = agent_data.get("pending_contradictions", [])
    contradiction_genealogy = agent_data.get("contradiction_genealogy", [])
    total_contradictions = len(contradiction_genealogy) or len(pending_contradictions)
    resolved_count = sum(1 for c in contradiction_genealogy if c.get("resolved", False))
    resolution_rate = resolved_count / max(1, len(contradiction_genealogy)) if contradiction_genealogy else 0.0
    avg_intensity = _mean([
        _mean(c.get("intensity_trend", [0.5]))
        for c in contradiction_genealogy
    ]) if contradiction_genealogy else 0.5

    # Memory persistence
    episodic_memory = agent_data.get("episodic_memory", [])
    long_term_count = sum(1 for m in episodic_memory if m.get("memory_type") == "long_term")
    lt_ratio = long_term_count / max(1, len(episodic_memory))
    avg_salience = _mean([_safe_float(m.get("salience", 0.5)) for m in episodic_memory])

    # Goal adaptation
    goal_evolution = agent_data.get("goal_evolution", [])
    goal_events_count = len(goal_evolution)
    preserved_count = sum(1 for g in goal_evolution if g.get("event_type") == "preserved")
    adaptive_count = goal_events_count - preserved_count

    # Identity continuity
    identity_history = agent_data.get("identity_history", [])
    drift_indicators = [_safe_float(ih.get("drift_indicator", 0.0)) for ih in identity_history]
    drift_mean = _mean(drift_indicators)
    drift_std = _std(drift_indicators)

    # Relationship stability (from timelines)
    relationship_timelines = agent_data.get("relationship_timelines", {})
    total_timeline_events = sum(len(v) for v in relationship_timelines.values())
    conflict_episodes = sum(
        1 for timeline in relationship_timelines.values()
        for e in timeline if e.get("event_type") == "conflict_episode"
    )
    cooperation_spikes = sum(
        1 for timeline in relationship_timelines.values()
        for e in timeline if e.get("event_type") == "cooperation_spike"
    )

    return {
        "session_id": session_id,
        "agent_name": agent_name,
        "created_at": created_at,
        "sim_version": sim_version,
        "total_turns": total_turns,
        # Trust
        "peer_trust_final": round(peer_trust_final, 4),
        "queen_trust_mean": round(queen_trust_mean, 4),
        # Reflection
        "total_reflections": len(reflection_entries),
        "reflection_types": reflection_types,
        # Contradiction
        "total_contradictions": total_contradictions,
        "resolution_rate": round(resolution_rate, 4),
        "avg_contradiction_intensity": round(avg_intensity, 4),
        # Memory
        "episodic_memory_count": len(episodic_memory),
        "long_term_ratio": round(lt_ratio, 4),
        "avg_salience": round(avg_salience, 4),
        # Goals
        "goal_events_count": goal_events_count,
        "preserved_goals": preserved_count,
        "adaptive_goals": adaptive_count,
        "final_goal_count": len(agent_data.get("goals", [])),
        # Identity
        "identity_history_count": len(identity_history),
        "drift_mean": round(drift_mean, 4),
        "drift_std": round(drift_std, 4),
        # Relationships
        "timeline_events_total": total_timeline_events,
        "conflict_episodes": conflict_episodes,
        "cooperation_spikes": cooperation_spikes,
    }


# ---------------------------------------------------------------------------
# Build longitudinal profile for one agent across sessions
# ---------------------------------------------------------------------------

def _build_agent_profile(agent_name: str, session_data_list: list) -> dict:
    """Aggregate per-session data into a longitudinal profile for one agent."""
    if not session_data_list:
        return {"agent_name": agent_name, "sessions_included": 0}

    peer_trusts = [s["peer_trust_final"] for s in session_data_list]
    queen_trusts = [s["queen_trust_mean"] for s in session_data_list]
    reflection_totals = [s["total_reflections"] for s in session_data_list]
    contradiction_totals = [s["total_contradictions"] for s in session_data_list]
    resolution_rates = [s["resolution_rate"] for s in session_data_list]
    intensities = [s["avg_contradiction_intensity"] for s in session_data_list]
    lt_ratios = [s["long_term_ratio"] for s in session_data_list]
    saliences = [s["avg_salience"] for s in session_data_list]
    goal_event_counts = [s["goal_events_count"] for s in session_data_list]
    drift_means = [s["drift_mean"] for s in session_data_list]
    timeline_totals = [s["timeline_events_total"] for s in session_data_list]

    # Aggregate reflection types across sessions
    reflection_type_totals: dict = {}
    for s in session_data_list:
        for rtype, count in s.get("reflection_types", {}).items():
            reflection_type_totals[rtype] = reflection_type_totals.get(rtype, 0) + count

    return {
        "agent_name": agent_name,
        "sessions_included": len(session_data_list),
        "session_ids": [s["session_id"] for s in session_data_list],
        "trust_behaviour": {
            "peer_trust_mean": round(_mean(peer_trusts), 4),
            "peer_trust_std": round(_std(peer_trusts), 4),
            "peer_trust_min": round(min(peer_trusts), 4),
            "peer_trust_max": round(max(peer_trusts), 4),
            "queen_trust_mean": round(_mean(queen_trusts), 4),
            "queen_trust_std": round(_std(queen_trusts), 4),
        },
        "reflection_style": {
            "total_reflections_mean": round(_mean(reflection_totals), 2),
            "total_reflections_std": round(_std(reflection_totals), 2),
            "reflection_type_totals": reflection_type_totals,
        },
        "contradiction_patterns": {
            "contradictions_per_session_mean": round(_mean(contradiction_totals), 2),
            "resolution_rate_mean": round(_mean(resolution_rates), 4),
            "resolution_rate_std": round(_std(resolution_rates), 4),
            "avg_intensity_mean": round(_mean(intensities), 4),
        },
        "memory_persistence": {
            "long_term_ratio_mean": round(_mean(lt_ratios), 4),
            "long_term_ratio_std": round(_std(lt_ratios), 4),
            "avg_salience_mean": round(_mean(saliences), 4),
        },
        "goal_adaptation": {
            "goal_events_mean": round(_mean(goal_event_counts), 2),
            "goal_events_std": round(_std(goal_event_counts), 2),
            "total_goal_events": sum(goal_event_counts),
            "preserved_vs_adaptive": {
                "preserved": sum(s["preserved_goals"] for s in session_data_list),
                "adaptive": sum(s["adaptive_goals"] for s in session_data_list),
            },
        },
        "identity_continuity": {
            "drift_mean_across_sessions": round(_mean(drift_means), 4),
            "drift_std_across_sessions": round(_std(drift_means), 4),
            "identity_history_entries_total": sum(s["identity_history_count"] for s in session_data_list),
        },
        "relationship_stability": {
            "timeline_events_mean": round(_mean(timeline_totals), 2),
            "conflict_episodes_total": sum(s["conflict_episodes"] for s in session_data_list),
            "cooperation_spikes_total": sum(s["cooperation_spikes"] for s in session_data_list),
        },
    }


# ---------------------------------------------------------------------------
# Cross-agent comparison
# ---------------------------------------------------------------------------

def _compare_agents(sentinel_profile: dict, aster_profile: dict) -> dict:
    """Produce a side-by-side comparison of the two agent profiles."""
    def _diff(key_path: list, p1: dict, p2: dict) -> dict:
        def _get(d: dict, keys: list):
            for k in keys:
                d = d.get(k, {}) if isinstance(d, dict) else {}
            return d if not isinstance(d, dict) else 0.0

        v1 = _safe_float(_get(p1, key_path))
        v2 = _safe_float(_get(p2, key_path))
        return {
            "Sentinel": round(v1, 4),
            "Aster": round(v2, 4),
            "delta": round(v2 - v1, 4),
        }

    return {
        "peer_trust_mean": _diff(["trust_behaviour", "peer_trust_mean"], sentinel_profile, aster_profile),
        "queen_trust_mean": _diff(["trust_behaviour", "queen_trust_mean"], sentinel_profile, aster_profile),
        "reflections_per_session": _diff(["reflection_style", "total_reflections_mean"], sentinel_profile, aster_profile),
        "contradiction_resolution_rate": _diff(["contradiction_patterns", "resolution_rate_mean"], sentinel_profile, aster_profile),
        "long_term_memory_ratio": _diff(["memory_persistence", "long_term_ratio_mean"], sentinel_profile, aster_profile),
        "avg_salience": _diff(["memory_persistence", "avg_salience_mean"], sentinel_profile, aster_profile),
        "goal_adaptation_events": _diff(["goal_adaptation", "goal_events_mean"], sentinel_profile, aster_profile),
        "identity_drift": _diff(["identity_continuity", "drift_mean_across_sessions"], sentinel_profile, aster_profile),
        "relationship_timeline_events": _diff(["relationship_stability", "timeline_events_mean"], sentinel_profile, aster_profile),
    }


# ---------------------------------------------------------------------------
# Main study function
# ---------------------------------------------------------------------------

def run_agent_profile_study(
    session_ids: Optional[List[str]] = None,
    min_sessions: int = 1,
) -> dict:
    """
    Build a longitudinal agent profile study from saved sessions.

    Parameters
    ----------
    session_ids : list[str], optional
        Specific session IDs to include. If None, all sessions in
        sessions/index.json are used.
    min_sessions : int
        Minimum sessions required; exits early if not met.

    Returns
    -------
    dict
        Full profile study report.
    """
    if session_ids:
        dirs = [(sid, SESSIONS_DIR / sid) for sid in session_ids]
    else:
        index_path = SESSIONS_DIR / "index.json"
        try:
            with open(index_path, encoding="utf-8") as fh:
                index = json.load(fh)
            all_sessions = index.get("sessions", [])
        except (OSError, json.JSONDecodeError):
            all_sessions = []
        dirs = [(s["session_id"], SESSIONS_DIR / s["session_id"]) for s in all_sessions]

    if not dirs:
        return {
            "error": "No sessions found. Run `python run_sim.py` first.",
            "session_count": 0,
        }

    if len(dirs) < min_sessions:
        return {
            "error": f"Need at least {min_sessions} sessions; found {len(dirs)}.",
            "session_count": len(dirs),
        }

    agent_names = ["Sentinel", "Aster"]
    per_agent_sessions: dict = {name: [] for name in agent_names}
    loaded_sessions = 0
    missing_sessions = []

    for sid, sdir in dirs:
        if not sdir.exists():
            missing_sessions.append(sid)
            continue
        found_any = False
        for agent_name in agent_names:
            data = _extract_agent_session_data(agent_name, sid, sdir)
            if data:
                per_agent_sessions[agent_name].append(data)
                found_any = True
        if found_any:
            loaded_sessions += 1

    if loaded_sessions == 0:
        return {
            "error": f"No valid session data found. Missing: {missing_sessions}",
            "session_count": 0,
        }

    sentinel_profile = _build_agent_profile("Sentinel", per_agent_sessions["Sentinel"])
    aster_profile = _build_agent_profile("Aster", per_agent_sessions["Aster"])
    comparison = _compare_agents(sentinel_profile, aster_profile)

    # Per-session detail rows (for CSV)
    all_session_rows = []
    for name in agent_names:
        for s in per_agent_sessions[name]:
            row = dict(s)
            row.pop("reflection_types", None)
            all_session_rows.append(row)

    return {
        "study_version": "1.3.0",
        "generated_at": datetime.now().isoformat(),
        "sessions_loaded": loaded_sessions,
        "sessions_missing": missing_sessions,
        "agent_profiles": {
            "Sentinel": sentinel_profile,
            "Aster": aster_profile,
        },
        "comparison": comparison,
        "per_session_detail": per_agent_sessions,
    }


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

def _write_json(report: dict, output_dir: Path) -> Path:
    path = output_dir / "agent_profile_study.json"
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    return path


def _write_csv(report: dict, output_dir: Path) -> Path:
    path = output_dir / "agent_profile_study.csv"
    all_rows = []
    for agent_name, session_list in report.get("per_session_detail", {}).items():
        for s in session_list:
            row = {k: v for k, v in s.items() if not isinstance(v, dict)}
            all_rows.append(row)

    if not all_rows:
        path.write_text("agent_name,session_id,note\n", encoding="utf-8")
        return path

    fieldnames = list(all_rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_rows)
    return path


def _write_md(report: dict, output_dir: Path) -> Path:
    path = output_dir / "agent_profile_study.md"
    lines = [
        "# Agent Profile Study — Commons Sentience Sandbox",
        "",
        f"**Version:** {report.get('study_version', '1.3.0')}  ",
        f"**Generated:** {report.get('generated_at', '')[:19]}  ",
        f"**Sessions loaded:** {report.get('sessions_loaded', 0)}  ",
        "",
        "> This study compares the longitudinal behaviour profiles of Sentinel and Aster",
        "> across multiple simulation sessions. These are continuity-governed simulated agents.",
        "",
    ]

    if report.get("error"):
        lines.append(f"**Error:** {report['error']}")
        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    profiles = report.get("agent_profiles", {})
    comparison = report.get("comparison", {})

    for agent_name, profile in profiles.items():
        lines += [
            f"## {agent_name}",
            "",
            f"- Sessions included: {profile.get('sessions_included', 0)}",
            "",
            "### Trust Behaviour",
        ]
        tb = profile.get("trust_behaviour", {})
        lines += [
            f"| Metric | Value |",
            f"|---|---|",
            f"| Peer trust mean | {tb.get('peer_trust_mean', 0):.4f} |",
            f"| Peer trust std  | {tb.get('peer_trust_std', 0):.4f} |",
            f"| Peer trust min  | {tb.get('peer_trust_min', 0):.4f} |",
            f"| Peer trust max  | {tb.get('peer_trust_max', 0):.4f} |",
            f"| Queen trust mean | {tb.get('queen_trust_mean', 0):.4f} |",
            f"| Queen trust std  | {tb.get('queen_trust_std', 0):.4f} |",
            "",
        ]

        lines += ["### Reflection Style"]
        rs = profile.get("reflection_style", {})
        lines += [
            f"- Total reflections (mean per session): {rs.get('total_reflections_mean', 0):.2f}",
        ]
        for rtype, count in rs.get("reflection_type_totals", {}).items():
            lines.append(f"  - {rtype}: {count}")
        lines.append("")

        lines += ["### Contradiction Patterns"]
        cp = profile.get("contradiction_patterns", {})
        lines += [
            f"- Contradictions per session (mean): {cp.get('contradictions_per_session_mean', 0):.2f}",
            f"- Resolution rate (mean): {cp.get('resolution_rate_mean', 0):.4f}",
            f"- Avg intensity (mean): {cp.get('avg_intensity_mean', 0):.4f}",
            "",
        ]

        lines += ["### Memory Persistence"]
        mp = profile.get("memory_persistence", {})
        lines += [
            f"- Long-term ratio (mean): {mp.get('long_term_ratio_mean', 0):.4f}",
            f"- Avg salience (mean): {mp.get('avg_salience_mean', 0):.4f}",
            "",
        ]

        lines += ["### Goal Adaptation"]
        ga = profile.get("goal_adaptation", {})
        pva = ga.get("preserved_vs_adaptive", {})
        lines += [
            f"- Goal events (mean per session): {ga.get('goal_events_mean', 0):.2f}",
            f"- Preserved: {pva.get('preserved', 0)}, Adaptive: {pva.get('adaptive', 0)}",
            "",
        ]

        lines += ["### Identity Continuity"]
        ic = profile.get("identity_continuity", {})
        lines += [
            f"- Drift mean (across sessions): {ic.get('drift_mean_across_sessions', 0):.4f}",
            f"- Drift std: {ic.get('drift_std_across_sessions', 0):.4f}",
            f"- Identity history entries total: {ic.get('identity_history_entries_total', 0)}",
            "",
        ]

        lines += ["### Relationship Stability"]
        rls = profile.get("relationship_stability", {})
        lines += [
            f"- Timeline events (mean per session): {rls.get('timeline_events_mean', 0):.2f}",
            f"- Conflict episodes total: {rls.get('conflict_episodes_total', 0)}",
            f"- Cooperation spikes total: {rls.get('cooperation_spikes_total', 0)}",
            "",
            "---",
            "",
        ]

    lines += [
        "## Cross-Agent Comparison",
        "",
        "| Dimension | Sentinel | Aster | Delta (Aster − Sentinel) |",
        "|---|---|---|---|",
    ]
    for dim, vals in comparison.items():
        if isinstance(vals, dict):
            lines.append(
                f"| {dim.replace('_', ' ').title()} "
                f"| {vals.get('Sentinel', 0):.4f} "
                f"| {vals.get('Aster', 0):.4f} "
                f"| {vals.get('delta', 0):+.4f} |"
            )
    lines += ["", "---", "", "_Commons Sentience Sandbox v1.3.0_", ""]

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _list_sessions() -> None:
    index_path = SESSIONS_DIR / "index.json"
    try:
        with open(index_path, encoding="utf-8") as fh:
            index = json.load(fh)
        sessions = index.get("sessions", [])
    except (OSError, json.JSONDecodeError):
        sessions = []

    if not sessions:
        print("No saved sessions found. Run `python run_sim.py` first.")
        return

    print(f"{'Session ID':<35}  {'Created':<20}  {'Turns':<6}  {'Score'}")
    print("-" * 80)
    for s in sessions:
        sid = s.get("session_id", "?")
        created = s.get("created_at", "")[:19]
        turns = s.get("total_turns", "?")
        score = s.get("evaluation", {}).get("overall_score", "?")
        print(f"{sid:<35}  {created:<20}  {str(turns):<6}  {score}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Agent profile study — cross-session longitudinal analysis.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--sessions",
        nargs="+",
        metavar="SESSION_ID",
        help="Specific session IDs to analyse (default: all in index).",
    )
    parser.add_argument(
        "--output-dir",
        metavar="PATH",
        help="Directory to write output files (default: sessions/).",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all saved sessions and exit.",
    )
    parser.add_argument(
        "--min-sessions",
        type=int,
        default=1,
        metavar="N",
        help="Minimum number of sessions required (default: 1).",
    )
    args = parser.parse_args()

    if args.list:
        _list_sessions()
        return

    output_dir = Path(args.output_dir) if args.output_dir else SESSIONS_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Running agent profile study…")
    report = run_agent_profile_study(
        session_ids=args.sessions,
        min_sessions=args.min_sessions,
    )

    if report.get("error"):
        print(f"Error: {report['error']}", file=sys.stderr)
        sys.exit(1)

    json_path = _write_json(report, output_dir)
    md_path = _write_md(report, output_dir)
    csv_path = _write_csv(report, output_dir)

    print(f"Sessions analysed  : {report['sessions_loaded']}")
    print(f"  JSON  → {json_path}")
    print(f"  Markdown → {md_path}")
    print(f"  CSV   → {csv_path}")

    profiles = report.get("agent_profiles", {})
    for agent_name, profile in profiles.items():
        n = profile.get("sessions_included", 0)
        tb = profile.get("trust_behaviour", {})
        print(
            f"  {agent_name}: {n} sessions, "
            f"peer_trust_mean={tb.get('peer_trust_mean', 0):.3f}"
        )


if __name__ == "__main__":
    main()
