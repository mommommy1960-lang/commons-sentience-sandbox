"""Tests for reality_audit/experiments/calibrated_campaigns.py"""
from __future__ import annotations

import csv
import json
import tempfile
from pathlib import Path
from typing import List
from unittest import mock

import pytest

from reality_audit.experiments.calibrated_campaigns import (
    _CAMPAIGN_DEFS,
    TRUSTED_METRICS,
    _mean,
    _std,
    _cohens_d,
    _compare_campaigns,
    build_campaign_comparison_report,
    run_campaign_single,
    aggregate_campaign,
    run_calibrated_campaigns,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class TestHelpers:
    def test_mean_empty(self):
        assert _mean([]) == 0.0

    def test_std_single(self):
        assert _std([3.0]) == 0.0

    def test_cohens_d_no_spread(self):
        assert _cohens_d([1.0, 1.0], [1.0, 1.0]) == 0.0

    def test_cohens_d_large_separation(self):
        d = _cohens_d([9.0, 10.0, 11.0], [0.5, 1.0, 1.5])
        assert d is not None and abs(d) > 1.0


# ---------------------------------------------------------------------------
# Campaign definitions
# ---------------------------------------------------------------------------

class TestCampaignDefs:
    def test_all_campaigns_defined(self):
        expected = {
            "campaign_A", "campaign_B", "campaign_C",
            "campaign_D_passive", "campaign_D_inactive",
            "campaign_E_passive", "campaign_E_active",
        }
        assert expected.issubset(_CAMPAIGN_DEFS.keys())

    def test_each_def_has_required_keys(self):
        for cid, defn in _CAMPAIGN_DEFS.items():
            assert "probe_mode" in defn, f"{cid} missing probe_mode"
            assert "params" in defn, f"{cid} missing params"

    def test_experimental_campaigns_marked(self):
        assert _CAMPAIGN_DEFS["campaign_E_passive"].get("experimental") is True
        assert _CAMPAIGN_DEFS["campaign_E_active"].get("experimental") is True

    def test_campaign_A_gov_on(self):
        assert not _CAMPAIGN_DEFS["campaign_A"].get("gov_off", False)

    def test_campaign_B_gov_off(self):
        assert _CAMPAIGN_DEFS["campaign_B"].get("gov_off") is True


# ---------------------------------------------------------------------------
# _compare_campaigns
# ---------------------------------------------------------------------------

class TestCompareCampaigns:
    def _make_summary(self, campaign_id: str, turns: List[int], val: float):
        from reality_audit.experiments.calibrated_campaigns import TRUSTED_METRICS, EXPERIMENTAL_METRICS
        agg = {}
        for t in turns:
            agg[t] = {m: {"mean": val, "std": 0.01, "n": 3} for m in TRUSTED_METRICS + EXPERIMENTAL_METRICS}
        return {
            "campaign_id": campaign_id,
            "label": campaign_id,
            "description": "",
            "probe_mode": "passive",
            "gov_off": False,
            "experimental": False,
            "turn_counts": turns,
            "aggregated": agg,
        }

    def test_compare_identical_no_meaningful(self):
        sa = self._make_summary("A", [25], 1.0)
        sb = self._make_summary("B", [25], 1.0)
        result = _compare_campaigns(sa, sb)
        for m_info in result[25].values():
            assert not m_info.get("meaningful", False)

    def test_compare_large_delta_meaningful(self):
        sa = self._make_summary("A", [25], 10.0)
        sb = self._make_summary("B", [25], 1.0)
        result = _compare_campaigns(sa, sb)
        assert any(v.get("meaningful") for v in result[25].values())


# ---------------------------------------------------------------------------
# Integration: mock out _run_simulation_with_probe
# ---------------------------------------------------------------------------

_FAKE_SUMMARY = {
    "path_smoothness": 0.4,
    "avg_control_effort": 0.02,
    "audit_bandwidth": 1.0,
    "stability_score": 0.5,
    "mean_position_error": 1.2,
    "observer_dependence_score": 0.0,
}


def _fake_run_sim(cfg, probe, run_dir):
    """Stub — don't call actual sandbox."""
    pass


def _fake_finalize(self):
    """Write a minimal summary.json and return the audit_dir."""
    audit_dir = self._output_dir / "reality_audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    with open(audit_dir / "summary.json", "w") as fh:
        json.dump(_FAKE_SUMMARY, fh)
    return audit_dir


class TestRunCampaignSingle:
    @pytest.fixture(autouse=True)
    def patch_sim(self):
        with mock.patch(
            "reality_audit.experiments.calibrated_campaigns._run_simulation_with_probe",
            side_effect=_fake_run_sim,
        ):
            with mock.patch(
                "reality_audit.adapters.sim_probe.SimProbe.finalize",
                _fake_finalize,
            ):
                yield

    def test_campaign_A_runs(self, tmp_path):
        result = run_campaign_single("campaign_A", 5, 0, output_root=tmp_path)
        assert result["campaign_id"] == "campaign_A"
        assert "probe_metrics" in result

    def test_inactive_probe_no_metrics(self, tmp_path):
        result = run_campaign_single("campaign_D_inactive", 5, 0, output_root=tmp_path)
        assert result["probe_metrics"] == {}

    def test_result_json_written(self, tmp_path):
        run_campaign_single("campaign_A", 5, 0, output_root=tmp_path)
        p = tmp_path / "campaign_A" / "turns_005" / "seed_00" / "campaign_result.json"
        assert p.exists()


class TestAggregateCampaign:
    @pytest.fixture(autouse=True)
    def patch_sim(self):
        with mock.patch(
            "reality_audit.experiments.calibrated_campaigns._run_simulation_with_probe",
            side_effect=_fake_run_sim,
        ):
            with mock.patch(
                "reality_audit.adapters.sim_probe.SimProbe.finalize",
                _fake_finalize,
            ):
                yield

    def test_aggregated_summary_written(self, tmp_path):
        aggregate_campaign("campaign_A", [5], 2, output_root=tmp_path)
        assert (tmp_path / "campaign_A" / "aggregated_summary.json").exists()

    def test_aggregated_keys_present(self, tmp_path):
        summary = aggregate_campaign("campaign_A", [5], 2, output_root=tmp_path)
        assert "aggregated" in summary
        assert 5 in summary["aggregated"]


class TestRunCalibratedCampaigns:
    @pytest.fixture(autouse=True)
    def patch_sim(self):
        with mock.patch(
            "reality_audit.experiments.calibrated_campaigns._run_simulation_with_probe",
            side_effect=_fake_run_sim,
        ):
            with mock.patch(
                "reality_audit.adapters.sim_probe.SimProbe.finalize",
                _fake_finalize,
            ):
                yield

    def test_comparison_report_written(self, tmp_path):
        run_calibrated_campaigns(turn_counts=[5], n_seeds=1, output_root=tmp_path)
        assert (tmp_path / "campaign_comparison_report.json").exists()

    def test_csv_written(self, tmp_path):
        run_calibrated_campaigns(turn_counts=[5], n_seeds=1, output_root=tmp_path)
        assert (tmp_path / "calibrated_campaigns_summary.csv").exists()

    def test_result_has_summaries_and_comparison(self, tmp_path):
        result = run_calibrated_campaigns(turn_counts=[5], n_seeds=1, output_root=tmp_path)
        assert "summaries" in result
        assert "comparison_report" in result

    def test_all_campaigns_in_summaries(self, tmp_path):
        result = run_calibrated_campaigns(turn_counts=[5], n_seeds=1, output_root=tmp_path)
        for cid in _CAMPAIGN_DEFS:
            assert cid in result["summaries"]
