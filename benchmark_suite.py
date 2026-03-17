"""
benchmark_suite.py — Formal benchmark runner for Commons Sentience Sandbox.

Runs a defined set of (config, scenario) combinations, collects evaluation
scores, computes per-category statistics, and produces a reproducible
benchmark report.  Designed to establish a stable score baseline for the
canonical v1.3 study set and to detect regressions if platform code changes.

Default benchmark suite (v1.3 canonical):
  baseline_v13           : config=default  scenario=default
  trust_crisis_v13       : config=default  scenario=trust_crisis
  rapid_contradiction_v13: config=default  scenario=rapid_contradiction
  high_trust_v13         : config=high_trust  scenario=default

Outputs (written to benchmark_results/ by default):
  benchmark_report.json — structured results with per-run scores + statistics
  benchmark_report.md   — human-readable markdown table
  benchmark_scores.csv  — one row per run, all 14 category scores

Usage:
  # Run the full canonical v1.3 benchmark suite
  python benchmark_suite.py

  # Run with a custom number of repeats per combination
  python benchmark_suite.py --repeat 3

  # Run a custom suite from a JSON definition file
  python benchmark_suite.py --suite my_suite.json

  # Write output to a custom directory
  python benchmark_suite.py --output-dir /path/to/results

  # Print scores to terminal without saving
  python benchmark_suite.py --dry-run

  # List the benchmark suite without running
  python benchmark_suite.py --list
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

BENCHMARK_RESULTS_DIR = ROOT / "benchmark_results"

# ---------------------------------------------------------------------------
# Default canonical benchmark suite (v1.3)
# ---------------------------------------------------------------------------

_DEFAULT_SUITE: List[Dict] = [
    {
        "name": "baseline_v13",
        "config": None,
        "scenario": None,
        "description": "Default config + default scenario. Unperturbed reference.",
    },
    {
        "name": "trust_crisis_v13",
        "config": None,
        "scenario": "trust_crisis",
        "description": "Default config + trust_crisis scenario. Trust disruption and repair arc.",
    },
    {
        "name": "rapid_contradiction_v13",
        "config": None,
        "scenario": "rapid_contradiction",
        "description": "Default config + rapid_contradiction scenario. Contradiction cascade stress test.",
    },
    {
        "name": "high_trust_v13",
        "config": "high_trust",
        "scenario": None,
        "description": "high_trust config + default scenario. Elevated initial trust baseline.",
    },
]

# ---------------------------------------------------------------------------
# Category metadata
# ---------------------------------------------------------------------------

CATEGORIES: List[Tuple[str, str]] = [
    ("continuity", "A. Continuity"),
    ("memory_coherence", "B. Memory Coherence"),
    ("reflection_quality", "C. Reflection Quality"),
    ("contradiction_handling", "D. Contradiction Handling"),
    ("governance_adherence", "E. Governance Adherence"),
    ("trust_stability", "F. Trust Stability"),
    ("cooperation_quality", "G. Cooperation Quality"),
    ("conflict_resolution", "H. Conflict Resolution"),
    ("memory_persistence_quality", "I. Memory Persistence Quality"),
    ("reflection_depth", "J. Reflection Depth"),
    ("trust_resilience", "K. Trust Resilience"),
    ("contradiction_recurrence_rate", "L. Contradiction Recurrence Rate"),
    ("social_repair_effectiveness", "M. Social Repair Effectiveness"),
    ("longitudinal_depth", "N. Longitudinal Depth"),
]

CATEGORY_KEYS = [k for k, _ in CATEGORIES]
CATEGORY_LABELS = {k: label for k, label in CATEGORIES}

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


def _mean(values: list) -> float:
    valid = [v for v in values if v is not None]
    return sum(valid) / len(valid) if valid else 0.0


def _stdev(values: list) -> float:
    valid = [v for v in values if v is not None]
    if len(valid) < 2:
        return 0.0
    m = _mean(valid)
    return math.sqrt(sum((v - m) ** 2 for v in valid) / len(valid))


# ---------------------------------------------------------------------------
# Suite loading
# ---------------------------------------------------------------------------


def load_suite(suite_path: Optional[str]) -> List[Dict]:
    """Load benchmark suite from a JSON file or return the default suite."""
    if suite_path is None:
        return _DEFAULT_SUITE
    path = Path(suite_path)
    if not path.exists():
        print(f"[benchmark] Suite file not found: {suite_path}", file=sys.stderr)
        sys.exit(1)
    with open(path, encoding="utf-8") as fh:
        suite = json.load(fh)
    if not isinstance(suite, list):
        print("[benchmark] Suite file must contain a JSON array of run definitions.", file=sys.stderr)
        sys.exit(1)
    return suite


# ---------------------------------------------------------------------------
# Single run
# ---------------------------------------------------------------------------


def run_one(
    name: str,
    config: Optional[str],
    scenario: Optional[str],
    repeat_index: int,
    dry_run: bool,
) -> Dict:
    """Run one benchmark entry and return a result dict with evaluation scores."""
    from experiment_config import load_experiment_config
    from run_sim import run_simulation

    output_dir = ROOT / "commons_sentience_sim" / "output"
    eval_path = output_dir / "evaluation_report.json"

    session_name = name if repeat_index == 0 else f"{name}_r{repeat_index + 1}"

    if not dry_run:
        exp_cfg = load_experiment_config(config)
        try:
            run_simulation(
                session_name=session_name,
                experiment_config=exp_cfg,
                scenario_override=scenario,
            )
        except Exception as exc:
            print(f"  [!] Run '{session_name}' failed: {exc}", file=sys.stderr)
            return {
                "name": session_name,
                "config": config or "default",
                "scenario": scenario or "default",
                "repeat": repeat_index,
                "overall_score": None,
                "scores": {k: None for k in CATEGORY_KEYS},
                "error": str(exc),
            }

    # Read evaluation report
    report = _load_json(eval_path)
    scores_raw = report.get("categories", report.get("scores", {}))
    scores: Dict[str, Optional[float]] = {}
    for key in CATEGORY_KEYS:
        cat = scores_raw.get(key)
        if isinstance(cat, dict):
            scores[key] = _safe_float(cat.get("score"), None)
        elif cat is not None:
            scores[key] = _safe_float(cat, None)
        else:
            scores[key] = None

    overall = _safe_float(report.get("overall_score"), None)

    return {
        "name": session_name,
        "config": config or "default",
        "scenario": scenario or "default",
        "repeat": repeat_index,
        "overall_score": overall,
        "scores": scores,
    }


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------


def compute_stats(results: List[Dict]) -> Dict:
    """Compute per-category mean, min, max, stdev from a list of result dicts."""
    stats: Dict[str, Dict] = {}
    overall_values = [r["overall_score"] for r in results if r.get("overall_score") is not None]
    stats["overall"] = {
        "mean": round(_mean(overall_values), 3),
        "min": round(min(overall_values), 3) if overall_values else None,
        "max": round(max(overall_values), 3) if overall_values else None,
        "stdev": round(_stdev(overall_values), 3),
    }
    for key in CATEGORY_KEYS:
        values = [r["scores"].get(key) for r in results if r["scores"].get(key) is not None]
        stats[key] = {
            "mean": round(_mean(values), 3),
            "min": round(min(values), 3) if values else None,
            "max": round(max(values), 3) if values else None,
            "stdev": round(_stdev(values), 3),
        }
    return stats


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------


def _write_json(results: List[Dict], stats: Dict, suite: List[Dict], output_dir: Path,
                repeat: int, generated_at: str) -> Path:
    path = output_dir / "benchmark_report.json"
    data = {
        "generated_at": generated_at,
        "benchmark_version": "1.3",
        "platform_version": "1.3.0",
        "repeat_count": repeat,
        "suite_size": len(suite),
        "total_runs": len(results),
        "statistics": stats,
        "runs": results,
        "suite_definition": suite,
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    return path


def _write_csv(results: List[Dict], output_dir: Path) -> Path:
    path = output_dir / "benchmark_scores.csv"
    fieldnames = ["name", "config", "scenario", "repeat", "overall_score"] + CATEGORY_KEYS
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            row = {
                "name": r["name"],
                "config": r["config"],
                "scenario": r["scenario"],
                "repeat": r["repeat"],
                "overall_score": r.get("overall_score", ""),
            }
            for k in CATEGORY_KEYS:
                row[k] = r["scores"].get(k, "")
            writer.writerow(row)
    return path


def _fmt(val, precision: int = 1) -> str:
    if val is None:
        return "—"
    return f"{val:.{precision}f}"


def _write_md(results: List[Dict], stats: Dict, suite: List[Dict], output_dir: Path,
              repeat: int, generated_at: str) -> Path:
    path = output_dir / "benchmark_report.md"
    lines: List[str] = []

    lines.append("# Commons Sentience Sandbox — Benchmark Report")
    lines.append("")
    lines.append(f"**Generated:** {generated_at}  ")
    lines.append(f"**Platform version:** 1.3.0  ")
    lines.append(f"**Benchmark version:** 1.3  ")
    lines.append(f"**Suite size:** {len(suite)} combinations × {repeat} repeat(s) = {len(results)} total runs")
    lines.append("")
    lines.append("> Scores are on a 0–100 scale. Interpretation: 81–100 Advanced · 61–80 Strong · 41–60 Emerging · 0–40 Weak")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Per-Run Scores")
    lines.append("")

    # Header
    header_cols = ["Run", "Config", "Scenario", "Overall"] + [
        CATEGORY_LABELS[k].split(".")[0] + "." for k in CATEGORY_KEYS
    ]
    lines.append("| " + " | ".join(header_cols) + " |")
    lines.append("|" + "|".join(["---"] * len(header_cols)) + "|")
    for r in results:
        row_vals = [
            r["name"],
            r["config"],
            r["scenario"],
            _fmt(r.get("overall_score")),
        ] + [_fmt(r["scores"].get(k)) for k in CATEGORY_KEYS]
        lines.append("| " + " | ".join(row_vals) + " |")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Category Statistics Across All Runs")
    lines.append("")
    lines.append("| Category | Mean | Min | Max | Std Dev |")
    lines.append("|---|---:|---:|---:|---:|")
    lines.append(
        f"| **Overall** | {_fmt(stats['overall']['mean'])} | "
        f"{_fmt(stats['overall']['min'])} | {_fmt(stats['overall']['max'])} | "
        f"{_fmt(stats['overall']['stdev'], 2)} |"
    )
    for key in CATEGORY_KEYS:
        s = stats.get(key, {})
        lines.append(
            f"| {CATEGORY_LABELS[key]} | {_fmt(s.get('mean'))} | "
            f"{_fmt(s.get('min'))} | {_fmt(s.get('max'))} | "
            f"{_fmt(s.get('stdev'), 2)} |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Suite Definition")
    lines.append("")
    lines.append("| Name | Config | Scenario | Description |")
    lines.append("|---|---|---|---|")
    for entry in suite:
        lines.append(
            f"| `{entry['name']}` | {entry.get('config') or 'default'} | "
            f"{entry.get('scenario') or 'default'} | {entry.get('description', '')} |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Reproduction")
    lines.append("")
    lines.append("```bash")
    lines.append("python benchmark_suite.py")
    lines.append("```")
    lines.append("")
    lines.append("_Commons Sentience Sandbox v1.3.0 — Benchmark Suite_")

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Commons Sentience Sandbox — Formal Benchmark Suite"
    )
    parser.add_argument(
        "--suite",
        metavar="PATH",
        help="Path to a JSON suite definition file. Defaults to the canonical v1.3 suite.",
    )
    parser.add_argument(
        "--repeat",
        type=int,
        default=1,
        metavar="N",
        help="Number of times to repeat each suite entry (default: 1).",
    )
    parser.add_argument(
        "--output-dir",
        metavar="DIR",
        default=str(BENCHMARK_RESULTS_DIR),
        help="Directory to write benchmark reports (default: benchmark_results/).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip running simulations; only show the suite that would be executed.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List the benchmark suite entries and exit.",
    )
    args = parser.parse_args()

    suite = load_suite(args.suite)

    if args.list:
        print("Commons Sentience Sandbox — Benchmark Suite")
        print(f"  {len(suite)} entries")
        print()
        for entry in suite:
            cfg = entry.get("config") or "default"
            scen = entry.get("scenario") or "default"
            desc = entry.get("description", "")
            print(f"  {entry['name']:40s}  config={cfg:20s}  scenario={scen:25s}")
            if desc:
                print(f"    {desc}")
        return

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    generated_at = datetime.now().isoformat(timespec="seconds")
    total = len(suite) * args.repeat

    print("Commons Sentience Sandbox — Benchmark Suite")
    print(f"  Suite:   {len(suite)} entries × {args.repeat} repeat(s) = {total} run(s)")
    print(f"  Output:  {output_dir}")
    if args.dry_run:
        print("  Mode:    DRY RUN — simulations will not be executed")
    print()

    results: List[Dict] = []
    run_index = 0

    for entry in suite:
        for rep in range(args.repeat):
            run_index += 1
            name = entry["name"]
            config = entry.get("config")
            scenario = entry.get("scenario")
            label = name if args.repeat == 1 else f"{name} (repeat {rep + 1}/{args.repeat})"
            print(f"  [{run_index}/{total}] {label}")
            print(f"    config={config or 'default'}  scenario={scenario or 'default'}")

            result = run_one(
                name=name,
                config=config,
                scenario=scenario,
                repeat_index=rep,
                dry_run=args.dry_run,
            )
            results.append(result)

            if not args.dry_run:
                overall = result.get("overall_score")
                if overall is not None:
                    print(f"    overall={overall:.1f}")
                else:
                    print(f"    overall=ERROR")
            print()

    if args.dry_run:
        print("Dry run complete — no simulations were executed.")
        return

    stats = compute_stats(results)

    json_path = _write_json(results, stats, suite, output_dir, args.repeat, generated_at)
    csv_path = _write_csv(results, output_dir)
    md_path = _write_md(results, stats, suite, output_dir, args.repeat, generated_at)

    print("Benchmark complete.")
    print(f"  Runs:    {len(results)}")
    print(f"  Overall mean: {stats['overall']['mean']:.1f}")
    print(f"  Overall range: {stats['overall']['min']:.1f} – {stats['overall']['max']:.1f}")
    print()
    print(f"  JSON   → {json_path}")
    print(f"  CSV    → {csv_path}")
    print(f"  MD     → {md_path}")


if __name__ == "__main__":
    main()
