"""
reflection.py — Reflection cycle logic for the Commons Sentience Sandbox.

v0.3: ReflectionEntry now carries five structured sections:
      what_happened, what_mattered, what_conflicted, what_changed, future_adjustment.
"""
from __future__ import annotations

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

        # v0.3 five-section narrative
        what_happened = self._what_happened(agent, recent_memories, trigger)
        what_mattered = self._what_mattered(agent, recent_memories)
        what_conflicted = self._what_conflicted(agent, contradictions)
        what_changed = self._what_changed(affective_shift, updated_goals, agent)
        future_adjustment = self._future_adjustment(agent, updated_goals, contradictions)

        narrative = self._compose_narrative(
            trigger, patterns, contradictions, updated_goals, affective_shift
        )

        entry = ReflectionEntry(
            turn=agent.turn,
            trigger=trigger,
            what_happened=what_happened,
            what_mattered=what_mattered,
            what_conflicted=what_conflicted,
            what_changed=what_changed,
            future_adjustment=future_adjustment,
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
    # Five-section content builders
    # ------------------------------------------------------------------

    def _what_happened(
        self, agent: "Agent", memories: List[EpisodicMemory], trigger: str
    ) -> str:
        if not memories:
            return f"Turn {agent.turn}: No high-salience events recorded recently. Trigger: {trigger}."
        recent = memories[:3]
        summaries = "; ".join(m.summary[:60] for m in recent)
        return (
            f"In the most recent turns, the following events occurred: {summaries}. "
            f"This reflection was triggered by: {trigger}."
        )

    def _what_mattered(self, agent: "Agent", memories: List[EpisodicMemory]) -> str:
        resonance_counts: dict = {}
        for m in memories:
            resonance_counts[m.emotional_resonance] = (
                resonance_counts.get(m.emotional_resonance, 0) + 1
            )
        if not resonance_counts:
            return "No dominant emotional resonance detected."
        dominant = max(resonance_counts, key=lambda r: resonance_counts[r])
        humans = {tag for m in memories for tag in m.tags}
        human_str = (
            f" Interactions with {', '.join(sorted(humans))} were most significant."
            if humans
            else ""
        )
        return (
            f"The dominant emotional resonance was '{dominant}' "
            f"({resonance_counts[dominant]} occurrences).{human_str}"
        )

    def _what_conflicted(
        self, agent: "Agent", contradictions: List[str]
    ) -> str:
        if not contradictions and not agent.pending_contradictions:
            # Check value history for recent conflicts
            cp = agent.affective_state.get("contradiction_pressure", 0)
            if cp > 0.3:
                return (
                    f"Elevated contradiction pressure ({cp:.2f}) suggests unresolved "
                    "tension between governance compliance and relational obligations."
                )
            return "No active contradictions or value conflicts requiring resolution."
        items = contradictions or agent.pending_contradictions
        return "Contradictions present: " + "; ".join(items[:3]) + "."

    def _what_changed(
        self, affective_shift: dict, updated_goals: List[str], agent: "Agent"
    ) -> str:
        lines = []
        if affective_shift:
            shift_str = ", ".join(
                f"{k} {'rose' if v > 0 else 'fell'} by {abs(v):.1f}"
                for k, v in affective_shift.items()
            )
            lines.append(f"Affective state adjusted: {shift_str}.")
        new_goals = [g for g in updated_goals if g not in agent.goals]
        if new_goals:
            lines.append(f"New goal(s) added: {'; '.join(new_goals)}.")
        return " ".join(lines) if lines else "No significant internal changes this cycle."

    def _future_adjustment(
        self,
        agent: "Agent",
        updated_goals: List[str],
        contradictions: List[str],
    ) -> str:
        adjustments = []
        if contradictions:
            adjustments.append(
                "Continue monitoring for recurrence of the resolved contradiction."
            )
        if agent.affective_state.get("trust", 0) > 0.7:
            adjustments.append(
                "Leverage deepened trust with known humans for richer collaboration."
            )
        if agent.affective_state.get("urgency", 0) > 0.4:
            adjustments.append(
                "Reduce urgency by completing deferred tasks in priority order."
            )
        if not adjustments:
            adjustments.append(
                "Maintain current trajectory: stable, governed, and memory-consistent."
            )
        return " ".join(adjustments)

    # ------------------------------------------------------------------
    # Legacy helpers (still used for patterns / goals / affective shift)
    # ------------------------------------------------------------------

    def _identify_patterns(
        self, agent: "Agent", memories: List[EpisodicMemory]
    ) -> List[str]:
        patterns: List[str] = []
        humans_seen = {m.tags[0] for m in memories if m.tags}
        rooms_seen = {m.room for m in memories}

        for human in humans_seen:
            patterns.append(self.PATTERN_TEMPLATES[0].format(human=human))
        for room in list(rooms_seen)[:2]:
            patterns.append(self.PATTERN_TEMPLATES[1].format(room=room))
        if agent.affective_state.get("contradiction_pressure", 0) > 0.3:
            patterns.append(self.PATTERN_TEMPLATES[2])
        if agent.affective_state.get("recovery", 0) > 0.5:
            patterns.append(self.PATTERN_TEMPLATES[6])
        return patterns[:4]

    def _resolve_contradictions(self, agent: "Agent") -> List[str]:
        return [
            f"Contradiction resolved: {c}" for c in agent.pending_contradictions
        ]

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

