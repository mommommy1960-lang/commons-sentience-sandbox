import math
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

Vector2 = Tuple[float, float]

class WorldMode(str, Enum):
    CONTINUOUS_BASELINE = "continuous_baseline"
    DISCRETE_GRID = "discrete_grid"
    ANISOTROPIC_PREFERRED_AXIS = "anisotropic_preferred_axis"
    BANDWIDTH_LIMITED = "bandwidth_limited"
    OBSERVER_TRIGGERED_UPDATES = "observer_triggered_updates"
    NOISY_QUANTIZED_MEASUREMENT = "noisy_quantized_measurement"

@dataclass
class WorldConfig:
    mode: WorldMode = WorldMode.CONTINUOUS_BASELINE
    duration: float = 10.0
    dt: float = 0.05
    start_position: Vector2 = (0.0, 0.0)
    start_velocity: Vector2 = (0.0, 0.0)
    max_speed: float = 2.0
    goal_position: Vector2 = (10.0, 0.0)
    params: Dict[str, float] = field(default_factory=dict)
    orientation_rotation: float = 0.0
    seed: Optional[int] = None

@dataclass
class WorldState:
    time: float
    position: Vector2
    velocity: Vector2
    heading: float
    measured_position: Vector2
    measured_velocity: Vector2
    observed: bool
    hidden_state: Dict[str, float]

class RealityWorld:
    def __init__(self, config: WorldConfig):
        self.config = config
        self._rng = random.Random(config.seed)
        self.reset()

    def reset(self) -> None:
        self.time = 0.0
        self.position = tuple(self.config.start_position)
        self.velocity = tuple(self.config.start_velocity)
        self.heading = math.atan2(self.velocity[1], self.velocity[0]) if any(self.velocity) else 0.0
        self.hidden_state = {
            "position": self.position,
            "velocity": self.velocity,
            "heading": self.heading,
        }
        self.last_update_time = 0.0
        self.update_count = 0
        # Stale measurement cache: holds the last observed position/velocity.
        # Used by bandwidth-limited and observer modes to return stale readings
        # when sensing is suppressed.
        self._last_measured_position: Vector2 = self.position
        self._last_measured_velocity: Vector2 = self.velocity

    def step(self, control_input: Vector2, observe: bool = True) -> WorldState:
        dt = self.config.dt
        target_vel = self._clip_vector(control_input, self.config.max_speed)
        self.velocity = self._blend_velocity(self.velocity, target_vel, dt)
        self.position = (
            self.position[0] + self.velocity[0] * dt,
            self.position[1] + self.velocity[1] * dt,
        )
        self.heading = math.atan2(self.velocity[1], self.velocity[0]) if any(self.velocity) else self.heading
        self.time += dt

        if self.config.mode == WorldMode.DISCRETE_GRID:
            self.position = self._apply_grid(self.position)
        elif self.config.mode == WorldMode.ANISOTROPIC_PREFERRED_AXIS:
            self.position = self._apply_anisotropic(self.position)
        elif self.config.mode == WorldMode.BANDWIDTH_LIMITED:
            observe = self._apply_bandwidth_limit(observe)
        elif self.config.mode == WorldMode.OBSERVER_TRIGGERED_UPDATES:
            self._apply_observer_triggered(observe)

        if observe:
            fresh_pos = self._apply_measurement_pipeline(self.position, self.velocity)
            fresh_vel = self._apply_measurement_pipeline(self.velocity, self.velocity)
            self._last_measured_position = fresh_pos
            self._last_measured_velocity = fresh_vel
            self.update_count += 1
            self.last_update_time = self.time

        # Return stale readings when not observing (bandwidth-limited / unobserved steps)
        measured_position = self._last_measured_position
        measured_velocity = self._last_measured_velocity

        state = WorldState(
            time=self.time,
            position=self.position,
            velocity=self.velocity,
            heading=self.heading,
            measured_position=measured_position,
            measured_velocity=measured_velocity,
            observed=observe,
            hidden_state={
                "position": self.hidden_state["position"],
                "velocity": self.hidden_state["velocity"],
                "heading": self.hidden_state["heading"],
            },
        )
        return state

    def _blend_velocity(self, current: Vector2, target: Vector2, dt: float) -> Vector2:
        blend = self.config.params.get("velocity_blend", 0.75)
        return (
            current[0] * (1.0 - blend) + target[0] * blend,
            current[1] * (1.0 - blend) + target[1] * blend,
        )

    def _clip_vector(self, vector: Vector2, max_value: float) -> Vector2:
        magnitude = math.hypot(vector[0], vector[1])
        if magnitude <= max_value or magnitude == 0.0:
            return vector
        scale = max_value / magnitude
        return vector[0] * scale, vector[1] * scale

    def _apply_grid(self, position: Vector2) -> Vector2:
        grid_size = float(self.config.params.get("grid_size", 0.5))
        return (
            round(position[0] / grid_size) * grid_size,
            round(position[1] / grid_size) * grid_size,
        )

    def _apply_anisotropic(self, prev_position: Vector2) -> Vector2:
        """Anisotropic preferred-axis displacement model.

        Stretches the *per-step displacement* along the preferred axis by
        axis_strength, leaving the perpendicular component unscaled.  This
        means equal control effort produces faster motion along the axis —
        as would happen in a medium with direction-dependent resistance.

        Parameters
        ----------
        preferred_axis : float  (world_params key, radians)
            Angle of the preferred axis from the x-axis.  Default 0 (x-axis).
        axis_strength : float  (world_params key)
            Multiplier for displacement along the preferred axis.  Default 1.5.
        """
        axis = float(self.config.params.get("preferred_axis", 0.0))
        factor = float(self.config.params.get("axis_strength", 1.5))
        dt = self.config.dt
        # Displacement this step (before distortion)
        dx = self.velocity[0] * dt
        dy = self.velocity[1] * dt
        # Project displacement onto preferred axis and stretch
        cos_a = math.cos(axis)
        sin_a = math.sin(axis)
        parallel = dx * cos_a + dy * sin_a   # component along preferred axis
        perp_x = dx - parallel * cos_a       # perpendicular remainder
        perp_y = dy - parallel * sin_a
        # Stretched displacement: axis component is amplified, perp unchanged
        stretched_dx = perp_x + parallel * factor * cos_a
        stretched_dy = perp_y + parallel * factor * sin_a
        # Return the position corrected with the stretched displacement
        # (prev_position already has the un-stretched velocity baked in, so we
        #  replace rather than add)
        undisplaced = (prev_position[0] - dx, prev_position[1] - dy)
        return (undisplaced[0] + stretched_dx, undisplaced[1] + stretched_dy)

    def _apply_bandwidth_limit(self, observe: bool) -> bool:
        """Bandwidth-limited sensing model.

        When the time since the last observation is shorter than the minimum
        sensing interval (1 / max_updates_per_second), the sensor is not polled
        this timestep.  The agent continues to receive the STALE measurement
        from the last successful poll rather than a zeroed velocity.
        Physics (position integration) always advances normally.

        Parameters
        ----------
        max_updates_per_second : int  (world_params key)
            Maximum sensor-poll rate.  Default 10 Hz.

        Returns
        -------
        bool
            Whether the sensor was actually read this step.
        """
        max_updates = int(self.config.params.get("max_updates_per_second", 10))
        interval = 1.0 / max_updates if max_updates > 0 else self.config.dt
        if self.time - self.last_update_time < interval:
            return False   # suppress observation; caller returns stale measurement
        return observe     # honour caller's observe flag when interval is met

    def _apply_observer_triggered(self, observe: bool) -> None:
        if observe:
            self.hidden_state["position"] = self.position
            self.hidden_state["velocity"] = self.velocity
            self.hidden_state["heading"] = self.heading
        else:
            decay = float(self.config.params.get("hidden_decay", 0.98))
            self.hidden_state["position"] = (
                self.hidden_state["position"][0] * decay,
                self.hidden_state["position"][1] * decay,
            )
            self.hidden_state["velocity"] = (
                self.hidden_state["velocity"][0] * decay,
                self.hidden_state["velocity"][1] * decay,
            )

    def _apply_measurement_pipeline(self, position: Vector2, velocity: Vector2) -> Vector2:
        noisy = self._apply_noise(position)
        if self.config.mode == WorldMode.NOISY_QUANTIZED_MEASUREMENT:
            quantized = self._apply_quantization(noisy)
            return quantized
        return noisy

    def _apply_noise(self, vector: Vector2) -> Vector2:
        sigma = float(self.config.params.get("measurement_noise", 0.0))
        return (
            vector[0] + self._rng.gauss(0.0, sigma),
            vector[1] + self._rng.gauss(0.0, sigma),
        )

    def _apply_quantization(self, vector: Vector2) -> Vector2:
        step = float(self.config.params.get("quantization_step", 0.25))
        return (self._quantize_value(vector[0], step), self._quantize_value(vector[1], step))

    @staticmethod
    def _quantize_value(value: float, step: float) -> float:
        if step <= 0.0:
            return value
        return round(value / step) * step

    def rotate_vector(self, vector: Vector2, angle: float) -> Vector2:
        cos_theta = math.cos(angle)
        sin_theta = math.sin(angle)
        x, y = vector
        return (x * cos_theta - y * sin_theta, x * sin_theta + y * cos_theta)
