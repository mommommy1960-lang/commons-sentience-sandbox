"""Compile and verify tamper-evident Reality Audit evidence bundles.

This module intentionally separates integrity from identity. SHA-256 digests make
the bundle tamper-evident; they are not a digital signature and do not establish
who created the bundle.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

BUNDLE_VERSION = "1.0"
GATE_ORDER = (
    "provenance",
    "preregistration",
    "ordinary_baseline",
    "synthetic_calibration",
    "response_model",
    "systematics",
    "multiple_testing",
    "ordinary_alternatives",
    "independent_dataset",
    "independent_replication",
)


class BundleError(ValueError):
    """Raised when a manifest or bundle violates the product contract."""


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _digest_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _require_text(manifest: Mapping[str, Any], key: str) -> str:
    value = manifest.get(key)
    if not isinstance(value, str) or not value.strip():
        raise BundleError(f"manifest field {key!r} must be non-empty text")
    return value.strip()


def _evaluate_gates(manifest: Mapping[str, Any], artifact_records: list[dict]) -> list[dict]:
    supplied = manifest.get("gates")
    if not isinstance(supplied, Mapping):
        raise BundleError("manifest 'gates' must be an object")

    results = []
    provenance_artifacts_ok = all(item["status"] == "VERIFIED" for item in artifact_records)
    for gate_id in GATE_ORDER:
        raw = supplied.get(gate_id)
        if not isinstance(raw, Mapping):
            passed = False
            evidence = "gate absent"
        else:
            passed = raw.get("status") == "PASS"
            evidence = str(raw.get("evidence") or "no evidence supplied")
        if gate_id == "provenance":
            passed = passed and provenance_artifacts_ok
            if not provenance_artifacts_ok:
                evidence += "; one or more artifacts failed digest verification"
        results.append({"id": gate_id, "passed": passed, "evidence": evidence})
    return results


def _decision(manifest: Mapping[str, Any], gates: list[dict]) -> dict:
    failed = [gate["id"] for gate in gates if not gate["passed"]]
    scientific = manifest.get("scientific_result")
    if not isinstance(scientific, Mapping):
        raise BundleError("manifest 'scientific_result' must be an object")
    outcome = scientific.get("outcome")
    if outcome not in {"NULL_CONSISTENT", "CANDIDATE_RESIDUAL", "INPUT_FAILURE"}:
        raise BundleError("unsupported scientific_result.outcome")

    if "provenance" in failed or outcome == "INPUT_FAILURE":
        state = "REJECTED_PROVENANCE"
    elif outcome == "NULL_CONSISTENT":
        state = "KILLED_BY_NULL"
    elif failed:
        state = "PROVISIONAL_BLOCKED"
    else:
        state = "PROMOTABLE_FOR_EXTERNAL_REVIEW"
    return {
        "state": state,
        "failed_gates": failed,
        "claim_survived_available_tests": outcome == "CANDIDATE_RESIDUAL",
        "external_review_required": state == "PROMOTABLE_FOR_EXTERNAL_REVIEW",
        "discovery_claim_authorized": False,
    }


def build_bundle(manifest_path: str | Path, output_path: str | Path) -> dict:
    manifest_file = Path(manifest_path).resolve()
    output = Path(output_path).resolve()
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    for key in ("claim_id", "claim_text", "owner", "run_mode"):
        _require_text(manifest, key)
    if manifest["run_mode"] not in {"exploratory", "preregistered_confirmatory"}:
        raise BundleError("run_mode must be exploratory or preregistered_confirmatory")

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise BundleError("manifest requires at least one artifact")
    records = []
    for item in artifacts:
        if not isinstance(item, Mapping) or not item.get("path"):
            raise BundleError("every artifact requires a path")
        path = (manifest_file.parent / str(item["path"])).resolve()
        expected = item.get("sha256")
        actual = _digest_file(path) if path.is_file() else None
        status = "VERIFIED" if actual and expected == actual else "FAILED"
        records.append({
            "role": str(item.get("role") or "evidence"),
            "path": os.path.relpath(path, output.parent),
            "bytes": path.stat().st_size if path.is_file() else None,
            "expected_sha256": expected,
            "actual_sha256": actual,
            "status": status,
        })

    gates = _evaluate_gates(manifest, records)
    prior_digest = manifest.get("previous_bundle_sha256")
    payload = {
        "bundle_version": BUNDLE_VERSION,
        "claim": {
            "id": manifest["claim_id"],
            "text": manifest["claim_text"],
            "owner": manifest["owner"],
            "run_mode": manifest["run_mode"],
        },
        "artifacts": records,
        "gates": gates,
        "scientific_result": manifest["scientific_result"],
        "decision": _decision(manifest, gates),
        "limitations": list(manifest.get("limitations") or []),
        "chain": {"previous_bundle_sha256": prior_digest},
        "integrity_boundary": "SHA-256 integrity only; creator identity is not cryptographically signed",
    }
    payload["bundle_sha256"] = _digest_bytes(_canonical(payload))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def verify_bundle(path: str | Path) -> dict:
    bundle_file = Path(path).resolve()
    try:
        bundle = json.loads(bundle_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return {
            "valid": False,
            "claimed_bundle_sha256": None,
            "actual_bundle_sha256": None,
            "artifact_failures": [],
            "decision_state": None,
            "error": f"UNREADABLE_BUNDLE: {type(exc).__name__}",
        }
    if not isinstance(bundle, dict):
        return {
            "valid": False,
            "claimed_bundle_sha256": None,
            "actual_bundle_sha256": None,
            "artifact_failures": [],
            "decision_state": None,
            "error": "INVALID_BUNDLE_ROOT",
        }
    claimed = bundle.pop("bundle_sha256", None)
    actual = _digest_bytes(_canonical(bundle))
    artifact_failures = []
    for artifact in bundle.get("artifacts", []):
        artifact_path = (bundle_file.parent / artifact.get("path", "")).resolve()
        digest = _digest_file(artifact_path) if artifact_path.is_file() else None
        if digest != artifact.get("actual_sha256"):
            artifact_failures.append(str(artifact_path))
    return {
        "valid": claimed == actual and not artifact_failures,
        "claimed_bundle_sha256": claimed,
        "actual_bundle_sha256": actual,
        "artifact_failures": artifact_failures,
        "decision_state": bundle.get("decision", {}).get("state"),
    }
