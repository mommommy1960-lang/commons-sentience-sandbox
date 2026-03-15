"""
memory.py — Memory types for the Commons Sentience Sandbox.

Defines EpisodicMemory, RelationalMemory, and ReflectionEntry.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class EpisodicMemory:
    """A single experiential memory tied to a specific turn and location."""

    memory_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    turn: int = 0
    room: str = ""
    event_type: str = ""
    summary: str = ""
    emotional_resonance: str = "neutral"   # wonder, grief, resolve, joy, ambiguity, neutral
    salience: float = 0.5                  # 0.0 – 1.0; higher = more memorable
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    def __repr__(self) -> str:
        return (
            f"[T{self.turn:02d}|{self.room}] ({self.emotional_resonance}) {self.summary}"
        )


@dataclass
class RelationalMemory:
    """Tracks the agent's accumulated knowledge of a specific person."""

    human_id: str = ""
    name: str = ""
    interaction_count: int = 0
    trust_level: float = 0.0           # 0.0 – 1.0
    last_seen_turn: int = 0
    notes: List[str] = field(default_factory=list)
    interaction_history: List[str] = field(default_factory=list)

    def record_interaction(self, turn: int, note: str) -> None:
        self.interaction_count += 1
        self.last_seen_turn = turn
        self.interaction_history.append(f"T{turn:02d}: {note}")
        if note:
            self.notes.append(note)

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    def __repr__(self) -> str:
        return (
            f"RelationalMemory({self.name}, trust={self.trust_level:.2f}, "
            f"interactions={self.interaction_count})"
        )


@dataclass
class ReflectionEntry:
    """A structured record produced by a reflection cycle."""

    entry_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    turn: int = 0
    trigger: str = ""                   # what prompted this reflection
    patterns_identified: List[str] = field(default_factory=list)
    contradictions_resolved: List[str] = field(default_factory=list)
    updated_goals: List[str] = field(default_factory=list)
    affective_shift: dict = field(default_factory=dict)
    narrative: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    def __repr__(self) -> str:
        return f"[Reflection T{self.turn:02d}] {self.narrative[:80]}"
