"""
tests/test_double_slit.py — Unit tests for the double-slit benchmark module.
"""

from __future__ import annotations

import math
import pytest
from reality_audit.benchmarks.double_slit import (
    SlitCondition,
    _sinc,
    single_slit_intensity,
    two_slit_intensity,
    two_slit_measured_intensity,
    compute_intensity_profile,
    sample_hits,
    run_condition,
    run_all_conditions,
)


class TestSinc:
    def test_at_zero(self):
        assert _sinc(0.0) == 1.0

    def test_at_integer(self):
        # sinc(n) = 0 for non-zero integer n
        for n in [1, 2, 3]:
            assert abs(_sinc(n)) < 1e-10, f"sinc({n}) should be ~0"

    def test_symmetry(self):
        for x in [0.3, 0.7, 1.2]:
            assert pytest.approx(_sinc(x), abs=1e-12) == _sinc(-x)

    def test_positive(self):
        for x in [0.0, 0.5]:
            assert _sinc(x) >= 0


class TestSingleSlitIntensity:
    def test_maximum_at_center(self):
        # y=0 should give I=1.0
        i = single_slit_intensity(0.0, slit_width=1.0, wavelength=1.0, screen_distance=100.0)
        assert pytest.approx(i, abs=1e-6) == 1.0

    def test_symmetry(self):
        y = 5.0
        i1 = single_slit_intensity(y, 1.0, 1.0, 100.0)
        i2 = single_slit_intensity(-y, 1.0, 1.0, 100.0)
        assert pytest.approx(i1, abs=1e-10) == i2

    def test_nonnegative(self):
        for y in [-20, -10, 0, 10, 20]:
            assert single_slit_intensity(y, 1.0, 1.0, 100.0) >= 0


class TestTwoSlitIntensity:
    def test_maximum_at_center(self):
        # At y=0: cos(0)=1, sinc(0)=1 → I=1
        i = two_slit_intensity(0.0, 4.0, 1.0, 1.0, 100.0)
        assert pytest.approx(i, abs=1e-6) == 1.0

    def test_has_fringes(self):
        """Two-slit profile should oscillate (have local minima < max)."""
        positions = [y * 0.1 for y in range(-100, 101)]
        intensities = [two_slit_intensity(y, 4.0, 1.0, 1.0, 100.0) for y in positions]
        assert max(intensities) > 0.9
        assert min(intensities) < max(intensities) * 0.3

    def test_greater_than_measured_at_center(self):
        """Constructive interference: two-slit unmeasured > measured at center."""
        y = 0.0
        i_unmeasured = two_slit_intensity(y, 4.0, 1.0, 1.0, 100.0)
        i_measured = two_slit_measured_intensity(y, 4.0, 1.0, 1.0, 100.0)
        assert i_unmeasured >= i_measured


class TestTwoSlitMeasuredIntensity:
    def test_incoherent_sum(self):
        """Measured = average of two shifted single-slit patterns."""
        d = 4.0
        y = 5.0
        i_meas = two_slit_measured_intensity(y, d, 1.0, 1.0, 100.0)
        i_plus  = single_slit_intensity(y - d/2, 1.0, 1.0, 100.0)
        i_minus = single_slit_intensity(y + d/2, 1.0, 1.0, 100.0)
        assert pytest.approx(i_meas, abs=1e-10) == (i_plus + i_minus) / 2.0

    def test_nonnegative(self):
        for y in [-15, -5, 0, 5, 15]:
            assert two_slit_measured_intensity(y, 4.0, 1.0, 1.0, 100.0) >= 0


class TestComputeIntensityProfile:
    def test_one_slit_profile(self):
        positions = [0.0, 5.0, 10.0]
        result = compute_intensity_profile(
            SlitCondition.ONE_SLIT, positions, 4.0, 1.0, 1.0, 100.0
        )
        assert len(result) == 3
        assert result[0] == pytest.approx(1.0, abs=1e-6)  # center = 1.0

    def test_two_slit_profile_length(self):
        positions = list(range(20))
        result = compute_intensity_profile(
            SlitCondition.TWO_SLIT, positions, 4.0, 1.0, 1.0, 100.0
        )
        assert len(result) == 20

    def test_invalid_condition_raises(self):
        with pytest.raises((ValueError, AttributeError, KeyError)):
            compute_intensity_profile("invalid_cond", [0.0], 4.0, 1.0, 1.0, 100.0)


class TestSampleHits:
    def test_total_hits_approx_n_trials(self):
        intensities = [1.0] * 50
        hits = sample_hits(intensities, n_trials=10_000, seed=42)
        assert abs(sum(hits) - 10_000) <= 1  # multinomial should sum exactly

    def test_deterministic_with_seed(self):
        intensities = [float(i + 1) for i in range(20)]
        h1 = sample_hits(intensities, 5000, seed=7)
        h2 = sample_hits(intensities, 5000, seed=7)
        assert h1 == h2

    def test_different_seeds_differ(self):
        intensities = [1.0] * 10
        h1 = sample_hits(intensities, 1000, seed=0)
        h2 = sample_hits(intensities, 1000, seed=1)
        assert h1 != h2

    def test_zero_intensity(self):
        hits = sample_hits([0.0, 0.0, 0.0], 100, seed=0)
        assert all(h == 0 for h in hits)

    def test_all_hits_in_brightest_bin(self):
        """If one bin dominates, almost all hits should fall there."""
        intensities = [0.0] * 9 + [1000.0]
        hits = sample_hits(intensities, 1000, seed=0)
        assert hits[-1] > 950


class TestRunCondition:
    def test_returns_required_keys(self):
        result = run_condition(SlitCondition.ONE_SLIT, n_trials=100, n_bins=20)
        for key in ["condition", "params", "screen_positions", "intensity_profile",
                    "hit_counts", "n_trials", "seed", "summary"]:
            assert key in result

    def test_screen_positions_length(self):
        result = run_condition(SlitCondition.TWO_SLIT, n_trials=100, n_bins=50)
        assert len(result["screen_positions"]) == 50

    def test_intensity_profile_length(self):
        result = run_condition(SlitCondition.TWO_SLIT, n_trials=100, n_bins=50)
        assert len(result["intensity_profile"]) == 50

    def test_hit_counts_length(self):
        result = run_condition(SlitCondition.TWO_SLIT, n_trials=500, n_bins=30)
        assert len(result["hit_counts"]) == 30

    def test_hit_counts_sum_to_n_trials(self):
        result = run_condition(SlitCondition.TWO_SLIT_MEASURED, n_trials=1000, n_bins=40)
        assert sum(result["hit_counts"]) == 1000

    def test_invalid_n_bins_raises(self):
        with pytest.raises(ValueError):
            run_condition(SlitCondition.ONE_SLIT, n_bins=1)

    def test_two_slit_has_higher_center_intensity_than_measured(self):
        # Use n_bins=101 (odd) so center bin lands exactly at y=0
        r_ts   = run_condition(SlitCondition.TWO_SLIT,          n_trials=1000, n_bins=101, seed=0)
        r_tsm  = run_condition(SlitCondition.TWO_SLIT_MEASURED, n_trials=1000, n_bins=101, seed=0)
        ci_ts  = r_ts["summary"]["center_intensity"]
        ci_tsm = r_tsm["summary"]["center_intensity"]
        assert ci_ts >= ci_tsm, (
            f"Two-slit constructive max ({ci_ts}) should be >= measured ({ci_tsm})"
        )


class TestRunAllConditions:
    def test_returns_all_three_conditions(self):
        results = run_all_conditions(n_trials=200, n_bins=20)
        assert set(results.keys()) == {"one_slit", "two_slit", "two_slit_measured"}

    def test_each_has_required_keys(self):
        results = run_all_conditions(n_trials=200, n_bins=20)
        for cond, result in results.items():
            assert "intensity_profile" in result, f"{cond} missing intensity_profile"
            assert "hit_counts" in result, f"{cond} missing hit_counts"
