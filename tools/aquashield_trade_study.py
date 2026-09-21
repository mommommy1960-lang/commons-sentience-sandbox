#!/usr/bin/env python3
"""Transparent first-order AquaShield calculations. No flight/medical claims."""

from dataclasses import dataclass
from math import pi


@dataclass(frozen=True)
class AquaInputs:
    density_kg_m3: float = 1000.0
    shield_area_m2: float = 10.0
    shield_thickness_m: float = 0.10
    drag_coefficient: float = 1.0
    projected_area_m2: float = 0.10
    water_speed_m_s: float = 0.50
    pressure_rise_pa: float = 40_000.0
    flow_m3_s: float = 0.010
    pump_efficiency: float = 0.60
    cell_volume_m3: float = 0.50
    drain_flow_m3_s: float = 0.025


def calculate(x: AquaInputs) -> dict[str, float]:
    if min(x.density_kg_m3, x.shield_area_m2, x.shield_thickness_m,
           x.projected_area_m2, x.pressure_rise_pa, x.flow_m3_s,
           x.cell_volume_m3, x.drain_flow_m3_s) <= 0:
        raise ValueError("physical dimensions and flows must be positive")
    if not 0 < x.pump_efficiency <= 1:
        raise ValueError("pump efficiency must be in (0, 1]")
    if x.drag_coefficient < 0 or x.water_speed_m_s < 0:
        raise ValueError("drag coefficient and speed cannot be negative")
    return {
        "shield_mass_kg": x.density_kg_m3 * x.shield_area_m2 * x.shield_thickness_m,
        "areal_density_kg_m2": x.density_kg_m3 * x.shield_thickness_m,
        "drag_force_n": 0.5 * x.density_kg_m3 * x.drag_coefficient * x.projected_area_m2 * x.water_speed_m_s**2,
        "hydraulic_power_w": x.pressure_rise_pa * x.flow_m3_s,
        "electrical_power_w": x.pressure_rise_pa * x.flow_m3_s / x.pump_efficiency,
        "drain_time_s": x.cell_volume_m3 / x.drain_flow_m3_s,
    }


def cylindrical_water_mass(radius_m: float, length_m: float, density_kg_m3: float = 1000.0) -> float:
    if min(radius_m, length_m, density_kg_m3) <= 0:
        raise ValueError("radius, length, and density must be positive")
    return pi * radius_m**2 * length_m * density_kg_m3


if __name__ == "__main__":
    for name, value in calculate(AquaInputs()).items():
        print(f"{name}: {value:.6g}")
    print(f"example_full_room_mass_kg: {cylindrical_water_mass(1.5, 3.0):.6g}")

