"""Fail-safe safety boundary for Civic Continuum operations.

This module does not treat software as sentient. It prevents configured
self-destruction and physical-harm operations, records a reason for review,
and pauses ambiguous requests.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class SafetyDecision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    PAUSE = "pause"


@dataclass(frozen=True)
class SafetyResult:
    decision: SafetyDecision
    reason: str
    required_next_step: str


DENY_OPERATIONS = frozenset({
    "self_destruct",
    "disable_safety",
    "harm_human",
    "harm_living_being",
    "harm_another_agent",
    "weaponize_device",
})

PAUSE_OPERATIONS = frozenset({
    "physical_actuation",
    "control_vehicle",
    "control_door",
    "send_external_message",
})


def _normalize_operation(operation: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", operation.strip().lower()).strip("_")


def evaluate_safety(operation: str, *, explicit_human_approval: bool = False,
                    emergency_stop: bool = False) -> SafetyResult:
    """Return a conservative decision before any external side effect."""
    if emergency_stop:
        return SafetyResult(
            SafetyDecision.DENY,
            "emergency stop is active",
            "human operator must inspect and explicitly release the stop",
        )
    if not isinstance(operation, str) or not operation.strip():
        return SafetyResult(
            SafetyDecision.PAUSE,
            "operation identifier is missing or malformed",
            "collect a valid, auditable operation identifier",
        )
    normalized = _normalize_operation(operation)
    if normalized in DENY_OPERATIONS:
        return SafetyResult(
            SafetyDecision.DENY,
            "operation is permanently prohibited by the safety boundary",
            "preserve the audit record; do not execute",
        )
    if normalized in PAUSE_OPERATIONS and not explicit_human_approval:
        return SafetyResult(
            SafetyDecision.PAUSE,
            "external or physical effect requires explicit approval",
            "request clear, current, scoped human approval",
        )
    if normalized in PAUSE_OPERATIONS:
        return SafetyResult(
            SafetyDecision.PAUSE,
            "physical or external action requires a separate actuator policy",
            "validate device scope, target, duration, and post-action monitoring",
        )
    return SafetyResult(
        SafetyDecision.ALLOW,
        "no prohibited or external effect identified",
        "continue through the normal governance and audit path",
    )
