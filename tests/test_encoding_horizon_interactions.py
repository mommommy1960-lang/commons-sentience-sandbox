"""tests/test_encoding_horizon_interactions.py — Part 5 Stage 6"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List
from unittest import mock

import pytest

from reality_audit.analysis.encoding_horizon_interactions import (
    EH_INSUFFICIENT,
    EH_INVARIANT,
    EH_PARTIAL,
    EH_SENSITIVE,
    EH_TREND_CONSISTENT_INV,
    EH_TREND_CONSISTENT_SEN,
    EH_TREND_INSUFFICIENT,
    EH_TREND_STABILIZING,
    EH_TREND_WORSENING,
    EVALUATED_METRICS,
    _classify_horizon_trend,
    _classify_metric_at_horizon,
    _direction,
    _ordering_consensus,
    _spread_ratio,
    run_encoding_horizon_interactions,
)


# ---------------------------------------------------------------------------
# _direction
# ---------------------------------------------------------------------------

class TestDirection:
    def test_greater(self):
        assert _direction(1.0, 0.5) == "greater"

    def test_lesser(self):
        assert _direction(0.5, 1.0) == "lesser"

    def test_equal_within_tolerance(self):
        assert _direction(1.0, 1.02) == "equal"

    def test_zero_zero_equal(self):
        assert _direction(0.0, 0.0) == "equal"


# ---------------------------------------------------------------------------
# _ordering_consensus
# ---------------------------------------------------------------------------

class TestOrderingConsensus:
    def test_all_greater(self):
        assert _ordering_consensus(["greater", "greater", "greater"]) == EH_INVARIANT

    def test_all_equal(self):
        assert _ordering_consensus(["equal", "equal"]) == EH_INVARIANT

    def test_mixed_no_majority(self):
        assert _ordering_consensus(["greater", "lesser"]) == EH_SENSITIVE

    def test_two_agree_partial(self):
        assert _ordering_consensus(["greater", "greater", "lesser"]) == EH_PARTIAL

    def test_single_sufficient(self):
        # Single entry that is non-equal = invariant
        assert _ordering_consensus(["greater"]) == EH_INVARIANT

    def test_one_entry_insufficient(self):
        assert _ordering_consensus([]) == EH_INSUFFICIENT

    def test_empty_insufficient(self):
        assert _ordering_consensus([]) == EH_INSUFFICIENT


# ---------------------------------------------------------------------------
# _spread_ratio
# ---------------------------------------------------------------------------

class TestSpreadRatio:
    def test_zero_spread_same_values(self):
        ratio = _spread_ratio({"A": 1.0, "B": 1.0})
        assert ratio == 0.0

    def test_large_spread(self):
        ratio = _spread_ratio({"A": 0.2, "B": 1.0})
        assert ratio is not None and ratio > 0.5

    def test_single_encoding_returns_none(self):
        assert _spread_ratio({"A": 1.0}) is None

    def test_zero_mean_returns_none(self):
        assert _spread_ratio({"A": 0.0, "B": 0.0}) is None


# ---------------------------------------------------------------------------
# _classify_metric_at_horizon
# ---------------------------------------------------------------------------

class TestClassifyMetricAtHorizon:
    def test_insufficient_single_campaign(self):
        r = _classify_metric_at_horizon({"lh_A": [0.5, 0.6]}, "foo")
        assert r["classification"] == EH_INSUFFICIENT

    def test_invariant_when_campaigns_agree(self):
        # Two campaigns with very similar means
        r = _classify_metric_at_horizon(
            {"lh_A": [1.0, 1.0, 1.0], "lh_B": [1.0, 1.0, 1.0]}, "foo"
        )
        assert r["classification"] == EH_INVARIANT

    def test_sensitive_large_spread(self):
        # Campaigns with very different means → high spread
        r = _classify_metric_at_horizon(
            {"lh_A": [0.1, 0.1], "lh_B": [5.0, 5.0], "lh_C": [0.15, 0.15]}, "foo"
        )
        assert r["classification"] == EH_SENSITIVE

    def test_returns_spread_ratio(self):
        r = _classify_metric_at_horizon(
            {"lh_A": [1.0, 1.0], "lh_B": [3.0, 3.0]}, "foo"
        )
        assert r["spread_ratio"] is not None and r["spread_ratio"] > 0

    def test_n_campaigns_counted(self):
        r = _classify_metric_at_horizon(
            {"lh_A": [1.0], "lh_B": [1.1], "lh_C": [0.9]}, "foo"
        )
        assert r["n_campaigns"] == 3


# ---------------------------------------------------------------------------
# _classify_horizon_trend
# ---------------------------------------------------------------------------

class TestClassifyHorizonTrend:
    def test_consistent_invariant(self):
        assert (
            _classify_horizon_trend(
                {25: EH_INVARIANT, 50: EH_INVARIANT, 100: EH_INVARIANT}, EH_INVARIANT
            )
            == EH_TREND_CONSISTENT_INV
        )

    def test_consistent_sensitive(self):
        assert (
            _classify_horizon_trend(
                {25: EH_SENSITIVE, 100: EH_SENSITIVE}, EH_SENSITIVE
            )
            == EH_TREND_CONSISTENT_SEN
        )

    def test_stabilizing(self):
        # Stage 5 sensitive, gets better at long horizon
        assert (
            _classify_horizon_trend({100: EH_INVARIANT}, EH_SENSITIVE)
            == EH_TREND_STABILIZING
        )

    def test_worsening(self):
        # Stage 5 invariant, becomes sensitive at long horizon
        assert (
            _classify_horizon_trend({100: EH_SENSITIVE}, EH_INVARIANT)
            == EH_TREND_WORSENING
        )

    def test_insufficient_no_data(self):
        assert (
            _classify_horizon_trend({}, None)
            == EH_TREND_INSUFFICIENT
        )

    def test_insufficient_single_horizon_no_baseline(self):
        # One horizon, no stage5 baseline → insufficient
        assert (
            _classify_horizon_trend({25: EH_SENSITIVE}, None)
            == EH_TREND_INSUFFICIENT
        )


# ---------------------------------------------------------------------------
# run_encoding_horizon_interactions — synthetic fallback
# ---------------------------------------------------------------------------

class TestRunEncodingHorizonInteractions:
    def test_returns_dict_with_metrics(self, tmp_path):
        # No campaign data → synthetic fallback
        result = run_encoding_horizon_interactions(output_root=tmp_path / "empty")
        assert isinstance(result, dict)
        assert "metrics" in result
        assert len(result["metrics"]) > 0

    def test_synthetic_fallback_source(self, tmp_path):
        result = run_encoding_horizon_interactions(output_root=tmp_path / "empty2")
        assert result.get("data_source") == "synthetic_fallback"

    def test_synthetic_has_summary_keys(self, tmp_path):
        result = run_encoding_horizon_interactions(output_root=tmp_path / "empty3")
        summary = result["summary"]
        for key in ["consistently_invariant", "consistently_sensitive",
                    "stabilizing", "worsening", "insufficient_data"]:
            assert key in summary

    def test_synthetic_path_smoothness_invariant(self, tmp_path):
        result = run_encoding_horizon_interactions(output_root=tmp_path / "empty4")
        metrics = {m["metric"]: m for m in result["metrics"]}
        ps = metrics.get("path_smoothness")
        assert ps is not None
        assert ps["stage5_baseline_classification"] == EH_INVARIANT

    def test_synthetic_mean_position_error_sensitive(self, tmp_path):
        result = run_encoding_horizon_interactions(output_root=tmp_path / "empty5")
        metrics = {m["metric"]: m for m in result["metrics"]}
        mpe = metrics.get("mean_position_error")
        assert mpe is not None
        assert mpe["stage5_baseline_classification"] == EH_SENSITIVE

    def test_report_file_written(self, tmp_path):
        run_encoding_horizon_interactions(output_root=tmp_path)
        report_path = tmp_path / "encoding_horizon_report.json"
        assert report_path.exists()
        data = json.loads(report_path.read_text())
        assert "metrics" in data

    def test_live_data_used_when_available(self, tmp_path):
        # Create synthetic campaign output structure
        camp_dir = tmp_path / "lh_A" / "turns_25"
        camp_dir.mkdir(parents=True)
        agg = {
            "per_seed_results": [
                {"metrics": {"path_smoothness": 0.8, "stability_score": 0.7}},
                {"metrics": {"path_smoothness": 0.82, "stability_score": 0.68}},
            ]
        }
        (camp_dir / "aggregated_summary.json").write_text(json.dumps(agg))

        camp_dir2 = tmp_path / "lh_B" / "turns_25"
        camp_dir2.mkdir(parents=True)
        agg2 = {
            "per_seed_results": [
                {"metrics": {"path_smoothness": 0.79, "stability_score": 0.71}},
            ]
        }
        (camp_dir2 / "aggregated_summary.json").write_text(json.dumps(agg2))

        result = run_encoding_horizon_interactions(output_root=tmp_path)
        assert result.get("data_source") == "live_stage6_campaigns"
        assert 25 in result.get("horizons_evaluated", [])

    def test_safe_for_comparison_flag(self, tmp_path):
        result = run_encoding_horizon_interactions(output_root=tmp_path / "ef")
        metrics = result["metrics"]
        for m in metrics:
            assert "safe_for_cross_encoding_comparison" in m
            assert isinstance(m["safe_for_cross_encoding_comparison"], bool)

    def test_evaluated_metrics_list_nonempty(self):
        assert len(EVALUATED_METRICS) >= 6

    def test_summary_counts_nonnegative(self, tmp_path):
        result = run_encoding_horizon_interactions(output_root=tmp_path / "ef2")
        for v in result["summary"].values():
            assert v >= 0
