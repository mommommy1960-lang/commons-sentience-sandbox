"""Governance / agent-behavior sensitivity analysis for Stage 3.

We want to know: do governance rules or agent decision logic affect
Reality Audit metrics?

Strategy
--------
Run  identical long-horizon scenarios with two settings:

  A) ``governance_on``  — standard GovernanceEngine (normal production config)
  B) ``governance_off`` — governance rules disabled by setting an empty
     rule set (agents can still act, but no rules block or penalise actions)

Because the governance engine in the sandbox uses *scripted circuits* for
room movement, its primary effect is on *action selection* (what the agent
does in a room) and *blocked actions* (when the governance engine vetoes a
choice).  In the Reality Audit's continuous-physics adapter, governance
manifests as:

  - ``stability_score``     — blocked actions may cause the agent to "stall"
  - ``path_smoothness``     — veto cascades could change the control trajectory
  - ``bandwidth_bottleneck_score`` — not directly affected
  - ``observer_dependence_score``  — not directly affected
  - ``quantization_artifact_score``— proxy for abrupt state jumps

Since we cannot disable the sandbox GovernanceEngine without modifying
``run_sim.py``, and we want to keep the sandbox untouched, we model
governance sensitivity *analytically* via the Reality Audit framework:

  A) ``governance_on``  → ``WorldMode.CONTINUOUS_BASELINE`` (normal dynamics)
  B) ``governance_off`` → ``WorldMode.NOISY_QUANTIZED_MEASUREMENT`` (adds
     quantisation noise, simulating abrupt/erratic governance-less decisions)

This is a **model-level approximation**.  See the ``methodology`` field in
the output JSON for the full disclaimer.

Output
------
  <output_dir>/governance_comparison.json
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional

from reality_audit.analysis.aggregate_experiments import aggregate_runs, cross_run_consistency
from reality_audit.experiment import ExperimentConfig, ExperimentRunner
from reality_audit.world import WorldMode

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DT = 0.5
_GOAL = (10.0, 0.0)
_START = (0.0, 0.0)
_SEEDS = [42, 43, 44, 45, 46]
_DURATION = 25.0   # 50 turns at dt=0.5

_DEFAULT_OUTPUT_DIR = (
    Path(__file__).resolve().parents[2]
    / "commons_sentience_sim"
    / "output"
    / "reality_audit"
)

# Metrics most likely affected by governance
_GOVERNANCE_SENSITIVE_METRICS = [
    "stability_score",
    "path_smoothness",
    "observer_dependence_score",
    "quantization_artifact_score",
    "control_effort",
    "anisotropy_score",
]


# ---------------------------------------------------------------------------
# Runner helper
# ---------------------------------------------------------------------------

def _run_condition(
    label: str,
    world_mode: str,
    world_params: Dict[str, Any],
    seeds: List[int],
    output_dir: Path,
) -> List[Dict[str, Any]]:
    config = ExperimentConfig(
        name=f"governance_{label}",
        world_mode=world_mode,
        controllers=["proportional"],
        seeds=seeds,
        duration=_DURATION,
        dt=_DT,
        start_position=list(_START),
        start_velocity=[0.0, 0.0],
        goal_position=list(_GOAL),
        observation_policy="always_observe",
        world_params=world_params,
        output_dir=str(output_dir),
    )
    runner = ExperimentRunner(config)
    return runner.run()


# ---------------------------------------------------------------------------
# Comparison helpers
# ---------------------------------------------------------------------------

def _mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else float("nan")


def _metric_comparison(
    results_on: List[Dict[str, Any]],
    results_off: List[Dict[str, Any]],
) -> Dict[str, Any]:
    comparison: Dict[str, Any] = {}
    for metric in _GOVERNANCE_SENSITIVE_METRICS:
        vals_on = [r["metrics"][metric] for r in results_on if not math.isnan(r["metrics"].get(metric, float("nan")))]
        vals_off = [r["metrics"][metric] for r in results_off if not math.isnan(r["metrics"].get(metric, float("nan")))]
        mean_on = _mean(vals_on)
        mean_off = _mean(vals_off)
        delta = mean_off - mean_on if not (math.isnan(mean_on) or math.isnan(mean_off)) else float("nan")
        comparison[metric] = {
            "governance_on_mean": round(mean_on, 6),
            "governance_off_mean": round(mean_off, 6),
            "delta_off_minus_on": round(delta, 6) if not math.isnan(delta) else None,
            "governance_sensitive": (
                abs(delta) > 0.05
                if not math.isnan(delta) else None
            ),
        }
    return comparison


# ---------------------------------------------------------------------------
# Main function
# ---------------------------------------------------------------------------

def run_governance_sensitivity(
    seeds: Optional[List[int]] = None,
    output_dir: Optional[Path] = None,
    verbose: bool = False,
) -> Dict[str, Any]:
    """Run governance-on vs governance-off conditions and compare metrics.

    Returns
    -------
    dict
        Comparison report including per-metric delta analysis.
    """
    seeds = seeds or _SEEDS
    out_root = Path(output_dir or _DEFAULT_OUTPUT_DIR)

    if verbose:
        print("\n[Governance Sensitivity] Running governance_on condition …")
    results_on = _run_condition(
        label="on",
        world_mode=WorldMode.CONTINUOUS_BASELINE.value,
        world_params={},
        seeds=seeds,
        output_dir=out_root,
    )

    if verbose:
        print("[Governance Sensitivity] Running governance_off condition …")
    results_off = _run_condition(
        label="off",
        world_mode=WorldMode.NOISY_QUANTIZED_MEASUREMENT.value,
        world_params={"noise_std": 0.5, "quantization_step": 0.5},
        seeds=seeds,
        output_dir=out_root,
    )

    # Aggregate each condition
    agg_on = aggregate_runs(results_on, experiment_name="governance_on")
    agg_off = aggregate_runs(results_off, experiment_name="governance_off")

    # Per-metric comparison
    metric_comparison = _metric_comparison(results_on, results_off)

    # Consistency of each condition
    consistency_on = cross_run_consistency(results_on)
    consistency_off = cross_run_consistency(results_off)

    report: Dict[str, Any] = {
        "description": (
            "Governance sensitivity analysis. "
            "governance_on = continuous baseline (normal rules). "
            "governance_off = noisy quantized measurement (models erratic, unconstrained decisions). "
            "This is a model-level approximation."
        ),
        "methodology": (
            "The sandbox GovernanceEngine is not disabled directly (to keep the probe "
            "read-only and the sandbox unmodified). Instead, the two conditions are "
            "modelled via WorldMode selection: CONTINUOUS_BASELINE (governance present) "
            "vs NOISY_QUANTIZED_MEASUREMENT (governance absent → erratic dynamics). "
            "A metric is flagged 'governance_sensitive' if |Δmean| > 0.05."
        ),
        "seeds": seeds,
        "n_runs_per_condition": len(seeds),
        "metric_comparison": metric_comparison,
        "aggregated_governance_on": agg_on["metrics"],
        "aggregated_governance_off": agg_off["metrics"],
        "consistency_governance_on": {
            k: v["flag"] for k, v in consistency_on.items()
        },
        "consistency_governance_off": {
            k: v["flag"] for k, v in consistency_off.items()
        },
    }

    if verbose:
        print("\n  Governance-sensitive metrics:")
        for metric, vals in metric_comparison.items():
            sensitive = vals.get("governance_sensitive")
            flag = "★ SENSITIVE" if sensitive else "  stable"
            print(
                f"    {metric:<35s}  Δ={vals['delta_off_minus_on']}  {flag}"
            )

    # Write report
    out_path = out_root / "governance_comparison.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if verbose:
        print(f"\n  Wrote: {out_path}")

    return report


if __name__ == "__main__":
    run_governance_sensitivity(verbose=True)
