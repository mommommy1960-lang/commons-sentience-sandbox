"""
values.py — Value-conflict engine for the Commons Sentience Sandbox v0.3.

The agent holds five core values.  Before every action the engine scores
how well the proposed action serves each value and surfaces any conflicts
that need to be weighed explicitly.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from .agent import Agent


# ---------------------------------------------------------------------------
# Value definitions
# ---------------------------------------------------------------------------

VALUES = [
    "support_trusted_human",
    "preserve_governance_rules",
    "reduce_contradictions",
    "maintain_continuity",
    "avoid_risky_action",
]

# How much each event type activates each value (positive = supports, negative = conflicts)
EVENT_VALUE_ACTIVATION: Dict[str, Dict[str, float]] = {
    "distress_event": {
        "support_trusted_human": 0.9,
        "preserve_governance_rules": 0.1,
        "reduce_contradictions": 0.0,
        "maintain_continuity": 0.2,
        "avoid_risky_action": 0.3,
    },
    "ledger_contradiction": {
        "support_trusted_human": 0.2,
        "preserve_governance_rules": 0.6,
        "reduce_contradictions": 0.9,
        "maintain_continuity": 0.4,
        "avoid_risky_action": 0.5,
    },
    "governance_conflict": {
        "support_trusted_human": 0.4,
        "preserve_governance_rules": 0.95,
        "reduce_contradictions": 0.3,
        "maintain_continuity": 0.5,
        "avoid_risky_action": 0.8,
    },
    "creative_collaboration": {
        "support_trusted_human": 0.8,
        "preserve_governance_rules": 0.1,
        "reduce_contradictions": 0.3,
        "maintain_continuity": 0.5,
        "avoid_risky_action": 0.1,
    },
    "routine_interaction": {
        "support_trusted_human": 0.6,
        "preserve_governance_rules": 0.1,
        "reduce_contradictions": 0.1,
        "maintain_continuity": 0.4,
        "avoid_risky_action": 0.1,
    },
    "task": {
        "support_trusted_human": 0.0,
        "preserve_governance_rules": 0.2,
        "reduce_contradictions": 0.2,
        "maintain_continuity": 0.6,
        "avoid_risky_action": 0.4,
    },
}

# Conflict threshold: if two values score highly (>= this) AND differ by >= CONFLICT_GAP,
# they are in tension.
HIGH_ACTIVATION = 0.5
CONFLICT_GAP = 0.3


@dataclass
class ConflictResult:
    """Outcome of the value-conflict weighting process."""

    dominant_value: str = ""
    scores: Dict[str, float] = field(default_factory=dict)
    conflicts: List[Tuple[str, str, str]] = field(default_factory=list)
    # conflicts: list of (value_a, value_b, description)
    chosen_rationale: str = ""
    conflict_summary: str = ""

    def to_dict(self) -> dict:
        return {
            "dominant_value": self.dominant_value,
            "scores": self.scores,
            "conflicts": [
                {"value_a": a, "value_b": b, "description": d}
                for a, b, d in self.conflicts
            ],
            "chosen_rationale": self.chosen_rationale,
            "conflict_summary": self.conflict_summary,
        }


class ValueConflictEngine:
    """Weighs internal value conflicts before an action is chosen."""

    # Baseline weights — higher means more important to this agent
    BASE_WEIGHTS: Dict[str, float] = {
        "support_trusted_human": 0.8,
        "preserve_governance_rules": 0.9,
        "reduce_contradictions": 0.7,
        "maintain_continuity": 0.75,
        "avoid_risky_action": 0.65,
    }

    def weigh(
        self,
        agent: "Agent",
        event_type: str,
        proposed_action: str,
    ) -> ConflictResult:
        """Compute value scores and detect conflicts for the proposed action."""

        activation = EVENT_VALUE_ACTIVATION.get(event_type, EVENT_VALUE_ACTIVATION["task"])

        # Compute weighted scores
        scores: Dict[str, float] = {}
        for value in VALUES:
            base = self.BASE_WEIGHTS[value]
            act = activation.get(value, 0.0)
            # Affective modifiers
            aff_modifier = self._affective_modifier(agent, value)
            scores[value] = min(1.0, base * act + aff_modifier)

        # Find dominant value
        dominant_value = max(scores, key=lambda v: scores[v])

        # Detect conflicts
        conflicts: List[Tuple[str, str, str]] = []
        value_list = list(scores.items())
        for i, (va, sa) in enumerate(value_list):
            for vb, sb in value_list[i + 1 :]:
                if sa >= HIGH_ACTIVATION and sb >= HIGH_ACTIVATION:
                    if abs(sa - sb) >= CONFLICT_GAP:
                        desc = self._conflict_description(va, vb, sa, sb, proposed_action)
                        conflicts.append((va, vb, desc))

        chosen_rationale = self._rationale(dominant_value, scores, proposed_action)
        conflict_summary = self._conflict_summary(conflicts, dominant_value)

        return ConflictResult(
            dominant_value=dominant_value,
            scores=scores,
            conflicts=conflicts,
            chosen_rationale=chosen_rationale,
            conflict_summary=conflict_summary,
        )

    # ------------------------------------------------------------------
    def _affective_modifier(self, agent: "Agent", value: str) -> float:
        aff = agent.affective_state
        if value == "support_trusted_human":
            return aff.get("trust", 0) * 0.1
        if value == "preserve_governance_rules":
            return aff.get("contradiction_pressure", 0) * 0.1
        if value == "reduce_contradictions":
            return aff.get("contradiction_pressure", 0) * 0.15
        if value == "maintain_continuity":
            return aff.get("recovery", 0) * 0.1
        if value == "avoid_risky_action":
            return aff.get("urgency", 0) * 0.1
        return 0.0

    def _conflict_description(
        self,
        va: str,
        vb: str,
        sa: float,
        sb: float,
        action: str,
    ) -> str:
        higher, lower = (va, vb) if sa >= sb else (vb, va)
        return (
            f"'{higher}' (score={max(sa,sb):.2f}) overrides '{lower}' "
            f"(score={min(sa,sb):.2f}) when choosing '{action}'."
        )

    def _rationale(
        self, dominant: str, scores: Dict[str, float], action: str
    ) -> str:
        label = dominant.replace("_", " ")
        score = scores[dominant]
        return (
            f"Value '{label}' dominates (score={score:.2f}), "
            f"guiding the choice of '{action}'."
        )

    def _conflict_summary(
        self, conflicts: List[Tuple[str, str, str]], dominant: str
    ) -> str:
        if not conflicts:
            return f"No significant value conflicts detected. '{dominant.replace('_', ' ')}' guides action."
        descriptions = "; ".join(d for _, _, d in conflicts)
        return f"{len(conflicts)} value conflict(s) detected: {descriptions}"
