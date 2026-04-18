"""Tests for governance_horizon_effects.py."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

from reality_audit.analysis.governance_horizon_effects import (
    _mean,
    _std,
    _cohens_d,
    classify_governance_effect,
    extract_gov_comparison,
    build_governance_horizon_entries,
    run_governance_horizon_effects,
    _build_synthetic_comparison_report,
    G_DOMINATED,
    G_MODULATED,
    G_NEUTRAL,
    G_INSUFFICIENT,
    EFFECT_THRESH,
)


# ---------------------------------------------------------------------------
# Math helpers
# ---------------------------------------------------------------------------

class TestMathHelpers:
    def test_mean_empty(self):
        assert _mean([]) == 0.0

    def test_std_single(self):
        assert _std([5.0]) == 0.0

    def test_cohens_d_none_on_empty(self):
        assert _cohens_d([], [1.0, 2.0]) is None

    def test_cohens_d_zero_variance(self):
        assert _cohens_d([3.0, 3.0], [3.0, 3.0]) == pytest.approx(0.0)

    def test_cohens_d_large(self):
        d = _cohens_d([9.0, 10.0, 11.0], [0.5, 1.0, 1.5])
        assert d is not None and abs(d) > 5.0


# ---------------------------------------------------------------------------
# classify_governance_effect
# ---------------------------------------------------------------------------

class TestClassifyGovernanceEffect:
    def test_none_delta_is_insufficient(self):
        assert classify_governance_effect("x", None, None, None) == G_INSUFFICIENT

    def test_small_effect_is_neutral(self):
        # d = 0.1 < EFFECT_THRESH = 0.4
        assert classify_governance_effect("x", 0.01, 0.1, None) == G_NEUTRAL

    def test_large_effect_dominated(self):
        # d >> EFFECT_THRESH, no FP threshold set
        assert classify_governance_effect("x", 5.0, 2.0, None) == G_DOMINATED

    def test_large_effect_but_below_fp_threshold(self):
        # delta is small fraction of fp_threshold -> modulated
        result = classify_governance_effect("x", 0.05, 0.60, 10.0)
        assert result == G_MODULATED

    def test_no_cohens_d_is_insufficient(self):
        assert classify_governance_effect("x", 1.0, None, None) == G_INSUFFICIENT


# ---------------------------------------------------------------------------
# extract_gov_comparison
# ---------------------------------------------------------------------------

class TestExtractGovComparison:
    def _report(self, turns=5):
        return {
            "comparisons_by_horizon": {
                str(turns): [
                    {
                        "label": "lh_A_vs_lh_B__gov_sensitivity",
                        "campaign_a": "lh_A",
                        "campaign_b": "lh_B",
                        "total_turns": turns,
                        "metrics": {"path_smoothness": {"delta": 0.01, "cohens_d": 0.05}},
                    }
                ]
            }
        }

    def test_finds_gov_comparison(self):
        report = self._report(5)
        result = extract_gov_comparison(report, 5)
        assert result is not None
        assert result["campaign_a"] == "lh_A"

    def test_missing_horizon_returns_none(self):
        report = self._report(5)
        result = extract_gov_comparison(report, 50)
        assert result is None

    def test_empty_report_returns_none(self):
        result = extract_gov_comparison({}, 5)
        assert result is None


# ---------------------------------------------------------------------------
# build_governance_horizon_entries
# ---------------------------------------------------------------------------

class TestBuildGovernanceHorizonEntries:
    def _comparison_report(self, turn_counts):
        report = _build_synthetic_comparison_report(turn_counts)
        return report

    def test_entries_for_each_metric(self):
        tc = [5, 25]
        report = self._comparison_report(tc)
        entries = build_governance_horizon_entries(report, tc)
        assert len(entries) > 0
        metrics = [e["metric"] for e in entries]
        assert "path_smoothness" in metrics

    def test_horizon_classifications_present(self):
        tc = [5, 25]
        report = self._comparison_report(tc)
        entries = build_governance_horizon_entries(report, tc)
        for e in entries:
            for t in tc:
                assert str(t) in e["horizon_classifications"]

    def test_neutral_at_all_horizons_short_runs(self):
        # At very short scale, all effects should be tiny -> neutral
        tc = [5]
        report = _build_synthetic_comparison_report(tc)
        entries = build_governance_horizon_entries(report, tc)
        # path_smoothness d=0.05*0.05=tiny -> neutral
        ps_entry = next(e for e in entries if e["metric"] == "path_smoothness")
        assert ps_entry["horizon_classifications"]["5"]["classification"] == G_NEUTRAL

    def test_sensitivity_emerges_at_100(self):
        tc = [100]
        report = _build_synthetic_comparison_report(tc)
        entries = build_governance_horizon_entries(report, tc)
        # avg_control_effort d=0.30 at t=100 -> should be detectable
        ce_entry = next(e for e in entries if e["metric"] == "avg_control_effort")
        assert ce_entry["horizon_classifications"]["100"]["classification"] in (
            G_MODULATED, G_DOMINATED, G_NEUTRAL  # depends on threshold
        )

    def test_empty_report_returns_empty(self):
        entries = build_governance_horizon_entries({}, [5])
        assert entries == []


# ---------------------------------------------------------------------------
# run_governance_horizon_effects
# ---------------------------------------------------------------------------

class TestRunGovernanceHorizonEffects:
    def test_writes_report_json(self, tmp_path):
        result = run_governance_horizon_effects(output_root=tmp_path)
        assert (tmp_path / "governance_horizon_report.json").exists()

    def test_returns_interpretation_key(self, tmp_path):
        result = run_governance_horizon_effects(output_root=tmp_path)
        assert "interpretation" in result

    def test_returns_n_metrics(self, tmp_path):
        result = run_governance_horizon_effects(output_root=tmp_path)
        assert result["n_metrics"] > 0

    def test_uses_synthetic_when_no_live_data(self, tmp_path):
        result = run_governance_horizon_effects(output_root=tmp_path)
        assert result["data_source"] == "synthetic_fallback"

    def test_uses_live_data_when_present(self, tmp_path):
        report = _build_synthetic_comparison_report([10, 20])
        (tmp_path / "campaign_comparison_report.json").write_text(json.dumps(report))
        result = run_governance_horizon_effects(output_root=tmp_path)
        assert result["data_source"] == "live"

    def test_neutral_at_all_horizons_key_present(self, tmp_path):
        result = run_governance_horizon_effects(output_root=tmp_path)
        assert "metrics_neutral_at_all_horizons" in result

    def test_sensitive_metrics_key_present(self, tmp_path):
        result = run_governance_horizon_effects(output_root=tmp_path)
        assert "metrics_showing_governance_sensitivity" in result

    def test_earliest_effect_horizon_key_present(self, tmp_path):
        result = run_governance_horizon_effects(output_root=tmp_path)
        assert "earliest_effect_horizon" in result
