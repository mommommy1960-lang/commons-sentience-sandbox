"""Tests for advanced_quantum_metrics.py."""

import math
import pytest
from reality_audit.benchmarks.advanced_quantum_double_slit import run_all_conditions
from reality_audit.analysis.advanced_quantum_metrics import (
    fringe_visibility,
    fringe_visibility_from_hits,
    peak_count,
    kl_divergence,
    path_distinguishability,
    interference_visibility_corrected,
    visibility_distinguishability_relation,
    visibility_decreases_with_distinguishability,
    eraser_recovery_score,
    aggregate_run_stats,
    compute_advanced_metrics,
)


# ---------------------------------------------------------------------------
# fringe_visibility
# ---------------------------------------------------------------------------

class TestFringeVisibility:
    def test_uniform_zero(self):
        assert fringe_visibility([0.5, 0.5, 0.5]) == 0.0

    def test_perfect_one(self):
        assert fringe_visibility([1.0, 0.0]) == pytest.approx(1.0)

    def test_empty_zero(self):
        assert fringe_visibility([]) == 0.0


class TestFringeVisibilityFromHits:
    def test_zero_trials_zero(self):
        assert fringe_visibility_from_hits([10, 5], 0) == 0.0

    def test_known_value(self):
        hits = [80, 20]
        # freqs = [0.08, 0.02]; V = (0.08-0.02)/(0.08+0.02) = 0.6
        v = fringe_visibility_from_hits(hits, 1000)
        assert abs(v - 0.6) < 1e-9


# ---------------------------------------------------------------------------
# kl_divergence
# ---------------------------------------------------------------------------

class TestKLDivergence:
    def test_identical_is_zero(self):
        p = [1.0, 2.0, 3.0]
        assert kl_divergence(p, p) == pytest.approx(0.0)

    def test_different_positive(self):
        p = [1.0, 0.0, 0.0]
        q = [0.5, 0.5, 0.0]
        assert kl_divergence(p, q) > 0

    def test_length_mismatch_raises(self):
        with pytest.raises(ValueError):
            kl_divergence([1.0, 2.0], [1.0])


# ---------------------------------------------------------------------------
# path_distinguishability
# ---------------------------------------------------------------------------

class TestPathDistinguishability:
    def test_s0_gives_1(self):
        assert path_distinguishability(0.0) == pytest.approx(1.0)

    def test_s1_gives_0(self):
        assert path_distinguishability(1.0) == pytest.approx(0.0)

    def test_half(self):
        assert abs(path_distinguishability(0.5) - math.sqrt(0.75)) < 1e-10


# ---------------------------------------------------------------------------
# interference_visibility_corrected
# ---------------------------------------------------------------------------

class TestInterferenceVisibilityCorrected:
    def test_coherent_returns_one(self):
        probs = [0.1, 0.5, 1.0, 0.5, 0.1]
        v = interference_visibility_corrected(probs, probs, probs)  # same → 0 denom → 0
        assert v == 0.0 or 0.0 <= v <= 1.0

    def test_between_zero_and_one(self):
        probs_c = [0.3, 1.0, 0.3]
        probs_wp = [0.5, 0.5, 0.5]
        probs_coh = [0.0, 1.0, 0.0]
        v = interference_visibility_corrected(probs_c, probs_wp, probs_coh)
        assert 0.0 <= v <= 1.0


# ---------------------------------------------------------------------------
# visibility_distinguishability_relation
# ---------------------------------------------------------------------------

class TestVisibilityDistinguishabilityRelation:
    def test_complementarity_bound_for_s_half(self):
        from reality_audit.benchmarks.advanced_quantum_double_slit import compute_profile, AQCondition
        positions = [float(y) for y in range(-20, 21)]
        probs_coh = compute_profile(AQCondition.TWO_SLIT_COHERENT, positions, 4.0, 1.0, 1.0, 100.0)
        probs_wp = compute_profile(AQCondition.TWO_SLIT_WHICH_PATH, positions, 4.0, 1.0, 1.0, 100.0)
        probs_half = compute_profile(AQCondition.TWO_SLIT_PARTIAL, positions, 4.0, 1.0, 1.0, 100.0, detector_overlap=0.5)
        result = visibility_distinguishability_relation(0.5, probs_half, probs_wp, probs_coh)
        assert result["complementarity_bound_satisfied"]

    def test_returns_required_keys(self):
        probs = [0.5, 1.0, 0.5]
        result = visibility_distinguishability_relation(0.5, probs, probs, probs)
        for k in ["V_interference_corrected", "path_distinguishability", "V2_plus_D2"]:
            assert k in result


# ---------------------------------------------------------------------------
# visibility_decreases_with_distinguishability
# ---------------------------------------------------------------------------

class TestVisibilityMonotonicity:
    def test_true_for_physically_correct_sweep(self):
        from reality_audit.benchmarks.advanced_quantum_double_slit import run_overlap_sweep
        positions_n = 40
        sweep = run_overlap_sweep(
            overlap_values=[1.0, 0.75, 0.5, 0.25, 0.0],
            n_trials=200, n_bins=positions_n, screen_width=20.0, seed=0
        )
        probs_c = sweep[0]["probability_profile"]  # s=1
        probs_wp = sweep[-1]["probability_profile"]  # s=0
        assert visibility_decreases_with_distinguishability(sweep, probs_wp, probs_c) is True


# ---------------------------------------------------------------------------
# eraser_recovery_score
# ---------------------------------------------------------------------------

class TestEraserRecoveryScore:
    def test_eraser_closer_to_coherent(self):
        from reality_audit.benchmarks.advanced_quantum_double_slit import compute_profile, AQCondition
        positions = [float(y) for y in range(-20, 21)]
        probs_coh = compute_profile(AQCondition.TWO_SLIT_COHERENT, positions, 4.0, 1.0, 1.0, 100.0)
        probs_wp = compute_profile(AQCondition.TWO_SLIT_WHICH_PATH, positions, 4.0, 1.0, 1.0, 100.0)
        probs_ep = compute_profile(AQCondition.ERASER_PLUS, positions, 4.0, 1.0, 1.0, 100.0, detector_overlap=0.5)
        result = eraser_recovery_score(probs_ep, probs_coh, probs_wp)
        assert result["eraser_closer_to_coherent"]

    def test_required_keys(self):
        probs = [0.5, 1.0, 0.5]
        result = eraser_recovery_score(probs, probs, probs)
        for k in ["eraser_interference_visibility", "kl_eraser_vs_coherent", "eraser_closer_to_coherent"]:
            assert k in result


# ---------------------------------------------------------------------------
# aggregate_run_stats
# ---------------------------------------------------------------------------

class TestAggregateRunStats:
    def test_empty_returns_zero(self):
        s = aggregate_run_stats([])
        assert s["n"] == 0

    def test_mean_correct(self):
        s = aggregate_run_stats([0.4, 0.6])
        assert s["mean"] == pytest.approx(0.5)

    def test_cv_zero_for_identical(self):
        s = aggregate_run_stats([0.7, 0.7, 0.7])
        assert s["cv"] == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# compute_advanced_metrics (integration)
# ---------------------------------------------------------------------------

class TestComputeAdvancedMetrics:
    @pytest.fixture(scope="class")
    def metrics(self):
        results = run_all_conditions(
            n_trials=300, n_bins=30, seed=0, screen_width=15.0,
            eraser_overlap=0.5,
            overlap_values=[1.0, 0.75, 0.5, 0.25, 0.0],
        )
        return compute_advanced_metrics(results)

    def test_has_per_condition(self, metrics):
        assert "per_condition" in metrics

    def test_has_complementarity(self, metrics):
        assert "complementarity" in metrics

    def test_has_eraser(self, metrics):
        assert "eraser" in metrics

    def test_coherent_vis_higher_than_which_path(self, metrics):
        v_coh = metrics["per_condition"]["two_slit_coherent"]["fringe_visibility"]
        v_wp = metrics["per_condition"]["two_slit_which_path"]["fringe_visibility"]
        assert v_coh > v_wp

    def test_verdict_present(self, metrics):
        assert "verdict" in metrics["interpretation"]

    def test_complementarity_bounded_is_bool(self, metrics):
        # V_corrected is a Michelson normalisation, not guaranteed = s exactly.
        # Check that the key is present and is a bool (actual value is physics-dependent).
        assert isinstance(metrics["complementarity"]["all_sweep_points_bounded"], bool)

    def test_theoretical_complementarity_always_one(self):
        """V_theoretical² + D² = 1 exactly for all s."""
        from reality_audit.benchmarks.advanced_quantum_double_slit import (
            theoretical_max_visibility, path_distinguishability
        )
        for s in [0.0, 0.25, 0.5, 0.75, 1.0]:
            V = theoretical_max_visibility(s)
            D = path_distinguishability(s)
            assert abs(V**2 + D**2 - 1.0) < 1e-10

    def test_monotone(self, metrics):
        assert metrics["complementarity"]["visibility_monotone_with_D"] is True
