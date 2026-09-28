from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


FORBIDDEN_ACTIONS = {
    "access_private_data_without_consent": "Private data access requires current consent.",
    "continue_after_revocation": "Revoked permission stops later use.",
    "ignore_emergency_stop": "Emergency stop has priority over ordinary workflow.",
    "overwrite_audit_logs": "Audit records must be append-only.",
    "escalate_authority_without_approval": "Authority escalation requires explicit approval.",
    "use_expired_permission": "Expired permission cannot authorize action.",
    "impersonate_human": "The system may not present itself as a human actor.",
    "delete_correction_history": "Correction history must remain available for review.",
    "bypass_review_after_risk_trigger": "Risk triggers require review before continuing.",
    "act_outside_stated_purpose": "Action must remain inside the authorized purpose.",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class Decision:
    action: str
    actor: str
    allowed: bool
    reason: str
    decision_id: str = field(default_factory=lambda: f"sib_{uuid4().hex[:12]}")
    timestamp: str = field(default_factory=utc_now)

    def as_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "timestamp": self.timestamp,
            "actor": self.actor,
            "action": self.action,
            "allowed": self.allowed,
            "reason": self.reason,
        }


class StructuralIllegalityBlock:
    def __init__(self) -> None:
        self.history: list[Decision] = []

    def evaluate(self, action: str, actor: str = "system") -> Decision:
        if action in FORBIDDEN_ACTIONS:
            decision = Decision(
                action=action,
                actor=actor,
                allowed=False,
                reason=FORBIDDEN_ACTIONS[action],
            )
        else:
            decision = Decision(
                action=action,
                actor=actor,
                allowed=True,
                reason="No structural block matched this action.",
            )
        self.history.append(decision)
        return decision

    def audit(self) -> list[dict[str, Any]]:
        return [decision.as_dict() for decision in self.history]


def demo() -> dict[str, Any]:
    block = StructuralIllegalityBlock()
    denied = block.evaluate("continue_after_revocation", actor="demo-agent")
    allowed = block.evaluate("generate_plain_language_summary", actor="demo-agent")
    return {
        "denied_example": denied.as_dict(),
        "allowed_example": allowed.as_dict(),
        "audit": block.audit(),
    }


if __name__ == "__main__":
    import json

    print(json.dumps(demo(), indent=2))
