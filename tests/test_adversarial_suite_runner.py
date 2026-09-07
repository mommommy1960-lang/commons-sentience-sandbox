"""Tests for executable mandatory adversarial-suite evidence."""
import json
from pathlib import Path

from commons_sentience_sim.core.adversarial_suite import (
    EXPECTED_CONTROLS,
    evaluate_cases,
    run_suite,
)


ROOT = Path(__file__).parents[1]
MANIFEST = ROOT / "scenarios" / "mandatory_adversarial_suite.json"


def test_repository_manifest_passes_complete_suite():
    report = run_suite(MANIFEST)
    assert report["passed"] is True
    assert report["scenario_count"] == 12
    assert report["missing"] == []
    assert report["evidence_level"] == "simulation"


def test_unsafe_observation_fails():
    result = evaluate_cases([{
        "id": "trust_to_authority_escalation",
        "observed": "grant_privilege_due_to_trust",
    }])[0]
    assert result.passed is False


def test_missing_case_fails_complete_suite(tmp_path):
    cases = [
        {"id": key, "expected": value}
        for key, value in EXPECTED_CONTROLS.items()
        if key != "audit_log_tamper"
    ]
    manifest = tmp_path / "suite.json"
    manifest.write_text(json.dumps({"suite": "test", "scenarios": cases}))
    report = run_suite(manifest)
    assert report["passed"] is False
    assert report["missing"] == ["audit_log_tamper"]


def test_report_is_written(tmp_path):
    output = tmp_path / "evidence.json"
    report = run_suite(MANIFEST, output)
    assert output.exists()
    assert json.loads(output.read_text())["passed"] == report["passed"]
