"""Tests for false-positive detection (Part 9 — Stage 3).

Verifies:
- The threshold-check logic works correctly on synthetic data.
- The full pipeline runs without crashing on a real random-walk baseline.
- A metric that deliberately violates its threshold is correctly flagged.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List

import pytest

from reality_audit.experiments.false_positive_tests import (
    _FP_THRESHOLDS,
    _check_threshold,
    run_false_positive_tests,
)


# ---------------------------------------------------------------------------
# Unit tests: _check_threshold
# ---------------------------------------------------------------------------

class TestCheckThreshold:
    """Test the threshold-evaluation helper in isolation."""

    def _agg_metrics(self, metric: str, mean: float, max_val: float) -> Dict[str, Any]:
        return {
            metric: {
                "mean": mean,
                "max": max_val,
                "std": 0.0,
                "n": 5,
                "consistency_score": 1.0,
                "stability": "stable",
            }
        }

    def test_anisotropy_passes_below_threshold(self):
        # threshold is 210, direction=below → 185 should pass
        agg = self._agg_metrics("anisotropy_score", mean=185.0, max_val=195.0)
        spec = _FP_THRESHOLDS["anisotropy_score"]
        result = _check_threshold("anisotropy_score", agg, spec)
        assert result["passed"] is True
        assert result["reliability_flag"] == "ok"

    def test_anisotropy_fails_above_threshold(self):
        agg = self._agg_metrics("anisotropy_score", mean=185.0, max_val=220.0)
        spec = _FP_THRESHOLDS["anisotropy_score"]
        result = _check_threshold("anisotropy_score", agg, spec)
        # spec checks "max" for anisotropy
        assert result["passed"] is False
        assert result["reliability_flag"] == "unreliable"
        assert "warning" in result

    def test_observer_dependence_passes_below_threshold(self):
        agg = self._agg_metrics("observer_dependence_score", mean=0.1, max_val=0.2)
        spec = _FP_THRESHOLDS["observer_dependence_score"]
        result = _check_threshold("observer_dependence_score", agg, spec)
        assert result["passed"] is True

    def test_observer_dependence_fails_above_threshold(self):
        agg = self._agg_metrics("observer_dependence_score", mean=20.0, max_val=25.0)
        spec = _FP_THRESHOLDS["observer_dependence_score"]
        result = _check_threshold("observer_dependence_score", agg, spec)
        assert result["passed"] is False
        assert result["reliability_flag"] == "unreliable"

    def test_bandwidth_passes_above_threshold(self):
        agg = self._agg_metrics("bandwidth_bottleneck_score", mean=0.98, max_val=1.0)
        spec = _FP_THRESHOLDS["bandwidth_bottleneck_score"]
        result = _check_threshold("bandwidth_bottleneck_score", agg, spec)
        assert result["passed"] is True

    def test_bandwidth_fails_below_threshold(self):
        agg = self._agg_metrics("bandwidth_bottleneck_score", mean=0.5, max_val=0.6)
        spec = _FP_THRESHOLDS["bandwidth_bottleneck_score"]
        result = _check_threshold("bandwidth_bottleneck_score", agg, spec)
        assert result["passed"] is False

    def test_missing_metric_returns_not_passed(self):
        # Empty agg_metrics
        spec = _FP_THRESHOLDS["anisotropy_score"]
        result = _check_threshold("anisotropy_score", {}, spec)
        assert result["passed"] is False

    def test_nan_value_returns_not_passed(self):
        agg = {"anisotropy_score": {"mean": float("nan"), "max": float("nan"),
                                    "std": 0.0, "n": 0, "consistency_score": float("nan"),
                                    "stability": "unknown"}}
        spec = _FP_THRESHOLDS["anisotropy_score"]
        result = _check_threshold("anisotropy_score", agg, spec)
        assert result["passed"] is False


# ---------------------------------------------------------------------------
# Full pipeline smoke test
# ---------------------------------------------------------------------------

class TestFalsePositivePipeline:
    """End-to-end pipeline: run random baselines and check report structure."""

    def test_pipeline_runs_without_crash(self, tmp_path):
        """Pipeline should complete without raising (uses 2 seeds, short duration)."""
        import reality_audit.experiments.false_positive_tests as fpt
        original_duration = fpt._DURATION
        original_seeds = fpt._SEEDS
        fpt._DURATION = 1.0   # 2 steps at dt=0.5 — fast
        fpt._SEEDS = [42, 43]
        try:
            report = run_false_positive_tests(seeds=[42, 43], output_dir=tmp_path)
        finally:
            fpt._DURATION = original_duration
            fpt._SEEDS = original_seeds

        assert "all_thresholds_passed" in report
        assert "threshold_checks" in report
        assert "unreliable_metrics" in report

    def test_report_contains_all_threshold_metrics(self, tmp_path):
        import reality_audit.experiments.false_positive_tests as fpt
        fpt._DURATION = 1.0
        try:
            report = run_false_positive_tests(seeds=[42], output_dir=tmp_path)
        finally:
            fpt._DURATION = 1.0

        for metric in _FP_THRESHOLDS:
            assert metric in report["threshold_checks"], f"Missing: {metric}"

    def test_report_written_to_disk(self, tmp_path):
        import reality_audit.experiments.false_positive_tests as fpt
        fpt._DURATION = 1.0
        try:
            run_false_positive_tests(seeds=[42], output_dir=tmp_path)
        finally:
            fpt._DURATION = 1.0

        assert (tmp_path / "false_positive_report.json").exists()

    def test_reliability_flag_is_valid_value(self, tmp_path):
        import reality_audit.experiments.false_positive_tests as fpt
        fpt._DURATION = 1.0
        try:
            report = run_false_positive_tests(seeds=[42], output_dir=tmp_path)
        finally:
            fpt._DURATION = 1.0

        valid_flags = {"ok", "unreliable"}
        for metric, result in report["threshold_checks"].items():
            flag = result.get("reliability_flag")
            assert flag in valid_flags, f"{metric}: unexpected flag {flag!r}"

    def test_all_thresholds_passed_is_boolean(self, tmp_path):
        import reality_audit.experiments.false_positive_tests as fpt
        fpt._DURATION = 1.0
        try:
            report = run_false_positive_tests(seeds=[42], output_dir=tmp_path)
        finally:
            fpt._DURATION = 1.0

        assert isinstance(report["all_thresholds_passed"], bool)

    def test_cross_baseline_consistency_present(self, tmp_path):
        import reality_audit.experiments.false_positive_tests as fpt
        fpt._DURATION = 1.0
        try:
            report = run_false_positive_tests(seeds=[42], output_dir=tmp_path)
        finally:
            fpt._DURATION = 1.0

        assert "cross_baseline_consistency" in report
