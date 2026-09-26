#!/usr/bin/env python3
"""Validate Civic Continuum legislative control records without dependencies."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ALLOWED_STATUS = {
    "idea", "discussion_draft", "counsel_reviewed", "introduced", "enacted",
    "funded", "operational", "evaluated", "sunset",
}
REQUIRED_TOP_LEVEL = {
    "id", "title", "jurisdiction", "status", "rights", "evidence", "fiscal",
    "transition", "accountability", "anti_capture", "metrics", "stop_conditions", "sunset",
}
REQUIRED_ACCOUNTABILITY = {
    "public_reporting", "privacy_protection", "appeal", "correction_timeline",
    "whistleblower_protection", "independent_audit_or_evaluation",
}
REQUIRED_ANTI_CAPTURE = {
    "open_procurement", "conflict_disclosure", "exclusive_vendor_control",
    "separated_enforcement_and_appeal", "portable_data_and_exit",
}


def validate_program(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_TOP_LEVEL - data.keys())
    if missing:
        errors.append("missing required fields: " + ", ".join(missing))
    if data.get("status") not in ALLOWED_STATUS:
        errors.append("status must use an allowed reality label")
    for field in ("rights", "metrics", "stop_conditions"):
        if not isinstance(data.get(field), list) or not data.get(field):
            errors.append(f"{field} must be a non-empty list")

    accountability = data.get("accountability", {})
    for key in sorted(REQUIRED_ACCOUNTABILITY):
        if accountability.get(key) is not True:
            errors.append(f"accountability.{key} must be true")

    anti_capture = data.get("anti_capture", {})
    for key in sorted(REQUIRED_ANTI_CAPTURE - {"exclusive_vendor_control"}):
        if anti_capture.get(key) is not True:
            errors.append(f"anti_capture.{key} must be true")
    if anti_capture.get("exclusive_vendor_control") is not False:
        errors.append("anti_capture.exclusive_vendor_control must be false")

    transition = data.get("transition", {})
    if transition.get("stable_essentials_first") is not True:
        errors.append("transition.stable_essentials_first must be true")
    if transition.get("existing_support_removed_before_replacement") is not False:
        errors.append("existing support cannot be removed before replacement")

    sunset = data.get("sunset", {})
    if sunset.get("required") is not True:
        errors.append("sunset.required must be true")
    if not isinstance(sunset.get("operational_years"), int) or sunset.get("operational_years", 0) <= 0:
        errors.append("sunset.operational_years must be a positive integer")
    if sunset.get("affirmative_legislative_renewal") is not True:
        errors.append("sunset requires affirmative legislative renewal")

    for index, power in enumerate(data.get("emergency_powers", [])):
        for key in ("trigger", "owner", "public_log", "review", "expiry_days"):
            if key not in power:
                errors.append(f"emergency_powers[{index}] missing {key}")
        expiry = power.get("expiry_days")
        if not isinstance(expiry, int) or expiry <= 0 or expiry > 30:
            errors.append(f"emergency_powers[{index}].expiry_days must be 1..30")
        if power.get("public_log") is not True:
            errors.append(f"emergency_powers[{index}].public_log must be true")
    return errors


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: validate_legislative_program.py PROGRAM.json", file=sys.stderr)
        return 2
    path = Path(argv[1])
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    errors = validate_program(data)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"OK: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
