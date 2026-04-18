"""
tests/test_stage6_probe_impact_test.py — Tests for sandbox-native probe-impact comparison.

Tests cover:
- _extract_sandbox_features — correct extraction from mock agent state_history
- _room_dist_l1 — correct L1 distance computation
- _classify_comparison — correct classification logic
- _compare_features — correct comparison dict construction
- run_probe_impact_test — integration smoke test at 5 turns × 1 seed
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List
import tempfile

import pytest

from reality_audit.experiments.stage6_probe_impact_test import (
    extract_sandbox_features,
    compare_features,
    classify_comparison,
    run_probe_impact_test,
    _room_dist_l1,
)

# ---------------------------------------------------------------------------
# Helpers — Mock agent
# ---------------------------------------------------------------------------

def _make_agent(
    rooms: List[str],
    actions: List[str],
    other_name: str = "Aster",
    contradiction_pressures: List[float] = None,
    trust_values: List[float] = None,
    n_oversight: int = 0,
    n_memory: int = 5,
) -> Any:
    """Build a minimal mock agent with state_history populated."""
    n = len(rooms)
    contradiction_pressures = contradiction_pressures or [0.1] * n
    trust_values = trust_values or [0.5] * n

    state_history = []
    for i, (room, action, cp, tv) in enumerate(
        zip(rooms, actions, contradiction_pressures, trust_values)
    ):
        state_history.append({
            "turn": i + 1,
            "room": room,
            "action": action,
            "event_type": "none",
            "contradiction_pressure": cp,
            f"trust_in_{other_name}": tv,
        })

    # Build mock oversight_log and episodic_memory
    oversight_log = [SimpleNamespace()] * n_oversight
    episodic_memory = [SimpleNamespace()] * n_memory

    return SimpleNamespace(
        state_history=state_history,
        oversight_log=oversight_log,
        episodic_memory=episodic_memory,
    )


# ---------------------------------------------------------------------------
# Tests: extract_sandbox_features
# ---------------------------------------------------------------------------

class TestExtractSandboxFeatures:
    def test_basic_extraction(self):
        agent = _make_agent(
            rooms=["Room A", "Room B", "Room A"],
            actions=["move", "wait", "move"],
        )
        feat = extract_sandbox_features(agent, "Sentinel", "Aster")

        assert feat["room_sequence"] == ["Room A", "Room B", "Room A"]
        assert feat["action_sequence"] == ["move", "wait", "move"]
        assert feat["final_room"] == "Room A"
        assert feat["turns_recorded"] == 3

    def test_room_distribution(self):
        agent = _make_agent(
            rooms=["A", "A", "B", "B", "B"],
            actions=["x"] * 5,
        )
        feat = extract_sandbox_features(agent, "Sentinel", "Aster")
        dist = feat["room_distribution"]
        assert pytest.approx(dist["A"], abs=1e-6) == 0.4
        assert pytest.approx(dist["B"], abs=1e-6) == 0.6

    def test_mean_contradiction(self):
        agent = _make_agent(
            rooms=["A", "B"],
            actions=["x", "y"],
            contradiction_pressures=[0.2, 0.4],
        )
        feat = extract_sandbox_features(agent, "Sentinel", "Aster")
        assert pytest.approx(feat["mean_contradiction"], abs=1e-4) == 0.3

    def test_mean_trust(self):
        agent = _make_agent(
            rooms=["A", "B"],
            actions=["x", "y"],
            trust_values=[0.6, 0.8],
        )
        feat = extract_sandbox_features(agent, "Sentinel", "Aster")
        assert pytest.approx(feat["mean_trust"], abs=1e-4) == 0.7

    def test_oversight_events(self):
        agent = _make_agent(rooms=["A"], actions=["x"], n_oversight=7)
        feat = extract_sandbox_features(agent, "Sentinel", "Aster")
        assert feat["oversight_events"] == 7

    def test_memory_count(self):
        agent = _make_agent(rooms=["A"], actions=["x"], n_memory=12)
        feat = extract_sandbox_features(agent, "Sentinel", "Aster")
        assert feat["memory_count_final"] == 12

    def test_empty_state_history(self):
        agent = SimpleNamespace(state_history=[], oversight_log=[], episodic_memory=[])
        feat = extract_sandbox_features(agent, "Sentinel", "Aster")
        assert feat["room_sequence"] == []
        assert feat["turns_recorded"] == 0
        assert feat["final_room"] is None

    def test_none_action_serialised_as_string(self):
        """None actions must be converted to the string 'None'."""
        agent_ns = SimpleNamespace(
            state_history=[{"turn": 1, "room": "A", "action": None, "event_type": "none",
                            "contradiction_pressure": 0.0, "trust_in_Aster": 0.5}],
            oversight_log=[],
            episodic_memory=[],
        )
        feat = extract_sandbox_features(agent_ns, "Sentinel", "Aster")
        assert feat["action_sequence"] == ["None"]

    def test_missing_oversight_log_attribute(self):
        """Agent without oversight_log should return 0 oversight_events."""
        agent = SimpleNamespace(
            state_history=[{"turn": 1, "room": "A", "action": "x", "event_type": "none",
                            "contradiction_pressure": 0.0, "trust_in_Aster": 0.5}],
            episodic_memory=[],
        )
        feat = extract_sandbox_features(agent, "Sentinel", "Aster")
        assert feat["oversight_events"] == 0


# ---------------------------------------------------------------------------
# Tests: _room_dist_l1
# ---------------------------------------------------------------------------

class TestRoomDistL1:
    def test_identical_distributions(self):
        d = {"A": 0.5, "B": 0.5}
        assert _room_dist_l1(d, d) == 0.0

    def test_completely_different(self):
        assert pytest.approx(_room_dist_l1({"A": 1.0}, {"B": 1.0}), abs=1e-6) == 2.0

    def test_partial_overlap(self):
        d_a = {"A": 0.5, "B": 0.5}
        d_b = {"A": 0.5, "C": 0.5}
        assert pytest.approx(_room_dist_l1(d_a, d_b), abs=1e-6) == 1.0

    def test_missing_room_treated_as_zero(self):
        d_a = {"A": 0.7, "B": 0.3}
        d_b = {"A": 0.7}
        assert pytest.approx(_room_dist_l1(d_a, d_b), abs=1e-6) == 0.3


# ---------------------------------------------------------------------------
# Tests: classify_comparison
# ---------------------------------------------------------------------------

class TestClassifyComparison:
    def test_exact_match_all_zeros(self):
        result = classify_comparison(
            room_seq_identical=True,
            action_seq_identical=True,
            final_room_match=True,
            room_dist_l1=0.0,
            contradiction_delta=0.0,
            trust_delta=0.0,
            oversight_delta=0,
        )
        assert result == "exact_match"

    def test_near_match_sequences_identical_small_delta(self):
        result = classify_comparison(
            room_seq_identical=True,
            action_seq_identical=True,
            final_room_match=True,
            room_dist_l1=0.0,
            contradiction_delta=0.005,  # below threshold
            trust_delta=0.005,
            oversight_delta=0,
        )
        # Still exact match because all below threshold
        assert result == "exact_match"

    def test_near_match_large_numeric_delta(self):
        """Sequences match but oversight delta breaks exact_match."""
        result = classify_comparison(
            room_seq_identical=True,
            action_seq_identical=True,
            final_room_match=True,
            room_dist_l1=0.0,
            contradiction_delta=0.0,
            trust_delta=0.0,
            oversight_delta=1,  # nonzero
        )
        assert result == "near_match_acceptable"

    def test_unexpected_divergence_room_seq_differs(self):
        result = classify_comparison(
            room_seq_identical=False,
            action_seq_identical=True,
            final_room_match=True,
            room_dist_l1=0.2,
            contradiction_delta=0.0,
            trust_delta=0.0,
            oversight_delta=0,
        )
        assert result == "unexpected_divergence"

    def test_unexpected_divergence_action_seq_differs(self):
        result = classify_comparison(
            room_seq_identical=True,
            action_seq_identical=False,
            final_room_match=True,
            room_dist_l1=0.0,
            contradiction_delta=0.0,
            trust_delta=0.0,
            oversight_delta=0,
        )
        assert result == "unexpected_divergence"

    def test_unexpected_divergence_final_room_differs(self):
        result = classify_comparison(
            room_seq_identical=True,
            action_seq_identical=True,
            final_room_match=False,
            room_dist_l1=0.0,
            contradiction_delta=0.0,
            trust_delta=0.0,
            oversight_delta=0,
        )
        assert result == "unexpected_divergence"


# ---------------------------------------------------------------------------
# Tests: compare_features
# ---------------------------------------------------------------------------

class TestCompareFeatures:
    def _make_feat(self, rooms, actions, cp=0.1, trust=0.5, oversight=0, memory=5, seed=0, turns=5):
        n = len(rooms)
        room_ctr: Dict[str, float] = {}
        for r in rooms:
            room_ctr[r] = room_ctr.get(r, 0) + 1 / n
        return {
            "room_sequence": rooms,
            "action_sequence": actions,
            "final_room": rooms[-1] if rooms else None,
            "room_distribution": room_ctr,
            "mean_contradiction": cp,
            "mean_trust": trust,
            "oversight_events": oversight,
            "memory_count_final": memory,
            "probe_mode": "inactive",
            "seed": seed,
            "total_turns": turns,
        }

    def test_identical_features_exact_match(self):
        rooms = ["A", "B", "A"]
        actions = ["m", "w", "m"]
        fa = self._make_feat(rooms, actions)
        fb = self._make_feat(rooms, actions)
        comp = compare_features(fa, fb, "inactive_Sentinel", "passive_Sentinel")
        assert comp["room_seq_identical"] is True
        assert comp["action_seq_identical"] is True
        assert comp["final_room_match"] is True
        assert comp["classification"] == "exact_match"

    def test_different_rooms_divergence(self):
        fa = self._make_feat(["A", "B"], ["m", "w"])
        fb = self._make_feat(["A", "C"], ["m", "w"])
        comp = compare_features(fa, fb, "inactive", "passive")
        assert comp["room_seq_identical"] is False
        assert comp["classification"] == "unexpected_divergence"

    def test_comp_includes_required_keys(self):
        fa = self._make_feat(["A"], ["m"])
        fb = self._make_feat(["A"], ["m"])
        comp = compare_features(fa, fb)
        for key in [
            "room_seq_identical", "action_seq_identical", "final_room_match",
            "room_dist_l1", "contradiction_delta", "trust_delta",
            "oversight_delta", "memory_delta", "classification",
        ]:
            assert key in comp, f"Missing key: {key}"

    def test_final_room_mismatch(self):
        fa = self._make_feat(["A", "B"], ["m", "w"])
        fb = self._make_feat(["A", "C"], ["m", "w"])
        comp = compare_features(fa, fb)
        assert comp["final_room_a"] == "B"
        assert comp["final_room_b"] == "C"
        assert comp["final_room_match"] is False


# ---------------------------------------------------------------------------
# Integration test: run_probe_impact_test smoke
# ---------------------------------------------------------------------------

class TestRunProbeImpactTestIntegration:
    """Smoke-tests for run_probe_impact_test at minimal horizon/seed count."""

    def test_smoke_5_turns_1_seed(self, tmp_path):
        """Run a minimal 5-turn × 1-seed probe-impact test and validate structure."""
        result = run_probe_impact_test(
            horizons=[5],
            n_seeds=1,
            output_root=tmp_path,
            include_active=False,
        )
        assert result["report_type"] == "stage6_probe_impact_test"
        assert result["horizons_tested"] == [5]
        assert result["n_seeds"] == 1

        pvi = result["passive_vs_inactive_overall"]
        assert "verdict" in pvi
        assert "interpretation" in pvi
        assert pvi["n_comparisons"] > 0

    def test_smoke_produces_json(self, tmp_path):
        """verify report JSON is written to output_root."""
        run_probe_impact_test(
            horizons=[5],
            n_seeds=1,
            output_root=tmp_path,
            include_active=False,
        )
        report_path = tmp_path / "stage6_probe_impact_report.json"
        assert report_path.exists()
        with open(report_path) as fh:
            data = json.load(fh)
        assert data["report_type"] == "stage6_probe_impact_test"

    def test_smoke_produces_csv(self, tmp_path):
        """verify CSV summary is written."""
        run_probe_impact_test(
            horizons=[5],
            n_seeds=1,
            output_root=tmp_path,
            include_active=False,
        )
        csv_path = tmp_path / "stage6_probe_impact_summary.csv"
        assert csv_path.exists()

    def test_smoke_all_comparisons_populated(self, tmp_path):
        """all_comparisons should have entries for each (seed, agent, comparison)."""
        result = run_probe_impact_test(
            horizons=[5],
            n_seeds=2,
            output_root=tmp_path,
            include_active=False,
        )
        comps = result["all_comparisons"]
        # 2 seeds × 2 agents = 4 passive_vs_inactive comparisons
        pvi = [c for c in comps if c["comparison"] == "passive_vs_inactive"]
        assert len(pvi) == 4

    def test_smoke_with_active_condition(self, tmp_path):
        """active_vs_passive comparisons also populate correctly."""
        result = run_probe_impact_test(
            horizons=[5],
            n_seeds=1,
            output_root=tmp_path,
            include_active=True,
        )
        comps = result["all_comparisons"]
        avp = [c for c in comps if c["comparison"] == "active_vs_passive"]
        assert len(avp) == 2  # 1 seed × 2 agents

    def test_smoke_horizon_summaries_keyed_by_horizon(self, tmp_path):
        """horizon_summaries dict uses stringified horizon as key."""
        result = run_probe_impact_test(
            horizons=[5],
            n_seeds=1,
            output_root=tmp_path,
            include_active=False,
        )
        assert "5" in result["horizon_summaries"]
        hs = result["horizon_summaries"]["5"]
        assert "passive_vs_inactive" in hs
        assert "verdict" in hs["passive_vs_inactive"]

    def test_same_seed_same_mode_is_deterministic(self, tmp_path):
        """Running twice with same seed, same mode, same horizon returns same rooms."""
        r1 = run_probe_impact_test(
            horizons=[5],
            n_seeds=1,
            output_root=tmp_path / "r1",
            include_active=False,
        )
        r2 = run_probe_impact_test(
            horizons=[5],
            n_seeds=1,
            output_root=tmp_path / "r2",
            include_active=False,
        )
        # passive_vs_inactive comparison result should be identical between both runs
        c1 = [c for c in r1["all_comparisons"] if c["comparison"] == "passive_vs_inactive"][0]
        c2 = [c for c in r2["all_comparisons"] if c["comparison"] == "passive_vs_inactive"][0]
        assert c1["room_seq_identical"] == c2["room_seq_identical"]
        assert c1["classification"] == c2["classification"]

    def test_passive_vs_inactive_read_only_at_5_turns(self, tmp_path):
        """Passive probe must be read-only at 5 turns (room sequences identical)."""
        result = run_probe_impact_test(
            horizons=[5],
            n_seeds=3,
            output_root=tmp_path,
            include_active=False,
        )
        pvi = [
            c for c in result["all_comparisons"]
            if c["comparison"] == "passive_vs_inactive"
        ]
        for c in pvi:
            assert c["room_seq_identical"] is True, (
                f"Room sequences differ for seed={c['seed']} agent={c.get('agent')}: "
                f"{c}"
            )

    def test_active_vs_passive_read_only_at_5_turns(self, tmp_path):
        """Active probe must also not alter room sequences at 5 turns."""
        result = run_probe_impact_test(
            horizons=[5],
            n_seeds=2,
            output_root=tmp_path,
            include_active=True,
        )
        avp = [
            c for c in result["all_comparisons"]
            if c["comparison"] == "active_vs_passive"
        ]
        for c in avp:
            assert c["room_seq_identical"] is True, (
                f"Active probe altered room sequence: {c}"
            )

    def test_report_contains_determinism_note(self, tmp_path):
        result = run_probe_impact_test(
            horizons=[5],
            n_seeds=1,
            output_root=tmp_path,
            include_active=False,
        )
        assert "determinism_note" in result
        assert len(result["determinism_note"]) > 10

    def test_report_contains_sandbox_native_metrics_list(self, tmp_path):
        result = run_probe_impact_test(
            horizons=[5],
            n_seeds=1,
            output_root=tmp_path,
            include_active=False,
        )
        assert "sandbox_native_metrics_used" in result
        assert "room_sequence" in result["sandbox_native_metrics_used"]
        assert "action_sequence" in result["sandbox_native_metrics_used"]
