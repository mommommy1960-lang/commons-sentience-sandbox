import math

from scripts.run_auger_ra_harmonic_audit import empirical_upper, harmonic, synthetic_calibration


def test_uniform_circle_has_zero_first_harmonic():
    result = harmonic([i for i in range(360)])
    assert result["n"] == 360
    assert result["amplitude"] < 1e-12


def test_injected_direction_is_detected_by_calibration():
    result = synthetic_calibration()["injected_ra0"]
    assert result["amplitude"] > 0.19
    assert min(result["phase_deg"], 360.0 - result["phase_deg"]) < 1e-10


def test_empirical_upper_uses_add_one_correction():
    assert math.isclose(empirical_upper(0.9, [0.1, 0.2, 0.3]), 0.25)
