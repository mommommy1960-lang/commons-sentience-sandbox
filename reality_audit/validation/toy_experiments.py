"""Toy / validation experiments with deliberately predictable outcomes.

Each scenario is self-contained: it constructs a ``RealityWorld`` with a
specific ``WorldMode``, runs the control loop for a short episode, and
returns a metrics dict.  The metrics can then be compared against expected
qualitative directions in tests.

Scenarios
---------
A. straight_path_baseline
   Continuous world, proportional controller, no distortion.
   Expected: low observer_dependence, stable path, low anomaly metrics.

B. anisotropy_scenario
   Anisotropic world with strong axis preference.
   Expected: anisotropy_score higher than baseline.

C. observer_divergence_scenario
   Continuous world with periodic (sparse) observation.
   Expected: observer_dependence_score higher than always-observe baseline.

D. bandwidth_staleness_scenario
   Bandwidth-limited world — sensor cache frozen between updates.
   Expected: bandwidth_bottleneck_score < 1.0, stability_score lower than
   baseline.
"""

from __future__ import annotations

import math
from typing import Any, Dict, Optional

from reality_audit.controller import ProportionalController
from reality_audit.experiment import ExperimentConfig, ExperimentRunner
from reality_audit.measurement import MeasurementSuite
from reality_audit.world import RealityWorld, WorldConfig, WorldMode

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

_DURATION = 5.0        # seconds (short enough for tests)
_DT = 0.1
_GOAL = (5.0, 0.0)
_START = (0.0, 0.0)
_SEED = 42


# ---------------------------------------------------------------------------
# Internal runner
# ---------------------------------------------------------------------------

def _run_scenario(
    mode: WorldMode,
    observe_policy: str = "always_observe",
    world_params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Run one episode and return the metrics dict."""
    config = ExperimentConfig(
        name=f"toy_{mode.value}",
        world_mode=mode.value,
        controllers=["proportional"],
        seeds=[_SEED],
        duration=_DURATION,
        dt=_DT,
        start_position=list(_START),
        start_velocity=[0.0, 0.0],
        goal_position=list(_GOAL),
        observation_policy=observe_policy,
        world_params=world_params or {},
        output_dir="outputs/toy_experiments",
    )
    runner = ExperimentRunner(config)
    results = runner.run()
    return results[0]["metrics"]


# ---------------------------------------------------------------------------
# Public scenario functions
# ---------------------------------------------------------------------------

def scenario_A_straight_path_baseline() -> Dict[str, Any]:
    """Scenario A: deterministic straight-path baseline.

    Continuous world, proportional controller, always observed, no noise.
    """
    return _run_scenario(WorldMode.CONTINUOUS_BASELINE, observe_policy="always_observe")


def scenario_B_anisotropy() -> Dict[str, Any]:
    """Scenario B: deliberate anisotropy.

    Anisotropic world with strong axis preference (axis_strength=3.0).
    """
    return _run_scenario(
        WorldMode.ANISOTROPIC_PREFERRED_AXIS,
        observe_policy="always_observe",
        world_params={"axis_angle": 0.0, "axis_strength": 3.0},
    )


def scenario_C_observer_divergence() -> Dict[str, Any]:
    """Scenario C: deliberate observer divergence.

    Continuous world but observation is periodic (every 10 steps ≈ 1 s).
    The sensor cache goes stale between observations, so hidden state and
    measured state diverge.
    """
    return _run_scenario(
        WorldMode.OBSERVER_TRIGGERED_UPDATES,
        observe_policy="periodic_observe",
        world_params={"observe_period": 10},
    )


def scenario_D_bandwidth_staleness() -> Dict[str, Any]:
    """Scenario D: deliberate bandwidth / stale-information scenario.

    Bandwidth-limited world — the update gate fires only when there is
    bandwidth, and the observe_period forces sparse sensor refreshes.
    True physics still advance each step; only the sensor cache freezes.
    """
    return _run_scenario(
        WorldMode.BANDWIDTH_LIMITED,
        observe_policy="periodic_observe",
        world_params={
            "bandwidth_p": 0.2,  # 20 % pass-through rate → high staleness
            "observe_period": 5,
        },
    )


# ---------------------------------------------------------------------------
# Run-all convenience function
# ---------------------------------------------------------------------------

def run_all_toy_scenarios(verbose: bool = False) -> Dict[str, Dict[str, Any]]:
    """Run all four toy scenarios and return a dict keyed by scenario label."""
    scenarios = {
        "A_straight_path_baseline": scenario_A_straight_path_baseline,
        "B_anisotropy": scenario_B_anisotropy,
        "C_observer_divergence": scenario_C_observer_divergence,
        "D_bandwidth_staleness": scenario_D_bandwidth_staleness,
    }
    results: Dict[str, Dict[str, Any]] = {}
    for label, fn in scenarios.items():
        metrics = fn()
        results[label] = metrics
        if verbose:
            print(f"\n── Scenario {label} ──")
            for k, v in metrics.items():
                print(f"  {k:<35} {v:.4f}")
    return results


if __name__ == "__main__":
    run_all_toy_scenarios(verbose=True)
