"""Identity-authenticated Reality Audit evidence envelopes.

Ed25519 signatures authenticate possession of a private key. They do not, by
themselves, prove a person's legal identity or provide a trusted timestamp.
"""

from __future__ import annotations

import base64
import hashlib
import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from .evidence_bundle import verify_bundle


SIGNED_VERSION = "1.0"


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def _b64(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def _unb64(value: str) -> bytes:
    return base64.b64decode(value, validate=True)


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def generate_keypair() -> dict[str, str]:
    private = Ed25519PrivateKey.generate()
    private_raw = private.private_bytes(
        serialization.Encoding.Raw,
        serialization.PrivateFormat.Raw,
        serialization.NoEncryption(),
    )
    public_raw = private.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    return {
        "algorithm": "Ed25519",
        "key_id": _sha(public_raw),
        "private_key_base64": _b64(private_raw),
        "public_key_base64": _b64(public_raw),
    }


def public_key_record(keypair: dict[str, str], owner: str) -> dict[str, str]:
    return {
        "schema_version": "1.0",
        "algorithm": "Ed25519",
        "key_id": keypair["key_id"],
        "owner": owner,
        "public_key_base64": keypair["public_key_base64"],
        "status": "ACTIVE",
    }


def _load_log(path: Path) -> list[dict]:
    if not path.exists():
        return []
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError("transparency log must be a JSON array")
    return value


def _verify_log_chain(entries: list[dict]) -> tuple[bool, str | None]:
    previous = None
    nonces: set[str] = set()
    for index, entry in enumerate(entries):
        supplied = entry.get("entry_sha256")
        payload = dict(entry)
        payload.pop("entry_sha256", None)
        if entry.get("index") != index or entry.get("previous_entry_sha256") != previous:
            return False, "BROKEN_LOG_CHAIN"
        if supplied != _sha(_canonical(payload)):
            return False, "BROKEN_LOG_DIGEST"
        nonce = entry.get("nonce")
        if not isinstance(nonce, str) or nonce in nonces:
            return False, "REPLAYED_NONCE"
        nonces.add(nonce)
        previous = supplied
    return True, None


def sign_bundle(
    bundle_path: str | Path,
    envelope_path: str | Path,
    private_key_base64: str,
    public_record: dict[str, str],
    transparency_log_path: str | Path,
    nonce: str | None = None,
) -> dict:
    bundle_path = Path(bundle_path).resolve()
    envelope_path = Path(envelope_path).resolve()
    log_path = Path(transparency_log_path).resolve()
    bundle_check = verify_bundle(bundle_path)
    if not bundle_check["valid"]:
        raise ValueError("refusing to sign an invalid evidence bundle")
    public_raw = _unb64(public_record["public_key_base64"])
    if public_record.get("key_id") != _sha(public_raw) or public_record.get("status") != "ACTIVE":
        raise ValueError("invalid or inactive public-key record")
    nonce = nonce or secrets.token_hex(16)
    entries = _load_log(log_path)
    chain_ok, chain_error = _verify_log_chain(entries)
    if not chain_ok:
        raise ValueError(chain_error)
    if any(entry["nonce"] == nonce for entry in entries):
        raise ValueError("replayed nonce")
    statement = {
        "signed_version": SIGNED_VERSION,
        "bundle_sha256": bundle_check["actual_bundle_sha256"],
        "key_id": public_record["key_id"],
        "signer": public_record["owner"],
        "nonce": nonce,
        "signed_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    private = Ed25519PrivateKey.from_private_bytes(_unb64(private_key_base64))
    derived = private.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    if derived != public_raw:
        raise ValueError("private key does not match public-key record")
    envelope = {
        "statement": statement,
        "public_key": public_record,
        "signature_base64": _b64(private.sign(_canonical(statement))),
        "identity_boundary": "Key-possession authentication only; legal identity and trusted time require external verification.",
    }
    envelope_path.parent.mkdir(parents=True, exist_ok=True)
    envelope_path.write_text(json.dumps(envelope, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    entry = {
        "index": len(entries),
        "previous_entry_sha256": entries[-1]["entry_sha256"] if entries else None,
        "event": "BUNDLE_SIGNED",
        "bundle_sha256": statement["bundle_sha256"],
        "key_id": statement["key_id"],
        "nonce": nonce,
        "envelope_sha256": _sha(envelope_path.read_bytes()),
    }
    entry["entry_sha256"] = _sha(_canonical(entry))
    entries.append(entry)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(json.dumps(entries, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return envelope


def verify_signed_bundle(
    bundle_path: str | Path,
    envelope_path: str | Path,
    transparency_log_path: str | Path,
    revocation_registry_path: str | Path | None = None,
) -> dict:
    bundle_check = verify_bundle(bundle_path)
    try:
        envelope_path = Path(envelope_path).resolve()
        envelope = json.loads(envelope_path.read_text(encoding="utf-8"))
        statement = envelope["statement"]
        public_record = envelope["public_key"]
        public_raw = _unb64(public_record["public_key_base64"])
        key_id = _sha(public_raw)
        Ed25519PublicKey.from_public_bytes(public_raw).verify(
            _unb64(envelope["signature_base64"]), _canonical(statement)
        )
    except (OSError, KeyError, ValueError, TypeError, InvalidSignature) as exc:
        return {"valid": False, "error": f"INVALID_SIGNATURE_ENVELOPE:{type(exc).__name__}"}
    revoked = set()
    if revocation_registry_path and Path(revocation_registry_path).exists():
        registry = json.loads(Path(revocation_registry_path).read_text(encoding="utf-8"))
        revoked = {item["key_id"] for item in registry.get("revoked_keys", [])}
    entries = _load_log(Path(transparency_log_path))
    chain_ok, chain_error = _verify_log_chain(entries)
    included = sum(
        entry.get("event") == "BUNDLE_SIGNED"
        and entry.get("bundle_sha256") == statement.get("bundle_sha256")
        and entry.get("key_id") == statement.get("key_id")
        and entry.get("nonce") == statement.get("nonce")
        and entry.get("envelope_sha256") == _sha(envelope_path.read_bytes())
        for entry in entries
    ) == 1
    checks = {
        "bundle_valid": bundle_check.get("valid", False),
        "bundle_digest_matches": statement.get("bundle_sha256") == bundle_check.get("actual_bundle_sha256"),
        "key_id_matches": statement.get("key_id") == public_record.get("key_id") == key_id,
        "key_active": public_record.get("status") == "ACTIVE",
        "key_not_revoked": key_id not in revoked,
        "log_chain_valid": chain_ok,
        "unique_log_inclusion": included,
    }
    return {
        "valid": all(checks.values()),
        "checks": checks,
        "error": chain_error,
        "key_id": key_id,
        "signer": statement.get("signer"),
        "decision_state": bundle_check.get("decision_state"),
    }


def revoke_key(registry_path: str | Path, key_id: str, reason: str) -> dict:
    path = Path(registry_path)
    registry = json.loads(path.read_text()) if path.exists() else {"schema_version": "1.0", "revoked_keys": []}
    if any(item["key_id"] == key_id for item in registry["revoked_keys"]):
        return registry
    registry["revoked_keys"].append({
        "key_id": key_id,
        "reason": reason,
        "revoked_at_utc": datetime.now(timezone.utc).isoformat(),
    })
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n")
    return registry
