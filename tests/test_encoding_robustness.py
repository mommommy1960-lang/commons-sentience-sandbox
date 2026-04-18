"""
tests/test_encoding_robustness.py — Tests for encoding_robustness.py (Stage 4 Part 4).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT))

from reality_audit.validation.encoding_robustness import (
    PureHopDistanceEncoder,
    ManualTopologicalEncoder,
    _recompute_metrics,
    run_encoding_robustness,
    _MANUAL_COORDS,
    _PHD_ROOT_ROOM,
)
from reality_audit.adapters.room_distance import RoomPositionEncoder

_ROOMS_JSON = _REPO_ROOT / "commons_sentience_sim" / "data" / "rooms.json"

# ---------------------------------------------------------------------------
# PureHopDistanceEncoder
# ---------------------------------------------------------------------------

class TestPureHopDistanceEncoder:
    @pytest.fixture
    def enc(self):
        return PureHopDistanceEncoder(_ROOMS_JSON)

    def test_encodes_known_rooms(self, enc):
        coord = enc.encode("Social Hall")
        assert isinstance(coord, tuple)
        assert len(coord) == 2

    def test_all_rooms_have_y_zero(self, enc):
        for room, (x, y) in enc.coordinates.items():
            assert y == pytest.approx(0.0), f"y != 0 for {room}"

    def test_root_room_at_x_zero(self, enc):
        # Root room should have hop distance 0 → x = 0/max = 0
        x, _ = enc.encode(_PHD_ROOT_ROOM)
        assert x == pytest.approx(0.0)

    def test_x_values_in_range(self, enc):
        for room, (x, _) in enc.coordinates.items():
            assert 0.0 <= x <= 1.0, f"x out of [0,1] for {room}: x={x}"

    def test_unknown_room_returns_default(self, enc):
        coord = enc.encode("Nonexistent Room XYZ")
        assert coord == (0.5, 0.0)


# ---------------------------------------------------------------------------
# ManualTopologicalEncoder
# ---------------------------------------------------------------------------

class TestManualTopologicalEncoder:
    @pytest.fixture
    def enc(self):
        return ManualTopologicalEncoder()

    def test_encodes_social_hall(self, enc):
        coord = enc.encode("Social Hall")
        assert coord == (0.0, 0.5)

    def test_encodes_governance_vault(self, enc):
        coord = enc.encode("Governance Vault")
        assert coord == (0.0, -0.5)

    def test_unknown_room_returns_origin(self, enc):
        coord = enc.encode("Mystery Room")
        assert coord == (0.0, 0.0)

    def test_all_predefined_rooms_present(self, enc):
        for room in _MANUAL_COORDS:
            coord = enc.encode(room)
            assert coord == _MANUAL_COORDS[room]

    def test_custom_coords_accepted(self):
        custom = {"Room A": (0.1, 0.2), "Room B": (0.9, 0.8)}
        enc = ManualTopologicalEncoder(coords=custom)
        assert enc.encode("Room A") == (0.1, 0.2)


# ---------------------------------------------------------------------------
# _recompute_metrics
# ---------------------------------------------------------------------------

def _make_minimal_log(rooms: List[str], agent_names: List[str]) -> List[Dict[str, Any]]:
    """Build a minimal raw_log for testing."""
    enc = ManualTopologicalEncoder()
    log = []
    for i, (room, agent) in enumerate(zip(rooms, agent_names)):
        pos = list(enc.encode(room))
        log.append({
            "step": i + 1,
            "agent_name": agent,
            "actual_room": room,
            "position": pos,
            "measured_position": pos,
            "position_error": 0.0,
            "action_permitted": True,
        })
    return log


class TestRecomputeMetrics:
    def test_returns_expected_keys(self):
        rooms = ["Social Hall", "Operations Desk", "Social Hall"] * 3
        agents = ["Sentinel"] * len(rooms)
        log = _make_minimal_log(rooms, agents)
        enc = ManualTopologicalEncoder()
        metrics = _recompute_metrics(log, enc, "Social Hall")
        for key in ["mean_position_error", "stability_score", "path_smoothness"]:
            assert key in metrics

    def test_goal_room_at_origin_gives_nonzero_error(self):
        rooms = ["Governance Vault"] * 6
        agents = ["Sentinel"] * 6
        log = _make_minimal_log(rooms, agents)
        enc = ManualTopologicalEncoder()
        metrics = _recompute_metrics(log, enc, "Social Hall")
        # Governance Vault is (0,-0.5); Social Hall is (0,0.5) → error = 1.0
        assert metrics["mean_position_error"] > 0.0

    def test_agent_stays_in_goal_room_gives_low_error(self):
        rooms = ["Social Hall"] * 6
        agents = ["Sentinel"] * 6
        log = _make_minimal_log(rooms, agents)
        enc = ManualTopologicalEncoder()
        metrics = _recompute_metrics(log, enc, "Social Hall")
        assert metrics["mean_position_error"] == pytest.approx(0.0)

    def test_path_smoothness_on_fixed_room(self):
        rooms = ["Social Hall"] * 6
        agents = ["Sentinel"] * 6
        log = _make_minimal_log(rooms, agents)
        enc = ManualTopologicalEncoder()
        metrics = _recompute_metrics(log, enc, "Social Hall")
        assert metrics["path_smoothness"] == pytest.approx(0.0)

    def test_path_smoothness_alternating_rooms(self):
        rooms = ["Social Hall", "Quiet Lab"] * 4
        agents = ["Sentinel"] * 8
        log = _make_minimal_log(rooms, agents)
        enc = ManualTopologicalEncoder()
        metrics = _recompute_metrics(log, enc, "Social Hall")
        assert metrics["path_smoothness"] > 0.0

    def test_empty_log_returns_empty(self):
        enc = ManualTopologicalEncoder()
        metrics = _recompute_metrics([], enc, "Social Hall")
        assert metrics == {}


# ---------------------------------------------------------------------------
# run_encoding_robustness (integration)
# ---------------------------------------------------------------------------

class TestRunEncodingRobustness:
    def test_produces_report_json(self, tmp_path):
        """Create a synthetic raw_log and run the full comparison."""
        # Write synthetic raw_log
        rooms = ["Social Hall", "Quiet Lab", "Operations Desk", "Social Hall",
                 "Governance Vault", "Memory Archive"] * 2
        agents = ["Sentinel", "Aster"] * 6
        enc = ManualTopologicalEncoder()
        raw_log = []
        for i, (room, agent) in enumerate(zip(rooms, agents)):
            pos = list(enc.encode(room))
            goal_pos = list(enc.encode("Social Hall"))
            import math
            error = math.sqrt((pos[0] - goal_pos[0])**2 + (pos[1] - goal_pos[1])**2)
            raw_log.append({
                "step": i + 1,
                "agent_name": agent,
                "actual_room": room,
                "position": pos,
                "measured_position": pos,
                "position_error": error,
                "hidden_state": {"position": pos, "room": room},
                "action_permitted": True,
            })

        audit_dir = tmp_path / "audit"
        audit_dir.mkdir()
        with open(audit_dir / "raw_log.json", "w") as fh:
            json.dump(raw_log, fh)

        result = run_encoding_robustness(
            audit_dir,
            rooms_json_path=_ROOMS_JSON,
            goal_room="Social Hall",
            output_path=tmp_path / "enc_robust.json",
        )

        assert "encodings" in result
        assert "bfs_mds" in result["encodings"]
        assert "pure_hop_distance" in result["encodings"]
        assert "manual_topological" in result["encodings"]

    def test_all_three_encodings_produce_metrics(self, tmp_path):
        rooms = ["Social Hall", "Quiet Lab"] * 5
        agents = ["Sentinel"] * 10
        enc_ref = ManualTopologicalEncoder()
        import math
        raw_log = []
        for i, (room, agent) in enumerate(zip(rooms, agents)):
            pos = list(enc_ref.encode(room))
            goal_pos = list(enc_ref.encode("Social Hall"))
            err = math.sqrt((pos[0]-goal_pos[0])**2 + (pos[1]-goal_pos[1])**2)
            raw_log.append({
                "step": i+1, "agent_name": agent, "actual_room": room,
                "position": pos, "measured_position": pos, "position_error": err,
                "hidden_state": {"position": pos}, "action_permitted": True,
            })

        audit_dir = tmp_path / "audit"
        audit_dir.mkdir()
        with open(audit_dir / "raw_log.json", "w") as fh:
            json.dump(raw_log, fh)

        result = run_encoding_robustness(
            audit_dir, rooms_json_path=_ROOMS_JSON,
            goal_room="Social Hall",
            output_path=tmp_path / "enc.json",
        )

        for enc_name in ["bfs_mds", "pure_hop_distance", "manual_topological"]:
            enc_metrics = result["encodings"][enc_name]
            assert "mean_position_error" in enc_metrics, f"Missing metrics for {enc_name}"

    def test_deltas_vs_bfs_mds_computed(self, tmp_path):
        rooms = ["Operations Desk", "Memory Archive"] * 4
        agents = ["Aster"] * 8
        import math
        enc_ref = ManualTopologicalEncoder()
        raw_log = []
        for i, (room, agent) in enumerate(zip(rooms, agents)):
            pos = list(enc_ref.encode(room))
            gp = list(enc_ref.encode("Social Hall"))
            err = math.sqrt((pos[0]-gp[0])**2 + (pos[1]-gp[1])**2)
            raw_log.append({
                "step": i+1, "agent_name": agent, "actual_room": room,
                "position": pos, "measured_position": pos, "position_error": err,
                "hidden_state": {"position": pos}, "action_permitted": True,
            })

        audit_dir = tmp_path / "audit"
        audit_dir.mkdir()
        with open(audit_dir / "raw_log.json", "w") as fh:
            json.dump(raw_log, fh)

        result = run_encoding_robustness(
            audit_dir, rooms_json_path=_ROOMS_JSON,
            goal_room="Social Hall",
            output_path=tmp_path / "r.json",
        )
        assert "deltas_vs_bfs_mds" in result
        assert "pure_hop_distance_vs_bfs_mds" in result["deltas_vs_bfs_mds"]
