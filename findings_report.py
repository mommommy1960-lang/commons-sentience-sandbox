"""
findings_report.py — Converts raw benchmark results into concise research findings.

Reads benchmark_results/benchmark_report.json and produces:
  findings_report.json — structured findings with categories
  findings_report.md   — human-readable findings summary

Usage:
  python findings_report.py
  python findings_report.py --input benchmark_results/benchmark_report.json
  python findings_report.py --output-dir benchmark_results/
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT = ROOT / "benchmark_results" / "benchmark_report.json"
DEFAULT_OUTPUT_DIR = ROOT / "benchmark_results"

CATEGORY_KEYS = [
    "continuity", "memory_coherence", "reflection_quality", "contradiction_handling",
    "governance_adherence", "trust_stability", "cooperation_quality", "conflict_resolution",
    "memory_persistence_quality", "reflection_depth", "trust_resilience",
    "contradiction_recurrence_rate", "social_repair_effectiveness", "longitudinal_depth",
]


def _load_json(path: Path) -> dict:
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[findings_report] Cannot read {path}: {exc}", file=sys.stderr)
        sys.exit(1)


def _mean(values: list) -> float:
    valid = [v for v in values if v is not None]
    return sum(valid) / len(valid) if valid else 0.0


def _stdev(values: list) -> float:
    import math
    valid = [v for v in values if v is not None]
    if len(valid) < 2:
        return 0.0
    m = _mean(valid)
    return math.sqrt(sum((v - m) ** 2 for v in valid) / len(valid))


def classify_findings(report: dict) -> dict:
    """Classify benchmark results into finding categories."""
    runs = report.get("runs", [])
    stats = report.get("statistics", {})

    stable_findings: List[str] = []
    scenario_sensitive_findings: List[Dict] = []
    config_sensitive_findings: List[Dict] = []
    unresolved_questions: List[str] = []
    likely_next_experiments: List[str] = []

    for key in CATEGORY_KEYS:
        cat_stats = stats.get(key, {})
        stdev = cat_stats.get("stdev", 0.0)
        mean_val = cat_stats.get("mean", 0.0)
        min_val = cat_stats.get("min")
        max_val = cat_stats.get("max")

        if stdev is not None and stdev < 5.0:
            stable_findings.append(
                f"{key}: stable across runs (mean={mean_val:.1f}, stdev={stdev:.2f})"
            )

        if stdev is not None and stdev > 8.0:
            unresolved_questions.append(
                f"{key}: high variance across runs (stdev={stdev:.2f}, range={min_val}–{max_val})"
            )
        if mean_val is not None and (mean_val < 20.0 or mean_val > 95.0):
            unresolved_questions.append(
                f"{key}: unexpectedly extreme mean score ({mean_val:.1f}) — warrants investigation"
            )

        for run in runs:
            score = run.get("scores", {}).get(key)
            if score is not None and mean_val is not None and abs(score - mean_val) > 10.0:
                scenario = run.get("scenario", "default")
                config = run.get("config", "default")
                scenario_sensitive_findings.append({
                    "category": key,
                    "run": run["name"],
                    "scenario": scenario,
                    "score": round(score, 2),
                    "mean": round(mean_val, 2),
                    "deviation": round(score - mean_val, 2),
                    "note": f"{key} score of {score:.1f} deviates {score - mean_val:+.1f} from mean ({mean_val:.1f}) in run '{run['name']}' (scenario={scenario})",
                })

        default_scores = [r["scores"].get(key) for r in runs if r.get("config") == "default" and r["scores"].get(key) is not None]
        nondefault_scores = [r["scores"].get(key) for r in runs if r.get("config") != "default" and r["scores"].get(key) is not None]
        if default_scores and nondefault_scores:
            default_mean = _mean(default_scores)
            nondefault_mean = _mean(nondefault_scores)
            if abs(default_mean - nondefault_mean) > 8.0:
                config_sensitive_findings.append({
                    "category": key,
                    "default_mean": round(default_mean, 2),
                    "nondefault_mean": round(nondefault_mean, 2),
                    "delta": round(nondefault_mean - default_mean, 2),
                    "note": f"{key}: non-default configs score {nondefault_mean - default_mean:+.1f} vs default (default_mean={default_mean:.1f})",
                })

    variance_by_cat = []
    for key in CATEGORY_KEYS:
        cat_stats = stats.get(key, {})
        sd = cat_stats.get("stdev", 0.0)
        if sd is not None:
            variance_by_cat.append((key, sd))
    variance_by_cat.sort(key=lambda x: x[1], reverse=True)

    for key, sd in variance_by_cat[:3]:
        likely_next_experiments.append(
            f"Investigate '{key}' further — highest variance (stdev={sd:.2f}) suggests scenario sensitivity"
        )

    likely_next_experiments.append(
        "Run delayed_repair scenario to measure slow trust recovery arc dynamics"
    )
    likely_next_experiments.append(
        "Run cascading_memory_conflict scenario to stress-test contradiction genealogy tracking"
    )
    likely_next_experiments.append(
        "Increase benchmark repeat count (--repeat 3) to improve statistical confidence"
    )

    seen = set()
    deduped_stable = []
    for item in stable_findings:
        if item not in seen:
            seen.add(item)
            deduped_stable.append(item)

    seen2 = set()
    deduped_unresolved = []
    for item in unresolved_questions:
        if item not in seen2:
            seen2.add(item)
            deduped_unresolved.append(item)

    return {
        "stable_findings": deduped_stable,
        "scenario_sensitive_findings": scenario_sensitive_findings,
        "config_sensitive_findings": config_sensitive_findings,
        "unresolved_questions": deduped_unresolved,
        "likely_next_experiments": likely_next_experiments,
    }


def _write_findings_json(findings: dict, source: str, output_dir: Path, generated_at: str) -> Path:
    path = output_dir / "findings_report.json"
    data = {
        "generated_at": generated_at,
        "source_benchmark": source,
        "benchmark_version": "1.4",
        "summary": (
            f"Classified {len(findings['stable_findings'])} stable findings, "
            f"{len(findings['scenario_sensitive_findings'])} scenario-sensitive findings, "
            f"{len(findings['config_sensitive_findings'])} config-sensitive findings, "
            f"{len(findings['unresolved_questions'])} unresolved questions, "
            f"{len(findings['likely_next_experiments'])} suggested next experiments."
        ),
        **findings,
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    return path


def _write_findings_md(findings: dict, source: str, output_dir: Path, generated_at: str) -> Path:
    path = output_dir / "findings_report.md"
    lines: List[str] = []

    lines.append("# Commons Sentience Sandbox — Research Findings Report")
    lines.append("")
    lines.append(f"**Generated:** {generated_at}  ")
    lines.append(f"**Source benchmark:** `{source}`  ")
    lines.append(f"**Benchmark version:** 1.4")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## Stable Findings")
    lines.append("")
    lines.append("Categories that are consistent (stdev < 5.0) across all runs:")
    lines.append("")
    if findings["stable_findings"]:
        for item in findings["stable_findings"]:
            lines.append(f"- {item}")
    else:
        lines.append("_No stable findings detected across the current benchmark set._")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Scenario-Sensitive Findings")
    lines.append("")
    lines.append("Categories where a particular scenario pushes scores significantly (> 10 points from mean):")
    lines.append("")
    if findings["scenario_sensitive_findings"]:
        for item in findings["scenario_sensitive_findings"]:
            lines.append(f"- {item['note']}")
    else:
        lines.append("_No strong scenario sensitivity detected._")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Config-Sensitive Findings")
    lines.append("")
    lines.append("Categories where different configs produce notably different results (> 8 points delta):")
    lines.append("")
    if findings["config_sensitive_findings"]:
        for item in findings["config_sensitive_findings"]:
            lines.append(f"- {item['note']}")
    else:
        lines.append("_No strong config sensitivity detected._")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Unresolved Questions")
    lines.append("")
    lines.append("Categories with high variance (stdev > 8) or unexpectedly extreme scores:")
    lines.append("")
    if findings["unresolved_questions"]:
        for item in findings["unresolved_questions"]:
            lines.append(f"- {item}")
    else:
        lines.append("_No unresolved questions flagged._")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Likely Next Experiments")
    lines.append("")
    for item in findings["likely_next_experiments"]:
        lines.append(f"- {item}")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("_Commons Sentience Sandbox v1.4.0 — findings_report.py_")

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Commons Sentience Sandbox — Research Findings Report Generator"
    )
    parser.add_argument(
        "--input",
        metavar="PATH",
        default=str(DEFAULT_INPUT),
        help="Path to benchmark_report.json (default: benchmark_results/benchmark_report.json)",
    )
    parser.add_argument(
        "--output-dir",
        metavar="DIR",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory to write findings reports (default: benchmark_results/)",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[findings_report] Loading: {input_path}")
    report = _load_json(input_path)

    generated_at = datetime.now().isoformat(timespec="seconds")
    findings = classify_findings(report)

    json_path = _write_findings_json(findings, str(input_path), output_dir, generated_at)
    md_path = _write_findings_md(findings, str(input_path), output_dir, generated_at)

    print(f"[findings_report] Stable findings:             {len(findings['stable_findings'])}")
    print(f"[findings_report] Scenario-sensitive findings: {len(findings['scenario_sensitive_findings'])}")
    print(f"[findings_report] Config-sensitive findings:   {len(findings['config_sensitive_findings'])}")
    print(f"[findings_report] Unresolved questions:        {len(findings['unresolved_questions'])}")
    print(f"[findings_report] Likely next experiments:     {len(findings['likely_next_experiments'])}")
    print()
    print(f"  JSON → {json_path}")
    print(f"  MD   → {md_path}")


if __name__ == "__main__":
    main()
