"""
memory.py — Memory types for the Commons Sentience Sandbox.

v0.3: Adds importance field, weighted retrieval score, memory summaries
      for older events, and associative recall support.
v1.2: Long-horizon memory tiers (short_term/medium_term/long_term/archival),
      recall-count tracking, salience evolution over time, explicit promotion
      and compression policies.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

# ---------------------------------------------------------------------------
# Memory tier constants
# ---------------------------------------------------------------------------

MEMORY_TIER_SHORT_TERM = "short_term"
MEMORY_TIER_MEDIUM_TERM = "medium_term"
MEMORY_TIER_LONG_TERM = "long_term"
MEMORY_TIER_ARCHIVAL = "archival"

# Tier promotion thresholds
PROMOTE_TO_LONG_TERM_SALIENCE = 0.75   # salience above this → long_term candidate
PROMOTE_TO_LONG_TERM_RECALL = 3        # recall count above this → long_term candidate
ARCHIVAL_AGE_THRESHOLD = 20            # turns old before archival is considered
ARCHIVAL_SALIENCE_CEILING = 0.35       # only archive if salience is below this

# Salience evolution parameters
SALIENCE_RECALL_BOOST = 0.05           # per recall event
SALIENCE_CONTRADICTION_BOOST = 0.10   # when memory is recalled due to contradiction
SALIENCE_TRUST_BOOST = 0.07           # when memory is recalled in trust context
SALIENCE_DECAY_RATE = 0.02            # per-turn passive decay for low-use neutral memories
SALIENCE_DECAY_THRESHOLD = 0.40       # only decay if below this and not long_term


@dataclass
class EpisodicMemory:
    """A single experiential memory tied to a specific turn and location.

    v1.2 additions
    --------------
    memory_tier   : placement in the long-horizon memory hierarchy
    recall_count  : number of times this memory has been retrieved
    """

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

    # v1.2 long-horizon fields
    memory_tier: str = MEMORY_TIER_SHORT_TERM
    recall_count: int = 0

    def weighted_score(self, current_turn: int, query_tags: Optional[List[str]] = None) -> float:
        """Composite retrieval score combining relevance, importance, recency, and relational significance.

        - relevance      : tag overlap with query (0–1)
        - importance     : stored importance value
        - recency        : decays with turn distance (long_term memories decay slower)
        - relational     : boosted if memory involves a known human (non-empty tags)
        - tier_boost     : long_term and archival memories get a small persistence bonus
        """
        # Recency: long-term memories have a longer effective half-life
        if self.memory_tier in (MEMORY_TIER_LONG_TERM, MEMORY_TIER_ARCHIVAL):
            recency = max(0.0, 1.0 - (current_turn - self.turn) / 50.0)
        else:
            recency = max(0.0, 1.0 - (current_turn - self.turn) / 20.0)

        # Relevance: tag overlap
        if query_tags:
            overlap = len(set(self.tags) & set(query_tags))
            relevance = min(1.0, overlap / max(1, len(query_tags)))
        else:
            relevance = 0.3  # moderate baseline when no query

        # Relational boost: memories involving humans are more significant
        relational = 0.2 if self.tags else 0.0

        # Tier persistence bonus
        tier_boost = {
            MEMORY_TIER_LONG_TERM: 0.10,
            MEMORY_TIER_ARCHIVAL: 0.05,
            MEMORY_TIER_MEDIUM_TERM: 0.03,
            MEMORY_TIER_SHORT_TERM: 0.0,
        }.get(self.memory_tier, 0.0)

        # Weighted composite
        score = (
            0.28 * self.salience
            + 0.22 * self.importance
            + 0.22 * recency
            + 0.10 * relevance
            + 0.08 * relational
            + 0.10 * tier_boost
        )
        return round(min(1.0, score), 4)

    def record_recall(self, context: str = "generic") -> None:
        """Increment recall count and boost salience based on recall context.

        Parameters
        ----------
        context : str
            One of "generic", "contradiction", "trust".  Determines the size
            of the salience boost applied.
        """
        self.recall_count += 1
        boost = {
            "contradiction": SALIENCE_CONTRADICTION_BOOST,
            "trust": SALIENCE_TRUST_BOOST,
        }.get(context, SALIENCE_RECALL_BOOST)
        self.salience = min(1.0, self.salience + boost)

    def apply_salience_decay(self) -> None:
        """Passively decay salience each turn for low-use neutral memories."""
        if (
            self.memory_tier not in (MEMORY_TIER_LONG_TERM, MEMORY_TIER_ARCHIVAL)
            and self.salience < SALIENCE_DECAY_THRESHOLD
            and self.emotional_resonance == "neutral"
            and self.recall_count == 0
        ):
            self.salience = max(0.0, self.salience - SALIENCE_DECAY_RATE)

    def evaluate_tier(self, current_turn: int) -> str:
        """Return the recommended tier for this memory given its current state.

        Rules (in priority order)
        -------------------------
        1. Already archival → stay archival.
        2. High-salience or high-recall, or Queen/governance/conflict/cooperation
           tag present → long_term.
        3. Old + low-salience → archival candidate.
        4. Moderate age → medium_term.
        5. Recent → short_term.
        """
        if self.memory_tier == MEMORY_TIER_ARCHIVAL:
            return MEMORY_TIER_ARCHIVAL

        age = current_turn - self.turn

        # High-value memories always stay long_term
        high_value_tags = {"queen", "Queen", "governance", "conflict", "cooperation"}
        has_high_value_tag = bool(set(self.tags) & high_value_tags)
        if (
            self.salience >= PROMOTE_TO_LONG_TERM_SALIENCE
            or self.recall_count >= PROMOTE_TO_LONG_TERM_RECALL
            or has_high_value_tag
            or self.importance >= 0.75
            or self.emotional_resonance in ("grief", "wonder", "resolve")
        ):
            return MEMORY_TIER_LONG_TERM

        # Old and low-salience → archival
        if age >= ARCHIVAL_AGE_THRESHOLD and self.salience < ARCHIVAL_SALIENCE_CEILING:
            return MEMORY_TIER_ARCHIVAL

        # Medium age
        if age >= 5:
            return MEMORY_TIER_MEDIUM_TERM

        return MEMORY_TIER_SHORT_TERM

    def compress(self) -> None:
        """Condense a long summary to a shorter archival form."""
        if not self.compressed and len(self.summary) > 80:
            self.summary = self.summary[:77] + "…"
            self.compressed = True

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    def __repr__(self) -> str:
        flag = "📦" if self.compressed else ""
        tier_badge = {
            MEMORY_TIER_SHORT_TERM: "ST",
            MEMORY_TIER_MEDIUM_TERM: "MT",
            MEMORY_TIER_LONG_TERM: "LT",
            MEMORY_TIER_ARCHIVAL: "AR",
        }.get(self.memory_tier, "??")
        return (
            f"[T{self.turn:02d}|{self.room}|{tier_badge}] ({self.emotional_resonance}) "
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
    """A structured record produced by a reflection cycle.

    v0.3: five-section narrative (what_happened … future_adjustment).
    v1.2: reflection_type classification, cross-window synthesis fields
          (recurring_contradictions, trust_pattern_summary, cooperation_changes,
          human_relationship_stability, unresolved_themes, window_turns).
    """

    entry_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    turn: int = 0
    trigger: str = ""                         # what prompted this reflection

    # v1.2 reflection type
    # "immediate" | "periodic_synthesis" | "high_pressure_contradiction"
    reflection_type: str = "immediate"

    # v0.3 richer fields
    what_happened: str = ""                   # factual summary of recent events
    what_mattered: str = ""                   # which values/goals were most affected
    what_conflicted: str = ""                 # tensions or contradictions encountered
    what_changed: str = ""                    # internal state adjustments made
    future_adjustment: str = ""              # concrete intent going forward

    # v1.2 cross-window synthesis fields (populated in periodic_synthesis)
    recurring_contradictions: List[str] = field(default_factory=list)
    trust_pattern_summary: str = ""
    cooperation_changes: str = ""
    human_relationship_stability: str = ""
    unresolved_themes: List[str] = field(default_factory=list)
    window_turns: int = 0                     # how many turns this synthesis covers

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
        return f"[Reflection T{self.turn:02d}|{self.reflection_type}] {self.narrative[:80]}"

