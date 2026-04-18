"""
governance_horizon_effects.py — Determine whether governance sensitivity emerges
only after enough simulation turns.

Loads Stage 6 long-horizon campaign outputs for governance ON (lh_A) vs
governance OFF (lh_B) across 25, 50, and 100 turns.  For each horizon length,
computes the governance-induced delta relative to run-to-run variability.

Classification schema
---------------------
G_DOMINATED    governance_dominated    — shift > FP threshold AND > sandbox variability
G_MODULATED    governance_modulated    — shift detectable but within FP margin
G_NEUTRAL      governance_neutral      — no detectable shift
G_INSUFFICIENT data_insufficient       — not enough runs / turns

The key question:
  At which turn count (if any) does governance sensitivity first appear?
  If sensitivty remains absent at 100 turns, state that explicitly.

Output
------
commons_sentience_sim/output/reality_audit/stage6_long_horizon/
  governance_horizon_report.json
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_OUTPUT_ROOT = _REPO_ROOT / "commons_sentience_sim" / "output" / "reality_audit" / "stage6_long_horizon"

# Classification constants
G_DOMINATED   = "governance_dominated"
G_MODULATED   = "governance_modulated"
G_NEUTRAL     = "governance_neutral"
G_INSUFFICIENT = "data_insufficient"

# Effect size threshold for "meaningful" (Cohen's d)
EFFECT_THRESH = 0.40  # more conservative than Stage 5

# Stage 3 false-positive thresholds (copied from governance_interpretation.py)
FP_THRESHOLDS: Dict[str, Optional[float]] = {
    "mean_position_error":       6.0,
    "stability_score":           0.05,
    "avg_control_effort":        0.95,
    "path_smoothness":           None,
    "observer_dependence_score": 15.0,
    "audit_bandwidth":           None,
    "anisotropy_score":          None,
}


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


def _cohens_d(a: List[float], b: List[float]) -> Optional[float]:
    if not a or not b:
        return None
    sa, sb = _std(a), _std(b)
    pooled = math.sqrt((sa ** 2 + sb ** 2) / 2.0)
    if pooled < 1e-12:
        return 0.0
    return (_mean(a) - _mean(b)) / pooled


def _load_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        return None


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

def classify_governance_effect(
    metric: str,
    delta: Optional[float],
    cohens_d_val: Optional[float],
    fp_threshold: Optional[float],
) -> str:
    """Classify the governance effect for a single metric at one horizon."""
    if delta is None or cohens_d_val is None:
        return G_INSUFFICIENT

    abs_d = abs(cohens_d_val)

    if abs_d < EFFECT_THRESH:
        return G_NEUTRAL

    # Effect detected — check FP threshold
    if fp_threshold is not None and abs(delta) < fp_threshold * 0.10:
        # Shift is detectable but well below false-positive territory
        return G_MODULATED

    return G_DOMINATED


# ---------------------------------------------------------------------------
# Extract governance comparison from campaign comparison report
# ---------------------------------------------------------------------------

def extract_gov_comparison(
    comparison_report: Dict[str, Any],
    turns: int,
) -> Optional[Dict[str, Any]]:
    """Find the A-vs-B governance comparison entry for a given turn count."""
    comps = comparison_report.get("comparisons_by_horizon", {}).get(str(turns), [])
    for comp in comps:
        if "lh_A" in comp.get("campaign_a", "") and "lh_B" in comp.get("campaign_b", ""):
            return comp
        if "gov_sensitivity" in comp.get("label", "").lower():
            return comp
    return None


# ---------------------------------------------------------------------------
# Build per-metric, per-horizon classification
# ---------------------------------------------------------------------------

def build_governance_horizon_entries(
    comparison_report: Dict[str, Any],
    turn_counts: List[int],
) -> List[Dict[str, Any]]:
    """Build a list of (metric × horizon) governance classification entries."""
    # Collect all metrics from the first available comparison
    all_metrics: List[str] = []
    for t in turn_counts:
        comp = extract_gov_comparison(comparison_report, t)
        if comp:
            all_metrics = list(comp.get("metrics", {}).keys())
            break

    if not all_metrics:
        return []

    entries: List[Dict[str, Any]] = []
    for metric in all_metrics:
        horizon_results: Dict[str, Any] = {}
        first_sensitive_horizon: Optional[int] = None

        for t in turn_counts:
            comp = extract_gov_comparison(comparison_report, t)
            if not comp:
                horizon_results[str(t)] = {"classification": G_INSUFFICIENT}
                continue

            m_data = comp.get("metrics", {}).get(metric, {})
            delta = m_data.get("delta")
            d_val = m_data.get("cohens_d")
            fp_thresh = FP_THRESHOLDS.get(metric)

            classification = classify_governance_effect(metric, delta, d_val, fp_thresh)
            horizon_results[str(t)] = {
                "classification": classification,
                "delta": delta,
                "cohens_d": d_val,
            }

            if first_sensitive_horizon is None and classification in (G_DOMINATED, G_MODULATED):
                first_sensitive_horizon = t

        entries.append({
            "metric": metric,
            "horizon_classifications": horizon_results,
            "first_sensitive_horizon": first_sensitive_horizon,
            "neutral_at_all_horizons": first_sensitive_horizon is None,
        })

    return entries


# ---------------------------------------------------------------------------
# Synthetic fallback
# ---------------------------------------------------------------------------

def _build_synthetic_comparison_report(turn_counts: List[int]) -> Dict[str, Any]:
    """Construct a synthetic comparison report for when live data isn't available."""
    comparisons_by_horizon: Dict[str, Any] = {}
    for t in turn_counts:
        # At short horizons: all neutral.  At 100 turns: avg_control_effort becomes sensitive.
        scale = t / 100.0
        comparisons_by_horizon[str(t)] = [
            {
                "label": "lh_A_vs_lh_B__gov_sensitivity",
                "campaign_a": "lh_A",
                "campaign_b": "lh_B",
                "total_turns": t,
                "metrics": {
                    "path_smoothness":           {"delta": 0.01 * scale, "cohens_d": 0.05 * scale},
                    "avg_control_effort":        {"delta": 0.05 * scale, "cohens_d": 0.30 * scale},
                    "stability_score":           {"delta": 0.02 * scale, "cohens_d": 0.10 * scale},
                    "mean_position_error":       {"delta": 0.10 * scale, "cohens_d": 0.12 * scale},
                    "audit_bandwidth":           {"delta": 0.50 * scale, "cohens_d": 0.08 * scale},
                    "anisotropy_score":          {"delta": 0.02 * scale, "cohens_d": 0.15 * scale},
                    "observer_dependence_score": {"delta": 0.20 * scale, "cohens_d": 0.10 * scale},
                },
            }
        ]
    return {
        "turn_counts": turn_counts,
        "comparisons_by_horizon": comparisons_by_horizon,
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_governance_horizon_effects(
    output_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Classify governance effects across turn horizons.

    Uses live Stage 6 comparison report if available; falls back to synthetic.
    """
    root = output_root or _OUTPUT_ROOT

    comp_path = root / "campaign_comparison_report.json"
    comparison_report = _load_json(comp_path)
    data_source = "live"

    if comparison_report:
        turn_counts = [int(t) for t in comparison_report.get("turn_counts", [])]
    else:
        turn_counts = [5, 25, 50, 100]
        comparison_report = _build_synthetic_comparison_report(turn_counts)
        data_source = "synthetic_fallback"

    entries = build_governance_horizon_entries(comparison_report, turn_counts)

    # Build summary
    any_sensitive = [
        e for e in entries if not e.get("neutral_at_all_horizons")
    ]
    all_neutral = [
        e for e in entries if e.get("neutral_at_all_horizons")
    ]

    # Determine earliest horizon where any governance effect appears
    earliest_effect_horizon: Optional[int] = None
    for e in entries:
        fsh = e.get("first_sensitive_horizon")
        if fsh is not None:
            if earliest_effect_horizon is None or fsh < earliest_effect_horizon:
                earliest_effect_horizon = fsh

    report = {
        "data_source": data_source,
        "turn_counts_evaluated": turn_counts,
        "n_metrics": len(entries),
        "metrics_showing_governance_sensitivity": [
            e["metric"] for e in any_sensitive
        ],
        "metrics_neutral_at_all_horizons": [
            e["metric"] for e in all_neutral
        ],
        "earliest_effect_horizon": earliest_effect_horizon,
        "interpretation": (
            f"Governance effects first detectable at {earliest_effect_horizon} turns."
            if earliest_effect_horizon
            else "Governance remained neutral across all evaluated horizons. "
                 "Longer runs or different conditions may be required."
        ),
        "metrics": entries,
    }

    root.mkdir(parents=True, exist_ok=True)
    (root / "governance_horizon_report.json").write_text(json.dumps(report, indent=2))

    print(
        f"Governance horizon analysis complete ({data_source}).\n"
        f"  Horizons: {turn_counts}\n"
        f"  Sensitive metrics: {[e['metric'] for e in any_sensitive]}\n"
        f"  Neutral at all horizons: {[e['metric'] for e in all_neutral]}\n"
        f"  Earliest governance effect: {earliest_effect_horizon}\n"
        f"  Output: {root}"
    )
    return report


if __name__ == "__main__":
    run_governance_horizon_effects()
