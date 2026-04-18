"""Tests for long_horizon_read_only.py."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

from reality_audit.validation.long_horizon_read_only import (
    _mean,
    _std,
    _relative_diff,
    _levenshtein_fraction,
    compare_probe_summaries,
    run_long_horizon_read_only_validation,
    _build_synthetic_validation_data,
    RO_SUPPORTED,
    RO_NO_EVIDENCE,
    RO_INCONCLUSIVE,
    RO_DIVERGENCE,
    DISTRIBUTIONAL_FIELDS,
    EXACT_MATCH_FIELDS,
)


# ---------------------------------------------------------------------------
# Math utilities
# ---------------------------------------------------------------------------

class TestMathUtils:
    def test_mean_empty(self):
        assert _mean([]) == 0.0

    def test_mean_values(self):
        assert _mean([2.0, 4.0]) == pytest.approx(3.0)

    def test_relative_diff_equal(self):
        assert _relative_diff(1.0, 1.0) == pytest.approx(0.0)

    def test_relative_diff_different(self):
        d = _relative_diff(1.0, 2.0)
        assert d == pytest.approx(0.5)

    def test_relative_diff_none_input(self):
        assert _relative_diff(None, 1.0) is None
        assert _relative_diff(1.0, None) is None


# ---------------------------------------------------------------------------
# Levenshtein fraction
# ---------------------------------------------------------------------------

class TestLevenshteinFraction:
    def test_identical_sequences(self):
        assert _levenshtein_fraction(["A", "B", "C"], ["A", "B", "C"]) == pytest.approx(0.0)

    def test_completely_different(self):
        f = _levenshtein_fraction(["A", "B"], ["C", "D"])
        assert f > 0.5

    def test_empty_sequences(self):
        assert _levenshtein_fraction([], []) == pytest.approx(0.0)

    def test_one_empty(self):
        f = _levenshtein_fraction(["A", "B", "C"], [])
        assert f == pytest.approx(1.0)

    def test_fraction_bounded_01(self):
        f = _levenshtein_fraction(["A", "B", "C", "D"], ["B", "C", "X", "Y"])
        assert 0.0 <= f <= 1.0


# ---------------------------------------------------------------------------
# compare_probe_summaries
# ---------------------------------------------------------------------------

class TestCompareProbesSummaries:
    def _identical_summaries(self):
        return {
            "path_smoothness": 0.60,
            "avg_control_effort": 0.50,
            "stability_score": 0.70,
            "mean_position_error": 2.0,
            "audit_bandwidth": 30.0,
            "goal_room": "nexus",
            "total_records": 50,
        }

    def test_identical_summaries_supported(self):
        s = self._identical_summaries()
        result = compare_probe_summaries(s, s.copy(), total_turns=25)
        assert result["overall_classification"] == RO_SUPPORTED
        assert result["n_divergences"] == 0

    def test_none_inactive_no_evidence(self):
        s = self._identical_summaries()
        result = compare_probe_summaries(s, None, total_turns=25)
        assert result["overall_classification"] == RO_NO_EVIDENCE

    def test_large_distributional_divergence(self):
        s_p = self._identical_summaries()
        s_i = self._identical_summaries()
        s_i["path_smoothness"] = 0.10  # large delta
        s_i["stability_score"] = 0.10
        s_i["mean_position_error"] = 20.0
        result = compare_probe_summaries(s_p, s_i, total_turns=25)
        assert result["overall_classification"] == RO_DIVERGENCE

    def test_small_distributional_difference_inconclusive_or_supported(self):
        s_p = self._identical_summaries()
        s_i = self._identical_summaries()
        s_i["path_smoothness"] = 0.61  # tiny difference
        result = compare_probe_summaries(s_p, s_i, total_turns=25)
        assert result["overall_classification"] in (RO_SUPPORTED, RO_INCONCLUSIVE)

    def test_result_has_distributional_details(self):
        s = self._identical_summaries()
        result = compare_probe_summaries(s, s.copy(), total_turns=25)
        assert "distributional_details" in result
        for field in DISTRIBUTIONAL_FIELDS:
            assert field in result["distributional_details"]

    def test_exact_match_divergence_goal_room(self):
        s_p = self._identical_summaries()
        s_i = self._identical_summaries()
        s_i["goal_room"] = "vault"  # different!
        result = compare_probe_summaries(s_p, s_i, total_turns=25)
        assert "goal_room" in result["exact_match_divergences"]

    def test_path_history_comparison_identical(self):
        s_p = self._identical_summaries()
        s_p["path_history"] = ["A", "B", "C"]
        s_i = s_p.copy()
        s_i["path_history"] = ["A", "B", "C"]
        result = compare_probe_summaries(s_p, s_i, total_turns=25)
        assert result["path_similarity"]["status"] == "similar"

    def test_path_history_comparison_diverged(self):
        s_p = self._identical_summaries()
        s_p["path_history"] = ["A", "B", "C", "D", "E"]
        s_i = s_p.copy()
        s_i["path_history"] = ["X", "Y", "Z", "W", "V"]  # completely different
        result = compare_probe_summaries(s_p, s_i, total_turns=25)
        assert result["path_similarity"]["status"] == "diverged"


# ---------------------------------------------------------------------------
# _build_synthetic_validation_data
# ---------------------------------------------------------------------------

class TestBuildSyntheticValidationData:
    def test_returns_one_entry_per_horizon(self):
        results = _build_synthetic_validation_data([25, 50, 100])
        assert len(results) == 3
        turns = {r["total_turns"] for r in results}
        assert turns == {25, 50, 100}

    def test_each_result_has_comparison(self):
        results = _build_synthetic_validation_data([25])
        assert "comparison" in results[0]
        assert "overall_classification" in results[0]["comparison"]

    def test_synthetic_results_generally_supported(self):
        # Synthetic data models close-to-identical runs, so should not diverge
        results = _build_synthetic_validation_data([25, 50, 100])
        for r in results:
            assert r["comparison"]["overall_classification"] in (
                RO_SUPPORTED, RO_NO_EVIDENCE, RO_INCONCLUSIVE
            )


# ---------------------------------------------------------------------------
# run_long_horizon_read_only_validation
# ---------------------------------------------------------------------------

class TestRunLongHorizonReadOnlyValidation:
    def test_writes_report_json(self, tmp_path):
        result = run_long_horizon_read_only_validation(
            turn_counts=[10], n_seeds=1, output_root=tmp_path
        )
        assert (tmp_path / "long_horizon_read_only_report.json").exists()

    def test_returns_overall_verdict(self, tmp_path):
        result = run_long_horizon_read_only_validation(
            turn_counts=[10], n_seeds=1, output_root=tmp_path
        )
        assert "overall_verdict" in result
        assert result["overall_verdict"] in (
            RO_SUPPORTED, RO_NO_EVIDENCE, RO_INCONCLUSIVE, RO_DIVERGENCE
        )

    def test_returns_per_horizon(self, tmp_path):
        result = run_long_horizon_read_only_validation(
            turn_counts=[10, 20], n_seeds=1, output_root=tmp_path
        )
        assert "per_horizon" in result
        assert len(result["per_horizon"]) == 2

    def test_uses_synthetic_when_no_live_data(self, tmp_path):
        result = run_long_horizon_read_only_validation(
            turn_counts=[10], n_seeds=1, output_root=tmp_path
        )
        assert result["data_source"] == "synthetic_fallback"

    def test_uses_live_data_when_metadata_present(self, tmp_path):
        # Write fake run_metadata.json for lh_C_passive
        meta_dir = tmp_path / "lh_C_passive" / "turns_10" / "seed_00"
        meta_dir.mkdir(parents=True)
        meta = {
            "campaign_id": "lh_C_passive",
            "metrics": {
                "path_smoothness": 0.60,
                "avg_control_effort": 0.50,
                "stability_score": 0.70,
                "mean_position_error": 2.0,
                "audit_bandwidth": 30.0,
            },
        }
        (meta_dir / "run_metadata.json").write_text(json.dumps(meta))
        result = run_long_horizon_read_only_validation(
            turn_counts=[10], n_seeds=1, output_root=tmp_path
        )
        assert result["data_source"] == "live"

    def test_returns_interpretation_string(self, tmp_path):
        result = run_long_horizon_read_only_validation(
            turn_counts=[10], n_seeds=1, output_root=tmp_path
        )
        assert isinstance(result.get("interpretation"), str)
        assert len(result["interpretation"]) > 10
