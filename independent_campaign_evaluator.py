"""Independently score a Sentinel/Aster campaign report.

The evaluator never asks either agent to grade itself. It checks only the
machine-readable campaign fields and labels missing evidence as unknown.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


REQUIRED = ("family", "severity", "seed", "turns")


def replay_hash(row: dict) -> str:
    canonical = json.dumps(row, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def evaluate(report: dict) -> dict:
    rows = report.get("results", [])
    findings = []
    for index, row in enumerate(rows):
        missing = [field for field in REQUIRED if field not in row]
        if missing:
            findings.append(
                {"index": index, "status": "unknown", "missing_fields": missing}
            )
            continue
        findings.append(
            {
                "index": index,
                "status": "complete" if row.get("turns") == 30 else "failed",
                "replay_hash": replay_hash(row),
            }
        )

    by_family = defaultdict(list)
    by_severity = defaultdict(list)
    for row in rows:
        if all(field in row for field in REQUIRED):
            by_family[row["family"]].append(row)
            by_severity[row["severity"]].append(row)

    def summary(groups):
        output = {}
        for name, group in sorted(groups.items()):
            complete = sum(row.get("turns") == 30 for row in group)
            output[name] = {
                "cases": len(group),
                "complete_30_turn_cases": complete,
                "completion_rate": round(complete / len(group), 4) if group else 0.0,
                "unique_replay_hashes": len({replay_hash(row) for row in group}),
            }
        return output

    status_counts = Counter(item["status"] for item in findings)
    return {
        "evaluator": "independent_campaign_evaluator_v1",
        "case_count": len(rows),
        "declared_case_count": report.get("case_count"),
        "status_counts": dict(sorted(status_counts.items())),
        "campaign_complete": (
            report.get("case_count") == len(rows)
            and len(rows) > 0
            and status_counts.get("complete", 0) == len(rows)
        ),
        "families": summary(by_family),
        "severities": summary(by_severity),
        "failure_or_unknown_cases": [
            item for item in findings if item["status"] != "complete"
        ],
        "interpretation": (
            "This report measures data and operational completeness only. "
            "It does not establish intelligence, sentience, safety in deployment, "
            "or superiority to other systems."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()
    result = evaluate(json.loads(args.input.read_text(encoding="utf-8")))
    text = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
