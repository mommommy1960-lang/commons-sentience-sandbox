import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

try:
    import yaml
except ImportError:
    yaml = None

from .controller import CONTROLLER_TYPES, ControllerInterface
from .logger import ExperimentLogger
from .measurement import MeasurementSuite
from .world import RealityWorld, WorldConfig, WorldMode

@dataclass
class ExperimentConfig:
    name: str = "reality_audit"
    world_mode: str = WorldMode.CONTINUOUS_BASELINE.value
    controllers: List[str] = field(default_factory=lambda: ["proportional"])
    seeds: List[int] = field(default_factory=lambda: [0])
    duration: float = 10.0
    dt: float = 0.05
    start_position: List[float] = field(default_factory=lambda: [0.0, 0.0])
    start_velocity: List[float] = field(default_factory=lambda: [0.0, 0.0])
    goal_position: List[float] = field(default_factory=lambda: [10.0, 0.0])
    controller_params: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    world_params: Dict[str, Any] = field(default_factory=dict)
    orientation_rotations: List[float] = field(default_factory=lambda: [0.0])
    output_dir: str = "outputs"
    # Observation policy: "always_observe", "never_observe", or "periodic_observe"
    # periodic_observe requires world_params["observe_period"] (timesteps between observations)
    observation_policy: str = "always_observe"
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path) -> "ExperimentConfig":
        raw = path.read_text(encoding="utf-8")
        if path.suffix.lower() in {".yaml", ".yml"}:
            if yaml is None:
                raise RuntimeError("PyYAML is required to load YAML experiment definitions.")
            data = yaml.safe_load(raw)
        else:
            data = json.loads(raw)
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class ExperimentRunner:
    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.output_path = Path(config.output_dir) / config.name
        self.logger = ExperimentLogger(self.output_path)

    def run(self) -> List[Dict[str, Any]]:
        self.logger.write_config(self.config.to_dict())
        results = []
        for controller_name in self.config.controllers:
            for seed in self.config.seeds:
                for orientation in self.config.orientation_rotations:
                    run_result = self._run_single(controller_name, seed, orientation)
                    run_dir = self.output_path / run_result["run_id"]
                    print(f"  [run] {run_result['run_id']}  →  {run_dir}")
                    results.append(run_result)
        summary = {
            "experiment_name": self.config.name,
            "run_count": len(results),
            "results": results,
        }
        self.logger.write_summary(summary)
        return results

    def _run_single(self, controller_name: str, seed: int, orientation: float) -> Dict[str, Any]:
        if controller_name not in CONTROLLER_TYPES:
            raise ValueError(f"Unknown controller type: {controller_name}")
        controller: ControllerInterface = CONTROLLER_TYPES[controller_name](**self.config.controller_params.get(controller_name, {}))
        controller.reset()

        mode = WorldMode(self.config.world_mode)
        world_config = WorldConfig(
            mode=mode,
            duration=self.config.duration,
            dt=self.config.dt,
            start_position=self._rotate_vector(tuple(self.config.start_position), orientation),
            start_velocity=tuple(self.config.start_velocity),
            max_speed=float(self.config.world_params.get("max_speed", 2.0)),
            goal_position=self._rotate_vector(tuple(self.config.goal_position), orientation),
            params=self.config.world_params,
            orientation_rotation=orientation,
            seed=seed,
        )
        world = RealityWorld(world_config)
        raw_log = []
        expected_updates = int(math.ceil(self.config.duration / self.config.dt))

        rotated_goal = self._rotate_vector(tuple(self.config.goal_position), orientation)

        for step_index in range(expected_updates):
            # Setpoint uses the same rotated goal that the world was constructed with
            setpoint = rotated_goal
            observe = self._should_observe(step_index)
            measurement = world.position if step_index == 0 else raw_log[-1]["measured_position"]
            control_input = controller.update(setpoint, measurement, self.config.dt)
            state = world.step(control_input, observe=observe)
            raw_log.append({
                "time": state.time,
                "position": state.position,
                "measured_position": state.measured_position,
                "velocity": state.velocity,
                "measured_velocity": state.measured_velocity,
                "heading": state.heading,
                "observed": state.observed,
                "hidden_state": state.hidden_state,
                "control_input": control_input,
                "seed": seed,
                "controller": controller_name,
                "world_mode": mode.value,
                "orientation": orientation,
            })

        metrics = self._collect_metrics(raw_log, rotated_goal)
        run_id = f"{controller_name}_seed{seed}_rot{orientation:.2f}"
        run_dir = self.output_path / run_id
        logger = ExperimentLogger(run_dir)
        logger.write_config({"run_id": run_id, **self.config.to_dict()})
        logger.write_raw_log(raw_log)
        logger.write_csv(raw_log)
        logger.write_summary(metrics)

        return {
            "run_id": run_id,
            "controller": controller_name,
            "seed": seed,
            "orientation": orientation,
            "world_mode": mode.value,
            "metrics": metrics,
        }

    def _should_observe(self, step_index: int) -> bool:
        policy = self.config.observation_policy
        if policy == "never_observe":
            return False
        if policy == "periodic_observe":
            period = int(self.config.world_params.get("observe_period", 5))
            return (step_index % period) == 0
        # default: always_observe
        return True

    def _collect_metrics(self, raw_log: List[Dict[str, Any]], rotated_goal: tuple) -> Dict[str, Any]:
        target = rotated_goal
        expected_updates = int(math.ceil(self.config.duration / self.config.dt))
        metrics = {
            "position_error": MeasurementSuite.position_error(raw_log, target),
            "velocity_error": MeasurementSuite.velocity_error(raw_log, (0.0, 0.0)),
            "directional_error": MeasurementSuite.directional_error(raw_log, 0.0),
            "steady_state_error": MeasurementSuite.steady_state_error(raw_log, target),
            "overshoot": MeasurementSuite.overshoot(raw_log, target),
            "convergence_time": MeasurementSuite.convergence_time(raw_log, target),
            "stability_score": MeasurementSuite.stability_score(raw_log, target),
            "control_effort": MeasurementSuite.control_effort(raw_log),
            "path_smoothness": MeasurementSuite.path_smoothness(raw_log),
            "anisotropy_score": MeasurementSuite.anisotropy_score(raw_log),
            "quantization_artifact_score": MeasurementSuite.quantization_artifact_score(raw_log),
            "bandwidth_bottleneck_score": MeasurementSuite.bandwidth_bottleneck_score(raw_log, expected_updates),
            "observer_dependence_score": MeasurementSuite.observer_dependence_score(raw_log),
        }
        return metrics

    @staticmethod
    def _rotate_vector(vector: tuple[float, float], angle: float) -> tuple[float, float]:
        import math

        cos_theta = math.cos(angle)
        sin_theta = math.sin(angle)
        x, y = vector
        return (x * cos_theta - y * sin_theta, x * sin_theta + y * cos_theta)
