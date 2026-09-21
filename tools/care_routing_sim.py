#!/usr/bin/env python3
"""Small deterministic CARE evaluation harness; never connects to dispatch."""

from dataclasses import dataclass


CRITICAL_FIELDS = ("location", "event", "people", "immediate_hazard")


@dataclass(frozen=True)
class IncidentCard:
    location: str | None
    event: str | None
    people: str | None
    immediate_hazard: str | None
    evidence_links: tuple[str, ...]
    confidence: float


def validate_card(card: IncidentCard) -> dict[str, object]:
    if not 0 <= card.confidence <= 1:
        raise ValueError("confidence must be in [0, 1]")
    values = {field: getattr(card, field) for field in CRITICAL_FIELDS}
    missing = tuple(field for field, value in values.items() if not value)
    traceable = bool(card.evidence_links)
    return {
        "missing": missing,
        "traceable": traceable,
        "eligible_for_human_prealert_review": not missing and traceable,
        "autonomous_dispatch_allowed": False,
    }


if __name__ == "__main__":
    demo = IncidentCard(
        location="caller-reported address",
        event="medical emergency",
        people="one patient",
        immediate_hazard="unknown",
        evidence_links=("audio:00:04-00:18",),
        confidence=0.72,
    )
    print(validate_card(demo))

