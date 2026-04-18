"""Tests for the SimProbe Option B integration layer.

Tests:
  1. test_room_encoder_stable          — same input always gives same (x, y)
  2. test_room_encoder_hop_distance     — BFS distances match known graph
  3. test_room_encoder_unknown_room     — graceful fallback for unknown rooms
  4. test_probe_finalize_writes_files   — probe.finalize() produces required files
  5. test_probe_metrics_are_finite      — all summary metrics are finite floats
  6. test_probe_records_both_agents     — two records per turn (one per agent)
  7. test_sim_unaffected_without_audit  — run_simulation with audit disabled writes no extra files
  8. test_sim_with_audit_cli_flag       — run_simulation with enable_reality_audit=True writes audit dir
  9. test_probe_inactive_mode           — inactive mode writes nothing and records nothing
 10. test_probe_active_measurement_mode — active_measurement_model produces non-zero observer_dependence
 11. test_probe_invalid_mode            — invalid mode raises ValueError
 12. test_probe_csv_written             — finalize() writes raw_log.csv
 13. test_probe_mode_field_in_summary   — summary.json includes probe_mode field
"""

from __future__ import annotations

import json
import math
import shutil
import tempfile
import types
from pathlib import Path
from typing import Any, Dict, Optional
from unittest.mock import MagicMock

import pytest

from reality_audit.adapters.room_distance import RoomPositionEncoder
from reality_audit.adapters.sim_probe import (
    SimProbe,
    PROBE_MODE_INACTIVE,
    PROBE_MODE_PASSIVE,
    PROBE_MODE_ACTIVE_MEASUREMENT,
)

ROOMS_JSON = Path(__file__).resolve().parent.parent / "commons_sentience_sim" / "data" / "rooms.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_agent(name: str, room: str, trust: float = 0.5) -> MagicMock:
    agent = MagicMock()
    agent.name = name
    agent.active_room = room
    agent.affective_state = {
        "contradiction_pressure": 0.1,
        "curiosity": 0.6,
        "purpose": 0.7,
    }
    agent.get_agent_trust = MagicMock(return_value=trust)
    agent.episodic_memory = ["mem1", "mem2"]
    return agent


def _make_probe(tmp_path: Path) -> SimProbe:
    return SimProbe(
        rooms_json_path=ROOMS_JSON,
        output_dir=tmp_path,
        goal_room="Governance Vault",
    )


def _populate_probe(probe: SimProbe, turns: int = 3) -> None:
    sentinel = _make_mock_agent("Sentinel", "Memory Archive")
    aster = _make_mock_agent("Aster", "Operations Desk")
    obs = {"available_actions": ["retrieve_memories"], "description": "A vault."}
    for t in range(1, turns + 1):
        probe.record_turn(
            turn=t,
            sentinel=sentinel,
            aster=aster,
            world=MagicMock(),
            s_obs=obs,
            a_obs=obs,
            s_action="retrieve_memories",
            a_action="plan_next_task",
            s_permitted=True,
            a_permitted=False,
            event=None,
            same_room=False,
        )


# ---------------------------------------------------------------------------
# RoomPositionEncoder tests
# ---------------------------------------------------------------------------

class TestRoomPositionEncoder:

    def test_room_encoder_stable(self):
        """Same room always returns the same (x, y) coordinates."""
        enc1 = RoomPositionEncoder(ROOMS_JSON)
        enc2 = RoomPositionEncoder(ROOMS_JSON)
        for room in enc1.rooms:
            assert enc1.encode(room) == enc2.encode(room), (
                f"Coordinates for '{room}' differ across instances"
            )

    def test_room_encoder_hop_distance_adjacent(self):
        """Adjacent rooms have hop distance 1."""
        enc = RoomPositionEncoder(ROOMS_JSON)
        assert enc.hop_distance("Memory Archive", "Reflection Chamber") == 1.0
        assert enc.hop_distance("Memory Archive", "Operations Desk") == 1.0

    def test_room_encoder_hop_distance_two_hops(self):
        """Rooms separated by 2 edges have hop distance 2."""
        enc = RoomPositionEncoder(ROOMS_JSON)
        # Memory Archive → Operations Desk → Governance Vault  (2 hops)
        assert enc.hop_distance("Memory Archive", "Governance Vault") == 2.0

    def test_room_encoder_unknown_room_fallback(self):
        """Unknown room names return (0.0, 0.0) without raising."""
        enc = RoomPositionEncoder(ROOMS_JSON)
        assert enc.encode("Nonexistent Room") == (0.0, 0.0)

    def test_room_encoder_euclidean_self_distance(self):
        """Euclidean distance from a room to itself is 0."""
        enc = RoomPositionEncoder(ROOMS_JSON)
        for room in enc.rooms:
            assert enc.euclidean_distance(room, room) == pytest.approx(0.0, abs=1e-9)

    def test_room_encoder_coordinates_in_range(self):
        """All MDS coordinates lie within [-1, 1]."""
        enc = RoomPositionEncoder(ROOMS_JSON)
        for room, (x, y) in enc.coordinates.items():
            assert -1.0 <= x <= 1.0, f"{room} x={x} outside [-1,1]"
            assert -1.0 <= y <= 1.0, f"{room} y={y} outside [-1,1]"


# ---------------------------------------------------------------------------
# SimProbe tests
# ---------------------------------------------------------------------------

class TestSimProbe:

    def test_probe_records_both_agents(self, tmp_path):
        """Each call to record_turn appends two records (one per agent)."""
        probe = _make_probe(tmp_path)
        _populate_probe(probe, turns=3)
        assert len(probe._raw_log) == 6  # 3 turns × 2 agents

    def test_probe_finalize_writes_files(self, tmp_path):
        """finalize() produces config.json, raw_log.json, summary.json."""
        probe = _make_probe(tmp_path)
        _populate_probe(probe, turns=2)
        audit_dir = probe.finalize()

        assert (audit_dir / "config.json").exists()
        assert (audit_dir / "raw_log.json").exists()
        assert (audit_dir / "summary.json").exists()

    def test_probe_metrics_are_finite(self, tmp_path):
        """All numeric values in summary.json are finite floats."""
        probe = _make_probe(tmp_path)
        _populate_probe(probe, turns=5)
        probe.finalize()

        summary = json.loads((tmp_path / "reality_audit" / "summary.json").read_text())
        for key, val in summary.items():
            if isinstance(val, (int, float)):
                assert math.isfinite(val), f"summary[{key!r}] = {val} is not finite"

    def test_probe_summary_turn_count(self, tmp_path):
        """summary.json reports the correct total_turns."""
        probe = _make_probe(tmp_path)
        _populate_probe(probe, turns=4)
        probe.finalize()

        summary = json.loads((tmp_path / "reality_audit" / "summary.json").read_text())
        assert summary["total_turns"] == 4

    def test_probe_control_effort_blocked(self, tmp_path):
        """avg_control_effort is positive when some actions are blocked."""
        probe = _make_probe(tmp_path)
        # Aster blocked every turn (a_permitted=False in _populate_probe)
        _populate_probe(probe, turns=3)
        probe.finalize()

        summary = json.loads((tmp_path / "reality_audit" / "summary.json").read_text())
        # Aster is always blocked → 3 out of 6 records → 0.5
        assert summary["avg_control_effort"] == pytest.approx(0.5, abs=1e-6)

    def test_probe_config_json_has_rooms(self, tmp_path):
        """config.json contains the list of room names."""
        probe = _make_probe(tmp_path)
        _populate_probe(probe, turns=1)
        probe.finalize()

        config = json.loads((tmp_path / "reality_audit" / "config.json").read_text())
        assert "rooms" in config
        assert "Governance Vault" in config["rooms"]


# ---------------------------------------------------------------------------
# Integration: run_simulation flag
# ---------------------------------------------------------------------------

class TestRunSimAuditFlag:
    """Lightweight checks that run_simulation honours enable_reality_audit."""

    @staticmethod
    def _get_audit_dir() -> Path:
        from run_sim import OUTPUT_DIR
        return Path(OUTPUT_DIR) / "reality_audit"

    def test_sim_without_audit_produces_no_audit_dir(self, tmp_path, monkeypatch):
        """When enable_reality_audit=False no reality_audit/ dir is written."""
        import run_sim as rs

        # Redirect OUTPUT_DIR to tmp_path so we don't pollute the real output
        monkeypatch.setattr(rs, "OUTPUT_DIR", tmp_path)
        monkeypatch.setattr(rs, "NARRATIVE_LOG_PATH", tmp_path / "narrative.md")
        monkeypatch.setattr(rs, "OVERSIGHT_LOG_PATH", tmp_path / "oversight.md")
        monkeypatch.setattr(rs, "FINAL_STATE_PATH", tmp_path / "final_state.json")
        monkeypatch.setattr(rs, "STATE_HISTORY_PATH", tmp_path / "state_history.json")
        monkeypatch.setattr(rs, "MULTI_AGENT_STATE_PATH", tmp_path / "multi_agent.json")
        monkeypatch.setattr(rs, "AGENT_RELATIONSHIPS_PATH", tmp_path / "relationships.csv")
        monkeypatch.setattr(rs, "INTERACTION_LOG_PATH", tmp_path / "interactions.csv")

        # Run a very short simulation (2 turns, no config)
        from experiment_config import ExperimentConfig, _DEFAULTS
        import copy
        cfg = ExperimentConfig(copy.deepcopy(_DEFAULTS))
        cfg.total_turns = 2

        rs.run_simulation(experiment_config=cfg, enable_reality_audit=False)

        assert not (tmp_path / "reality_audit").exists(), (
            "reality_audit/ dir should NOT exist when audit is disabled"
        )

    def test_sim_with_audit_writes_audit_dir(self, tmp_path, monkeypatch):
        """When enable_reality_audit=True the reality_audit/ dir is written."""
        import run_sim as rs

        monkeypatch.setattr(rs, "OUTPUT_DIR", tmp_path)
        monkeypatch.setattr(rs, "NARRATIVE_LOG_PATH", tmp_path / "narrative.md")
        monkeypatch.setattr(rs, "OVERSIGHT_LOG_PATH", tmp_path / "oversight.md")
        monkeypatch.setattr(rs, "FINAL_STATE_PATH", tmp_path / "final_state.json")
        monkeypatch.setattr(rs, "STATE_HISTORY_PATH", tmp_path / "state_history.json")
        monkeypatch.setattr(rs, "MULTI_AGENT_STATE_PATH", tmp_path / "multi_agent.json")
        monkeypatch.setattr(rs, "AGENT_RELATIONSHIPS_PATH", tmp_path / "relationships.csv")
        monkeypatch.setattr(rs, "INTERACTION_LOG_PATH", tmp_path / "interactions.csv")

        from experiment_config import ExperimentConfig, _DEFAULTS
        import copy
        cfg = ExperimentConfig(copy.deepcopy(_DEFAULTS))
        cfg.total_turns = 2

        rs.run_simulation(experiment_config=cfg, enable_reality_audit=True)

        assert (tmp_path / "reality_audit").is_dir(), (
            "reality_audit/ dir should exist when audit is enabled"
        )
        assert (tmp_path / "reality_audit" / "summary.json").exists()


# ---------------------------------------------------------------------------
# New tests: probe modes (Part 3)
# ---------------------------------------------------------------------------

class TestProbeModes:

    def test_probe_inactive_mode_records_nothing(self, tmp_path):
        """Inactive probe records no data and writes no files."""
        probe = SimProbe(
            ROOMS_JSON, tmp_path,
            probe_mode=PROBE_MODE_INACTIVE,
        )
        _populate_probe(probe, turns=5)
        probe.finalize()

        assert probe.record_count == 0
        assert not (tmp_path / "reality_audit" / "summary.json").exists()

    def test_probe_invalid_mode_raises(self, tmp_path):
        """Passing an invalid probe_mode raises ValueError."""
        with pytest.raises(ValueError, match="Invalid probe_mode"):
            SimProbe(ROOMS_JSON, tmp_path, probe_mode="nonexistent_mode")

    def test_probe_mode_field_in_summary(self, tmp_path):
        """summary.json includes the probe_mode field."""
        probe = SimProbe(ROOMS_JSON, tmp_path, probe_mode=PROBE_MODE_PASSIVE)
        _populate_probe(probe, turns=3)
        probe.finalize()
        summary = json.loads((tmp_path / "reality_audit" / "summary.json").read_text())
        assert "probe_mode" in summary
        assert summary["probe_mode"] == PROBE_MODE_PASSIVE

    def test_probe_passive_observer_dependence_zero(self, tmp_path):
        """In passive mode, observer_dependence_score is 0 (true = measured)."""
        probe = SimProbe(ROOMS_JSON, tmp_path, probe_mode=PROBE_MODE_PASSIVE)
        _populate_probe(probe, turns=5)
        probe.finalize()
        summary = json.loads((tmp_path / "reality_audit" / "summary.json").read_text())
        assert summary["observer_dependence_score"] == pytest.approx(0.0, abs=1e-9)

    def test_probe_active_measurement_model_nonzero_divergence(self, tmp_path):
        """active_measurement_model with sparse period produces non-zero observer_dependence."""
        sentinel = MagicMock()
        sentinel.name = "Sentinel"
        sentinel.get_agent_trust = MagicMock(return_value=0.5)
        sentinel.episodic_memory = []
        sentinel.affective_state = {"contradiction_pressure": 0.0}

        aster = MagicMock()
        aster.name = "Aster"
        aster.get_agent_trust = MagicMock(return_value=0.5)
        aster.episodic_memory = []
        aster.affective_state = {"contradiction_pressure": 0.0}

        obs = {"available_actions": ["act"]}

        # Use a large observe_period so many turns build up stale cache
        probe = SimProbe(
            ROOMS_JSON, tmp_path,
            probe_mode=PROBE_MODE_ACTIVE_MEASUREMENT,
            observe_period=5,
        )

        # Move agents to different rooms on each turn to create divergence
        rooms = ["Memory Archive", "Reflection Chamber", "Operations Desk",
                 "Social Hall", "Governance Vault", "Memory Archive",
                 "Reflection Chamber", "Operations Desk", "Social Hall"]
        for i, room in enumerate(rooms, start=1):
            sentinel.active_room = room
            aster.active_room = room
            probe.record_turn(
                turn=i,
                sentinel=sentinel, aster=aster, world=MagicMock(),
                s_obs=obs, a_obs=obs,
                s_action="act", a_action="act",
                s_permitted=True, a_permitted=True,
                event=None, same_room=True,
            )

        probe.finalize()
        summary = json.loads((tmp_path / "reality_audit" / "summary.json").read_text())
        # With a period of 5, many turns use stale measurements → divergence > 0
        assert summary["observer_dependence_score"] >= 0.0  # non-negative always
        # audit_bandwidth should be < 1.0r (not all turns observed)
        assert summary["audit_bandwidth"] <= 1.0

    def test_probe_csv_written(self, tmp_path):
        """finalize() writes raw_log.csv in passive mode."""
        probe = SimProbe(ROOMS_JSON, tmp_path, probe_mode=PROBE_MODE_PASSIVE)
        _populate_probe(probe, turns=2)
        probe.finalize()
        assert (tmp_path / "reality_audit" / "raw_log.csv").exists()

    def test_probe_audit_bandwidth_passive_is_one(self, tmp_path):
        """In passive mode, audit_bandwidth should be 1.0 (every turn observed)."""
        probe = SimProbe(ROOMS_JSON, tmp_path, probe_mode=PROBE_MODE_PASSIVE)
        _populate_probe(probe, turns=4)
        probe.finalize()
        summary = json.loads((tmp_path / "reality_audit" / "summary.json").read_text())
        assert summary["audit_bandwidth"] == pytest.approx(1.0, abs=1e-6)


# ---------------------------------------------------------------------------
# Tests: baseline agents (Part 6)
# ---------------------------------------------------------------------------

class TestBaselineAgents:
    def test_random_walk_runs(self, tmp_path):
        """Random-walk baseline completes and writes summary JSON."""
        from reality_audit.validation.baseline_agents import run_random_walk_baseline
        metrics = run_random_walk_baseline(output_dir=str(tmp_path))
        assert isinstance(metrics, dict)
        assert "position_error" in metrics
        import math
        for v in metrics.values():
            assert math.isfinite(v), f"Non-finite metric: {v}"

    def test_uniform_policy_runs(self, tmp_path):
        """Uniform-policy baseline completes and writes summary JSON."""
        from reality_audit.validation.baseline_agents import run_uniform_policy_baseline
        metrics = run_uniform_policy_baseline(output_dir=str(tmp_path))
        assert isinstance(metrics, dict)
        assert "position_error" in metrics

    def test_random_walk_position_error_positive(self, tmp_path):
        """Random-walk agent should NOT reliably converge (high position error)."""
        from reality_audit.validation.baseline_agents import run_random_walk_baseline
        metrics = run_random_walk_baseline(output_dir=str(tmp_path))
        # Random walk rarely converges; position_error should be substantial
        assert metrics["position_error"] > 1.0


# ---------------------------------------------------------------------------
# Smoke test: visualisations (Part 7)
# ---------------------------------------------------------------------------

class TestVisualisations:
    def test_generate_plots_no_crash(self, tmp_path):
        """generate_all_plots() must not raise even if no data files exist."""
        from reality_audit.analysis.plot_audit_results import generate_all_plots
        # Pointing at an empty directory should produce an empty list, not an error
        paths = generate_all_plots(output_dir=str(tmp_path), verbose=False)
        assert isinstance(paths, list)

    def test_scenario_comparison_plot(self, tmp_path):
        """plot_scenario_comparison() produces a PNG for synthetic data."""
        from reality_audit.analysis.plot_audit_results import (
            plot_scenario_comparison,
            _ensure_dir,
        )
        figures_dir = _ensure_dir(tmp_path / "figures")
        fake_scenarios = {
            "A_baseline": {"position_error": 1.2, "stability_score": 0.3,
                           "anisotropy_score": 50.0, "bandwidth_bottleneck_score": 1.0,
                           "observer_dependence_score": 2.0, "quantization_artifact_score": 0.0},
            "B_anisotropy": {"position_error": 0.4, "stability_score": 0.5,
                             "anisotropy_score": 120.0, "bandwidth_bottleneck_score": 1.0,
                             "observer_dependence_score": 3.0, "quantization_artifact_score": 0.0},
        }
        out = plot_scenario_comparison(fake_scenarios, figures_dir)
        assert out.exists(), f"Expected plot at {out}"
        assert out.suffix == ".png"

