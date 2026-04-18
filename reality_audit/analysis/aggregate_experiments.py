"""Multi-run statistical aggregation for Stage 3.

Takes a list of per-run metric dicts (from ExperimentRunner or
long_horizon_runs) and computes summary statistics for each metric:

  - mean
  - standard deviation
  - min / max
  - 95 % confidence interval (mean ± 1.96 * std_error)
  - consistency_score : 1 - (std / (|mean| + epsilon))
      → 1.0 = perfectly consistent, 0.0 = fully noisy

Metrics aggregated
------------------
  position_error, stability_score, anisotropy_score,
  observer_dependence_score, bandwidth_bottleneck_score,
  quantization_artifact_score, control_effort, path_smoothness,
  velocity_error, convergence_time

Outputs
-------
  aggregated_summary.json
  aggregated_summary.csv

Both are written to the directory passed in (or inferred from the
experiment output directory).
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Metric names that we aggregate
# ---------------------------------------------------------------------------

AGGREGATED_METRICS = [
    "position_error",
    "velocity_error",
    "stability_score",
    "anisotropy_score",
    "observer_dependence_score",
    "bandwidth_bottleneck_score",
    "quantization_artifact_score",
    "control_effort",
    "path_smoothness",
    "convergence_time",
]

_EPSILON = 1e-9  # avoid division by zero in consistency_score


# ---------------------------------------------------------------------------
# Core statistics
# ---------------------------------------------------------------------------

def _stats(values: List[float]) -> Dict[str, float]:
    """Return mean, std, min, max, ci_lo, ci_hi, consistency_score."""
    n = len(values)
    if n == 0:
        return {
            "mean": float("nan"),
            "std": float("nan"),
            "min": float("nan"),
            "max": float("nan"),
            "ci_lo": float("nan"),
            "ci_hi": float("nan"),
            "n": 0,
            "consistency_score": float("nan"),
        }
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / n  # population std
    std = math.sqrt(variance)
    std_err = std / math.sqrt(n) if n > 1 else std
    # 95 % CI using z = 1.96
    ci_lo = mean - 1.96 * std_err
    ci_hi = mean + 1.96 * std_err
    # consistency_score: 1 = stable, 0 = fully noisy
    consistency_score = max(0.0, 1.0 - std / (abs(mean) + _EPSILON))
    return {
        "mean": round(mean, 6),
        "std": round(std, 6),
        "min": round(min(values), 6),
        "max": round(max(values), 6),
        "ci_lo": round(ci_lo, 6),
        "ci_hi": round(ci_hi, 6),
        "n": n,
        "consistency_score": round(consistency_score, 4),
    }


# ---------------------------------------------------------------------------
# Per-metric stability flag
# ---------------------------------------------------------------------------

_UNSTABLE_THRESHOLD = 0.5  # consistency_score below this → flagged unstable


def _stability_flag(consistency_score: float) -> str:
    if math.isnan(consistency_score):
        return "unknown"
    if consistency_score >= 0.8:
        return "stable"
    if consistency_score >= _UNSTABLE_THRESHOLD:
        return "moderate"
    return "unstable"


# ---------------------------------------------------------------------------
# Main aggregation function
# ---------------------------------------------------------------------------

def aggregate_runs(
    run_results: List[Dict[str, Any]],
    experiment_name: str = "experiment",
    output_dir: Optional[Path] = None,
    verbose: bool = False,
) -> Dict[str, Any]:
    """Aggregate metric statistics across a list of run-result dicts.

    Parameters
    ----------
    run_results : list of dicts
        Each dict must contain a ``"metrics"`` key with a metric dict,
        as returned by ``ExperimentRunner.run()``.
    experiment_name : str
        Used as the ``experiment_name`` field in the output.
    output_dir : Path, optional
        Where to write ``aggregated_summary.json`` and
        ``aggregated_summary.csv``.  If *None*, files are not written.

    Returns
    -------
    dict
        Aggregated summary with per-metric statistics.
    """
    # Collect values per metric
    per_metric: Dict[str, List[float]] = {m: [] for m in AGGREGATED_METRICS}
    n_runs = 0
    for result in run_results:
        metrics = result.get("metrics", result)  # allow bare metric dicts
        for metric in AGGREGATED_METRICS:
            val = metrics.get(metric)
            if val is not None and not math.isnan(float(val)):
                per_metric[metric].append(float(val))
        n_runs += 1

    # Compute stats
    aggregated: Dict[str, Any] = {}
    for metric, values in per_metric.items():
        stats = _stats(values)
        aggregated[metric] = {
            **stats,
            "stability": _stability_flag(stats["consistency_score"]),
        }

    summary = {
        "experiment_name": experiment_name,
        "n_runs": n_runs,
        "metrics": aggregated,
    }

    if verbose:
        print(f"\n[Aggregation] {experiment_name}  ({n_runs} runs)")
        for metric, s in aggregated.items():
            print(
                f"  {metric:<35s}  mean={s['mean']:.4f}  std={s['std']:.4f}"
                f"  stability={s['stability']}"
            )

    if output_dir is not None:
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        json_path = out_path / "aggregated_summary.json"
        json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        _write_csv(aggregated, experiment_name, n_runs, out_path / "aggregated_summary.csv")
        if verbose:
            print(f"  Wrote: {json_path}")

    return summary


def _write_csv(
    aggregated: Dict[str, Any],
    experiment_name: str,
    n_runs: int,
    csv_path: Path,
) -> None:
    fieldnames = [
        "metric", "mean", "std", "min", "max",
        "ci_lo", "ci_hi", "n", "consistency_score", "stability",
    ]
    rows = []
    for metric, stats in aggregated.items():
        rows.append({"metric": metric, **stats})
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# Cross-run consistency check (Part 5)
# ---------------------------------------------------------------------------

def cross_run_consistency(
    run_results: List[Dict[str, Any]],
    verbose: bool = False,
) -> Dict[str, Any]:
    """Compute per-metric consistency scores and flag unreliable metrics.

    Returns a dict with:
        {metric: {consistency_score, variance, flag: "stable"|"moderate"|"unstable"}}
    """
    per_metric: Dict[str, List[float]] = {m: [] for m in AGGREGATED_METRICS}
    for result in run_results:
        metrics = result.get("metrics", result)
        for metric in AGGREGATED_METRICS:
            val = metrics.get(metric)
            if val is not None and not math.isnan(float(val)):
                per_metric[metric].append(float(val))

    consistency: Dict[str, Any] = {}
    for metric, values in per_metric.items():
        s = _stats(values)
        flag = _stability_flag(s["consistency_score"])
        consistency[metric] = {
            "consistency_score": s["consistency_score"],
            "variance": round(s["std"] ** 2, 8),
            "std": s["std"],
            "n": s["n"],
            "flag": flag,
        }
        if verbose:
            print(f"  {metric:<35s}  cs={s['consistency_score']:.3f}  [{flag}]")

    return consistency


# ---------------------------------------------------------------------------
# Convenience: aggregate from directory of summary.json files
# ---------------------------------------------------------------------------

def aggregate_from_directory(
    directory: Path,
    experiment_name: Optional[str] = None,
    output_dir: Optional[Path] = None,
    verbose: bool = False,
) -> Dict[str, Any]:
    """Load all summary.json files under *directory* and aggregate them.

    Looks for ``*/summary.json`` or ``summary.json`` at the given path.
    """
    directory = Path(directory)
    experiment_name = experiment_name or directory.name

    # Collect run results from per-run summary.json files
    run_results: List[Dict[str, Any]] = []
    # Check for a top-level summary.json with embedded results list
    top_summary = directory / "summary.json"
    if top_summary.exists():
        data = json.loads(top_summary.read_text(encoding="utf-8"))
        if "results" in data:
            run_results.extend(data["results"])
    else:
        # Per-run subdirectories
        for sub in sorted(directory.iterdir()):
            sub_summary = sub / "summary.json"
            if sub_summary.exists():
                data = json.loads(sub_summary.read_text(encoding="utf-8"))
                if "metrics" in data:
                    run_results.append(data)

    if not run_results:
        raise ValueError(f"No run results found under {directory}")

    out = output_dir or directory
    return aggregate_runs(
        run_results,
        experiment_name=experiment_name,
        output_dir=out,
        verbose=verbose,
    )
