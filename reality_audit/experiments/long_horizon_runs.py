"""Long-horizon experiment runs for Stage 3 statistical validation.

This module runs the Reality Audit framework for extended durations
(equivalent to 50, 75, and 100 "turns") across multiple seeds and
world-mode conditions.  Each scenario produces:

  <output_dir>/
    <scenario_name>/
      run_<seed>/
        raw_log.json
        summary.json
      aggregated_summary.json

Scenarios
---------
``baseline``              : Continuous baseline, proportional controller.
``anisotropy``            : Anisotropic preferred-axis world.
``observer_divergence``   : Periodic observation (sparse).
``bandwidth_limited``     : Bandwidth-limited sensor gate.
``random_baseline_agent`` : Random-walk controller (null baseline).
``normal_agent``          : Proportional controller, continuous world
                            (alias for baseline — included for naming clarity
                            when comparing against random_baseline_agent).

Duration mapping
----------------
The ``RealityWorld`` runs in continuous time with a fixed dt.
"Turns" here correspond to integration steps.

  50  turns  →  duration = 25.0 s  (dt = 0.5 → 50 steps)
  75  turns  →  duration = 37.5 s
  100 turns  →  duration = 50.0 s

Seeds: 5 per configuration (42, 43, 44, 45, 46) by default.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional

import reality_audit.validation.baseline_agents  # noqa: F401 — registers random_walk + uniform_policy controllers
from reality_audit.experiment import ExperimentConfig, ExperimentRunner
from reality_audit.world import WorldMode

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DT = 0.5          # 1 "turn" = 0.5 s
_GOAL = (10.0, 0.0)
_START = (0.0, 0.0)
_DEFAULT_SEEDS = [42, 43, 44, 45, 46]

# Maps "N turns" → wall-clock duration in seconds
_TURN_COUNTS = {50: 25.0, 75: 37.5, 100: 50.0}

_DEFAULT_OUTPUT_DIR = (
    Path(__file__).resolve().parents[2]
    / "commons_sentience_sim"
    / "output"
    / "reality_audit"
    / "long_runs"
)

# ---------------------------------------------------------------------------
# Scenario definitions
# ---------------------------------------------------------------------------

_SCENARIOS: Dict[str, Dict[str, Any]] = {
    "baseline": {
        "world_mode": WorldMode.CONTINUOUS_BASELINE.value,
        "controllers": ["proportional"],
        "observation_policy": "always_observe",
        "world_params": {},
    },
    "anisotropy": {
        "world_mode": WorldMode.ANISOTROPIC_PREFERRED_AXIS.value,
        "controllers": ["proportional"],
        "observation_policy": "always_observe",
        "world_params": {"axis_angle": 0.0, "axis_strength": 3.0},
    },
    "observer_divergence": {
        "world_mode": WorldMode.OBSERVER_TRIGGERED_UPDATES.value,
        "controllers": ["proportional"],
        "observation_policy": "periodic_observe",
        "world_params": {"observe_period": 5},
    },
    "bandwidth_limited": {
        "world_mode": WorldMode.BANDWIDTH_LIMITED.value,
        "controllers": ["proportional"],
        "observation_policy": "periodic_observe",
        "world_params": {"observe_period": 10, "bandwidth_fraction": 0.2},
    },
    "random_baseline_agent": {
        "world_mode": WorldMode.CONTINUOUS_BASELINE.value,
        "controllers": ["random_walk"],
        "observation_policy": "always_observe",
        "world_params": {},
    },
    "normal_agent": {
        "world_mode": WorldMode.CONTINUOUS_BASELINE.value,
        "controllers": ["proportional"],
        "observation_policy": "always_observe",
        "world_params": {},
    },
}


# ---------------------------------------------------------------------------
# Run helpers
# ---------------------------------------------------------------------------

def run_scenario(
    scenario_name: str,
    n_turns: int,
    seeds: Optional[List[int]] = None,
    output_dir: Optional[Path] = None,
    verbose: bool = False,
) -> Dict[str, Any]:
    """Run a single named scenario for *n_turns* turns across *seeds*.

    Returns the per-run results list (before aggregation).
    """
    if scenario_name not in _SCENARIOS:
        raise ValueError(
            f"Unknown scenario {scenario_name!r}. "
            f"Choose from: {sorted(_SCENARIOS)}"
        )
    if n_turns not in _TURN_COUNTS:
        raise ValueError(
            f"n_turns must be one of {sorted(_TURN_COUNTS)}; got {n_turns}."
        )
    seeds = seeds or _DEFAULT_SEEDS
    duration = _TURN_COUNTS[n_turns]
    out_root = Path(output_dir or _DEFAULT_OUTPUT_DIR)
    spec = _SCENARIOS[scenario_name]

    run_dir = out_root / f"{scenario_name}_t{n_turns}"

    config = ExperimentConfig(
        name=f"{scenario_name}_t{n_turns}",
        world_mode=spec["world_mode"],
        controllers=spec["controllers"],
        seeds=seeds,
        duration=duration,
        dt=_DT,
        start_position=list(_START),
        start_velocity=[0.0, 0.0],
        goal_position=list(_GOAL),
        observation_policy=spec["observation_policy"],
        world_params=spec.get("world_params", {}),
        output_dir=str(out_root),
    )
    runner = ExperimentRunner(config)
    if verbose:
        print(f"  Running scenario '{scenario_name}' n_turns={n_turns} seeds={seeds}")
    results = runner.run()
    return results


def run_all_long_horizon(
    turn_counts: Optional[List[int]] = None,
    seeds: Optional[List[int]] = None,
    output_dir: Optional[Path] = None,
    verbose: bool = False,
) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
    """Run all scenarios across all turn counts.

    Returns
    -------
    dict : {scenario_name: {n_turns: [run_results]}}
    """
    turn_counts = turn_counts or list(_TURN_COUNTS)
    all_results: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
    for scenario in _SCENARIOS:
        all_results[scenario] = {}
        for n_turns in turn_counts:
            if verbose:
                print(f"\n[long_horizon] {scenario}  t={n_turns}")
            results = run_scenario(
                scenario_name=scenario,
                n_turns=n_turns,
                seeds=seeds,
                output_dir=output_dir,
                verbose=verbose,
            )
            all_results[scenario][str(n_turns)] = results
    return all_results
