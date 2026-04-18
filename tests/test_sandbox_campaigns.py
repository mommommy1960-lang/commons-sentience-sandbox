"""
tests/test_sandbox_campaigns.py — Tests for sandbox_campaigns.py (Stage 4 Part 1).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT))

from reality_audit.experiments.sandbox_campaigns import (
    _make_config,
    _CONFIG_A_PARAMS,
    _CONFIG_B_PARAMS,
    _CONFIG_C_PARAMS,
    _CONFIG_D_PARAMS,
    _CONFIG_E_PARAMS,
    _CONFIG_F_PARAMS,
    run_single_campaign,
    run_config_a,
    run_all_campaigns,
    CAMPAIGN_TURN_COUNTS,
)
from reality_audit.adapters.sim_probe import (
    PROBE_MODE_PASSIVE,
    PROBE_MODE_INACTIVE,
    PROBE_MODE_ACTIVE_MEASUREMENT,
)


# ---------------------------------------------------------------------------
# Config building
# ---------------------------------------------------------------------------

class TestMakeConfig:
    def test_returns_experiment_config(self):
        cfg = _make_config(_CONFIG_A_PARAMS, 10)
        assert cfg.total_turns == 10

    def test_governance_strictness_preserved(self):
        cfg = _make_config(_CONFIG_B_PARAMS, 5)
        assert cfg.governance_strictness == 1.5

    def test_relaxed_governance_strictness(self):
        cfg = _make_config(_CONFIG_C_PARAMS, 5)
        assert cfg.governance_strictness == 0.5

    def test_low_cooperation_config(self):
        cfg = _make_config(_CONFIG_F_PARAMS, 5)
        assert cfg.cooperation_bias == pytest.approx(0.1)
        assert cfg.initial_agent_trust == pytest.approx(0.3)

    def test_all_config_names_set(self):
        for params in [_CONFIG_A_PARAMS, _CONFIG_B_PARAMS, _CONFIG_C_PARAMS,
                       _CONFIG_D_PARAMS, _CONFIG_E_PARAMS, _CONFIG_F_PARAMS]:
            cfg = _make_config(params, 3)
            assert cfg.name.startswith("sc_")


# ---------------------------------------------------------------------------
# Single campaign run
# ---------------------------------------------------------------------------

class TestRunSingleCampaign:
    def test_run_returns_dict(self, tmp_path):
        result = run_single_campaign(
            _CONFIG_A_PARAMS, total_turns=3, seed=0,
            probe_mode=PROBE_MODE_PASSIVE, output_root=tmp_path,
        )
        assert isinstance(result, dict)

    def test_result_has_required_keys(self, tmp_path):
        result = run_single_campaign(
            _CONFIG_A_PARAMS, total_turns=3, seed=0,
            probe_mode=PROBE_MODE_PASSIVE, output_root=tmp_path,
        )
        required = ["config_name", "probe_mode", "total_turns", "seed",
                    "probe_metrics", "audit_dir"]
        for key in required:
            assert key in result, f"Missing key: {key}"

    def test_passive_probe_collects_metrics(self, tmp_path):
        result = run_single_campaign(
            _CONFIG_A_PARAMS, total_turns=3, seed=1,
            probe_mode=PROBE_MODE_PASSIVE, output_root=tmp_path,
        )
        pm = result["probe_metrics"]
        assert "mean_position_error" in pm
        assert "stability_score" in pm
        assert "path_smoothness" in pm

    def test_inactive_probe_no_metrics(self, tmp_path):
        result = run_single_campaign(
            _CONFIG_D_PARAMS, total_turns=3, seed=0,
            probe_mode=PROBE_MODE_INACTIVE, output_root=tmp_path,
        )
        pm = result["probe_metrics"]
        assert "note" in pm
        assert "inactive" in pm["note"].lower()

    def test_active_measurement_probe_runs(self, tmp_path):
        result = run_single_campaign(
            _CONFIG_E_PARAMS, total_turns=3, seed=0,
            probe_mode=PROBE_MODE_ACTIVE_MEASUREMENT, output_root=tmp_path,
        )
        pm = result["probe_metrics"]
        assert "audit_bandwidth" in pm
        # In active measurement mode, audit_bandwidth may be < 1.0
        bw = pm.get("audit_bandwidth", 1.0)
        assert 0.0 <= bw <= 1.0

    def test_campaign_result_json_written(self, tmp_path):
        run_single_campaign(
            _CONFIG_A_PARAMS, total_turns=3, seed=0,
            probe_mode=PROBE_MODE_PASSIVE, output_root=tmp_path,
        )
        result_files = list(tmp_path.rglob("campaign_result.json"))
        assert len(result_files) >= 1

    def test_different_seeds_produce_independent_runs(self, tmp_path):
        r0 = run_single_campaign(
            _CONFIG_A_PARAMS, total_turns=3, seed=0,
            probe_mode=PROBE_MODE_PASSIVE, output_root=tmp_path,
        )
        r1 = run_single_campaign(
            _CONFIG_A_PARAMS, total_turns=3, seed=1,
            probe_mode=PROBE_MODE_PASSIVE, output_root=tmp_path,
        )
        # Same config but different seed → different audit dirs
        assert r0["audit_dir"] != r1["audit_dir"]

    def test_config_f_low_cooperation(self, tmp_path):
        result = run_single_campaign(
            _CONFIG_F_PARAMS, total_turns=3, seed=0,
            probe_mode=PROBE_MODE_PASSIVE, output_root=tmp_path,
        )
        assert result["cooperation_bias"] == pytest.approx(0.1)
        assert result["initial_agent_trust"] == pytest.approx(0.3)


# ---------------------------------------------------------------------------
# run_config_a convenience function
# ---------------------------------------------------------------------------

class TestRunConfigA:
    def test_returns_list(self, tmp_path):
        results = run_config_a(total_turns=3, n_seeds=2, output_root=tmp_path)
        assert isinstance(results, list)
        assert len(results) == 2

    def test_seeds_are_sequential(self, tmp_path):
        results = run_config_a(total_turns=3, n_seeds=3, output_root=tmp_path)
        seeds = [r["seed"] for r in results]
        assert seeds == [0, 1, 2]


# ---------------------------------------------------------------------------
# run_all_campaigns
# ---------------------------------------------------------------------------

class TestRunAllCampaigns:
    def test_all_configs_present(self, tmp_path):
        results = run_all_campaigns(
            turn_counts=[3], n_seeds=1, output_root=tmp_path
        )
        expected = [
            "sc_baseline", "sc_strict_governance", "sc_relaxed_governance",
            "sc_probe_inactive", "sc_active_measurement", "sc_low_cooperation",
        ]
        for cfg in expected:
            assert cfg in results, f"Missing config: {cfg}"

    def test_report_json_written(self, tmp_path):
        run_all_campaigns(turn_counts=[3], n_seeds=1, output_root=tmp_path)
        report = tmp_path / "sandbox_campaigns_report.json"
        assert report.exists()

    def test_report_json_valid(self, tmp_path):
        run_all_campaigns(turn_counts=[3], n_seeds=1, output_root=tmp_path)
        with open(tmp_path / "sandbox_campaigns_report.json") as fh:
            data = json.load(fh)
        assert "sc_baseline" in data
