"""Deterministic Newtonian physical-realism baseline for Reality Audit.

This module is deliberately conservative: it implements ordinary classical
mechanics in SI units so that higher-level simulations have a known reality
anchor before speculative or anomaly-seeking modes are exercised.

It is not a precision CFD, FEM, contact-mechanics, or relativistic engine.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Tuple

Vector3 = Tuple[float, float, float]


def _add(a: Vector3, b: Vector3) -> Vector3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _scale(v: Vector3, s: float) -> Vector3:
    return (v[0] * s, v[1] * s, v[2] * s)


def _norm(v: Vector3) -> float:
    return math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)


@dataclass(frozen=True)
class PhysicalWorldConfig:
    """World constants in SI units."""

    dt_s: float = 0.001
    gravity_m_s2: Vector3 = (0.0, 0.0, -9.80665)
    ground_z_m: float = 0.0
    air_density_kg_m3: float = 1.225
    enable_drag: bool = False
    ground_friction: float = 0.7
    rest_speed_threshold_m_s: float = 0.01

    def __post_init__(self) -> None:
        if self.dt_s <= 0:
            raise ValueError("dt_s must be > 0")
        if self.air_density_kg_m3 < 0:
            raise ValueError("air_density_kg_m3 must be >= 0")
        if not 0.0 <= self.ground_friction <= 1.0:
            raise ValueError("ground_friction must be in [0, 1]")
        if self.rest_speed_threshold_m_s < 0:
            raise ValueError("rest_speed_threshold_m_s must be >= 0")


@dataclass
class PhysicalBody:
    """Single rigid-body point-mass approximation with a spherical/area proxy."""

    mass_kg: float
    position_m: Vector3 = (0.0, 0.0, 0.0)
    velocity_m_s: Vector3 = (0.0, 0.0, 0.0)
    radius_m: float = 0.05
    drag_coefficient: float = 0.47
    cross_section_m2: float | None = None
    restitution: float = 0.3

    def __post_init__(self) -> None:
        if self.mass_kg <= 0:
            raise ValueError("mass_kg must be > 0")
        if self.radius_m < 0:
            raise ValueError("radius_m must be >= 0")
        if self.drag_coefficient < 0:
            raise ValueError("drag_coefficient must be >= 0")
        if self.cross_section_m2 is not None and self.cross_section_m2 < 0:
            raise ValueError("cross_section_m2 must be >= 0")
        if not 0.0 <= self.restitution <= 1.0:
            raise ValueError("restitution must be in [0, 1]")

    @property
    def area_m2(self) -> float:
        if self.cross_section_m2 is not None:
            return self.cross_section_m2
        return math.pi * self.radius_m ** 2


@dataclass(frozen=True)
class PhysicsSnapshot:
    time_s: float
    position_m: Vector3
    velocity_m_s: Vector3
    acceleration_m_s2: Vector3
    gravity_force_n: Vector3
    drag_force_n: Vector3
    external_force_n: Vector3
    normal_force_n: Vector3
    net_force_n: Vector3
    kinetic_energy_j: float
    gravitational_potential_energy_j: float
    weight_n: float
    grounded: bool


class PhysicalWorld:
    """Minimal deterministic 3D Newtonian world.

    Integration uses semi-implicit Euler:
      v(t+dt) = v(t) + a(t) dt
      x(t+dt) = x(t) + v(t+dt) dt

    Ground contact is a simple non-penetration constraint with restitution
    and tangential damping. This is suitable for reality-anchor tests, not
    precision contact mechanics.
    """

    def __init__(self, config: PhysicalWorldConfig | None = None):
        self.config = config or PhysicalWorldConfig()
        self.time_s = 0.0

    def gravity_force(self, body: PhysicalBody) -> Vector3:
        return _scale(self.config.gravity_m_s2, body.mass_kg)

    def weight_n(self, body: PhysicalBody) -> float:
        return body.mass_kg * _norm(self.config.gravity_m_s2)

    def drag_force(self, body: PhysicalBody) -> Vector3:
        if not self.config.enable_drag:
            return (0.0, 0.0, 0.0)
        speed = _norm(body.velocity_m_s)
        if speed == 0.0:
            return (0.0, 0.0, 0.0)
        magnitude = (
            0.5
            * self.config.air_density_kg_m3
            * body.drag_coefficient
            * body.area_m2
            * speed
            * speed
        )
        return _scale(body.velocity_m_s, -magnitude / speed)

    def _grounded(self, body: PhysicalBody) -> bool:
        contact_z = self.config.ground_z_m + body.radius_m
        return (
            body.position_m[2] <= contact_z + 1e-12
            and body.velocity_m_s[2] <= 0.0
        )

    def step(
        self,
        body: PhysicalBody,
        external_force_n: Vector3 = (0.0, 0.0, 0.0),
    ) -> PhysicsSnapshot:
        dt = self.config.dt_s
        gravity_force = self.gravity_force(body)
        drag_force = self.drag_force(body)
        raw_force = _add(_add(gravity_force, drag_force), external_force_n)

        grounded_before = self._grounded(body)
        normal_force: Vector3 = (0.0, 0.0, 0.0)

        # A body resting on the ground should not accelerate through the floor.
        if grounded_before and raw_force[2] < 0.0:
            normal_force = (0.0, 0.0, -raw_force[2])

        net_force = _add(raw_force, normal_force)
        acceleration = _scale(net_force, 1.0 / body.mass_kg)

        new_velocity = _add(body.velocity_m_s, _scale(acceleration, dt))
        new_position = _add(body.position_m, _scale(new_velocity, dt))

        contact_z = self.config.ground_z_m + body.radius_m
        grounded_after = False

        if new_position[2] < contact_z:
            new_position = (new_position[0], new_position[1], contact_z)
            if new_velocity[2] < 0.0:
                vz = -new_velocity[2] * body.restitution
                if abs(vz) < self.config.rest_speed_threshold_m_s:
                    vz = 0.0
                tangential_factor = max(0.0, 1.0 - self.config.ground_friction)
                new_velocity = (
                    new_velocity[0] * tangential_factor,
                    new_velocity[1] * tangential_factor,
                    vz,
                )
            grounded_after = True
        elif abs(new_position[2] - contact_z) <= 1e-12 and new_velocity[2] <= 0.0:
            grounded_after = True

        body.position_m = new_position
        body.velocity_m_s = new_velocity
        self.time_s += dt

        speed = _norm(body.velocity_m_s)
        kinetic = 0.5 * body.mass_kg * speed * speed
        height = max(0.0, body.position_m[2] - contact_z)
        potential = self.weight_n(body) * height

        return PhysicsSnapshot(
            time_s=self.time_s,
            position_m=body.position_m,
            velocity_m_s=body.velocity_m_s,
            acceleration_m_s2=acceleration,
            gravity_force_n=gravity_force,
            drag_force_n=drag_force,
            external_force_n=external_force_n,
            normal_force_n=normal_force,
            net_force_n=net_force,
            kinetic_energy_j=kinetic,
            gravitational_potential_energy_j=potential,
            weight_n=self.weight_n(body),
            grounded=grounded_after,
        )

    def simulate(
        self,
        body: PhysicalBody,
        duration_s: float,
        external_force_n: Vector3 = (0.0, 0.0, 0.0),
    ) -> list[PhysicsSnapshot]:
        if duration_s < 0:
            raise ValueError("duration_s must be >= 0")
        steps = int(math.ceil(duration_s / self.config.dt_s))
        return [self.step(body, external_force_n) for _ in range(steps)]


@dataclass(frozen=True)
class AppleThrowResult:
    launch_speed_m_s: float
    simulated_apex_m: float
    analytic_vacuum_apex_m: float
    simulated_flight_time_s: float
    analytic_vacuum_flight_time_s: float
    returned_to_ground: bool


def run_apple_throw_baseline(
    launch_speed_m_s: float = 10.0,
    *,
    mass_kg: float = 0.182,
    radius_m: float = 0.04,
    dt_s: float = 0.0005,
    enable_drag: bool = False,
) -> AppleThrowResult:
    """Canonical 'throw the apple up; it comes back down' reality-anchor test."""

    if launch_speed_m_s <= 0:
        raise ValueError("launch_speed_m_s must be > 0")

    config = PhysicalWorldConfig(dt_s=dt_s, enable_drag=enable_drag)
    world = PhysicalWorld(config)
    body = PhysicalBody(
        mass_kg=mass_kg,
        radius_m=radius_m,
        position_m=(0.0, 0.0, config.ground_z_m + radius_m),
        velocity_m_s=(0.0, 0.0, launch_speed_m_s),
        restitution=0.0,
    )

    gravity = _norm(config.gravity_m_s2)
    analytic_apex = launch_speed_m_s ** 2 / (2.0 * gravity)
    analytic_flight = 2.0 * launch_speed_m_s / gravity

    apex = 0.0
    returned = False
    max_duration = analytic_flight * 2.0 + 1.0

    while world.time_s < max_duration:
        snapshot = world.step(body)
        height = max(0.0, body.position_m[2] - radius_m - config.ground_z_m)
        apex = max(apex, height)
        if world.time_s > dt_s and snapshot.grounded and body.velocity_m_s[2] == 0.0:
            returned = True
            break

    return AppleThrowResult(
        launch_speed_m_s=launch_speed_m_s,
        simulated_apex_m=apex,
        analytic_vacuum_apex_m=analytic_apex,
        simulated_flight_time_s=world.time_s,
        analytic_vacuum_flight_time_s=analytic_flight,
        returned_to_ground=returned,
    )
