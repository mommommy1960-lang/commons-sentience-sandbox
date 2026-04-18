"""Tests for advanced_quantum_double_slit.py — core model."""

import math
import pytest
from reality_audit.benchmarks.advanced_quantum_double_slit import (
    AQCondition,
    marginal_probability,
    eraser_probability,
    one_slit_probability,
    path_distinguishability,
    theoretical_max_visibility,
    complementarity_bound_check,
    compute_profile,
    run_condition,
    run_overlap_sweep,
    run_all_conditions,
)


# ---------------------------------------------------------------------------
# marginal_probability
# ---------------------------------------------------------------------------

class TestMarginalProbability:
    def test_s1_matches_coherent_formula(self):
        """s=1 → full interference; P(0) ≈ 2·|A(0)|² (both amplitudes add)."""
        p = marginal_probability(0.0, 1.0, 4.0, 1.0, 1.0, 100.0)
        assert p > 0.5  # coherent sum > incoherent

    def test_s0_matches_incoherent(self):
        """s=0 → incoherent sum; no interference cross-term."""
        p_s0 = marginal_probability(0.0, 0.0, 4.0, 1.0, 1.0, 100.0)
        p_s1 = marginal_probability(0.0, 1.0, 4.0, 1.0, 1.0, 100.0)
        # incoherent is strictly less at the constructive centre
        assert p_s0 < p_s1

    def test_nonneg_all_y(self):
        for y in range(-20, 21):
            assert marginal_probability(y, 0.5, 4.0, 1.0, 1.0, 100.0) >= 0.0

    def test_symmetric(self):
        p_plus = marginal_probability(5.0, 0.7, 4.0, 1.0, 1.0, 100.0)
        p_minus = marginal_probability(-5.0, 0.7, 4.0, 1.0, 1.0, 100.0)
        assert abs(p_plus - p_minus) < 1e-10

    def test_invalid_overlap_raises(self):
        with pytest.raises(ValueError):
            marginal_probability(0.0, 1.5, 4.0, 1.0, 1.0, 100.0)


# ---------------------------------------------------------------------------
# eraser_probability
# ---------------------------------------------------------------------------

class TestEraserProbability:
    def test_plus_selection_bright_at_centre(self):
        """Eraser |+⟩ amplifies constructive interference."""
        p_plus = eraser_probability(0.0, 0.5, 4.0, 1.0, 1.0, 100.0, +1)
        p_minus_cond = eraser_probability(0.0, 0.5, 4.0, 1.0, 1.0, 100.0, -1)
        assert p_plus > p_minus_cond  # |+⟩ gives constructive at y=0

    def test_minus_selection_dark_at_centre(self):
        """Eraser |−⟩ gives anti-fringe (node at y=0)."""
        p_minus = eraser_probability(0.0, 0.5, 4.0, 1.0, 1.0, 100.0, -1)
        assert p_minus < 0.01  # near-zero at y=0

    def test_nonneg_all_y(self):
        for y in range(-20, 21):
            assert eraser_probability(y, 0.5, 4.0, 1.0, 1.0, 100.0, +1) >= 0.0
            assert eraser_probability(y, 0.5, 4.0, 1.0, 1.0, 100.0, -1) >= 0.0

    def test_invalid_sign_raises(self):
        with pytest.raises(ValueError):
            eraser_probability(0.0, 0.5, 4.0, 1.0, 1.0, 100.0, 0)

    def test_s1_eraser_minus_is_zero_everywhere(self):
        """With s=1, |−⟩ eraser has zero weight."""
        for y in range(-10, 11):
            p = eraser_probability(y, 1.0, 4.0, 1.0, 1.0, 100.0, -1)
            assert p < 1e-10


# ---------------------------------------------------------------------------
# Complementarity
# ---------------------------------------------------------------------------

class TestComplementarity:
    def test_path_distinguishability_s0(self):
        assert path_distinguishability(0.0) == pytest.approx(1.0)

    def test_path_distinguishability_s1(self):
        assert path_distinguishability(1.0) == pytest.approx(0.0)

    def test_path_distinguishability_half(self):
        D = path_distinguishability(0.5)
        assert abs(D - math.sqrt(0.75)) < 1e-10

    def test_theoretical_visibility_equals_overlap(self):
        for s in [0.0, 0.3, 0.7, 1.0]:
            assert theoretical_max_visibility(s) == pytest.approx(s)

    def test_complementarity_bound_exact(self):
        for s in [0.0, 0.25, 0.5, 0.75, 1.0]:
            result = complementarity_bound_check(s)
            assert result["complementarity_satisfied"], f"Failed for s={s}: {result['V2_plus_D2']}"


# ---------------------------------------------------------------------------
# compute_profile
# ---------------------------------------------------------------------------

class TestComputeProfile:
    def test_one_slit_length(self):
        positions = list(range(-5, 6))
        probs = compute_profile(AQCondition.ONE_SLIT, positions, 4.0, 1.0, 1.0, 100.0)
        assert len(probs) == len(positions)

    def test_coherent_higher_at_centre_than_which_path(self):
        positions = [float(y) for y in range(-20, 21)]
        p_coh = compute_profile(AQCondition.TWO_SLIT_COHERENT, positions, 4.0, 1.0, 1.0, 100.0)
        p_wp = compute_profile(AQCondition.TWO_SLIT_WHICH_PATH, positions, 4.0, 1.0, 1.0, 100.0)
        centre = len(positions) // 2
        assert p_coh[centre] > p_wp[centre]

    def test_eraser_plus_coherent_at_centre(self):
        positions = [float(y) for y in range(-10, 11)]
        p_ep = compute_profile(AQCondition.ERASER_PLUS, positions, 4.0, 1.0, 1.0, 100.0, detector_overlap=0.5)
        p_em = compute_profile(AQCondition.ERASER_MINUS, positions, 4.0, 1.0, 1.0, 100.0, detector_overlap=0.5)
        centre = len(positions) // 2
        assert p_ep[centre] > p_em[centre]

    def test_unknown_condition_raises(self):
        with pytest.raises((ValueError, AttributeError)):
            compute_profile("bad_cond", [0.0], 4.0, 1.0, 1.0, 100.0)


# ---------------------------------------------------------------------------
# run_condition
# ---------------------------------------------------------------------------

class TestRunCondition:
    def _run(self, condition, **kw):
        return run_condition(condition, n_trials=200, n_bins=20, screen_width=20.0, **kw)

    def test_required_keys(self):
        r = self._run(AQCondition.TWO_SLIT_COHERENT)
        for k in ["condition", "detector_overlap", "params", "screen_positions",
                  "probability_profile", "hit_counts", "n_trials", "seed", "summary"]:
            assert k in r

    def test_hit_sum_equals_n_trials(self):
        r = self._run(AQCondition.TWO_SLIT_WHICH_PATH)
        assert sum(r["hit_counts"]) == 200

    def test_profile_length_n_bins(self):
        r = self._run(AQCondition.ERASER_PLUS, detector_overlap=0.5)
        assert len(r["probability_profile"]) == 20

    def test_invalid_n_bins_raises(self):
        with pytest.raises(ValueError):
            run_condition(AQCondition.ONE_SLIT, n_bins=1)

    def test_summary_fringe_visibility_present(self):
        r = self._run(AQCondition.TWO_SLIT_PARTIAL, detector_overlap=0.5)
        assert "fringe_visibility" in r["summary"]


# ---------------------------------------------------------------------------
# run_all_conditions
# ---------------------------------------------------------------------------

class TestRunAllConditions:
    def test_all_keys_present(self):
        r = run_all_conditions(n_trials=100, n_bins=10, seed=0, screen_width=10.0,
                               eraser_overlap=0.5, overlap_values=[0.5, 1.0])
        for k in ["one_slit", "two_slit_coherent", "two_slit_which_path",
                  "eraser_plus", "eraser_minus", "overlap_sweep"]:
            assert k in r

    def test_overlap_sweep_length(self):
        r = run_all_conditions(n_trials=100, n_bins=10, seed=0, screen_width=10.0,
                               eraser_overlap=0.5, overlap_values=[1.0, 0.5, 0.0])
        assert len(r["overlap_sweep"]) == 3

    def test_coherent_visibility_exceeds_which_path(self):
        r = run_all_conditions(n_trials=200, n_bins=40, seed=0, screen_width=20.0,
                               eraser_overlap=0.5, overlap_values=[])
        s_c = r["two_slit_coherent"]["summary"]["fringe_visibility"]
        s_w = r["two_slit_which_path"]["summary"]["fringe_visibility"]
        assert s_c > s_w
