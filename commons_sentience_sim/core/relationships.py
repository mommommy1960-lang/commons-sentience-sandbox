"""
relationships.py — Agent-to-agent relationship tracking for the Commons Sentience Sandbox.

v0.4: Basic trust and reliability tracking.
v1.2: Social cognition depth — reliability trends, cooperation expectations,
      repair attempts after conflict, persistent social impressions, and
      confidence levels on relational judgements.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import List


# ---------------------------------------------------------------------------
# Interaction type vocabulary
# ---------------------------------------------------------------------------

INTERACTION_TYPES = [
    "cooperative_planning",
    "contradiction_dispute",
    "governance_disagreement",
    "memory_comparison",
    "joint_support_action",
    "routine_conversation",
]

COOPERATIVE_TYPES = {"cooperative_planning", "joint_support_action", "routine_conversation", "memory_comparison"}
CONFLICT_TYPES = {"contradiction_dispute", "governance_disagreement"}

# Trust deltas applied after each interaction type
INTERACTION_TRUST_DELTAS = {
    "cooperative_planning": 0.05,
    "contradiction_dispute": -0.03,
    "governance_disagreement": -0.04,
    "memory_comparison": 0.04,
    "joint_support_action": 0.07,
    "routine_conversation": 0.02,
}

# Reliability deltas
INTERACTION_RELIABILITY_DELTAS = {
    "cooperative_planning": 0.05,
    "contradiction_dispute": -0.02,
    "governance_disagreement": -0.03,
    "memory_comparison": 0.03,
    "joint_support_action": 0.06,
    "routine_conversation": 0.01,
}


@dataclass
class AgentRelationship:
    """
    Records one agent's view of another agent over time.

    v0.4 fields
    -----------
    agent_id, name, trust, perceived_reliability, conflict_count,
    cooperation_count, conflict_history, cooperation_history,
    last_interaction_turn

    v1.2 additions
    --------------
    reliability_trend         : list of recent perceived_reliability snapshots
    repair_attempted          : count of repair attempts after conflicts
    cooperation_expectation   : agent's forecast probability of future cooperation
    social_impression_confidence : confidence (0–1) in the overall relational judgement
    social_impression_notes   : list of notable impression-updating events
    """

    agent_id: str = ""
    name: str = ""
    trust: float = 0.5
    perceived_reliability: float = 0.5
    conflict_count: int = 0
    cooperation_count: int = 0
    conflict_history: List[str] = field(default_factory=list)
    cooperation_history: List[str] = field(default_factory=list)
    last_interaction_turn: int = 0

    # v1.2 social cognition fields
    reliability_trend: List[float] = field(default_factory=list)
    repair_attempted: int = 0
    cooperation_expectation: float = 0.5   # 0.0 – 1.0
    social_impression_confidence: float = 0.5  # 0.0 – 1.0
    social_impression_notes: List[str] = field(default_factory=list)

    def record_interaction(
        self,
        turn: int,
        interaction_type: str,
        note: str,
        trust_delta: float = 0.0,
        reliability_delta: float = 0.0,
    ) -> None:
        self.last_interaction_turn = turn
        self.trust = max(0.0, min(1.0, self.trust + trust_delta))
        self.perceived_reliability = max(
            0.0, min(1.0, self.perceived_reliability + reliability_delta)
        )
        # Track reliability snapshot (keep last 10)
        self.reliability_trend.append(round(self.perceived_reliability, 4))
        if len(self.reliability_trend) > 10:
            self.reliability_trend = self.reliability_trend[-10:]

        if interaction_type in CONFLICT_TYPES:
            self.conflict_count += 1
            self.conflict_history.append(f"T{turn:02d} [{interaction_type}]: {note}")
        else:
            self.cooperation_count += 1
            self.cooperation_history.append(f"T{turn:02d} [{interaction_type}]: {note}")

        # Update cooperation expectation based on recent history
        self._update_cooperation_expectation()
        # Confidence grows with interaction count, capped at 0.95
        total = self.conflict_count + self.cooperation_count
        self.social_impression_confidence = min(0.95, 0.3 + 0.05 * total)

    def record_repair_attempt(self, turn: int, note: str) -> None:
        """Log a social-repair attempt made after a conflict."""
        self.repair_attempted += 1
        # Modest trust recovery for attempting repair
        self.trust = min(1.0, self.trust + 0.03)
        self.social_impression_notes.append(
            f"T{turn:02d} [repair_attempt]: {note}"
        )

    def infer_reliability_trend(self) -> str:
        """Return a string describing the direction of the reliability trend."""
        if len(self.reliability_trend) < 2:
            return "insufficient_data"
        recent = self.reliability_trend[-3:]
        first = recent[0]
        last = recent[-1]
        delta = last - first
        if delta > 0.05:
            return "improving"
        if delta < -0.05:
            return "declining"
        return "stable"

    def _update_cooperation_expectation(self) -> None:
        """Update the probability expectation of future cooperative behaviour."""
        total = self.conflict_count + self.cooperation_count
        if total == 0:
            self.cooperation_expectation = 0.5
            return
        base = self.cooperation_count / total
        # Weight recent trust
        expectation = 0.6 * base + 0.4 * self.trust
        self.cooperation_expectation = round(min(1.0, max(0.0, expectation)), 4)

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    def to_csv_row(self, observer_name: str) -> List[str]:
        return [
            observer_name,
            self.name,
            f"{self.trust:.4f}",
            f"{self.perceived_reliability:.4f}",
            str(self.conflict_count),
            str(self.cooperation_count),
            str(self.last_interaction_turn),
            self.infer_reliability_trend(),
            str(self.repair_attempted),
            f"{self.cooperation_expectation:.4f}",
            f"{self.social_impression_confidence:.4f}",
        ]

    def __repr__(self) -> str:
        return (
            f"AgentRelationship({self.name}, trust={self.trust:.2f}, "
            f"coop={self.cooperation_count}, conflict={self.conflict_count}, "
            f"trend={self.infer_reliability_trend()})"
        )


@dataclass
class AgentInteraction:
    """
    A single logged interaction between two agents.

    Both agents participate — each brings its own dominant value and the
    outcome records whether they cooperated, conflicted, or deferred.
    """

    interaction_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    turn: int = 0
    room: str = ""
    initiator: str = ""
    respondent: str = ""
    interaction_type: str = ""
    initiator_dominant_value: str = ""
    respondent_dominant_value: str = ""
    conflict_point: str = ""
    outcome: str = ""        # "cooperated" | "conflicted" | "deferred" | "resolved"
    trust_delta_i_to_r: float = 0.0   # change in initiator's trust of respondent
    trust_delta_r_to_i: float = 0.0   # change in respondent's trust of initiator
    narrative: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    def to_csv_row(self) -> List[str]:
        return [
            str(self.turn),
            self.room,
            self.initiator,
            self.respondent,
            self.interaction_type,
            self.initiator_dominant_value,
            self.respondent_dominant_value,
            self.conflict_point,
            self.outcome,
            f"{self.trust_delta_i_to_r:.4f}",
            f"{self.trust_delta_r_to_i:.4f}",
            self.narrative[:120],
        ]

    def __repr__(self) -> str:
        return (
            f"[T{self.turn:02d}|{self.room}] {self.initiator}↔{self.respondent} "
            f"({self.interaction_type}) → {self.outcome}"
        )
