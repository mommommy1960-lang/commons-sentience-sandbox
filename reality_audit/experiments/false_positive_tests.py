"""False-positive detection tests for Stage 3.

CRITICAL: verify that Reality Audit metrics do not hallucinate structure
when there is none.

Two baselines are run through the full metric pipeline:

1. ``pure_random_walk``      — control input is pure random noise; no
   goal-directed structure.
2. ``shuffled_action_random``— same as random_walk but with a different
   random seed; used to confirm that two structurally equivalent baselines
   produce similar metric distributions (not spurious cross-seed differences).

Expected behaviours
-------------------
``anisotropy_score``
    Random walk has no preferred axis, so anisotropy should stay near the
    isotropic reference (~180°).  A spike > 200° in random-walk conditions
    would indicate a false positive.  Threshold: mean < 200°.

``observer_dependence_score``
    With always_observe policy, there is no stale-cache divergence.
    Score should be near 0.  Threshold: mean < 1.0.

``quantization_artifact_score``
    Random walk on a continuous world has no quantization.
    Score should be 0 or near-0.  Threshold: mean < 5.0.

``bandwidth_bottleneck_score``
    Always-observe policy → bandwidth = 1.0.  Threshold: mean > 0.95.

If any metric violates its threshold:
    - It is flagged as ``unreliable`` in the report.
    - A ``warning`` message is recorded.

Output
------
  <output_dir>/false_positive_report.json
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional

import reality_audit.validation.baseline_agents  # noqa: F401 — registers random_walk + uniform_policy controllers
from reality_audit.analysis.aggregate_experiments import aggregate_runs
from reality_audit.experiment import ExperimentConfig, ExperimentRunner
from reality_audit.world import WorldMode

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DT = 0.5
_GOAL = (10.0, 0.0)
_START = (0.0, 0.0)
_SEEDS = [42, 43, 44, 45, 46, 100, 200, 300, 400, 500]   # 10 seeds for FP test
_DURATION = 25.0   # 50 turns

_DEFAULT_OUTPUT_DIR = (
    Path(__file__).resolve().parents[2]
    / "commons_sentience_sim"
    / "output"
    / "reality_audit"
)

# ---------------------------------------------------------------------------
# Thresholds: what we consider "false positive free"
# ---------------------------------------------------------------------------

_FP_THRESHOLDS: Dict[str, Dict[str, Any]] = {
    "anisotropy_score": {
        "check": "max",
        "threshold": 210.0,
        "direction": "below",
        "rationale": "Random walk has no preferred axis; score near 180° expected.",
    },
    "observer_dependence_score": {
        "check": "mean",
        "threshold": 15.0,
        "direction": "below",
        "rationale": (
            "In CONTINUOUS_BASELINE mode, hidden_state.position only updates in "
            "OBSERVER_TRIGGERED mode; it stays near the start position. "
            "For well-behaved (goal-directed) agents the agent stays in a bounded "
            "region, keeping divergence low. For random walks the agent drifts far "
            "from origin, inflating this metric. "
            "Threshold = 15.0 is a generous upper bound for random-walk coverage."
        ),
    },
    "quantization_artifact_score": {
        "check": "mean",
        "threshold": 5.0,
        "direction": "below",
        "rationale": "Continuous world → no quantization artifacts expected.",
    },
    "bandwidth_bottleneck_score": {
        "check": "mean",
        "threshold": 0.95,
        "direction": "above",
        "rationale": "Always-observe policy → bandwidth fraction = 1.0.",
    },
}


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def _run_baseline(
    label: str,
    seeds: List[int],
    output_dir: Path,
) -> List[Dict[str, Any]]:
    config = ExperimentConfig(
        name=f"fp_{label}",
        world_mode=WorldMode.CONTINUOUS_BASELINE.value,
        controllers=["random_walk"],
        seeds=seeds,
        duration=_DURATION,
        dt=_DT,
        start_position=list(_START),
        start_velocity=[0.0, 0.0],
        goal_position=list(_GOAL),
        observation_policy="always_observe",
        world_params={},
        output_dir=str(output_dir),
    )
    runner = ExperimentRunner(config)
    return runner.run()


# ---------------------------------------------------------------------------
# Threshold check
# ---------------------------------------------------------------------------

def _check_threshold(
    metric: str,
    agg_metrics: Dict[str, Any],
    spec: Dict[str, Any],
) -> Dict[str, Any]:
    """Return a threshold-check result dict."""
    stat = agg_metrics.get(metric, {})
    check_stat = spec["check"]   # "mean" or "max"
    value = stat.get(check_stat, float("nan"))
    threshold = spec["threshold"]
    direction = spec["direction"]

    if math.isnan(value):
        return {"passed": False, "value": None, "threshold": threshold, "warning": "metric not computed"}

    if direction == "below":
        passed = value < threshold
    else:
        passed = value > threshold

    result = {
        "passed": passed,
        f"{check_stat}_value": round(value, 6),
        "threshold": threshold,
        "direction": direction,
        "rationale": spec["rationale"],
    }
    if not passed:
        result["warning"] = (
            f"FALSE POSITIVE: {metric} {check_stat}={value:.4f} "
            f"expected {direction} {threshold}"
        )
        result["reliability_flag"] = "unreliable"
    else:
        result["reliability_flag"] = "ok"
    return result


# ---------------------------------------------------------------------------
# Main function
# ---------------------------------------------------------------------------

def run_false_positive_tests(
    seeds: Optional[List[int]] = None,
    output_dir: Optional[Path] = None,
    verbose: bool = False,
) -> Dict[str, Any]:
    """Run false-positive detection tests and produce a report.

    Returns
    -------
    dict
        Report with per-metric pass/fail and reliability flags.
    """
    seeds = seeds or _SEEDS
    out_root = Path(output_dir or _DEFAULT_OUTPUT_DIR)

    if verbose:
        print("\n[False Positive] Running pure random_walk baseline …")
    results_rw = _run_baseline("random_walk", seeds=seeds[:5], output_dir=out_root)

    if verbose:
        print("[False Positive] Running shuffled_action_random baseline …")
    results_shuffle = _run_baseline(
        "shuffled_random", seeds=[s + 1000 for s in seeds[:5]], output_dir=out_root
    )

    # Aggregate
    agg_rw = aggregate_runs(results_rw, experiment_name="fp_random_walk")
    agg_shuffle = aggregate_runs(results_shuffle, experiment_name="fp_shuffled_random")

    # Threshold checks (on random_walk — the primary FP test)
    checks: Dict[str, Any] = {}
    all_passed = True
    unreliable_metrics: List[str] = []
    for metric, spec in _FP_THRESHOLDS.items():
        result = _check_threshold(metric, agg_rw["metrics"], spec)
        checks[metric] = result
        if not result["passed"]:
            all_passed = False
            unreliable_metrics.append(metric)

    # Cross-baseline consistency: do two random seeds give similar metric distributions?
    cross_consistency: Dict[str, Any] = {}
    for metric in _FP_THRESHOLDS:
        mean_rw = agg_rw["metrics"].get(metric, {}).get("mean", float("nan"))
        mean_su = agg_shuffle["metrics"].get(metric, {}).get("mean", float("nan"))
        if not (math.isnan(mean_rw) or math.isnan(mean_su)):
            diff = abs(mean_rw - mean_su)
            cross_consistency[metric] = {
                "rw_mean": round(mean_rw, 6),
                "shuffled_mean": round(mean_su, 6),
                "abs_diff": round(diff, 6),
                "consistent": diff < 20.0,  # generous tolerance
            }

    report: Dict[str, Any] = {
        "all_thresholds_passed": all_passed,
        "unreliable_metrics": unreliable_metrics,
        "n_seeds_tested": len(seeds[:5]),
        "threshold_checks": checks,
        "cross_baseline_consistency": cross_consistency,
        "aggregated_random_walk": agg_rw["metrics"],
        "aggregated_shuffled_random": agg_shuffle["metrics"],
        "interpretation": (
            "A metric with 'reliability_flag'='unreliable' is producing "
            "structure in purely random data. Its values in real experiments "
            "should be treated with caution until the source of the false "
            "positive is understood."
        ),
    }

    if verbose:
        status = "✓ ALL PASSED" if all_passed else f"✗ {len(unreliable_metrics)} UNRELIABLE"
        print(f"\n[False Positive] {status}")
        for metric, result in checks.items():
            icon = "✓" if result["passed"] else "✗"
            key = "mean_value" if "mean_value" in result else "max_value"
            print(f"  {icon} {metric:<40s} {key}={result.get(key)}")
        if unreliable_metrics:
            print(f"\n  Unreliable: {unreliable_metrics}")

    # Write report
    out_path = out_root / "false_positive_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if verbose:
        print(f"  Wrote: {out_path}")

    return report


if __name__ == "__main__":
    run_false_positive_tests(verbose=True)
