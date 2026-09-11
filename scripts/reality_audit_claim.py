#!/usr/bin/env python3
"""Customer-facing claim stress-test evidence bundle CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reality_audit.product.evidence_bundle import build_bundle, verify_bundle


def main() -> int:
    parser = argparse.ArgumentParser(prog="reality-audit-claim")
    sub = parser.add_subparsers(dest="command", required=True)
    compile_parser = sub.add_parser("compile", help="compile a claim manifest into an evidence bundle")
    compile_parser.add_argument("manifest")
    compile_parser.add_argument("output")
    verify_parser = sub.add_parser("verify", help="verify bundle and referenced artifact integrity")
    verify_parser.add_argument("bundle")
    args = parser.parse_args()

    if args.command == "compile":
        result = build_bundle(args.manifest, args.output)
        print(json.dumps({"bundle_sha256": result["bundle_sha256"], "decision": result["decision"]}, indent=2))
        return 0
    result = verify_bundle(args.bundle)
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
