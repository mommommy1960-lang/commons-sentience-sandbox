"""Null / baseline agents for the Reality Audit framework.

These agents operate on the ``RealityWorld`` (continuous physics world) to
establish what audit metrics look like under essentially random or uniform
behaviour — i.e. "what noise looks like."

They are *not* replacements for the full sandbox agents.  They exist solely
to generate baseline audit metric values against which sandbox experiment
results can be compared.

Two baselines are provided:

``random_walk``
    At each step the control input is sampled uniformly from [-max_speed,
    max_speed] on each axis.  There is no goal-directed learning.

``uniform_policy``
    The control input is always the same unit vector pointing toward the
    goal position, scaled to 50% of max_speed.  This is a "dumb" but not
    entirely random policy that always points the right way but never
    corrects for overshoot.

Both are run through the standard ``ExperimentRunner`` pipeline so the
output format is identical to all other experiments.
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from reality_audit.controller import ControllerInterface
from reality_audit.experiment import ExperimentConfig, ExperimentRunner

# ---------------------------------------------------------------------------
# Baseline controller implementations
# ---------------------------------------------------------------------------

class _RandomWalkController(ControllerInterface):
    """Control input is uniform random in [-max_speed, max_speed]^2."""

    def __init__(self, max_speed: float = 2.0, seed: Optional[int] = None):
        self._max = max_speed
        self._rng = random.Random(seed)

    def reset(self) -> None:
        pass  # stateless

    def update(
        self,
        setpoint: Tuple[float, float],
        measurement: Tuple[float, float],
        dt: float,
    ) -> Tuple[float, float]:
        return (
            self._rng.uniform(-self._max, self._max),
            self._rng.uniform(-self._max, self._max),
        )


class _UniformPolicyController(ControllerInterface):
    """Always outputs a half-speed unit vector toward the goal."""

    def __init__(self, max_speed: float = 2.0):
        self._speed = max_speed * 0.5

    def reset(self) -> None:
        pass  # stateless

    def update(
        self,
        setpoint: Tuple[float, float],
        measurement: Tuple[float, float],
        dt: float,
    ) -> Tuple[float, float]:
        dx = setpoint[0] - measurement[0]
        dy = setpoint[1] - measurement[1]
        dist = math.hypot(dx, dy)
        if dist < 1e-9:
            return (0.0, 0.0)
        scale = self._speed / dist
        return (dx * scale, dy * scale)


# ---------------------------------------------------------------------------
# Register the baseline controllers so ExperimentRunner can find them
# ---------------------------------------------------------------------------

from reality_audit.controller import CONTROLLER_TYPES  # noqa: E402

CONTROLLER_TYPES["random_walk"] = _RandomWalkController
CONTROLLER_TYPES["uniform_policy"] = _UniformPolicyController

# ---------------------------------------------------------------------------
# Baseline runner
# ---------------------------------------------------------------------------

_BASELINE_DURATION = 10.0
_BASELINE_DT = 0.1
_BASELINE_GOAL = [10.0, 0.0]
_BASELINE_START = [0.0, 0.0]
_BASELINE_SEED = 42
_OUTPUT_ROOT = "outputs/baselines"


def run_random_walk_baseline(
    output_dir: str = _OUTPUT_ROOT,
    verbose: bool = False,
) -> Dict[str, Any]:
    """Run a random-walk null baseline and return the metrics dict."""
    config = ExperimentConfig(
        name="baseline_random_walk",
        world_mode="continuous_baseline",
        controllers=["random_walk"],
        seeds=[_BASELINE_SEED],
        duration=_BASELINE_DURATION,
        dt=_BASELINE_DT,
        start_position=_BASELINE_START,
        goal_position=_BASELINE_GOAL,
        observation_policy="always_observe",
        output_dir=output_dir,
    )
    runner = ExperimentRunner(config)
    results = runner.run()
    metrics = results[0]["metrics"]

    # Write a dedicated summary file expected by tests / consumers
    out_path = Path(output_dir) / "baseline_random_walk_summary.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    if verbose:
        print("\n── Random-walk baseline ──")
        for k, v in metrics.items():
            print(f"  {k:<35} {v:.4f}")
        print(f"  Summary → {out_path}")

    return metrics


def run_uniform_policy_baseline(
    output_dir: str = _OUTPUT_ROOT,
    verbose: bool = False,
) -> Dict[str, Any]:
    """Run a uniform-policy null baseline and return the metrics dict."""
    config = ExperimentConfig(
        name="baseline_uniform_policy",
        world_mode="continuous_baseline",
        controllers=["uniform_policy"],
        seeds=[_BASELINE_SEED],
        duration=_BASELINE_DURATION,
        dt=_BASELINE_DT,
        start_position=_BASELINE_START,
        goal_position=_BASELINE_GOAL,
        observation_policy="always_observe",
        output_dir=output_dir,
    )
    runner = ExperimentRunner(config)
    results = runner.run()
    metrics = results[0]["metrics"]

    out_path = Path(output_dir) / "baseline_uniform_policy_summary.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    if verbose:
        print("\n── Uniform-policy baseline ──")
        for k, v in metrics.items():
            print(f"  {k:<35} {v:.4f}")
        print(f"  Summary → {out_path}")

    return metrics


def run_all_baselines(
    output_dir: str = _OUTPUT_ROOT,
    verbose: bool = False,
) -> Dict[str, Dict[str, Any]]:
    """Run both baselines and return results dict."""
    return {
        "random_walk": run_random_walk_baseline(output_dir=output_dir, verbose=verbose),
        "uniform_policy": run_uniform_policy_baseline(output_dir=output_dir, verbose=verbose),
    }


if __name__ == "__main__":
    run_all_baselines(verbose=True)
