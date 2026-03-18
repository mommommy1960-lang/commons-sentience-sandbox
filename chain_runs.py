"""chain_runs.py — Run 5 chained carryover sessions of the Commons Sentience Sandbox.

Each run continues automatically from the previous one via the `continue_from`
mechanism, carrying agent state, memories, and relationships forward.
"""

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

from run_sim import run_simulation
from session_manager import get_latest_session_id, list_sessions, save_session
from experiment_config import load_experiment_config, ExperimentConfig, _DEFAULTS

CHAIN_LENGTH = 5
SESSIONS_DIR = Path("sessions")


# ---------------------------------------------------------------------------
# Safe JSON loading helpers
# ---------------------------------------------------------------------------

def _load_json(path: Path) -> dict:
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


# ---------------------------------------------------------------------------
# Per-session metric extraction
# ---------------------------------------------------------------------------

def _collect_run_metrics(session_id: str) -> dict:
    session_dir = SESSIONS_DIR / session_id

    summary = _load_json(session_dir / "session_summary.json")
    eval_report = _load_json(session_dir / "evaluation_report.json")
    multi_state = _load_json(session_dir / "multi_agent_state.json")

    metrics = summary.get("metrics", {})

    # Scores from evaluation report categories
    categories = eval_report.get("categories", {})
    narrative_coherence_v2_score = (
        categories.get("narrative_coherence_v2", {}).get("score", 0.0)
    )
    trust_stability_score = (
        categories.get("trust_stability", {}).get("score", 0.0)
    )

    sentinel_trust_in_queen = metrics.get("sentinel_trust_in_queen", 0.0)
    aster_trust_in_queen = metrics.get("aster_trust_in_queen", 0.0)
    mutual_trust = metrics.get("mutual_trust_sentinel_aster", 0.0)
    contradiction_pressure_sentinel = metrics.get(
        "sentinel_final_contradiction_pressure", 0.0
    )
    cooperation_events = metrics.get("cooperation_events", 0)
    conflict_events = metrics.get("conflict_events", 0)

    # Identity rupture and revision counts — sum across agents
    identity_rupture_count = 0
    narrative_revision_count = 0
    project_threads_generated = 0

    agents_state = multi_state.get("agents", {})
    for agent_data in agents_state.values():
        narrative_identity = agent_data.get("narrative_identity", {})

        rupture_events = narrative_identity.get("continuity_rupture_events", [])
        identity_rupture_count += len(rupture_events)

        revision_history = narrative_identity.get("self_narrative_history", [])
        narrative_revision_count += len(revision_history)

        ptm = agent_data.get("project_thread_manager", {})
        generation_log = ptm.get("project_generation_log", [])
        project_threads_generated += len(generation_log)

    return {
        "session_id": session_id,
        "narrative_coherence_v2_score": narrative_coherence_v2_score,
        "trust_stability_score": trust_stability_score,
        "sentinel_trust_in_queen": sentinel_trust_in_queen,
        "aster_trust_in_queen": aster_trust_in_queen,
        "mutual_trust": mutual_trust,
        "contradiction_pressure_sentinel": contradiction_pressure_sentinel,
        "cooperation_events": cooperation_events,
        "conflict_events": conflict_events,
        "identity_rupture_count": identity_rupture_count,
        "narrative_revision_count": narrative_revision_count,
        "project_threads_generated": project_threads_generated,
    }


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

def _coherence_trend_label(scores: list) -> str:
    if len(scores) < 2:
        return "stable"
    if scores[-1] > scores[0]:
        return "strengthening"
    if scores[-1] < scores[0]:
        return "fragmenting"
    return "stable"


def _write_json_report(report: dict) -> Path:
    out = SESSIONS_DIR / "chain_run_report.json"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    return out


def _write_csv_report(runs: list) -> Path:
    out = SESSIONS_DIR / "chain_run_report.csv"
    if not runs:
        return out
    fieldnames = list(runs[0].keys())
    with open(out, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(runs)
    return out


def _verdict_sentence(trend: str) -> str:
    if trend == "strengthening":
        return "Narrative identity strengthens across the chain."
    if trend == "fragmenting":
        return "Narrative identity fragments under chain pressure."
    return "Narrative identity remains stable."


def _write_markdown_report(report: dict) -> Path:
    out = SESSIONS_DIR / "chain_run_report.md"
    chain_name = report["chain_name"]
    config = report["config"]
    scenario = report["scenario"]
    turns = report["turns_per_run"]
    summary = report["chain_summary"]
    runs = report["runs"]
    generated_at = report["generated_at"]
    trend = summary["coherence_trend"]

    lines = [
        f"# Chain Run Report: {chain_name}",
        "",
        f"**Generated:** {generated_at}  ",
        f"**Config:** {config}  ",
        f"**Scenario:** {scenario}  ",
        f"**Turns per run:** {turns}  ",
        f"**Chain length:** {report['chain_length']} runs",
        "",
        "---",
        "",
        "## Per-Run Metrics",
        "",
        "| Run | Session ID | Coherence | Trust Stability | Cooperation | Conflicts | Ruptures | Revisions |",
        "|-----|-----------|-----------|-----------------|-------------|-----------|----------|-----------|",
    ]

    for i, run in enumerate(runs, 1):
        sid = run["session_id"]
        coherence = f"{run['narrative_coherence_v2_score']:.1f}"
        trust_stab = f"{run['trust_stability_score']:.1f}"
        coop = run["cooperation_events"]
        conf = run["conflict_events"]
        ruptures = run["identity_rupture_count"]
        revisions = run["narrative_revision_count"]
        lines.append(
            f"| {i} | `{sid}` | {coherence} | {trust_stab} | {coop} | {conf} | {ruptures} | {revisions} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Chain Summary",
        "",
        f"- **Mean narrative coherence:** {summary['mean_narrative_coherence']:.2f}",
        f"- **First coherence:** {summary['first_coherence']:.1f}",
        f"- **Final coherence:** {summary['final_coherence']:.1f}",
        f"- **Mean trust stability:** {summary['mean_trust_stability']:.2f}",
        f"- **Total ruptures:** {summary['total_ruptures']}",
        f"- **Total revisions:** {summary['total_revisions']}",
        f"- **Total cooperation events:** {summary['total_cooperation_events']}",
        f"- **Total conflict events:** {summary['total_conflict_events']}",
        f"- **Total project threads:** {summary['total_project_threads']}",
        "",
        "## Coherence Trend Analysis",
        "",
        f"Trend: **{trend.upper()}**",
        "",
        f"> {_verdict_sentence(trend)}",
        "",
        "## Chain Verdict",
        "",
        f"**{_verdict_sentence(trend)}**",
        "",
    ]

    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    return out


# ---------------------------------------------------------------------------
# Summary table printed to stdout
# ---------------------------------------------------------------------------

def _print_summary_table(runs: list, trend: str) -> None:
    header = f"{'Run':<4} {'Session ID':<35} {'Coherence':>10} {'Trust Stab':>11} {'Coop':>5} {'Conf':>5}"
    sep = "-" * len(header)
    print()
    print("=" * len(header))
    print("  CHAIN RUN SUMMARY")
    print("=" * len(header))
    print(header)
    print(sep)
    for i, run in enumerate(runs, 1):
        sid = run["session_id"][:33]
        print(
            f"{i:<4} {sid:<35} {run['narrative_coherence_v2_score']:>10.1f}"
            f" {run['trust_stability_score']:>11.1f}"
            f" {run['cooperation_events']:>5}"
            f" {run['conflict_events']:>5}"
        )
    print(sep)
    print(f"\nCoherence trend: {trend.upper()}")
    print(_verdict_sentence(trend))
    print()


# ---------------------------------------------------------------------------
# Core chain runner
# ---------------------------------------------------------------------------

def run_chain(
    turns: int = None,
    scenario: str = None,
    config_name: str = None,
    chain_name: str = None,
) -> dict:
    """Run CHAIN_LENGTH sessions in sequence, each continuing from the last.

    Parameters
    ----------
    turns : int, optional
        Override total_turns for each session (default: 30).
    scenario : str, optional
        Scenario name or path to pass to each simulation run.
    config_name : str, optional
        Experiment config name or path to load.
    chain_name : str, optional
        Human-readable label for this chain run.

    Returns
    -------
    dict
        The full chain report dictionary.
    """
    label = chain_name or "default"

    # Load or build experiment config
    if config_name:
        exp_cfg = load_experiment_config(config_name)
    else:
        exp_cfg = load_experiment_config(None)

    if turns is not None:
        exp_cfg.total_turns = turns

    session_ids: list[str] = []
    continue_from: str | None = None

    for i in range(CHAIN_LENGTH):
        session_name = f"chain{i + 1}_{label}_chain"
        print(f"[chain_runs] Run {i + 1}/{CHAIN_LENGTH}: {session_name}")

        run_simulation(
            session_name=session_name,
            experiment_config=exp_cfg,
            scenario_override=scenario,
            continue_from=continue_from,
        )

        sid = get_latest_session_id()
        if sid is None:
            print(
                f"[chain_runs] WARNING: could not retrieve session ID after run {i + 1}",
                file=sys.stderr,
            )
            sid = f"unknown_run_{i + 1}"

        session_ids.append(sid)
        continue_from = sid
        print(f"[chain_runs] Saved as: {sid}")

    # Collect per-run metrics
    run_metrics: list[dict] = [_collect_run_metrics(sid) for sid in session_ids]

    coherence_scores = [r["narrative_coherence_v2_score"] for r in run_metrics]
    trend = _coherence_trend_label(coherence_scores)

    mean_coherence = (
        sum(coherence_scores) / len(coherence_scores) if coherence_scores else 0.0
    )
    trust_scores = [r["trust_stability_score"] for r in run_metrics]
    mean_trust = sum(trust_scores) / len(trust_scores) if trust_scores else 0.0

    chain_summary = {
        "mean_narrative_coherence": round(mean_coherence, 4),
        "coherence_trend": trend,
        "final_coherence": coherence_scores[-1] if coherence_scores else 0.0,
        "first_coherence": coherence_scores[0] if coherence_scores else 0.0,
        "mean_trust_stability": round(mean_trust, 4),
        "total_ruptures": sum(r["identity_rupture_count"] for r in run_metrics),
        "total_revisions": sum(r["narrative_revision_count"] for r in run_metrics),
        "total_cooperation_events": sum(r["cooperation_events"] for r in run_metrics),
        "total_conflict_events": sum(r["conflict_events"] for r in run_metrics),
        "total_project_threads": sum(r["project_threads_generated"] for r in run_metrics),
        "continuity_verdict": trend,
    }

    report = {
        "chain_name": label,
        "generated_at": datetime.now().isoformat(),
        "chain_length": CHAIN_LENGTH,
        "config": config_name or "baseline",
        "scenario": scenario or "default",
        "turns_per_run": turns or 30,
        "session_ids": session_ids,
        "runs": run_metrics,
        "chain_summary": chain_summary,
    }

    # Write outputs
    json_path = _write_json_report(report)
    csv_path = _write_csv_report(run_metrics)
    md_path = _write_markdown_report(report)

    print(f"\n[chain_runs] Reports written:")
    print(f"  JSON: {json_path}")
    print(f"  CSV:  {csv_path}")
    print(f"  MD:   {md_path}")

    _print_summary_table(run_metrics, trend)

    return report


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run 5 chained carryover sessions of the Commons Sentience Sandbox."
    )
    parser.add_argument(
        "--turns",
        type=int,
        default=None,
        help="Number of turns per session (default: 30).",
    )
    parser.add_argument(
        "--scenario",
        type=str,
        default=None,
        help="Scenario name or path to use for all runs.",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Experiment config name or path (e.g. 'baseline', 'high_trust').",
    )
    parser.add_argument(
        "--name",
        type=str,
        default=None,
        help="Optional label for this chain run (used in session names and reports).",
    )
    args = parser.parse_args()
    run_chain(
        turns=args.turns,
        scenario=args.scenario,
        config_name=args.config,
        chain_name=args.name,
    )
