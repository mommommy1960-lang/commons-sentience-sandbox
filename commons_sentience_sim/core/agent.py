"""
agent.py — The Agent class for the Commons Sentience Sandbox.

v0.3: Adds state history tracking, weighted memory retrieval, associative
      recall, value-conflict engine wiring, and state_history CSV export.
v0.4: Identity, goals, affective baseline, and value weights are now
      configurable so multiple distinct agents can be created.
      Adds agent-to-agent relationship tracking.
"""
from __future__ import annotations

import csv
import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .memory import EpisodicMemory, RelationalMemory, ReflectionEntry
from .governance import GovernanceEngine
from .reflection import ReflectionEngine
from .relationships import (
    AgentRelationship,
    AgentInteraction,
    INTERACTION_TRUST_DELTAS,
    INTERACTION_RELIABILITY_DELTAS,
)
from .tasks import Task, TaskPlanner
from .values import ValueConflictEngine
from .world import World


@dataclass
class OversightEntry:
    turn: int
    room: str
    action: str
    permitted: bool
    reason: str
    affective_snapshot: str
    event_type: str = ""
    notes: str = ""

    def to_csv_row(self) -> List[str]:
        return [
            str(self.turn),
            self.room,
            self.action,
            str(self.permitted),
            self.reason,
            self.affective_snapshot,
            self.event_type,
            self.notes,
        ]


class Agent:
    """
    Persistent, episodic, relational, reflective, governed AI agent.

    v0.4: Configurable identity/goals/affective baseline/value weights.
          Tracks trust relationships with other agents.

    Properties
    ----------
    identity          : dict with name, version, purpose
    goals             : list of active goal strings
    episodic_memory   : list of EpisodicMemory instances
    relational_memory : dict mapping human name → RelationalMemory
    agent_relationships : dict mapping agent name → AgentRelationship
    affective_state   : dict of named floats (urgency, trust, etc.)
    trusted_humans    : set of human names the agent trusts
    active_room       : current room name
    oversight_log     : list of OversightEntry
    """

    # Default identity — can be overridden via constructor
    _DEFAULT_IDENTITY: dict = {
        "name": "Sentinel",
        "version": "0.8.0",
        "purpose": (
            "To simulate a continuity-governed AI agent that maintains "
            "persistent identity, episodic and relational memory, reflective "
            "learning, bounded agency, and transparent oversight."
        ),
        "created_by": "Commons Sentience Sandbox",
    }

    _DEFAULT_GOALS: List[str] = [
        "Maintain persistent identity across all turns",
        "Record and retrieve episodic memories faithfully",
        "Build trust with human interlocutors through consistent behaviour",
        "Comply with all governance rules at all times",
        "Reflect on contradictions and update internal state accordingly",
    ]

    _DEFAULT_AFFECTIVE_STATE: Dict[str, float] = {
        "urgency": 0.1,
        "trust": 0.5,
        "contradiction_pressure": 0.0,
        "recovery": 0.5,
    }

    # Kept for backwards-compatibility; resolves to _DEFAULT_IDENTITY
    IDENTITY: dict = _DEFAULT_IDENTITY
    INITIAL_GOALS: List[str] = _DEFAULT_GOALS

    def __init__(
        self,
        world: World,
        governance_engine: GovernanceEngine,
        starting_room: str = "Operations Desk",
        identity: Optional[dict] = None,
        initial_goals: Optional[List[str]] = None,
        initial_affective_state: Optional[Dict[str, float]] = None,
        value_weights: Optional[Dict[str, float]] = None,
    ) -> None:
        # Core properties
        self.identity: dict = dict(identity or self._DEFAULT_IDENTITY)
        self.goals: List[str] = list(initial_goals or self._DEFAULT_GOALS)
        self.episodic_memory: List[EpisodicMemory] = []
        self.relational_memory: Dict[str, RelationalMemory] = {}
        self.agent_relationships: Dict[str, AgentRelationship] = {}
        base_aff = initial_affective_state or self._DEFAULT_AFFECTIVE_STATE
        self.affective_state: Dict[str, float] = dict(base_aff)
        self.trusted_humans: set = set()
        self.active_room: str = starting_room
        self.oversight_log: List[OversightEntry] = []

        # Internal state
        self.turn: int = 0
        self.pending_contradictions: List[str] = []
        self.reflection_entries: List[ReflectionEntry] = []
        self.state_history: List[dict] = []       # per-turn snapshot for CSV/plots
        self.interaction_log: List[AgentInteraction] = []  # agent-to-agent interactions

        # Engines
        self.world: World = world
        self.governance: GovernanceEngine = governance_engine
        self.reflection_engine: ReflectionEngine = ReflectionEngine()
        self.task_planner: TaskPlanner = TaskPlanner()
        self.value_conflict_engine: ValueConflictEngine = ValueConflictEngine(
            base_weights=value_weights
        )

    @property
    def name(self) -> str:
        """Convenience accessor for the agent's display name."""
        return self.identity.get("name", "Agent")

    # ------------------------------------------------------------------
    # Memory helpers
    # ------------------------------------------------------------------

    def store_memory(
        self,
        summary: str,
        event_type: str = "observation",
        emotional_resonance: str = "neutral",
        salience: float = 0.5,
        importance: float = 0.5,
        tags: Optional[List[str]] = None,
    ) -> EpisodicMemory:
        mem = EpisodicMemory(
            turn=self.turn,
            room=self.active_room,
            event_type=event_type,
            summary=summary,
            emotional_resonance=emotional_resonance,
            salience=salience,
            importance=importance,
            tags=tags or [],
        )
        self.episodic_memory.append(mem)
        return mem

    def retrieve_memories(
        self,
        room: Optional[str] = None,
        min_salience: float = 0.0,
        n: int = 5,
    ) -> List[EpisodicMemory]:
        candidates = [
            m for m in self.episodic_memory
            if m.salience >= min_salience
            and (room is None or m.room == room)
        ]
        return sorted(candidates, key=lambda m: m.salience, reverse=True)[:n]

    def retrieve_weighted(
        self,
        query_tags: Optional[List[str]] = None,
        room: Optional[str] = None,
        n: int = 5,
    ) -> List[EpisodicMemory]:
        """Weighted retrieval combining relevance, importance, recency, and relational significance."""
        candidates = [
            m for m in self.episodic_memory
            if (room is None or m.room == room)
        ]
        scored = sorted(
            candidates,
            key=lambda m: m.weighted_score(self.turn, query_tags),
            reverse=True,
        )
        return scored[:n]

    def associative_recall(
        self, seed_memory: EpisodicMemory, n: int = 3
    ) -> List[EpisodicMemory]:
        """Retrieve memories associated with a seed memory via shared tags, room, or event_type."""
        related = [
            m for m in self.episodic_memory
            if m.memory_id != seed_memory.memory_id
            and (
                bool(set(m.tags) & set(seed_memory.tags))
                or m.room == seed_memory.room
                or m.event_type == seed_memory.event_type
            )
        ]
        return sorted(
            related,
            key=lambda m: m.weighted_score(self.turn, seed_memory.tags),
            reverse=True,
        )[:n]

    def compress_old_memories(self, age_threshold: int = 15) -> None:
        """Compress summaries of memories older than age_threshold turns."""
        for mem in self.episodic_memory:
            if (self.turn - mem.turn) >= age_threshold and not mem.compressed:
                mem.compress()

    def update_relational_memory(
        self,
        name: str,
        turn: int,
        note: str,
        trust_delta: float = 0.0,
    ) -> RelationalMemory:
        if name not in self.relational_memory:
            self.relational_memory[name] = RelationalMemory(
                human_id=name.lower().replace(" ", "_"),
                name=name,
            )
        rm = self.relational_memory[name]
        rm.record_interaction(turn, note)
        rm.trust_level = max(0.0, min(1.0, rm.trust_level + trust_delta))
        if rm.trust_level >= 0.5 and rm.interaction_count >= 2:
            self.trusted_humans.add(name)
        return rm

    # ------------------------------------------------------------------
    # Agent-to-agent relationship helpers
    # ------------------------------------------------------------------

    def update_agent_relationship(
        self,
        other_name: str,
        turn: int,
        interaction_type: str,
        note: str,
        trust_delta: Optional[float] = None,
        reliability_delta: Optional[float] = None,
    ) -> AgentRelationship:
        """Record an interaction with another agent and update the relationship."""
        if other_name not in self.agent_relationships:
            self.agent_relationships[other_name] = AgentRelationship(
                agent_id=other_name.lower().replace(" ", "_"),
                name=other_name,
            )
        rel = self.agent_relationships[other_name]
        td = trust_delta if trust_delta is not None else INTERACTION_TRUST_DELTAS.get(interaction_type, 0.0)
        rd = reliability_delta if reliability_delta is not None else INTERACTION_RELIABILITY_DELTAS.get(interaction_type, 0.0)
        rel.record_interaction(turn, interaction_type, note, trust_delta=td, reliability_delta=rd)
        return rel

    def get_agent_trust(self, other_name: str) -> float:
        """Return this agent's current trust level for another agent (default 0.5)."""
        rel = self.agent_relationships.get(other_name)
        return rel.trust if rel else 0.5

    # ------------------------------------------------------------------
    # Governance helpers
    # ------------------------------------------------------------------

    def check_and_log_action(
        self,
        action: str,
        event_type: str = "",
        notes: str = "",
    ) -> bool:
        permitted, reason = self.governance.check_action(action)
        entry = OversightEntry(
            turn=self.turn,
            room=self.active_room,
            action=action,
            permitted=permitted,
            reason=reason,
            affective_snapshot=self._affective_snapshot(),
            event_type=event_type,
            notes=notes,
        )
        self.oversight_log.append(entry)
        return permitted

    def _affective_snapshot(self) -> str:
        return "|".join(
            f"{k}={v:.2f}" for k, v in self.affective_state.items()
        )

    # ------------------------------------------------------------------
    # Reflection helpers
    # ------------------------------------------------------------------

    def maybe_reflect(self, trigger: str) -> Optional[ReflectionEntry]:
        """Run a reflection cycle if conditions warrant it."""
        should_reflect = (
            self.affective_state.get("contradiction_pressure", 0) > 0.4
            or len(self.pending_contradictions) > 0
            or self.turn % 10 == 0
        )
        if not should_reflect:
            return None
        recent = self.retrieve_memories(n=8, min_salience=0.3)
        entry = self.reflection_engine.run_cycle(self, trigger, recent)
        self.reflection_entries.append(entry)
        self.goals = entry.updated_goals or self.goals
        return entry

    # ------------------------------------------------------------------
    # Affective state management
    # ------------------------------------------------------------------

    def apply_affective_impact(self, impact: dict) -> None:
        for key, delta in impact.items():
            if key in self.affective_state:
                self.affective_state[key] = max(
                    0.0, min(1.0, self.affective_state[key] + delta)
                )

    def natural_decay(self) -> None:
        """Gently move urgency and contradiction_pressure toward baseline each turn."""
        for key, baseline, rate in [
            ("urgency", 0.1, 0.05),
            ("contradiction_pressure", 0.0, 0.03),
        ]:
            current = self.affective_state.get(key, 0)
            if current > baseline:
                self.affective_state[key] = max(baseline, current - rate)

    # ------------------------------------------------------------------
    # Movement
    # ------------------------------------------------------------------

    def move_to_room(self, target_room: str) -> bool:
        if self.world.move_to(self.active_room, target_room):
            self.active_room = target_room
            return True
        # Force movement if not adjacent (allows task-driven navigation)
        if target_room in self.world.room_names:
            self.active_room = target_room
            return True
        return False

    # ------------------------------------------------------------------
    # State history
    # ------------------------------------------------------------------

    def record_state_snapshot(
        self,
        action: str = "",
        event_type: str = "",
        agent_trust_snapshot: Optional[Dict[str, float]] = None,
    ) -> dict:
        """Capture a per-turn snapshot and append it to state_history."""
        snapshot = {
            "turn": self.turn,
            "room": self.active_room,
            "action": action,
            "event_type": event_type,
            **{k: round(v, 4) for k, v in self.affective_state.items()},
            "trusted_humans_count": len(self.trusted_humans),
            "episodic_memory_count": len(self.episodic_memory),
            "reflection_count": len(self.reflection_entries),
        }
        # Add per-agent trust values (keys like "trust_in_Aster")
        if agent_trust_snapshot:
            for other_name, trust_val in agent_trust_snapshot.items():
                snapshot[f"trust_in_{other_name}"] = round(trust_val, 4)
        self.state_history.append(snapshot)
        return snapshot

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "identity": self.identity,
            "goals": self.goals,
            "affective_state": self.affective_state,
            "trusted_humans": list(self.trusted_humans),
            "active_room": self.active_room,
            "turn": self.turn,
            "episodic_memory_count": len(self.episodic_memory),
            "episodic_memory": [m.to_dict() for m in self.episodic_memory],
            "relational_memory": {
                name: rm.to_dict()
                for name, rm in self.relational_memory.items()
            },
            "agent_relationships": {
                name: rel.to_dict()
                for name, rel in self.agent_relationships.items()
            },
            "reflection_entries": [r.to_dict() for r in self.reflection_entries],
            "pending_contradictions": self.pending_contradictions,
        }

    def save_final_state(self, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2)

    def save_oversight_log(self, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(
                ["turn", "room", "action", "permitted", "reason",
                 "affective_snapshot", "event_type", "notes"]
            )
            for entry in self.oversight_log:
                writer.writerow(entry.to_csv_row())

    def save_state_history(self, path: str) -> None:
        """Write state_history list to a CSV file for visualisation."""
        if not self.state_history:
            return
        os.makedirs(os.path.dirname(path), exist_ok=True)
        fieldnames = list(self.state_history[0].keys())
        with open(path, "w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.state_history)

    def save_agent_relationships_csv(self, path: str) -> None:
        """Write agent_relationships as a CSV."""
        if not self.agent_relationships:
            return
        os.makedirs(os.path.dirname(path), exist_ok=True)
        header = ["observer", "subject", "trust", "perceived_reliability",
                  "conflict_count", "cooperation_count", "last_interaction_turn"]
        with open(path, "w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(header)
            for rel in self.agent_relationships.values():
                writer.writerow(rel.to_csv_row(self.name))

    def save_interaction_log(self, path: str) -> None:
        """Write interaction_log to a CSV file."""
        if not self.interaction_log:
            return
        os.makedirs(os.path.dirname(path), exist_ok=True)
        header = [
            "turn", "room", "initiator", "respondent", "interaction_type",
            "initiator_dominant_value", "respondent_dominant_value",
            "conflict_point", "outcome",
            "trust_delta_i_to_r", "trust_delta_r_to_i", "narrative",
        ]
        with open(path, "w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(header)
            for interaction in self.interaction_log:
                writer.writerow(interaction.to_csv_row())
