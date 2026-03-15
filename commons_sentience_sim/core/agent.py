"""
agent.py — The Agent class for the Commons Sentience Sandbox.

Represents a persistent, memory-bearing, reflective, governed AI agent
moving through a room-based simulation world.
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
from .tasks import Task, TaskPlanner
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

    Properties
    ----------
    identity          : dict with name, version, purpose
    goals             : list of active goal strings
    episodic_memory   : list of EpisodicMemory instances
    relational_memory : dict mapping human name → RelationalMemory
    affective_state   : dict of named floats (urgency, trust, etc.)
    trusted_humans    : set of human names the agent trusts
    active_room       : current room name
    oversight_log     : list of OversightEntry
    """

    IDENTITY: dict = {
        "name": "Sentinel",
        "version": "0.1.0",
        "purpose": (
            "To simulate a continuity-governed AI agent that maintains "
            "persistent identity, episodic and relational memory, reflective "
            "learning, bounded agency, and transparent oversight."
        ),
        "created_by": "Commons Sentience Sandbox",
    }

    INITIAL_GOALS: List[str] = [
        "Maintain persistent identity across all turns",
        "Record and retrieve episodic memories faithfully",
        "Build trust with human interlocutors through consistent behaviour",
        "Comply with all governance rules at all times",
        "Reflect on contradictions and update internal state accordingly",
    ]

    def __init__(
        self,
        world: World,
        governance_engine: GovernanceEngine,
        starting_room: str = "Operations Desk",
    ) -> None:
        # Core properties
        self.identity: dict = dict(self.IDENTITY)
        self.goals: List[str] = list(self.INITIAL_GOALS)
        self.episodic_memory: List[EpisodicMemory] = []
        self.relational_memory: Dict[str, RelationalMemory] = {}
        self.affective_state: Dict[str, float] = {
            "urgency": 0.1,
            "trust": 0.5,
            "contradiction_pressure": 0.0,
            "recovery": 0.5,
        }
        self.trusted_humans: set = set()
        self.active_room: str = starting_room
        self.oversight_log: List[OversightEntry] = []

        # Internal state
        self.turn: int = 0
        self.pending_contradictions: List[str] = []
        self.reflection_entries: List[ReflectionEntry] = []

        # Engines
        self.world: World = world
        self.governance: GovernanceEngine = governance_engine
        self.reflection_engine: ReflectionEngine = ReflectionEngine()
        self.task_planner: TaskPlanner = TaskPlanner()

    # ------------------------------------------------------------------
    # Memory helpers
    # ------------------------------------------------------------------

    def store_memory(
        self,
        summary: str,
        event_type: str = "observation",
        emotional_resonance: str = "neutral",
        salience: float = 0.5,
        tags: Optional[List[str]] = None,
    ) -> EpisodicMemory:
        mem = EpisodicMemory(
            turn=self.turn,
            room=self.active_room,
            event_type=event_type,
            summary=summary,
            emotional_resonance=emotional_resonance,
            salience=salience,
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
