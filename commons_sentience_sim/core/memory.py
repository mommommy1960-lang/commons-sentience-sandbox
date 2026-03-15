"""
memory.py — Memory types for the Commons Sentience Sandbox.

v0.3: Adds importance field, weighted retrieval score, memory summaries
      for older events, and associative recall support.
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
    importance: float = 0.5               # 0.0 – 1.0; domain importance weight
    compressed: bool = False              # True once summary has been condensed
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    tags: List[str] = field(default_factory=list)

    def weighted_score(self, current_turn: int, query_tags: Optional[List[str]] = None) -> float:
        """Composite retrieval score combining relevance, importance, recency, and relational significance.

        - relevance      : tag overlap with query (0–1)
        - importance     : stored importance value
        - recency        : decays with turn distance
        - relational     : boosted if memory involves a known human (non-empty tags)
        """
        # Recency: half-life of ~10 turns
        recency = max(0.0, 1.0 - (current_turn - self.turn) / 20.0)

        # Relevance: tag overlap
        if query_tags:
            overlap = len(set(self.tags) & set(query_tags))
            relevance = min(1.0, overlap / max(1, len(query_tags)))
        else:
            relevance = 0.3  # moderate baseline when no query

        # Relational boost: memories involving humans are more significant
        relational = 0.2 if self.tags else 0.0

        # Weighted composite
        score = (
            0.30 * self.salience
            + 0.25 * self.importance
            + 0.25 * recency
            + 0.10 * relevance
            + 0.10 * relational
        )
        return round(min(1.0, score), 4)

    def compress(self) -> None:
        """Condense a long summary to a shorter archival form."""
        if not self.compressed and len(self.summary) > 80:
            self.summary = self.summary[:77] + "…"
            self.compressed = True

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    def __repr__(self) -> str:
        flag = "📦" if self.compressed else ""
        return (
            f"[T{self.turn:02d}|{self.room}] ({self.emotional_resonance}) "
            f"{self.summary}{flag}"
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
    """A structured record produced by a reflection cycle (v0.3 richer format)."""

    entry_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    turn: int = 0
    trigger: str = ""                         # what prompted this reflection

    # v0.3 richer fields
    what_happened: str = ""                   # factual summary of recent events
    what_mattered: str = ""                   # which values/goals were most affected
    what_conflicted: str = ""                 # tensions or contradictions encountered
    what_changed: str = ""                    # internal state adjustments made
    future_adjustment: str = ""              # concrete intent going forward

    # Legacy / aggregate fields (still populated)
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

