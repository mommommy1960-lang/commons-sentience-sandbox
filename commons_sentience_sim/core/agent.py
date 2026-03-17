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
        "version": "1.0.0",
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

        # v1.3 longitudinal tracking fields
        self.identity_history: List[dict] = []
        self.goal_evolution: List[dict] = []
        self.contradiction_genealogy: List[dict] = []
        self.relationship_timelines: Dict[str, List[dict]] = {}

        # v1.5 self-model subsystem
        self.self_model: dict = self._init_self_model()

        # v1.5 prediction / surprise loop
        self.prediction_log: List[dict] = []

        # v1.5 memory consolidation log
        self.consolidation_log: List[dict] = []

        # v1.5 goal hierarchy
        self.goal_hierarchy: dict = self._init_goal_hierarchy(
            initial_goals or self._DEFAULT_GOALS
        )

        # v1.6 endogenous drives
        self.drives: Dict[str, float] = self._init_drives()

        # v1.6 self-initiated action log
        self.endogenous_action_log: List[dict] = []

        # v1.6 world-state summary carried from a prior run (if any)
        self.prior_world_state_summary: Optional[dict] = None

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
        recall_context: str = "generic",
    ) -> List[EpisodicMemory]:
        """Weighted retrieval combining relevance, importance, recency, and relational significance.

        Parameters
        ----------
        recall_context : str
            Passed to ``EpisodicMemory.record_recall`` to apply the appropriate
            salience boost ("generic" | "contradiction" | "trust").
        """
        candidates = [
            m for m in self.episodic_memory
            if (room is None or m.room == room)
        ]
        scored = sorted(
            candidates,
            key=lambda m: m.weighted_score(self.turn, query_tags),
            reverse=True,
        )
        results = scored[:n]
        for mem in results:
            mem.record_recall(context=recall_context)
        return results

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
        """Compress summaries of memories older than age_threshold turns.

        In v1.2 archival-tier memories are always compressed regardless of age.
        """
        for mem in self.episodic_memory:
            should_compress = (
                (self.turn - mem.turn) >= age_threshold
                or mem.memory_tier == "archival"
            )
            if should_compress and not mem.compressed:
                mem.compress()

    def promote_memories(self) -> None:
        """Evaluate and update the memory tier for all episodic memories.

        Promotion policy (v1.2):
        - high-salience, high-recall, or high-value-tag memories → long_term
        - old, low-salience memories → archival (with compression)
        - medium age → medium_term
        - Preservation: Queen, governance conflicts, contradictions, cooperation
          milestones never get archived while their salience is above 0.4.
        """
        for mem in self.episodic_memory:
            new_tier = mem.evaluate_tier(self.turn)
            if new_tier != mem.memory_tier:
                mem.memory_tier = new_tier
                if new_tier == "archival":
                    mem.compress()

    def evolve_salience(self) -> None:
        """Apply per-turn salience decay to low-use neutral short-term memories."""
        for mem in self.episodic_memory:
            mem.apply_salience_decay()

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
        """Run a reflection cycle if conditions warrant it.

        v1.2 reflection type routing:
        - high_pressure_contradiction : raised contradiction pressure or pending contradictions
        - periodic_synthesis           : every 10 turns (cross-window reasoning)
        - immediate                    : default single-event reflection
        """
        high_pressure = (
            self.affective_state.get("contradiction_pressure", 0) > 0.4
            or len(self.pending_contradictions) > 0
        )
        periodic = self.turn > 0 and self.turn % 10 == 0

        if not (high_pressure or periodic):
            return None

        if high_pressure:
            reflection_type = "high_pressure_contradiction"
            recall_ctx = "contradiction"
        elif periodic:
            reflection_type = "periodic_synthesis"
            recall_ctx = "generic"
        else:
            reflection_type = "immediate"
            recall_ctx = "generic"

        recent = self.retrieve_memories(n=8, min_salience=0.3)
        entry = self.reflection_engine.run_cycle(
            self, trigger, recent, reflection_type=reflection_type
        )
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

    # ------------------------------------------------------------------
    # v1.3 Longitudinal tracking helpers
    # ------------------------------------------------------------------

    def record_identity_snapshot(self, turn: int, notes: str = "", drift_indicator: float = 0.0) -> None:
        """Append a snapshot to identity_history for longitudinal tracking."""
        entry = {
            "turn": turn,
            "identity_version": self.identity.get("version", "1.0.0"),
            "purpose": self.identity.get("purpose", ""),
            "goals_count": len(self.goals),
            "goals_snapshot": list(self.goals),
            "affective_snapshot": dict(self.affective_state),
            "continuity_marker": f"{self.name}_t{turn}",
            "drift_indicator": round(drift_indicator, 4),
            "notes": notes,
        }
        self.identity_history.append(entry)

    def record_goal_event(self, event_type: str, goal: str, trigger: str = "", turn: int = 0, priority_before: int = -1, priority_after: int = -1) -> None:
        """Record a goal addition, removal, revision, or priority shift."""
        entry = {
            "turn": turn or self.turn,
            "event_type": event_type,  # "added", "removed", "revised", "priority_shift", "preserved"
            "goal": goal,
            "trigger": trigger,
            "priority_before": priority_before,
            "priority_after": priority_after,
        }
        self.goal_evolution.append(entry)

    def record_contradiction_in_genealogy(self, contradiction: str, turn: int, parent_id: Optional[str] = None, resolved: bool = False, intensity: float = 0.5) -> str:
        """Record or update a contradiction in the genealogy, returning its ID."""
        import hashlib
        contradiction_id = hashlib.md5(contradiction.encode()).hexdigest()[:8]
        for entry in self.contradiction_genealogy:
            if entry["contradiction_id"] == contradiction_id:
                entry["last_seen"] = turn
                entry["occurrences"] = entry.get("occurrences", 1) + 1
                entry["resolved"] = resolved
                intensity_trend = entry.get("intensity_trend", [])
                intensity_trend.append(round(intensity, 4))
                entry["intensity_trend"] = intensity_trend
                return contradiction_id
        family_id = parent_id or contradiction_id
        entry = {
            "contradiction_id": contradiction_id,
            "family_id": family_id,
            "parent_id": parent_id,
            "text": contradiction,
            "first_seen": turn,
            "last_seen": turn,
            "occurrences": 1,
            "resolved": resolved,
            "intensity_trend": [round(intensity, 4)],
            "lineage_depth": 0 if parent_id is None else (
                next((e["lineage_depth"] + 1 for e in self.contradiction_genealogy if e["contradiction_id"] == parent_id), 1)
            ),
        }
        self.contradiction_genealogy.append(entry)
        return contradiction_id

    def record_relationship_timeline_event(self, relationship_key: str, turn: int, event_type: str, note: str, trust_before: float = 0.5, trust_after: float = 0.5) -> None:
        """Append an event to the relationship timeline for a given relationship key."""
        if relationship_key not in self.relationship_timelines:
            self.relationship_timelines[relationship_key] = []
        event = {
            "turn": turn,
            "event_type": event_type,  # "trust_milestone", "cooperation_spike", "repair_attempt", "conflict_episode", "stability_marker"
            "note": note,
            "trust_before": round(trust_before, 4),
            "trust_after": round(trust_after, 4),
            "trust_delta": round(trust_after - trust_before, 4),
        }
        self.relationship_timelines[relationship_key].append(event)

    # ------------------------------------------------------------------
    # v1.5 Self-model helpers
    # ------------------------------------------------------------------

    def _init_self_model(self) -> dict:
        """Initialise the self-model subsystem."""
        purpose = self.identity.get("purpose", "")
        name = self.identity.get("name", "Agent")
        return {
            "current_description": (
                purpose[:200] if purpose
                else f"I am {name}, a continuity-governed simulated agent."
            ),
            "description_history": [],
            "core_traits": ["continuity", "governance", "memory", "reflection"],
            "adaptive_traits": [],
            "detected_drift": 0.0,
            "self_consistency_score": 1.0,
            "last_updated_turn": 0,
        }

    def update_self_model(self, turn: int) -> None:
        """Recompute and persist the self-model snapshot for *turn*."""
        trust = self.affective_state.get("trust", 0.5)
        cp = self.affective_state.get("contradiction_pressure", 0.0)
        mem_count = len(self.episodic_memory)
        ref_count = len(self.reflection_entries)

        desc = (
            f"Turn {turn}: {self.name} — "
            f"trust={trust:.2f}, contradiction_pressure={cp:.2f}, "
            f"memories={mem_count}, reflections={ref_count}. "
            f"Active in {self.active_room}."
        )

        # Update adaptive traits
        adaptive: List[str] = list(self.self_model.get("adaptive_traits", []))
        if cp > 0.5 and "contradiction-sensitive" not in adaptive:
            adaptive.append("contradiction-sensitive")
        if trust > 0.7 and "high-trust" not in adaptive:
            adaptive.append("high-trust")
        elif trust < 0.3 and "trust-recovering" not in adaptive:
            adaptive.append("trust-recovering")
        if ref_count > 5 and "reflective" not in adaptive:
            adaptive.append("reflective")
        adaptive = adaptive[-5:]  # keep recent 5

        # Compute drift vs recent history
        history = self.self_model.get("description_history", [])
        prev_trusts = [
            float(h.get("trust_snapshot", trust))
            for h in history[-5:]
            if h.get("trust_snapshot") is not None
        ]
        drift = min(1.0, abs(trust - (sum(prev_trusts) / len(prev_trusts))) * 4.0) if prev_trusts else 0.0

        all_drifts = [h.get("drift", 0.0) for h in history[-10:]] + [drift]
        consistency = max(0.0, 1.0 - sum(all_drifts) / len(all_drifts))

        history.append({
            "turn": turn,
            "description": desc,
            "trust_snapshot": round(trust, 4),
            "contradiction_snapshot": round(cp, 4),
            "drift": round(drift, 4),
        })

        self.self_model.update({
            "current_description": desc,
            "description_history": history,
            "adaptive_traits": adaptive,
            "detected_drift": round(drift, 4),
            "self_consistency_score": round(consistency, 4),
            "last_updated_turn": turn,
        })

    # ------------------------------------------------------------------
    # v1.5 Prediction / surprise loop helpers
    # ------------------------------------------------------------------

    def record_prediction(self, turn: int, context: str, expected_outcome: str) -> int:
        """Record a pre-action prediction.  Returns the entry index."""
        entry = {
            "turn": turn,
            "context": context,
            "expected_outcome": expected_outcome,
            "actual_outcome": None,
            "surprise_magnitude": 0.0,
            "prediction_error": "pending",
        }
        self.prediction_log.append(entry)
        return len(self.prediction_log) - 1

    def resolve_prediction(self, index: int, actual_outcome: str, surprise_magnitude: float) -> None:
        """Fill in the actual outcome and classify the prediction error."""
        if not (0 <= index < len(self.prediction_log)):
            return
        sm = min(1.0, max(0.0, surprise_magnitude))
        entry = self.prediction_log[index]
        entry["actual_outcome"] = actual_outcome
        entry["surprise_magnitude"] = round(sm, 4)
        if sm < 0.2:
            entry["prediction_error"] = "none"
        elif sm < 0.4:
            entry["prediction_error"] = "low"
        elif sm < 0.7:
            entry["prediction_error"] = "medium"
        else:
            entry["prediction_error"] = "high"

        # High surprise → boost salience of last stored memory
        if sm > 0.5 and self.episodic_memory:
            self.episodic_memory[-1].salience = min(
                1.0, self.episodic_memory[-1].salience + 0.15
            )

        # Very high surprise → register a pending contradiction for reflection
        if sm > 0.6:
            expected = entry.get("expected_outcome", "")
            self.pending_contradictions.append(
                f"Prediction error at turn {entry['turn']}: "
                f"expected '{expected[:60]}' but outcome was unexpected."
            )

    # ------------------------------------------------------------------
    # v1.5 Memory consolidation helpers
    # ------------------------------------------------------------------

    def run_consolidation(self, turn: int) -> dict:
        """Run a consolidation cycle:
        - Compress memories with salience < 0.3 that are older than 5 turns.
        - Reinforce importance of high-salience (≥ 0.7) memories.
        - Carry unresolved themes from recent reflections forward.
        - Refresh the self-model.
        Returns the consolidation record.
        """
        low_value = [
            m for m in self.episodic_memory
            if m.salience < 0.3 and m.turn < turn - 5 and not m.compressed
        ]
        high_value = [m for m in self.episodic_memory if m.salience >= 0.7]

        compressed_count = 0
        for m in low_value:
            m.compressed = True
            compressed_count += 1

        for m in high_value:
            m.importance = min(1.0, m.importance + 0.02)

        # Collect unresolved themes from recent reflections
        unresolved_themes: List[str] = []
        for ref in self.reflection_entries[-5:]:
            themes = getattr(ref, "unresolved_themes", None)
            if isinstance(themes, list):
                unresolved_themes.extend(themes[:2])
            elif isinstance(themes, str) and themes:
                unresolved_themes.append(themes)

        self.update_self_model(turn)

        record = {
            "turn": turn,
            "memories_compressed": compressed_count,
            "high_salience_chains": len(high_value),
            "themes_carried_forward": list(dict.fromkeys(unresolved_themes))[:5],
            "self_model_revised": True,
            "consolidation_summary": (
                f"Consolidated at turn {turn}: compressed {compressed_count} "
                f"low-value memories, reinforced {len(high_value)} high-salience "
                f"chains. Self-consistency: "
                f"{self.self_model.get('self_consistency_score', 0.0):.2f}."
            ),
        }
        self.consolidation_log.append(record)
        return record

    # ------------------------------------------------------------------
    # v1.5 Goal hierarchy helpers
    # ------------------------------------------------------------------

    def _init_goal_hierarchy(self, goals: List[str]) -> dict:
        """Classify *goals* into core / adaptive / temporary / conflict tiers."""
        # First 3 goals are treated as core; remainder as adaptive
        core = goals[:3] if len(goals) >= 3 else list(goals)
        adaptive = goals[3:] if len(goals) > 3 else []
        return {
            "core": list(core),
            "adaptive": list(adaptive),
            "temporary": [],
            "conflict_resolution": [],
            "priority_history": [],
        }

    def record_goal_hierarchy_snapshot(self, turn: int) -> None:
        """Append a snapshot of the current goal hierarchy to priority_history."""
        self.goal_hierarchy["priority_history"].append({
            "turn": turn,
            "core_count": len(self.goal_hierarchy["core"]),
            "adaptive_count": len(self.goal_hierarchy["adaptive"]),
            "temporary_count": len(self.goal_hierarchy["temporary"]),
            "conflict_resolution_count": len(self.goal_hierarchy["conflict_resolution"]),
        })

    # ------------------------------------------------------------------
    # v1.6 Endogenous drives
    # ------------------------------------------------------------------

    def _init_drives(self) -> Dict[str, float]:
        """Initialise the agent's internal endogenous drive levels (0.0–1.0)."""
        return {
            "curiosity": 0.3,
            "maintenance_urge": 0.1,
            "repair_urge": 0.0,
            "investigation_urge": 0.1,
            "continuity_loop_urge": 0.2,
        }

    def update_drives(self) -> None:
        """Update endogenous drive levels based on current internal state.

        Called once per turn *before* action selection so that drive values
        can influence the agent's self-initiated behaviours.
        """
        cp = self.affective_state.get("contradiction_pressure", 0.0)
        trust = self.affective_state.get("trust", 0.5)
        urgency = self.affective_state.get("urgency", 0.1)
        recovery = self.affective_state.get("recovery", 0.5)
        mem_count = len(self.episodic_memory)

        # Repair urge rises with contradiction pressure and high urgency
        self.drives["repair_urge"] = min(1.0, cp * 0.8 + urgency * 0.2)

        # Maintenance urge rises when trust is low or recovery is poor
        self.drives["maintenance_urge"] = min(
            1.0, (1.0 - trust) * 0.5 + (1.0 - recovery) * 0.5
        )

        # Curiosity is suppressed under high urgency / contradiction pressure;
        # grows when many memories exist (more to reflect on)
        base_curiosity = 0.3 + min(0.3, mem_count / 200.0)
        self.drives["curiosity"] = max(
            0.0, base_curiosity - urgency * 0.3 - cp * 0.2
        )

        # Investigation urge grows with unresolved contradictions
        n_pending = len(self.pending_contradictions)
        self.drives["investigation_urge"] = min(1.0, n_pending * 0.15)

        # Continuity loop urge grows when self-consistency score is low
        sc = self.self_model.get("self_consistency_score", 0.5)
        self.drives["continuity_loop_urge"] = min(1.0, max(0.0, 1.0 - sc))

    def check_self_initiation(self, turn: int) -> Optional[str]:
        """Check whether any endogenous drive is strong enough to trigger a
        self-initiated action.

        Returns the action key as a string if a drive fires, otherwise ``None``.
        Logs the event to ``endogenous_action_log``.

        Drive thresholds:
          - continuity_loop_urge ≥ 0.7 → ``run_continuity_maintenance``
          - repair_urge          ≥ 0.6 → ``self_initiate_repair``
          - investigation_urge   ≥ 0.5 → ``self_initiate_investigation``
          - maintenance_urge     ≥ 0.5 → ``self_initiate_maintenance``
          - curiosity            ≥ 0.65 → ``self_initiate_exploration``
        """
        triggered: Optional[str] = None

        if self.drives.get("continuity_loop_urge", 0.0) >= 0.7:
            triggered = "run_continuity_maintenance"
        elif self.drives.get("repair_urge", 0.0) >= 0.6:
            triggered = "self_initiate_repair"
        elif self.drives.get("investigation_urge", 0.0) >= 0.5:
            triggered = "self_initiate_investigation"
        elif self.drives.get("maintenance_urge", 0.0) >= 0.5:
            triggered = "self_initiate_maintenance"
        elif self.drives.get("curiosity", 0.0) >= 0.65:
            triggered = "self_initiate_exploration"

        if triggered:
            drive_name = triggered.replace("self_initiate_", "").replace(
                "run_continuity_", ""
            )
            record = {
                "turn": turn,
                "action": triggered,
                "drive_snapshot": dict(self.drives),
                "note": (
                    f"Endogenous drive '{drive_name}' reached threshold at turn {turn}. "
                    f"Agent self-initiated '{triggered}'."
                ),
            }
            self.endogenous_action_log.append(record)

        return triggered

    # ------------------------------------------------------------------
    # v1.6 Cross-run carryover
    # ------------------------------------------------------------------

    def load_carryover(self, prior_state: dict, world_state: Optional[dict] = None) -> None:
        """Restore selected state from a prior simulation run.

        This allows cross-run continuity: long-term memories, unresolved
        themes, contradiction lineages, relationship states, self-model, and
        an optional world-state summary are all carried into the new run.

        Parameters
        ----------
        prior_state :
            The agent's serialised state dict from the prior run
            (as produced by ``Agent.to_dict()``).  Only this agent's own
            state section should be passed (i.e. ``multi_agent_state["agents"]["Sentinel"]``).
        world_state :
            Optional world-state snapshot as produced by
            ``world_state.build_world_state()``.  When provided, a summary
            is stored on the agent for use in reflection / narrative.
        """
        # ── Long-term memories ───────────────────────────────────────────────
        from .memory import EpisodicMemory  # local import avoids circularity

        prior_mems = prior_state.get("episodic_memory", [])
        carried_count = 0
        for mem_dict in prior_mems:
            tier = mem_dict.get("memory_tier", "short_term")
            if tier in ("long_term", "archival"):
                mem = EpisodicMemory(
                    turn=mem_dict.get("turn", 0),
                    room=mem_dict.get("room", ""),
                    event_type=mem_dict.get("event_type", "observation"),
                    summary=f"[carried] {mem_dict.get('summary', '')}",
                    emotional_resonance=mem_dict.get("emotional_resonance", "neutral"),
                    salience=mem_dict.get("salience", 0.3),
                    importance=mem_dict.get("importance", 0.3),
                    tags=mem_dict.get("tags", []) + ["carried_forward"],
                )
                mem.memory_tier = tier
                mem.compressed = mem_dict.get("compressed", False)
                self.episodic_memory.append(mem)
                carried_count += 1

        # ── Relationship states ──────────────────────────────────────────────
        from .memory import RelationalMemory  # local import

        prior_rel = prior_state.get("relational_memory", {})
        for name, rel_dict in prior_rel.items():
            if name not in self.relational_memory:
                self.relational_memory[name] = RelationalMemory(
                    name=name,
                    trust_level=rel_dict.get("trust_level", 0.5),
                    interaction_count=rel_dict.get("interaction_count", 0),
                    last_seen_turn=rel_dict.get("last_seen_turn", 0),
                )
                # Preserve recent notes (up to 3)
                notes = rel_dict.get("notes", [])[-3:]
                self.relational_memory[name].notes.extend(notes)
            else:
                # Blend existing trust with carried-over trust
                existing = self.relational_memory[name]
                prior_trust = rel_dict.get("trust_level", existing.trust_level)
                existing.trust_level = round(
                    existing.trust_level * 0.4 + prior_trust * 0.6, 4
                )

        # ── Agent-to-agent relationship states ──────────────────────────────
        from .relationships import AgentRelationship  # local import

        prior_agent_rels = prior_state.get("agent_relationships", {})
        for agent_name, rel_dict in prior_agent_rels.items():
            if agent_name not in self.agent_relationships:
                self.agent_relationships[agent_name] = AgentRelationship(
                    agent_id=rel_dict.get("agent_id", agent_name.lower()),
                    name=agent_name,
                    trust=rel_dict.get("trust", 0.5),
                    perceived_reliability=rel_dict.get("perceived_reliability", 0.5),
                )

        # ── Contradiction lineages ───────────────────────────────────────────
        prior_genealogy = prior_state.get("contradiction_genealogy", [])
        # Carry forward unresolved entries only (those without a resolved_at key)
        for entry in prior_genealogy:
            if not entry.get("resolved_at"):
                if entry not in self.contradiction_genealogy:
                    self.contradiction_genealogy.append(entry)
                    # Also ensure it surfaces as a pending contradiction
                    text = entry.get("text", "")
                    if text and text not in self.pending_contradictions:
                        self.pending_contradictions.append(
                            f"[carried] {text}"
                        )

        # ── Self-model ───────────────────────────────────────────────────────
        prior_sm = prior_state.get("self_model", {})
        if prior_sm:
            # Blend: keep current (freshly initialised) structure but seed
            # key scores from the prior run to provide continuity.
            for key in (
                "self_consistency_score",
                "dominant_value",
                "prediction_accuracy_recent",
            ):
                if key in prior_sm:
                    self.self_model[key] = prior_sm[key]
            self.self_model["carried_from_prior_run"] = True

        # ── Unresolved themes (from prior reflection entries) ────────────────
        prior_reflections = prior_state.get("reflection_entries", [])
        carried_themes: List[str] = []
        for ref_dict in prior_reflections[-5:]:
            themes = ref_dict.get("unresolved_themes", [])
            if isinstance(themes, list):
                carried_themes.extend(themes[:2])
            elif isinstance(themes, str) and themes:
                carried_themes.append(themes)

        # Store as a seed memory so they surface during retrieval
        if carried_themes:
            unique_themes = list(dict.fromkeys(carried_themes))[:5]
            self.store_memory(
                summary=(
                    "Unresolved themes carried from prior run: "
                    + "; ".join(unique_themes)
                ),
                event_type="observation",
                emotional_resonance="ambiguity",
                salience=0.65,
                importance=0.70,
                tags=["carried_forward", "unresolved_themes"],
            )

        # ── World-state summary ──────────────────────────────────────────────
        if world_state:
            self.prior_world_state_summary = {
                "run_label": world_state.get("run_label", ""),
                "saved_at": world_state.get("saved_at", ""),
                "total_turns_at_save": world_state.get("total_turns_at_save", 0),
                "unresolved_contradictions": world_state.get(
                    "unresolved_contradictions", []
                )[:5],
                "environmental_tensions": world_state.get("environmental_tensions", {}),
                "unresolved_themes": world_state.get("unresolved_themes", [])[:5],
                "prior_major_events_count": len(
                    world_state.get("prior_major_events", [])
                ),
            }
            # Log carryover as an episodic memory with high salience
            tension_val = world_state.get("environmental_tensions", {}).get(
                "combined_tension", 0.0
            )
            self.store_memory(
                summary=(
                    f"World-state carried from prior run "
                    f"(label='{world_state.get('run_label', 'unknown')}', "
                    f"turns={world_state.get('total_turns_at_save', '?')}, "
                    f"combined_tension={tension_val:.2f}). "
                    f"Unresolved contradictions: "
                    f"{len(world_state.get('unresolved_contradictions', []))}."
                ),
                event_type="observation",
                emotional_resonance="resolve",
                salience=0.70,
                importance=0.75,
                tags=["carried_forward", "world_state_summary"],
            )

        # Log summary
        self.store_memory(
            summary=(
                f"Cross-run carryover applied: {carried_count} long-term memories "
                f"restored, {len(self.pending_contradictions)} contradictions pending."
            ),
            event_type="observation",
            emotional_resonance="resolve",
            salience=0.55,
            importance=0.60,
            tags=["carried_forward", "carryover_summary"],
        )

    def to_dict(self) -> dict:
        return {
            "identity": self.identity,
            "goals": self.goals,
            "goal_hierarchy": self.goal_hierarchy,
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
            "identity_history": self.identity_history,
            "goal_evolution": self.goal_evolution,
            "contradiction_genealogy": self.contradiction_genealogy,
            "relationship_timelines": self.relationship_timelines,
            # v1.5 fields
            "self_model": self.self_model,
            "prediction_log": self.prediction_log,
            "consolidation_log": self.consolidation_log,
            # v1.6 fields
            "drives": self.drives,
            "endogenous_action_log": self.endogenous_action_log,
            "prior_world_state_summary": self.prior_world_state_summary,
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
        header = [
            "observer", "subject", "trust", "perceived_reliability",
            "conflict_count", "cooperation_count", "last_interaction_turn",
            "reliability_trend", "repair_attempted",
            "cooperation_expectation", "social_impression_confidence",
        ]
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
