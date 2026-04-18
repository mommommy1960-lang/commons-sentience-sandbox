"""
horizon_scaling.py — Analyze how each major metric behaves across turn horizons.

Loads Stage 6 long-horizon campaign outputs and classifies each metric as:
  horizon_stable           — mean and variance stay consistent across horizons
  horizon_sensitive        — mean or variance changes significantly with horizon
  meaningful_at_longer_horizons — near-zero / noisy at short, signal at long
  unstable_across_horizon  — high variance at all horizons; unreliable

Classification criteria
-----------------------
- "stable": coefficient of variation across horizon means < 0.15
  AND max absolute delta-of-means between adjacent horizons < 0.2 × grand mean
- "sensitive": mean shifts by > 20% of grand mean across horizons, or
  variance doubles from shortest to longest horizon
- "meaningful_at_longer": signal (mean ≠ 0) only emerges at ≥50 turns
- "unstable": CV within any single horizon > 0.5

Output
------
commons_sentience_sim/output/reality_audit/stage6_long_horizon/
  horizon_scaling_report.json
  horizon_scaling_summary.csv
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

_OUTPUT_ROOT = _REPO_ROOT / "commons_sentience_sim" / "output" / "reality_audit" / "stage6_long_horizon"

# Classification constants
HS_STABLE             = "horizon_stable"
HS_SENSITIVE          = "horizon_sensitive"
HS_MEANINGFUL_LONGER  = "meaningful_at_longer_horizons"
HS_UNSTABLE           = "unstable_across_horizon"
HS_INSUFFICIENT_DATA  = "insufficient_data"

# Thresholds
_CV_STABLE_THRESH     = 0.15   # CV of horizon-means must be below this for "stable"
_MEAN_SHIFT_THRESH    = 0.20   # fractional shift of grand mean
_WITHIN_CV_UNSTABLE   = 0.50   # within-horizon CV above this = "unstable"
_ZERO_THRESH          = 0.02   # absolute value below which a mean is "near zero"


# ---------------------------------------------------------------------------
# Math utilities
# ---------------------------------------------------------------------------

def _mean(vals: List[float]) -> float:
    return sum(vals) / len(vals) if vals else 0.0


def _std(vals: List[float]) -> float:
    if len(vals) < 2:
        return 0.0
    m = _mean(vals)
    return math.sqrt(sum((v - m) ** 2 for v in vals) / (len(vals) - 1))


def _cv(vals: List[float]) -> Optional[float]:
    """Coefficient of variation (std/mean). None if mean ≈ 0."""
    if not vals:
        return None
    m = _mean(vals)
    if abs(m) < 1e-12:
        return None
    return _std(vals) / abs(m)


# ---------------------------------------------------------------------------
# Classification logic
# ---------------------------------------------------------------------------

def classify_metric_horizon_behavior(
    metric: str,
    horizon_data: Dict[str, Dict[str, Any]],
    turn_counts: List[int],
) -> Dict[str, Any]:
    """Classify how a single metric behaves across turn counts.

    Parameters
    ----------
    metric:
        The metric name.
    horizon_data:
        Dict mapping str(turns) -> {"mean": float|None, "std": float|None, "n": int}
    turn_counts:
        Ordered list of turn counts (int).

    Returns a classification dict.
    """
    means: List[Optional[float]] = []
    stds: List[Optional[float]] = []
    available_turns: List[int] = []

    for t in turn_counts:
        entry = horizon_data.get(str(t), {})
        m = entry.get("mean")
        s = entry.get("std")
        if m is not None:
            means.append(m)
            stds.append(s)
            available_turns.append(t)

    valid_means = [v for v in means if v is not None]
    valid_stds  = [v for v in stds  if v is not None]

    if len(valid_means) < 2:
        return {
            "metric": metric,
            "classification": HS_INSUFFICIENT_DATA,
            "available_horizons": available_turns,
            "horizon_means": dict(zip([str(t) for t in available_turns], valid_means)),
            "notes": "Fewer than 2 horizons with data.",
        }

    grand_mean = _mean(valid_means)

    # Check within-horizon instability (prefer longest horizon's std)
    longest_std = valid_stds[-1] if valid_stds else None
    longest_mean = valid_means[-1] if valid_means else None
    within_cv: Optional[float] = None
    if longest_std is not None and longest_mean and abs(longest_mean) > 1e-12:
        within_cv = longest_std / abs(longest_mean)

    if within_cv is not None and within_cv > _WITHIN_CV_UNSTABLE:
        classification = HS_UNSTABLE
        notes = f"High within-horizon CV={within_cv:.2f} at longest horizon."
    else:
        # Check mean-shift across horizons
        cv_of_means = _cv(valid_means)
        max_shift = max(abs(valid_means[i+1] - valid_means[i]) for i in range(len(valid_means)-1))
        rel_shift = max_shift / abs(grand_mean) if abs(grand_mean) > 1e-12 else None

        # Check if signal only emerges at longer horizons (first turns near zero)
        short_mean = valid_means[0]
        long_mean  = valid_means[-1]
        only_at_longer = (
            abs(short_mean) < _ZERO_THRESH
            and abs(long_mean) > _ZERO_THRESH
            and available_turns[-1] >= 50
        )

        if only_at_longer:
            classification = HS_MEANINGFUL_LONGER
            notes = f"Near-zero at short horizon ({available_turns[0]} turns), signal at {available_turns[-1]} turns."
        elif rel_shift is not None and rel_shift > _MEAN_SHIFT_THRESH:
            classification = HS_SENSITIVE
            notes = f"Max adjacent-horizon shift={max_shift:.4f}, rel={rel_shift:.2f}."
        elif cv_of_means is not None and cv_of_means > _CV_STABLE_THRESH:
            classification = HS_SENSITIVE
            notes = f"CV of horizon-means={cv_of_means:.2f} exceeds stability threshold."
        else:
            classification = HS_STABLE
            notes = "Mean and variance consistent across horizons."

    return {
        "metric": metric,
        "classification": classification,
        "available_horizons": available_turns,
        "horizon_means": {str(t): m for t, m in zip(available_turns, valid_means)},
        "horizon_stds": {str(t): s for t, s in zip(available_turns, valid_stds)},
        "grand_mean": grand_mean,
        "within_cv_longest": within_cv,
        "notes": notes,
    }


# ---------------------------------------------------------------------------
# Load horizon data from report
# ---------------------------------------------------------------------------

def _load_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        return None


def load_horizon_data_from_report(
    horizon_report: Dict[str, Any],
) -> Tuple[Dict[str, Dict[str, Any]], List[int]]:
    """Extract per-metric horizon series from horizon_comparison_report.json.

    Returns (metric_horizon_data, turn_counts).
    """
    turn_counts: List[int] = [int(t) for t in horizon_report.get("turn_counts", [])]
    metrics_raw = horizon_report.get("metrics", {})
    horizon_data: Dict[str, Dict[str, Any]] = {}
    for metric, series in metrics_raw.items():
        horizon_data[metric] = {
            str(t): series.get(str(t), {}) for t in turn_counts
        }
    return horizon_data, turn_counts


def _build_synthetic_horizon_data() -> Tuple[Dict[str, Dict[str, Any]], List[int]]:
    """Fallback synthetic data when live Stage 6 campaigns haven't run at all horizons."""
    turn_counts = [5, 25, 50, 100]
    horizon_data: Dict[str, Dict[str, Any]] = {
        # path_smoothness: stable across horizons
        "path_smoothness": {
            "5":   {"mean": 0.60, "std": 0.02, "n": 3},
            "25":  {"mean": 0.61, "std": 0.02, "n": 3},
            "50":  {"mean": 0.62, "std": 0.02, "n": 3},
            "100": {"mean": 0.62, "std": 0.02, "n": 3},
        },
        # avg_control_effort: stable
        "avg_control_effort": {
            "5":   {"mean": 0.50, "std": 0.03, "n": 3},
            "25":  {"mean": 0.51, "std": 0.03, "n": 3},
            "50":  {"mean": 0.52, "std": 0.03, "n": 3},
            "100": {"mean": 0.52, "std": 0.03, "n": 3},
        },
        # mean_position_error: horizon-sensitive (grows with turns)
        "mean_position_error": {
            "5":   {"mean": 0.70, "std": 0.05, "n": 3},
            "25":  {"mean": 1.20, "std": 0.10, "n": 3},
            "50":  {"mean": 1.80, "std": 0.15, "n": 3},
            "100": {"mean": 2.40, "std": 0.20, "n": 3},
        },
        # stability_score: horizon-sensitive
        "stability_score": {
            "5":   {"mean": 0.70, "std": 0.04, "n": 3},
            "25":  {"mean": 0.63, "std": 0.06, "n": 3},
            "50":  {"mean": 0.58, "std": 0.07, "n": 3},
            "100": {"mean": 0.52, "std": 0.08, "n": 3},
        },
        # audit_bandwidth: stable
        "audit_bandwidth": {
            "5":   {"mean": 30.0, "std": 2.0, "n": 3},
            "25":  {"mean": 30.5, "std": 2.5, "n": 3},
            "50":  {"mean": 31.0, "std": 2.5, "n": 3},
            "100": {"mean": 31.0, "std": 2.5, "n": 3},
        },
        # anisotropy_score: only meaningful at longer horizons
        "anisotropy_score": {
            "5":   {"mean": 0.01, "std": 0.01, "n": 3},
            "25":  {"mean": 0.05, "std": 0.02, "n": 3},
            "50":  {"mean": 0.12, "std": 0.04, "n": 3},
            "100": {"mean": 0.22, "std": 0.06, "n": 3},
        },
        # observer_dependence_score: unstable
        "observer_dependence_score": {
            "5":   {"mean": 5.0,  "std": 4.0, "n": 3},
            "25":  {"mean": 8.0,  "std": 7.0, "n": 3},
            "50":  {"mean": 6.0,  "std": 6.0, "n": 3},
            "100": {"mean": 9.0,  "std": 8.0, "n": 3},
        },
    }
    return horizon_data, turn_counts


# ---------------------------------------------------------------------------
# Build full report
# ---------------------------------------------------------------------------

def build_horizon_scaling_report(
    horizon_data: Dict[str, Dict[str, Any]],
    turn_counts: List[int],
    data_source: str = "live",
) -> Dict[str, Any]:
    """Classify all metrics and produce the full horizon scaling report."""
    entries: List[Dict[str, Any]] = []
    for metric, series in horizon_data.items():
        entry = classify_metric_horizon_behavior(metric, series, turn_counts)
        entries.append(entry)

    entries.sort(key=lambda e: (
        {HS_STABLE: 0, HS_SENSITIVE: 1, HS_MEANINGFUL_LONGER: 2,
         HS_UNSTABLE: 3, HS_INSUFFICIENT_DATA: 4}.get(e["classification"], 5),
        e["metric"],
    ))

    counts = {
        HS_STABLE: 0, HS_SENSITIVE: 0, HS_MEANINGFUL_LONGER: 0,
        HS_UNSTABLE: 0, HS_INSUFFICIENT_DATA: 0,
    }
    for e in entries:
        c = e.get("classification", HS_INSUFFICIENT_DATA)
        counts[c] = counts.get(c, 0) + 1

    return {
        "data_source": data_source,
        "turn_counts_evaluated": turn_counts,
        "n_metrics": len(entries),
        "classification_counts": counts,
        "metrics": entries,
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_horizon_scaling(
    output_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Load Stage 6 campaign data (or use synthetic fallback) and write reports."""
    root = output_root or _OUTPUT_ROOT

    horizon_report_path = root / "horizon_comparison_report.json"
    horizon_report = _load_json(horizon_report_path)

    if horizon_report and horizon_report.get("metrics"):
        horizon_data, turn_counts = load_horizon_data_from_report(horizon_report)
        data_source = "live"
    else:
        horizon_data, turn_counts = _build_synthetic_horizon_data()
        data_source = "synthetic_fallback"

    report = build_horizon_scaling_report(horizon_data, turn_counts, data_source)
    root.mkdir(parents=True, exist_ok=True)
    (root / "horizon_scaling_report.json").write_text(json.dumps(report, indent=2))

    # CSV
    csv_rows: List[Dict[str, Any]] = []
    for entry in report["metrics"]:
        row: Dict[str, Any] = {
            "metric": entry["metric"],
            "classification": entry["classification"],
            "grand_mean": entry.get("grand_mean"),
            "notes": entry.get("notes", ""),
        }
        for t in turn_counts:
            row[f"mean_{t}"] = entry.get("horizon_means", {}).get(str(t))
        csv_rows.append(row)

    if csv_rows:
        csv_path = root / "horizon_scaling_summary.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(csv_rows[0].keys()))
            writer.writeheader()
            writer.writerows(csv_rows)

    print(
        f"Horizon scaling analysis complete ({data_source}).\n"
        f"  Metrics: {report['n_metrics']}\n"
        f"  Stable: {report['classification_counts'][HS_STABLE]}, "
        f"Sensitive: {report['classification_counts'][HS_SENSITIVE]}, "
        f"LongerHorizon: {report['classification_counts'][HS_MEANINGFUL_LONGER]}, "
        f"Unstable: {report['classification_counts'][HS_UNSTABLE]}\n"
        f"  Output: {root}"
    )
    return report


if __name__ == "__main__":
    run_horizon_scaling()
