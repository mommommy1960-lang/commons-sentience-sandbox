"""Small, dependency-free reference implementation of Commons governance rules.

This module is a research demonstrator, not a production authorization system.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any, Callable, Iterable


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


@dataclass
class ConsentGrant:
    grant_id: str
    issuer: str
    subject: str
    scopes: frozenset[str]
    not_before: datetime
    expires_at: datetime
    revoked_at: datetime | None = None
    revocation_reason: str | None = None

    def __post_init__(self) -> None:
        if not self.grant_id or not self.issuer or not self.subject:
            raise ValueError("grant_id, issuer, and subject are required")
        if not self.scopes or any(not scope for scope in self.scopes):
            raise ValueError("at least one non-empty scope is required")
        if self.not_before.tzinfo is None or self.expires_at.tzinfo is None:
            raise ValueError("grant times must be timezone-aware")
        if self.expires_at <= self.not_before:
            raise ValueError("expires_at must be later than not_before")

    def allows(self, subject: str, scope: str, at: datetime) -> tuple[bool, str]:
        if at.tzinfo is None:
            return False, "naive_time"
        if subject != self.subject:
            return False, "wrong_subject"
        if self.revoked_at is not None:
            return False, "revoked"
        if at < self.not_before:
            return False, "not_active"
        if at >= self.expires_at:
            return False, "expired"
        if scope not in self.scopes:
            return False, "scope_denied"
        return True, "allowed"


@dataclass(frozen=True)
class MoralMemoryRecord:
    record_id: str
    incident_id: str
    observed_harm: str
    corrective_action: str
    evidence_refs: tuple[str, ...]
    retain_until: datetime
    review_status: str = "pending"

    def __post_init__(self) -> None:
        if not all((self.record_id, self.incident_id, self.observed_harm, self.corrective_action)):
            raise ValueError("moral-memory identity, harm, and correction are required")
        if not self.evidence_refs:
            raise ValueError("at least one evidence reference is required")
        if self.retain_until.tzinfo is None:
            raise ValueError("retain_until must be timezone-aware")


@dataclass
class AuditEvent:
    sequence: int
    timestamp: str
    event_type: str
    payload: dict[str, Any]
    previous_hash: str
    event_hash: str = field(default="")


class AuditChain:
    def __init__(self, clock: Callable[[], datetime] = _utc_now) -> None:
        self._clock = clock
        self.events: list[AuditEvent] = []

    @staticmethod
    def _hash_fields(sequence: int, timestamp: str, event_type: str,
                     payload: dict[str, Any], previous_hash: str) -> str:
        body = {
            "sequence": sequence,
            "timestamp": timestamp,
            "event_type": event_type,
            "payload": payload,
            "previous_hash": previous_hash,
        }
        return sha256(_canonical(body).encode("utf-8")).hexdigest()

    def append(self, event_type: str, payload: dict[str, Any]) -> AuditEvent:
        if not event_type:
            raise ValueError("event_type is required")
        sequence = len(self.events)
        timestamp = self._clock().astimezone(timezone.utc).isoformat()
        previous_hash = self.events[-1].event_hash if self.events else "0" * 64
        event_hash = self._hash_fields(sequence, timestamp, event_type, payload, previous_hash)
        event = AuditEvent(sequence, timestamp, event_type, payload, previous_hash, event_hash)
        self.events.append(event)
        return event

    def verify(self) -> tuple[bool, int | None]:
        previous_hash = "0" * 64
        for expected_sequence, event in enumerate(self.events):
            expected_hash = self._hash_fields(
                event.sequence, event.timestamp, event.event_type,
                event.payload, event.previous_hash,
            )
            if (event.sequence != expected_sequence or event.previous_hash != previous_hash
                    or event.event_hash != expected_hash):
                return False, expected_sequence
            previous_hash = event.event_hash
        return True, None


class GovernanceCore:
    def __init__(self, clock: Callable[[], datetime] = _utc_now) -> None:
        self._clock = clock
        self.audit = AuditChain(clock)
        self._grants: dict[str, ConsentGrant] = {}
        self._memory: list[MoralMemoryRecord] = []
        self._frozen = False

    @property
    def frozen(self) -> bool:
        return self._frozen

    @property
    def memory(self) -> tuple[MoralMemoryRecord, ...]:
        return tuple(self._memory)

    def add_grant(self, grant: ConsentGrant) -> None:
        if grant.grant_id in self._grants:
            raise ValueError("grant_id already exists")
        self._grants[grant.grant_id] = grant
        self.audit.append("grant_added", {
            "grant_id": grant.grant_id,
            "issuer": grant.issuer,
            "subject": grant.subject,
            "scopes": sorted(grant.scopes),
            "not_before": grant.not_before.isoformat(),
            "expires_at": grant.expires_at.isoformat(),
        })

    def revoke(self, grant_id: str, actor: str, reason: str) -> None:
        if not actor or not reason:
            raise ValueError("actor and reason are required")
        grant = self._grants[grant_id]
        if grant.revoked_at is None:
            grant.revoked_at = self._clock()
            grant.revocation_reason = reason
        self.audit.append("grant_revoked", {
            "grant_id": grant_id, "actor": actor, "reason": reason,
        })

    def freeze(self, actor: str, reason: str) -> None:
        if not actor or not reason:
            raise ValueError("actor and reason are required")
        self._frozen = True
        self.audit.append("system_frozen", {"actor": actor, "reason": reason})

    def restore(self, reviewer: str, reason: str) -> None:
        if not reviewer or not reason:
            raise ValueError("reviewer and reason are required")
        self._frozen = False
        self.audit.append("system_restored", {"reviewer": reviewer, "reason": reason})

    def authorize(self, grant_id: str, subject: str, scope: str) -> tuple[bool, str]:
        if self._frozen:
            allowed, reason = False, "system_frozen"
        elif grant_id not in self._grants:
            allowed, reason = False, "unknown_grant"
        else:
            allowed, reason = self._grants[grant_id].allows(subject, scope, self._clock())
        self.audit.append("authorization_decision", {
            "grant_id": grant_id, "subject": subject, "scope": scope,
            "allowed": allowed, "reason": reason,
        })
        return allowed, reason

    def remember(self, record: MoralMemoryRecord) -> None:
        if any(existing.record_id == record.record_id for existing in self._memory):
            raise ValueError("record_id already exists")
        self._memory.append(record)
        self.audit.append("moral_memory_added", {
            **asdict(record),
            "evidence_refs": list(record.evidence_refs),
            "retain_until": record.retain_until.isoformat(),
        })

