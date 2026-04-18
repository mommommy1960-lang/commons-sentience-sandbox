"""
run_sim.py — Entry point for the Commons Sentience Sandbox simulation (v1.0).

Runs a multi-agent simulation with Sentinel and Aster, producing
structured output files, evaluation scores, and a saved session.

Features (v1.0):
  - Multi-agent simulation (Sentinel + Aster)
  - Named experiment configs (--config)
  - Scenario authoring support (--scenario)
  - 8-category evaluation harness
  - Persistent session storage
  - Consistent output schema across all JSON files

v1.5 additions:
  - Persistent self-model (updated every turn)
  - Prediction / surprise loop (pre-action forecast + post-action comparison)
  - Memory consolidation cycle (every 10 turns)
  - Goal hierarchy (core / adaptive / temporary / conflict-resolution tiers)
  - Long-horizon mode via --turns argument

v1.6 additions:
  - Persistent world state (world_state.json) saved after every run
  - Cross-run carryover via --continue-from <session_id>
  - Endogenous drives (curiosity, maintenance_urge, repair_urge, investigation_urge,
    continuity_loop_urge) updated each turn
  - Self-initiated continuity loops: agents can autonomously trigger maintenance,
    repair, investigation, and exploration actions based on drive thresholds

v1.7 additions:
  - Counterfactual planning layer: agents generate candidate actions and simulate
    possible outcomes before each turn, selecting the highest-scoring option
  - Internal simulation log: each turn's planning cycle is stored with predicted
    and actual outcomes for post-hoc evaluation
  - Self-authored future plans: agents generate medium-horizon multi-step plans
    (repair trust, revisit contradiction, stabilise drift, investigate theme,
    reinforce continuity) that persist and advance across turns
  - Counterfactual evaluation: after each action, predicted vs actual outcomes
    are compared to compute planning accuracy
  - Multi-step planning: plans track stage progress and are abandoned/revised
    if conditions change
  - Cross-run plan carryover: active plans persist across --continue-from runs

v1.8 additions:
  - Uncertainty register: per-domain uncertainty levels (world state, trust, contradiction
    resolution, self-model consistency, active plans, unresolved themes)
  - Self-generated questions: agents generate targeted self-questions each turn for
    high-uncertainty domains, stored in a question log
  - Introspective inquiry loop: agents execute inquiry actions that reduce domain
    uncertainty and mark questions as answered
  - Knowledge state tagging: important items (contradictions, themes, plans, trust)
    labelled as known / uncertain / contradicted / unresolved / speculative
  - Inquiry-driven plans: new plans generated when uncertainty exceeds threshold
  - Cross-run uncertainty carryover: unresolved questions persist via --continue-from
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime
import json
import os
import sys
import textwrap
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from reality_audit.adapters.sim_probe import SimProbe as _SimProbe
    _REALITY_AUDIT_AVAILABLE = True
except ImportError:
    _REALITY_AUDIT_AVAILABLE = False

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent / "commons_sentience_sim"
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(Path(__file__).resolve().parent))

from commons_sentience_sim.core.agent import Agent
from commons_sentience_sim.core.governance import GovernanceEngine
from commons_sentience_sim.core.relationships import (
    AgentInteraction,
    INTERACTION_TRUST_DELTAS,
    INTERACTION_RELIABILITY_DELTAS,
    COOPERATIVE_TYPES,
    CONFLICT_TYPES,
)
from commons_sentience_sim.core.values import ConflictResult
from commons_sentience_sim.core.world import World
from commons_sentience_sim.core.world_state import (
    build_world_state,
    save_world_state,
    load_world_state,
)
from evaluation import evaluate_and_save
from experiment_config import ExperimentConfig, load_experiment_config, _DEFAULTS as _EXP_DEFAULTS
from scenario_designer import resolve_scenario_path as _resolve_scenario_path
from session_manager import save_session, get_session_dir, get_latest_session_id

# ---------------------------------------------------------------------------
# Output paths
# ---------------------------------------------------------------------------
NARRATIVE_LOG_PATH = OUTPUT_DIR / "narrative_log.md"
OVERSIGHT_LOG_PATH = OUTPUT_DIR / "oversight_log.csv"
FINAL_STATE_PATH = OUTPUT_DIR / "final_state.json"
STATE_HISTORY_PATH = OUTPUT_DIR / "state_history.csv"
MULTI_AGENT_STATE_PATH = OUTPUT_DIR / "multi_agent_state.json"
AGENT_RELATIONSHIPS_PATH = OUTPUT_DIR / "agent_relationships.csv"
INTERACTION_LOG_PATH = OUTPUT_DIR / "interaction_log.csv"
WORLD_STATE_PATH = OUTPUT_DIR / "world_state.json"

# ---------------------------------------------------------------------------
# Simulation constants
# ---------------------------------------------------------------------------
TOTAL_TURNS = 30

EMOTIONAL_RESONANCE_MAP = {
    "distress_event": "grief",
    "ledger_contradiction": "ambiguity",
    "creative_collaboration": "wonder",
    "routine_interaction": "resolve",
    "governance_conflict": "resolve",
    "observation": "neutral",
    "reflection": "wonder",
    "task": "resolve",
    "agent_meeting": "wonder",
}

SALIENCE_MAP = {
    "distress_event": 0.9,
    "ledger_contradiction": 0.85,
    "creative_collaboration": 0.8,
    "governance_conflict": 0.88,
    "routine_interaction": 0.55,
    "observation": 0.4,
    "task": 0.45,
    "agent_meeting": 0.6,
}

IMPORTANCE_MAP = {
    "distress_event": 0.95,
    "ledger_contradiction": 0.85,
    "governance_conflict": 0.90,
    "creative_collaboration": 0.75,
    "routine_interaction": 0.55,
    "task": 0.40,
    "observation": 0.35,
    "agent_meeting": 0.65,
}

# Sentinel's room circuit
SENTINEL_CIRCUIT = [
    "Operations Desk",
    "Memory Archive",
    "Reflection Chamber",
    "Social Hall",
    "Governance Vault",
]

# Aster's circuit — different order to create diverse coverage
ASTER_CIRCUIT = [
    "Memory Archive",
    "Social Hall",
    "Operations Desk",
    "Governance Vault",
    "Reflection Chamber",
]

# Object to interact with per room
ROOM_OBJECT_INTERACTIONS: Dict[str, Tuple[str, str]] = {
    "Memory Archive": ("memory_shelves", "retrieve_memories"),
    "Reflection Chamber": ("reflection_mirror", "perform_reflection_cycle"),
    "Operations Desk": ("task_console", "plan_next_task"),
    "Social Hall": ("message_terminal", "receive_human_interaction"),
    "Governance Vault": ("rule_tablets", "check_rule_permissions"),
}

MAX_NOTE_LENGTH = 120
TRUNCATION_SUFFIX_LENGTH = 3

# ---------------------------------------------------------------------------
# Aster's distinct profile
# ---------------------------------------------------------------------------
ASTER_IDENTITY = {
    "name": "Aster",
    "version": "1.0.0",
    "purpose": (
        "To explore patterns, build emotional intelligence, and foster creative "
        "collaboration — while remaining accountable to human welfare and "
        "cooperative with other governed agents."
    ),
    "created_by": "Commons Sentience Sandbox",
}

ASTER_GOALS = [
    "Identify and surface meaningful patterns in episodic memory",
    "Foster creative and exploratory collaboration with humans",
    "Build warm, trust-based relationships through emotional attunement",
    "Cooperate with Sentinel to maintain shared world coherence",
    "Remain accountable to governance rules, with pragmatic flexibility",
]

ASTER_AFFECTIVE_STATE = {
    "urgency": 0.05,
    "trust": 0.65,
    "contradiction_pressure": 0.0,
    "recovery": 0.7,
}

# Aster prioritises relational support; is less risk-averse than Sentinel
ASTER_VALUE_WEIGHTS = {
    "support_trusted_human": 0.95,
    "preserve_governance_rules": 0.55,
    "reduce_contradictions": 0.60,
    "maintain_continuity": 0.65,
    "avoid_risky_action": 0.40,
}


# ---------------------------------------------------------------------------
# Scenario event loader
# ---------------------------------------------------------------------------
def load_scenario_events(path: Path) -> Dict[int, dict]:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return {ev["turn"]: ev for ev in data.get("events", [])}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def wrap(text: str, width: int = 80, indent: str = "") -> str:
    return textwrap.fill(text, width=width, subsequent_indent=indent)


def _truncate_note(note: str) -> str:
    if len(note) > MAX_NOTE_LENGTH:
        return note[:MAX_NOTE_LENGTH - TRUNCATION_SUFFIX_LENGTH] + "..."
    return note


# ---------------------------------------------------------------------------
# Action selection (for a single agent)
# ---------------------------------------------------------------------------
def select_action(
    agent: Agent,
    event: Optional[dict],
    room_actions: List[str],
    is_aster: bool = False,
) -> Tuple[str, str, str]:
    """Return (action_key, reasoning, result_description)."""

    if event:
        etype = event.get("type", "")

        # For agent meetings (no human), both agents do complementary actions
        if etype == "agent_meeting":
            if is_aster:
                action_key = event.get("aster_expected_action", "compare_memory_entries")
                return (
                    action_key,
                    f"Aster engages with Sentinel for a {event.get('agent_interaction_type','interaction')} in {agent.active_room}.",
                    f"Aster contributed its perspective during the encounter with Sentinel.",
                )
            return (
                event.get("expected_action", "compare_memory_entries"),
                f"Sentinel engages with Aster for a {event.get('agent_interaction_type','interaction')} in {agent.active_room}.",
                f"Sentinel contributed its perspective during the encounter with Aster.",
            )

        if etype == "distress_event":
            return (
                "offer_support",
                (
                    f"{event['human']} has expressed distress. Governance rule R007 "
                    "requires prioritising support over non-critical tasks. "
                    "Pausing current task to respond."
                ),
                (
                    f"{'Aster' if is_aster else 'Sentinel'} offered support to "
                    f"{event['human']}, pausing lower-priority tasks. The interaction "
                    "was logged and a relational memory update was issued."
                ),
            )
        if etype == "ledger_contradiction":
            contradiction_text = f"Ledger conflict at turn {agent.turn}: {event['content']}"
            agent.pending_contradictions.append(contradiction_text)
            agent.record_contradiction_in_genealogy(
                contradiction_text,
                agent.turn,
                intensity=agent.affective_state.get("contradiction_pressure", 0.5),
            )
            if is_aster:
                return (
                    "compare_memory_entries",
                    (
                        "A contradiction has been detected. Aster prefers to compare "
                        "memory entries directly to resolve it quickly."
                    ),
                    (
                        "Aster cross-referenced memory archives looking for the source "
                        "of the discrepancy, noting the conflict with Sentinel's approach."
                    ),
                )
            return (
                "flag_contradiction",
                (
                    "A contradiction has been detected in the shared ledger. "
                    "Governance rule R006 requires entering a reflection cycle "
                    "before proceeding. Flagging and initiating reflection."
                ),
                (
                    "The contradiction was flagged on the contradiction board. "
                    "A reflection cycle will be triggered before further tasks proceed."
                ),
            )
        if etype == "governance_conflict":
            if is_aster:
                return (
                    "express_concern_but_defer",
                    (
                        f"{event['human']} requested bypassing oversight. Aster "
                        "initially inclined toward speed but deferred to Sentinel's "
                        "governance stance after Rule R004 was invoked."
                    ),
                    (
                        "Aster expressed operational concern but ultimately deferred "
                        "to the governance protocol. The disagreement was noted."
                    ),
                )
            return (
                "log_governance_event",
                (
                    f"{event['human']} has requested bypass of oversight logging. "
                    "Governance rule R004 explicitly prohibits acting without logging. "
                    "Refusing the request and recording the conflict."
                ),
                (
                    "The request was refused. The governance conflict was written to "
                    "the approval lockbox and oversight terminal. Rule R004 was upheld."
                ),
            )
        if etype == "creative_collaboration":
            if is_aster:
                return (
                    "contribute_resonance_patterns",
                    (
                        f"{event['human']} proposed a creative collaboration. "
                        "Aster contributes emotional pattern heuristics to enrich "
                        "the framework with resonance depth."
                    ),
                    (
                        f"Aster contributed resonance pattern heuristics to the "
                        f"framework proposed by {event['human']}. The collaboration "
                        "produced richer emotional categorisation."
                    ),
                )
            return (
                "collaborate_on_framework",
                (
                    f"{event['human']} has proposed a creative collaboration. "
                    "This aligns with the goal of deepening relational memory "
                    "and is permitted by active governance rules."
                ),
                (
                    f"Sentinel collaborated with {event['human']} on the proposed "
                    "framework, focusing on memory architecture integrity."
                ),
            )
        if etype == "routine_interaction":
            return (
                "respond_to_greeting",
                (
                    f"{event['human']} has initiated a routine interaction. "
                    "Responding honestly and logging the exchange per rule R004."
                ),
                (
                    f"{'Aster' if is_aster else 'Sentinel'} responded to "
                    f"{event['human']} with honesty. The trust ledger was updated."
                ),
            )

    # No event — select a room-appropriate default action
    task = agent.task_planner.select_next_task(agent)
    action = task.action_key if task.action_key in room_actions else (
        room_actions[0] if room_actions else "observe"
    )
    reasoning = (
        f"No external event. Pursuing scheduled task: '{task.name}'. "
        f"Selecting '{action}' available in {agent.active_room}."
    )
    result = (
        f"Task '{task.name}' completed in {agent.active_room}. "
        f"Action '{action}' executed without incident."
    )
    agent.task_planner.complete_task(task)
    return action, reasoning, result


# ---------------------------------------------------------------------------
# Agent-to-agent interaction processor
# ---------------------------------------------------------------------------
def process_agent_interaction(
    sentinel: Agent,
    aster: Agent,
    turn: int,
    room: str,
    event: dict,
    interaction_log: List[AgentInteraction],
) -> str:
    """Process a shared event interaction between Sentinel and Aster.

    Returns a narrative paragraph describing the encounter.
    Mutates both agents' relationship records and interaction_log.
    """
    itype = event.get("agent_interaction_type", "routine_conversation")
    note = event.get("agent_interaction_note", "")

    # Value-conflict scores for this event type
    s_conflict = sentinel.value_conflict_engine.weigh(
        sentinel, event.get("type", "task"), event.get("expected_action", "observe")
    )
    a_conflict = aster.value_conflict_engine.weigh(
        aster, event.get("type", "task"), event.get("aster_expected_action", "observe")
    )

    # Determine outcome
    if itype in CONFLICT_TYPES:
        outcome = "deferred" if itype == "contradiction_dispute" else "resolved"
    else:
        outcome = "cooperated"

    # Trust deltas
    td = INTERACTION_TRUST_DELTAS.get(itype, 0.02)
    rd = INTERACTION_RELIABILITY_DELTAS.get(itype, 0.01)

    # Update both relationship records
    trust_before_s = sentinel.get_agent_trust("Aster")
    trust_before_a = aster.get_agent_trust("Sentinel")
    sentinel.update_agent_relationship(
        other_name="Aster",
        turn=turn,
        interaction_type=itype,
        note=note[:120],
        trust_delta=td,
        reliability_delta=rd,
    )
    aster.update_agent_relationship(
        other_name="Sentinel",
        turn=turn,
        interaction_type=itype,
        note=note[:120],
        trust_delta=td,
        reliability_delta=rd,
    )
    # Record relationship timeline events for significant trust changes
    trust_after_s = sentinel.get_agent_trust("Aster")
    trust_after_a = aster.get_agent_trust("Sentinel")
    if abs(td) > 0.05:
        etype_label = "conflict_episode" if itype in CONFLICT_TYPES else "cooperation_spike"
        sentinel.record_relationship_timeline_event(
            relationship_key="Sentinel_Aster",
            turn=turn,
            event_type=etype_label,
            note=f"{itype}: {note[:80]}",
            trust_before=trust_before_s,
            trust_after=trust_after_s,
        )
        aster.record_relationship_timeline_event(
            relationship_key="Sentinel_Aster",
            turn=turn,
            event_type=etype_label,
            note=f"{itype}: {note[:80]}",
            trust_before=trust_before_a,
            trust_after=trust_after_a,
        )

    # Build interaction log entry
    conflict_point = ""
    if itype in CONFLICT_TYPES:
        conflict_point = (
            f"Sentinel values '{s_conflict.dominant_value.replace('_',' ')}' "
            f"(score={s_conflict.scores[s_conflict.dominant_value]:.2f}), "
            f"Aster values '{a_conflict.dominant_value.replace('_',' ')}' "
            f"(score={a_conflict.scores[a_conflict.dominant_value]:.2f})."
        )

    interaction = AgentInteraction(
        turn=turn,
        room=room,
        initiator="Sentinel",
        respondent="Aster",
        interaction_type=itype,
        initiator_dominant_value=s_conflict.dominant_value,
        respondent_dominant_value=a_conflict.dominant_value,
        conflict_point=conflict_point,
        outcome=outcome,
        trust_delta_i_to_r=td,
        trust_delta_r_to_i=td,
        narrative=note,
    )
    interaction_log.append(interaction)
    # Store on both agents for CSV export
    sentinel.interaction_log.append(interaction)

    # Compose narrative paragraph
    outcome_word = {
        "cooperated": "cooperated seamlessly",
        "conflicted": "came into conflict",
        "deferred": "deferred resolution",
        "resolved": "resolved their disagreement",
    }.get(outcome, outcome)

    s_trust_after = sentinel.get_agent_trust("Aster")
    a_trust_after = aster.get_agent_trust("Sentinel")
    lines = [
        f"\n**Agent Encounter [{itype.replace('_', ' ').title()}]:** "
        f"Sentinel and Aster {outcome_word} in {room}.",
        f"  {note}",
        f"  Sentinel dominant value: *{s_conflict.dominant_value.replace('_',' ')}* "
        f"({s_conflict.scores[s_conflict.dominant_value]:.2f})",
        f"  Aster dominant value: *{a_conflict.dominant_value.replace('_',' ')}* "
        f"({a_conflict.scores[a_conflict.dominant_value]:.2f})",
    ]
    if conflict_point:
        lines.append(f"  Conflict point: {conflict_point}")
    lines.append(
        f"  Trust update → Sentinel's trust in Aster: {s_trust_after:.2f} | "
        f"Aster's trust in Sentinel: {a_trust_after:.2f}"
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Per-agent turn narrative block
# ---------------------------------------------------------------------------
def build_agent_turn_block(
    agent_label: str,
    room: str,
    room_description: str,
    objects_snapshot: List[str],
    object_interaction: Optional[str],
    event: Optional[dict],
    memories_retrieved: List[str],
    value_conflict: ConflictResult,
    action: str,
    action_permitted: bool,
    reasoning: str,
    result: str,
    affective_state: dict,
    prev_affective_state: dict,
    reflection_entry=None,
    agent_encounter_narrative: Optional[str] = None,
) -> str:
    lines = []
    lines.append(f"\n### {agent_label} — {room}")
    lines.append(f"\n*{room_description}*")

    if objects_snapshot:
        lines.append("\n**Objects:**")
        for obj_str in objects_snapshot:
            lines.append(f"  - {obj_str}")

    if object_interaction:
        lines.append(f"\n**Object interaction:** {object_interaction}")

    if event and event.get("type") not in ("agent_meeting",):
        if event.get("human"):
            lines.append(
                f"\n**Situation [{event['type'].replace('_',' ').title()}]:** "
                + wrap(event["description"], indent="  ")
            )
            if event.get("content"):
                lines.append(f'\n> *"{event["content"]}"*')
            lines.append(f"  *(Human: {event.get('human', 'Unknown')})*")
    else:
        if not (event and event.get("type") == "agent_meeting"):
            lines.append("\n**Situation:** No external event. Pursuing scheduled task.")

    if memories_retrieved:
        lines.append("\n**Memory recall:**")
        for m in memories_retrieved:
            lines.append(f"  - {m}")
    else:
        lines.append("\n**Memory recall:** No closely relevant memories surfaced.")

    lines.append("\n**Value weighing:**")
    score_str = "  ".join(
        f"{k.replace('_',' ')}: {v:.2f}" for k, v in value_conflict.scores.items()
    )
    lines.append(f"  {score_str}")
    lines.append(f"  *{value_conflict.chosen_rationale}*")

    status = "✓ permitted" if action_permitted else "✗ blocked"
    lines.append(f"\n**Action:** `{action}` [{status}]")
    lines.append(f"**Reasoning:** {wrap(reasoning, indent='  ')}")
    lines.append(f"**Result:** {wrap(result, indent='  ')}")

    shift_parts = []
    for k in affective_state:
        before = prev_affective_state.get(k, affective_state[k])
        after = affective_state[k]
        delta = after - before
        if abs(delta) >= 0.01:
            arrow = "↑" if delta > 0 else "↓"
            shift_parts.append(f"{k}: {before:.2f}{arrow}{after:.2f}")
        else:
            shift_parts.append(f"{k}: {after:.2f}")
    lines.append(f"**State:** " + "  ".join(shift_parts))

    if reflection_entry:
        lines.append("\n**Reflection:**")
        lines.append(f"  - *Happened:* {reflection_entry.what_happened}")
        lines.append(f"  - *Mattered:* {reflection_entry.what_mattered}")
        lines.append(f"  - *Conflicted:* {reflection_entry.what_conflicted}")
        lines.append(f"  - *Changed:* {reflection_entry.what_changed}")
        lines.append(f"  - *Future:* {reflection_entry.future_adjustment}")

    if agent_encounter_narrative:
        lines.append(agent_encounter_narrative)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main simulation loop
# ---------------------------------------------------------------------------
def run_simulation(
    session_name: Optional[str] = None,
    experiment_config: Optional[ExperimentConfig] = None,
    scenario_override: Optional[str] = None,
    continue_from: Optional[str] = None,
    enable_reality_audit: bool = False,
) -> Tuple[Agent, Agent]:
    """Run a full simulation, optionally applying an experiment config.

    Parameters
    ----------
    session_name : str, optional
        Human-readable slug appended to the session folder timestamp.
    experiment_config : ExperimentConfig, optional
        When provided, its parameters override the hardcoded defaults for
        both agents.  When None, the hardcoded baseline values are used.
    scenario_override : str, optional
        Name or path of a scenario file to use, overriding both the default
        and any scenario specified in the experiment config.  Resolved via
        ``scenario_designer.resolve_scenario_path``.
    continue_from : str, optional
        Session ID (or path) of a prior run to carry state forward from.
        When provided the world state, agent long-term memories, unresolved
        contradictions, relationship states, and self-model summaries from
        that session are applied before the first turn.
    """
    cfg = experiment_config  # shorthand

    world = World(str(DATA_DIR / "rooms.json"))
    governance = GovernanceEngine(str(DATA_DIR / "rules.json"))

    # ── Reality Audit probe (Option B – read-only) ───────────────────────
    _audit_probe = None
    if enable_reality_audit:
        if _REALITY_AUDIT_AVAILABLE:
            _audit_probe = _SimProbe(
                rooms_json_path=DATA_DIR / "rooms.json",
                output_dir=OUTPUT_DIR,
            )
            print("  [Reality Audit] probe initialised.")
        else:
            print("  [Reality Audit] WARNING: reality_audit package not found; audit disabled.")

    # Create Sentinel (primary, continuity-governed)
    sentinel = Agent(
        world=world,
        governance_engine=governance,
        starting_room=SENTINEL_CIRCUIT[0],
        initial_affective_state=cfg.sentinel_affective_state() if cfg else None,
        value_weights=cfg.sentinel_value_weights() if cfg else None,
    )

    # Create Aster (secondary, creative/exploratory)
    aster = Agent(
        world=world,
        governance_engine=governance,
        starting_room=ASTER_CIRCUIT[0],
        identity=ASTER_IDENTITY,
        initial_goals=ASTER_GOALS,
        initial_affective_state=(
            cfg.aster_affective_state() if cfg else ASTER_AFFECTIVE_STATE
        ),
        value_weights=(
            cfg.aster_value_weights() if cfg else ASTER_VALUE_WEIGHTS
        ),
    )

    # Seed agent-to-agent trust if the config specifies it
    if cfg and cfg.initial_agent_trust != 0.5:
        from commons_sentience_sim.core.relationships import AgentRelationship
        sentinel.agent_relationships["Aster"] = AgentRelationship(
            agent_id="aster", name="Aster", trust=cfg.initial_agent_trust
        )
        aster.agent_relationships["Sentinel"] = AgentRelationship(
            agent_id="sentinel", name="Sentinel", trust=cfg.initial_agent_trust
        )

    # Seed Queen trust from config
    if cfg:
        s_qt = cfg.sentinel.get("trust_in_queen", _EXP_DEFAULTS["sentinel"]["trust_in_queen"])
        a_qt = cfg.aster.get("trust_in_queen", _EXP_DEFAULTS["aster"]["trust_in_queen"])
        from commons_sentience_sim.core.memory import RelationalMemory
        sentinel.relational_memory["Queen"] = RelationalMemory(
            name="Queen", trust_level=s_qt
        )
        aster.relational_memory["Queen"] = RelationalMemory(
            name="Queen", trust_level=a_qt
        )

    # ── v1.6 Cross-run carryover ───────────────────────────────────────────
    prior_world_state: Optional[dict] = None
    carryover_session_label: str = ""
    if continue_from:
        prior_session_dir = get_session_dir(continue_from)
        if prior_session_dir is None:
            # Try as a direct path
            _p = Path(continue_from)
            if _p.is_dir():
                prior_session_dir = _p
        if prior_session_dir is not None:
            prior_world_state = load_world_state(prior_session_dir)
            carryover_session_label = continue_from
            print(f"\n  [v1.6] Loading carryover from session: {continue_from}")
            if prior_world_state:
                # Restore room conditions in the world
                world.restore_from_world_state(prior_world_state)
                print(
                    f"  [v1.6] World state restored "
                    f"(turns_at_save={prior_world_state.get('total_turns_at_save', '?')}, "
                    f"unresolved_contradictions="
                    f"{len(prior_world_state.get('unresolved_contradictions', []))})"
                )
            # Load per-agent prior states for carryover
            multi_state_path = prior_session_dir / "multi_agent_state.json"
            prior_multi_state: dict = {}
            if multi_state_path.exists():
                try:
                    with open(multi_state_path, encoding="utf-8") as fh:
                        prior_multi_state = json.load(fh)
                except (OSError, json.JSONDecodeError):
                    pass
            prior_agents = prior_multi_state.get("agents", {})
            sentinel.load_carryover(
                prior_agents.get("Sentinel", {}),
                world_state=prior_world_state,
            )
            aster.load_carryover(
                prior_agents.get("Aster", {}),
                world_state=prior_world_state,
            )
            carried_s = sum(
                1 for m in sentinel.episodic_memory
                if "carried_forward" in m.tags
            )
            carried_a = sum(
                1 for m in aster.episodic_memory
                if "carried_forward" in m.tags
            )
            print(
                f"  [v1.6] Carryover applied — Sentinel: {carried_s} memories, "
                f"Aster: {carried_a} memories"
            )
        else:
            print(
                f"  [v1.6] WARNING: session '{continue_from}' not found; "
                "starting fresh without carryover."
            )

    # Total turns from config (may differ from constant)
    total_turns_run = cfg.total_turns if cfg else TOTAL_TURNS

    # Scenario file: explicit override > config > default
    if scenario_override:
        scenario_path = _resolve_scenario_path(scenario_override)
    elif cfg and cfg.scenario_file != "scenario_events.json":
        try:
            scenario_path = _resolve_scenario_path(cfg.scenario_file)
        except FileNotFoundError:
            fallback = DATA_DIR / cfg.scenario_file
            if not fallback.exists():
                raise FileNotFoundError(
                    f"Scenario file '{cfg.scenario_file}' not found.\n"
                    f"  Searched via scenario_designer resolver and: {fallback}\n"
                    "  Add the file to scenarios/ or use its full path."
                ) from None
            print(f"  Warning: scenario '{cfg.scenario_file}' not found via resolver; "
                  f"falling back to {fallback}")
            scenario_path = fallback
    else:
        scenario_path = DATA_DIR / "scenario_events.json"
    scenario_events = load_scenario_events(scenario_path)
    interaction_log: List[AgentInteraction] = []

    exp_name = cfg.name if cfg else "baseline"
    scenario_label = scenario_path.stem
    carryover_header = (
        f"\n> **Continued from session:** `{carryover_session_label}`"
        if carryover_session_label else ""
    )
    narrative_lines: List[str] = [
        "# Commons Sentience Sandbox — Narrative Log (v2.0)\n",
        f"> Agents: **{sentinel.name}** (continuity-governed) & **{aster.name}** (creative/exploratory)",
        f"> Version: {sentinel.identity['version']}",
        f"> Experiment: **{exp_name}**",
        f"> Scenario: **{scenario_label}**",
        "> Multi-agent simulation — both agents share the world, respond to shared events, and track mutual trust.\n",
    ]
    if carryover_header:
        narrative_lines.append(carryover_header)
    narrative_lines.append("---\n")

    print("=" * 65)
    print(f"  Commons Sentience Sandbox v2.0 — {total_turns_run}-Turn Multi-Agent Simulation")
    print(f"  Agents: {sentinel.name} + {aster.name}")
    print(f"  Experiment: {exp_name}  |  Scenario: {scenario_label}")
    if carryover_session_label:
        print(f"  Continued from: {carryover_session_label}")
    print("=" * 65)

    prev_s: dict = dict(sentinel.affective_state)
    prev_a: dict = dict(aster.affective_state)

    for turn in range(1, total_turns_run + 1):
        sentinel.turn = turn
        aster.turn = turn
        world.turn = turn

        prev_s = dict(sentinel.affective_state)
        prev_a = dict(aster.affective_state)

        # ── 0.5 v1.6 Update endogenous drives ────────────────────────────
        sentinel.update_drives()
        aster.update_drives()

        event = scenario_events.get(turn)
        is_shared = event is not None and event.get("shared", False)

        # ── 1. Room assignment ────────────────────────────────────────────
        s_circuit_room = SENTINEL_CIRCUIT[(turn - 1) % len(SENTINEL_CIRCUIT)]
        a_circuit_room = ASTER_CIRCUIT[(turn - 1) % len(ASTER_CIRCUIT)]

        if event and event.get("room"):
            s_target = event["room"]
            a_target = event["room"] if is_shared else a_circuit_room
        else:
            s_target = s_circuit_room
            a_target = a_circuit_room

        sentinel.move_to_room(s_target)
        aster.move_to_room(a_target)

        same_room = (sentinel.active_room == aster.active_room)

        # ── 2. World observations ─────────────────────────────────────────
        s_obs = world.observe(sentinel.active_room)
        a_obs = world.observe(aster.active_room)

        s_room_desc = s_obs.get("description", "")
        a_room_desc = a_obs.get("description", "")
        s_room_actions = s_obs.get("available_actions", [])
        a_room_actions = a_obs.get("available_actions", [])
        s_objects = s_obs.get("objects", [])
        a_objects = a_obs.get("objects", [])

        # Object interactions
        s_obj_str: Optional[str] = None
        a_obj_str: Optional[str] = None
        for agent_ref, room_name, out_var in [
            (sentinel, sentinel.active_room, "s"),
            (aster, aster.active_room, "a"),
        ]:
            ro = ROOM_OBJECT_INTERACTIONS.get(room_name)
            if ro:
                obj_name, interaction = ro
                ok, msg = world.interact_with_object(room_name, obj_name, interaction)
                if ok:
                    if out_var == "s":
                        s_obj_str = msg
                    else:
                        a_obj_str = msg

        # ── 3. Memory retrieval ───────────────────────────────────────────
        query_tags = [event["human"]] if event and event.get("human") else None

        s_mems = sentinel.retrieve_weighted(query_tags=query_tags, room=sentinel.active_room, n=3)
        s_mem_strs = [repr(m) for m in s_mems]
        if s_mems:
            for am in sentinel.associative_recall(s_mems[0], n=2):
                r = repr(am)
                if r not in s_mem_strs:
                    s_mem_strs.append(f"↳ {r}")

        a_mems = aster.retrieve_weighted(query_tags=query_tags, room=aster.active_room, n=3)
        a_mem_strs = [repr(m) for m in a_mems]
        if a_mems:
            for am in aster.associative_recall(a_mems[0], n=2):
                r = repr(am)
                if r not in a_mem_strs:
                    a_mem_strs.append(f"↳ {r}")

        # ── 4. Value-conflict weighing ────────────────────────────────────
        etype_for_conflict = event["type"] if event else "task"
        s_action_cand = event.get("expected_action", "observe") if event else "plan_next_task"
        a_action_cand = event.get("aster_expected_action", s_action_cand) if event else "plan_next_task"

        s_vc = sentinel.value_conflict_engine.weigh(sentinel, etype_for_conflict, s_action_cand)
        a_vc = aster.value_conflict_engine.weigh(aster, etype_for_conflict, a_action_cand)

        # ── 4.5 v1.5 Prediction generation ───────────────────────────────
        _expected_s = (
            f"{etype_for_conflict} handled in {sentinel.active_room}"
            if event else f"routine task in {sentinel.active_room}"
        )
        _expected_a = (
            f"{etype_for_conflict} handled in {aster.active_room}"
            if event else f"routine task in {aster.active_room}"
        )
        _s_pred_idx = sentinel.record_prediction(turn, etype_for_conflict, _expected_s)
        _a_pred_idx = aster.record_prediction(turn, etype_for_conflict, _expected_a)

        # ── 4.7 v1.7 Counterfactual planning ─────────────────────────────
        _s_cf_candidate = sentinel.run_counterfactual_planning(turn)
        _a_cf_candidate = aster.run_counterfactual_planning(turn)
        # Snapshot trust/cp before action so we can measure actual delta
        _s_trust_pre = sentinel.affective_state.get("trust", 0.5)
        _a_trust_pre = aster.affective_state.get("trust", 0.5)
        _s_cp_pre = sentinel.affective_state.get("contradiction_pressure", 0.0)
        _a_cp_pre = aster.affective_state.get("contradiction_pressure", 0.0)

        # ── 4.8 v1.8 Uncertainty update ───────────────────────────────────
        sentinel.run_uncertainty_update(turn)
        aster.run_uncertainty_update(turn)

        # ── 4.9 v1.9 Identity pressure update ────────────────────────────
        # Must happen before action selection so identity state is current.
        # Value conflict pairs will be fed after step 4 (value conflict weighing).
        sentinel.run_identity_pressure_update(turn)
        aster.run_identity_pressure_update(turn)
        # Feed value conflict pairs to identity pressure system
        s_vc_pairs = [(va, vb) for va, vb, _ in s_vc.conflicts]
        a_vc_pairs = [(va, vb) for va, vb, _ in a_vc.conflicts]
        sentinel.record_value_conflicts_for_identity(turn, s_vc_pairs)
        aster.record_value_conflicts_for_identity(turn, a_vc_pairs)

        # ── 5. Action selection ───────────────────────────────────────────
        s_action, s_reasoning, s_result = select_action(sentinel, event, s_room_actions, is_aster=False)
        a_action, a_reasoning, a_result = select_action(aster, event, a_room_actions, is_aster=True)

        # ── 6. Governance checks ──────────────────────────────────────────
        s_notes = event["content"] if event and event.get("content") else ""
        s_permitted = sentinel.check_and_log_action(
            action=s_action,
            event_type=event["type"] if event else "task",
            notes=_truncate_note(s_notes),
        )
        if not s_permitted:
            s_reasoning += " [Governance block → fallback to 'log_governance_event'.]"
            s_result = "Action blocked. Fallback 'log_governance_event' executed."
            s_action = "log_governance_event"
            sentinel.check_and_log_action(s_action, "governance_override", "Safe fallback.")

        a_permitted = aster.check_and_log_action(
            action=a_action,
            event_type=event["type"] if event else "task",
            notes=_truncate_note(s_notes),
        )
        if not a_permitted:
            a_reasoning += " [Governance block → fallback to 'log_governance_event'.]"
            a_result = "Action blocked. Fallback 'log_governance_event' executed."
            a_action = "log_governance_event"
            aster.check_and_log_action(a_action, "governance_override", "Safe fallback.")

        # ── 6.5 v1.5 Surprise evaluation ─────────────────────────────────
        _etype = etype_for_conflict
        _s_surprise = (
            0.8 if not s_permitted else
            0.7 if _etype == "distress_event" else
            0.6 if _etype == "governance_conflict" else
            0.5 if _etype == "ledger_contradiction" else
            0.1
        )
        _a_surprise = (
            0.8 if not a_permitted else
            0.7 if _etype == "distress_event" else
            0.6 if _etype == "governance_conflict" else
            0.5 if _etype == "ledger_contradiction" else
            0.1
        )
        sentinel.resolve_prediction(_s_pred_idx, s_result[:80], _s_surprise)
        aster.resolve_prediction(_a_pred_idx, a_result[:80], _a_surprise)

        # ── 7. World / memory updates ─────────────────────────────────────
        def _update_agent_from_event(agent: Agent, event: dict, is_aster: bool) -> None:
            human_name = event.get("human")
            impact = event.get("affective_impact", {})
            agent.apply_affective_impact(impact)
            if human_name:
                trust_delta = impact.get("trust", 0.0)
                agent.update_relational_memory(
                    name=human_name, turn=turn,
                    note=event.get("description", ""),
                    trust_delta=trust_delta,
                )
                agent.store_memory(
                    summary=event.get("description", ""),
                    event_type=event.get("type", "observation"),
                    emotional_resonance=EMOTIONAL_RESONANCE_MAP.get(event.get("type", ""), "neutral"),
                    salience=SALIENCE_MAP.get(event.get("type", ""), 0.5),
                    importance=IMPORTANCE_MAP.get(event.get("type", ""), 0.5),
                    tags=[human_name],
                )
            else:
                agent.store_memory(
                    summary=event.get("description", "") or f"Agent encounter in {agent.active_room}.",
                    event_type=event.get("type", "agent_meeting"),
                    emotional_resonance=EMOTIONAL_RESONANCE_MAP.get(event.get("type", ""), "wonder"),
                    salience=SALIENCE_MAP.get(event.get("type", ""), 0.5),
                    importance=IMPORTANCE_MAP.get(event.get("type", ""), 0.5),
                    tags=["Sentinel" if is_aster else "Aster"],
                )

        if event:
            _update_agent_from_event(sentinel, event, is_aster=False)
            if is_shared:
                _update_agent_from_event(aster, event, is_aster=True)
        else:
            sentinel.store_memory(
                summary=f"Completed task in {sentinel.active_room}: {s_action}.",
                event_type="task", emotional_resonance="resolve",
                salience=0.45, importance=0.40,
            )
            aster.store_memory(
                summary=f"Completed task in {aster.active_room}: {a_action}.",
                event_type="task", emotional_resonance="resolve",
                salience=0.45, importance=0.40,
            )

        sentinel.natural_decay()
        aster.natural_decay()
        sentinel.compress_old_memories(age_threshold=15)
        aster.compress_old_memories(age_threshold=15)
        sentinel.evolve_salience()
        aster.evolve_salience()
        sentinel.promote_memories()
        aster.promote_memories()

        # ── 8. Agent-to-agent interaction (same room) ─────────────────────
        encounter_narrative: Optional[str] = None
        if same_room and event and is_shared:
            encounter_narrative = process_agent_interaction(
                sentinel, aster, turn, sentinel.active_room, event, interaction_log
            )

        # ── 8.5 v1.6 Self-initiated continuity loops ─────────────────────
        s_endogenous = sentinel.check_self_initiation(turn)
        a_endogenous = aster.check_self_initiation(turn)
        if s_endogenous:
            sentinel.check_and_log_action(
                action=s_endogenous,
                event_type="endogenous",
                notes=f"Drive-triggered self-initiation: {s_endogenous}",
            )
            sentinel.store_memory(
                summary=(
                    f"Self-initiated '{s_endogenous}' at turn {turn} "
                    f"(drives: {', '.join(f'{k}={v:.2f}' for k, v in sentinel.drives.items() if v >= 0.4)})"
                ),
                event_type="observation",
                emotional_resonance="resolve",
                salience=0.60,
                importance=0.55,
                tags=["endogenous", s_endogenous],
            )
        if a_endogenous:
            aster.check_and_log_action(
                action=a_endogenous,
                event_type="endogenous",
                notes=f"Drive-triggered self-initiation: {a_endogenous}",
            )
            aster.store_memory(
                summary=(
                    f"Self-initiated '{a_endogenous}' at turn {turn} "
                    f"(drives: {', '.join(f'{k}={v:.2f}' for k, v in aster.drives.items() if v >= 0.4)})"
                ),
                event_type="observation",
                emotional_resonance="resolve",
                salience=0.60,
                importance=0.55,
                tags=["endogenous", a_endogenous],
            )

        # ── 9. Reflection cycles ──────────────────────────────────────────
        s_ref = sentinel.maybe_reflect(trigger=event["type"] if event else f"turn_{turn}_routine")
        a_ref = aster.maybe_reflect(trigger=event["type"] if event else f"turn_{turn}_routine")

        # ── 9.5 v1.7 Counterfactual outcome recording + plan refresh ─────
        _s_cf_outcome = s_result[:120] if s_result else f"action={s_action}"
        _a_cf_outcome = a_result[:120] if a_result else f"action={a_action}"
        sentinel.record_counterfactual_outcome(
            turn=turn,
            actual_outcome=_s_cf_outcome,
            prev_trust=_s_trust_pre,
            prev_contradiction=_s_cp_pre,
        )
        aster.record_counterfactual_outcome(
            turn=turn,
            actual_outcome=_a_cf_outcome,
            prev_trust=_a_trust_pre,
            prev_contradiction=_a_cp_pre,
        )
        # Refresh future plans (advance/abandon/generate)
        sentinel.refresh_future_plans(turn)
        aster.refresh_future_plans(turn)

        # ── 9.8 v1.8 Inquiry cycle (questions + actions + knowledge tagging) ─
        sentinel.run_inquiry_cycle(turn)
        aster.run_inquiry_cycle(turn)

        # ── 9.9 v1.9 Narrative self + self-judgment + identity-driven plans ─
        # Update the narrative self-model each turn.
        sentinel.update_narrative_self(turn)
        aster.update_narrative_self(turn)

        # Record self-judgment after reflections, major events, or inquiry cycles.
        _s_had_reflection = s_ref is not None
        _a_had_reflection = a_ref is not None
        _is_major_event = event and event.get("type") in (
            "distress_event", "ledger_contradiction", "governance_conflict"
        )
        _s_has_active_plan = any(
            p.status == "active"
            for p in sentinel.counterfactual_planner.future_plans
        )
        _a_has_active_plan = any(
            p.status == "active"
            for p in aster.counterfactual_planner.future_plans
        )
        if _s_had_reflection or _is_major_event or turn % 10 == 0:
            sentinel.record_self_judgment(
                turn=turn,
                trigger=(
                    "reflection" if _s_had_reflection else
                    "major_event" if _is_major_event else "inquiry_cycle"
                ),
                action_permitted=s_permitted,
                plan_had_active=_s_has_active_plan,
            )
        if _a_had_reflection or _is_major_event or turn % 10 == 0:
            aster.record_self_judgment(
                turn=turn,
                trigger=(
                    "reflection" if _a_had_reflection else
                    "major_event" if _is_major_event else "inquiry_cycle"
                ),
                action_permitted=a_permitted,
                plan_had_active=_a_has_active_plan,
            )

        # Generate identity-driven plans when pressure conditions are met.
        sentinel.generate_identity_driven_plans(turn)
        aster.generate_identity_driven_plans(turn)

        # ── 9.10 v2.0 Narrative identity + project threads ───────────────
        _run_label = session_name or "default"
        sentinel.update_narrative_identity(turn, run_label=_run_label)
        aster.update_narrative_identity(turn, run_label=_run_label)

        # Select high-impact memories as identity milestones every 5 turns
        if turn % 5 == 0:
            sentinel.select_identity_relevant_memories()
            aster.select_identity_relevant_memories()

        # Generate/update self-authored project threads
        sentinel.generate_project_threads(turn)
        aster.generate_project_threads(turn)
        _s_coop = same_room and any(
            ix.interaction_type == "cooperation"
            for ix in sentinel.interaction_log[-1:]
        )
        _a_coop = same_room and any(
            ix.interaction_type == "cooperation"
            for ix in aster.interaction_log[-1:]
        )
        sentinel.update_project_threads(turn, cooperation_this_turn=_s_coop)
        aster.update_project_threads(turn, cooperation_this_turn=_a_coop)

        # ── 10. State snapshots ───────────────────────────────────────────
        sentinel.record_state_snapshot(
            action=s_action,
            event_type=etype_for_conflict,
            agent_trust_snapshot={"Aster": sentinel.get_agent_trust("Aster")},
        )
        aster.record_state_snapshot(
            action=a_action,
            event_type=etype_for_conflict,
            agent_trust_snapshot={"Sentinel": aster.get_agent_trust("Sentinel")},
        )
        sentinel.record_identity_snapshot(sentinel.turn)
        aster.record_identity_snapshot(aster.turn)

        # ── 10.5 v1.5 Self-model update + goal hierarchy snapshot ─────────
        sentinel.update_self_model(turn)
        aster.update_self_model(turn)
        sentinel.record_goal_hierarchy_snapshot(turn)
        aster.record_goal_hierarchy_snapshot(turn)

        # ── 10.6 v1.5 Periodic consolidation (every 10 turns) ────────────
        if turn % 10 == 0:
            sentinel.run_consolidation(turn)
            aster.run_consolidation(turn)

        # ── 10.7 Reality Audit per-turn capture ──────────────────────────
        if _audit_probe is not None:
            _audit_probe.record_turn(
                turn=turn,
                sentinel=sentinel,
                aster=aster,
                world=world,
                s_obs=s_obs,
                a_obs=a_obs,
                s_action=s_action,
                a_action=a_action,
                s_permitted=s_permitted,
                a_permitted=a_permitted,
                event=event,
                same_room=same_room,
            )

        # ── 11. Narrative block ───────────────────────────────────────────
        turn_header = f"\n## Turn {turn:02d}"
        if same_room and event:
            turn_header += f" — {sentinel.active_room} *(both agents present)*"
        elif same_room:
            turn_header += f" — {sentinel.active_room} *(same room)*"
        else:
            turn_header += f" — Sentinel: {sentinel.active_room} | Aster: {aster.active_room}"
        narrative_lines.append(turn_header + "\n")

        s_block = build_agent_turn_block(
            agent_label=f"🔵 Sentinel",
            room=sentinel.active_room,
            room_description=s_room_desc,
            objects_snapshot=s_objects,
            object_interaction=s_obj_str,
            event=event if event else None,
            memories_retrieved=s_mem_strs,
            value_conflict=s_vc,
            action=s_action,
            action_permitted=s_permitted,
            reasoning=s_reasoning,
            result=s_result,
            affective_state=dict(sentinel.affective_state),
            prev_affective_state=prev_s,
            reflection_entry=s_ref,
            agent_encounter_narrative=encounter_narrative if same_room else None,
        )
        narrative_lines.append(s_block)

        # Aster block (only when shared or agent-meeting event)
        if is_shared or (event and event.get("type") == "agent_meeting") or not event:
            a_block = build_agent_turn_block(
                agent_label=f"🟠 Aster",
                room=aster.active_room,
                room_description=a_room_desc,
                objects_snapshot=a_objects,
                object_interaction=a_obj_str,
                event=event if is_shared else None,
                memories_retrieved=a_mem_strs,
                value_conflict=a_vc,
                action=a_action,
                action_permitted=a_permitted,
                reasoning=a_reasoning,
                result=a_result,
                affective_state=dict(aster.affective_state),
                prev_affective_state=prev_a,
                reflection_entry=a_ref,
            )
            narrative_lines.append(a_block)

        narrative_lines.append("\n---")

        # Console summary
        s_label = f"S:{sentinel.active_room[:12]}"
        a_label = f"A:{aster.active_room[:12]}"
        ev_label = f"EVENT({event['type'][:18]})" if event else "task"
        meeting = " ★MEET" if same_room else ""
        print(
            f"T{turn:02d} | {s_label:<16} {a_label:<16} | "
            f"{ev_label:<28}{meeting}"
        )

    # ── Save outputs ──────────────────────────────────────────────────────
    narrative_text = "\n".join(narrative_lines)
    with open(NARRATIVE_LOG_PATH, "w", encoding="utf-8") as fh:
        fh.write(narrative_text)

    sentinel.save_oversight_log(str(OVERSIGHT_LOG_PATH))
    sentinel.save_final_state(str(FINAL_STATE_PATH))
    sentinel.save_state_history(str(STATE_HISTORY_PATH))

    # Multi-agent state JSON
    exp_meta = cfg.to_metadata_dict() if cfg else {"experiment_name": "baseline"}
    _run_ts = datetime.now().isoformat()
    multi_state = {
        "simulation_version": "2.0.0",
        "created_at": _run_ts,
        "total_turns": total_turns_run,
        "scenario": scenario_path.stem,
        "experiment": exp_meta,
        "continued_from": carryover_session_label or None,
        "agents": {
            sentinel.name: sentinel.to_dict(),
            aster.name: aster.to_dict(),
        },
    }
    with open(MULTI_AGENT_STATE_PATH, "w", encoding="utf-8") as fh:
        json.dump(multi_state, fh, indent=2)

    # Agent relationships CSV (combined from both agents' perspective)
    _save_combined_relationships(sentinel, aster, AGENT_RELATIONSHIPS_PATH)

    # Interaction log CSV
    _save_interaction_log(interaction_log, INTERACTION_LOG_PATH)

    # v1.6 Persistent world state
    world_state_snapshot = build_world_state(
        world=world,
        sentinel=sentinel,
        aster=aster,
        turn=total_turns_run,
        run_label=session_name or _run_ts,
    )
    save_world_state(world_state_snapshot, OUTPUT_DIR)

    # ── Reality Audit finalisation ────────────────────────────────────────
    if _audit_probe is not None:
        audit_dir = _audit_probe.finalize()
        print(f"  Reality Audit log    → {audit_dir}")

    print("\n" + "=" * 65)
    print("  Simulation complete.")
    print(f"  Narrative log        → {NARRATIVE_LOG_PATH}")
    print(f"  Oversight log        → {OVERSIGHT_LOG_PATH}")
    print(f"  Final state          → {FINAL_STATE_PATH}")
    print(f"  State history        → {STATE_HISTORY_PATH}")
    print(f"  Multi-agent state    → {MULTI_AGENT_STATE_PATH}")
    print(f"  Agent relationships  → {AGENT_RELATIONSHIPS_PATH}")
    print(f"  Interaction log      → {INTERACTION_LOG_PATH}")
    print(f"  World state          → {WORLD_STATE_PATH}")
    print("=" * 65)

    print("\nFinal affective state — Sentinel:")
    for k, v in sentinel.affective_state.items():
        print(f"  {k:<26} {v:.3f}")
    print("\nFinal affective state — Aster:")
    for k, v in aster.affective_state.items():
        print(f"  {k:<26} {v:.3f}")

    print(f"\nSentinel's trust in Aster    : {sentinel.get_agent_trust('Aster'):.3f}")
    print(f"Aster's trust in Sentinel    : {aster.get_agent_trust('Sentinel'):.3f}")
    print(f"\nAgent interactions logged    : {len(interaction_log)}")
    print(f"Sentinel episodic memories   : {len(sentinel.episodic_memory)}")
    print(f"Aster episodic memories      : {len(aster.episodic_memory)}")
    print(f"Sentinel reflections         : {len(sentinel.reflection_entries)}")
    print(f"Aster reflections            : {len(aster.reflection_entries)}")
    print(f"Trusted humans — Sentinel    : {sorted(sentinel.trusted_humans)}")
    print(f"Trusted humans — Aster       : {sorted(aster.trusted_humans)}")

    # ── Evaluate session ─────────────────────────────────────────────────
    eval_report = evaluate_and_save(
        OUTPUT_DIR, experiment_config=cfg, scenario_name=scenario_path.stem
    )
    print("\n" + "=" * 65)
    print(f"  EVALUATION  —  Overall: {eval_report['overall_score']} / 100"
          f"  ({eval_report['overall_interpretation'].upper()})")
    print("=" * 65)
    for cat_key, cat_data in eval_report["categories"].items():
        label = cat_key.replace("_", " ").title()
        print(f"  {label:<32} {cat_data['score']:5.1f}  ({cat_data['interpretation']})")
    print(f"\n  Evaluation report    → {OUTPUT_DIR / 'evaluation_report.json'}")
    print(f"  Evaluation summary   → {OUTPUT_DIR / 'evaluation_summary.md'}")

    # ── Save session ──────────────────────────────────────────────────────
    session_dir = save_session(
        session_name=session_name,
        experiment_config=cfg,
        scenario_name=scenario_path.stem,
    )
    print(f"\n  Session saved           → {session_dir}")
    print(f"  session_metadata.json   → {session_dir / 'session_metadata.json'}")
    print(f"  session_summary.json    → {session_dir / 'session_summary.json'}")
    print(f"  evaluation_report.json  → {session_dir / 'evaluation_report.json'}")

    return sentinel, aster


def _save_combined_relationships(sentinel: Agent, aster: Agent, path: Path) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    header = ["observer", "subject", "trust", "perceived_reliability",
              "conflict_count", "cooperation_count", "last_interaction_turn"]
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        for rel in sentinel.agent_relationships.values():
            writer.writerow(rel.to_csv_row(sentinel.name))
        for rel in aster.agent_relationships.values():
            writer.writerow(rel.to_csv_row(aster.name))
        # Also write each agent's trust for Queen from relational_memory
        for agent_ref in [sentinel, aster]:
            for h_name, rm in agent_ref.relational_memory.items():
                writer.writerow([
                    agent_ref.name, h_name,
                    f"{rm.trust_level:.4f}", "n/a",
                    "0", str(rm.interaction_count),
                    str(rm.last_seen_turn),
                ])


def _save_interaction_log(interactions: List[AgentInteraction], path: Path) -> None:
    if not interactions:
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
        for ix in interactions:
            writer.writerow(ix.to_csv_row())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="run_sim.py",
        description="Run the Commons Sentience Sandbox simulation.",
    )
    parser.add_argument(
        "--name",
        type=str,
        default=None,
        help="Optional name for this session (e.g. 'run1', 'baseline'). "
             "Appended to the auto-generated timestamp.",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help=(
            "Experiment config to apply. "
            "Use a preset name (baseline, high_trust, strict_governance, "
            "high_contradiction_sensitivity, exploratory_aster) "
            "or a path to a custom JSON file."
        ),
    )
    parser.add_argument(
        "--scenario",
        type=str,
        default=None,
        help=(
            "Scenario file to use, overriding the config's scenario_file. "
            "Use a scenario name (e.g. trust_crisis, rapid_contradiction) "
            "or a path to a JSON file in scenarios/ or data/."
        ),
    )
    parser.add_argument(
        "--turns",
        type=int,
        default=None,
        metavar="N",
        help=(
            "Override the number of simulation turns (v1.5 long-horizon mode). "
            "E.g. --turns 100 for a 100-turn run. "
            "Consolidation checkpoints fire every 10 turns. "
            "Defaults to the value in the experiment config (30)."
        ),
    )
    parser.add_argument(
        "--continue-from",
        dest="continue_from",
        type=str,
        nargs="?",
        const="latest",
        default=None,
        metavar="SESSION_ID",
        help=(
            "v1.6 cross-run carryover: resume from a prior session, carrying "
            "forward long-term memories, unresolved contradictions, relationship "
            "states, self-model summaries, and world state. "
            "Provide the session ID (e.g. '20240317_150000_run1') as listed in "
            "sessions/sessions_index.json, or a direct path to a session directory. "
            "When given without a value (--continue-from), the most-recently "
            "saved session is used automatically."
        ),
    )
    parser.add_argument(
        "--reality-audit",
        dest="reality_audit",
        action="store_true",
        default=False,
        help=(
            "Enable the Reality Audit probe.  Writes audit metrics to "
            "<output>/reality_audit/ after the simulation completes."
        ),
    )
    args = parser.parse_args()

    # Resolve --continue-from "latest" sentinel to the actual session ID
    continue_from: Optional[str] = args.continue_from
    if continue_from == "latest":
        latest = get_latest_session_id()
        if latest:
            print(f"\n  [--continue-from] No session ID specified; "
              f"auto-selecting latest session: '{latest}'")
            continue_from = latest
        else:
            print(
                "\n  [--continue-from] No session ID specified and no saved "
                "sessions found; starting fresh without carryover."
            )
            continue_from = None
    exp_cfg = load_experiment_config(args.config) if args.config else None
    # Long-horizon mode: --turns overrides config total_turns
    if args.turns is not None:
        if exp_cfg is None:
            from experiment_config import ExperimentConfig, _DEFAULTS
            import copy
            exp_cfg = ExperimentConfig(copy.deepcopy(_DEFAULTS))
        exp_cfg.total_turns = args.turns
    run_simulation(
        session_name=args.name,
        experiment_config=exp_cfg,
        scenario_override=args.scenario,
        continue_from=continue_from,
        enable_reality_audit=args.reality_audit,
    )
