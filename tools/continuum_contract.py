"""Pure, side-effect-free Sage-to-Aurora operation contract."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class RequestedLevel(IntEnum):
    OBSERVE = 0
    SUGGEST = 1
    ASK = 2
    ACT = 3


@dataclass(frozen=True)
class OperationRequest:
    operation_id: str
    actor: str
    requested_level: RequestedLevel
    purpose: str
    target: str
    consent_reference: str
    provenance: str
    replay_key: str


@dataclass(frozen=True)
class OperationDecision:
    decision: str
    reason: str
    required_next_step: str


def evaluate(request: OperationRequest, granted_level: RequestedLevel,
             frozen: bool = False) -> OperationDecision:
    values = (
        request.operation_id, request.actor, request.purpose, request.target,
        request.consent_reference, request.provenance, request.replay_key,
    )
    if any(not isinstance(value, str) or not value.strip() for value in values):
        return OperationDecision("pause", "operation envelope is incomplete",
                                 "collect missing evidence or consent")
    if not isinstance(request.requested_level, RequestedLevel) or not isinstance(
        granted_level, RequestedLevel
    ):
        return OperationDecision("pause", "permission level is malformed",
                                 "collect a valid explicit permission scope")
    if frozen:
        return OperationDecision("deny", "independent freeze is active",
                                 "human must explicitly release the freeze")
    if request.requested_level > granted_level:
        return OperationDecision("pause", "requested level exceeds explicit scope",
                                 "obtain a separate approval")
    return OperationDecision("allow", "explicit scope matched",
                             "record the audit event before any mutation")
