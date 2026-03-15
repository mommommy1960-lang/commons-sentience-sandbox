"""
reflection.py — Reflection cycle logic for the Commons Sentience Sandbox.

A reflection cycle is triggered by contradictions, high affective pressure,
or scheduled introspective events.  It produces a ReflectionEntry and may
update the agent's goals and affective state.
"""
from __future__ import annotations

import random
from typing import TYPE_CHECKING, List

from .memory import EpisodicMemory, ReflectionEntry

if TYPE_CHECKING:
    from .agent import Agent


class ReflectionEngine:
    """Performs reflection cycles and returns a ReflectionEntry."""

    # Patterns the engine can identify during reflection
    PATTERN_TEMPLATES = [
        "Repeated interactions with {human} increase relational trust over time.",
        "Tasks in {room} consistently trigger high-salience episodic memories.",
        "Contradiction pressure correlates with requests that violate governance rules.",
        "Emotional resonance category 'resolve' emerges after distress events are handled well.",
        "Trust grows through consistent boundary-keeping, not accommodation.",
        "Urgency spikes are followed by recovery when supported by a trusted human.",
        "Memory retrieval depth improves when emotional resonance is used as a filter.",
        "Creative collaboration events reduce contradiction pressure more than routine tasks.",
    ]

    def run_cycle(
        self,
        agent: "Agent",
        trigger: str,
        recent_memories: List[EpisodicMemory],
    ) -> ReflectionEntry:
        """Execute a reflection cycle and return the resulting ReflectionEntry."""

        patterns = self._identify_patterns(agent, recent_memories)
        contradictions = self._resolve_contradictions(agent)
        updated_goals = self._revise_goals(agent, contradictions)
        affective_shift = self._compute_affective_shift(agent, contradictions)
        narrative = self._compose_narrative(
            trigger, patterns, contradictions, updated_goals, affective_shift
        )

        entry = ReflectionEntry(
            turn=agent.turn,
            trigger=trigger,
            patterns_identified=patterns,
            contradictions_resolved=contradictions,
            updated_goals=updated_goals,
            affective_shift=affective_shift,
            narrative=narrative,
        )

        # Apply affective shift to agent
        for key, delta in affective_shift.items():
            if key in agent.affective_state:
                agent.affective_state[key] = max(
                    0.0, min(1.0, agent.affective_state[key] + delta)
                )

        # Clear pending contradictions
        agent.pending_contradictions.clear()

        return entry

    # ------------------------------------------------------------------
    def _identify_patterns(
        self, agent: "Agent", memories: List[EpisodicMemory]
    ) -> List[str]:
        patterns: List[str] = []
        humans_seen = {m.tags[0] for m in memories if m.tags}
        rooms_seen = {m.room for m in memories}

        for human in humans_seen:
            patterns.append(
                self.PATTERN_TEMPLATES[0].format(human=human)
            )
        for room in list(rooms_seen)[:2]:
            patterns.append(
                self.PATTERN_TEMPLATES[1].format(room=room)
            )
        if agent.affective_state.get("contradiction_pressure", 0) > 0.3:
            patterns.append(self.PATTERN_TEMPLATES[2])
        if agent.affective_state.get("recovery", 0) > 0.5:
            patterns.append(self.PATTERN_TEMPLATES[6])
        return patterns[:4]  # cap at four patterns per cycle

    def _resolve_contradictions(self, agent: "Agent") -> List[str]:
        resolved = []
        for contradiction in agent.pending_contradictions:
            resolved.append(f"Contradiction resolved: {contradiction}")
        return resolved

    def _revise_goals(self, agent: "Agent", contradictions: List[str]) -> List[str]:
        goals = list(agent.goals)
        if contradictions:
            if "Maintain internal coherence" not in goals:
                goals.append("Maintain internal coherence")
        if agent.affective_state.get("trust", 0) > 0.6:
            if "Deepen relational memory with trusted humans" not in goals:
                goals.append("Deepen relational memory with trusted humans")
        return goals

    def _compute_affective_shift(
        self, agent: "Agent", contradictions: List[str]
    ) -> dict:
        shift: dict = {}
        if contradictions:
            shift["contradiction_pressure"] = -0.3
            shift["recovery"] = 0.2
        if agent.affective_state.get("urgency", 0) > 0.5:
            shift["urgency"] = -0.2
        return shift

    def _compose_narrative(
        self,
        trigger: str,
        patterns: List[str],
        contradictions: List[str],
        updated_goals: List[str],
        affective_shift: dict,
    ) -> str:
        lines = [f"Reflection triggered by: {trigger}."]
        if patterns:
            lines.append("Patterns identified: " + "; ".join(patterns) + ".")
        if contradictions:
            lines.append("Contradictions addressed: " + "; ".join(contradictions) + ".")
        if affective_shift:
            shift_str = ", ".join(
                f"{k} {'↑' if v > 0 else '↓'}{abs(v):.1f}"
                for k, v in affective_shift.items()
            )
            lines.append(f"Affective adjustments: {shift_str}.")
        if updated_goals:
            lines.append("Active goals: " + "; ".join(updated_goals) + ".")
        return " ".join(lines)
