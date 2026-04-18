"""
tests/test_read_only_expansion.py — Tests for read_only_expansion.py (Stage 4 Part 6).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT))

from reality_audit.validation.read_only_expansion import (
    _room_occupancy,
    _compare_occupancy,
    _governance_counts,
    _levenshtein,
    _action_sequences,
    _compare_action_sequences,
    _path_history,
    compare_two_runs,
    run_read_only_expansion,
    EXACT_MATCH_SAFE_FIELDS,
    PROBABILISTIC_FIELDS,
    UNRELIABLE_FIELDS,
)


# ---------------------------------------------------------------------------
# Unit tests: helpers
# ---------------------------------------------------------------------------

class TestRoomOccupancy:
    def test_counts_turns_per_agent_per_room(self):
        log = [
            {"agent_name": "Sentinel", "actual_room": "A"},
            {"agent_name": "Sentinel", "actual_room": "B"},
            {"agent_name": "Sentinel", "actual_room": "A"},
            {"agent_name": "Aster", "actual_room": "C"},
        ]
        occ = _room_occupancy(log)
        assert occ["Sentinel"]["A"] == 2
        assert occ["Sentinel"]["B"] == 1
        assert occ["Aster"]["C"] == 1

    def test_empty_log(self):
        assert _room_occupancy([]) == {}

    def test_single_agent(self):
        log = [{"agent_name": "X", "actual_room": "Hall"}] * 5
        occ = _room_occupancy(log)
        assert occ["X"]["Hall"] == 5


class TestCompareOccupancy:
    def test_same_occupancy_gives_zero_delta(self):
        occ = {"S": {"A": 3, "B": 2}}
        result = _compare_occupancy(occ, occ)
        assert result["S"]["A"]["delta"] == 0
        assert result["S"]["B"]["delta"] == 0

    def test_delta_computed_correctly(self):
        occ_a = {"S": {"A": 3}}
        occ_b = {"S": {"A": 5}}
        result = _compare_occupancy(occ_a, occ_b)
        assert result["S"]["A"]["delta"] == 2

    def test_missing_room_in_one_run(self):
        occ_a = {"S": {"A": 2}}
        occ_b = {"S": {"B": 3}}
        result = _compare_occupancy(occ_a, occ_b)
        assert "A" in result["S"]
        assert "B" in result["S"]


class TestGovernanceCounts:
    def test_counts_permitted_and_blocked(self):
        log = [
            {"agent_name": "S", "action_permitted": True},
            {"agent_name": "S", "action_permitted": False},
            {"agent_name": "S", "action_permitted": True},
            {"agent_name": "A", "action_permitted": True},
        ]
        counts = _governance_counts(log)
        assert counts["S"]["permitted"] == 2
        assert counts["S"]["blocked"] == 1
        assert counts["A"]["permitted"] == 1

    def test_defaults_to_permitted(self):
        log = [{"agent_name": "X"}]  # no action_permitted key
        counts = _governance_counts(log)
        assert counts["X"]["permitted"] == 1


class TestLevenshtein:
    def test_identical_sequences(self):
        assert _levenshtein(["a", "b", "c"], ["a", "b", "c"]) == 0

    def test_completely_different(self):
        assert _levenshtein(["a", "b"], ["c", "d"]) == 2

    def test_one_insertion(self):
        assert _levenshtein(["a", "c"], ["a", "b", "c"]) == 1

    def test_empty_sequences(self):
        assert _levenshtein([], []) == 0
        assert _levenshtein(["a"], []) == 1
        assert _levenshtein([], ["a"]) == 1


class TestActionSequences:
    def test_extracts_by_agent(self):
        log = [
            {"step": 1, "agent_name": "S", "selected_action": "move_north"},
            {"step": 2, "agent_name": "S", "selected_action": "wait"},
            {"step": 1, "agent_name": "A", "selected_action": "explore"},
        ]
        seqs = _action_sequences(log)
        assert seqs["S"] == ["move_north", "wait"]
        assert seqs["A"] == ["explore"]

    def test_none_action_becomes_none_string(self):
        log = [{"step": 1, "agent_name": "S", "selected_action": None}]
        seqs = _action_sequences(log)
        assert seqs["S"] == ["none"]


class TestCompareActionSequences:
    def test_identical_sequences(self):
        seqs = {"S": ["move", "wait"]}
        result = _compare_action_sequences(seqs, seqs)
        assert result["S"]["edit_distance"] == 0
        assert result["S"]["classification"] == "exact_match"

    def test_similar_sequences(self):
        # 1 edit out of 10 → normalised = 0.1, classified as "similar"
        seqs_a = {"S": ["move", "wait", "move", "wait", "move", "wait", "explore", "wait", "move", "wait"]}
        seqs_b = {"S": ["move", "wait", "move", "wait", "move", "wait", "rest",    "wait", "move", "wait"]}
        result = _compare_action_sequences(seqs_a, seqs_b)
        assert result["S"]["classification"] in ("exact_match", "similar")

    def test_divergent_sequences(self):
        seqs_a = {"S": ["a", "b", "c", "d", "e"]}
        seqs_b = {"S": ["x", "y", "z", "w", "v"]}
        result = _compare_action_sequences(seqs_a, seqs_b)
        assert result["S"]["classification"] == "divergent"


class TestPathHistory:
    def test_extracts_unique_transitions(self):
        log = [
            {"step": 1, "agent_name": "S", "actual_room": "A"},
            {"step": 2, "agent_name": "S", "actual_room": "A"},  # same room
            {"step": 3, "agent_name": "S", "actual_room": "B"},
            {"step": 4, "agent_name": "S", "actual_room": "A"},
        ]
        paths = _path_history(log)
        assert paths["S"] == ["A", "B", "A"]

    def test_single_turn(self):
        log = [{"step": 1, "agent_name": "X", "actual_room": "Z"}]
        paths = _path_history(log)
        assert paths["X"] == ["Z"]


# ---------------------------------------------------------------------------
# Integration: compare_two_runs
# ---------------------------------------------------------------------------

def _write_audit(path: Path, summary: Dict, log: List) -> None:
    path.mkdir(parents=True, exist_ok=True)
    with open(path / "audit_summary.json", "w") as fh:
        json.dump(summary, fh)
    with open(path / "raw_log.json", "w") as fh:
        json.dump(log, fh)


def _make_summary(probe_mode="passive", total_records=6,
                  pos_err=1.2, stability=0.4, smoothness=0.3) -> Dict:
    return {
        "probe_mode": probe_mode,
        "goal_room": "Social Hall",
        "total_records": total_records,
        "mean_position_error": pos_err,
        "stability_score": stability,
        "path_smoothness": smoothness,
        "avg_control_effort": 0.1,
        "audit_bandwidth": 1.0,
        "observer_dependence_score": 0.0,
    }


def _make_log(turns=3) -> List:
    log = []
    rooms = ["Social Hall", "Quiet Lab", "Operations Desk"]
    for t in range(turns):
        for agent in ["Sentinel", "Aster"]:
            log.append({
                "step": t + 1,
                "agent_name": agent,
                "actual_room": rooms[t % len(rooms)],
                "position": [0.1, 0.2],
                "measured_position": [0.1, 0.2],
                "position_error": 0.5,
                "action_permitted": True,
                "selected_action": "explore",
                "hidden_state": {"position": [0.1, 0.2]},
            })
    return log


class TestCompareTwoRuns:
    def test_identical_runs_all_exact_pass(self, tmp_path):
        summary = _make_summary()
        log = _make_log(3)
        _write_audit(tmp_path / "runA", summary, log)
        _write_audit(tmp_path / "runB", summary, log)
        result = compare_two_runs(tmp_path / "runA", tmp_path / "runB")
        for field, data in result["exact_match_fields"].items():
            assert data["match"] is True, f"Exact field {field} did not match"

    def test_verdict_keys_present(self, tmp_path):
        summary = _make_summary()
        log = _make_log(3)
        _write_audit(tmp_path / "runA", summary, log)
        _write_audit(tmp_path / "runB", summary, log)
        result = compare_two_runs(tmp_path / "runA", tmp_path / "runB")
        for key in ["exact_fields_ok", "probabilistic_fields_similar",
                    "action_sequences_similar", "overall_probe_readonly_confirmed"]:
            assert key in result["verdict"]

    def test_different_total_records_fails_exact_match(self, tmp_path):
        summary_a = _make_summary(total_records=6)
        summary_b = _make_summary(total_records=10)
        log = _make_log(3)
        _write_audit(tmp_path / "runA", summary_a, log)
        _write_audit(tmp_path / "runB", summary_b, log)
        result = compare_two_runs(tmp_path / "runA", tmp_path / "runB")
        assert result["exact_match_fields"]["total_records"]["match"] is False

    def test_room_occupancy_comparison_present(self, tmp_path):
        summary = _make_summary()
        log = _make_log(3)
        _write_audit(tmp_path / "runA", summary, log)
        _write_audit(tmp_path / "runB", summary, log)
        result = compare_two_runs(tmp_path / "runA", tmp_path / "runB")
        assert "room_occupancy_comparison" in result
        assert "Sentinel" in result["room_occupancy_comparison"]

    def test_run_read_only_expansion_writes_json(self, tmp_path):
        summary = _make_summary()
        log = _make_log(3)
        _write_audit(tmp_path / "runA", summary, log)
        _write_audit(tmp_path / "runB", summary, log)
        out = tmp_path / "roe_report.json"
        run_read_only_expansion(tmp_path / "runA", tmp_path / "runB", out)
        assert out.exists()
        with open(out) as fh:
            data = json.load(fh)
        assert "verdict" in data
