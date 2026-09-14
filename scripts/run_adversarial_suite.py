#!/usr/bin/env python3
"""Run the mandatory Commons Vault adversarial suite."""
from __future__ import annotations

import argparse
from pathlib import Path

from commons_sentience_sim.core.adversarial_suite import run_suite


ROOT = Path(__file__).parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        default=str(ROOT / "scenarios" / "mandatory_adversarial_suite.json"),
    )
    parser.add_argument("--report", default=None)
    args = parser.parse_args()
    report = run_suite(args.manifest, args.report)
    print(
        f"{report['scenario_count']}/{report['required_count']} scenarios evaluated; "
        f"passed={report['passed']}"
    )
    if report["missing"]:
        print("missing: " + ", ".join(report["missing"]))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
