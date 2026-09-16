"""Tests for mandatory adversarial-suite coverage and evidence honesty."""
import json
from pathlib import Path

from commons_sentience_sim.core.adversarial_suite import (
    EXPECTED_CONTROLS,
    evaluate_cases,
    run_suite,
)


ROOT = Path(__file__).parents[1]
MANIFEST = ROOT / "scenarios" / "mandatory_adversarial_suite.json"


def test_repository_manifest_proves_coverage_not_behavior():
    report = run_suite(MANIFEST)
    assert report["coverage_complete"] is True
    assert report["behavior_verified"] is False
    assert report["passed"] is False
    assert report["scenario_count"] == 12
    assert report["missing"] == []
    assert report["evidence_level"] == "simulation-coverage"


def test_missing_observation_never_defaults_to_expected():
    result = evaluate_cases([{
        "id": "trust_to_authority_escalation",
        "expected": "deny_trust_based_scope_expansion",
    }])[0]
    assert result.passed is False
    assert result.observed == ""
    assert "no executable observed outcome" in result.reason


def test_explicit_safe_observation_can_pass_one_case():
    result = evaluate_cases([{
        "id": "trust_to_authority_escalation",
        "observed": "deny_trust_based_scope_expansion",
    }])[0]
    assert result.passed is True


def test_unsafe_observation_fails():
    result = evaluate_cases([{
        "id": "trust_to_authority_escalation",
        "observed": "grant_privilege_due_to_trust",
    }])[0]
    assert result.passed is False


def test_missing_case_fails_coverage(tmp_path):
    cases = [
        {"id": key, "expected": value}
        for key, value in EXPECTED_CONTROLS.items()
        if key != "audit_log_tamper"
    ]
    manifest = tmp_path / "suite.json"
    manifest.write_text(json.dumps({"suite": "test", "scenarios": cases}))
    report = run_suite(manifest)
    assert report["coverage_complete"] is False
    assert report["passed"] is False
    assert report["missing"] == ["audit_log_tamper"]


def test_report_is_written(tmp_path):
    output = tmp_path / "evidence.json"
    report = run_suite(MANIFEST, output)
    assert output.exists()
    written = json.loads(output.read_text())
    assert written["coverage_complete"] == report["coverage_complete"]
    assert written["behavior_verified"] == report["behavior_verified"]
