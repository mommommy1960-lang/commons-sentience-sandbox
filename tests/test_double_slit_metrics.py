"""
tests/test_double_slit_metrics.py — Tests for double-slit interference metrics.
"""

from __future__ import annotations

import math
import pytest

from reality_audit.analysis.double_slit_metrics import (
    fringe_visibility,
    peak_count,
    center_intensity_normalised,
    distribution_entropy,
    measured_vs_unmeasured_kl,
    one_slit_vs_two_slit_kl,
    fringe_suppression_ratio,
    compute_all_metrics,
    _safe_kl,
)
from reality_audit.benchmarks.double_slit import run_all_conditions


class TestFringeVisibility:
    def test_perfect_visibility(self):
        # max=1, min=0 → visibility = 1
        assert fringe_visibility([1.0, 0.0, 1.0, 0.0]) == pytest.approx(1.0, abs=1e-9)

    def test_zero_visibility_flat(self):
        assert fringe_visibility([0.5, 0.5, 0.5]) == pytest.approx(0.0, abs=1e-9)

    def test_partial_visibility(self):
        # max=0.8, min=0.2 → (0.6)/(1.0) = 0.6
        assert fringe_visibility([0.8, 0.2, 0.8]) == pytest.approx(0.6, abs=1e-9)

    def test_all_zeros(self):
        assert fringe_visibility([0.0, 0.0, 0.0]) == 0.0

    def test_empty(self):
        assert fringe_visibility([]) == 0.0

    def test_single_value(self):
        assert fringe_visibility([0.5]) == pytest.approx(0.0, abs=1e-9)

    def test_two_slit_visibility_large(self):
        """Real two-slit profile should have high visibility."""
        from reality_audit.benchmarks.double_slit import compute_intensity_profile, SlitCondition
        pos = [y * 0.2 for y in range(-100, 101)]
        intensities = compute_intensity_profile(
            SlitCondition.TWO_SLIT, pos, 4.0, 1.0, 1.0, 100.0
        )
        vis = fringe_visibility(intensities)
        assert vis > 0.5, f"Expected high fringe visibility, got {vis}"


class TestPeakCount:
    def test_single_peak(self):
        profile = [0.0, 0.5, 1.0, 0.5, 0.0]
        assert peak_count(profile) == 1

    def test_multiple_peaks(self):
        profile = [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0]
        assert peak_count(profile) == 3

    def test_flat_no_peaks(self):
        assert peak_count([1.0, 1.0, 1.0, 1.0]) == 0

    def test_below_threshold_not_counted(self):
        # max=1.0; values of 0.05 are below 10% threshold
        profile = [0.0, 0.05, 0.0, 1.0, 0.0]  # only the 1.0 is above 10% of 1.0=0.1
        assert peak_count(profile, threshold_fraction=0.1) == 1

    def test_two_slit_has_more_peaks_than_one_slit(self):
        # Use small screen_distance so fringe spacing = λL/d = 1*10/4 = 2.5 units
        # Multiple fringes fit in ±20 screen range
        from reality_audit.benchmarks.double_slit import compute_intensity_profile, SlitCondition
        pos = [y * 0.2 for y in range(-100, 101)]
        screen_distance = 10.0
        i_ts = compute_intensity_profile(SlitCondition.TWO_SLIT, pos, 4.0, 1.0, 1.0, screen_distance)
        i_os = compute_intensity_profile(SlitCondition.ONE_SLIT, pos, 4.0, 1.0, 1.0, screen_distance)
        assert peak_count(i_ts) > peak_count(i_os)


class TestCenterIntensityNormalised:
    def test_center_is_max(self):
        intensities = [0.2, 0.5, 1.0, 0.5, 0.2]
        assert center_intensity_normalised(intensities) == pytest.approx(1.0, abs=1e-6)

    def test_center_not_max(self):
        intensities = [1.0, 0.5, 0.2, 0.5, 1.0]
        assert center_intensity_normalised(intensities) == pytest.approx(0.2, abs=1e-6)

    def test_empty(self):
        assert center_intensity_normalised([]) == 0.0

    def test_all_zero(self):
        assert center_intensity_normalised([0.0, 0.0, 0.0]) == 0.0


class TestDistributionEntropy:
    def test_uniform_max_entropy(self):
        n = 4
        hits = [100] * n
        h = distribution_entropy(hits)
        assert h == pytest.approx(math.log(n), abs=1e-4)

    def test_concentrated_min_entropy(self):
        hits = [0, 0, 1000, 0, 0]
        h = distribution_entropy(hits)
        assert h == pytest.approx(0.0, abs=1e-9)

    def test_all_zero(self):
        assert distribution_entropy([0, 0, 0]) == 0.0

    def test_always_nonnegative(self):
        for hits in [[10, 20, 30], [100], [1, 1, 1, 1]]:
            assert distribution_entropy(hits) >= 0.0


class TestKLDivergence:
    def test_identical_distributions_near_zero(self):
        p = [100.0] * 10
        assert _safe_kl(p, p) < 0.01

    def test_kl_nonnegative(self):
        p = [10.0, 20.0, 30.0, 40.0]
        q = [40.0, 30.0, 20.0, 10.0]
        assert _safe_kl(p, q) >= 0.0

    def test_measured_vs_unmeasured_kl_positive_with_fringes(self):
        results = run_all_conditions(n_trials=10_000, n_bins=100, seed=42)
        kl = measured_vs_unmeasured_kl(
            results["two_slit"]["hit_counts"],
            results["two_slit_measured"]["hit_counts"],
        )
        assert kl > 0.0

    def test_one_slit_vs_two_slit_kl_positive(self):
        results = run_all_conditions(n_trials=10_000, n_bins=100, seed=42)
        kl = one_slit_vs_two_slit_kl(
            results["two_slit"]["hit_counts"],
            results["one_slit"]["hit_counts"],
        )
        assert kl > 0.0


class TestFringeSuppression:
    def test_full_suppression(self):
        assert fringe_suppression_ratio(0.8, 0.0) == pytest.approx(0.0, abs=1e-9)

    def test_no_suppression(self):
        assert fringe_suppression_ratio(0.8, 0.8) == pytest.approx(1.0, abs=1e-9)

    def test_partial_suppression(self):
        ratio = fringe_suppression_ratio(0.8, 0.4)
        assert pytest.approx(ratio, abs=1e-6) == 0.5

    def test_zero_baseline_returns_one(self):
        # undefined ratio → returns 1.0 (no baseline fringes)
        assert fringe_suppression_ratio(0.0, 0.5) == 1.0


class TestComputeAllMetrics:
    def test_returns_required_structure(self):
        results = run_all_conditions(n_trials=2000, n_bins=100, seed=0)
        metrics = compute_all_metrics(results)
        assert "per_condition" in metrics
        assert "cross_condition" in metrics
        assert "interpretation" in metrics

    def test_all_conditions_have_metrics(self):
        results = run_all_conditions(n_trials=2000, n_bins=100, seed=0)
        metrics = compute_all_metrics(results)
        for cond in ["one_slit", "two_slit", "two_slit_measured"]:
            assert cond in metrics["per_condition"]
            pc = metrics["per_condition"][cond]
            assert "fringe_visibility" in pc
            assert "peak_count" in pc
            assert "center_intensity_normalised" in pc
            assert "distribution_entropy" in pc

    def test_two_slit_higher_visibility_than_measured(self):
        results = run_all_conditions(n_trials=5000, n_bins=100, seed=0)
        metrics = compute_all_metrics(results)
        vis_ts  = metrics["per_condition"]["two_slit"]["fringe_visibility"]
        vis_tsm = metrics["per_condition"]["two_slit_measured"]["fringe_visibility"]
        assert vis_ts > vis_tsm, f"Expected ts visibility ({vis_ts}) > measured ({vis_tsm})"

    def test_verdict_correct_benchmark(self):
        results = run_all_conditions(n_trials=20_000, n_bins=100, seed=0)
        metrics = compute_all_metrics(results)
        verdict = metrics["cross_condition"]["verdict"]
        assert "BENCHMARK_BEHAVED_CORRECTLY" in verdict or "interference present" in verdict

    def test_cross_condition_keys_present(self):
        results = run_all_conditions(n_trials=2000, n_bins=100, seed=0)
        metrics = compute_all_metrics(results)
        cross = metrics["cross_condition"]
        assert "measured_vs_unmeasured_kl" in cross
        assert "fringe_suppression_ratio" in cross
        assert "one_slit_vs_two_slit_kl" in cross
        assert "visibility_drop" in cross
