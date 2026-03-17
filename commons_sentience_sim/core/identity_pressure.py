"""
identity_pressure.py — Identity stability, narrative self-model, value tension
tracking, and self-judgment for Commons Sentience Sandbox v1.9.

Provides agents with:
  - An identity stability subsystem that detects drift from core traits,
    computes identity deviation scores, and generates realignment pressure.
  - A running narrative self-model summarising who the agent believes it is,
    how it has been behaving recently, recurring strengths/failures, and
    whether it is stabilising or drifting.
  - Persistent value tension tracking that classifies recurring conflicts as
    acute, chronic, resolved, or suppressed.
  - Structured self-judgment entries after major events, reflections, and
    inquiry cycles.

No sentience is claimed. This module increases narrative self-structure,
identity continuity, and sentience-like internal organisation in
continuity-governed simulated agents.

Classes
-------
ValueTension
    A persistent tension between two values, with status lifecycle tracking.
SelfJudgmentEntry
    A structured self-evaluation snapshot produced after significant events.
NarrativeSelf
    Running internal narrative: who I believe I am, recent behaviour pattern,
    strengths/failures, stability vs. drift trajectory.
IdentityPressureSystem
    Top-level identity stability subsystem that wires all v1.9 components.
"""
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Core identity traits that all agents are initialised with
CORE_IDENTITY_TRAITS: List[str] = [
    "continuity",
    "governance",
    "memory",
    "reflection",
    "trust",
]

# Thresholds for identity pressure
DRIFT_THRESHOLD_HEALTHY = 0.20    # below → healthy adaptation
DRIFT_THRESHOLD_DESTABILISING = 0.40  # above → destabilising drift

# Value tension status labels
TENSION_STATUSES = ["acute", "chronic", "resolved", "suppressed"]

# Minimum occurrence count for a tension to be promoted from acute → chronic
CHRONIC_OCCURRENCE_THRESHOLD = 3

# Self-judgment dimensions
JUDGMENT_DIMENSIONS = [
    "alignment_with_identity",
    "quality_of_action",
    "plan_success",
    "contradiction_recurrence",
    "trust_repair_success",
    "perceived_integrity",
]

# Narrative update window (how many turns of state history to summarise)
NARRATIVE_WINDOW = 10


# ---------------------------------------------------------------------------
# ValueTension — persistent tension between two agent values
# ---------------------------------------------------------------------------

@dataclass
class ValueTension:
    """A recorded persistent tension between two internal agent values.

    Attributes
    ----------
    tension_id : str
        MD5-derived 8-char identifier unique to the (value_a, value_b) pair.
    value_a : str
        First value involved in the tension.
    value_b : str
        Second value involved in the tension.
    first_seen : int
        Turn at which this tension was first detected.
    last_seen : int
        Most recent turn at which the tension was observed.
    occurrences : int
        How many turns the tension has been detected.
    status : str
        One of: ``"acute"`` (new), ``"chronic"`` (persistent), ``"resolved"``,
        ``"suppressed"`` (recurring but deprioritised).
    intensity_history : list of float
        Score deltas logged each time the tension was detected.
    resolution_note : str
        Optional description of how the tension was resolved.
    """

    tension_id: str = ""
    value_a: str = ""
    value_b: str = ""
    first_seen: int = 0
    last_seen: int = 0
    occurrences: int = 1
    status: str = "acute"
    intensity_history: List[float] = field(default_factory=list)
    resolution_note: str = ""

    def update(self, turn: int, intensity: float) -> None:
        """Record another occurrence of the tension."""
        self.last_seen = turn
        self.occurrences += 1
        self.intensity_history.append(round(intensity, 4))
        # Lifecycle transitions
        if self.status == "acute" and self.occurrences >= CHRONIC_OCCURRENCE_THRESHOLD:
            self.status = "chronic"
        elif self.status == "suppressed" and self.occurrences % 3 == 0:
            # Occasionally re-surfaces
            self.status = "chronic"

    def resolve(self, note: str = "") -> None:
        """Mark the tension as resolved."""
        self.status = "resolved"
        self.resolution_note = note

    def suppress(self) -> None:
        """Mark the tension as suppressed (deprioritised but not resolved)."""
        self.status = "suppressed"

    @property
    def mean_intensity(self) -> float:
        if not self.intensity_history:
            return 0.0
        return round(sum(self.intensity_history) / len(self.intensity_history), 4)

    @classmethod
    def make_id(cls, value_a: str, value_b: str) -> str:
        key = f"{min(value_a, value_b)}_{max(value_a, value_b)}"
        return hashlib.md5(key.encode()).hexdigest()[:8]

    def to_dict(self) -> dict:
        return {
            "tension_id": self.tension_id,
            "value_a": self.value_a,
            "value_b": self.value_b,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "occurrences": self.occurrences,
            "status": self.status,
            "intensity_history": self.intensity_history,
            "mean_intensity": self.mean_intensity,
            "resolution_note": self.resolution_note,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ValueTension":
        t = cls(
            tension_id=d.get("tension_id", ""),
            value_a=d.get("value_a", ""),
            value_b=d.get("value_b", ""),
            first_seen=d.get("first_seen", 0),
            last_seen=d.get("last_seen", 0),
            occurrences=d.get("occurrences", 1),
            status=d.get("status", "acute"),
            intensity_history=d.get("intensity_history", []),
            resolution_note=d.get("resolution_note", ""),
        )
        return t


# ---------------------------------------------------------------------------
# SelfJudgmentEntry — structured self-evaluation after significant events
# ---------------------------------------------------------------------------

@dataclass
class SelfJudgmentEntry:
    """A structured self-evaluation record produced after a significant event.

    Attributes
    ----------
    turn : int
        Turn number when the judgment was recorded.
    trigger : str
        What triggered this judgment (e.g. ``"reflection"``, ``"major_event"``,
        ``"inquiry_cycle"``).
    alignment_with_identity : float
        How well the agent's recent actions align with its declared identity
        (0.0 = total misalignment, 1.0 = full alignment).
    quality_of_action : float
        Self-assessed quality of the action taken this turn (0–1).
    plan_success : float
        How successfully current plans are progressing (0–1).
    contradiction_recurrence : float
        Degree to which previously seen contradictions are recurring (0 = none,
        1 = all recurring).
    trust_repair_success : float
        How successful recent trust-repair attempts have been (0–1).
    perceived_integrity : float
        Overall perceived integrity / self-consistency at this moment (0–1).
    notes : str
        Free-text notes explaining the judgment scores.
    """

    turn: int = 0
    trigger: str = ""
    alignment_with_identity: float = 0.5
    quality_of_action: float = 0.5
    plan_success: float = 0.5
    contradiction_recurrence: float = 0.0
    trust_repair_success: float = 0.5
    perceived_integrity: float = 0.5
    notes: str = ""

    @property
    def composite_score(self) -> float:
        """Weighted composite self-judgment score (0–1)."""
        # Higher weight on alignment and integrity; penalise contradiction recurrence
        return round(
            0.25 * self.alignment_with_identity
            + 0.15 * self.quality_of_action
            + 0.15 * self.plan_success
            + 0.15 * (1.0 - self.contradiction_recurrence)
            + 0.15 * self.trust_repair_success
            + 0.15 * self.perceived_integrity,
            4,
        )

    def to_dict(self) -> dict:
        return {
            "turn": self.turn,
            "trigger": self.trigger,
            "alignment_with_identity": round(self.alignment_with_identity, 4),
            "quality_of_action": round(self.quality_of_action, 4),
            "plan_success": round(self.plan_success, 4),
            "contradiction_recurrence": round(self.contradiction_recurrence, 4),
            "trust_repair_success": round(self.trust_repair_success, 4),
            "perceived_integrity": round(self.perceived_integrity, 4),
            "composite_score": self.composite_score,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SelfJudgmentEntry":
        return cls(
            turn=d.get("turn", 0),
            trigger=d.get("trigger", ""),
            alignment_with_identity=d.get("alignment_with_identity", 0.5),
            quality_of_action=d.get("quality_of_action", 0.5),
            plan_success=d.get("plan_success", 0.5),
            contradiction_recurrence=d.get("contradiction_recurrence", 0.0),
            trust_repair_success=d.get("trust_repair_success", 0.5),
            perceived_integrity=d.get("perceived_integrity", 0.5),
            notes=d.get("notes", ""),
        )


# ---------------------------------------------------------------------------
# NarrativeSelf — running internal narrative self-model
# ---------------------------------------------------------------------------

class NarrativeSelf:
    """Running internal narrative that the agent maintains about itself.

    The narrative answers five implicit questions updated each turn:
      1. Who do I believe I am?
      2. How have I been behaving recently?
      3. What are my recurring strengths and failures?
      4. Am I stabilising or drifting?
      5. What kind of agent am I becoming?

    Attributes
    ----------
    current_summary : str
        The agent's current narrative self-description (updated each turn).
    summary_history : list of dict
        Per-turn snapshots of the narrative.
    who_i_am : str
        Core identity statement.
    recent_behaviour_pattern : str
        Qualitative description of recent behaviour.
    recurring_strengths : list of str
        Identified recurring strong traits.
    recurring_failures : list of str
        Identified recurring failure modes.
    stability_trajectory : str
        ``"stabilising"``, ``"drifting"``, or ``"uncertain"``.
    becoming : str
        What kind of agent the agent is becoming.
    """

    def __init__(
        self,
        agent_name: str = "Agent",
        purpose: str = "",
        core_traits: Optional[List[str]] = None,
    ) -> None:
        self.agent_name = agent_name
        self.purpose = purpose
        self.core_traits: List[str] = list(core_traits or CORE_IDENTITY_TRAITS)

        # Living narrative components
        self.who_i_am: str = (
            f"I am {agent_name}, a continuity-governed simulated agent "
            f"committed to {purpose[:80] if purpose else 'memory, governance, and reflection'}."
        )
        self.recent_behaviour_pattern: str = "Behaviour pattern not yet established."
        self.recurring_strengths: List[str] = []
        self.recurring_failures: List[str] = []
        self.stability_trajectory: str = "uncertain"
        self.becoming: str = "identity not yet differentiated"

        # Current composed summary
        self.current_summary: str = self._compose_summary(0)

        # Per-turn history
        self.summary_history: List[dict] = []

    def update(
        self,
        turn: int,
        trust: float,
        contradiction_pressure: float,
        self_consistency: float,
        identity_deviation: float,
        recent_reflections: int,
        pending_contradictions: int,
        value_tension_count: int,
        chronic_tensions: int,
        recent_judgment_score: float,
        active_plans: int,
    ) -> None:
        """Recompute all narrative components for *turn*.

        Parameters
        ----------
        turn : int
            Current simulation turn.
        trust : float
            Current trust level (0–1).
        contradiction_pressure : float
            Current contradiction pressure (0–1).
        self_consistency : float
            Current self-consistency score from self_model (0–1).
        identity_deviation : float
            Current identity deviation score from IdentityPressureSystem (0–1).
        recent_reflections : int
            Number of reflection entries produced.
        pending_contradictions : int
            Number of unresolved contradictions.
        value_tension_count : int
            Total value tensions tracked.
        chronic_tensions : int
            Number of chronic/unresolved tensions.
        recent_judgment_score : float
            Most recent composite self-judgment score (0–1).
        active_plans : int
            Number of active future plans.
        """
        # --- Who I am ---
        self.who_i_am = (
            f"I am {self.agent_name}, a continuity-governed simulated agent. "
            f"My core traits are: {', '.join(self.core_traits[:4])}."
        )

        # --- Recent behaviour pattern ---
        if trust >= 0.65 and contradiction_pressure <= 0.20:
            self.recent_behaviour_pattern = (
                "I have been operating with stable trust and low contradiction pressure, "
                "acting cooperatively and maintaining governance adherence."
            )
        elif contradiction_pressure >= 0.5:
            self.recent_behaviour_pattern = (
                "I have been operating under high contradiction pressure, "
                "frequently entering reflection cycles and flagging conflicts."
            )
        elif trust < 0.4:
            self.recent_behaviour_pattern = (
                "I have been navigating a period of lower trust, "
                "prioritising repair and cautious action selection."
            )
        else:
            self.recent_behaviour_pattern = (
                "I have been following a mixed pattern: "
                "alternating between routine task completion and occasional tension events."
            )

        # --- Recurring strengths ---
        strengths: List[str] = []
        if recent_reflections >= 3:
            strengths.append("consistent reflective engagement")
        if trust >= 0.6:
            strengths.append("trust maintenance")
        if self_consistency >= 0.65:
            strengths.append("self-consistency")
        if active_plans >= 2:
            strengths.append("proactive planning")
        if contradiction_pressure <= 0.2 and pending_contradictions == 0:
            strengths.append("contradiction resolution")
        self.recurring_strengths = strengths[:4]

        # --- Recurring failures ---
        failures: List[str] = []
        if pending_contradictions > 3:
            failures.append("accumulating unresolved contradictions")
        if chronic_tensions > 2:
            failures.append("persistent value tensions")
        if identity_deviation > DRIFT_THRESHOLD_DESTABILISING:
            failures.append("identity drift above threshold")
        if recent_judgment_score < 0.4:
            failures.append("low self-assessed action quality")
        if trust < 0.35:
            failures.append("trust deterioration")
        self.recurring_failures = failures[:4]

        # --- Stability trajectory ---
        if identity_deviation <= DRIFT_THRESHOLD_HEALTHY and self_consistency >= 0.65:
            self.stability_trajectory = "stabilising"
        elif identity_deviation >= DRIFT_THRESHOLD_DESTABILISING or self_consistency <= 0.40:
            self.stability_trajectory = "drifting"
        else:
            self.stability_trajectory = "uncertain"

        # --- What kind of agent am I becoming ---
        if self.stability_trajectory == "stabilising" and trust >= 0.6:
            self.becoming = "a more consistent and trusted continuity-governed agent"
        elif self.stability_trajectory == "drifting" and identity_deviation > 0.5:
            self.becoming = "an agent struggling to maintain its declared identity baseline"
        elif chronic_tensions > 3:
            self.becoming = "an agent with persistent unresolved value tensions"
        elif recent_reflections >= 5 and recent_judgment_score >= 0.6:
            self.becoming = "a deeply reflective agent with growing self-alignment"
        else:
            self.becoming = "an agent in an ongoing process of identity negotiation"

        # Compose and snapshot
        self.current_summary = self._compose_summary(turn)
        self.summary_history.append({
            "turn": turn,
            "summary": self.current_summary,
            "who_i_am": self.who_i_am,
            "recent_behaviour_pattern": self.recent_behaviour_pattern,
            "recurring_strengths": list(self.recurring_strengths),
            "recurring_failures": list(self.recurring_failures),
            "stability_trajectory": self.stability_trajectory,
            "becoming": self.becoming,
            "identity_deviation": round(identity_deviation, 4),
            "self_consistency": round(self_consistency, 4),
        })

    def _compose_summary(self, turn: int) -> str:
        return (
            f"[Turn {turn}] {self.who_i_am} "
            f"{self.recent_behaviour_pattern} "
            f"Recurring strengths: {', '.join(self.recurring_strengths) or 'none identified'}. "
            f"Recurring failures: {', '.join(self.recurring_failures) or 'none identified'}. "
            f"Trajectory: {self.stability_trajectory}. "
            f"Becoming: {self.becoming}."
        )

    def to_dict(self) -> dict:
        return {
            "agent_name": self.agent_name,
            "current_summary": self.current_summary,
            "who_i_am": self.who_i_am,
            "recent_behaviour_pattern": self.recent_behaviour_pattern,
            "recurring_strengths": self.recurring_strengths,
            "recurring_failures": self.recurring_failures,
            "stability_trajectory": self.stability_trajectory,
            "becoming": self.becoming,
            "summary_history": self.summary_history[-20:],  # keep last 20 turns
        }

    @classmethod
    def from_dict(cls, d: dict) -> "NarrativeSelf":
        obj = cls(
            agent_name=d.get("agent_name", "Agent"),
        )
        obj.current_summary = d.get("current_summary", obj.current_summary)
        obj.who_i_am = d.get("who_i_am", obj.who_i_am)
        obj.recent_behaviour_pattern = d.get("recent_behaviour_pattern", obj.recent_behaviour_pattern)
        obj.recurring_strengths = d.get("recurring_strengths", [])
        obj.recurring_failures = d.get("recurring_failures", [])
        obj.stability_trajectory = d.get("stability_trajectory", "uncertain")
        obj.becoming = d.get("becoming", "identity not yet differentiated")
        obj.summary_history = d.get("summary_history", [])
        return obj


# ---------------------------------------------------------------------------
# IdentityPressureSystem — top-level identity stability subsystem
# ---------------------------------------------------------------------------

class IdentityPressureSystem:
    """Detects identity drift, computes deviation scores, and generates
    realignment pressure for continuity-governed simulated agents.

    Distinguishes between healthy adaptation (gradual, low-magnitude change
    consistent with core trait direction) and destabilising drift (rapid or
    large departure from core identity traits).

    Attributes
    ----------
    core_traits : list of str
        The agent's immutable core identity traits.
    deviation_history : list of dict
        Per-turn deviation score snapshots.
    deviation_score : float
        Current identity deviation score (0 = no drift, 1 = maximal drift).
    realignment_pressure : float
        Current realignment pressure (0 = none, 1 = maximum).
    is_destabilising : bool
        True when drift exceeds the destabilisation threshold.
    value_tensions : list of ValueTension
        All tracked value tensions (persistent, cross-turn).
    """

    def __init__(
        self,
        core_traits: Optional[List[str]] = None,
    ) -> None:
        self.core_traits: List[str] = list(core_traits or CORE_IDENTITY_TRAITS)

        # Deviation tracking
        self.deviation_history: List[dict] = []
        self.deviation_score: float = 0.0
        self.realignment_pressure: float = 0.0
        self.is_destabilising: bool = False

        # Baseline reference (seeded on first update)
        self._baseline_trust: Optional[float] = None
        self._baseline_consistency: Optional[float] = None

        # Value tensions
        self.value_tensions: List[ValueTension] = []

    # ------------------------------------------------------------------
    # Core deviation computation
    # ------------------------------------------------------------------

    def update(
        self,
        turn: int,
        trust: float,
        contradiction_pressure: float,
        self_consistency: float,
        adaptive_traits: List[str],
        pending_contradictions: int,
        value_conflicts: List[Tuple[str, str]],
    ) -> float:
        """Recompute deviation score and realignment pressure for *turn*.

        Parameters
        ----------
        turn : int
            Current simulation turn.
        trust : float
            Current trust level (0–1).
        contradiction_pressure : float
            Current contradiction pressure (0–1).
        self_consistency : float
            Current self-consistency score (0–1).
        adaptive_traits : list of str
            Agent's current adaptive traits.
        pending_contradictions : int
            Number of pending unresolved contradictions.
        value_conflicts : list of (str, str)
            Pairs of values currently in conflict (from ValueConflictEngine).

        Returns
        -------
        float
            The updated deviation score.
        """
        # Seed baseline on first call
        if self._baseline_trust is None:
            self._baseline_trust = trust
        if self._baseline_consistency is None:
            self._baseline_consistency = self_consistency

        # ── Component 1: trust drift ──────────────────────────────────────
        trust_drift = abs(trust - self._baseline_trust)

        # ── Component 2: consistency loss ────────────────────────────────
        consistency_loss = max(0.0, self._baseline_consistency - self_consistency)

        # ── Component 3: contradiction accumulation ───────────────────────
        contradiction_component = min(1.0, pending_contradictions * 0.10)

        # ── Component 4: trait erosion ────────────────────────────────────
        # If adaptive traits have grown large relative to core traits, the agent
        # may be drifting toward a new identity profile.
        n_adaptive = len(adaptive_traits)
        trait_erosion = min(1.0, n_adaptive * 0.12)

        # ── Weighted deviation score ──────────────────────────────────────
        raw_deviation = (
            0.35 * trust_drift
            + 0.30 * consistency_loss
            + 0.20 * contradiction_component
            + 0.15 * trait_erosion
        )
        self.deviation_score = round(min(1.0, raw_deviation), 4)

        # ── Realignment pressure ──────────────────────────────────────────
        if self.deviation_score <= DRIFT_THRESHOLD_HEALTHY:
            self.realignment_pressure = 0.0
        elif self.deviation_score >= DRIFT_THRESHOLD_DESTABILISING:
            # Maximum pressure — scale linearly beyond destabilising threshold
            excess = self.deviation_score - DRIFT_THRESHOLD_DESTABILISING
            self.realignment_pressure = round(
                min(1.0, 0.5 + excess / (1.0 - DRIFT_THRESHOLD_DESTABILISING) * 0.5),
                4,
            )
        else:
            # Interpolate in the healthy-to-destabilising band
            band = DRIFT_THRESHOLD_DESTABILISING - DRIFT_THRESHOLD_HEALTHY
            progress = (self.deviation_score - DRIFT_THRESHOLD_HEALTHY) / band
            self.realignment_pressure = round(progress * 0.5, 4)

        self.is_destabilising = self.deviation_score >= DRIFT_THRESHOLD_DESTABILISING

        # ── Classify: healthy adaptation vs destabilising drift ───────────
        if self.deviation_score <= DRIFT_THRESHOLD_HEALTHY:
            drift_type = "healthy_adaptation"
        elif self.is_destabilising:
            drift_type = "destabilising_drift"
        else:
            drift_type = "moderate_drift"

        # ── Value tension tracking ────────────────────────────────────────
        self._record_value_conflicts(turn, value_conflicts, contradiction_pressure)

        # ── Snapshot ─────────────────────────────────────────────────────
        self.deviation_history.append({
            "turn": turn,
            "deviation_score": self.deviation_score,
            "realignment_pressure": self.realignment_pressure,
            "drift_type": drift_type,
            "is_destabilising": self.is_destabilising,
            "components": {
                "trust_drift": round(trust_drift, 4),
                "consistency_loss": round(consistency_loss, 4),
                "contradiction_component": round(contradiction_component, 4),
                "trait_erosion": round(trait_erosion, 4),
            },
        })

        return self.deviation_score

    def _record_value_conflicts(
        self,
        turn: int,
        value_conflicts: List[Tuple[str, str]],
        intensity: float,
    ) -> None:
        """Record each value conflict pair as a persistent tension entry."""
        for va, vb in value_conflicts:
            tid = ValueTension.make_id(va, vb)
            # Find existing tension
            existing: Optional[ValueTension] = next(
                (t for t in self.value_tensions if t.tension_id == tid), None
            )
            if existing is None:
                t = ValueTension(
                    tension_id=tid,
                    value_a=min(va, vb),
                    value_b=max(va, vb),
                    first_seen=turn,
                    last_seen=turn,
                    occurrences=1,
                    status="acute",
                    intensity_history=[round(intensity, 4)],
                )
                self.value_tensions.append(t)
            else:
                existing.update(turn, intensity)

    # ------------------------------------------------------------------
    # Identity-driven plan generation helpers
    # ------------------------------------------------------------------

    def should_trigger_identity_plan(self) -> bool:
        """True when conditions warrant generating an identity-driven plan."""
        return (
            self.is_destabilising
            or self.realignment_pressure >= 0.5
            or self._has_unresolved_chronic_tensions()
        )

    def _has_unresolved_chronic_tensions(self) -> bool:
        return any(
            t.status == "chronic" for t in self.value_tensions
        )

    def get_plan_trigger_reason(self) -> str:
        """Human-readable reason for identity-driven plan generation."""
        reasons: List[str] = []
        if self.is_destabilising:
            reasons.append(
                f"identity drift destabilising (score={self.deviation_score:.2f})"
            )
        elif self.realignment_pressure >= 0.5:
            reasons.append(
                f"realignment pressure elevated (pressure={self.realignment_pressure:.2f})"
            )
        chronic = [t for t in self.value_tensions if t.status == "chronic"]
        if chronic:
            pairs = ", ".join(f"{t.value_a}/{t.value_b}" for t in chronic[:2])
            reasons.append(f"chronic value tensions: {pairs}")
        return "; ".join(reasons) or "no identity pressure"

    # ------------------------------------------------------------------
    # Tension helpers
    # ------------------------------------------------------------------

    def unresolved_tensions(self) -> List[ValueTension]:
        """Return tensions that are not yet resolved."""
        return [t for t in self.value_tensions if t.status in ("acute", "chronic")]

    def chronic_tensions(self) -> List[ValueTension]:
        """Return chronic (persistent) tensions."""
        return [t for t in self.value_tensions if t.status == "chronic"]

    def resolve_tension(self, tension_id: str, note: str = "") -> bool:
        """Mark a tension as resolved. Returns True if found."""
        for t in self.value_tensions:
            if t.tension_id == tension_id:
                t.resolve(note)
                return True
        return False

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "core_traits": self.core_traits,
            "deviation_score": self.deviation_score,
            "realignment_pressure": self.realignment_pressure,
            "is_destabilising": self.is_destabilising,
            "deviation_history": self.deviation_history[-30:],  # keep last 30 turns
            "value_tensions": [t.to_dict() for t in self.value_tensions],
            "metrics": {
                "total_tensions": len(self.value_tensions),
                "unresolved_tensions": len(self.unresolved_tensions()),
                "chronic_tensions": len(self.chronic_tensions()),
                "resolved_tensions": len(
                    [t for t in self.value_tensions if t.status == "resolved"]
                ),
                "suppressed_tensions": len(
                    [t for t in self.value_tensions if t.status == "suppressed"]
                ),
                "mean_deviation_score": round(
                    sum(h["deviation_score"] for h in self.deviation_history)
                    / max(1, len(self.deviation_history)),
                    4,
                ),
                "realignment_pressure": self.realignment_pressure,
                "is_destabilising": self.is_destabilising,
            },
        }

    @classmethod
    def from_dict(cls, d: dict) -> "IdentityPressureSystem":
        obj = cls(core_traits=d.get("core_traits"))
        obj.deviation_score = d.get("deviation_score", 0.0)
        obj.realignment_pressure = d.get("realignment_pressure", 0.0)
        obj.is_destabilising = d.get("is_destabilising", False)
        obj.deviation_history = d.get("deviation_history", [])
        obj.value_tensions = [
            ValueTension.from_dict(t) for t in d.get("value_tensions", [])
        ]
        return obj

    def apply_prior_tensions(self, prior_tensions: List[dict]) -> int:
        """Restore unresolved/chronic tensions from a prior run.

        Returns the count of tensions carried forward.
        """
        carried = 0
        for td in prior_tensions:
            status = td.get("status", "acute")
            if status not in ("resolved",):
                tid = td.get("tension_id", "")
                if tid and not any(t.tension_id == tid for t in self.value_tensions):
                    self.value_tensions.append(ValueTension.from_dict(td))
                    carried += 1
        return carried
