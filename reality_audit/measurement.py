import math
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

Vector2 = Tuple[float, float]

@dataclass
class MetricResult:
    metrics: Dict[str, float]

class MeasurementSuite:
    @staticmethod
    def position_error(path: Iterable[Dict], target: Vector2) -> float:
        errors = [MeasurementSuite._distance(entry["measured_position"], target) for entry in path]
        return float(sum(errors) / len(errors)) if errors else 0.0

    @staticmethod
    def velocity_error(path: Iterable[Dict], target_velocity: Vector2) -> float:
        errors = [MeasurementSuite._distance(entry["measured_velocity"], target_velocity) for entry in path]
        return float(sum(errors) / len(errors)) if errors else 0.0

    @staticmethod
    def directional_error(path: Iterable[Dict], heading: float) -> float:
        errors = [abs(MeasurementSuite._angle_difference(entry.get("heading", 0.0), heading)) for entry in path]
        return float(sum(errors) / len(errors)) if errors else 0.0

    @staticmethod
    def steady_state_error(path: Iterable[Dict], target: Vector2) -> float:
        return MeasurementSuite.position_error([path[-1]] if path else [], target)

    @staticmethod
    def overshoot(path: Iterable[Dict], target: Vector2) -> float:
        if not path:
            return 0.0
        baseline = MeasurementSuite._distance(path[0]["measured_position"], target)
        maximum = max(MeasurementSuite._distance(entry["measured_position"], target) for entry in path)
        return max(0.0, maximum - baseline)

    @staticmethod
    def convergence_time(path: Iterable[Dict], target: Vector2, tolerance: float = 0.2) -> float:
        cumulative = 0.0
        for entry in path:
            if MeasurementSuite._distance(entry["measured_position"], target) <= tolerance:
                return entry["time"]
        return float(path[-1]["time"] if path else 0.0)

    @staticmethod
    def stability_score(path: Iterable[Dict], target: Vector2) -> float:
        errors = [MeasurementSuite._distance(entry["measured_position"], target) for entry in path]
        if not errors:
            return 0.0
        mean_error = sum(errors) / len(errors)
        variance = sum((error - mean_error) ** 2 for error in errors) / len(errors)
        return float(1.0 / (1.0 + variance))

    @staticmethod
    def control_effort(path: Iterable[Dict]) -> float:
        efforts = [math.hypot(*entry.get("control_input", (0.0, 0.0))) for entry in path]
        return float(sum(efforts))

    @staticmethod
    def path_smoothness(path: Iterable[Dict]) -> float:
        velocities = [entry["measured_velocity"] for entry in path]
        if len(velocities) < 2:
            return 0.0
        jerk = 0.0
        for prev, current in zip(velocities, velocities[1:]):
            jerk += (current[0] - prev[0]) ** 2 + (current[1] - prev[1]) ** 2
        return float(jerk)

    @staticmethod
    def anisotropy_score(path: Iterable[Dict]) -> float:
        axes = [(abs(entry["measured_position"][0]), abs(entry["measured_position"][1])) for entry in path]
        if not axes:
            return 0.0
        x_sum = sum(x for x, _ in axes)
        y_sum = sum(y for _, y in axes)
        if y_sum == 0.0:
            return float(x_sum)
        return float(abs(x_sum - y_sum) / max(x_sum, y_sum))

    @staticmethod
    def quantization_artifact_score(path: Iterable[Dict]) -> float:
        repeated = 0
        last = None
        for entry in path:
            sample = entry["measured_position"]
            if sample == last:
                repeated += 1
            last = sample
        return float(repeated)

    @staticmethod
    def bandwidth_bottleneck_score(path: Iterable[Dict], expected_updates: int) -> float:
        actual_updates = sum(1 for entry in path if entry.get("observed", True))
        return float(actual_updates) / float(expected_updates) if expected_updates > 0 else 0.0

    @staticmethod
    def observer_dependence_score(path: Iterable[Dict]) -> float:
        hidden_diffs = [abs(entry.get("hidden_state", {}).get("position", (0.0, 0.0))[0] - entry["measured_position"][0])
                        + abs(entry.get("hidden_state", {}).get("position", (0.0, 0.0))[1] - entry["measured_position"][1])
                        for entry in path]
        return float(sum(hidden_diffs) / len(hidden_diffs)) if hidden_diffs else 0.0

    @staticmethod
    def _distance(a: Vector2, b: Vector2) -> float:
        return math.hypot(a[0] - b[0], a[1] - b[1])

    @staticmethod
    def _angle_difference(a: float, b: float) -> float:
        diff = abs((a - b + math.pi) % (2 * math.pi) - math.pi)
        return diff
