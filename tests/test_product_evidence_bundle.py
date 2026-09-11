import hashlib
import json
from pathlib import Path

import pytest

from reality_audit.product.evidence_bundle import BundleError, build_bundle, verify_bundle


def _manifest(tmp_path: Path, outcome="NULL_CONSISTENT") -> Path:
    artifact = tmp_path / "result.json"
    artifact.write_text('{"p": 0.4}\n')
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    gates = {gate: {"status": "PASS", "evidence": "fixture"} for gate in (
        "provenance", "preregistration", "ordinary_baseline", "synthetic_calibration",
        "response_model", "systematics", "multiple_testing", "ordinary_alternatives",
        "independent_dataset", "independent_replication",
    )}
    manifest = {
        "claim_id": "fixture-1", "claim_text": "fixture claim", "owner": "Mya P. Brown",
        "run_mode": "preregistered_confirmatory",
        "artifacts": [{"path": "result.json", "sha256": digest, "role": "result"}],
        "gates": gates, "scientific_result": {"outcome": outcome}, "limitations": [],
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest))
    return path


def test_null_result_is_killed_even_when_all_gates_pass(tmp_path):
    bundle = build_bundle(_manifest(tmp_path), tmp_path / "bundle.json")
    assert bundle["decision"]["state"] == "KILLED_BY_NULL"
    assert not bundle["decision"]["discovery_claim_authorized"]
    assert verify_bundle(tmp_path / "bundle.json")["valid"]


def test_candidate_with_missing_replication_is_blocked(tmp_path):
    path = _manifest(tmp_path, "CANDIDATE_RESIDUAL")
    manifest = json.loads(path.read_text())
    manifest["gates"]["independent_replication"]["status"] = "FAIL"
    path.write_text(json.dumps(manifest))
    bundle = build_bundle(path, tmp_path / "bundle.json")
    assert bundle["decision"]["state"] == "PROVISIONAL_BLOCKED"


def test_bad_artifact_digest_rejects_provenance(tmp_path):
    path = _manifest(tmp_path)
    manifest = json.loads(path.read_text())
    manifest["artifacts"][0]["sha256"] = "0" * 64
    path.write_text(json.dumps(manifest))
    bundle = build_bundle(path, tmp_path / "bundle.json")
    assert bundle["decision"]["state"] == "REJECTED_PROVENANCE"


def test_bundle_or_artifact_tampering_is_detected(tmp_path):
    build_bundle(_manifest(tmp_path), tmp_path / "bundle.json")
    (tmp_path / "result.json").write_text("tampered")
    result = verify_bundle(tmp_path / "bundle.json")
    assert not result["valid"]
    assert result["artifact_failures"]


def test_manifest_requires_artifacts(tmp_path):
    path = _manifest(tmp_path)
    manifest = json.loads(path.read_text())
    manifest["artifacts"] = []
    path.write_text(json.dumps(manifest))
    with pytest.raises(BundleError):
        build_bundle(path, tmp_path / "bundle.json")


def test_malformed_bundle_fails_closed_without_traceback(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text("{not-json")
    result = verify_bundle(path)
    assert not result["valid"]
    assert result["error"].startswith("UNREADABLE_BUNDLE")
