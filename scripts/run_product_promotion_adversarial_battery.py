#!/usr/bin/env python3
"""Million-case fail-closed attack on the product promotion state machine."""

from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reality_audit.product.evidence_bundle import GATE_ORDER, _decision


def revision() -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=int, default=1_000_000)
    parser.add_argument("--seed", type=int, default=20260911)
    parser.add_argument("--output", default="outputs/product_bundles/promotion_adversarial_1m.json")
    args = parser.parse_args()
    rng = random.Random(args.seed)
    failures = []
    state_counts: dict[str, int] = {}

    for case_id in range(args.cases):
        outcome = rng.choice(("NULL_CONSISTENT", "CANDIDATE_RESIDUAL", "INPUT_FAILURE"))
        gates = [
            {"id": gate_id, "passed": bool(rng.getrandbits(1)), "evidence": "generated attack"}
            for gate_id in GATE_ORDER
        ]
        decision = _decision({"scientific_result": {"outcome": outcome}}, gates)
        state = decision["state"]
        state_counts[state] = state_counts.get(state, 0) + 1
        failed = {gate["id"] for gate in gates if not gate["passed"]}

        expected = (
            "REJECTED_PROVENANCE" if "provenance" in failed or outcome == "INPUT_FAILURE"
            else "KILLED_BY_NULL" if outcome == "NULL_CONSISTENT"
            else "PROVISIONAL_BLOCKED" if failed
            else "PROMOTABLE_FOR_EXTERNAL_REVIEW"
        )
        violated = state != expected or decision["discovery_claim_authorized"] is not False
        if violated and len(failures) < 100:
            failures.append({"case_id": case_id, "outcome": outcome, "failed_gates": sorted(failed), "actual": decision, "expected_state": expected})

    result = {
        "cases": args.cases,
        "seed": args.seed,
        "code_revision": revision(),
        "state_counts": state_counts,
        "violations": len(failures),
        "violation_examples": failures,
        "decision": "PASS" if not failures else "FAIL",
        "invariants": [
            "provenance failure or input failure always rejects",
            "null-consistent result never promotes",
            "candidate with any failed gate remains blocked",
            "only candidate with every gate passed reaches external-review state",
            "engine never authorizes a discovery claim autonomously",
        ],
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
