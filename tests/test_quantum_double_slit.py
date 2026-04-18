"""Tests for quantum_double_slit.py — core quantum physics model."""

import math
import pytest
from reality_audit.benchmarks.quantum_double_slit import (
    QSlitCondition,
    slit_amplitude,
    coherent_probability,
    decohered_probability,
    partial_decoherence_probability,
    one_slit_probability,
    compute_probability_profile,
    born_sample,
    run_condition,
    run_decoherence_sweep,
    run_all_conditions,
    DEFAULT_SLIT_SEPARATION,
    DEFAULT_SLIT_WIDTH,
    DEFAULT_WAVELENGTH,
    DEFAULT_SCREEN_DISTANCE,
)


# ---------------------------------------------------------------------------
# slit_amplitude
# ---------------------------------------------------------------------------

class TestSlitAmplitude:
    def test_magnitude_at_slit_position_is_one(self):
        """Amplitude at y=y_slit has sinc(0)=1 envelope."""
        A = slit_amplitude(2.0, 2.0, slit_width=1.0, wavelength=1.0, screen_distance=100.0)
        assert abs(abs(A) - 1.0) < 1e-10

    def test_amplitude_is_complex(self):
        A = slit_amplitude(5.0, 0.0, slit_width=1.0, wavelength=1.0, screen_distance=100.0)
        assert isinstance(A, complex)

    def test_magnitude_less_than_one_away_from_slit(self):
        """Sinc envelope < 1 when y_screen != y_slit."""
        A = slit_amplitude(10.0, 0.0, slit_width=1.0, wavelength=1.0, screen_distance=10.0)
        assert abs(A) < 1.0

    def test_phase_encodes_slit_position(self):
        """Two slits at ±d/2 should have conjugate phases at y=0."""
        y_screen = 5.0
        A_L = slit_amplitude(y_screen, -2.0, slit_width=1.0, wavelength=1.0, screen_distance=100.0)
        A_R = slit_amplitude(y_screen, +2.0, slit_width=1.0, wavelength=1.0, screen_distance=100.0)
        # At symmetric y≠0: conjugate phases add constructively at y=0
        # Just confirm they are not equal (different phases)
        assert A_L != A_R

    def test_zero_slit_position_pure_real(self):
        """Slit at y_slit=0 has zero phase → amplitude is real."""
        A = slit_amplitude(3.0, 0.0, slit_width=1.0, wavelength=1.0, screen_distance=100.0)
        assert abs(A.imag) < 1e-12


# ---------------------------------------------------------------------------
# coherent_probability
# ---------------------------------------------------------------------------

class TestCoherentProbability:
    def test_returns_float(self):
        p = coherent_probability(0.0, 4.0, 1.0, 1.0, 100.0)
        assert isinstance(p, float)

    def test_nonnegative(self):
        for y in [-10, -5, 0, 5, 10]:
            assert coherent_probability(y, 4.0, 1.0, 1.0, 100.0) >= 0.0

    def test_symmetric_about_zero(self):
        p_plus = coherent_probability(5.0, 4.0, 1.0, 1.0, 100.0)
        p_minus = coherent_probability(-5.0, 4.0, 1.0, 1.0, 100.0)
        assert abs(p_plus - p_minus) < 1e-10

    def test_centre_is_high(self):
        """Constructive interference at y=0 should give a large value."""
        p_centre = coherent_probability(0.0, 4.0, 1.0, 1.0, 100.0)
        p_off = coherent_probability(15.0, 4.0, 1.0, 1.0, 100.0)
        assert p_centre > p_off


# ---------------------------------------------------------------------------
# decohered_probability
# ---------------------------------------------------------------------------

class TestDecoherence:
    def test_gamma0_equals_coherent(self):
        """partial_decoherence with gamma=0 == coherent."""
        y = 3.0
        p_coh = coherent_probability(y, 4.0, 1.0, 1.0, 100.0)
        p_part = partial_decoherence_probability(y, 4.0, 1.0, 1.0, 100.0, gamma=0.0)
        assert abs(p_coh - p_part) < 1e-10

    def test_gamma1_equals_decohered(self):
        """partial_decoherence with gamma=1 == decohered."""
        y = 3.0
        p_dec = decohered_probability(y, 4.0, 1.0, 1.0, 100.0)
        p_part = partial_decoherence_probability(y, 4.0, 1.0, 1.0, 100.0, gamma=1.0)
        assert abs(p_dec - p_part) < 1e-10

    def test_partial_between_coherent_and_decohered(self):
        """gamma=0.5 probability at y=0 should be between extremes."""
        y = 0.0
        p_coh = coherent_probability(y, 4.0, 1.0, 1.0, 100.0)
        p_dec = decohered_probability(y, 4.0, 1.0, 1.0, 100.0)
        p_half = partial_decoherence_probability(y, 4.0, 1.0, 1.0, 100.0, gamma=0.5)
        assert p_dec <= p_half <= p_coh + 1e-10

    def test_gamma_out_of_range_raises(self):
        with pytest.raises(ValueError):
            partial_decoherence_probability(0.0, 4.0, 1.0, 1.0, 100.0, gamma=1.5)

    def test_nonnegative_for_all_y(self):
        """Partial decoherence formula should never go negative."""
        for y in range(-20, 21):
            p = partial_decoherence_probability(y, 4.0, 1.0, 1.0, 100.0, gamma=0.5)
            assert p >= 0.0


# ---------------------------------------------------------------------------
# Monotonicity of fringe visibility with gamma
# ---------------------------------------------------------------------------

class TestPartialMonotonicity:
    def _visibility(self, probs):
        p_max, p_min = max(probs), min(probs)
        denom = p_max + p_min
        return (p_max - p_min) / denom if denom else 0.0

    def test_visibility_decreases_with_gamma(self):
        """Fringe visibility must decrease as gamma increases."""
        positions = [float(y) for y in range(-20, 21)]
        prev_v = None
        for gamma in [0.0, 0.25, 0.5, 0.75, 1.0]:
            probs = [
                partial_decoherence_probability(y, 4.0, 1.0, 1.0, 100.0, gamma=gamma)
                for y in positions
            ]
            v = self._visibility(probs)
            if prev_v is not None:
                assert v <= prev_v + 1e-6, f"Visibility increased at gamma={gamma}: {prev_v} → {v}"
            prev_v = v


# ---------------------------------------------------------------------------
# born_sample
# ---------------------------------------------------------------------------

class TestBornSample:
    def test_sum_equals_n_trials(self):
        probs = [0.1, 0.5, 0.4]
        hits = born_sample(probs, n_trials=1000, seed=42)
        assert sum(hits) == 1000

    def test_deterministic_with_same_seed(self):
        probs = [0.2, 0.3, 0.5]
        h1 = born_sample(probs, n_trials=500, seed=7)
        h2 = born_sample(probs, n_trials=500, seed=7)
        assert h1 == h2

    def test_different_seeds_different_results(self):
        probs = [0.2, 0.3, 0.5]
        h1 = born_sample(probs, n_trials=1000, seed=1)
        h2 = born_sample(probs, n_trials=1000, seed=2)
        assert h1 != h2

    def test_all_zero_prob_returns_zeros(self):
        hits = born_sample([0.0, 0.0, 0.0], n_trials=100, seed=0)
        assert all(h == 0 for h in hits)

    def test_length_matches_input(self):
        probs = [0.1] * 7
        hits = born_sample(probs, n_trials=100, seed=0)
        assert len(hits) == 7

    def test_concentrated_prob_concentrates_hits(self):
        probs = [0.0, 0.0, 1.0, 0.0, 0.0]
        hits = born_sample(probs, n_trials=200, seed=0)
        assert hits[2] == 200


# ---------------------------------------------------------------------------
# run_condition
# ---------------------------------------------------------------------------

class TestRunCondition:
    def _basic_run(self, condition, **kwargs):
        return run_condition(
            condition, n_trials=200, n_bins=20, seed=0, screen_width=20.0, **kwargs
        )

    def test_required_keys_present(self):
        r = self._basic_run(QSlitCondition.TWO_SLIT_COHERENT)
        for key in [
            "condition", "decoherence_gamma", "params",
            "screen_positions", "probability_profile", "hit_counts",
            "n_trials", "seed", "summary"
        ]:
            assert key in r, f"Missing key: {key}"

    def test_hit_count_length_matches_n_bins(self):
        r = self._basic_run(QSlitCondition.ONE_SLIT)
        assert len(r["hit_counts"]) == 20

    def test_hit_count_sums_to_n_trials(self):
        r = self._basic_run(QSlitCondition.TWO_SLIT_DECOHERED)
        assert sum(r["hit_counts"]) == 200

    def test_probability_profile_length_matches_n_bins(self):
        r = self._basic_run(QSlitCondition.TWO_SLIT_PARTIAL, decoherence_gamma=0.5)
        assert len(r["probability_profile"]) == 20

    def test_all_probabilities_nonneg(self):
        r = self._basic_run(QSlitCondition.TWO_SLIT_COHERENT)
        assert all(p >= 0.0 for p in r["probability_profile"])

    def test_summary_fringe_visibility_present(self):
        r = self._basic_run(QSlitCondition.TWO_SLIT_COHERENT)
        assert "fringe_visibility" in r["summary"]

    def test_invalid_n_bins_raises(self):
        with pytest.raises(ValueError):
            run_condition(QSlitCondition.ONE_SLIT, n_bins=1)


# ---------------------------------------------------------------------------
# run_all_conditions
# ---------------------------------------------------------------------------

class TestRunAllConditions:
    def test_all_keys_present(self):
        r = run_all_conditions(n_trials=100, n_bins=10, seed=0, screen_width=10.0, partial_gammas=[0.5])
        for key in ["one_slit", "two_slit_coherent", "two_slit_decohered", "decoherence_sweep"]:
            assert key in r, f"Missing key: {key}"

    def test_decoherence_sweep_length(self):
        gammas = [0.0, 0.5, 1.0]
        r = run_all_conditions(n_trials=100, n_bins=10, seed=0, screen_width=10.0, partial_gammas=gammas)
        assert len(r["decoherence_sweep"]) == len(gammas)

    def test_default_gammas_run_when_none(self):
        """partial_gammas=None uses the default gamma list (5 values)."""
        r = run_all_conditions(n_trials=100, n_bins=10, seed=0, screen_width=10.0, partial_gammas=None)
        assert len(r["decoherence_sweep"]) == 5

    def test_coherent_visibility_exceeds_decohered(self):
        r = run_all_conditions(
            n_trials=100, n_bins=50, seed=0, screen_width=20.0,
            slit_separation=4.0, slit_width=1.0, wavelength=1.0, screen_distance=100.0,
            partial_gammas=[],
        )
        v_coh = r["two_slit_coherent"]["summary"]["fringe_visibility"]
        v_dec = r["two_slit_decohered"]["summary"]["fringe_visibility"]
        assert v_coh > v_dec
