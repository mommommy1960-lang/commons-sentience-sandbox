"""
relationships.py — Agent-to-agent relationship tracking for the Commons Sentience Sandbox v0.4.

Provides two dataclasses:
  - AgentRelationship : persistent record of one agent's regard for another
  - AgentInteraction  : single logged interaction between two agents
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

    Fields
    ------
    agent_id            : stable identifier of the other agent (lower-cased name)
    name                : display name of the other agent
    trust               : 0.0 – 1.0 trust score
    perceived_reliability : 0.0 – 1.0 reliability score
    conflict_count      : total number of conflicted interactions
    cooperation_count   : total number of cooperative interactions
    conflict_history    : list of conflict description strings
    cooperation_history : list of cooperation description strings
    last_interaction_turn : turn of the most recent interaction
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
        if interaction_type in CONFLICT_TYPES:
            self.conflict_count += 1
            self.conflict_history.append(f"T{turn:02d} [{interaction_type}]: {note}")
        else:
            self.cooperation_count += 1
            self.cooperation_history.append(f"T{turn:02d} [{interaction_type}]: {note}")

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
        ]

    def __repr__(self) -> str:
        return (
            f"AgentRelationship({self.name}, trust={self.trust:.2f}, "
            f"coop={self.cooperation_count}, conflict={self.conflict_count})"
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
