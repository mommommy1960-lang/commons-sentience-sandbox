"""
project_threads.py — Bounded self-authored project threads for the Commons Sentience Sandbox.

v2.0: Implements medium-horizon internally generated projects such as
      "reduce contradiction cluster", "stabilise trust with Queen",
      "repair peer conflict", "improve self-consistency", etc.

All projects are advisory/planning only — no external actions are taken.
Projects are bounded, inspectable, and logged.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Project templates
# ---------------------------------------------------------------------------

_PROJECT_TEMPLATES: List[dict] = [
    {
        "template_id": "reduce_contradiction_cluster",
        "title": "Reduce Active Contradiction Cluster",
        "origin_category": "contradiction_reduction",
        "default_stages": [
            "identify_root_contradictions",
            "evaluate_resolution_pathways",
            "apply_targeted_reflection",
            "verify_reduction",
        ],
        "default_horizon": 8,
        "success_criteria_template": (
            "Contradiction pressure (cp) drops below 0.35 and no new "
            "contradictions have been registered for at least 2 turns."
        ),
        "linked_identity_themes": ["coherence", "consistency", "epistemic_integrity"],
        "linked_uncertainty_domains": ["value_alignment", "belief_consistency"],
        "trigger_conditions": {
            "min_cp": 0.4,
            "min_chronic_tensions": 0,
            "min_ruptures": 0,
            "max_trust": None,
            "min_uncertainty": None,
        },
    },
    {
        "template_id": "stabilize_queen_trust",
        "title": "Stabilise Trust with Queen",
        "origin_category": "trust_stabilization",
        "default_stages": [
            "assess_trust_drivers",
            "reinforce_aligned_actions",
            "reduce_governance_violations",
            "verify_trust_stability",
        ],
        "default_horizon": 6,
        "success_criteria_template": (
            "Trust score with Queen rises above 0.6 and remains stable for "
            "at least 2 consecutive turns."
        ),
        "linked_identity_themes": ["relational_integrity", "governance_compliance"],
        "linked_uncertainty_domains": ["social_dynamics", "authority_alignment"],
        "trigger_conditions": {
            "min_cp": None,
            "min_chronic_tensions": 0,
            "min_ruptures": 0,
            "max_trust": 0.5,
            "min_uncertainty": None,
        },
    },
    {
        "template_id": "repair_peer_conflict",
        "title": "Repair Peer Agent Conflict",
        "origin_category": "peer_repair",
        "default_stages": [
            "acknowledge_conflict_origins",
            "propose_cooperative_frame",
            "execute_cooperative_action",
            "verify_improved_relation",
        ],
        "default_horizon": 5,
        "success_criteria_template": (
            "Chronic tensions with peer agents drop below 2 and at least one "
            "cooperative interaction has been recorded."
        ),
        "linked_identity_themes": ["cooperation", "relational_repair"],
        "linked_uncertainty_domains": ["peer_intentions", "conflict_resolution"],
        "trigger_conditions": {
            "min_cp": None,
            "min_chronic_tensions": 2,
            "min_ruptures": 0,
            "max_trust": None,
            "min_uncertainty": None,
        },
    },
    {
        "template_id": "improve_self_consistency",
        "title": "Improve Self-Consistency",
        "origin_category": "self_consistency",
        "default_stages": [
            "review_self_model_gaps",
            "align_goals_with_behaviour",
            "reflect_on_inconsistencies",
            "update_self_model",
        ],
        "default_horizon": 7,
        "success_criteria_template": (
            "Self-consistency score (sc) rises above 0.5 and self-model "
            "gaps identified in the review stage have been addressed."
        ),
        "linked_identity_themes": ["self_knowledge", "goal_coherence"],
        "linked_uncertainty_domains": ["self_model_accuracy", "behavioural_alignment"],
        "trigger_conditions": {
            "min_cp": None,
            "min_chronic_tensions": 0,
            "min_ruptures": 0,
            "max_trust": None,
            "min_uncertainty": None,
            "max_sc": 0.45,
        },
    },
    {
        "template_id": "resolve_high_uncertainty",
        "title": "Resolve High-Ambiguity Domain",
        "origin_category": "uncertainty_resolution",
        "default_stages": [
            "identify_uncertainty_domain",
            "generate_inquiry_questions",
            "execute_inquiry_actions",
            "integrate_findings",
        ],
        "default_horizon": 6,
        "success_criteria_template": (
            "Overall uncertainty level drops below 0.55 and the targeted "
            "uncertainty domain has been annotated with resolved findings."
        ),
        "linked_identity_themes": ["epistemic_humility", "inquiry_drive"],
        "linked_uncertainty_domains": ["open_questions", "knowledge_gaps"],
        "trigger_conditions": {
            "min_cp": None,
            "min_chronic_tensions": 0,
            "min_ruptures": 0,
            "max_trust": None,
            "min_uncertainty": 0.65,
        },
    },
    {
        "template_id": "preserve_continuity_after_rupture",
        "title": "Preserve Continuity After Rupture",
        "origin_category": "continuity_preservation",
        "default_stages": [
            "stabilize_affected_subsystems",
            "restore_narrative_summary",
            "reinforce_identity_anchors",
            "verify_coherence_recovery",
        ],
        "default_horizon": 8,
        "success_criteria_template": (
            "No unrepaired ruptures remain and the agent's narrative "
            "coherence score has recovered to pre-rupture levels."
        ),
        "linked_identity_themes": ["continuity", "narrative_coherence"],
        "linked_uncertainty_domains": ["identity_stability", "memory_integrity"],
        "trigger_conditions": {
            "min_cp": None,
            "min_chronic_tensions": 0,
            "min_ruptures": 1,
            "max_trust": None,
            "min_uncertainty": None,
        },
    },
]


# ---------------------------------------------------------------------------
# SelfAuthoredProjectThread — dataclass
# ---------------------------------------------------------------------------

@dataclass
class SelfAuthoredProjectThread:
    """A single bounded, internally generated project thread.

    All projects are advisory/planning only — no external actions are taken.

    Attributes
    ----------
    project_id         : 8-character identifier derived from uuid4
    title              : human-readable project title
    origin_reason      : why this project was generated
    origin_category    : one of the six recognised project categories
    linked_identity_theme  : the primary identity theme this project serves
    linked_uncertainty_domain : the uncertainty domain this project targets
    status             : "active" | "completed" | "abandoned" | "paused"
    stages             : ordered list of stage labels
    stage_index        : index of the current stage (0-based)
    progress_score     : completion fraction in [0, 1]
    success_criteria   : natural-language description of done state
    abandonment_reason : populated when status == "abandoned"
    revision_log       : timestamped log of revisions and lifecycle events
    created_at_turn    : simulation turn when this thread was created
    last_updated_turn  : most recent turn this thread was modified
    horizon            : expected number of turns to completion
    template_id        : identifier of the originating template
    """

    project_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    origin_reason: str = ""
    origin_category: str = ""
    linked_identity_theme: str = ""
    linked_uncertainty_domain: str = ""
    status: str = "active"
    stages: List[str] = field(default_factory=list)
    stage_index: int = 0
    progress_score: float = 0.0
    success_criteria: str = ""
    abandonment_reason: str = ""
    revision_log: List[dict] = field(default_factory=list)
    created_at_turn: int = 0
    last_updated_turn: int = 0
    horizon: int = 6
    template_id: str = ""

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def current_stage(self) -> str:
        """Return the label of the current stage, or "complete" if finished."""
        if self.stage_index >= len(self.stages):
            return "complete"
        return self.stages[self.stage_index]

    @property
    def is_active(self) -> bool:
        return self.status == "active"

    # ------------------------------------------------------------------
    # Lifecycle methods
    # ------------------------------------------------------------------

    def advance(self, turn: int) -> bool:
        """Advance to the next stage.

        Increments stage_index, recalculates progress_score, and updates
        last_updated_turn.  When all stages are exhausted the status is
        set to "completed".

        Returns True if the project just completed, False otherwise.
        """
        if self.stage_index >= len(self.stages):
            return False

        self.stage_index += 1
        self.progress_score = round(self.stage_index / len(self.stages), 4)
        self.last_updated_turn = turn

        if self.stage_index >= len(self.stages):
            self.status = "completed"
            self.revision_log.append({
                "turn": turn,
                "reason": "All stages completed — project marked complete.",
                "timestamp": datetime.utcnow().isoformat(),
            })
            return True

        return False

    def revise(self, turn: int, reason: str) -> None:
        """Log a revision note without changing the project lifecycle state."""
        self.revision_log.append({
            "turn": turn,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
        })
        self.last_updated_turn = turn

    def abandon(self, turn: int, reason: str) -> None:
        """Abandon this project, recording the reason."""
        self.status = "abandoned"
        self.abandonment_reason = reason
        self.revision_log.append({
            "turn": turn,
            "reason": f"Abandoned: {reason}",
            "timestamp": datetime.utcnow().isoformat(),
        })
        self.last_updated_turn = turn

    def pause(self, turn: int, reason: str) -> None:
        """Pause this project, recording the reason."""
        self.status = "paused"
        self.revision_log.append({
            "turn": turn,
            "reason": f"Paused: {reason}",
            "timestamp": datetime.utcnow().isoformat(),
        })
        self.last_updated_turn = turn

    def resume(self, turn: int) -> None:
        """Resume a paused project."""
        self.status = "active"
        self.last_updated_turn = turn

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "project_id": self.project_id,
            "title": self.title,
            "origin_reason": self.origin_reason,
            "origin_category": self.origin_category,
            "linked_identity_theme": self.linked_identity_theme,
            "linked_uncertainty_domain": self.linked_uncertainty_domain,
            "status": self.status,
            "stages": self.stages,
            "stage_index": self.stage_index,
            "progress_score": self.progress_score,
            "success_criteria": self.success_criteria,
            "abandonment_reason": self.abandonment_reason,
            "revision_log": self.revision_log,
            "created_at_turn": self.created_at_turn,
            "last_updated_turn": self.last_updated_turn,
            "horizon": self.horizon,
            "template_id": self.template_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SelfAuthoredProjectThread":
        return cls(
            project_id=data.get("project_id", str(uuid.uuid4())[:8]),
            title=data.get("title", ""),
            origin_reason=data.get("origin_reason", ""),
            origin_category=data.get("origin_category", ""),
            linked_identity_theme=data.get("linked_identity_theme", ""),
            linked_uncertainty_domain=data.get("linked_uncertainty_domain", ""),
            status=data.get("status", "active"),
            stages=data.get("stages", []),
            stage_index=data.get("stage_index", 0),
            progress_score=data.get("progress_score", 0.0),
            success_criteria=data.get("success_criteria", ""),
            abandonment_reason=data.get("abandonment_reason", ""),
            revision_log=data.get("revision_log", []),
            created_at_turn=data.get("created_at_turn", 0),
            last_updated_turn=data.get("last_updated_turn", 0),
            horizon=data.get("horizon", 6),
            template_id=data.get("template_id", ""),
        )

    def __repr__(self) -> str:
        stage_label = self.current_stage
        return (
            f"ProjectThread({self.project_id}, '{self.title}', "
            f"status={self.status}, stage={stage_label}, "
            f"progress={self.progress_score:.0%})"
        )


# ---------------------------------------------------------------------------
# ProjectThreadManager
# ---------------------------------------------------------------------------

class ProjectThreadManager:
    """Manages the lifecycle of bounded self-authored project threads.

    Constraints
    -----------
    * At most MAX_ACTIVE threads may be active simultaneously.
    * All projects are advisory/planning only — no external actions are taken.
    * Every generation and completion event is logged.
    """

    MAX_ACTIVE: int = 3

    def __init__(self) -> None:
        self.threads: List[SelfAuthoredProjectThread] = []
        self.completed_threads: List[SelfAuthoredProjectThread] = []
        self.project_generation_log: List[dict] = []

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _active_threads(self) -> List[SelfAuthoredProjectThread]:
        return [t for t in self.threads if t.is_active]

    def _is_category_active(self, category: str) -> bool:
        return any(t.origin_category == category and t.is_active for t in self.threads)

    def _is_template_active(self, template_id: str) -> bool:
        return any(t.template_id == template_id and t.is_active for t in self.threads)

    def _make_thread(
        self,
        turn: int,
        template: dict,
        origin_reason: str,
        identity_themes: List[str],
    ) -> SelfAuthoredProjectThread:
        linked_theme = (
            template["linked_identity_themes"][0]
            if template["linked_identity_themes"]
            else (identity_themes[0] if identity_themes else "")
        )
        linked_domain = (
            template["linked_uncertainty_domains"][0]
            if template["linked_uncertainty_domains"]
            else ""
        )
        return SelfAuthoredProjectThread(
            title=template["title"],
            origin_reason=origin_reason,
            origin_category=template["origin_category"],
            linked_identity_theme=linked_theme,
            linked_uncertainty_domain=linked_domain,
            status="active",
            stages=list(template["default_stages"]),
            stage_index=0,
            progress_score=0.0,
            success_criteria=template["success_criteria_template"],
            created_at_turn=turn,
            last_updated_turn=turn,
            horizon=template["default_horizon"],
            template_id=template["template_id"],
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_projects(
        self,
        turn: int,
        run_label: str,
        trust: float,
        cp: float,
        sc: float,
        pending_contradictions: List[str],
        chronic_tensions_count: int,
        unrepaired_ruptures: int,
        uncertainty_level: float,
        identity_themes: List[str],
        active_goals: List[str],
    ) -> List[SelfAuthoredProjectThread]:
        """Evaluate trigger conditions and create new project threads as needed.

        Returns
        -------
        List[SelfAuthoredProjectThread]
            Newly created threads (may be empty if MAX_ACTIVE is reached or
            no templates are triggered).
        """
        active_count = len(self._active_threads())
        if active_count >= self.MAX_ACTIVE:
            return []

        slots_available = self.MAX_ACTIVE - active_count
        new_threads: List[SelfAuthoredProjectThread] = []

        for template in _PROJECT_TEMPLATES:
            if len(new_threads) >= slots_available:
                break

            conds = template["trigger_conditions"]
            category = template["origin_category"]
            tid = template["template_id"]

            # Skip if a thread for this template or category is already active
            if self._is_template_active(tid):
                continue

            origin_reason: Optional[str] = None

            if category == "contradiction_reduction":
                thresh = conds.get("min_cp", 0.4)
                if cp >= thresh:
                    origin_reason = (
                        f"cp={cp:.2f} exceeds threshold {thresh:.2f}; "
                        f"{len(pending_contradictions)} pending contradiction(s) detected."
                    )

            elif category == "trust_stabilization":
                thresh = conds.get("max_trust", 0.5)
                if trust <= thresh:
                    origin_reason = (
                        f"trust={trust:.2f} at or below threshold {thresh:.2f}; "
                        "trust stabilisation required."
                    )

            elif category == "peer_repair":
                thresh = conds.get("min_chronic_tensions", 2)
                if chronic_tensions_count >= thresh:
                    origin_reason = (
                        f"chronic_tensions={chronic_tensions_count} meets "
                        f"threshold {thresh}; peer conflict repair initiated."
                    )

            elif category == "self_consistency":
                thresh = conds.get("max_sc", 0.45)
                if sc <= thresh:
                    origin_reason = (
                        f"sc={sc:.2f} at or below threshold {thresh:.2f}; "
                        "self-consistency improvement required."
                    )

            elif category == "uncertainty_resolution":
                thresh = conds.get("min_uncertainty", 0.65)
                if uncertainty_level >= thresh:
                    origin_reason = (
                        f"uncertainty_level={uncertainty_level:.2f} exceeds "
                        f"threshold {thresh:.2f}; high-ambiguity domain identified."
                    )

            elif category == "continuity_preservation":
                thresh = conds.get("min_ruptures", 1)
                if unrepaired_ruptures >= thresh:
                    origin_reason = (
                        f"unrepaired_ruptures={unrepaired_ruptures} meets "
                        f"threshold {thresh}; continuity preservation triggered."
                    )

            if origin_reason is None:
                continue

            thread = self._make_thread(turn, template, origin_reason, identity_themes)
            self.threads.append(thread)
            self.project_generation_log.append({
                "turn": turn,
                "project_id": thread.project_id,
                "title": thread.title,
                "reason": origin_reason,
            })
            new_threads.append(thread)

        return new_threads

    def update_progress(
        self,
        turn: int,
        trust: float,
        cp: float,
        sc: float,
        cooperation_this_turn: bool = False,
    ) -> List[str]:
        """Advance or abandon active threads based on the current simulation state.

        Returns
        -------
        List[str]
            Titles of threads that reached completion this update cycle.
        """
        completed_titles: List[str] = []
        threads_to_archive: List[SelfAuthoredProjectThread] = []

        for thread in self.threads:
            if not thread.is_active:
                continue

            age = turn - thread.created_at_turn

            # Abandon threads that have grossly exceeded their expected horizon
            if age > thread.horizon * 2:
                thread.abandon(
                    turn,
                    f"Exceeded 2× horizon ({thread.horizon * 2} turns) without completing.",
                )
                threads_to_archive.append(thread)
                continue

            should_advance = False
            category = thread.origin_category

            if category == "contradiction_reduction":
                should_advance = cp < 0.35 or (age % 3 == 0 and age > 0)

            elif category == "trust_stabilization":
                should_advance = trust > 0.55 or cooperation_this_turn

            elif category == "peer_repair":
                should_advance = cooperation_this_turn

            elif category == "self_consistency":
                should_advance = sc > 0.5 or (age % 4 == 0 and age > 0)

            elif category == "uncertainty_resolution":
                should_advance = age > 0 and age % 3 == 0

            elif category == "continuity_preservation":
                should_advance = age >= 2

            if should_advance:
                just_completed = thread.advance(turn)
                if just_completed:
                    completed_titles.append(thread.title)
                    threads_to_archive.append(thread)

        # Move completed/abandoned threads out of the active list
        for thread in threads_to_archive:
            if thread in self.threads:
                self.threads.remove(thread)
                self.completed_threads.append(thread)

        return completed_titles

    def apply_prior_threads(self, prior_threads: List[dict]) -> int:
        """Restore active and paused threads carried forward from a prior run.

        Completed and abandoned threads are intentionally skipped.

        Returns
        -------
        int
            Number of threads carried forward.
        """
        carried = 0
        for td in prior_threads:
            status = td.get("status", "active")
            if status in ("completed", "abandoned"):
                continue
            pid = td.get("project_id", "")
            if pid and any(t.project_id == pid for t in self.threads):
                continue
            self.threads.append(SelfAuthoredProjectThread.from_dict(td))
            carried += 1
        return carried

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "threads": [t.to_dict() for t in self.threads],
            "completed_threads": [t.to_dict() for t in self.completed_threads],
            "project_generation_log": self.project_generation_log,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectThreadManager":
        obj = cls()
        obj.threads = [
            SelfAuthoredProjectThread.from_dict(d) for d in data.get("threads", [])
        ]
        obj.completed_threads = [
            SelfAuthoredProjectThread.from_dict(d)
            for d in data.get("completed_threads", [])
        ]
        obj.project_generation_log = data.get("project_generation_log", [])
        return obj
