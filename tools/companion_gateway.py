"""Hardware-neutral companion interface with an explicit safety boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from tools.continuum_contract import (
    OperationDecision,
    OperationRequest,
    RequestedLevel,
    evaluate,
)
from tools.safety_boundary import SafetyDecision, evaluate_safety


@dataclass(frozen=True)
class DeviceEvent:
    kind: str
    payload: dict


class DeviceDriver(Protocol):
    def observe(self) -> list[DeviceEvent]: ...
    def emit(self, event: DeviceEvent) -> None: ...


class CompanionGateway:
    """Routes observations and approved suggestions without hidden actuation."""

    def __init__(self, granted_level: RequestedLevel = RequestedLevel.OBSERVE):
        self.granted_level = granted_level
        self.frozen = False
        self.events: list[DeviceEvent] = []

    def ingest(self, event: DeviceEvent) -> None:
        self.events.append(event)

    def request(self, operation: OperationRequest) -> OperationDecision:
        safety = evaluate_safety(operation.target, emergency_stop=self.frozen)
        if safety.decision is not SafetyDecision.ALLOW:
            return OperationDecision(safety.decision.value, safety.reason,
                                     safety.required_next_step)
        return evaluate(operation, self.granted_level, frozen=self.frozen)
