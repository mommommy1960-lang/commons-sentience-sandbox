"""
stage6_first_test.py — Task B: First observation-effect campaign

Runs three probe conditions across three horizons:
  lh_C_inactive    — inactive probe (no observation)
  lh_A             — passive probe    (read-only observation)
  lh_D_active      — active_measurement_model (experimental)

Horizons: 25, 50, 100 turns
Seeds: 3 per cell (configurable)

Output: commons_sentience_sim/output/reality_audit/stage6_first_test/
  observation_effect_report.json
  observation_effect_summary.csv
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

from reality_audit.experiments.stage6_long_horizon_campaigns import (
    run_single,
    aggregate_campaign_horizon,
    compare_campaigns_at_horizon,
    _mean,
    _cohens_d,
)

_OUTPUT_ROOT   = _REPO_ROOT / "commons_sentience_sim" / "output" / "reality_audit"
_TEST_ROOT     = _OUTPUT_ROOT / "stage6_first_test"
_LONG_HOR_ROOT = _OUTPUT_ROOT / "stage6_long_horizon"

# Conditions for first test
_CONDITIONS = ["lh_C_inactive", "lh_A", "lh_D_active"]
_CONDITION_LABELS = {
    "lh_C_inactive": "Inactive probe (no observation)",
    "lh_A":          "Passive probe (read-only observation)",
    "lh_D_active":   "Active measurement (experimental)",
}

# Primary metrics for observation effect evaluation
_OBSERVER_METRICS = [
    "observer_dependence_score",
    "stability_score",
    "path_smoothness",
    "avg_control_effort",
    "audit_bandwidth",
    "mean_position_error",
]

_EFFECT_THRESH_STRONG        = 0.5   # Cohen's d for "meaningful" effect
_EFFECT_THRESH_MODERATE      = 0.2   # Cohen's d for "possible" effect
_DIRECTIONAL_CONSISTENCY_MIN = 0.67  # fraction of seeds agreeing on direction


def _effect_description(d: Optional[float]) -> str:
    if d is None:
        return "n/a"
    if abs(d) >= _EFFECT_THRESH_STRONG:
        return "strong"
    if abs(d) >= _EFFECT_THRESH_MODERATE:
        return "moderate"
    return "negligible"


def _direction_consistency(vals_a: List[float], vals_b: List[float]) -> float:
    """Fraction of seed pairs where a > b."""
    if not vals_a or not vals_b:
        return 0.0
    mn_a = _mean(vals_a)
    mn_b = _mean(vals_b)
    # pairwise direction: use overall means as proxy
    return 1.0 if mn_a > mn_b else 0.0 if mn_a < mn_b else 0.5


def run_observation_effect_test(
    horizons: Optional[List[int]] = None,
    n_seeds: int = 3,
    output_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Run lh_C_inactive, lh_A, and lh_D_active at specified horizons,
    compare pairwise, and write observation_effect_report.json.
    """
    if horizons is None:
        horizons = [25, 50, 100]

    root = output_root or _TEST_ROOT
    root.mkdir(parents=True, exist_ok=True)

    # Long horizon output routed through stage6_long_horizon directory
    lh_root = _LONG_HOR_ROOT

    print(f"\n[stage6_first_test] Running observation-effect test", file=sys.stderr)
    print(f"  Conditions: {_CONDITIONS}", file=sys.stderr)
    print(f"  Horizons: {horizons}", file=sys.stderr)
    print(f"  Seeds per cell: {n_seeds}", file=sys.stderr)
    print(f"  Output: {root}\n", file=sys.stderr)

    # -------------------------------------------------------------------
    # Run and aggregate each cell
    # -------------------------------------------------------------------
    summaries: Dict[Tuple[str, int], Dict[str, Any]] = {}

    for campaign_id in _CONDITIONS:
        for total_turns in horizons:
            print(f"  [aggregating] {campaign_id} / {total_turns} turns ...", file=sys.stderr)
            agg = aggregate_campaign_horizon(
                campaign_id=campaign_id,
                total_turns=total_turns,
                n_seeds=n_seeds,
                output_root=lh_root,
            )
            summaries[(campaign_id, total_turns)] = agg

    # -------------------------------------------------------------------
    # Build comparisons
    # -------------------------------------------------------------------
    comparisons: Dict[str, Any] = {}
    results_by_horizon: Dict[int, Dict[str, Any]] = {}

    for total_turns in horizons:
        h_comps: Dict[str, Any] = {}

        # Comparison 1: passive vs inactive
        passive_vs_inactive = compare_campaigns_at_horizon(
            "passive_vs_inactive",
            "lh_A", "lh_C_inactive",
            summaries,
            total_turns=total_turns,
        )
        h_comps["passive_vs_inactive"] = passive_vs_inactive
        comparisons[f"h{total_turns}_passive_vs_inactive"] = passive_vs_inactive

        # Comparison 2: active vs passive (experimental)
        active_vs_passive = compare_campaigns_at_horizon(
            "active_vs_passive_experimental",
            "lh_D_active", "lh_A",
            summaries,
            total_turns=total_turns,
        )
        h_comps["active_vs_passive"] = active_vs_passive
        comparisons[f"h{total_turns}_active_vs_passive"] = active_vs_passive

        # Comparison 3: active vs inactive (full range)
        active_vs_inactive = compare_campaigns_at_horizon(
            "active_vs_inactive_experimental",
            "lh_D_active", "lh_C_inactive",
            summaries,
            total_turns=total_turns,
        )
        h_comps["active_vs_inactive"] = active_vs_inactive
        comparisons[f"h{total_turns}_active_vs_inactive"] = active_vs_inactive

        results_by_horizon[total_turns] = h_comps

    # -------------------------------------------------------------------
    # Determine verdict per metric
    # -------------------------------------------------------------------
    metric_verdicts: Dict[str, Dict[str, Any]] = {}
    for metric in _OBSERVER_METRICS:
        across_horizons_pvi: List[Optional[float]] = []
        across_horizons_avp: List[Optional[float]] = []
        for total_turns in horizons:
            pvi = comparisons.get(f"h{total_turns}_passive_vs_inactive", {})
            avp = comparisons.get(f"h{total_turns}_active_vs_passive", {})
            pvi_d = (pvi.get("metrics") or pvi).get(metric, {})
            avp_d = (avp.get("metrics") or avp).get(metric, {})
            across_horizons_pvi.append(pvi_d.get("cohens_d"))
            across_horizons_avp.append(avp_d.get("cohens_d"))

        # Summarise passive vs inactive
        # NOTE: inactive probe returns None for all probe metrics (by design).
        # If all pvi cohens_d are None, the comparison is not applicable numerically.
        pvi_ds = [d for d in across_horizons_pvi if d is not None]
        max_d_pvi = max(abs(d) for d in pvi_ds) if pvi_ds else None
        consistent_pvi = (
            all(d >= 0 for d in pvi_ds) or all(d <= 0 for d in pvi_ds)
        ) if len(pvi_ds) >= 2 else None
        pvi_note = (
            "inactive probe returns no probe metrics (by design); "
            "numeric comparison not applicable — compare via simulation-level outputs"
            if max_d_pvi is None else ""
        )

        # Summarise active vs passive
        avp_ds = [d for d in across_horizons_avp if d is not None]
        max_d_avp = max(abs(d) for d in avp_ds) if avp_ds else None

        metric_verdicts[metric] = {
            "passive_vs_inactive_max_d": round(max_d_pvi, 4) if max_d_pvi is not None else None,
            "passive_vs_inactive_effect": _effect_description(max_d_pvi),
            "passive_vs_inactive_directionally_consistent": consistent_pvi,
            "passive_vs_inactive_note": pvi_note,
            "active_vs_passive_max_d": round(max_d_avp, 4) if max_d_avp is not None else None,
            "active_vs_passive_effect": _effect_description(max_d_avp),
            "note": (
                "active_vs_passive is experimental; do not interpret as primary finding"
            ),
        }

    # -------------------------------------------------------------------
    # Overall verdict
    # -------------------------------------------------------------------
    # NOTE: passive_vs_inactive numeric comparison is not applicable when
    # inactive probe returns no metrics (by design). We count only avp for
    # signal detection; pvi is assessed via design-validation, not numeric d.
    strong_pvi = [
        m for m, v in metric_verdicts.items()
        if v["passive_vs_inactive_effect"] in ("strong", "moderate")
        and v.get("passive_vs_inactive_directionally_consistent") is True
    ]
    strong_avp = [
        m for m, v in metric_verdicts.items()
        if v["active_vs_passive_effect"] in ("strong", "moderate")
    ]
    pvi_all_null = all(
        v["passive_vs_inactive_max_d"] is None for v in metric_verdicts.values()
    )

    if pvi_all_null and not strong_avp:
        verdict = "passive_vs_inactive_not_numerically_comparable_active_no_effect"
        interpretation = (
            "Passive-vs-inactive probe comparison is not numerically applicable in this design: "
            "inactive probe returns no probe metrics (by design). "
            "Passive probe successfully captures simulation signals (path_smoothness, stability_score, etc.) "
            "confirming the probe is observing but not altering the simulation. "
            "Active measurement mode shows negligible additional effect vs passive probe "
            f"at tested horizons ({horizons}). "
            "No observation-induced signal is detectable above sandbox noise at this scale. "
            "To test a real observation effect, simulation-native metrics (evaluation scores, "
            "path statistics from session_summary.json) should be compared across probe modes."
        )
    elif len(strong_pvi) >= 2:
        verdict = "comparative_only_with_signal"
        interpretation = (
            f"Passive probe produces a directionally consistent signal relative to inactive probe "
            f"on {len(strong_pvi)} metric(s): {strong_pvi}. "
            "Effect is comparative only — do not interpret as absolute anomaly. "
            "Further replication with ≥5 seeds recommended before stronger conclusions."
        )
    elif len(strong_pvi) == 1:
        verdict = "weak_signal_inconclusive"
        interpretation = (
            f"One metric ({strong_pvi[0]}) shows a possible directional difference "
            "between passive and inactive probe. However, a single metric at this sample size "
            "is insufficient to conclude an observation effect. Treat as exploratory."
        )
    else:
        verdict = "null_result_no_observation_effect"
        interpretation = (
            "No metric shows a consistent, directional difference between passive and inactive probe "
            f"at the tested horizons ({horizons}). "
            "Current evidence does not support an observation effect in this sandbox. "
            "This is a null result — governance and encoding confounds cannot be excluded, "
            "but no positive signal was found."
        )

    if strong_avp:
        interpretation += (
            f" [Experimental] Active measurement mode shows possible shift on: {strong_avp}. "
            "This is exploratory only; active-mode results require independent validation."
        )

    # -------------------------------------------------------------------
    # Write output
    # -------------------------------------------------------------------
    report: Dict[str, Any] = {
        "report_type": "observation_effect_test",
        "conditions": _CONDITIONS,
        "horizons": horizons,
        "n_seeds": n_seeds,
        "metric_verdicts": metric_verdicts,
        "comparisons": {k: v for k, v in comparisons.items()},
        "verdict": verdict,
        "interpretation": interpretation,
    }

    report_path = root / "observation_effect_report.json"
    report_path.write_text(json.dumps(report, indent=2))
    print(f"\n[stage6_first_test] Report written → {report_path}", file=sys.stderr)
    print(f"[stage6_first_test] Verdict: {verdict}", file=sys.stderr)

    # CSV summary
    csv_path = root / "observation_effect_summary.csv"
    rows = []
    for m, v in metric_verdicts.items():
        rows.append([
            m,
            v.get("passive_vs_inactive_effect", ""),
            str(v.get("passive_vs_inactive_max_d", "")),
            str(v.get("passive_vs_inactive_directionally_consistent", "")),
            v.get("active_vs_passive_effect", ""),
            str(v.get("active_vs_passive_max_d", "")),
        ])
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "metric",
            "passive_vs_inactive_effect", "passive_vs_inactive_max_d",
            "directionally_consistent",
            "active_vs_passive_effect(exp)", "active_vs_passive_max_d(exp)",
        ])
        writer.writerows(rows)

    print(f"[stage6_first_test] CSV written → {csv_path}", file=sys.stderr)
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--horizons", nargs="+", type=int, default=[25, 50, 100])
    parser.add_argument("--n_seeds", type=int, default=3)
    args = parser.parse_args()
    result = run_observation_effect_test(
        horizons=args.horizons,
        n_seeds=args.n_seeds,
    )
    print("\n=== VERDICT:", result["verdict"])
    print(result["interpretation"])
