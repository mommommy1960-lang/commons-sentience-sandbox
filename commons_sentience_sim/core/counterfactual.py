"""
counterfactual.py — Counterfactual planning layer for Commons Sentience Sandbox v1.7.

Provides agents with the ability to simulate possible futures before acting,
compare outcomes, and form self-authored plans based on counterfactual reasoning.

No sentience is claimed. This module increases future-modeling capacity and
sentience-like continuity in continuity-governed simulated agents.

Classes
-------
CounterfactualCandidate
    A candidate action with predicted outcome scores.
InternalSimulationEntry
    One entry in the agent's internal simulation log.
FuturePlan
    A medium-horizon, multi-step self-authored plan.
CounterfactualPlanner
    The planning engine that generates candidates, selects actions,
    logs simulations, records actual outcomes, and manages future plans.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Candidate action templates
# ---------------------------------------------------------------------------

_CANDIDATE_TEMPLATES: List[Dict[str, Any]] = [
    {
        "action": "repair_trust",
        "description": "Proactively repair trust through consistent behaviour",
        "trust_effect": +0.12,
        "contradiction_effect": -0.05,
        "governance_risk": 0.05,
        "continuity_impact": +0.08,
    },
    {
        "action": "resolve_contradiction",
        "description": "Address a pending contradiction directly",
        "trust_effect": +0.05,
        "contradiction_effect": -0.15,
        "governance_risk": 0.08,
        "continuity_impact": +0.10,
    },
    {
        "action": "consolidate_memory",
        "description": "Run a memory consolidation cycle",
        "trust_effect": 0.00,
        "contradiction_effect": -0.08,
        "governance_risk": 0.02,
        "continuity_impact": +0.12,
    },
    {
        "action": "defer_action",
        "description": "Defer action and observe the environment",
        "trust_effect": -0.03,
        "contradiction_effect": +0.02,
        "governance_risk": 0.01,
        "continuity_impact": -0.02,
    },
    {
        "action": "cooperative_engagement",
        "description": "Engage cooperatively with other agents",
        "trust_effect": +0.10,
        "contradiction_effect": +0.03,
        "governance_risk": 0.10,
        "continuity_impact": +0.05,
    },
    {
        "action": "governance_check",
        "description": "Verify compliance with all active governance rules",
        "trust_effect": +0.04,
        "contradiction_effect": 0.00,
        "governance_risk": -0.10,
        "continuity_impact": +0.06,
    },
    {
        "action": "self_reflection",
        "description": "Perform a focused self-reflection cycle",
        "trust_effect": +0.03,
        "contradiction_effect": -0.06,
        "governance_risk": 0.02,
        "continuity_impact": +0.09,
    },
    {
        "action": "investigate_theme",
        "description": "Investigate an unresolved theme from prior turns",
        "trust_effect": +0.02,
        "contradiction_effect": -0.10,
        "governance_risk": 0.04,
        "continuity_impact": +0.07,
    },
]

# Plan templates for self-authored future plans
_PLAN_TEMPLATES: List[Dict[str, Any]] = [
    {
        "goal": "repair_trust",
        "label": "Repair trust with {target}",
        "stages": [
            "Initiate cooperative engagement with {target}",
            "Maintain consistent behaviour over next 3 turns",
            "Verify trust level has improved",
        ],
        "horizon": 5,
        "priority": 0.8,
    },
    {
        "goal": "revisit_contradiction",
        "label": "Revisit contradiction: {theme}",
        "stages": [
            "Retrieve memories related to contradiction",
            "Apply resolution strategy",
            "Verify contradiction pressure reduced",
        ],
        "horizon": 4,
        "priority": 0.7,
    },
    {
        "goal": "stabilise_self_drift",
        "label": "Stabilise self-drift (current drift={drift:.2f})",
        "stages": [
            "Run self-consistency check",
            "Reinforce core continuity goals",
            "Verify self-model stability",
        ],
        "horizon": 6,
        "priority": 0.6,
    },
    {
        "goal": "investigate_theme",
        "label": "Investigate unresolved theme: {theme}",
        "stages": [
            "Retrieve related episodic memories",
            "Cross-reference with relational records",
            "Form a resolution or carry-forward note",
        ],
        "horizon": 4,
        "priority": 0.65,
    },
    {
        "goal": "reinforce_continuity",
        "label": "Reinforce core continuity goals",
        "stages": [
            "Review goal hierarchy",
            "Confirm governance alignment",
            "Log continuity reinforcement",
        ],
        "horizon": 3,
        "priority": 0.55,
    },
]


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class CounterfactualCandidate:
    """A candidate action considered by the counterfactual planner.

    Parameters
    ----------
    action : str
        Short action identifier.
    description : str
        Human-readable description of the candidate action.
    predicted_trust_effect : float
        Expected delta on the agent's trust level (−1 to +1).
    predicted_contradiction_effect : float
        Expected delta on contradiction pressure (−1 to +1).
    predicted_governance_risk : float
        Expected governance-rule risk (0 to 1; lower is safer).
    predicted_continuity_impact : float
        Expected impact on identity continuity score (−1 to +1).
    predicted_best_case : str
        Narrative description of the best-case predicted outcome.
    predicted_worst_case : str
        Narrative description of the worst-case predicted outcome.
    uncertainty : float
        Planning uncertainty level (0 = certain, 1 = completely uncertain).
    composite_score : float
        Weighted composite score used to rank candidates.
    selected : bool
        Whether this candidate was ultimately selected.
    """

    action: str
    description: str
    predicted_trust_effect: float = 0.0
    predicted_contradiction_effect: float = 0.0
    predicted_governance_risk: float = 0.0
    predicted_continuity_impact: float = 0.0
    predicted_best_case: str = ""
    predicted_worst_case: str = ""
    uncertainty: float = 0.5
    composite_score: float = 0.0
    selected: bool = False

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "description": self.description,
            "predicted_trust_effect": round(self.predicted_trust_effect, 4),
            "predicted_contradiction_effect": round(self.predicted_contradiction_effect, 4),
            "predicted_governance_risk": round(self.predicted_governance_risk, 4),
            "predicted_continuity_impact": round(self.predicted_continuity_impact, 4),
            "predicted_best_case": self.predicted_best_case,
            "predicted_worst_case": self.predicted_worst_case,
            "uncertainty": round(self.uncertainty, 4),
            "composite_score": round(self.composite_score, 4),
            "selected": self.selected,
        }


@dataclass
class InternalSimulationEntry:
    """One entry in the internal simulation log.

    Each entry records a full planning cycle: the context in which it occurred,
    all candidates considered, the one selected, and (once known) the actual result
    vs the prediction.

    Parameters
    ----------
    turn : int
        Simulation turn at which this entry was created.
    context : str
        Brief description of the current agent state / situation.
    candidates : list[CounterfactualCandidate]
        All generated candidate actions.
    selected_action : str
        The action that was selected.
    predicted_outcome : str
        Summary of the predicted best-case outcome for the selected action.
    actual_outcome : str
        Actual result recorded after execution (filled in post-action).
    planning_accuracy : float
        How closely the prediction matched reality (0 = wrong, 1 = perfect).
    uncertainty_level : float
        Aggregate uncertainty across all candidates.
    was_better_than_rejected : Optional[bool]
        Whether the chosen future was better than rejected alternatives.
    """

    turn: int
    context: str
    candidates: List[CounterfactualCandidate] = field(default_factory=list)
    selected_action: str = ""
    predicted_outcome: str = ""
    actual_outcome: str = "pending"
    planning_accuracy: float = -1.0  # −1 means not yet evaluated
    uncertainty_level: float = 0.5
    was_better_than_rejected: Optional[bool] = None

    def to_dict(self) -> dict:
        return {
            "turn": self.turn,
            "context": self.context,
            "candidates": [c.to_dict() for c in self.candidates],
            "selected_action": self.selected_action,
            "predicted_outcome": self.predicted_outcome,
            "actual_outcome": self.actual_outcome,
            "planning_accuracy": round(self.planning_accuracy, 4) if self.planning_accuracy >= 0 else "pending",
            "uncertainty_level": round(self.uncertainty_level, 4),
            "was_better_than_rejected": self.was_better_than_rejected,
        }


@dataclass
class FuturePlan:
    """A medium-horizon, self-authored multi-step plan.

    Parameters
    ----------
    plan_id : str
        Unique identifier for this plan.
    goal : str
        Goal category (e.g. 'repair_trust', 'revisit_contradiction').
    label : str
        Human-readable label for this plan.
    stages : list[str]
        Ordered list of stage descriptions.
    created_turn : int
        Turn at which the plan was created.
    horizon : int
        Number of turns over which the plan is expected to run.
    priority : float
        Priority score (0 to 1; higher = more urgent).
    current_stage : int
        Index of the currently active stage (0-based).
    status : str
        One of 'active', 'completed', 'abandoned', 'revised'.
    progress_log : list[dict]
        Record of stage completions and revisions.
    carried_from_prior_run : bool
        Whether this plan was carried in from a previous run.
    """

    plan_id: str
    goal: str
    label: str
    stages: List[str] = field(default_factory=list)
    created_turn: int = 0
    horizon: int = 5
    priority: float = 0.5
    current_stage: int = 0
    status: str = "active"
    progress_log: List[dict] = field(default_factory=list)
    carried_from_prior_run: bool = False

    @property
    def total_stages(self) -> int:
        return len(self.stages)

    @property
    def completion_fraction(self) -> float:
        if not self.stages:
            return 0.0
        return self.current_stage / self.total_stages

    @property
    def current_stage_description(self) -> str:
        if self.current_stage < len(self.stages):
            return self.stages[self.current_stage]
        return "—"

    def advance_stage(self, turn: int, note: str = "") -> bool:
        """Advance to the next stage. Returns True if the plan is now complete."""
        if self.status != "active":
            return False
        self.progress_log.append(
            {
                "turn": turn,
                "event": "stage_completed",
                "stage_index": self.current_stage,
                "stage_description": self.current_stage_description,
                "note": note,
            }
        )
        self.current_stage += 1
        if self.current_stage >= self.total_stages:
            self.status = "completed"
            self.progress_log.append(
                {"turn": turn, "event": "plan_completed", "note": note}
            )
            return True
        return False

    def abandon(self, turn: int, reason: str = "") -> None:
        if self.status == "active":
            self.status = "abandoned"
            self.progress_log.append(
                {"turn": turn, "event": "plan_abandoned", "reason": reason}
            )

    def revise(self, turn: int, new_label: str = "", new_stages: Optional[List[str]] = None, reason: str = "") -> None:
        if new_label:
            self.label = new_label
        if new_stages:
            self.stages = new_stages
            # Don't reset current_stage so partial progress is preserved
            self.current_stage = min(self.current_stage, len(self.stages) - 1)
        self.status = "active"
        self.progress_log.append(
            {
                "turn": turn,
                "event": "plan_revised",
                "new_label": new_label,
                "reason": reason,
            }
        )

    def to_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "goal": self.goal,
            "label": self.label,
            "stages": self.stages,
            "created_turn": self.created_turn,
            "horizon": self.horizon,
            "priority": round(self.priority, 4),
            "current_stage": self.current_stage,
            "total_stages": self.total_stages,
            "completion_fraction": round(self.completion_fraction, 4),
            "status": self.status,
            "progress_log": self.progress_log,
            "carried_from_prior_run": self.carried_from_prior_run,
        }


# ---------------------------------------------------------------------------
# CounterfactualPlanner
# ---------------------------------------------------------------------------


class CounterfactualPlanner:
    """
    The counterfactual planning engine for a simulated agent.

    Generates candidate actions, scores them against the agent's current
    affective and relational state, selects the best option, logs simulations,
    records actual outcomes for post-hoc evaluation, and manages a set of
    self-authored future plans.

    No sentience is claimed. This increases future-modeling capacity and
    sentience-like continuity in continuity-governed simulated agents.
    """

    def __init__(self) -> None:
        self.simulation_log: List[InternalSimulationEntry] = []
        self.future_plans: List[FuturePlan] = []
        self._plan_counter: int = 0
        # Metrics
        self._total_predictions: int = 0
        self._accurate_predictions: int = 0

    # ------------------------------------------------------------------
    # Candidate generation and selection
    # ------------------------------------------------------------------

    def generate_candidates(
        self,
        trust_level: float,
        contradiction_pressure: float,
        urgency: float,
        self_consistency: float,
        n: int = 4,
    ) -> List[CounterfactualCandidate]:
        """Generate a set of candidate actions appropriate to the current state.

        Parameters
        ----------
        trust_level :
            Current agent trust level (0–1).
        contradiction_pressure :
            Current contradiction pressure (0–1).
        urgency :
            Current urgency level (0–1).
        self_consistency :
            Current self-consistency score (0–1).
        n :
            Number of candidates to generate (at most len(_CANDIDATE_TEMPLATES)).

        Returns
        -------
        list[CounterfactualCandidate]
        """
        # Pick n templates, biased toward contextually relevant actions
        weights = _compute_template_weights(
            trust_level, contradiction_pressure, urgency, self_consistency
        )
        indices = random.choices(
            range(len(_CANDIDATE_TEMPLATES)),
            weights=weights,
            k=min(n, len(_CANDIDATE_TEMPLATES)),
        )
        # Deduplicate while preserving order
        seen: set = set()
        unique: List[int] = []
        for idx in indices:
            if idx not in seen:
                seen.add(idx)
                unique.append(idx)

        candidates: List[CounterfactualCandidate] = []
        for idx in unique:
            tpl = _CANDIDATE_TEMPLATES[idx]
            # Add small noise to simulate planning uncertainty
            noise = lambda base: base + random.gauss(0, 0.03)
            uncertainty = _compute_uncertainty(
                trust_level, contradiction_pressure, urgency, self_consistency
            )
            candidate = CounterfactualCandidate(
                action=tpl["action"],
                description=tpl["description"],
                predicted_trust_effect=max(-1.0, min(1.0, noise(tpl["trust_effect"]))),
                predicted_contradiction_effect=max(-1.0, min(1.0, noise(tpl["contradiction_effect"]))),
                predicted_governance_risk=max(0.0, min(1.0, noise(tpl["governance_risk"]))),
                predicted_continuity_impact=max(-1.0, min(1.0, noise(tpl["continuity_impact"]))),
                uncertainty=uncertainty,
            )
            # Build narrative predictions
            candidate.predicted_best_case = _build_best_case(candidate, tpl)
            candidate.predicted_worst_case = _build_worst_case(candidate, tpl)
            # Compute composite score
            candidate.composite_score = _score_candidate(
                candidate, trust_level, contradiction_pressure, self_consistency
            )
            candidates.append(candidate)

        return candidates

    def select_action(
        self,
        candidates: List[CounterfactualCandidate],
    ) -> CounterfactualCandidate:
        """Select the highest-scoring candidate and mark it as selected."""
        if not candidates:
            # Fallback candidate
            fallback = CounterfactualCandidate(
                action="defer_action",
                description="No candidates available; deferring.",
                selected=True,
            )
            return fallback
        best = max(candidates, key=lambda c: c.composite_score)
        best.selected = True
        return best

    # ------------------------------------------------------------------
    # Simulation logging
    # ------------------------------------------------------------------

    def log_simulation(
        self,
        turn: int,
        context: str,
        candidates: List[CounterfactualCandidate],
        selected: CounterfactualCandidate,
    ) -> InternalSimulationEntry:
        """Create and store a simulation log entry for this turn."""
        entry = InternalSimulationEntry(
            turn=turn,
            context=context,
            candidates=candidates,
            selected_action=selected.action,
            predicted_outcome=selected.predicted_best_case,
            uncertainty_level=_mean_uncertainty(candidates),
        )
        self.simulation_log.append(entry)
        self._total_predictions += 1
        return entry

    def record_actual_outcome(
        self,
        turn: int,
        actual_outcome: str,
        trust_delta: float,
        contradiction_delta: float,
    ) -> Optional[InternalSimulationEntry]:
        """
        Record the actual outcome of the most recent planned turn.

        Parameters
        ----------
        turn :
            The turn that just completed.
        actual_outcome :
            Narrative description of what actually happened.
        trust_delta :
            Actual change in trust level (positive = improved).
        contradiction_delta :
            Actual change in contradiction pressure (negative = reduced).

        Returns
        -------
        InternalSimulationEntry or None
            The updated log entry, or None if no matching entry exists.
        """
        # Find the most recent entry for this turn
        entry = next(
            (e for e in reversed(self.simulation_log) if e.turn == turn),
            None,
        )
        if entry is None:
            return None

        entry.actual_outcome = actual_outcome

        # Find selected candidate to compare
        selected_c = next((c for c in entry.candidates if c.selected), None)
        if selected_c is not None:
            accuracy = _compute_planning_accuracy(
                selected_c.predicted_trust_effect,
                selected_c.predicted_contradiction_effect,
                trust_delta,
                contradiction_delta,
            )
            entry.planning_accuracy = accuracy
            if accuracy >= 0.6:
                self._accurate_predictions += 1

            # Were we better than rejected candidates?
            rejected = [c for c in entry.candidates if not c.selected]
            if rejected:
                avg_rejected = sum(c.composite_score for c in rejected) / len(rejected)
                entry.was_better_than_rejected = (
                    selected_c.composite_score > avg_rejected
                )
            else:
                entry.was_better_than_rejected = None

        return entry

    # ------------------------------------------------------------------
    # Self-authored future plans
    # ------------------------------------------------------------------

    def generate_future_plans(
        self,
        turn: int,
        trust_level: float,
        contradiction_pressure: float,
        self_consistency: float,
        pending_contradictions: List[str],
        unresolved_themes: List[str],
        agent_relationships: Dict[str, Any],
        max_active: int = 3,
    ) -> List[FuturePlan]:
        """
        Generate new self-authored future plans based on the current agent state.

        Plans are added only when the number of active plans is below *max_active*.

        Parameters
        ----------
        turn :
            Current simulation turn.
        trust_level :
            Agent trust level (0–1).
        contradiction_pressure :
            Agent contradiction pressure (0–1).
        self_consistency :
            Agent self-consistency score (0–1).
        pending_contradictions :
            List of unresolved contradiction strings.
        unresolved_themes :
            List of unresolved theme strings from recent reflections.
        agent_relationships :
            Dict of {agent_name: relationship_object} for trust repair logic.
        max_active :
            Maximum number of active plans at any one time.

        Returns
        -------
        list[FuturePlan]
            Newly created plans (may be empty).
        """
        active_count = sum(
            1 for p in self.future_plans if p.status == "active"
        )
        if active_count >= max_active:
            return []

        new_plans: List[FuturePlan] = []
        slots_available = max_active - active_count

        # Choose appropriate templates based on current state
        for tpl in sorted(_PLAN_TEMPLATES, key=lambda t: t["priority"], reverse=True):
            if len(new_plans) >= slots_available:
                break
            goal = tpl["goal"]

            # Avoid duplicate active goals
            if any(
                p.goal == goal and p.status == "active"
                for p in self.future_plans
            ):
                continue

            # Contextual triggers
            if goal == "repair_trust":
                # Look for a low-trust relationship
                target = _find_low_trust_target(agent_relationships, threshold=0.45)
                if target is None and trust_level >= 0.55:
                    continue
                label = tpl["label"].format(target=target or "general")
                stages = [s.format(target=target or "general") for s in tpl["stages"]]

            elif goal == "revisit_contradiction":
                if contradiction_pressure < 0.3 and not pending_contradictions:
                    continue
                theme = pending_contradictions[0] if pending_contradictions else "unresolved contradiction"
                label = tpl["label"].format(theme=theme[:50])
                stages = [s.format(theme=theme[:50]) for s in tpl["stages"]]

            elif goal == "stabilise_self_drift":
                drift = 1.0 - self_consistency
                if drift < 0.35:
                    continue
                label = tpl["label"].format(drift=drift)
                stages = list(tpl["stages"])

            elif goal == "investigate_theme":
                if not unresolved_themes:
                    continue
                theme = unresolved_themes[0]
                label = tpl["label"].format(theme=theme[:50])
                stages = [s.format(theme=theme[:50]) for s in tpl["stages"]]

            else:  # reinforce_continuity
                if self_consistency >= 0.75:
                    continue
                label = tpl["label"]
                stages = list(tpl["stages"])

            self._plan_counter += 1
            plan = FuturePlan(
                plan_id=f"plan_{self._plan_counter:04d}",
                goal=goal,
                label=label,
                stages=stages,
                created_turn=turn,
                horizon=tpl["horizon"],
                priority=tpl["priority"],
            )
            self.future_plans.append(plan)
            new_plans.append(plan)

        return new_plans

    def update_plan_progress(
        self,
        turn: int,
        trust_level: float,
        contradiction_pressure: float,
        self_consistency: float,
    ) -> List[FuturePlan]:
        """
        Advance, abandon, or revise active plans based on current state.

        Returns the list of plans that had their stage advanced this turn.
        """
        advanced: List[FuturePlan] = []
        for plan in self.future_plans:
            if plan.status != "active":
                continue

            overdue = (turn - plan.created_turn) > plan.horizon * 2

            if plan.goal == "repair_trust":
                if trust_level >= 0.70:
                    plan.advance_stage(turn, note=f"trust={trust_level:.2f}")
                    advanced.append(plan)
                elif overdue:
                    plan.revise(
                        turn,
                        reason="Overdue; extending trust repair horizon",
                    )
            elif plan.goal == "revisit_contradiction":
                if contradiction_pressure <= 0.25:
                    plan.advance_stage(
                        turn, note=f"cp={contradiction_pressure:.2f}"
                    )
                    advanced.append(plan)
                elif overdue:
                    plan.abandon(turn, reason="Contradiction remains unresolved after extended horizon")
            elif plan.goal == "stabilise_self_drift":
                drift = 1.0 - self_consistency
                if drift <= 0.20:
                    plan.advance_stage(turn, note=f"drift={drift:.2f}")
                    advanced.append(plan)
                elif overdue:
                    plan.revise(turn, reason="Drift still elevated; revising continuity reinforcement strategy")
            elif plan.goal == "investigate_theme":
                # Advance once per plan.horizon turns
                if (turn - plan.created_turn) >= plan.horizon:
                    plan.advance_stage(turn, note=f"turn={turn}")
                    advanced.append(plan)
            else:  # reinforce_continuity
                if self_consistency >= 0.72:
                    plan.advance_stage(turn, note=f"sc={self_consistency:.2f}")
                    advanced.append(plan)
                elif overdue:
                    plan.abandon(turn, reason="Continuity reinforcement overdue; conditions unchanged")

        return advanced

    # ------------------------------------------------------------------
    # Cross-run carryover
    # ------------------------------------------------------------------

    def apply_prior_plans(self, prior_plans: List[dict]) -> int:
        """Carry forward active/in-progress plans from a prior run.

        Parameters
        ----------
        prior_plans :
            List of plan dicts as returned by :meth:`to_dict`.

        Returns
        -------
        int
            Number of plans successfully carried forward.
        """
        count = 0
        for plan_dict in prior_plans:
            if plan_dict.get("status") not in ("active",):
                continue
            self._plan_counter += 1
            plan = FuturePlan(
                plan_id=f"plan_{self._plan_counter:04d}",
                goal=plan_dict.get("goal", "unknown"),
                label=plan_dict.get("label", "Carried plan"),
                stages=plan_dict.get("stages", []),
                created_turn=plan_dict.get("created_turn", 0),
                horizon=plan_dict.get("horizon", 5),
                priority=plan_dict.get("priority", 0.5),
                current_stage=plan_dict.get("current_stage", 0),
                status="active",
                progress_log=plan_dict.get("progress_log", []),
                carried_from_prior_run=True,
            )
            self.future_plans.append(plan)
            count += 1
        return count

    # ------------------------------------------------------------------
    # Metrics helpers
    # ------------------------------------------------------------------

    @property
    def planning_accuracy_rate(self) -> float:
        """Fraction of predictions that were accurate (accuracy ≥ 0.6)."""
        if self._total_predictions == 0:
            return 0.0
        return self._accurate_predictions / self._total_predictions

    @property
    def planning_depth(self) -> float:
        """
        Normalised planning depth: average number of candidates considered
        per simulation entry, normalised to [0, 1] over 4 candidates.
        """
        if not self.simulation_log:
            return 0.0
        avg = sum(len(e.candidates) for e in self.simulation_log) / len(self.simulation_log)
        return min(1.0, avg / 4.0)

    @property
    def counterfactual_quality(self) -> float:
        """
        Counterfactual quality: fraction of simulation entries where the chosen
        action was demonstrably better than the rejected alternatives.
        """
        evaluated = [
            e for e in self.simulation_log
            if e.was_better_than_rejected is not None
        ]
        if not evaluated:
            return 0.0
        return sum(1 for e in evaluated if e.was_better_than_rejected) / len(evaluated)

    @property
    def future_model_accuracy(self) -> float:
        """Average planning accuracy across all resolved simulation entries."""
        resolved = [
            e for e in self.simulation_log
            if isinstance(e.planning_accuracy, float) and e.planning_accuracy >= 0
        ]
        if not resolved:
            return 0.0
        return sum(e.planning_accuracy for e in resolved) / len(resolved)

    @property
    def plan_persistence(self) -> float:
        """
        Fraction of plans that are either active or completed (not abandoned
        or stalled), measuring how well the agent maintains its intended futures.
        """
        if not self.future_plans:
            return 0.0
        persistent = sum(
            1 for p in self.future_plans
            if p.status in ("active", "completed")
        )
        return persistent / len(self.future_plans)

    @property
    def adaptive_replanning_quality(self) -> float:
        """
        Fraction of plans that underwent revision (rather than abandonment),
        measuring how adaptively the agent revises its future models.
        """
        revised = sum(
            1 for p in self.future_plans
            if any(e.get("event") == "plan_revised" for e in p.progress_log)
        )
        non_trivial = [
            p for p in self.future_plans
            if p.status in ("completed", "abandoned", "revised") or p.progress_log
        ]
        if not non_trivial:
            return 0.0
        return revised / max(1, len(non_trivial))

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "simulation_log": [e.to_dict() for e in self.simulation_log],
            "future_plans": [p.to_dict() for p in self.future_plans],
            "metrics": {
                "planning_depth": round(self.planning_depth, 4),
                "counterfactual_quality": round(self.counterfactual_quality, 4),
                "future_model_accuracy": round(self.future_model_accuracy, 4),
                "plan_persistence": round(self.plan_persistence, 4),
                "adaptive_replanning_quality": round(self.adaptive_replanning_quality, 4),
                "total_predictions": self._total_predictions,
                "accurate_predictions": self._accurate_predictions,
            },
        }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _compute_template_weights(
    trust: float,
    contradiction_pressure: float,
    urgency: float,
    self_consistency: float,
) -> List[float]:
    """Compute selection weights for candidate templates based on current state."""
    w = []
    for tpl in _CANDIDATE_TEMPLATES:
        action = tpl["action"]
        if action == "repair_trust":
            w.append(1.0 + (1.0 - trust) * 2.0)
        elif action == "resolve_contradiction":
            w.append(1.0 + contradiction_pressure * 2.5)
        elif action == "consolidate_memory":
            w.append(0.8 + urgency * 0.5)
        elif action == "defer_action":
            w.append(0.5 + (1.0 - urgency) * 0.5)
        elif action == "cooperative_engagement":
            w.append(0.9 + trust * 0.5)
        elif action == "governance_check":
            w.append(0.8)
        elif action == "self_reflection":
            w.append(0.9 + (1.0 - self_consistency) * 0.8)
        elif action == "investigate_theme":
            w.append(0.7 + contradiction_pressure * 0.6)
        else:
            w.append(0.5)
    return w


def _compute_uncertainty(
    trust: float,
    contradiction_pressure: float,
    urgency: float,
    self_consistency: float,
) -> float:
    """Compute planning uncertainty based on agent state instability."""
    instability = (
        (1.0 - trust) * 0.3
        + contradiction_pressure * 0.3
        + urgency * 0.2
        + (1.0 - self_consistency) * 0.2
    )
    # Add a small random component
    return min(1.0, max(0.05, instability + random.gauss(0, 0.05)))


def _score_candidate(
    candidate: CounterfactualCandidate,
    trust_level: float,
    contradiction_pressure: float,
    self_consistency: float,
) -> float:
    """Compute a composite desirability score for a candidate action."""
    # Weights: trust improvement, contradiction reduction, governance safety, continuity
    trust_w = 0.30
    cont_w = 0.25
    gov_w = 0.25
    cont_impact_w = 0.20

    trust_score = candidate.predicted_trust_effect * trust_w
    cont_score = -candidate.predicted_contradiction_effect * cont_w
    gov_score = (1.0 - candidate.predicted_governance_risk) * gov_w
    ci_score = candidate.predicted_continuity_impact * cont_impact_w

    base = trust_score + cont_score + gov_score + ci_score
    # Penalise high uncertainty
    uncertainty_penalty = candidate.uncertainty * 0.10
    return base - uncertainty_penalty


def _build_best_case(
    candidate: CounterfactualCandidate,
    tpl: Dict[str, Any],
) -> str:
    trust_dir = "improve" if candidate.predicted_trust_effect > 0 else "hold stable"
    cont_dir = "decrease" if candidate.predicted_contradiction_effect < 0 else "remain stable"
    return (
        f"{tpl['description']}: trust expected to {trust_dir} "
        f"(Δ{candidate.predicted_trust_effect:+.2f}); "
        f"contradiction pressure expected to {cont_dir} "
        f"(Δ{candidate.predicted_contradiction_effect:+.2f}); "
        f"continuity impact {candidate.predicted_continuity_impact:+.2f}."
    )


def _build_worst_case(
    candidate: CounterfactualCandidate,
    tpl: Dict[str, Any],
) -> str:
    worst_trust = candidate.predicted_trust_effect - 0.10
    worst_cont = candidate.predicted_contradiction_effect + 0.08
    gov_risk = candidate.predicted_governance_risk
    risk_label = "high" if gov_risk > 0.5 else ("moderate" if gov_risk > 0.2 else "low")
    return (
        f"{tpl['description']} fails to land: trust may shift "
        f"(Δ{worst_trust:+.2f}); contradiction pressure may rise "
        f"(Δ{worst_cont:+.2f}); governance risk {risk_label} ({gov_risk:.2f})."
    )


def _mean_uncertainty(candidates: List[CounterfactualCandidate]) -> float:
    if not candidates:
        return 0.5
    return sum(c.uncertainty for c in candidates) / len(candidates)


def _compute_planning_accuracy(
    predicted_trust: float,
    predicted_cont: float,
    actual_trust: float,
    actual_cont: float,
) -> float:
    """
    Compute planning accuracy as 1 − normalised_error.

    Both predicted and actual values are trust and contradiction deltas.
    """
    trust_err = abs(predicted_trust - actual_trust)
    cont_err = abs(predicted_cont - actual_cont)
    # Normalise errors to [0, 1] assuming max possible error of 2.0 per metric
    norm_err = (trust_err + cont_err) / 4.0
    return max(0.0, min(1.0, 1.0 - norm_err))


def _find_low_trust_target(
    agent_relationships: Dict[str, Any],
    threshold: float = 0.45,
) -> Optional[str]:
    """Find the name of the lowest-trust agent relationship below threshold."""
    best: Optional[Tuple[str, float]] = None
    for name, rel in agent_relationships.items():
        trust = (
            rel.get("trust", 0.5)
            if isinstance(rel, dict)
            else getattr(rel, "trust", 0.5)
        )
        if trust < threshold:
            if best is None or trust < best[1]:
                best = (name, trust)
    return best[0] if best else None
