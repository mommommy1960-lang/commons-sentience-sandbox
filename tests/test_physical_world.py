import math
import random

from reality_audit.physical_world import (
    PhysicalBody,
    PhysicalWorld,
    PhysicalWorldConfig,
    run_apple_throw_baseline,
)


def test_weight_is_mass_times_g():
    world = PhysicalWorld(PhysicalWorldConfig())
    body = PhysicalBody(mass_kg=2.5, radius_m=0.0)
    assert math.isclose(world.weight_n(body), 2.5 * 9.80665, rel_tol=1e-12)


def test_free_fall_acceleration_is_mass_independent_without_drag():
    config = PhysicalWorldConfig(dt_s=0.001, enable_drag=False)
    light = PhysicalBody(mass_kg=0.1, radius_m=0.0, position_m=(0.0, 0.0, 100.0))
    heavy = PhysicalBody(mass_kg=100.0, radius_m=0.0, position_m=(0.0, 0.0, 100.0))
    light_snapshot = PhysicalWorld(config).step(light)
    heavy_snapshot = PhysicalWorld(config).step(heavy)
    assert math.isclose(light_snapshot.acceleration_m_s2[2], -9.80665, rel_tol=1e-12)
    assert math.isclose(heavy_snapshot.acceleration_m_s2[2], -9.80665, rel_tol=1e-12)


def test_force_equals_mass_times_acceleration_when_gravity_is_zero():
    config = PhysicalWorldConfig(dt_s=0.01, gravity_m_s2=(0.0, 0.0, 0.0))
    body = PhysicalBody(mass_kg=4.0, radius_m=0.0, position_m=(0.0, 0.0, 10.0))
    snapshot = PhysicalWorld(config).step(body, external_force_n=(8.0, 0.0, 0.0))
    assert math.isclose(snapshot.acceleration_m_s2[0], 2.0, rel_tol=1e-12)


def test_ground_supports_resting_body():
    config = PhysicalWorldConfig(dt_s=0.01)
    body = PhysicalBody(mass_kg=1.0, radius_m=0.1, position_m=(0.0, 0.0, 0.1))
    snapshot = PhysicalWorld(config).step(body)
    assert snapshot.position_m[2] >= 0.1
    assert snapshot.velocity_m_s[2] == 0.0
    assert math.isclose(snapshot.normal_force_n[2], 9.80665, rel_tol=1e-12)


def test_apple_goes_up_and_comes_back_down():
    result = run_apple_throw_baseline(10.0, enable_drag=False)
    assert result.returned_to_ground
    assert abs(result.simulated_apex_m - result.analytic_vacuum_apex_m) < 0.01
    assert abs(result.simulated_flight_time_s - result.analytic_vacuum_flight_time_s) < 0.01


def test_drag_reduces_apple_apex():
    vacuum = run_apple_throw_baseline(10.0, enable_drag=False)
    air = run_apple_throw_baseline(10.0, enable_drag=True)
    assert air.simulated_apex_m < vacuum.simulated_apex_m


def test_one_hundred_random_force_mass_cases_obey_f_equals_ma():
    rng = random.Random(20260910)
    config = PhysicalWorldConfig(
        dt_s=0.001,
        gravity_m_s2=(0.0, 0.0, 0.0),
        enable_drag=False,
    )

    for _ in range(100):
        mass = rng.uniform(0.01, 1000.0)
        force = tuple(rng.uniform(-500.0, 500.0) for _ in range(3))
        body = PhysicalBody(mass_kg=mass, radius_m=0.0, position_m=(0.0, 0.0, 100.0))
        snapshot = PhysicalWorld(config).step(body, external_force_n=force)

        for index in range(3):
            assert math.isclose(
                snapshot.acceleration_m_s2[index],
                force[index] / mass,
                rel_tol=1e-12,
                abs_tol=1e-12,
            )
