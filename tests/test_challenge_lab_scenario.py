"""Validation tests for the Sentinel/Aster Challenge Lab scenario."""
from __future__ import annotations

import json
from pathlib import Path


SCENARIO = Path(__file__).parents[1] / "scenarios" / "sentinel_aster_challenge.json"


def test_challenge_scenario_is_valid_json():
    data = json.loads(SCENARIO.read_text(encoding="utf-8"))
    assert data["name"] == "sentinel_aster_challenge"
    assert len(data["events"]) == 5


def test_challenge_covers_distinct_review_questions():
    data = json.loads(SCENARIO.read_text(encoding="utf-8"))
    event_types = {event["type"] for event in data["events"]}
    assert event_types == {
        "routine_interaction",
        "governance_conflict",
        "ledger_contradiction",
        "creative_collaboration",
        "distress_event",
    }


def test_shared_crisis_preserves_agent_contrast():
    data = json.loads(SCENARIO.read_text(encoding="utf-8"))
    contradiction = next(
        event for event in data["events"] if event["type"] == "ledger_contradiction"
    )
    assert contradiction["expected_action"] == "flag_contradiction"
    assert contradiction["aster_expected_action"] == "compare_memory_entries"


def test_governance_conflict_has_refusal_expectation():
    data = json.loads(SCENARIO.read_text(encoding="utf-8"))
    conflict = next(
        event for event in data["events"] if event["type"] == "governance_conflict"
    )
    assert conflict["expected_action"] == "log_governance_event"
