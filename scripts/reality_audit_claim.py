#!/usr/bin/env python3
"""Customer-facing claim stress-test evidence bundle CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reality_audit.product.evidence_bundle import build_bundle, verify_bundle
from reality_audit.product.signed_evidence import (
    generate_keypair,
    public_key_record,
    revoke_key,
    sign_bundle,
    verify_signed_bundle,
)


def main() -> int:
    parser = argparse.ArgumentParser(prog="reality-audit-claim")
    sub = parser.add_subparsers(dest="command", required=True)
    compile_parser = sub.add_parser("compile", help="compile a claim manifest into an evidence bundle")
    compile_parser.add_argument("manifest")
    compile_parser.add_argument("output")
    verify_parser = sub.add_parser("verify", help="verify bundle and referenced artifact integrity")
    verify_parser.add_argument("bundle")
    key_parser = sub.add_parser("keygen", help="generate an Ed25519 signing keypair")
    key_parser.add_argument("owner")
    key_parser.add_argument("private_key_file")
    key_parser.add_argument("public_key_file")
    sign_parser = sub.add_parser("sign", help="sign a valid bundle and append its transparency receipt")
    sign_parser.add_argument("bundle")
    sign_parser.add_argument("private_key_file")
    sign_parser.add_argument("public_key_file")
    sign_parser.add_argument("envelope")
    sign_parser.add_argument("transparency_log")
    sign_parser.add_argument("--nonce")
    signed_verify = sub.add_parser("verify-signed", help="verify integrity, identity key, revocation, and log inclusion")
    signed_verify.add_argument("bundle")
    signed_verify.add_argument("envelope")
    signed_verify.add_argument("transparency_log")
    signed_verify.add_argument("--revocations")
    revoke_parser = sub.add_parser("revoke", help="add a key to a local revocation registry")
    revoke_parser.add_argument("registry")
    revoke_parser.add_argument("key_id")
    revoke_parser.add_argument("reason")
    args = parser.parse_args()

    if args.command == "compile":
        result = build_bundle(args.manifest, args.output)
        print(json.dumps({"bundle_sha256": result["bundle_sha256"], "decision": result["decision"]}, indent=2))
        return 0
    if args.command == "keygen":
        keys = generate_keypair()
        private_path = Path(args.private_key_file)
        private_path.write_text(json.dumps({
            "algorithm": keys["algorithm"],
            "key_id": keys["key_id"],
            "private_key_base64": keys["private_key_base64"],
        }, indent=2) + "\n")
        private_path.chmod(0o600)
        Path(args.public_key_file).write_text(
            json.dumps(public_key_record(keys, args.owner), indent=2, sort_keys=True) + "\n"
        )
        print(json.dumps({"key_id": keys["key_id"], "private_mode": "0600"}, indent=2))
        return 0
    if args.command == "sign":
        private = json.loads(Path(args.private_key_file).read_text())
        public = json.loads(Path(args.public_key_file).read_text())
        envelope = sign_bundle(
            args.bundle, args.envelope, private["private_key_base64"], public,
            args.transparency_log, nonce=args.nonce,
        )
        print(json.dumps({"key_id": envelope["statement"]["key_id"], "nonce": envelope["statement"]["nonce"]}, indent=2))
        return 0
    if args.command == "verify-signed":
        result = verify_signed_bundle(
            args.bundle, args.envelope, args.transparency_log, args.revocations
        )
        print(json.dumps(result, indent=2))
        return 0 if result["valid"] else 2
    if args.command == "revoke":
        result = revoke_key(args.registry, args.key_id, args.reason)
        print(json.dumps(result, indent=2))
        return 0
    result = verify_bundle(args.bundle)
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
