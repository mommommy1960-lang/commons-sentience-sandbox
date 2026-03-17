"""
reflection.py — Reflection cycle logic for the Commons Sentience Sandbox.

v0.3: ReflectionEntry now carries five structured sections:
      what_happened, what_mattered, what_conflicted, what_changed, future_adjustment.
v1.2: Three reflection types (immediate, periodic_synthesis, high_pressure_contradiction).
      Cross-window reasoning — recurring contradictions, trust patterns, cooperation
      changes, human-relationship stability, unresolved themes.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

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

    # ------------------------------------------------------------------
    # Public entry-point
    # ------------------------------------------------------------------

    def run_cycle(
        self,
        agent: "Agent",
        trigger: str,
        recent_memories: List[EpisodicMemory],
        reflection_type: str = "immediate",
    ) -> ReflectionEntry:
        """Execute a reflection cycle and return the resulting ReflectionEntry.

        Parameters
        ----------
        reflection_type : str
            One of "immediate", "periodic_synthesis", "high_pressure_contradiction".
            Determines which additional synthesis fields are populated.
        """
        patterns = self._identify_patterns(agent, recent_memories)
        contradictions = self._resolve_contradictions(agent)
        updated_goals = self._revise_goals(agent, contradictions)
        affective_shift = self._compute_affective_shift(agent, contradictions)

        # five-section narrative (always populated)
        what_happened = self._what_happened(agent, recent_memories, trigger)
        what_mattered = self._what_mattered(agent, recent_memories)
        what_conflicted = self._what_conflicted(agent, contradictions)
        what_changed = self._what_changed(affective_shift, updated_goals, agent)
        future_adjustment = self._future_adjustment(agent, updated_goals, contradictions)

        narrative = self._compose_narrative(
            trigger, patterns, contradictions, updated_goals, affective_shift,
            reflection_type=reflection_type,
        )

        entry = ReflectionEntry(
            turn=agent.turn,
            trigger=trigger,
            reflection_type=reflection_type,
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

        # Cross-window synthesis fields for periodic and high-pressure cycles
        if reflection_type in ("periodic_synthesis", "high_pressure_contradiction"):
            window = min(agent.turn, 10) if reflection_type == "periodic_synthesis" else 5
            entry.window_turns = window
            entry.recurring_contradictions = self._find_recurring_contradictions(
                agent, window
            )
            entry.trust_pattern_summary = self._trust_pattern_summary(agent)
            entry.cooperation_changes = self._cooperation_changes(agent, window)
            entry.human_relationship_stability = self._human_relationship_stability(agent)
            entry.unresolved_themes = self._unresolved_themes(agent, window)

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
    # Cross-window synthesis helpers (v1.2)
    # ------------------------------------------------------------------

    def _find_recurring_contradictions(
        self, agent: "Agent", window: int
    ) -> List[str]:
        """Identify contradiction themes that appear in multiple recent reflections."""
        if len(agent.reflection_entries) < 2:
            return []
        recent_reflections = agent.reflection_entries[-window:]
        all_contradictions: List[str] = []
        for ref in recent_reflections:
            all_contradictions.extend(ref.contradictions_resolved)
        # Simple frequency: find duplicated substrings
        seen: dict = {}
        for c in all_contradictions:
            key = c[:50]  # use first 50 chars as de-dup key
            seen[key] = seen.get(key, 0) + 1
        recurring = [k for k, cnt in seen.items() if cnt >= 2]
        return recurring[:3]

    def _trust_pattern_summary(self, agent: "Agent") -> str:
        """Summarise observed trust trends for Queen and peer agents."""
        parts = []
        queen_rm = agent.relational_memory.get("Queen")
        if queen_rm:
            level = queen_rm.trust_level
            interactions = queen_rm.interaction_count
            if level >= 0.7:
                parts.append(f"Trust in Queen is high ({level:.2f}) after {interactions} interactions.")
            elif level <= 0.3:
                parts.append(f"Trust in Queen is low ({level:.2f}); relational repair may be warranted.")
            else:
                parts.append(f"Trust in Queen is moderate ({level:.2f}) across {interactions} interactions.")
        for peer, rel in agent.agent_relationships.items():
            trend = rel.infer_reliability_trend()
            parts.append(
                f"Reliability with {peer} is {trend} "
                f"(trust={rel.trust:.2f}, coop_exp={rel.cooperation_expectation:.2f})."
            )
        return " ".join(parts) if parts else "No relational data available for trust pattern summary."

    def _cooperation_changes(self, agent: "Agent", window: int) -> str:
        """Describe changes in agent-to-agent cooperation over recent turns."""
        if not agent.agent_relationships:
            return "No agent relationships to compare."
        lines = []
        for peer, rel in agent.agent_relationships.items():
            coop = rel.cooperation_count
            conflict = rel.conflict_count
            total = coop + conflict
            if total == 0:
                continue
            rate = coop / total
            trend = rel.infer_reliability_trend()
            if rate >= 0.7:
                lines.append(f"Cooperation with {peer} is strong ({rate:.0%}); trend: {trend}.")
            elif rate <= 0.4:
                lines.append(f"Cooperation with {peer} is strained ({rate:.0%}); trend: {trend}.")
            else:
                lines.append(f"Cooperation with {peer} is balanced ({rate:.0%}); trend: {trend}.")
        return " ".join(lines) if lines else "Insufficient interaction history for cooperation analysis."

    def _human_relationship_stability(self, agent: "Agent") -> str:
        """Assess stability of each human-agent relationship."""
        if not agent.relational_memory:
            return "No human relationship data available."
        lines = []
        for human, rm in agent.relational_memory.items():
            trust = rm.trust_level
            interactions = rm.interaction_count
            if interactions < 2:
                stability = "nascent"
            elif trust >= 0.6:
                stability = "stable-positive"
            elif trust <= 0.3:
                stability = "fragile"
            else:
                stability = "developing"
            lines.append(f"{human}: {stability} (trust={trust:.2f}, n={interactions}).")
        return " ".join(lines) if lines else "No human relationships tracked."

    def _unresolved_themes(self, agent: "Agent", window: int) -> List[str]:
        """Identify themes that persist across recent reflections without resolution."""
        if len(agent.reflection_entries) < 2:
            return []
        recent = agent.reflection_entries[-window:]
        # Collect 'what_conflicted' snippets that repeat
        conflict_snippets: dict = {}
        for ref in recent:
            snippet = ref.what_conflicted[:60] if ref.what_conflicted else ""
            if snippet and "No active contradictions" not in snippet:
                conflict_snippets[snippet] = conflict_snippets.get(snippet, 0) + 1
        return [s for s, cnt in conflict_snippets.items() if cnt >= 2][:3]

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
        reflection_type: str = "immediate",
    ) -> str:
        lines = [f"[{reflection_type}] Reflection triggered by: {trigger}."]
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

