"""Tests for horizon_scaling.py."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest import mock

import pytest

from reality_audit.analysis.horizon_scaling import (
    _mean,
    _std,
    _cv,
    classify_metric_horizon_behavior,
    load_horizon_data_from_report,
    build_horizon_scaling_report,
    run_horizon_scaling,
    _build_synthetic_horizon_data,
    HS_STABLE,
    HS_SENSITIVE,
    HS_MEANINGFUL_LONGER,
    HS_UNSTABLE,
    HS_INSUFFICIENT_DATA,
)


# ---------------------------------------------------------------------------
# Math helpers
# ---------------------------------------------------------------------------

class TestMeanStdCv:
    def test_mean_empty(self):
        assert _mean([]) == 0.0

    def test_mean_basic(self):
        assert _mean([1.0, 3.0]) == pytest.approx(2.0)

    def test_std_single(self):
        assert _std([5.0]) == 0.0

    def test_cv_zero_mean(self):
        assert _cv([0.0, 0.0]) is None

    def test_cv_positive(self):
        cv = _cv([1.0, 2.0, 3.0])
        assert cv is not None and cv > 0


# ---------------------------------------------------------------------------
# classify_metric_horizon_behavior
# ---------------------------------------------------------------------------

class TestClassifyMetricHorizonBehavior:
    def _series(self, vals: List[float], turns=(5, 25, 50, 100)) -> Dict[str, Any]:
        return {str(t): {"mean": v, "std": 0.02, "n": 3} for t, v in zip(turns, vals)}

    def test_stable_metric(self):
        series = self._series([0.60, 0.61, 0.61, 0.62])
        result = classify_metric_horizon_behavior("path_smoothness", series, [5, 25, 50, 100])
        assert result["classification"] == HS_STABLE

    def test_sensitive_metric(self):
        series = self._series([0.70, 1.20, 1.80, 2.40])
        result = classify_metric_horizon_behavior("mean_position_error", series, [5, 25, 50, 100])
        assert result["classification"] == HS_SENSITIVE

    def test_meaningful_at_longer(self):
        series = self._series([0.01, 0.05, 0.12, 0.22])
        result = classify_metric_horizon_behavior("anisotropy_score", series, [5, 25, 50, 100])
        assert result["classification"] == HS_MEANINGFUL_LONGER

    def test_unstable_metric(self):
        # Very high std relative to mean
        series = {
            "5":   {"mean": 5.0, "std": 4.0,  "n": 3},
            "25":  {"mean": 8.0, "std": 7.0,  "n": 3},
            "50":  {"mean": 6.0, "std": 6.0,  "n": 3},
            "100": {"mean": 9.0, "std": 9.0,  "n": 3},
        }
        result = classify_metric_horizon_behavior("observer_dependence_score", series, [5, 25, 50, 100])
        assert result["classification"] == HS_UNSTABLE

    def test_insufficient_data_single_horizon(self):
        series = {"5": {"mean": 0.6, "std": 0.02, "n": 3}}
        result = classify_metric_horizon_behavior("path_smoothness", series, [5])
        assert result["classification"] == HS_INSUFFICIENT_DATA

    def test_result_contains_horizon_means(self):
        series = self._series([0.60, 0.61, 0.61, 0.62])
        result = classify_metric_horizon_behavior("path_smoothness", series, [5, 25, 50, 100])
        assert "horizon_means" in result
        assert "5" in result["horizon_means"]

    def test_result_contains_grand_mean(self):
        series = self._series([0.60, 0.62]) 
        result = classify_metric_horizon_behavior("path_smoothness", series, [5, 25])
        assert "grand_mean" in result


# ---------------------------------------------------------------------------
# load_horizon_data_from_report
# ---------------------------------------------------------------------------

class TestLoadHorizonDataFromReport:
    def test_basic_loading(self):
        report = {
            "turn_counts": [5, 50],
            "metrics": {
                "path_smoothness": {
                    "5":  {"mean": 0.6, "std": 0.02, "n": 3},
                    "50": {"mean": 0.62, "std": 0.02, "n": 3},
                }
            },
        }
        data, turns = load_horizon_data_from_report(report)
        assert turns == [5, 50]
        assert "path_smoothness" in data
        assert "5" in data["path_smoothness"]

    def test_empty_report(self):
        data, turns = load_horizon_data_from_report({})
        assert turns == []
        assert data == {}


# ---------------------------------------------------------------------------
# build_horizon_scaling_report
# ---------------------------------------------------------------------------

class TestBuildHorizonScalingReport:
    def test_returns_expected_keys(self):
        data, turns = _build_synthetic_horizon_data()
        report = build_horizon_scaling_report(data, turns, data_source="synthetic")
        assert "n_metrics" in report
        assert "classification_counts" in report
        assert "metrics" in report

    def test_all_classification_types_present(self):
        data, turns = _build_synthetic_horizon_data()
        report = build_horizon_scaling_report(data, turns)
        classifications = {e["classification"] for e in report["metrics"]}
        # Synthetic data includes at least stable, sensitive, and meaningful_at_longer
        assert HS_STABLE in classifications
        assert HS_SENSITIVE in classifications
        assert HS_MEANINGFUL_LONGER in classifications

    def test_counts_sum_to_n_metrics(self):
        data, turns = _build_synthetic_horizon_data()
        report = build_horizon_scaling_report(data, turns)
        total = sum(report["classification_counts"].values())
        assert total == report["n_metrics"]

    def test_entries_sorted(self):
        data, turns = _build_synthetic_horizon_data()
        report = build_horizon_scaling_report(data, turns)
        classifications = [e["classification"] for e in report["metrics"]]
        order = {HS_STABLE: 0, HS_SENSITIVE: 1, HS_MEANINGFUL_LONGER: 2,
                 HS_UNSTABLE: 3, HS_INSUFFICIENT_DATA: 4}
        ordered_vals = [order.get(c, 5) for c in classifications]
        assert ordered_vals == sorted(ordered_vals)


# ---------------------------------------------------------------------------
# run_horizon_scaling (integration — uses synthetic fallback)
# ---------------------------------------------------------------------------

class TestRunHorizonScaling:
    def test_writes_report_json(self, tmp_path):
        result = run_horizon_scaling(output_root=tmp_path)
        assert (tmp_path / "horizon_scaling_report.json").exists()

    def test_writes_csv(self, tmp_path):
        run_horizon_scaling(output_root=tmp_path)
        assert (tmp_path / "horizon_scaling_summary.csv").exists()

    def test_returns_report_dict(self, tmp_path):
        result = run_horizon_scaling(output_root=tmp_path)
        assert "metrics" in result
        assert "classification_counts" in result

    def test_uses_live_data_when_present(self, tmp_path):
        live_report = {
            "turn_counts": [10, 20],
            "metrics": {
                "path_smoothness": {
                    "10": {"mean": 0.6, "std": 0.02, "n": 3},
                    "20": {"mean": 0.61, "std": 0.02, "n": 3},
                }
            },
        }
        (tmp_path / "horizon_comparison_report.json").write_text(json.dumps(live_report))
        result = run_horizon_scaling(output_root=tmp_path)
        assert result["data_source"] == "live"

    def test_uses_synthetic_when_no_live_data(self, tmp_path):
        result = run_horizon_scaling(output_root=tmp_path)
        assert result["data_source"] == "synthetic_fallback"

    def test_n_metrics_positive(self, tmp_path):
        result = run_horizon_scaling(output_root=tmp_path)
        assert result["n_metrics"] > 0
