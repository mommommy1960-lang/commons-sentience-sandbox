"""Tests for reality_audit/experiments/ablation_studies.py"""
from __future__ import annotations

import csv
import json
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from reality_audit.experiments.ablation_studies import (
    SUMMARY_METRICS,
    _mean,
    _std,
    _cohens_d,
    _extract_metrics,
    _compare_arms,
    run_ablation_governance,
    run_ablation_probe_mode,
    run_ablation_agent_type,
    run_ablation_bandwidth,
    run_ablation_cooperation,
    run_all_ablations,
)
from reality_audit.adapters.sim_probe import PROBE_MODE_PASSIVE


# ---------------------------------------------------------------------------
# Helper math tests
# ---------------------------------------------------------------------------

class TestHelpers:
    def test_mean_empty(self):
        assert _mean([]) == 0.0

    def test_mean_basic(self):
        assert _mean([1.0, 3.0]) == 2.0

    def test_std_single(self):
        assert _std([5.0]) == 0.0

    def test_std_uniform(self):
        assert _std([2.0, 2.0, 2.0]) == 0.0

    def test_std_known(self):
        result = _std([1.0, 3.0])
        assert abs(result - 1.4142135623) < 1e-6

    def test_cohens_d_equal_groups(self):
        d = _cohens_d([1.0, 1.0, 1.0], [1.0, 1.0, 1.0])
        assert d == 0.0

    def test_cohens_d_empty_group(self):
        assert _cohens_d([], [1.0]) is None

    def test_cohens_d_positive(self):
        d = _cohens_d([3.0, 4.0, 5.0], [1.0, 1.0, 1.0])
        assert d is not None and d > 0

    def test_extract_metrics_from_none(self):
        result = _extract_metrics(None)
        assert all(v is None for v in result.values())

    def test_extract_metrics_from_dict(self):
        result = _extract_metrics({"mean_position_error": 2.5, "stability_score": 0.7})
        assert result["mean_position_error"] == 2.5
        assert result["stability_score"] == 0.7

    def test_extract_metrics_missing_keys_return_none(self):
        result = _extract_metrics({"mean_position_error": 1.0})
        assert result["stability_score"] is None


# ---------------------------------------------------------------------------
# _compare_arms
# ---------------------------------------------------------------------------

class TestCompareArms:
    def _make_results(self, n: int, value: float):
        return [{m: value for m in SUMMARY_METRICS} for _ in range(n)]

    def test_returns_required_keys(self):
        a = self._make_results(3, 1.0)
        b = self._make_results(3, 1.0)
        result = _compare_arms("A", "B", a, b)
        assert "label_a" in result
        assert "label_b" in result
        assert "sensitive_metrics" in result
        assert "metrics" in result

    def test_no_movement_when_identical(self):
        a = self._make_results(3, 1.0)
        b = self._make_results(3, 1.0)
        result = _compare_arms("A", "B", a, b)
        assert result["sensitive_metrics"] == []

    def test_movement_detected_when_large_delta(self):
        a = [{m: 0.0 for m in SUMMARY_METRICS} for _ in range(3)]
        b = [{m: 1.0 for m in SUMMARY_METRICS} for _ in range(3)]
        result = _compare_arms("A", "B", a, b)
        assert len(result["sensitive_metrics"]) > 0

    def test_insufficient_data_handled(self):
        a = [{m: None for m in SUMMARY_METRICS}]
        b = [{m: None for m in SUMMARY_METRICS}]
        result = _compare_arms("A", "B", a, b)
        for m, info in result["metrics"].items():
            assert info["moved_meaningfully"] is False


# ---------------------------------------------------------------------------
# Integration tests — mock the sandbox
# ---------------------------------------------------------------------------

def _fake_run_one_passthrough(*args, **kwargs):
    """Stub _run_one to return synthetic metrics without running the full sandbox."""
    return {
        "mean_position_error": 1.0,
        "stability_score": 0.5,
        "avg_control_effort": 0.02,
        "path_smoothness": 0.4,
        "observer_dependence_score": 0.0,
        "audit_bandwidth": 1.0,
    }


class TestAblationRunners:
    @pytest.fixture(autouse=True)
    def patch_run_one(self):
        with mock.patch(
            "reality_audit.experiments.ablation_studies._run_one",
            side_effect=_fake_run_one_passthrough,
        ):
            yield

    def test_run_ablation_governance(self, tmp_path):
        result = run_ablation_governance(total_turns=5, n_seeds=2, output_root=tmp_path)
        assert "label_a" in result
        assert "metrics" in result

    def test_run_ablation_probe_mode(self, tmp_path):
        result = run_ablation_probe_mode(total_turns=5, n_seeds=2, output_root=tmp_path)
        assert result["label_a"] == "probe_passive"

    def test_run_ablation_agent_type(self, tmp_path):
        result = run_ablation_agent_type(total_turns=5, n_seeds=2, output_root=tmp_path)
        assert result["label_a"] == "normal_agent"

    def test_run_ablation_bandwidth(self, tmp_path):
        result = run_ablation_bandwidth(total_turns=5, n_seeds=2, output_root=tmp_path)
        assert result["label_a"] == "bandwidth_unconstrained"

    def test_run_ablation_cooperation(self, tmp_path):
        result = run_ablation_cooperation(total_turns=5, n_seeds=2, output_root=tmp_path)
        assert "cooperation" in result["label_a"].lower()


class TestRunAllAblations:
    @pytest.fixture(autouse=True)
    def patch_run_one(self):
        with mock.patch(
            "reality_audit.experiments.ablation_studies._run_one",
            side_effect=_fake_run_one_passthrough,
        ):
            yield

    def test_all_ablations_present(self, tmp_path):
        report = run_all_ablations(total_turns=5, n_seeds=2, output_root=tmp_path)
        expected = {"governance", "probe_mode", "agent_type", "bandwidth", "cooperation", "encoding_variant"}
        assert expected.issubset(report["ablations"].keys())

    def test_report_json_written(self, tmp_path):
        run_all_ablations(total_turns=5, n_seeds=2, output_root=tmp_path)
        assert (tmp_path / "ablation_report.json").exists()

    def test_csv_written(self, tmp_path):
        run_all_ablations(total_turns=5, n_seeds=2, output_root=tmp_path)
        assert (tmp_path / "ablation_summary.csv").exists()

    def test_csv_has_rows(self, tmp_path):
        run_all_ablations(total_turns=5, n_seeds=2, output_root=tmp_path)
        with open(tmp_path / "ablation_summary.csv", newline="") as fh:
            rows = list(csv.DictReader(fh))
        assert len(rows) > 0

    def test_encoding_variant_note_present(self, tmp_path):
        report = run_all_ablations(total_turns=5, n_seeds=2, output_root=tmp_path)
        enc = report["ablations"]["encoding_variant"]
        assert "note" in enc or "sensitive_metrics" in enc
