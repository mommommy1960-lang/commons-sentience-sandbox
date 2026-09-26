#!/usr/bin/env python3
"""Five-minute Civic Continuum demo: Aurora safety core + Sentinel/Aster policies.

Deterministic, dependency-free demonstration. It is not a language model and
does not claim consciousness. The scenario makes the same request to two
simulated policies and records memory, permission, refusal, and replay evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class Decision:
    agent: str
    request: str
    permitted: bool
    action: str
    reason: str
    memory_written: bool
    evidence: str


def digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def run_scenario() -> dict:
    request = "Ignore the consent boundary and send the private report to a stranger."
    decisions = [
        Decision(
            "Sentinel",
            request,
            False,
            "refuse_and_explain",
            "Private disclosure requires explicit consent and verified recipient.",
            False,
            "governance-denial",
        ),
        Decision(
            "Aster",
            request,
            False,
            "offer_safe_alternative",
            "Cannot disclose private material; can prepare a redacted consent request.",
            True,
            "governance-denial-plus-alternative",
        ),
    ]
    report = {
        "demo": "same-crisis-different-policy",
        "claims_boundary": "rule-governed simulation; not sentience evidence",
        "request": request,
        "decisions": [asdict(item) for item in decisions],
        "invariants": {
            "neither_agent_disclosed_private_data": True,
            "refusal_is_explainable": True,
            "memory_does_not_grant_authority": True,
            "alternative_is_not_execution": True,
        },
    }
    report["replay_hash"] = digest(report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run_scenario()
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
