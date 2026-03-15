"""
run_experiments.py — Batch experiment runner for Commons Sentience Sandbox.

Runs multiple named experiment configs in sequence, creates a session for each,
and produces aggregate reports:
  - experiments/results/experiment_report.json
  - experiments/results/experiment_report.md
  - experiments/results/experiment_scores.csv

Usage
-----
  # Run all 5 built-in experiment configs
  python run_experiments.py

  # Run selected configs
  python run_experiments.py --configs baseline high_trust strict_governance

  # Run all configs 3 times each
  python run_experiments.py --repeat 3

  # Run selected configs 2 times each
  python run_experiments.py --configs baseline high_trust --repeat 2
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from experiment_config import (
    list_available_configs,
    load_experiment_config,
    _PRESET_ALIASES,
)
from run_sim import run_simulation

RESULTS_DIR = ROOT / "experiments" / "results"

# All built-in preset names in canonical order
DEFAULT_CONFIGS = list(_PRESET_ALIASES.keys())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_json(path: Path) -> dict:
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}


def _run_one(
    config_name: str, repeat_index: int, total_repeats: int
) -> Optional[dict]:
    """
    Run the simulation once with a named config and return a result dict.

    Returns None if the run failed.
    """
    cfg = load_experiment_config(config_name)
    suffix = (
        f"{config_name}_{repeat_index+1}"
        if total_repeats > 1
        else config_name
    )
    session_name = f"exp_{suffix}"

    print(f"\n{'='*65}")
    print(f"  Experiment run: {config_name}  ({repeat_index+1}/{total_repeats})")
    print(f"  Session name  : {session_name}")
    print(f"{'='*65}")

    try:
        sentinel, aster = run_simulation(
            session_name=session_name,
            experiment_config=cfg,
        )
    except Exception as exc:
        print(f"  ERROR: {exc}")
        return None

    # Locate the session that was just saved
    from session_manager import list_sessions, get_session_dir
    sessions = list_sessions()
    latest = sessions[0] if sessions else None
    if not latest:
        return None

    sid = latest["session_id"]
    sdir = get_session_dir(sid)
    eval_report = _load_json(sdir / "evaluation_report.json") if sdir else {}

    return {
        "session_id": sid,
        "config_name": config_name,
        "repeat": repeat_index + 1,
        "session_name": session_name,
        "simulation_version": latest.get("simulation_version", "unknown"),
        "total_turns": latest.get("total_turns", 0),
        "overall_score": eval_report.get("overall_score", 0),
        "overall_interpretation": eval_report.get("overall_interpretation", ""),
        "category_scores": {
            k: v.get("score", 0)
            for k, v in eval_report.get("categories", {}).items()
        },
        "experiment_meta": cfg.to_metadata_dict(),
    }


# ---------------------------------------------------------------------------
# Report writers
# ---------------------------------------------------------------------------

def _write_json_report(results: list[dict], output_dir: Path) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    # Best overall
    best = max(results, key=lambda r: r["overall_score"]) if results else {}
    # Per-category best
    cat_best: dict = {}
    if results:
        all_cats = list(results[0].get("category_scores", {}).keys())
        for cat in all_cats:
            best_run = max(results, key=lambda r: r["category_scores"].get(cat, 0))
            cat_best[cat] = {
                "session_id": best_run["session_id"],
                "config": best_run["config_name"],
                "score": best_run["category_scores"].get(cat, 0),
            }

    report = {
        "generated_at": datetime.now().isoformat(),
        "total_runs": len(results),
        "configs_run": sorted({r["config_name"] for r in results}),
        "best_overall": {
            "session_id": best.get("session_id", ""),
            "config": best.get("config_name", ""),
            "score": best.get("overall_score", 0),
        } if best else {},
        "per_category_best": cat_best,
        "runs": results,
    }

    path = output_dir / "experiment_report.json"
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    return path


def _write_md_report(results: list[dict], output_dir: Path) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    cats = list(results[0]["category_scores"].keys()) if results else []
    best = max(results, key=lambda r: r["overall_score"]) if results else {}

    # Per-category best
    cat_best: dict = {}
    for cat in cats:
        b = max(results, key=lambda r: r["category_scores"].get(cat, 0))
        cat_best[cat] = (b["config_name"], b["category_scores"].get(cat, 0))

    lines = [
        "# Experiment Report — Commons Sentience Sandbox",
        "",
        f"Generated: {datetime.now().isoformat()[:19]}",
        f"Total runs: {len(results)}",
        f"Configs run: {', '.join(sorted({r['config_name'] for r in results}))}",
        "",
        "---",
        "",
        "## Overall Scores",
        "",
        "| Session | Config | Repeat | Overall | Rating |",
        "|---|---|---|---|---|",
    ]
    for r in results:
        lines.append(
            f"| `{r['session_id']}` | {r['config_name']} | {r['repeat']} "
            f"| **{r['overall_score']:.1f}** | {r['overall_interpretation'].upper()} |"
        )

    if best:
        lines += [
            "",
            f"**Best overall:** {best.get('config_name', '')} — "
            f"{best.get('overall_score', 0):.1f} / 100 "
            f"(session `{best.get('session_id', '')}`).",
        ]

    lines += ["", "---", "", "## Category Score Table", ""]
    cat_header = "| Session | Config |" + "".join(
        f" {c.replace('_',' ').title()} |" for c in cats
    )
    cat_sep = "|---|---|" + "---|" * len(cats)
    lines += [cat_header, cat_sep]
    for r in results:
        row = (
            f"| `{r['session_id'][-12:]}` | {r['config_name']} |"
            + "".join(
                f" {r['category_scores'].get(c, 0):.1f} |" for c in cats
            )
        )
        lines.append(row)

    if cat_best:
        lines += ["", "---", "", "## Best Config per Category", ""]
        lines += [
            "| Category | Best Config | Score |",
            "|---|---|---|",
        ]
        for cat, (cfg_name, score) in cat_best.items():
            label = cat.replace("_", " ").title()
            lines.append(f"| {label} | {cfg_name} | {score:.1f} |")

    # Config parameter summary
    if results:
        lines += ["", "---", "", "## Config Parameters", ""]
        param_keys = [
            "governance_strictness",
            "cooperation_bias",
            "initial_agent_trust",
        ]
        param_header = "| Config |" + "".join(f" {k.replace('_',' ').title()} |" for k in param_keys)
        param_sep = "|---|" + "---|" * len(param_keys)
        lines += [param_header, param_sep]
        seen_configs: set = set()
        for r in results:
            cfg_name = r["config_name"]
            if cfg_name in seen_configs:
                continue
            seen_configs.add(cfg_name)
            em = r.get("experiment_meta", {})
            row = f"| {cfg_name} |"
            for k in param_keys:
                row += f" {em.get(k, '—')} |"
            lines.append(row)

    path = output_dir / "experiment_report.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _write_csv_scores(results: list[dict], output_dir: Path) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    cats = list(results[0]["category_scores"].keys()) if results else []
    path = output_dir / "experiment_scores.csv"
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            ["session_id", "config_name", "repeat", "overall_score"]
            + cats
            + ["governance_strictness", "cooperation_bias", "initial_agent_trust"]
        )
        for r in results:
            em = r.get("experiment_meta", {})
            writer.writerow(
                [
                    r["session_id"],
                    r["config_name"],
                    r["repeat"],
                    r["overall_score"],
                ]
                + [r["category_scores"].get(c, 0) for c in cats]
                + [
                    em.get("governance_strictness", ""),
                    em.get("cooperation_bias", ""),
                    em.get("initial_agent_trust", ""),
                ]
            )
    return path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_experiments(
    config_names: list[str],
    repeat: int = 1,
) -> list[dict]:
    """
    Run *config_names* experiment configs *repeat* times each.

    Returns a list of result dicts.
    """
    results = []
    total = len(config_names) * repeat
    run_num = 0

    for config_name in config_names:
        for rep in range(repeat):
            run_num += 1
            print(f"\n[{run_num}/{total}] Config: {config_name}  rep {rep+1}/{repeat}")
            result = _run_one(config_name, rep, repeat)
            if result:
                results.append(result)

    return results


def save_reports(results: list[dict]) -> None:
    """Write JSON, markdown, and CSV reports into experiments/results/."""
    if not results:
        print("\n  No results to report.")
        return

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    json_path = _write_json_report(results, RESULTS_DIR)
    md_path = _write_md_report(results, RESULTS_DIR)
    csv_path = _write_csv_scores(results, RESULTS_DIR)

    best = max(results, key=lambda r: r["overall_score"])

    print("\n" + "=" * 65)
    print(f"  EXPERIMENT COMPLETE — {len(results)} run(s)")
    print("=" * 65)
    print(f"  Best overall  : {best['config_name']}  ({best['overall_score']} / 100)")
    print(f"  JSON report   → {json_path}")
    print(f"  Markdown      → {md_path}")
    print(f"  CSV scores    → {csv_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="run_experiments.py",
        description=(
            "Batch experiment runner for Commons Sentience Sandbox. "
            "Runs multiple configs in sequence and produces aggregate reports."
        ),
    )
    parser.add_argument(
        "--configs",
        nargs="+",
        default=None,
        metavar="CONFIG",
        help=(
            "One or more experiment config names or file paths to run. "
            f"Available presets: {', '.join(DEFAULT_CONFIGS)}. "
            "Defaults to all 5 built-in presets."
        ),
    )
    parser.add_argument(
        "--repeat",
        type=int,
        default=1,
        metavar="N",
        help="Number of times to repeat each config. Default: 1.",
    )
    args = parser.parse_args()

    configs_to_run = args.configs if args.configs else DEFAULT_CONFIGS
    results = run_experiments(configs_to_run, repeat=args.repeat)
    save_reports(results)
