import math
import random

from reality_audit.physical_validation import (
    analytic_constant_acceleration,
    run_integrator_convergence_audit,
)
from reality_audit.physical_world import PhysicalBody, PhysicalWorld, PhysicalWorldConfig


def test_integrator_converges_toward_analytic_constant_gravity_solution():
    report = run_integrator_convergence_audit()
    assert report.passed
    assert report.position_error_monotonic
    assert report.energy_error_monotonic


def test_halving_dt_approximately_halves_position_error_for_current_integrator():
    report = run_integrator_convergence_audit(dts_s=(0.1, 0.05, 0.025, 0.0125))
    errors = [row.position_error_m for row in report.rows]
    ratios = [errors[i] / errors[i + 1] for i in range(len(errors) - 1)]
    for ratio in ratios:
        assert 1.95 < ratio < 2.05


def test_constant_gravity_velocity_matches_analytic_solution():
    report = run_integrator_convergence_audit()
    assert max(row.velocity_error_m_s for row in report.rows) < 1e-10


def test_analytic_solution_matches_expected_vertical_formula():
    position, velocity = analytic_constant_acceleration(
        (0.0, 0.0, 0.0),
        (0.0, 0.0, 10.0),
        (0.0, 0.0, -9.80665),
        1.0,
    )
    assert math.isclose(position[2], 10.0 - 0.5 * 9.80665, rel_tol=1e-12)
    assert math.isclose(velocity[2], 10.0 - 9.80665, rel_tol=1e-12)


def test_one_hundred_random_ballistic_cases_track_analytic_solution_with_bounded_error():
    rng = random.Random(20260910)
    gravity = (0.0, 0.0, -9.80665)
    dt_s = 0.001
    duration_s = 0.5
    steps = int(duration_s / dt_s)

    for _ in range(100):
        mass = rng.uniform(0.01, 1000.0)
        start_position = (
            rng.uniform(-100.0, 100.0),
            rng.uniform(-100.0, 100.0),
            rng.uniform(100.0, 1000.0),
        )
        start_velocity = tuple(rng.uniform(-50.0, 50.0) for _ in range(3))
        expected_position, expected_velocity = analytic_constant_acceleration(
            start_position,
            start_velocity,
            gravity,
            duration_s,
        )

        world = PhysicalWorld(
            PhysicalWorldConfig(
                dt_s=dt_s,
                gravity_m_s2=gravity,
                ground_z_m=-1_000_000.0,
                enable_drag=False,
                ground_friction=0.0,
            )
        )
        body = PhysicalBody(
            mass_kg=mass,
            radius_m=0.0,
            position_m=start_position,
            velocity_m_s=start_velocity,
        )
        for _ in range(steps):
            world.step(body)

        position_error = math.dist(body.position_m, expected_position)
        velocity_error = math.dist(body.velocity_m_s, expected_velocity)

        # Semi-implicit Euler under constant acceleration has first-order
        # position error ≈ 0.5 * |g| * T * dt for this vertical case.
        expected_bound = 0.5 * 9.80665 * duration_s * dt_s * 1.01
        assert position_error <= expected_bound
        assert velocity_error < 1e-9
