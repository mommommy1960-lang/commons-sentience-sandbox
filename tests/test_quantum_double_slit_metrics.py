"""Tests for quantum_double_slit_metrics.py."""

import pytest
from reality_audit.analysis.quantum_double_slit_metrics import (
    fringe_visibility,
    peak_count,
    center_intensity_normalised,
    distribution_entropy,
    coherence_sensitivity,
    partial_decoherence_monotonicity,
    visibility_at_gamma,
    compute_quantum_metrics,
)
from reality_audit.benchmarks.quantum_double_slit import run_all_conditions


# ---------------------------------------------------------------------------
# fringe_visibility
# ---------------------------------------------------------------------------

class TestFringeVisibility:
    def test_uniform_is_zero(self):
        assert fringe_visibility([0.5, 0.5, 0.5]) == 0.0

    def test_perfect_is_one(self):
        assert fringe_visibility([1.0, 0.0]) == pytest.approx(1.0)

    def test_empty_returns_zero(self):
        assert fringe_visibility([]) == 0.0

    def test_all_zero_returns_zero(self):
        assert fringe_visibility([0.0, 0.0]) == 0.0

    def test_known_value(self):
        # max=0.8, min=0.2 → (0.6/1.0)=0.6
        assert fringe_visibility([0.8, 0.2, 0.5]) == pytest.approx(0.6)


# ---------------------------------------------------------------------------
# peak_count
# ---------------------------------------------------------------------------

class TestPeakCount:
    def test_single_peak(self):
        probs = [0.0, 0.5, 1.0, 0.5, 0.0]
        assert peak_count(probs) == 1

    def test_two_peaks(self):
        probs = [0.1, 0.9, 0.1, 0.9, 0.1]
        assert peak_count(probs) == 2

    def test_too_short_returns_zero(self):
        assert peak_count([1.0]) == 0
        assert peak_count([1.0, 0.5]) == 0

    def test_flat_returns_zero(self):
        assert peak_count([0.5, 0.5, 0.5, 0.5]) == 0


# ---------------------------------------------------------------------------
# center_intensity_normalised
# ---------------------------------------------------------------------------

class TestCentreIntensity:
    def test_maximum_centre_returns_one(self):
        probs = [0.1, 0.2, 1.0, 0.2, 0.1]
        assert center_intensity_normalised(probs) == pytest.approx(1.0)

    def test_zero_max_returns_zero(self):
        assert center_intensity_normalised([0.0, 0.0]) == 0.0

    def test_empty_returns_zero(self):
        assert center_intensity_normalised([]) == 0.0


# ---------------------------------------------------------------------------
# distribution_entropy
# ---------------------------------------------------------------------------

class TestDistributionEntropy:
    def test_uniform_higher_than_concentrated(self):
        uniform = [1] * 100
        concentrated = [0] * 99 + [100]
        assert distribution_entropy(uniform) > distribution_entropy(concentrated)

    def test_all_zero_returns_zero(self):
        assert distribution_entropy([0, 0, 0]) == 0.0

    def test_total_zero_returns_zero(self):
        assert distribution_entropy([]) == 0.0


# ---------------------------------------------------------------------------
# coherence_sensitivity
# ---------------------------------------------------------------------------

class TestCoherenceSensitivity:
    def _make_sweep(self, gammas, visibilities):
        return [
            {"decoherence_gamma": g, "summary": {"fringe_visibility": v}}
            for g, v in zip(gammas, visibilities)
        ]

    def test_negative_slope_for_decreasing_visibility(self):
        sweep = self._make_sweep([0.0, 0.5, 1.0], [1.0, 0.5, 0.0])
        slope = coherence_sensitivity(sweep)
        assert slope < 0.0

    def test_zero_for_constant_visibility(self):
        sweep = self._make_sweep([0.0, 0.5, 1.0], [0.7, 0.7, 0.7])
        slope = coherence_sensitivity(sweep)
        assert abs(slope) < 1e-10

    def test_single_entry_returns_zero(self):
        sweep = self._make_sweep([0.0], [1.0])
        assert coherence_sensitivity(sweep) == 0.0


# ---------------------------------------------------------------------------
# partial_decoherence_monotonicity
# ---------------------------------------------------------------------------

class TestMonotonicity:
    def _make_sweep(self, gammas, visibilities):
        return [
            {"decoherence_gamma": g, "summary": {"fringe_visibility": v}}
            for g, v in zip(gammas, visibilities)
        ]

    def test_strictly_decreasing_is_monotone(self):
        sweep = self._make_sweep([0.0, 0.5, 1.0], [1.0, 0.5, 0.0])
        assert partial_decoherence_monotonicity(sweep) is True

    def test_increasing_is_not_monotone(self):
        sweep = self._make_sweep([0.0, 0.5, 1.0], [0.1, 0.9, 0.2])
        assert partial_decoherence_monotonicity(sweep) is False

    def test_empty_is_trivially_monotone(self):
        assert partial_decoherence_monotonicity([]) is True


# ---------------------------------------------------------------------------
# visibility_at_gamma
# ---------------------------------------------------------------------------

class TestVisibilityAtGamma:
    def _make_sweep(self, gammas, visibilities):
        return [
            {"decoherence_gamma": g, "summary": {"fringe_visibility": v}}
            for g, v in zip(gammas, visibilities)
        ]

    def test_exact_match(self):
        sweep = self._make_sweep([0.0, 1.0], [0.9, 0.1])
        assert visibility_at_gamma(sweep, 0.0) == pytest.approx(0.9)

    def test_closest_gamma(self):
        sweep = self._make_sweep([0.0, 0.5, 1.0], [1.0, 0.5, 0.0])
        assert visibility_at_gamma(sweep, 0.4) == pytest.approx(0.5)

    def test_empty_returns_none(self):
        assert visibility_at_gamma([], 0.5) is None


# ---------------------------------------------------------------------------
# compute_quantum_metrics (integration)
# ---------------------------------------------------------------------------

class TestComputeQuantumMetrics:
    @pytest.fixture(scope="class")
    def metrics(self):
        results = run_all_conditions(
            n_trials=500, n_bins=40, seed=0, screen_width=20.0,
            slit_separation=4.0, slit_width=1.0, wavelength=1.0,
            screen_distance=100.0, partial_gammas=[0.0, 0.5, 1.0],
        )
        return compute_quantum_metrics(results)

    def test_has_per_condition(self, metrics):
        assert "per_condition" in metrics

    def test_has_decoherence_analysis(self, metrics):
        assert "decoherence_analysis" in metrics

    def test_has_cross_condition(self, metrics):
        assert "cross_condition" in metrics

    def test_has_interpretation(self, metrics):
        assert "interpretation" in metrics

    def test_verdict_consistent(self, metrics):
        assert metrics["interpretation"]["verdict"] in {"METRICS_CONSISTENT", "METRICS_ANOMALY_DETECTED"}

    def test_coherent_visibility_higher(self, metrics):
        v_coh = metrics["per_condition"]["two_slit_coherent"]["fringe_visibility"]
        v_dec = metrics["per_condition"]["two_slit_decohered"]["fringe_visibility"]
        assert v_coh > v_dec

    def test_decoherence_monotone(self, metrics):
        assert metrics["decoherence_analysis"]["is_monotone_decreasing"] is True
