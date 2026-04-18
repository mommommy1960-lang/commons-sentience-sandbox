"""Tests for multi-run aggregation and cross-run consistency (Part 9 — Stage 3)."""

from __future__ import annotations

import math
from typing import Any, Dict, List

import pytest

from reality_audit.analysis.aggregate_experiments import (
    AGGREGATED_METRICS,
    _stats,
    _stability_flag,
    aggregate_runs,
    cross_run_consistency,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_run(seed: int, offset: float = 0.0) -> Dict[str, Any]:
    """Construct a synthetic run-result dict with deterministic metric values."""
    return {
        "run_id": f"proportional_seed{seed}_rot0.00",
        "seed": seed,
        "metrics": {
            "position_error": 1.0 + offset,
            "velocity_error": 0.5 + offset * 0.1,
            "stability_score": 0.3 + offset * 0.01,
            "anisotropy_score": 180.0 + offset,
            "observer_dependence_score": 0.0,
            "bandwidth_bottleneck_score": 1.0,
            "quantization_artifact_score": 0.0,
            "control_effort": 50.0 + offset,
            "path_smoothness": 0.35,
            "convergence_time": 3.0 + offset * 0.1,
        },
    }


IDENTICAL_RUNS = [_make_run(i) for i in range(5)]
VARIED_RUNS = [_make_run(i, offset=i * 2.0) for i in range(5)]


# ---------------------------------------------------------------------------
# Unit tests: _stats
# ---------------------------------------------------------------------------

class TestStats:
    def test_empty_returns_nan(self):
        s = _stats([])
        assert s["n"] == 0
        assert math.isnan(s["mean"])

    def test_single_value(self):
        s = _stats([3.0])
        assert s["mean"] == 3.0
        assert s["std"] == 0.0
        assert s["min"] == s["max"] == 3.0

    def test_mean_correct(self):
        s = _stats([1.0, 2.0, 3.0])
        assert abs(s["mean"] - 2.0) < 1e-9

    def test_std_correct(self):
        # population std of [1, 2, 3] = sqrt(2/3) ≈ 0.8165
        s = _stats([1.0, 2.0, 3.0])
        expected_std = (2 / 3) ** 0.5
        assert abs(s["std"] - expected_std) < 1e-6

    def test_ci_contains_mean_for_single(self):
        s = _stats([5.0])
        assert s["ci_lo"] <= s["mean"] <= s["ci_hi"]

    def test_consistency_score_is_1_for_identical(self):
        s = _stats([4.0, 4.0, 4.0])
        assert s["consistency_score"] == pytest.approx(1.0, abs=1e-6)

    def test_consistency_score_is_low_for_noisy(self):
        # Values spanning a very wide range relative to mean
        s = _stats([0.001, 10.0, 20.0, 30.0])
        assert s["consistency_score"] < 0.5


class TestStabilityFlag:
    def test_stable(self):
        assert _stability_flag(0.9) == "stable"

    def test_moderate(self):
        assert _stability_flag(0.6) == "moderate"

    def test_unstable(self):
        assert _stability_flag(0.3) == "unstable"

    def test_nan_returns_unknown(self):
        assert _stability_flag(float("nan")) == "unknown"


# ---------------------------------------------------------------------------
# aggregate_runs
# ---------------------------------------------------------------------------

class TestAggregateRuns:
    def test_produces_expected_fields(self):
        summary = aggregate_runs(IDENTICAL_RUNS, experiment_name="test")
        assert summary["experiment_name"] == "test"
        assert summary["n_runs"] == 5
        assert "metrics" in summary

    def test_all_aggregated_metrics_present(self):
        summary = aggregate_runs(IDENTICAL_RUNS)
        for m in AGGREGATED_METRICS:
            assert m in summary["metrics"], f"Missing metric: {m}"

    def test_identical_runs_give_zero_std(self):
        summary = aggregate_runs(IDENTICAL_RUNS)
        assert summary["metrics"]["position_error"]["std"] == pytest.approx(0.0, abs=1e-9)
        assert summary["metrics"]["position_error"]["consistency_score"] == pytest.approx(1.0, abs=1e-6)

    def test_varied_runs_give_nonzero_std(self):
        summary = aggregate_runs(VARIED_RUNS)
        assert summary["metrics"]["position_error"]["std"] > 0

    def test_stability_flag_present(self):
        summary = aggregate_runs(IDENTICAL_RUNS)
        for m in AGGREGATED_METRICS:
            assert "stability" in summary["metrics"][m]

    def test_writes_json_file(self, tmp_path):
        aggregate_runs(IDENTICAL_RUNS, output_dir=tmp_path)
        assert (tmp_path / "aggregated_summary.json").exists()

    def test_writes_csv_file(self, tmp_path):
        aggregate_runs(IDENTICAL_RUNS, output_dir=tmp_path)
        assert (tmp_path / "aggregated_summary.csv").exists()

    def test_ci_lo_less_than_ci_hi(self):
        summary = aggregate_runs(VARIED_RUNS)
        m = summary["metrics"]["position_error"]
        assert m["ci_lo"] <= m["ci_hi"]

    def test_min_max_correct(self):
        summary = aggregate_runs(VARIED_RUNS)
        m = summary["metrics"]["position_error"]
        # offset = i*2, values = 1.0, 3.0, 5.0, 7.0, 9.0
        assert m["min"] == pytest.approx(1.0, abs=1e-9)
        assert m["max"] == pytest.approx(9.0, abs=1e-9)


# ---------------------------------------------------------------------------
# cross_run_consistency
# ---------------------------------------------------------------------------

class TestCrossRunConsistency:
    def test_returns_all_metrics(self):
        c = cross_run_consistency(IDENTICAL_RUNS)
        for m in AGGREGATED_METRICS:
            assert m in c

    def test_identical_runs_are_stable(self):
        c = cross_run_consistency(IDENTICAL_RUNS)
        assert c["position_error"]["flag"] == "stable"

    def test_varied_runs_detect_instability(self):
        # Large offset => high std => lower consistency score
        very_varied = [_make_run(i, offset=i * 50.0) for i in range(5)]
        c = cross_run_consistency(very_varied)
        # position_error values: 1, 51, 101, 151, 201
        assert c["position_error"]["flag"] in ("moderate", "unstable")

    def test_consistency_score_in_range(self):
        c = cross_run_consistency(VARIED_RUNS)
        for m in AGGREGATED_METRICS:
            cs = c[m]["consistency_score"]
            if not math.isnan(cs):
                assert 0.0 <= cs <= 1.0, f"{m} cs={cs} out of range"
