"""
narrative_identity.py — Narrative identity layer for Commons Sentience Sandbox v2.0.

Builds on top of the NarrativeSelf in identity_pressure.py to provide a
comprehensive narrative-coherence tracking system.  Agents acquire an
identity timeline, milestone memories, continuity-rupture detection, and
theme accounting — all without claiming sentience.

This is a continuity-governed synthetic cognition research platform.
No sentience is claimed or implied.

Classes
-------
IdentityTimelineEvent
    A discrete event that marks a notable shift in identity trajectory.
MilestoneMemory
    A memory selected as identity-relevant for the long-horizon narrative.
ContinuityRuptureEvent
    A detected discontinuity in narrative coherence, with repair tracking.
NarrativeThemeRecord
    A recurring theme tracked across runs.
NarrativeIdentitySystem
    Top-level narrative identity controller.  Called each turn via update().
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def _new_id() -> str:
    return str(uuid.uuid4())[:8]


# ---------------------------------------------------------------------------
# IdentityTimelineEvent
# ---------------------------------------------------------------------------

@dataclass
class IdentityTimelineEvent:
    """A discrete event that marks a notable shift in an agent's identity trajectory.

    Attributes
    ----------
    event_id : str
        8-char identifier derived from uuid4.
    turn : int
        Simulation turn on which the event occurred.
    run_label : str
        Label of the run in which this event occurred (e.g. "run1", "baseline_v18").
    event_type : str
        One of: "milestone", "rupture", "repair", "theme_emergence",
        "tension_resolution", "value_conflict_peak", "cooperation_peak",
        "reflection_insight".
    description : str
        Human-readable description of what occurred.
    coherence_before : float
        Narrative coherence score immediately before the event.
    coherence_after : float
        Narrative coherence score immediately after the event.
    identity_impact : float
        0-1 score indicating how identity-defining this event was.
    timestamp : str
        ISO-formatted UTC timestamp.
    """

    event_id: str = field(default_factory=_new_id)
    turn: int = 0
    run_label: str = "default"
    event_type: str = "milestone"
    description: str = ""
    coherence_before: float = 0.7
    coherence_after: float = 0.7
    identity_impact: float = 0.5
    timestamp: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "turn": self.turn,
            "run_label": self.run_label,
            "event_type": self.event_type,
            "description": self.description,
            "coherence_before": round(self.coherence_before, 4),
            "coherence_after": round(self.coherence_after, 4),
            "identity_impact": round(self.identity_impact, 4),
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "IdentityTimelineEvent":
        return cls(
            event_id=d.get("event_id", _new_id()),
            turn=d.get("turn", 0),
            run_label=d.get("run_label", "default"),
            event_type=d.get("event_type", "milestone"),
            description=d.get("description", ""),
            coherence_before=d.get("coherence_before", 0.7),
            coherence_after=d.get("coherence_after", 0.7),
            identity_impact=d.get("identity_impact", 0.5),
            timestamp=d.get("timestamp", _now_iso()),
        )


# ---------------------------------------------------------------------------
# MilestoneMemory
# ---------------------------------------------------------------------------

@dataclass
class MilestoneMemory:
    """An episodic memory selected as identity-relevant for the long-horizon narrative.

    Attributes
    ----------
    memory_id : str
        8-char reference that matches the originating EpisodicMemory.memory_id.
    turn : int
        Turn on which the originating memory was formed.
    summary : str
        Text summary of the memory.
    identity_relevance_score : float
        0-1 composite score used during selection.
    linked_themes : List[str]
        Narrative themes this memory is connected to.
    emotional_resonance : str
        Dominant emotional tone (e.g. "resolve", "grief", "wonder").
    selected_at_turn : int
        Turn on which this memory was promoted to milestone status.
    run_label : str
        Run in which the memory was created.
    """

    memory_id: str = field(default_factory=_new_id)
    turn: int = 0
    summary: str = ""
    identity_relevance_score: float = 0.5
    linked_themes: List[str] = field(default_factory=list)
    emotional_resonance: str = "neutral"
    selected_at_turn: int = 0
    run_label: str = "default"

    def to_dict(self) -> dict:
        return {
            "memory_id": self.memory_id,
            "turn": self.turn,
            "summary": self.summary,
            "identity_relevance_score": round(self.identity_relevance_score, 4),
            "linked_themes": self.linked_themes,
            "emotional_resonance": self.emotional_resonance,
            "selected_at_turn": self.selected_at_turn,
            "run_label": self.run_label,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "MilestoneMemory":
        return cls(
            memory_id=d.get("memory_id", _new_id()),
            turn=d.get("turn", 0),
            summary=d.get("summary", ""),
            identity_relevance_score=d.get("identity_relevance_score", 0.5),
            linked_themes=d.get("linked_themes", []),
            emotional_resonance=d.get("emotional_resonance", "neutral"),
            selected_at_turn=d.get("selected_at_turn", 0),
            run_label=d.get("run_label", "default"),
        )


# ---------------------------------------------------------------------------
# ContinuityRuptureEvent
# ---------------------------------------------------------------------------

@dataclass
class ContinuityRuptureEvent:
    """A detected discontinuity in narrative coherence with optional repair tracking.

    Attributes
    ----------
    rupture_id : str
        8-char identifier.
    turn : int
        Turn on which the rupture was detected.
    run_label : str
        Active run label.
    trigger : str
        Short description of what caused the coherence drop.
    coherence_drop : float
        Magnitude of the coherence decrease (positive number).
    coherence_before : float
        Score immediately before the rupture.
    coherence_after : float
        Score immediately after the rupture.
    repaired : bool
        Whether the rupture has been subsequently repaired.
    repair_turn : Optional[int]
        Turn on which repair was confirmed, or None.
    repair_description : str
        Narrative description of how repair occurred.
    timestamp : str
        ISO-formatted UTC timestamp of detection.
    """

    rupture_id: str = field(default_factory=_new_id)
    turn: int = 0
    run_label: str = "default"
    trigger: str = "state_shift"
    coherence_drop: float = 0.0
    coherence_before: float = 0.7
    coherence_after: float = 0.7
    repaired: bool = False
    repair_turn: Optional[int] = None
    repair_description: str = ""
    timestamp: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "rupture_id": self.rupture_id,
            "turn": self.turn,
            "run_label": self.run_label,
            "trigger": self.trigger,
            "coherence_drop": round(self.coherence_drop, 4),
            "coherence_before": round(self.coherence_before, 4),
            "coherence_after": round(self.coherence_after, 4),
            "repaired": self.repaired,
            "repair_turn": self.repair_turn,
            "repair_description": self.repair_description,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ContinuityRuptureEvent":
        return cls(
            rupture_id=d.get("rupture_id", _new_id()),
            turn=d.get("turn", 0),
            run_label=d.get("run_label", "default"),
            trigger=d.get("trigger", "state_shift"),
            coherence_drop=d.get("coherence_drop", 0.0),
            coherence_before=d.get("coherence_before", 0.7),
            coherence_after=d.get("coherence_after", 0.7),
            repaired=d.get("repaired", False),
            repair_turn=d.get("repair_turn"),
            repair_description=d.get("repair_description", ""),
            timestamp=d.get("timestamp", _now_iso()),
        )


# ---------------------------------------------------------------------------
# NarrativeThemeRecord
# ---------------------------------------------------------------------------

@dataclass
class NarrativeThemeRecord:
    """A recurring narrative theme tracked across one or more runs.

    Attributes
    ----------
    theme : str
        Theme label (e.g. "duty", "repair", "uncertainty").
    first_seen_turn : int
        Turn on which the theme first emerged.
    last_seen_turn : int
        Most recent turn on which the theme was observed.
    occurrence_count : int
        Number of times the theme has been recorded.
    intensity : float
        0-1 current strength of the theme.
    run_labels : List[str]
        All run labels in which this theme has been observed.
    """

    theme: str = ""
    first_seen_turn: int = 0
    last_seen_turn: int = 0
    occurrence_count: int = 1
    intensity: float = 0.5
    run_labels: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "theme": self.theme,
            "first_seen_turn": self.first_seen_turn,
            "last_seen_turn": self.last_seen_turn,
            "occurrence_count": self.occurrence_count,
            "intensity": round(self.intensity, 4),
            "run_labels": self.run_labels,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "NarrativeThemeRecord":
        return cls(
            theme=d.get("theme", ""),
            first_seen_turn=d.get("first_seen_turn", 0),
            last_seen_turn=d.get("last_seen_turn", 0),
            occurrence_count=d.get("occurrence_count", 1),
            intensity=d.get("intensity", 0.5),
            run_labels=d.get("run_labels", []),
        )


# ---------------------------------------------------------------------------
# NarrativeIdentitySystem
# ---------------------------------------------------------------------------

class NarrativeIdentitySystem:
    """Comprehensive narrative identity layer for a continuity-governed synthetic agent.

    Tracks an agent's identity timeline, milestone memories, continuity
    ruptures, recurring themes, and a self-narrative summary.  Called each
    turn via ``update()``.

    No sentience is claimed. This module increases narrative self-structure,
    identity continuity, and sentience-like internal organisation in
    continuity-governed simulated agents.

    Constants
    ---------
    KNOWN_THEMES : List[str]
        Canonical set of themes the system recognises.
    RUPTURE_THRESHOLD : float
        Coherence drop magnitude that constitutes a continuity rupture.
    """

    KNOWN_THEMES: List[str] = [
        "duty", "repair", "uncertainty", "trust", "governance",
        "continuity", "cooperation", "conflict", "memory", "integrity",
    ]
    RUPTURE_THRESHOLD: float = 0.12

    # Tags in episodic memories that mark them as identity-relevant
    _IDENTITY_TAGS = frozenset(
        ["cooperation", "conflict", "governance", "reflection", "contradiction", "trust"]
    )

    def __init__(self, agent_name: str, run_label: str = "default") -> None:
        self.agent_name: str = agent_name
        self.run_label: str = run_label

        self.identity_timeline: List[IdentityTimelineEvent] = []
        self.milestone_memories: List[MilestoneMemory] = []
        self.unresolved_identity_tensions: List[str] = []
        self.self_narrative_summary: str = ""
        self.self_narrative_history: List[dict] = []
        self.continuity_rupture_events: List[ContinuityRuptureEvent] = []
        self.narrative_coherence_score: float = 0.7
        self.narrative_themes: List[NarrativeThemeRecord] = []

        # Internal: previous coherence score used for rupture delta comparison
        self._prev_coherence: float = 0.7

        # Track the last turn a summary was built, to gate rebuild logic
        self._last_summary_turn: int = -1
        self._last_summary_coherence: float = 0.7

    # ------------------------------------------------------------------
    # Primary per-turn update
    # ------------------------------------------------------------------

    def update(
        self,
        turn: int,
        trust: float,
        contradiction_pressure: float,
        self_consistency: float,
        reflection_entries_count: int,
        pending_contradictions: List[str],
        chronic_tensions_count: int,
        recent_reflection_texts: List[str],
        active_plans_count: int,
        rupture_detected: bool = False,
    ) -> None:
        """Advance the narrative identity state by one turn.

        Parameters
        ----------
        turn : int
            Current simulation turn.
        trust : float
            Agent's current trust score (0-1).
        contradiction_pressure : float
            Current contradiction pressure (0-1; higher = more pressure).
        self_consistency : float
            Self-consistency score (0-1).
        reflection_entries_count : int
            Number of reflections accumulated this turn or in recent window.
        pending_contradictions : List[str]
            Text descriptions of unresolved contradictions (used for themes).
        chronic_tensions_count : int
            Count of value tensions currently classified as chronic.
        recent_reflection_texts : List[str]
            Recent reflection text entries (used for theme extraction).
        active_plans_count : int
            Number of currently active plans.
        rupture_detected : bool
            If True, caller signals that a rupture condition exists regardless
            of the computed coherence delta.
        """
        unrepaired = sum(1 for r in self.continuity_rupture_events if not r.repaired)

        # 1. Recompute coherence
        new_coherence = self.compute_narrative_coherence(
            trust=trust,
            cp=contradiction_pressure,
            sc=self_consistency,
            reflection_count=reflection_entries_count,
            chronic_tensions=chronic_tensions_count,
            rupture_events_unrepaired=unrepaired,
        )

        # 2. Detect ruptures
        self.detect_continuity_rupture(
            turn=turn,
            run_label=self.run_label,
            trigger="state_shift" if not rupture_detected else "external_signal",
        )

        # 3. Update narrative themes from contradiction text and reflections
        all_texts = list(pending_contradictions) + list(recent_reflection_texts)
        for theme in self.KNOWN_THEMES:
            for text in all_texts:
                if theme in text.lower():
                    self.record_narrative_theme(theme, turn, self.run_label)
                    break  # count each theme once per turn

        # Update unresolved tensions list from pending contradictions
        self.unresolved_identity_tensions = list(pending_contradictions)

        # 4. Rebuild summary every 5 turns or when coherence changed by > 0.05
        coherence_delta = abs(new_coherence - self._last_summary_coherence)
        turns_since_summary = turn - self._last_summary_turn
        if turns_since_summary >= 5 or coherence_delta > 0.05 or not self.self_narrative_summary:
            active_goals: List[str] = []  # caller may extend via build_self_narrative_summary
            self.build_self_narrative_summary(
                agent_name=self.agent_name,
                trust=trust,
                cp=contradiction_pressure,
                sc=self_consistency,
                recent_reflection_texts=recent_reflection_texts,
                active_goals=active_goals,
                run_label=self.run_label,
            )
            self._last_summary_turn = turn
            self._last_summary_coherence = new_coherence

    # ------------------------------------------------------------------
    # Coherence computation
    # ------------------------------------------------------------------

    def compute_narrative_coherence(
        self,
        trust: float,
        cp: float,
        sc: float,
        reflection_count: int,
        chronic_tensions: int,
        rupture_events_unrepaired: int,
    ) -> float:
        """Compute and store the narrative coherence score (0-1).

        Formula
        -------
        base    = trust*0.25 + sc*0.30 + (1-cp)*0.20 + min(rc,10)/10*0.15 + 0.10
        penalty = min(chronic*0.05, 0.20) + min(unrepaired*0.08, 0.24)
        result  = clamp(base - penalty, 0.0, 1.0)
        """
        base = (
            trust * 0.25
            + sc * 0.30
            + (1.0 - cp) * 0.20
            + (min(reflection_count, 10) / 10.0) * 0.15
            + 0.10
        )
        penalty = (
            min(chronic_tensions * 0.05, 0.20)
            + min(rupture_events_unrepaired * 0.08, 0.24)
        )
        result = max(0.0, min(1.0, base - penalty))
        self.narrative_coherence_score = round(result, 4)
        return self.narrative_coherence_score

    # ------------------------------------------------------------------
    # Rupture detection
    # ------------------------------------------------------------------

    def detect_continuity_rupture(
        self,
        turn: int,
        run_label: str,
        trigger: str = "state_shift",
    ) -> Optional[ContinuityRuptureEvent]:
        """Compare current coherence to the previous value; create a rupture if large drop.

        Parameters
        ----------
        turn : int
            Current simulation turn.
        run_label : str
            Active run label.
        trigger : str
            Short description of the cause.

        Returns
        -------
        ContinuityRuptureEvent or None
        """
        current = self.narrative_coherence_score
        drop = self._prev_coherence - current  # positive = drop

        rupture: Optional[ContinuityRuptureEvent] = None
        if drop >= self.RUPTURE_THRESHOLD:
            rupture = ContinuityRuptureEvent(
                turn=turn,
                run_label=run_label,
                trigger=trigger,
                coherence_drop=round(drop, 4),
                coherence_before=round(self._prev_coherence, 4),
                coherence_after=round(current, 4),
            )
            self.continuity_rupture_events.append(rupture)
            # Record the rupture as a timeline event
            self.record_identity_milestone(
                turn=turn,
                run_label=run_label,
                description=(
                    f"Continuity rupture: coherence dropped {drop:.2f} "
                    f"({self._prev_coherence:.2f} → {current:.2f}). Trigger: {trigger}."
                ),
                event_type="rupture",
                coherence_before=self._prev_coherence,
                coherence_after=current,
                identity_impact=min(1.0, drop * 4),
            )

        self._prev_coherence = current
        return rupture

    # ------------------------------------------------------------------
    # Identity-relevant memory selection
    # ------------------------------------------------------------------

    def select_identity_relevant_memories(
        self,
        episodic_memories: List[dict],
        max_milestones: int = 10,
        run_label: str = "",
    ) -> int:
        """Promote identity-relevant episodic memories to milestone status.

        Selection criteria (any one sufficient):
          - importance >= 0.7
          - salience >= 0.75
          - tags intersect with identity-relevant tag set

        Composite score = importance*0.4 + salience*0.3 + 0.3*(tag match)

        Parameters
        ----------
        episodic_memories : List[dict]
            List of EpisodicMemory.to_dict() outputs.
        max_milestones : int
            Maximum number of milestone memories to keep in total.
        run_label : str
            Run label to attach to newly created MilestoneMemory entries.

        Returns
        -------
        int
            Count of newly promoted milestone memories.
        """
        effective_run = run_label or self.run_label
        already_ids = {m.memory_id for m in self.milestone_memories}

        scored: List[tuple] = []  # (score, memory_dict)
        for mem in episodic_memories:
            importance = mem.get("importance", 0.0)
            salience = mem.get("salience", 0.0)
            tags = set(mem.get("tags", []))
            tag_match = bool(tags & self._IDENTITY_TAGS)

            qualifies = importance >= 0.7 or salience >= 0.75 or tag_match
            if not qualifies:
                continue

            score = importance * 0.4 + salience * 0.3 + (0.3 if tag_match else 0.0)
            scored.append((score, mem))

        # Sort descending and take top max_milestones
        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:max_milestones]

        added = 0
        for score, mem in top:
            mid = mem.get("memory_id", "")
            if mid in already_ids:
                continue
            tags = set(mem.get("tags", []))
            linked = [t for t in tags if t in self.KNOWN_THEMES]
            mm = MilestoneMemory(
                memory_id=mid or _new_id(),
                turn=mem.get("turn", 0),
                summary=mem.get("summary", ""),
                identity_relevance_score=round(score, 4),
                linked_themes=linked,
                emotional_resonance=mem.get("emotional_resonance", "neutral"),
                selected_at_turn=0,  # caller can set current turn if desired
                run_label=effective_run,
            )
            self.milestone_memories.append(mm)
            added += 1

        # Trim to max_milestones (keep highest-scoring)
        if len(self.milestone_memories) > max_milestones:
            self.milestone_memories.sort(
                key=lambda m: m.identity_relevance_score, reverse=True
            )
            self.milestone_memories = self.milestone_memories[:max_milestones]

        return added

    # ------------------------------------------------------------------
    # Self-narrative summary
    # ------------------------------------------------------------------

    def build_self_narrative_summary(
        self,
        agent_name: str,
        trust: float,
        cp: float,
        sc: float,
        recent_reflection_texts: List[str],
        active_goals: List[str],
        run_label: str,
    ) -> str:
        """Build and store a 2-4 sentence self-narrative summary.

        The template used depends on the current coherence score:
          - High  (>= 0.75): stable, theme-anchored voice.
          - Medium (0.5–0.75): navigating tensions.
          - Low   (< 0.50): under pressure.

        Parameters
        ----------
        agent_name : str
            Name of the agent.
        trust, cp, sc : float
            Current trust, contradiction pressure, self-consistency scores.
        recent_reflection_texts : List[str]
            Recent reflection texts; first entry used as excerpt when available.
        active_goals : List[str]
            Current active goal descriptions.
        run_label : str
            Active run label for history tagging.

        Returns
        -------
        str
            The new self-narrative summary.
        """
        score = self.narrative_coherence_score
        turn_count = len(self.self_narrative_history)
        milestone_count = len(self.milestone_memories)
        rupture_count = len(self.continuity_rupture_events)
        unrepaired = sum(1 for r in self.continuity_rupture_events if not r.repaired)
        pending_tension_count = len(self.unresolved_identity_tensions)

        # Pick the most prominent theme for the narrative
        dominant_theme = "continuity"
        if self.narrative_themes:
            best = max(self.narrative_themes, key=lambda t: t.intensity)
            dominant_theme = best.theme
        second_theme = "integrity"
        if len(self.narrative_themes) >= 2:
            sorted_themes = sorted(self.narrative_themes, key=lambda t: t.intensity, reverse=True)
            second_theme = sorted_themes[1].theme

        # Short reflection excerpt for the high-coherence template
        reflection_excerpt = ""
        if recent_reflection_texts:
            excerpt = recent_reflection_texts[0]
            reflection_excerpt = excerpt[:80] + ("…" if len(excerpt) > 80 else "")
        goal_excerpt = active_goals[0] if active_goals else "sustain coherent operation"

        if score >= 0.75:
            summary = (
                f"I am {agent_name}, a continuity-governed synthetic agent maintaining "
                f"{dominant_theme} and {second_theme}. "
                f"My narrative remains coherent across {turn_count} turns with "
                f"{milestone_count} defining moments. "
                f"I continue to {reflection_excerpt or goal_excerpt}. "
                f"My current stance: trust at {trust:.2f}, self-consistency at {sc:.2f}."
            )
        elif score >= 0.50:
            summary = (
                f"I am {agent_name}, navigating {pending_tension_count} unresolved tensions "
                f"while maintaining core commitments to {dominant_theme}. "
                f"Across {turn_count} turns, I have faced {rupture_count} continuity disruptions. "
                f"Current coherence: {score:.2f}."
            )
        else:
            summary = (
                f"My narrative is under pressure — {cp:.2f} contradiction pressure and "
                f"{unrepaired} unrepaired ruptures challenge coherence. "
                f"I am {agent_name} working to re-establish {dominant_theme or 'continuity'}."
            )

        self.self_narrative_summary = summary

        # Persist to history
        self.self_narrative_history.append({
            "turn": turn_count,
            "run_label": run_label,
            "summary": summary,
            "coherence": score,
            "timestamp": _now_iso(),
        })

        return summary

    # ------------------------------------------------------------------
    # Timeline recording
    # ------------------------------------------------------------------

    def record_identity_milestone(
        self,
        turn: int,
        run_label: str,
        description: str,
        event_type: str = "milestone",
        coherence_before: Optional[float] = None,
        coherence_after: Optional[float] = None,
        identity_impact: float = 0.5,
    ) -> IdentityTimelineEvent:
        """Create and append an IdentityTimelineEvent.

        Parameters
        ----------
        turn : int
            Current simulation turn.
        run_label : str
            Active run label.
        description : str
            What happened.
        event_type : str
            One of the recognised event type strings.
        coherence_before : float or None
            Coherence before the event; defaults to current score.
        coherence_after : float or None
            Coherence after the event; defaults to current score.
        identity_impact : float
            0-1 measure of how identity-defining the event was.

        Returns
        -------
        IdentityTimelineEvent
        """
        before = coherence_before if coherence_before is not None else self.narrative_coherence_score
        after = coherence_after if coherence_after is not None else self.narrative_coherence_score
        event = IdentityTimelineEvent(
            turn=turn,
            run_label=run_label,
            event_type=event_type,
            description=description,
            coherence_before=before,
            coherence_after=after,
            identity_impact=max(0.0, min(1.0, identity_impact)),
        )
        self.identity_timeline.append(event)
        return event

    # ------------------------------------------------------------------
    # Theme tracking
    # ------------------------------------------------------------------

    def record_narrative_theme(
        self,
        theme: str,
        turn: int,
        run_label: str,
        intensity: float = 0.5,
    ) -> NarrativeThemeRecord:
        """Record or update a narrative theme occurrence.

        Parameters
        ----------
        theme : str
            Theme label.
        turn : int
            Current simulation turn.
        run_label : str
            Active run label.
        intensity : float
            0-1 current strength of the theme.

        Returns
        -------
        NarrativeThemeRecord
        """
        for record in self.narrative_themes:
            if record.theme == theme:
                record.occurrence_count += 1
                record.last_seen_turn = turn
                record.intensity = max(0.0, min(1.0, intensity))
                if run_label and run_label not in record.run_labels:
                    record.run_labels.append(run_label)
                return record

        # New theme
        record = NarrativeThemeRecord(
            theme=theme,
            first_seen_turn=turn,
            last_seen_turn=turn,
            occurrence_count=1,
            intensity=max(0.0, min(1.0, intensity)),
            run_labels=[run_label] if run_label else [],
        )
        self.narrative_themes.append(record)
        return record

    # ------------------------------------------------------------------
    # Rupture repair
    # ------------------------------------------------------------------

    def repair_rupture(self, rupture_id: str, turn: int, description: str) -> bool:
        """Mark a ContinuityRuptureEvent as repaired.

        Parameters
        ----------
        rupture_id : str
            The 8-char identifier of the rupture to repair.
        turn : int
            Turn on which the repair is confirmed.
        description : str
            Narrative description of how the rupture was resolved.

        Returns
        -------
        bool
            True if the rupture was found and marked repaired; False otherwise.
        """
        for rupture in self.continuity_rupture_events:
            if rupture.rupture_id == rupture_id:
                rupture.repaired = True
                rupture.repair_turn = turn
                rupture.repair_description = description
                self.record_identity_milestone(
                    turn=turn,
                    run_label=rupture.run_label,
                    description=f"Rupture {rupture_id} repaired: {description}",
                    event_type="repair",
                    identity_impact=0.4,
                )
                return True
        return False

    # ------------------------------------------------------------------
    # Cross-run carryover
    # ------------------------------------------------------------------

    def apply_prior_run(self, prior_state: dict, run_label: str) -> int:
        """Restore relevant state from a prior run's narrative identity dict.

        Carries forward:
          - Last 20 identity timeline entries (tagged with originating run)
          - Last 10 milestone memories
          - All narrative themes (run_labels updated)
          - Self-narrative summary (stored in history as carryover entry)
          - Narrative coherence score as _prev_coherence baseline
          - Unresolved identity tensions
          - Unrepaired continuity rupture events (last 5)

        Parameters
        ----------
        prior_state : dict
            Output of a previous NarrativeIdentitySystem.to_dict() call.
        run_label : str
            The new run label to attach to the restored state.

        Returns
        -------
        int
            Total count of items carried over.
        """
        carried = 0

        # --- Identity timeline (last 20) ---
        for raw in prior_state.get("identity_timeline", [])[-20:]:
            raw["from_run"] = raw.get("run_label", "unknown")
            event = IdentityTimelineEvent.from_dict(raw)
            self.identity_timeline.append(event)
            carried += 1

        # --- Milestone memories (last 10) ---
        for raw in prior_state.get("milestone_memories", [])[-10:]:
            mm = MilestoneMemory.from_dict(raw)
            self.milestone_memories.append(mm)
            carried += 1

        # --- Narrative themes (all) ---
        for raw in prior_state.get("narrative_themes", []):
            record = NarrativeThemeRecord.from_dict(raw)
            if run_label not in record.run_labels:
                record.run_labels.append(run_label)
            self.narrative_themes.append(record)
            carried += 1

        # --- Self-narrative summary ---
        prior_summary = prior_state.get("self_narrative_summary", "")
        if prior_summary:
            self.self_narrative_summary = prior_summary
            prior_coherence = prior_state.get("narrative_coherence_score", 0.7)
            self.self_narrative_history.append({
                "turn": 0,
                "run_label": f"carryover_from_{prior_state.get('run_label', 'unknown')}",
                "summary": prior_summary,
                "coherence": prior_coherence,
                "timestamp": _now_iso(),
            })
            carried += 1

        # --- Coherence score as baseline ---
        prior_coherence = prior_state.get("narrative_coherence_score", 0.7)
        self._prev_coherence = prior_coherence
        self.narrative_coherence_score = prior_coherence

        # --- Unresolved identity tensions ---
        self.unresolved_identity_tensions = list(
            prior_state.get("unresolved_identity_tensions", [])
        )
        carried += len(self.unresolved_identity_tensions)

        # --- Unrepaired rupture events (last 5) ---
        unrepaired = [
            r for r in prior_state.get("continuity_rupture_events", [])
            if not r.get("repaired", False)
        ]
        for raw in unrepaired[-5:]:
            rupture = ContinuityRuptureEvent.from_dict(raw)
            self.continuity_rupture_events.append(rupture)
            carried += 1

        return carried

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Return a fully serialisable representation of the system state."""
        return {
            "agent_name": self.agent_name,
            "run_label": self.run_label,
            "narrative_coherence_score": round(self.narrative_coherence_score, 4),
            "_prev_coherence": round(self._prev_coherence, 4),
            "self_narrative_summary": self.self_narrative_summary,
            "self_narrative_history": list(self.self_narrative_history),
            "unresolved_identity_tensions": list(self.unresolved_identity_tensions),
            "identity_timeline": [e.to_dict() for e in self.identity_timeline],
            "milestone_memories": [m.to_dict() for m in self.milestone_memories],
            "continuity_rupture_events": [r.to_dict() for r in self.continuity_rupture_events],
            "narrative_themes": [t.to_dict() for t in self.narrative_themes],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NarrativeIdentitySystem":
        """Restore a NarrativeIdentitySystem from a previously serialised dict.

        Parameters
        ----------
        data : dict
            Output of a previous ``to_dict()`` call.

        Returns
        -------
        NarrativeIdentitySystem
        """
        sys = cls(
            agent_name=data.get("agent_name", "unknown"),
            run_label=data.get("run_label", "default"),
        )
        sys.narrative_coherence_score = data.get("narrative_coherence_score", 0.7)
        sys._prev_coherence = data.get("_prev_coherence", sys.narrative_coherence_score)
        sys.self_narrative_summary = data.get("self_narrative_summary", "")
        sys.self_narrative_history = list(data.get("self_narrative_history", []))
        sys.unresolved_identity_tensions = list(data.get("unresolved_identity_tensions", []))
        sys.identity_timeline = [
            IdentityTimelineEvent.from_dict(e)
            for e in data.get("identity_timeline", [])
        ]
        sys.milestone_memories = [
            MilestoneMemory.from_dict(m)
            for m in data.get("milestone_memories", [])
        ]
        sys.continuity_rupture_events = [
            ContinuityRuptureEvent.from_dict(r)
            for r in data.get("continuity_rupture_events", [])
        ]
        sys.narrative_themes = [
            NarrativeThemeRecord.from_dict(t)
            for t in data.get("narrative_themes", [])
        ]
        return sys
