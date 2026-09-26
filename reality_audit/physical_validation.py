"""Validation experiments for the conservative PhysicalWorld baseline.

These experiments compare the numerical world against analytic constant-gravity
solutions. Their purpose is to measure numerical error before any unusual
behavior is interpreted as physically interesting.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Tuple

from .physical_world import PhysicalBody, PhysicalWorld, PhysicalWorldConfig

Vector3 = Tuple[float, float, float]


def _norm(v: Vector3) -> float:
    return math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)


def _sub(a: Vector3, b: Vector3) -> Vector3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def analytic_constant_acceleration(
    position_m: Vector3,
    velocity_m_s: Vector3,
    acceleration_m_s2: Vector3,
    time_s: float,
) -> tuple[Vector3, Vector3]:
    """Exact kinematic solution for constant acceleration."""

    p = tuple(
        position_m[i]
        + velocity_m_s[i] * time_s
        + 0.5 * acceleration_m_s2[i] * time_s * time_s
        for i in range(3)
    )
    v = tuple(
        velocity_m_s[i] + acceleration_m_s2[i] * time_s
        for i in range(3)
    )
    return p, v


@dataclass(frozen=True)
class IntegratorAuditRow:
    dt_s: float
    steps: int
    position_error_m: float
    velocity_error_m_s: float
    abs_relative_energy_error: float


@dataclass(frozen=True)
class IntegratorConvergenceReport:
    duration_s: float
    rows: tuple[IntegratorAuditRow, ...]
    position_error_monotonic: bool
    energy_error_monotonic: bool
    passed: bool


def mechanical_energy_j(
    mass_kg: float,
    position_m: Vector3,
    velocity_m_s: Vector3,
    gravity_m_s2: Vector3 = (0.0, 0.0, -9.80665),
    reference_z_m: float = 0.0,
) -> float:
    """Kinetic + gravitational potential energy for uniform vertical gravity."""

    speed2 = sum(component * component for component in velocity_m_s)
    kinetic = 0.5 * mass_kg * speed2
    g = _norm(gravity_m_s2)
    potential = mass_kg * g * (position_m[2] - reference_z_m)
    return kinetic + potential


def run_integrator_convergence_audit(
    dts_s: Iterable[float] = (0.1, 0.05, 0.025, 0.0125),
    *,
    duration_s: float = 1.0,
    mass_kg: float = 2.0,
    start_position_m: Vector3 = (0.0, 0.0, 100.0),
    start_velocity_m_s: Vector3 = (1.0, 2.0, 10.0),
    gravity_m_s2: Vector3 = (0.0, 0.0, -9.80665),
) -> IntegratorConvergenceReport:
    """Measure semi-implicit-Euler convergence against an exact gravity solution.

    The test keeps the body far above the ground and disables drag so the
    analytic constant-acceleration solution is the appropriate reference.
    Each dt must divide the requested duration closely enough to avoid comparing
    different final times.
    """

    if duration_s <= 0:
        raise ValueError("duration_s must be > 0")
    if mass_kg <= 0:
        raise ValueError("mass_kg must be > 0")

    rows = []
    exact_position, exact_velocity = analytic_constant_acceleration(
        start_position_m,
        start_velocity_m_s,
        gravity_m_s2,
        duration_s,
    )
    initial_energy = mechanical_energy_j(
        mass_kg,
        start_position_m,
        start_velocity_m_s,
        gravity_m_s2,
    )

    for dt_s in dts_s:
        if dt_s <= 0:
            raise ValueError("all dts_s must be > 0")
        steps = int(round(duration_s / dt_s))
        actual_duration = steps * dt_s
        if not math.isclose(actual_duration, duration_s, rel_tol=0.0, abs_tol=1e-12):
            raise ValueError("each dt_s must divide duration_s exactly within tolerance")

        config = PhysicalWorldConfig(
            dt_s=dt_s,
            gravity_m_s2=gravity_m_s2,
            ground_z_m=-1_000_000.0,
            enable_drag=False,
            ground_friction=0.0,
        )
        world = PhysicalWorld(config)
        body = PhysicalBody(
            mass_kg=mass_kg,
            radius_m=0.0,
            position_m=start_position_m,
            velocity_m_s=start_velocity_m_s,
            restitution=0.0,
        )

        for _ in range(steps):
            world.step(body)

        position_error = _norm(_sub(body.position_m, exact_position))
        velocity_error = _norm(_sub(body.velocity_m_s, exact_velocity))
        final_energy = mechanical_energy_j(
            mass_kg,
            body.position_m,
            body.velocity_m_s,
            gravity_m_s2,
        )
        relative_energy_error = (
            abs(final_energy - initial_energy) / abs(initial_energy)
            if initial_energy != 0.0
            else abs(final_energy - initial_energy)
        )

        rows.append(
            IntegratorAuditRow(
                dt_s=dt_s,
                steps=steps,
                position_error_m=position_error,
                velocity_error_m_s=velocity_error,
                abs_relative_energy_error=relative_energy_error,
            )
        )

    position_monotonic = all(
        rows[i + 1].position_error_m < rows[i].position_error_m
        for i in range(len(rows) - 1)
    )
    energy_monotonic = all(
        rows[i + 1].abs_relative_energy_error < rows[i].abs_relative_energy_error
        for i in range(len(rows) - 1)
    )

    # Constant acceleration makes the velocity update exact to floating-point
    # roundoff. Position and energy errors should decrease as dt is refined.
    velocity_ok = all(row.velocity_error_m_s < 1e-10 for row in rows)

    return IntegratorConvergenceReport(
        duration_s=duration_s,
        rows=tuple(rows),
        position_error_monotonic=position_monotonic,
        energy_error_monotonic=energy_monotonic,
        passed=position_monotonic and energy_monotonic and velocity_ok,
    )
