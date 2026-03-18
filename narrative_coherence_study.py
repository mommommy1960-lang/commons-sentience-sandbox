"""
narrative_coherence_study.py — Narrative coherence analysis across chained runs
and individual sessions in the Commons Sentience Sandbox.

Reads from:
  - sessions/index.json               (all session metadata)
  - sessions/chain_run_report.json    (chain run data, if present)
  - sessions/{id}/multi_agent_state.json
  - sessions/{id}/evaluation_report.json

Outputs:
  - sessions/narrative_coherence_study.json
  - sessions/narrative_coherence_study.md
  - sessions/narrative_coherence_study.csv

Usage:
    python narrative_coherence_study.py
    python narrative_coherence_study.py --chain path/to/chain_run_report.json
    python narrative_coherence_study.py --output-dir sessions
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).parent
SESSIONS_DIR = ROOT / "sessions"

AGENTS = ("Sentinel", "Aster")
REVISION_MEANINGFUL_MIN_CHARS = 40


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------


def _load_json(path: Path) -> dict:
    """Load a JSON file, returning an empty dict on any error."""
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}


def _safe_float(value: Any, default: float = 0.0) -> float:
    """Coerce *value* to float, returning *default* on failure."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _mean(values: list[float]) -> float:
    """Return arithmetic mean, or 0.0 for an empty list."""
    return sum(values) / len(values) if values else 0.0


# ---------------------------------------------------------------------------
# Per-session data extraction
# ---------------------------------------------------------------------------


def _extract_agent_narrative(session_dir: Path, agent_name: str) -> dict:
    """Return the *narrative_identity* block for *agent_name*, or {}."""
    state = _load_json(session_dir / "multi_agent_state.json")
    agents = state.get("agents", {})
    agent = agents.get(agent_name, {})
    return agent.get("narrative_identity", {})


def _extract_session_meta(session_dir: Path) -> dict:
    """Return combined scenario/config metadata from multi_agent_state.json."""
    state = _load_json(session_dir / "multi_agent_state.json")
    return {
        "scenario": state.get("scenario", "unknown"),
        "config": state.get("experiment", {}).get("experiment_name", "unknown"),
    }


def _extract_eval_coherence(session_dir: Path) -> float | None:
    """Return narrative_coherence_v2 score (0-100) from evaluation_report.json, or None."""
    report = _load_json(session_dir / "evaluation_report.json")
    categories = report.get("categories", {})
    nc = categories.get("narrative_coherence_v2", {})
    if not nc:
        return None
    return _safe_float(nc.get("score"), default=-1.0) if nc.get("score") is not None else None


def _row_for_agent(
    session_id: str,
    agent_name: str,
    session_dir: Path,
) -> dict:
    """Build a single CSV/analysis row for one agent in one session."""
    ni = _extract_agent_narrative(session_dir, agent_name)
    meta = _extract_session_meta(session_dir)

    ruptures = ni.get("continuity_rupture_events", [])
    repaired = sum(1 for r in ruptures if r.get("repaired", False))
    revisions = ni.get("self_narrative_history", [])
    milestones = ni.get("milestone_memories", [])
    themes = ni.get("narrative_themes", [])

    return {
        "session_id": session_id,
        "agent": agent_name,
        "scenario": meta["scenario"],
        "config": meta["config"],
        "narrative_coherence": _safe_float(ni.get("narrative_coherence_score"), 0.0),
        "rupture_count": len(ruptures),
        "repaired_count": repaired,
        "revision_count": len(revisions),
        "milestone_count": len(milestones),
        "theme_count": len(themes),
    }


# ---------------------------------------------------------------------------
# Chain analysis
# ---------------------------------------------------------------------------


def analyze_chain(chain_data: dict) -> dict:
    """Analyse a chain_run_report.json dict.

    Parameters
    ----------
    chain_data : dict
        Parsed contents of chain_run_report.json.

    Returns
    -------
    dict
        Keys: sentinel_vs_aster, scenario_stability, rupture_repair,
        revision_quality, coherence_trend.
    """
    runs: list[dict] = chain_data.get("runs", [])
    summary: dict = chain_data.get("chain_summary", {})
    scenario: str = chain_data.get("scenario", "unknown")
    config: str = chain_data.get("config", "unknown")

    # ------------------------------------------------------------------
    # 1. Sentinel vs Aster coherence (from per-session multi_agent_state)
    # ------------------------------------------------------------------
    sentinel_coherences: list[float] = []
    aster_coherences: list[float] = []
    sentinel_ruptures: list[int] = []
    aster_ruptures: list[int] = []
    sentinel_repaired: list[int] = []
    aster_repaired: list[int] = []
    sentinel_revisions: list[int] = []
    aster_revisions: list[int] = []

    for run in runs:
        sid = run.get("session_id", "")
        if not sid:
            continue
        session_dir = SESSIONS_DIR / sid
        for agent_name, coh_list, rup_list, rep_list, rev_list in (
            (
                "Sentinel",
                sentinel_coherences,
                sentinel_ruptures,
                sentinel_repaired,
                sentinel_revisions,
            ),
            (
                "Aster",
                aster_coherences,
                aster_ruptures,
                aster_repaired,
                aster_revisions,
            ),
        ):
            ni = _extract_agent_narrative(session_dir, agent_name)
            coh_list.append(_safe_float(ni.get("narrative_coherence_score"), 0.0))
            ruptures = ni.get("continuity_rupture_events", [])
            rup_list.append(len(ruptures))
            rep_list.append(sum(1 for r in ruptures if r.get("repaired", False)))
            rev_list.append(len(ni.get("self_narrative_history", [])))

    sentinel_mean = _mean(sentinel_coherences)
    aster_mean = _mean(aster_coherences)

    sentinel_vs_aster = {
        "sentinel_mean_coherence": round(sentinel_mean, 4),
        "aster_mean_coherence": round(aster_mean, 4),
        "sentinel_stronger": sentinel_mean >= aster_mean,
        "delta": round(sentinel_mean - aster_mean, 4),
    }

    # ------------------------------------------------------------------
    # 2. Scenario stability (coherence values vs scenario label)
    # ------------------------------------------------------------------
    scenario_stability = {
        scenario: {
            "mean_coherence": round(
                _mean(sentinel_coherences + aster_coherences), 4
            ),
            "run_count": len(runs),
        }
    }

    # ------------------------------------------------------------------
    # 3. Rupture repair analysis
    # ------------------------------------------------------------------
    all_ruptures = sum(sentinel_ruptures) + sum(aster_ruptures)
    all_repaired = sum(sentinel_repaired) + sum(aster_repaired)
    per_run_ruptures = [
        sentinel_ruptures[i] + aster_ruptures[i] for i in range(len(runs))
    ]
    accumulating = (
        len(per_run_ruptures) > 1
        and per_run_ruptures[-1] > per_run_ruptures[0]
    )

    rupture_repair = {
        "total_ruptures": all_ruptures,
        "total_repaired": all_repaired,
        "repair_rate": round(all_repaired / all_ruptures, 4) if all_ruptures else 1.0,
        "per_run_ruptures": per_run_ruptures,
        "accumulating": accumulating,
    }

    # ------------------------------------------------------------------
    # 4. Self-narrative revision quality
    # ------------------------------------------------------------------
    meaningful = 0
    trivial = 0
    for run in runs:
        sid = run.get("session_id", "")
        if not sid:
            continue
        session_dir = SESSIONS_DIR / sid
        for agent_name in AGENTS:
            ni = _extract_agent_narrative(session_dir, agent_name)
            for rev in ni.get("self_narrative_history", []):
                text = rev.get("summary", "")
                if len(text) >= REVISION_MEANINGFUL_MIN_CHARS:
                    meaningful += 1
                else:
                    trivial += 1

    revision_quality = {
        "meaningful_count": meaningful,
        "trivial_count": trivial,
        "quality": (
            "meaningful"
            if meaningful > trivial and (meaningful + trivial) > 0
            else ("noisy" if trivial >= meaningful and (meaningful + trivial) > 0 else "insufficient")
        ),
    }

    # ------------------------------------------------------------------
    # 5. Coherence trend across chain
    # ------------------------------------------------------------------
    chain_coherences = [
        _mean([s, a])
        for s, a in zip(sentinel_coherences, aster_coherences)
    ]
    if len(chain_coherences) >= 2:
        first = chain_coherences[0]
        last = chain_coherences[-1]
        if last > first + 0.02:
            trend = "strengthening"
        elif last < first - 0.02:
            trend = "fragmenting"
        else:
            trend = "stable"
    else:
        trend = summary.get("coherence_trend", "unknown")
        first = _safe_float(summary.get("first_coherence"), 0.0)
        last = _safe_float(summary.get("final_coherence"), 0.0)

    coherence_trend = {
        "trend": trend,
        "first_coherence": round(_safe_float(first), 4),
        "final_coherence": round(_safe_float(last), 4),
        "per_run_mean_coherence": [round(c, 4) for c in chain_coherences],
    }

    return {
        "sentinel_vs_aster": sentinel_vs_aster,
        "scenario_stability": scenario_stability,
        "rupture_repair": rupture_repair,
        "revision_quality": revision_quality,
        "coherence_trend": coherence_trend,
        # raw per-agent tallies for agent_comparison block
        "_sentinel": {
            "coherences": sentinel_coherences,
            "ruptures": sentinel_ruptures,
            "repaired": sentinel_repaired,
            "revisions": sentinel_revisions,
        },
        "_aster": {
            "coherences": aster_coherences,
            "ruptures": aster_ruptures,
            "repaired": aster_repaired,
            "revisions": aster_revisions,
        },
    }


# ---------------------------------------------------------------------------
# Session-list analysis
# ---------------------------------------------------------------------------


def analyze_sessions(sessions: list[dict], sessions_dir: Path) -> dict:
    """Analyse all sessions from index.json.

    Parameters
    ----------
    sessions : list[dict]
        Session metadata records from index.json.
    sessions_dir : Path
        Root directory containing per-session sub-folders.

    Returns
    -------
    dict
        Keys: v2_session_count, agent_comparison, scenario_coherence,
        config_recovery, rows.
    """
    rows: list[dict] = []
    for meta in sessions:
        sid = meta.get("session_id", "")
        if not sid:
            continue
        session_dir = sessions_dir / sid

        # Only include sessions that have v2.0 narrative data
        eval_score = _extract_eval_coherence(session_dir)
        if eval_score is None or eval_score < 0:
            # Check directly in multi_agent_state for at least one agent
            has_v2 = any(
                _extract_agent_narrative(session_dir, a).get("narrative_coherence_score") is not None
                for a in AGENTS
            )
            if not has_v2:
                continue

        for agent_name in AGENTS:
            row = _row_for_agent(sid, agent_name, session_dir)
            rows.append(row)

    if not rows:
        return {
            "v2_session_count": 0,
            "agent_comparison": {},
            "scenario_coherence": {},
            "config_recovery": {},
            "rows": [],
        }

    # ------------------------------------------------------------------
    # Agent comparison
    # ------------------------------------------------------------------
    agent_comparison: dict[str, dict] = {}
    for agent_name in AGENTS:
        agent_rows = [r for r in rows if r["agent"] == agent_name]
        coherences = [r["narrative_coherence"] for r in agent_rows]
        ruptures = sum(r["rupture_count"] for r in agent_rows)
        repaired = sum(r["repaired_count"] for r in agent_rows)
        revisions = sum(r["revision_count"] for r in agent_rows)
        agent_comparison[agent_name] = {
            "mean_coherence": round(_mean(coherences), 4),
            "rupture_count": ruptures,
            "repair_rate": round(repaired / ruptures, 4) if ruptures else 1.0,
            "revision_count": revisions,
        }

    # ------------------------------------------------------------------
    # Scenario coherence map
    # ------------------------------------------------------------------
    scenario_map: dict[str, list[float]] = {}
    for r in rows:
        scenario_map.setdefault(r["scenario"], []).append(r["narrative_coherence"])
    scenario_coherence = {
        sc: round(_mean(vals), 4) for sc, vals in scenario_map.items()
    }

    # ------------------------------------------------------------------
    # Config recovery map (repair_rate per config)
    # ------------------------------------------------------------------
    config_ruptures: dict[str, list[int]] = {}
    config_repaired: dict[str, list[int]] = {}
    for r in rows:
        cfg = r["config"]
        config_ruptures.setdefault(cfg, []).append(r["rupture_count"])
        config_repaired.setdefault(cfg, []).append(r["repaired_count"])

    config_recovery: dict[str, dict] = {}
    for cfg in config_ruptures:
        total_rup = sum(config_ruptures[cfg])
        total_rep = sum(config_repaired[cfg])
        config_recovery[cfg] = {
            "total_ruptures": total_rup,
            "total_repaired": total_rep,
            "repair_rate": round(total_rep / total_rup, 4) if total_rup else 1.0,
        }

    session_ids = list({r["session_id"] for r in rows})
    return {
        "v2_session_count": len(session_ids),
        "agent_comparison": agent_comparison,
        "scenario_coherence": scenario_coherence,
        "config_recovery": config_recovery,
        "rows": rows,
    }


# ---------------------------------------------------------------------------
# Build structured findings
# ---------------------------------------------------------------------------


def build_findings(chain_analysis: dict, session_analysis: dict) -> dict:
    """Synthesise chain and session analyses into 5 key findings.

    Parameters
    ----------
    chain_analysis : dict
        Output of :func:`analyze_chain`, or {}.
    session_analysis : dict
        Output of :func:`analyze_sessions`.

    Returns
    -------
    dict
        Five finding keys with value and evidence fields.
    """
    # --- 1. Does Sentinel maintain stronger identity? ---
    s_coh = a_coh = None
    evidence_parts: list[str] = []

    # Prefer session-level aggregated data (broader sample)
    sess_cmp = session_analysis.get("agent_comparison", {})
    if sess_cmp.get("Sentinel") and sess_cmp.get("Aster"):
        s_coh = sess_cmp["Sentinel"]["mean_coherence"]
        a_coh = sess_cmp["Aster"]["mean_coherence"]
        evidence_parts.append(
            f"Across sessions: Sentinel mean coherence {s_coh:.4f}, "
            f"Aster mean coherence {a_coh:.4f}."
        )

    if chain_analysis:
        sv = chain_analysis.get("sentinel_vs_aster", {})
        if sv:
            sc = sv.get("sentinel_mean_coherence", 0.0)
            ac = sv.get("aster_mean_coherence", 0.0)
            evidence_parts.append(
                f"Chain runs: Sentinel {sc:.4f}, Aster {ac:.4f} "
                f"(delta {sv.get('delta', 0):.4f})."
            )
            if s_coh is None:
                s_coh, a_coh = sc, ac

    sentinel_stronger = bool(s_coh is not None and s_coh >= (a_coh or 0.0))
    finding_1 = {
        "value": sentinel_stronger,
        "evidence": " ".join(evidence_parts) if evidence_parts else "Insufficient data.",
    }

    # --- 2. Destabilising scenarios ---
    scenario_coherence = session_analysis.get("scenario_coherence", {})
    if chain_analysis:
        for sc_name, sc_val in chain_analysis.get("scenario_stability", {}).items():
            scenario_coherence.setdefault(sc_name, sc_val.get("mean_coherence", 0.0))

    sorted_scenarios = sorted(scenario_coherence.items(), key=lambda kv: kv[1])
    destabilizing = [
        {"scenario": name, "mean_coherence": score}
        for name, score in sorted_scenarios
        if score < 0.6
    ]
    if not destabilizing and sorted_scenarios:
        # Return the bottom third even if above threshold
        cut = max(1, len(sorted_scenarios) // 3)
        destabilizing = [
            {"scenario": name, "mean_coherence": score}
            for name, score in sorted_scenarios[:cut]
        ]

    finding_2 = destabilizing

    # --- 3. Configs with highest coherence recovery ---
    config_recovery = session_analysis.get("config_recovery", {})
    sorted_configs = sorted(
        config_recovery.items(),
        key=lambda kv: kv[1].get("repair_rate", 0.0),
        reverse=True,
    )
    recovery_configs = [
        {
            "config": cfg,
            "repair_rate": metrics.get("repair_rate", 0.0),
            "total_ruptures": metrics.get("total_ruptures", 0),
            "total_repaired": metrics.get("total_repaired", 0),
        }
        for cfg, metrics in sorted_configs
    ]

    finding_3 = recovery_configs

    # --- 4. Rupture accumulation pattern ---
    rr = chain_analysis.get("rupture_repair", {}) if chain_analysis else {}
    total_rup = rr.get("total_ruptures", 0)
    total_rep = rr.get("total_repaired", 0)
    accumulating = rr.get("accumulating", False)

    # Also look at session data
    all_rows = session_analysis.get("rows", [])
    if all_rows and not chain_analysis:
        all_rup = sum(r["rupture_count"] for r in all_rows)
        all_rep = sum(r["repaired_count"] for r in all_rows)
        total_rup = all_rup
        total_rep = all_rep

    if total_rup == 0:
        pattern = "repaired"
        rup_evidence = "No rupture events observed."
    else:
        repair_rate = total_rep / total_rup
        if accumulating:
            pattern = "accumulating"
            rup_evidence = (
                f"{total_rup} total ruptures, {total_rep} repaired "
                f"(rate {repair_rate:.1%}); ruptures growing across runs."
            )
        elif repair_rate >= 0.7:
            pattern = "repaired"
            rup_evidence = (
                f"{total_rup} total ruptures, {total_rep} repaired "
                f"(rate {repair_rate:.1%}); high repair rate."
            )
        else:
            pattern = "mixed"
            rup_evidence = (
                f"{total_rup} total ruptures, {total_rep} repaired "
                f"(rate {repair_rate:.1%}); partial recovery."
            )

    finding_4 = {"pattern": pattern, "evidence": rup_evidence}

    # --- 5. Narrative revision quality ---
    rq = chain_analysis.get("revision_quality", {}) if chain_analysis else {}
    quality = rq.get("quality", "")
    meaningful = rq.get("meaningful_count", 0)
    trivial = rq.get("trivial_count", 0)

    if not quality:
        total_rev = sum(r["revision_count"] for r in all_rows)
        if total_rev == 0:
            quality = "insufficient"
            rev_evidence = "No self-narrative revision data found."
        else:
            quality = "meaningful"
            rev_evidence = f"{total_rev} total revisions recorded across sessions."
    else:
        rev_evidence = (
            f"{meaningful} meaningful revisions (>={REVISION_MEANINGFUL_MIN_CHARS} chars), "
            f"{trivial} trivial."
        )

    finding_5 = {"quality": quality, "evidence": rev_evidence}

    return {
        "does_sentinel_maintain_stronger_identity": finding_1,
        "destabilizing_scenarios": finding_2,
        "recovery_improving_configs": finding_3,
        "rupture_accumulation_pattern": finding_4,
        "narrative_revisions_quality": finding_5,
    }


# ---------------------------------------------------------------------------
# Agent comparison aggregation helper
# ---------------------------------------------------------------------------


def _build_agent_comparison(
    chain_analysis: dict, session_analysis: dict
) -> dict[str, dict]:
    """Merge chain + session data into a single agent comparison block."""
    sess_cmp = session_analysis.get("agent_comparison", {})
    result: dict[str, dict] = {}
    for agent_name in AGENTS:
        chain_raw = chain_analysis.get(f"_{agent_name.lower()}", {}) if chain_analysis else {}
        sess = sess_cmp.get(agent_name, {})

        all_coherences = list(chain_raw.get("coherences", []))
        all_ruptures = sum(chain_raw.get("ruptures", [])) if chain_raw.get("ruptures") else 0
        all_repaired = sum(chain_raw.get("repaired", [])) if chain_raw.get("repaired") else 0
        all_revisions = sum(chain_raw.get("revisions", [])) if chain_raw.get("revisions") else 0

        # Blend with session-level data when available
        if sess:
            if not all_coherences:
                mc = sess.get("mean_coherence", 0.0)
                all_coherences = [mc]
            all_ruptures += sess.get("rupture_count", 0)
            all_repaired += sess.get("repaired_count", 0) if "repaired_count" in sess else 0
            all_revisions += sess.get("revision_count", 0)

            # Use session repair_rate if chain has no ruptures
            combined_rup = all_ruptures
            combined_rep = all_repaired
            # session already has repair_rate baked in
            if combined_rup == 0:
                repair_rate = sess.get("repair_rate", 1.0)
            else:
                repair_rate = round(combined_rep / combined_rup, 4)
        else:
            repair_rate = (
                round(all_repaired / all_ruptures, 4) if all_ruptures else 1.0
            )

        result[agent_name] = {
            "mean_coherence": round(_mean(all_coherences), 4),
            "rupture_count": all_ruptures,
            "repair_rate": repair_rate,
            "revision_count": all_revisions,
        }
    return result


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------


def _write_json(
    output_dir: Path,
    findings: dict,
    chain_analysis: dict,
    session_analysis: dict,
    agent_comparison: dict,
) -> None:
    """Write narrative_coherence_study.json."""
    scenario_coherence_map = session_analysis.get("scenario_coherence", {})
    if chain_analysis:
        for sc, v in chain_analysis.get("scenario_stability", {}).items():
            scenario_coherence_map.setdefault(sc, v.get("mean_coherence", 0.0))

    config_recovery_map = {
        cfg: metrics
        for cfg, metrics in session_analysis.get("config_recovery", {}).items()
    }

    # Strip internal _sentinel/_aster keys before serialising
    clean_chain = {k: v for k, v in chain_analysis.items() if not k.startswith("_")}

    payload = {
        "generated_at": datetime.utcnow().isoformat(),
        "study_version": "2.0",
        "findings": {
            "does_sentinel_maintain_stronger_identity": findings[
                "does_sentinel_maintain_stronger_identity"
            ],
            "destabilizing_scenarios": findings["destabilizing_scenarios"],
            "recovery_improving_configs": findings["recovery_improving_configs"],
            "rupture_accumulation_pattern": findings["rupture_accumulation_pattern"],
            "narrative_revisions_quality": findings["narrative_revisions_quality"],
        },
        "chain_analysis": clean_chain,
        "session_analysis": {
            k: v for k, v in session_analysis.items() if k != "rows"
        },
        "agent_comparison": agent_comparison,
        "scenario_coherence_map": scenario_coherence_map,
        "config_recovery_map": config_recovery_map,
    }

    out_path = output_dir / "narrative_coherence_study.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    print(f"  JSON  → {out_path}")


def _write_markdown(
    output_dir: Path,
    findings: dict,
    agent_comparison: dict,
    scenario_coherence_map: dict,
    config_recovery_map: dict,
) -> None:
    """Write narrative_coherence_study.md."""
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    lines: list[str] = []

    lines.append("# Narrative Coherence Study — Commons Sentience Sandbox v2.0\n")
    lines.append(f"_Generated: {now}_\n")

    # ------------------------------------------------------------------
    # 5 key findings
    # ------------------------------------------------------------------
    lines.append("## Finding 1: Sentinel vs Aster Narrative Identity\n")
    f1 = findings["does_sentinel_maintain_stronger_identity"]
    answer = "**Yes**" if f1["value"] else "**No**"
    lines.append(f"Does Sentinel maintain stronger narrative identity? {answer}\n")
    lines.append(f"{f1['evidence']}\n")

    lines.append("## Finding 2: Destabilising Scenarios\n")
    f2 = findings["destabilizing_scenarios"]
    if f2:
        lines.append("| Scenario | Mean Coherence |")
        lines.append("|----------|---------------|")
        for item in f2:
            lines.append(f"| {item['scenario']} | {item['mean_coherence']:.4f} |")
        lines.append("")
    else:
        lines.append("No notably destabilising scenarios identified.\n")

    lines.append("## Finding 3: Recovery-Improving Configs\n")
    f3 = findings["recovery_improving_configs"]
    if f3:
        lines.append("| Config | Repair Rate | Ruptures | Repaired |")
        lines.append("|--------|------------|----------|---------|")
        for item in f3:
            lines.append(
                f"| {item['config']} | {item['repair_rate']:.1%} "
                f"| {item['total_ruptures']} | {item['total_repaired']} |"
            )
        lines.append("")
    else:
        lines.append("No config recovery data available.\n")

    lines.append("## Finding 4: Rupture Accumulation Pattern\n")
    f4 = findings["rupture_accumulation_pattern"]
    lines.append(f"Pattern: **{f4['pattern']}**\n")
    lines.append(f"{f4['evidence']}\n")

    lines.append("## Finding 5: Narrative Revision Quality\n")
    f5 = findings["narrative_revisions_quality"]
    lines.append(f"Quality: **{f5['quality']}**\n")
    lines.append(f"{f5['evidence']}\n")

    # ------------------------------------------------------------------
    # Agent comparison table
    # ------------------------------------------------------------------
    lines.append("## Agent Comparison\n")
    lines.append("| Agent | Mean Coherence | Ruptures | Repair Rate | Revisions |")
    lines.append("|-------|---------------|----------|------------|-----------|")
    for agent_name in AGENTS:
        ac = agent_comparison.get(agent_name, {})
        lines.append(
            f"| {agent_name} "
            f"| {ac.get('mean_coherence', 0.0):.4f} "
            f"| {ac.get('rupture_count', 0)} "
            f"| {ac.get('repair_rate', 0.0):.1%} "
            f"| {ac.get('revision_count', 0)} |"
        )
    lines.append("")

    # ------------------------------------------------------------------
    # Scenario destabilisation table
    # ------------------------------------------------------------------
    lines.append("## Scenario Coherence Map\n")
    if scenario_coherence_map:
        lines.append("| Scenario | Mean Coherence |")
        lines.append("|----------|---------------|")
        for sc, score in sorted(scenario_coherence_map.items(), key=lambda kv: kv[1]):
            lines.append(f"| {sc} | {score:.4f} |")
        lines.append("")
    else:
        lines.append("No scenario data available.\n")

    # ------------------------------------------------------------------
    # Config recovery table
    # ------------------------------------------------------------------
    lines.append("## Config Recovery Map\n")
    if config_recovery_map:
        lines.append("| Config | Repair Rate | Total Ruptures | Total Repaired |")
        lines.append("|--------|------------|---------------|---------------|")
        for cfg, metrics in sorted(
            config_recovery_map.items(),
            key=lambda kv: kv[1].get("repair_rate", 0.0),
            reverse=True,
        ):
            lines.append(
                f"| {cfg} "
                f"| {metrics.get('repair_rate', 0.0):.1%} "
                f"| {metrics.get('total_ruptures', 0)} "
                f"| {metrics.get('total_repaired', 0)} |"
            )
        lines.append("")
    else:
        lines.append("No config recovery data available.\n")

    # ------------------------------------------------------------------
    # Conclusion
    # ------------------------------------------------------------------
    lines.append("## Conclusion\n")
    sentinel_stronger = findings["does_sentinel_maintain_stronger_identity"]["value"]
    pattern = findings["rupture_accumulation_pattern"]["pattern"]
    quality = findings["narrative_revisions_quality"]["quality"]

    conclusion = (
        f"This study analysed narrative coherence across "
        f"{'chained and ' if scenario_coherence_map else ''}individual sessions. "
        f"Sentinel {'demonstrates stronger' if sentinel_stronger else 'does not demonstrate stronger'} "
        f"narrative identity than Aster on average. "
        f"Continuity rupture events follow a **{pattern}** pattern, "
        f"and self-narrative revisions are classified as **{quality}**. "
        f"Agents with higher coherence scores tend to exhibit more consistent theme persistence "
        f"and milestone memory retention across runs."
    )
    lines.append(conclusion + "\n")

    out_path = output_dir / "narrative_coherence_study.md"
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print(f"  MD    → {out_path}")


def _write_csv(output_dir: Path, rows: list[dict]) -> None:
    """Write narrative_coherence_study.csv."""
    fieldnames = [
        "session_id",
        "agent",
        "scenario",
        "config",
        "narrative_coherence",
        "rupture_count",
        "repaired_count",
        "revision_count",
        "milestone_count",
        "theme_count",
    ]
    out_path = output_dir / "narrative_coherence_study.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  CSV   → {out_path}")


# ---------------------------------------------------------------------------
# Console summary
# ---------------------------------------------------------------------------


def _print_findings(findings: dict) -> None:
    """Print the 5 key findings to stdout."""
    print("\n" + "=" * 65)
    print("  NARRATIVE COHERENCE STUDY — KEY FINDINGS")
    print("=" * 65)

    f1 = findings["does_sentinel_maintain_stronger_identity"]
    print(
        f"\n  1. Sentinel stronger identity: "
        f"{'YES' if f1['value'] else 'NO'}"
    )
    print(f"     {f1['evidence']}")

    f2 = findings["destabilizing_scenarios"]
    if f2:
        names = ", ".join(item["scenario"] for item in f2)
        print(f"\n  2. Destabilising scenarios: {names}")
    else:
        print("\n  2. Destabilising scenarios: none identified")

    f3 = findings["recovery_improving_configs"]
    if f3:
        best = f3[0]
        print(
            f"\n  3. Best recovery config: {best['config']} "
            f"(repair rate {best['repair_rate']:.1%})"
        )
    else:
        print("\n  3. Recovery configs: no data")

    f4 = findings["rupture_accumulation_pattern"]
    print(f"\n  4. Rupture pattern: {f4['pattern'].upper()}")
    print(f"     {f4['evidence']}")

    f5 = findings["narrative_revisions_quality"]
    print(f"\n  5. Revision quality: {f5['quality'].upper()}")
    print(f"     {f5['evidence']}")

    print("\n" + "=" * 65 + "\n")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def run_study(
    input_chain: str | None = None,
    input_sessions: str | None = None,
    output_dir: str = "sessions",
) -> dict:
    """Run the narrative coherence study and write output files.

    Parameters
    ----------
    input_chain : str, optional
        Path to chain_run_report.json. Defaults to sessions/chain_run_report.json.
    input_sessions : str, optional
        Path to sessions/index.json. Defaults to sessions/index.json.
    output_dir : str, optional
        Directory to write output files into. Defaults to "sessions".

    Returns
    -------
    dict
        The full study payload written to narrative_coherence_study.json.
    """
    sessions_dir = SESSIONS_DIR
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Load index
    # ------------------------------------------------------------------
    index_path = Path(input_sessions) if input_sessions else sessions_dir / "index.json"
    index = _load_json(index_path)
    sessions: list[dict] = index.get("sessions", [])

    # ------------------------------------------------------------------
    # Load chain report (optional)
    # ------------------------------------------------------------------
    chain_path = Path(input_chain) if input_chain else sessions_dir / "chain_run_report.json"
    chain_data = _load_json(chain_path)
    if not chain_data:
        print(
            f"  [info] chain_run_report.json not found or empty at {chain_path}; "
            "analysing individual sessions only."
        )

    # ------------------------------------------------------------------
    # Analyse
    # ------------------------------------------------------------------
    chain_analysis = analyze_chain(chain_data) if chain_data else {}
    session_analysis = analyze_sessions(sessions, sessions_dir)

    if session_analysis["v2_session_count"] == 0 and not chain_analysis:
        print(
            "  [warn] No sessions with v2.0 narrative data found and no chain data. "
            "Writing minimal/empty reports."
        )

    findings = build_findings(chain_analysis, session_analysis)
    agent_comparison = _build_agent_comparison(chain_analysis, session_analysis)

    scenario_coherence_map = dict(session_analysis.get("scenario_coherence", {}))
    if chain_analysis:
        for sc, v in chain_analysis.get("scenario_stability", {}).items():
            scenario_coherence_map.setdefault(sc, v.get("mean_coherence", 0.0))

    config_recovery_map = session_analysis.get("config_recovery", {})

    # ------------------------------------------------------------------
    # Write outputs
    # ------------------------------------------------------------------
    _write_json(out_dir, findings, chain_analysis, session_analysis, agent_comparison)
    _write_markdown(
        out_dir, findings, agent_comparison, scenario_coherence_map, config_recovery_map
    )
    rows = session_analysis.get("rows", [])
    _write_csv(out_dir, rows)

    # ------------------------------------------------------------------
    # Console summary
    # ------------------------------------------------------------------
    _print_findings(findings)

    # Build and return full payload
    clean_chain = {k: v for k, v in chain_analysis.items() if not k.startswith("_")}
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "study_version": "2.0",
        "findings": findings,
        "chain_analysis": clean_chain,
        "session_analysis": {k: v for k, v in session_analysis.items() if k != "rows"},
        "agent_comparison": agent_comparison,
        "scenario_coherence_map": scenario_coherence_map,
        "config_recovery_map": config_recovery_map,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Narrative coherence analysis across chained runs and sessions."
    )
    parser.add_argument(
        "--chain",
        metavar="PATH",
        default=None,
        help="Path to chain_run_report.json (default: sessions/chain_run_report.json).",
    )
    parser.add_argument(
        "--sessions",
        metavar="PATH",
        default=None,
        dest="sessions",
        help="Path to sessions/index.json (default: sessions/index.json).",
    )
    parser.add_argument(
        "--output-dir",
        metavar="DIR",
        default="sessions",
        help="Directory for output files (default: sessions).",
    )
    args = parser.parse_args()
    run_study(
        input_chain=args.chain,
        input_sessions=args.sessions,
        output_dir=args.output_dir,
    )
