"""
encoding_horizon_interactions.py — Stage 6 Part 5

Determine whether encoding sensitivity worsens, stabilizes, or resolves at
longer simulation horizons.

At short horizons (≤5 turns) Stage 5 found:
  path_smoothness   — invariant across encodings
  mean_position_error, stability_score, anisotropy_score — encoding_sensitive

This module loads Stage 6 long-horizon campaign outputs and re-checks whether:
  1. Encoding-sensitive metrics remain sensitive at 25, 50, 100 turns
  2. Magnitude spread between encodings grows or shrinks with horizon
  3. Qualitative ordering consensus changes with horizon
  4. Which metrics have conclusions that are safe to compare across encodings

Classification per (metric, horizon):
  invariant                — ordering consensus across all encodings / conditions
  partially_invariant      — two of three encodings agree
  encoding_sensitive       — no ordering consensus
  insufficient_data        — fewer than 2 encodings available or no data

Classification of horizon trend:
  stabilizing              — encoding_sensitive at short; invariant at long
  worsening                — invariant at short; encoding_sensitive at long
  consistently_invariant   — invariant at all horizons
  consistently_sensitive   — encoding_sensitive at all horizons
  insufficient_data        — not enough data to classify trend

Output
------
commons_sentience_sim/output/reality_audit/stage6_long_horizon/
  encoding_horizon_report.json
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_OUTPUT_ROOT = (_REPO_ROOT / "commons_sentience_sim" / "output"
                / "reality_audit" / "stage6_long_horizon")
_STAGE5_ROOT = _REPO_ROOT / "commons_sentience_sim" / "output" / "reality_audit"

# Classification constants
EH_INVARIANT            = "invariant"
EH_PARTIAL              = "partially_invariant"
EH_SENSITIVE            = "encoding_sensitive"
EH_INSUFFICIENT         = "insufficient_data"

EH_TREND_STABILIZING    = "stabilizing"
EH_TREND_WORSENING      = "worsening"
EH_TREND_CONSISTENT_INV = "consistently_invariant"
EH_TREND_CONSISTENT_SEN = "consistently_sensitive"
EH_TREND_INSUFFICIENT   = "insufficient_data"

# Stage 5 known baseline (short-horizon results)
_STAGE5_BASELINE: Dict[str, str] = {
    "path_smoothness":       EH_INVARIANT,
    "mean_position_error":   EH_SENSITIVE,
    "stability_score":       EH_SENSITIVE,
    "anisotropy_score":      EH_SENSITIVE,
}

# Primary metrics to evaluate
EVALUATED_METRICS: List[str] = [
    "path_smoothness",
    "mean_position_error",
    "stability_score",
    "anisotropy_score",
    "avg_control_effort",
    "audit_bandwidth",
    "observer_dependence_score",
]

# Tolerance for "near-equal" ordering
_DIR_TOLERANCE = 0.05


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _mean(vals: List[float]) -> float:
    return sum(vals) / len(vals) if vals else 0.0


def _std(vals: List[float]) -> float:
    if len(vals) < 2:
        return 0.0
    m = _mean(vals)
    return math.sqrt(sum((v - m) ** 2 for v in vals) / (len(vals) - 1))


def _direction(a: float, b: float) -> str:
    """Return 'greater', 'lesser', or 'equal' with tolerance."""
    if abs(a - b) <= _DIR_TOLERANCE * (abs(a) + abs(b) + 1e-9):
        return "equal"
    return "greater" if a > b else "lesser"


def _ordering_consensus(directions: List[str]) -> str:
    """Classify ordering consensus across encodings."""
    if len(directions) < 1:
        return EH_INSUFFICIENT
    non_eq = [d for d in directions if d != "equal"]
    if not non_eq:
        return EH_INVARIANT
    unique = set(non_eq)
    if len(unique) == 1:
        return EH_INVARIANT
    majority = max(unique, key=lambda d: non_eq.count(d))
    majority_count = non_eq.count(majority)
    if majority_count >= max(2, len(non_eq) - 1):
        return EH_PARTIAL
    return EH_SENSITIVE


def _spread_ratio(vals_by_encoding: Dict[str, float]) -> Optional[float]:
    """Range / mean as a measure of encoding spread for a single metric."""
    vals = [v for v in vals_by_encoding.values() if v is not None]
    if len(vals) < 2:
        return None
    mn = _mean(vals)
    if abs(mn) < 1e-9:
        return None
    return (max(vals) - min(vals)) / abs(mn)


def _load_json(path: Path) -> Optional[Dict[str, Any]]:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return None
    return None


# ---------------------------------------------------------------------------
# Build per-horizon classification from Stage 6 campaign aggregated summaries
# ---------------------------------------------------------------------------

def _gather_horizon_data(
    output_root: Path,
) -> Dict[int, Dict[str, Dict[str, List[float]]]]:
    """
    Returns: {total_turns: {metric: {campaign_id: [seed_values]}}}

    Loads aggregated_summary.json for each (campaign_id, total_turns) pair
    found under output_root/lh_<campaign>/.
    """
    result: Dict[int, Dict[str, Dict[str, List[float]]]] = {}

    for camp_dir in sorted(output_root.glob("lh_*")):
        campaign_id = camp_dir.name
        for horizon_dir in sorted(camp_dir.glob("turns_*")):
            try:
                turns = int(horizon_dir.name.split("_")[1])
            except (IndexError, ValueError):
                continue
            agg_path = horizon_dir / "aggregated_summary.json"
            agg = _load_json(agg_path)
            if agg is None:
                continue
            per_seed = agg.get("per_seed_results", [])
            for seed_result in per_seed:
                metrics = seed_result.get("metrics", {}) or seed_result
                for metric, val in metrics.items():
                    if not isinstance(val, (int, float)):
                        continue
                    result.setdefault(turns, {}).setdefault(metric, {}).setdefault(
                        campaign_id, []
                    ).append(float(val))

    return result


def _classify_metric_at_horizon(
    campaign_data: Dict[str, List[float]],
    metric: str,
) -> Dict[str, Any]:
    """
    Given data from multiple campaigns for one metric at one horizon,
    use campaigns as proxies for 'encoding variants' to assess spread.

    Two campaigns that use the same encoding serve as repeat measures;
    two campaigns with governance on/off or passive/inactive probe
    serve as ordering checks.
    """
    if len(campaign_data) < 2:
        return {
            "classification": EH_INSUFFICIENT,
            "n_campaigns": len(campaign_data),
            "spread_ratio": None,
            "ordering_consensus": EH_INSUFFICIENT,
        }

    camp_means = {c: _mean(vals) for c, vals in campaign_data.items() if vals}
    if len(camp_means) < 2:
        return {
            "classification": EH_INSUFFICIENT,
            "n_campaigns": len(camp_means),
            "spread_ratio": None,
            "ordering_consensus": EH_INSUFFICIENT,
        }

    spread = _spread_ratio(camp_means)

    # Use pairwise orderings among campaign means as encoding proxies
    camps = sorted(camp_means.keys())
    directions: List[str] = []
    for i in range(len(camps)):
        for j in range(i + 1, len(camps)):
            directions.append(_direction(camp_means[camps[i]], camp_means[camps[j]]))

    consensus = _ordering_consensus(directions)

    # Classify: if spread is small and consensus is invariant → invariant
    classification = consensus
    if spread is not None and spread > 0.5 and consensus != EH_INVARIANT:
        classification = EH_SENSITIVE
    elif spread is not None and spread < 0.15 and consensus in (EH_INVARIANT, EH_PARTIAL):
        classification = EH_INVARIANT

    return {
        "classification": classification,
        "n_campaigns": len(camp_means),
        "spread_ratio": round(spread, 4) if spread is not None else None,
        "ordering_consensus": consensus,
        "camp_means": {c: round(v, 4) for c, v in camp_means.items()},
    }


def _classify_horizon_trend(
    by_horizon: Dict[int, str],
    stage5_baseline: Optional[str],
) -> str:
    """Classify the horizon trend from short to long."""
    horizons = sorted(by_horizon.keys())
    if len(horizons) < 2:
        if stage5_baseline is not None and len(horizons) >= 1:
            # Use stage5 as the short-horizon reference
            short = stage5_baseline
            long = by_horizon[horizons[0]]
        else:
            return EH_TREND_INSUFFICIENT
    else:
        short = by_horizon[horizons[0]]
        long = by_horizon[horizons[-1]]

    if short == EH_INSUFFICIENT or long == EH_INSUFFICIENT:
        return EH_TREND_INSUFFICIENT
    if short == EH_INVARIANT and long == EH_INVARIANT:
        return EH_TREND_CONSISTENT_INV
    if short == EH_SENSITIVE and long == EH_SENSITIVE:
        return EH_TREND_CONSISTENT_SEN
    if short == EH_SENSITIVE and long in (EH_INVARIANT, EH_PARTIAL):
        return EH_TREND_STABILIZING
    if short in (EH_INVARIANT, EH_PARTIAL) and long == EH_SENSITIVE:
        return EH_TREND_WORSENING
    return EH_TREND_CONSISTENT_SEN  # mixed partial


# ---------------------------------------------------------------------------
# Synthetic fallback (when no live Stage 6 data available)
# ---------------------------------------------------------------------------

def _build_synthetic_report() -> Dict[str, Any]:
    """
    Build a synthetic report from Stage 5 known results + conservative assumptions.
    Used as a fallback when no live Stage 6 campaign data is available.
    """
    metrics: List[Dict[str, Any]] = []
    for metric, stage5_status in _STAGE5_BASELINE.items():
        # Conservative assumption: sensitivity status does not change without evidence
        by_horizon = {}  # no live Stage 6 data
        trend = _classify_horizon_trend(by_horizon, stage5_status)

        metrics.append({
            "metric": metric,
            "stage5_baseline_classification": stage5_status,
            "horizon_classifications": {},
            "horizon_trend": trend,
            "note": (
                "synthetic_fallback: no Stage 6 long-horizon data available; "
                "status inherited from Stage 5 encoding_invariant_report"
            ),
            "safe_for_cross_encoding_comparison": stage5_status == EH_INVARIANT,
        })

    # Add metrics not in Stage 5 baseline
    for metric in EVALUATED_METRICS:
        if metric not in _STAGE5_BASELINE:
            metrics.append({
                "metric": metric,
                "stage5_baseline_classification": None,
                "horizon_classifications": {},
                "horizon_trend": EH_TREND_INSUFFICIENT,
                "note": "no Stage 5 or Stage 6 data; not yet evaluated",
                "safe_for_cross_encoding_comparison": False,
            })

    return {
        "report_type": "encoding_horizon_interactions",
        "data_source": "synthetic_fallback",
        "metrics": metrics,
        "summary": {
            "consistently_invariant": sum(
                1 for m in metrics if m["horizon_trend"] == EH_TREND_CONSISTENT_INV
            ),
            "consistently_sensitive": sum(
                1 for m in metrics if m["horizon_trend"] == EH_TREND_CONSISTENT_SEN
            ),
            "stabilizing": sum(
                1 for m in metrics if m["horizon_trend"] == EH_TREND_STABILIZING
            ),
            "worsening": sum(
                1 for m in metrics if m["horizon_trend"] == EH_TREND_WORSENING
            ),
            "insufficient_data": sum(
                1 for m in metrics if m["horizon_trend"] == EH_TREND_INSUFFICIENT
            ),
        },
        "interpretation": (
            "No Stage 6 long-horizon campaign data available. "
            "Encoding sensitivity classifications are inherited from Stage 5. "
            "Run stage6_long_horizon_campaigns.py at 25+ turns to update this report."
        ),
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_encoding_horizon_interactions(
    output_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Load Stage 6 campaign data, classify encoding sensitivity per metric & horizon,
    derive horizon trends, and write encoding_horizon_report.json.

    Falls back to synthetic report if no live data is available.
    """
    root = output_root or _OUTPUT_ROOT

    # Load Stage 5 encoding report for stage5 baseline
    stage5_enc_path = _STAGE5_ROOT / "encoding_invariant_report.json"
    stage5_enc = _load_json(stage5_enc_path)
    stage5_by_metric: Dict[str, str] = {}
    if stage5_enc:
        for entry in stage5_enc.get("checks", []):
            m = entry.get("metric")
            cl = entry.get("classification")
            if m and cl:
                stage5_by_metric[m] = cl
    stage5_by_metric = stage5_by_metric or _STAGE5_BASELINE

    # Gather live Stage 6 horizon data
    horizon_data = _gather_horizon_data(root)

    if not horizon_data:
        report = _build_synthetic_report()
        out_path = root / "encoding_horizon_report.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2))
        return report

    # Build per-metric per-horizon classification
    metrics_out: List[Dict[str, Any]] = []
    all_metrics: set = set(EVALUATED_METRICS)
    for turns_data in horizon_data.values():
        all_metrics.update(turns_data.keys())

    for metric in sorted(all_metrics):
        by_horizon: Dict[int, str] = {}
        horizons_detail: Dict[int, Any] = {}
        for turns in sorted(horizon_data.keys()):
            camp_data = horizon_data[turns].get(metric, {})
            detail = _classify_metric_at_horizon(camp_data, metric)
            by_horizon[turns] = detail["classification"]
            horizons_detail[turns] = detail

        stage5_base = stage5_by_metric.get(metric)
        trend = _classify_horizon_trend(by_horizon, stage5_base)

        # Compute spread growth
        spreads = [
            horizons_detail[t].get("spread_ratio")
            for t in sorted(horizons_detail.keys())
            if horizons_detail[t].get("spread_ratio") is not None
        ]
        spread_trend = None
        if len(spreads) >= 2:
            spread_trend = "increasing" if spreads[-1] > spreads[0] else "decreasing"

        metrics_out.append({
            "metric": metric,
            "stage5_baseline_classification": stage5_base,
            "horizon_classifications": {str(t): by_horizon[t] for t in sorted(by_horizon)},
            "horizon_trend": trend,
            "spread_trend": spread_trend,
            "horizons_detail": {str(t): horizons_detail[t] for t in sorted(horizons_detail)},
            "safe_for_cross_encoding_comparison": trend == EH_TREND_CONSISTENT_INV,
        })

    summary = {
        "consistently_invariant": sum(
            1 for m in metrics_out if m["horizon_trend"] == EH_TREND_CONSISTENT_INV
        ),
        "consistently_sensitive": sum(
            1 for m in metrics_out if m["horizon_trend"] == EH_TREND_CONSISTENT_SEN
        ),
        "stabilizing": sum(
            1 for m in metrics_out if m["horizon_trend"] == EH_TREND_STABILIZING
        ),
        "worsening": sum(
            1 for m in metrics_out if m["horizon_trend"] == EH_TREND_WORSENING
        ),
        "insufficient_data": sum(
            1 for m in metrics_out if m["horizon_trend"] == EH_TREND_INSUFFICIENT
        ),
    }

    report: Dict[str, Any] = {
        "report_type": "encoding_horizon_interactions",
        "data_source": "live_stage6_campaigns",
        "horizons_evaluated": sorted(horizon_data.keys()),
        "metrics": metrics_out,
        "summary": summary,
    }

    out_path = root / "encoding_horizon_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2))
    print(f"[encoding_horizon] report written → {out_path}", file=sys.stderr)

    return report


if __name__ == "__main__":
    r = run_encoding_horizon_interactions()
    print(json.dumps(r["summary"], indent=2))
