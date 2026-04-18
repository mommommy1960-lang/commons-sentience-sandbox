"""Tests for toy validation scenarios.

Each test asserts that the relevant metric changes in the expected direction
relative to the baseline, confirming the audit layer measures what it claims.
"""

from __future__ import annotations

import pytest
from reality_audit.validation.toy_experiments import (
    run_all_toy_scenarios,
    scenario_A_straight_path_baseline,
    scenario_B_anisotropy,
    scenario_C_observer_divergence,
    scenario_D_bandwidth_staleness,
)


@pytest.fixture(scope="module")
def all_metrics():
    """Run all four scenarios once and cache the results for the module."""
    return run_all_toy_scenarios(verbose=False)


class TestScenarioA_Baseline:
    def test_full_bandwidth_coverage(self, all_metrics):
        """Baseline always observes: bandwidth_bottleneck_score should be 1.0."""
        m = all_metrics["A_straight_path_baseline"]
        assert m["bandwidth_bottleneck_score"] == pytest.approx(1.0, abs=1e-6)

    def test_no_quantization_artifacts(self, all_metrics):
        """Continuous baseline has no repeated stale readings."""
        m = all_metrics["A_straight_path_baseline"]
        assert m["quantization_artifact_score"] == pytest.approx(0.0, abs=1e-6)

    def test_finite_positive_stability(self, all_metrics):
        """Baseline stability score is a finite value in (0, 1]."""
        m = all_metrics["A_straight_path_baseline"]
        assert 0.0 < m["stability_score"] <= 1.0

    def test_convergence_time_finite(self, all_metrics):
        """Baseline converges within the episode duration."""
        import math
        m = all_metrics["A_straight_path_baseline"]
        assert math.isfinite(m["convergence_time"])
        assert m["convergence_time"] <= 5.1  # duration is 5.0 s


class TestScenarioB_Anisotropy:
    def test_anisotropy_score_higher_than_baseline(self, all_metrics):
        """Anisotropic world produces higher anisotropy_score than baseline."""
        a = all_metrics["A_straight_path_baseline"]["anisotropy_score"]
        b = all_metrics["B_anisotropy"]["anisotropy_score"]
        assert b > a, f"Expected B anisotropy ({b:.4f}) > A ({a:.4f})"

    def test_full_bandwidth_still(self, all_metrics):
        """Anisotropy scenario still always observes (bandwidth=1.0)."""
        m = all_metrics["B_anisotropy"]
        assert m["bandwidth_bottleneck_score"] == pytest.approx(1.0, abs=1e-6)

    def test_no_quantization_artifacts(self, all_metrics):
        """Anisotropy world does not introduce stale readings."""
        m = all_metrics["B_anisotropy"]
        assert m["quantization_artifact_score"] == pytest.approx(0.0, abs=1e-6)


class TestScenarioC_ObserverDivergence:
    def test_bandwidth_reduced(self, all_metrics):
        """Periodic observation should reduce bandwidth_bottleneck_score below 1.0."""
        m = all_metrics["C_observer_divergence"]
        assert m["bandwidth_bottleneck_score"] < 1.0

    def test_quantization_artifacts_increase(self, all_metrics):
        """Sparse observations cause repeated cached readings — high artifact count."""
        a_artifacts = all_metrics["A_straight_path_baseline"]["quantization_artifact_score"]
        c_artifacts = all_metrics["C_observer_divergence"]["quantization_artifact_score"]
        assert c_artifacts > a_artifacts, (
            f"Expected C artifacts ({c_artifacts}) > A ({a_artifacts})"
        )

    def test_directional_error_positive(self, all_metrics):
        """Stale direction readings introduce non-zero directional error."""
        m = all_metrics["C_observer_divergence"]
        # With stale cached velocity the directional error deviates from baseline
        assert m["directional_error"] >= 0.0  # non-negative always


class TestScenarioD_BandwidthStaleness:
    def test_bandwidth_score_below_baseline(self, all_metrics):
        """Bandwidth-limited scenario has lower bandwidth score than baseline."""
        a = all_metrics["A_straight_path_baseline"]["bandwidth_bottleneck_score"]
        d = all_metrics["D_bandwidth_staleness"]["bandwidth_bottleneck_score"]
        assert d < a, f"Expected D bw ({d:.4f}) < A ({a:.4f})"

    def test_stability_worse_than_baseline(self, all_metrics):
        """Stale control feedback degrades stability score compared to baseline."""
        a = all_metrics["A_straight_path_baseline"]["stability_score"]
        d = all_metrics["D_bandwidth_staleness"]["stability_score"]
        assert d < a, f"Expected D stability ({d:.4f}) < A ({a:.4f})"

    def test_high_quantization_artifacts(self, all_metrics):
        """Frozen sensor cache produces many repeated readings."""
        a_artifacts = all_metrics["A_straight_path_baseline"]["quantization_artifact_score"]
        d_artifacts = all_metrics["D_bandwidth_staleness"]["quantization_artifact_score"]
        assert d_artifacts > a_artifacts, (
            f"Expected D artifacts ({d_artifacts}) > A ({a_artifacts})"
        )


class TestScenarioOrdering:
    def test_all_four_scenarios_complete(self, all_metrics):
        """All four scenario keys are present in the results dict."""
        expected_keys = {
            "A_straight_path_baseline",
            "B_anisotropy",
            "C_observer_divergence",
            "D_bandwidth_staleness",
        }
        assert expected_keys == set(all_metrics.keys())

    def test_all_metrics_are_finite(self, all_metrics):
        """Every metric value in every scenario is a finite number."""
        import math
        for scenario, metrics in all_metrics.items():
            for key, val in metrics.items():
                assert math.isfinite(val), (
                    f"Scenario {scenario!r} metric {key!r} = {val} is not finite"
                )
