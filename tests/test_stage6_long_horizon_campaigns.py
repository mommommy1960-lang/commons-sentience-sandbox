"""Tests for stage6_long_horizon_campaigns.py."""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from unittest import mock

import pytest

from reality_audit.experiments.stage6_long_horizon_campaigns import (
    _mean,
    _std,
    _cohens_d,
    _extract_metrics,
    _load_summary,
    run_single,
    aggregate_campaign_horizon,
    compare_campaigns_at_horizon,
    build_horizon_comparison_report,
    run_stage6_long_horizon_campaigns,
    _CAMPAIGN_DEFS,
    _COMPARISON_PAIRS,
    ALL_TRACKED_METRICS,
    STAGE6_TURN_COUNTS,
    STAGE6_N_SEEDS,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_summary() -> Dict[str, Any]:
    return {
        "path_smoothness": 0.6,
        "avg_control_effort": 0.5,
        "audit_bandwidth": 30.0,
        "stability_score": 0.7,
        "mean_position_error": 2.0,
        "anisotropy_score": 0.3,
        "observer_dependence_score": 5.0,
        "probe_mode": "passive",
    }


def _fake_run_result(campaign_id: str = "lh_A", turns: int = 5, seed: int = 0) -> Dict[str, Any]:
    s = _fake_summary()
    return {
        "campaign_id": campaign_id,
        "label": "test",
        "total_turns": turns,
        "seed": seed,
        "probe_mode": "passive",
        "gov_off": False,
        "experimental": False,
        "metrics": {m: s.get(m) for m in ALL_TRACKED_METRICS},
    }


# ---------------------------------------------------------------------------
# Unit tests — math helpers
# ---------------------------------------------------------------------------

class TestMeanStd:
    def test_mean_empty(self):
        assert _mean([]) == 0.0

    def test_mean_values(self):
        assert _mean([1.0, 3.0]) == pytest.approx(2.0)

    def test_std_single(self):
        assert _std([5.0]) == 0.0

    def test_std_two_values(self):
        assert _std([0.0, 2.0]) == pytest.approx(math.sqrt(2.0))

    def test_std_identical(self):
        assert _std([7.0, 7.0, 7.0]) == 0.0


class TestCohensD:
    def test_returns_none_empty(self):
        assert _cohens_d([], [1.0]) is None
        assert _cohens_d([1.0], []) is None

    def test_zero_variance(self):
        assert _cohens_d([3.0, 3.0], [3.0, 3.0]) == pytest.approx(0.0)

    def test_positive_direction(self):
        d = _cohens_d([9.0, 10.0, 11.0], [0.5, 1.0, 1.5])
        assert d is not None and d > 5.0

    def test_negative_direction(self):
        d = _cohens_d([0.5, 1.0, 1.5], [9.0, 10.0, 11.0])
        assert d is not None and d < -5.0

    def test_symmetric_magnitude(self):
        d1 = abs(_cohens_d([9.0, 10.0, 11.0], [0.5, 1.0, 1.5]))
        d2 = abs(_cohens_d([0.5, 1.0, 1.5], [9.0, 10.0, 11.0]))
        assert d1 == pytest.approx(d2, rel=1e-5)


# ---------------------------------------------------------------------------
# Campaign definitions
# ---------------------------------------------------------------------------

class TestCampaignDefs:
    def test_all_campaigns_have_required_keys(self):
        for cid, defn in _CAMPAIGN_DEFS.items():
            assert "label" in defn, cid
            assert "probe_mode" in defn, cid
            assert "params" in defn, cid
            assert "gov_off" in defn, cid

    def test_experimental_campaigns_labelled(self):
        experimental = [cid for cid, d in _CAMPAIGN_DEFS.items() if d.get("experimental")]
        assert len(experimental) >= 3  # D arms + F constrained

    def test_comparison_pairs_reference_valid_campaigns(self):
        for label, cid_a, cid_b in _COMPARISON_PAIRS:
            assert cid_a in _CAMPAIGN_DEFS, f"{cid_a} not in defs"
            assert cid_b in _CAMPAIGN_DEFS, f"{cid_b} not in defs"

    def test_at_least_six_campaigns_defined(self):
        assert len(_CAMPAIGN_DEFS) >= 6

    def test_governance_off_only_in_B(self):
        gov_off = [cid for cid, d in _CAMPAIGN_DEFS.items() if d.get("gov_off")]
        assert "lh_B" in gov_off
        assert "lh_A" not in gov_off


# ---------------------------------------------------------------------------
# Extract metrics
# ---------------------------------------------------------------------------

class TestExtractMetrics:
    def test_extracts_known_metrics(self):
        s = _fake_summary()
        result = _extract_metrics(s)
        assert "path_smoothness" in result
        assert result["path_smoothness"] == pytest.approx(0.6)

    def test_none_for_missing_keys(self):
        result = _extract_metrics({"path_smoothness": 0.5})
        assert result.get("stability_score") is None

    def test_none_summary(self):
        result = _extract_metrics(None)
        assert all(v is None for v in result.values())

    def test_all_tracked_metrics_present(self):
        result = _extract_metrics(_fake_summary())
        for m in ALL_TRACKED_METRICS:
            assert m in result


# ---------------------------------------------------------------------------
# run_single (mocked)
# ---------------------------------------------------------------------------

class TestRunSingle:
    def _patch(self, tmp_path):
        """Return a context manager that patches _run_simulation_with_probe and SimProbe.finalize."""
        fake_audit = tmp_path / "reality_audit"
        fake_audit.mkdir(parents=True, exist_ok=True)
        summary = _fake_summary()
        (fake_audit / "summary.json").write_text(json.dumps(summary))

        def _fake_finalize(self_probe):
            return fake_audit

        return mock.patch.multiple(
            "reality_audit.experiments.stage6_long_horizon_campaigns",
            _run_simulation_with_probe=mock.MagicMock(),
        ), mock.patch(
            "reality_audit.adapters.sim_probe.SimProbe.finalize",
            _fake_finalize,
        )

    def test_run_single_returns_metrics(self, tmp_path):
        fake_audit = tmp_path / "reality_audit"
        fake_audit.mkdir(parents=True, exist_ok=True)
        (fake_audit / "summary.json").write_text(json.dumps(_fake_summary()))

        with mock.patch(
            "reality_audit.experiments.stage6_long_horizon_campaigns._run_simulation_with_probe"
        ), mock.patch(
            "reality_audit.adapters.sim_probe.SimProbe.finalize",
            return_value=fake_audit,
        ):
            result = run_single("lh_A", total_turns=5, seed=0, output_root=tmp_path)

        assert result["campaign_id"] == "lh_A"
        assert result["total_turns"] == 5
        assert "path_smoothness" in result["metrics"]

    def test_run_single_inactive_probe_no_metrics(self, tmp_path):
        with mock.patch(
            "reality_audit.experiments.stage6_long_horizon_campaigns._run_simulation_with_probe"
        ), mock.patch(
            "reality_audit.adapters.sim_probe.SimProbe.finalize",
            return_value=tmp_path,
        ):
            result = run_single("lh_C_inactive", total_turns=5, seed=0, output_root=tmp_path)

        assert all(v is None for v in result["metrics"].values())

    def test_run_single_writes_metadata_json(self, tmp_path):
        fake_audit = tmp_path / "reality_audit"
        fake_audit.mkdir(parents=True, exist_ok=True)
        (fake_audit / "summary.json").write_text(json.dumps(_fake_summary()))

        with mock.patch(
            "reality_audit.experiments.stage6_long_horizon_campaigns._run_simulation_with_probe"
        ), mock.patch(
            "reality_audit.adapters.sim_probe.SimProbe.finalize",
            return_value=fake_audit,
        ):
            run_single("lh_A", total_turns=5, seed=1, output_root=tmp_path)

        meta_path = tmp_path / "lh_A" / "turns_5" / "seed_01" / "run_metadata.json"
        assert meta_path.exists()
        meta = json.loads(meta_path.read_text())
        assert meta["seed"] == 1


# ---------------------------------------------------------------------------
# aggregate_campaign_horizon (mocked)
# ---------------------------------------------------------------------------

class TestAggregateCampaignHorizon:
    def test_aggregation_keys(self, tmp_path):
        fake_run = _fake_run_result("lh_A", turns=5, seed=0)

        with mock.patch(
            "reality_audit.experiments.stage6_long_horizon_campaigns.run_single",
            return_value=fake_run,
        ):
            result = aggregate_campaign_horizon("lh_A", total_turns=5, n_seeds=2, output_root=tmp_path)

        assert result["campaign_id"] == "lh_A"
        assert result["total_turns"] == 5
        assert "aggregated_metrics" in result
        assert "path_smoothness" in result["aggregated_metrics"]

    def test_aggregation_writes_json(self, tmp_path):
        fake_run = _fake_run_result("lh_A", turns=5, seed=0)

        with mock.patch(
            "reality_audit.experiments.stage6_long_horizon_campaigns.run_single",
            return_value=fake_run,
        ):
            aggregate_campaign_horizon("lh_A", total_turns=5, n_seeds=2, output_root=tmp_path)

        out_path = tmp_path / "lh_A" / "aggregated_turns_5.json"
        assert out_path.exists()

    def test_aggregation_mean_computation(self, tmp_path):
        def _run(cid, turns, seed, root):
            r = _fake_run_result(cid, turns, seed)
            r["metrics"]["path_smoothness"] = float(seed) * 0.1 + 0.5
            return r

        with mock.patch(
            "reality_audit.experiments.stage6_long_horizon_campaigns.run_single",
            side_effect=_run,
        ):
            result = aggregate_campaign_horizon("lh_A", total_turns=5, n_seeds=3, output_root=tmp_path)

        agg = result["aggregated_metrics"]["path_smoothness"]
        assert agg["mean"] == pytest.approx(0.6, abs=1e-5)


# ---------------------------------------------------------------------------
# compare_campaigns_at_horizon
# ---------------------------------------------------------------------------

class TestCompareCampaignsAtHorizon:
    def _make_summaries(self, turns=5):
        def _agg(vals):
            return {"mean": _mean(vals), "std": _std(vals), "n": len(vals), "values": vals}

        def _make(metrics):
            return {
                "aggregated_metrics": {m: _agg([v]) for m, v in metrics.items()}
            }

        return {
            ("lh_A", turns): _make({"path_smoothness": 0.6, "avg_control_effort": 0.5,
                                     "audit_bandwidth": 30.0, "stability_score": 0.7,
                                     "mean_position_error": 2.0, "anisotropy_score": 0.3,
                                     "observer_dependence_score": 5.0}),
            ("lh_B", turns): _make({"path_smoothness": 0.5, "avg_control_effort": 0.8,
                                     "audit_bandwidth": 25.0, "stability_score": 0.6,
                                     "mean_position_error": 3.0, "anisotropy_score": 0.4,
                                     "observer_dependence_score": 6.0}),
        }

    def test_comparison_has_metrics_key(self):
        sums = self._make_summaries()
        result = compare_campaigns_at_horizon("test", "lh_A", "lh_B", sums, total_turns=5)
        assert "metrics" in result
        assert "path_smoothness" in result["metrics"]

    def test_comparison_sensitive_metrics_list(self):
        sums = self._make_summaries()
        result = compare_campaigns_at_horizon("test", "lh_A", "lh_B", sums, total_turns=5)
        assert isinstance(result["sensitive_metrics"], list)

    def test_comparison_missing_campaign(self):
        sums: Dict[Tuple[str, int], Any] = {}
        result = compare_campaigns_at_horizon("test", "lh_A", "lh_B", sums, total_turns=5)
        # Should not crash, all deltas should be None
        for m, v in result["metrics"].items():
            assert v["delta"] is None

    def test_comparison_delta_direction(self):
        sums = self._make_summaries()
        result = compare_campaigns_at_horizon("test", "lh_A", "lh_B", sums, total_turns=5)
        # lh_A has higher path_smoothness (0.6) vs lh_B (0.5) -> delta > 0
        assert result["metrics"]["path_smoothness"]["delta"] > 0


# ---------------------------------------------------------------------------
# build_horizon_comparison_report
# ---------------------------------------------------------------------------

class TestBuildHorizonComparisonReport:
    def test_returns_expected_keys(self):
        summaries: Dict[Tuple[str, int], Any] = {}
        result = build_horizon_comparison_report(summaries, turn_counts=[5, 10], campaign_id="lh_A")
        assert "campaign_id" in result
        assert "turn_counts" in result
        assert "metrics" in result

    def test_each_turn_count_present(self):
        def _agg(val):
            return {"mean": val, "std": 0.0, "n": 1, "values": [val]}
        summaries = {
            ("lh_A", 5): {"aggregated_metrics": {"path_smoothness": _agg(0.6)}},
            ("lh_A", 10): {"aggregated_metrics": {"path_smoothness": _agg(0.65)}},
        }
        result = build_horizon_comparison_report(summaries, turn_counts=[5, 10])
        ps = result["metrics"].get("path_smoothness", {})
        assert "5" in ps
        assert "10" in ps

    def test_missing_horizon_gracefully_absent(self):
        summaries: Dict[Tuple[str, int], Any] = {}
        result = build_horizon_comparison_report(summaries, turn_counts=[5, 25])
        # No crash; entries may be empty dicts
        for m in ALL_TRACKED_METRICS:
            assert m in result["metrics"]


# ---------------------------------------------------------------------------
# run_stage6_long_horizon_campaigns — integration (fast mocked)
# ---------------------------------------------------------------------------

class TestRunStage6LongHorizonCampaigns:
    def test_integration_mocked(self, tmp_path):
        fake_run = _fake_run_result("lh_A", turns=5, seed=0)

        with mock.patch(
            "reality_audit.experiments.stage6_long_horizon_campaigns.run_single",
            return_value=fake_run,
        ):
            result = run_stage6_long_horizon_campaigns(
                turn_counts=[5], n_seeds=1, output_root=tmp_path
            )

        assert "summaries" in result
        assert "comparison_report" in result
        assert "horizon_report" in result

    def test_writes_comparison_report_json(self, tmp_path):
        fake_run = _fake_run_result("lh_A", turns=5, seed=0)

        with mock.patch(
            "reality_audit.experiments.stage6_long_horizon_campaigns.run_single",
            return_value=fake_run,
        ):
            run_stage6_long_horizon_campaigns(
                turn_counts=[5], n_seeds=1, output_root=tmp_path
            )

        assert (tmp_path / "campaign_comparison_report.json").exists()

    def test_writes_horizon_report_json(self, tmp_path):
        fake_run = _fake_run_result("lh_A", turns=5, seed=0)

        with mock.patch(
            "reality_audit.experiments.stage6_long_horizon_campaigns.run_single",
            return_value=fake_run,
        ):
            run_stage6_long_horizon_campaigns(
                turn_counts=[5], n_seeds=1, output_root=tmp_path
            )

        assert (tmp_path / "horizon_comparison_report.json").exists()

    def test_writes_csv(self, tmp_path):
        fake_run = _fake_run_result("lh_A", turns=5, seed=0)

        with mock.patch(
            "reality_audit.experiments.stage6_long_horizon_campaigns.run_single",
            return_value=fake_run,
        ):
            run_stage6_long_horizon_campaigns(
                turn_counts=[5], n_seeds=1, output_root=tmp_path
            )

        assert (tmp_path / "stage6_campaigns_summary.csv").exists()

    def test_comparison_report_structure(self, tmp_path):
        fake_run = _fake_run_result("lh_A", turns=5, seed=0)

        with mock.patch(
            "reality_audit.experiments.stage6_long_horizon_campaigns.run_single",
            return_value=fake_run,
        ):
            result = run_stage6_long_horizon_campaigns(
                turn_counts=[5], n_seeds=1, output_root=tmp_path
            )

        comp_report = result["comparison_report"]
        assert "turn_counts" in comp_report
        assert "comparisons_by_horizon" in comp_report
        assert "5" in comp_report["comparisons_by_horizon"]
