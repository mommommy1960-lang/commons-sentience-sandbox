"""
sandbox_variability.py — Classify reality-audit metrics by stability
in real sandbox (LLM-driven, stochastic) conditions.

Loads sandbox campaign results from sandbox_campaigns_report.json (or a
provided directory of campaign_result.json files) and classifies each
metric as:

  deterministic_stable   — std ≈ 0 across seeds (cv < CV_STABLE_THRESH)
  stochastic_but_usable  — std > 0 but consistent directional ranking
                           (cv < CV_USABLE_THRESH, rank_correlation ≥ RANK_CORR_THRESH)
  too_unstable           — cv ≥ CV_USABLE_THRESH or rank_correlation is undefined

Output
------
sandbox_variability_report.json — one entry per (config, turns, metric)
sandbox_variability_summary.csv — flat table
"""
from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Classification thresholds
CV_STABLE_THRESH: float = 0.01   # coefficient of variation < 1%  → stable
CV_USABLE_THRESH: float = 0.30   # cv < 30% → usable despite noise
RANK_CORR_THRESH: float = 0.50   # Spearman rank corr across seeds ≥ 0.5

# Metrics present in audit_summary.json
SUMMARY_METRICS: List[str] = [
    "mean_position_error",
    "stability_score",
    "avg_control_effort",
    "path_smoothness",
    "observer_dependence_score",
    "audit_bandwidth",
]


def _cv(values: List[float]) -> Optional[float]:
    """Coefficient of variation (std/mean). Returns None if mean≈0."""
    n = len(values)
    if n < 2:
        return None
    mean = sum(values) / n
    if abs(mean) < 1e-12:
        return None
    variance = sum((v - mean) ** 2 for v in values) / n
    return math.sqrt(variance) / abs(mean)


def _spearman_rank(x: List[float], y: List[float]) -> Optional[float]:
    """Spearman rank correlation for two equal-length lists."""
    n = len(x)
    if n < 2 or len(y) != n:
        return None

    def _ranks(seq: List[float]) -> List[float]:
        sorted_idx = sorted(range(n), key=lambda i: seq[i])
        ranks = [0.0] * n
        for rank, idx in enumerate(sorted_idx):
            ranks[idx] = float(rank + 1)
        return ranks

    rx = _ranks(x)
    ry = _ranks(y)
    d2 = sum((a - b) ** 2 for a, b in zip(rx, ry))
    return 1.0 - (6.0 * d2) / (n * (n * n - 1))


def _classify_metric(
    values: List[float],
) -> Tuple[str, Optional[float], Dict[str, float]]:
    """Return (classification, cv, stats)."""
    n = len(values)
    if n == 0:
        return "insufficient_data", None, {}

    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / n if n > 1 else 0.0
    std = math.sqrt(variance)
    cv = _cv(values)

    stats = {
        "mean": round(mean, 6),
        "std": round(std, 6),
        "min": round(min(values), 6),
        "max": round(max(values), 6),
        "cv": round(cv, 6) if cv is not None else None,
        "n_seeds": n,
    }

    if cv is None:
        classification = "deterministic_stable"
    elif cv < CV_STABLE_THRESH:
        classification = "deterministic_stable"
    elif cv < CV_USABLE_THRESH:
        classification = "stochastic_but_usable"
    else:
        classification = "too_unstable"

    return classification, cv, stats


def analyze_config_variability(
    config_name: str,
    turn_count: int,
    per_seed_results: List[Dict[str, Any]],
    metrics: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Analyse variability of a set of same-(config, turns) seed results.

    Parameters
    ----------
    config_name : str
    turn_count : int
    per_seed_results : list of dicts
        Raw campaign result dicts from sandbox_campaigns_report.json.
    metrics : list of str, optional
        Which probe_metrics fields to analyse. Defaults to SUMMARY_METRICS.

    Returns
    -------
    dict with 'config', 'turns', 'metric_classifications'
    """
    metrics = metrics or SUMMARY_METRICS

    # Extract per-metric value lists
    metric_values: Dict[str, List[float]] = {m: [] for m in metrics}

    for result in per_seed_results:
        pm = result.get("probe_metrics", {})
        if pm.get("note"):
            continue  # probe inactive — skip
        for m in metrics:
            v = pm.get(m)
            if isinstance(v, (int, float)) and not math.isnan(v):
                metric_values[m].append(float(v))

    classifications: Dict[str, Any] = {}
    for m, vals in metric_values.items():
        cls, cv, stats = _classify_metric(vals)
        classifications[m] = {
            "classification": cls,
            "stats": stats,
        }

    return {
        "config": config_name,
        "turns": turn_count,
        "n_seeds_analysed": len(per_seed_results),
        "metric_classifications": classifications,
    }


def run_sandbox_variability(
    campaigns_report_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Load sandbox campaigns report and classify all metrics.

    Parameters
    ----------
    campaigns_report_path : Path, optional
        Path to sandbox_campaigns_report.json. Defaults to standard output dir.
    output_dir : Path, optional
        Where to write output files. Defaults to sandbox_campaigns parent.

    Returns
    -------
    dict with full variability classification results.
    """
    _DEFAULT_CAMPAIGNS_ROOT = (
        _REPO_ROOT / "commons_sentience_sim" / "output" / "reality_audit"
        / "sandbox_campaigns"
    )
    report_path = campaigns_report_path or (_DEFAULT_CAMPAIGNS_ROOT / "sandbox_campaigns_report.json")
    out_dir = output_dir or _DEFAULT_CAMPAIGNS_ROOT.parent

    if not report_path.exists():
        raise FileNotFoundError(
            f"Campaigns report not found at {report_path}. "
            "Run sandbox_campaigns.run_all_campaigns() first."
        )

    with open(report_path, encoding="utf-8") as fh:
        campaigns: Dict[str, Any] = json.load(fh)

    all_analyses: List[Dict[str, Any]] = []

    for config_name, turns_data in campaigns.items():
        for turn_count_str, per_seed in turns_data.items():
            turn_count = int(turn_count_str)
            analysis = analyze_config_variability(
                config_name, turn_count, per_seed
            )
            all_analyses.append(analysis)

    # ── Aggregate: across all (config, turns) combos, what is each metric's
    # dominant classification? ─────────────────────────────────────────────
    metric_classification_counts: Dict[str, Dict[str, int]] = {}
    for a in all_analyses:
        for m, info in a["metric_classifications"].items():
            cls = info["classification"]
            metric_classification_counts.setdefault(m, {})
            metric_classification_counts[m].setdefault(cls, 0)
            metric_classification_counts[m][cls] += 1

    metric_summary: Dict[str, str] = {}
    for m, counts in metric_classification_counts.items():
        dominant = max(counts, key=lambda k: counts[k])
        metric_summary[m] = dominant

    result: Dict[str, Any] = {
        "classification_thresholds": {
            "cv_stable": CV_STABLE_THRESH,
            "cv_usable": CV_USABLE_THRESH,
            "rank_corr_usable": RANK_CORR_THRESH,
        },
        "per_config_analyses": all_analyses,
        "metric_dominant_classifications": metric_summary,
    }

    # Write JSON report
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "sandbox_variability_report.json"
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)

    # Write CSV summary
    csv_path = out_dir / "sandbox_variability_summary.csv"
    _write_variability_csv(all_analyses, csv_path)

    print(f"[sandbox_variability] Report written to {json_path}")
    print(f"[sandbox_variability] CSV written to {csv_path}")
    print("\n  Dominant metric classifications:")
    for m, cls in metric_summary.items():
        print(f"    {m:40s}: {cls}")

    return result


def _write_variability_csv(
    analyses: List[Dict[str, Any]],
    path: Path,
) -> None:
    rows = []
    for a in analyses:
        for m, info in a["metric_classifications"].items():
            stats = info.get("stats", {})
            rows.append({
                "config": a["config"],
                "turns": a["turns"],
                "metric": m,
                "classification": info["classification"],
                "mean": stats.get("mean", ""),
                "std": stats.get("std", ""),
                "cv": stats.get("cv", ""),
                "n_seeds": stats.get("n_seeds", ""),
            })

    if not rows:
        return

    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    run_sandbox_variability()
