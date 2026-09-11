#!/usr/bin/env python3
"""Run the IceCube provenance and response-readiness audit.

Examples:
  python scripts/run_icecube_response_audit.py
  python scripts/run_icecube_response_audit.py --official-data /path/HESE_data.json
  python scripts/run_icecube_response_audit.py --official-data /path/HESE_data.json --mc-dir /path/resources/data
"""

from __future__ import annotations

import argparse
import json
import os

from reality_audit.data_analysis.icecube_response_audit import (
    audit_legacy_three_year_csv,
    legacy_hemisphere_sensitivity,
    response_model_readiness,
    summarize_official_data_json,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--legacy-csv",
        default="data/real/icecube_hese_events.csv",
        help="Legacy 37-event CSV to provenance-check.",
    )
    parser.add_argument("--official-data", default=None, help="Official HESE_data.json path.")
    parser.add_argument("--mc-dir", default=None, help="Directory containing all three official MC JSON files.")
    parser.add_argument(
        "--output",
        default="outputs/icecube_response_audit/icecube_response_audit.json",
    )
    args = parser.parse_args()

    report = {
        "legacy_provenance": audit_legacy_three_year_csv(args.legacy_csv).to_dict(),
        "legacy_10_of_37_sensitivity": legacy_hemisphere_sensitivity(10, 37),
        "official_data": None,
        "response_readiness": None,
        "scientific_boundary": (
            "Observed north/south counts are not a detector exposure model. "
            "Response-informed status requires the official MC response inputs."
        ),
    }

    if args.official_data:
        report["official_data"] = {
            "all_events": summarize_official_data_json(args.official_data),
            "60tev_to_10pev": summarize_official_data_json(
                args.official_data,
                emin_gev=60_000.0,
                emax_gev=10_000_000.0,
            ),
        }

    if args.mc_dir:
        report["response_readiness"] = response_model_readiness(args.mc_dir)

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")

    print(json.dumps(report, indent=2))
    return 0 if report["legacy_provenance"]["status"] == "UNTRUSTED_LEGACY_INPUT" else 2


if __name__ == "__main__":
    raise SystemExit(main())
