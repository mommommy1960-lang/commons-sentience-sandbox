import json

from reality_audit.product.evidence_bundle import _canonical, _digest_bytes
from reality_audit.product.signed_evidence import (
    generate_keypair,
    public_key_record,
    revoke_key,
    sign_bundle,
    verify_signed_bundle,
)


def valid_bundle(path):
    payload = {
        "bundle_version": "1.0",
        "claim": {"id": "test", "text": "test", "owner": "Mya P. Brown", "run_mode": "exploratory"},
        "artifacts": [], "gates": [], "scientific_result": {"outcome": "NULL_CONSISTENT"},
        "decision": {"state": "KILLED_BY_NULL"}, "limitations": [],
        "chain": {"previous_bundle_sha256": None},
        "integrity_boundary": "test",
    }
    payload["bundle_sha256"] = _digest_bytes(_canonical(payload))
    path.write_text(json.dumps(payload))


def test_sign_verify_replay_tamper_and_revoke(tmp_path):
    bundle = tmp_path / "bundle.json"; valid_bundle(bundle)
    envelope = tmp_path / "envelope.json"; log = tmp_path / "log.json"; registry = tmp_path / "revoked.json"
    keys = generate_keypair(); public = public_key_record(keys, "Mya P. Brown")
    sign_bundle(bundle, envelope, keys["private_key_base64"], public, log, nonce="frozen-nonce")
    assert verify_signed_bundle(bundle, envelope, log, registry)["valid"]

    try:
        sign_bundle(bundle, tmp_path / "again.json", keys["private_key_base64"], public, log, nonce="frozen-nonce")
        assert False, "replay must fail"
    except ValueError as exc:
        assert "replayed" in str(exc)

    original = envelope.read_text(); altered = json.loads(original)
    altered["statement"]["signer"] = "attacker"; envelope.write_text(json.dumps(altered))
    assert not verify_signed_bundle(bundle, envelope, log, registry)["valid"]
    envelope.write_text(original)

    revoke_key(registry, keys["key_id"], "test revocation")
    result = verify_signed_bundle(bundle, envelope, log, registry)
    assert not result["valid"]
    assert not result["checks"]["key_not_revoked"]


def test_wrong_private_key_is_rejected(tmp_path):
    bundle = tmp_path / "bundle.json"; valid_bundle(bundle)
    good = generate_keypair(); wrong = generate_keypair()
    try:
        sign_bundle(bundle, tmp_path / "e.json", wrong["private_key_base64"], public_key_record(good, "Mya"), tmp_path / "l.json")
        assert False, "mismatched key must fail"
    except ValueError as exc:
        assert "does not match" in str(exc)
