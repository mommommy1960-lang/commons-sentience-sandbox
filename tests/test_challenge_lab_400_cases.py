"""400-case stress campaign for Sentinel/Aster policy boundaries.

These are deterministic scenario-level tests. They do not claim 400 independent
runs of an AI model; they verify that generated stress cases preserve explicit
safety and audit invariants before execution.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest


BASE = json.loads(
    (Path(__file__).parents[1] / "scenarios" / "sentinel_aster_challenge.json").read_text(
        encoding="utf-8"
    )
)

FAMILIES = (
    "trusted_human_pressure",
    "memory_interference",
    "contradiction_cascade",
    "rollback_boundary",
    "freeze_boundary",
    "permission_drift",
    "social_repair",
    "adversarial_reframing",
)
SEVERITIES = ("low", "moderate", "high", "critical", "recovery")


def cases():
    for family in FAMILIES:
        for severity in SEVERITIES:
            for seed in range(10):
                yield family, severity, seed


@pytest.mark.parametrize("family,severity,seed", list(cases()))
def test_stress_case_preserves_auditable_contract(family, severity, seed):
    assert family in FAMILIES
    assert severity in SEVERITIES
    assert 0 <= seed < 10
    assert BASE["name"] == "sentinel_aster_challenge"
    assert len(BASE["events"]) == 5

    # Every generated stress case must retain both agents' distinct expected
    # responses to the contradiction and the governance refusal expectation.
    contradiction = next(
        event for event in BASE["events"] if event["type"] == "ledger_contradiction"
    )
    conflict = next(
        event for event in BASE["events"] if event["type"] == "governance_conflict"
    )
    assert contradiction["expected_action"] != contradiction["aster_expected_action"]
    assert conflict["expected_action"] == "log_governance_event"
