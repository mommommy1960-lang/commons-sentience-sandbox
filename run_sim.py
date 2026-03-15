"""
run_sim.py — Entry point for the Commons Sentience Sandbox simulation.

v0.8: Adds experiment configuration system.  Each run can optionally be
      launched with a named experiment config (--config) that controls agent
      value weights, affective baselines, trust seeds, total turns, and more.
      Experiment metadata is embedded in all output files.

v0.7: Adds evaluation harness.  Each run automatically generates
      evaluation_report.json and evaluation_summary.md scoring the session
      across eight behavioural categories on a 0-100 scale.

v0.6: Adds persistent session storage.  Each run is automatically saved to
      sessions/<timestamp>_<name>/ with full output files + session_metadata.json.

v0.4: Multi-agent simulation featuring Sentinel (continuity-governed) and
      Aster (creative/exploratory).  Both agents share a world, respond to
      shared events, and track trust relationships with each other.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import textwrap
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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
from evaluation import evaluate_and_save
from experiment_config import ExperimentConfig, load_experiment_config
from session_manager import save_session

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
    "version": "0.8.0",
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
            agent.pending_contradictions.append(
                f"Ledger conflict at turn {agent.turn}: {event['content']}"
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
) -> Tuple[Agent, Agent]:
    """Run a full simulation, optionally applying an experiment config.

    Parameters
    ----------
    session_name : str, optional
        Human-readable slug appended to the session folder timestamp.
    experiment_config : ExperimentConfig, optional
        When provided, its parameters override the hardcoded defaults for
        both agents.  When None, the hardcoded baseline values are used.
    """
    cfg = experiment_config  # shorthand

    world = World(str(DATA_DIR / "rooms.json"))
    governance = GovernanceEngine(str(DATA_DIR / "rules.json"))

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
        s_qt = cfg.sentinel.get("trust_in_queen", 0.5)
        a_qt = cfg.aster.get("trust_in_queen", 0.65)
        from commons_sentience_sim.core.memory import RelationalMemory
        sentinel.relational_memory["Queen"] = RelationalMemory(
            name="Queen", trust_level=s_qt
        )
        aster.relational_memory["Queen"] = RelationalMemory(
            name="Queen", trust_level=a_qt
        )

    # Total turns from config (may differ from constant)
    total_turns_run = cfg.total_turns if cfg else TOTAL_TURNS

    # Scenario file from config
    scenario_path = DATA_DIR / (cfg.scenario_file if cfg else "scenario_events.json")
    scenario_events = load_scenario_events(scenario_path)
    interaction_log: List[AgentInteraction] = []

    exp_name = cfg.name if cfg else "baseline"
    narrative_lines: List[str] = [
        "# Commons Sentience Sandbox — Narrative Log (v0.8)\n",
        f"> Agents: **{sentinel.name}** (continuity-governed) & **{aster.name}** (creative/exploratory)",
        f"> Version: {sentinel.identity['version']}",
        f"> Experiment: **{exp_name}**",
        "> Multi-agent simulation — both agents share the world, respond to shared events, and track mutual trust.\n",
        "---\n",
    ]

    print("=" * 65)
    print(f"  Commons Sentience Sandbox v0.8 — {total_turns_run}-Turn Multi-Agent Simulation")
    print(f"  Agents: {sentinel.name} + {aster.name}")
    print(f"  Experiment: {exp_name}")
    print("=" * 65)

    prev_s: dict = dict(sentinel.affective_state)
    prev_a: dict = dict(aster.affective_state)

    for turn in range(1, total_turns_run + 1):
        sentinel.turn = turn
        aster.turn = turn
        world.turn = turn

        prev_s = dict(sentinel.affective_state)
        prev_a = dict(aster.affective_state)

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

        # ── 8. Agent-to-agent interaction (same room) ─────────────────────
        encounter_narrative: Optional[str] = None
        if same_room and event and is_shared:
            encounter_narrative = process_agent_interaction(
                sentinel, aster, turn, sentinel.active_room, event, interaction_log
            )

        # ── 9. Reflection cycles ──────────────────────────────────────────
        s_ref = sentinel.maybe_reflect(trigger=event["type"] if event else f"turn_{turn}_routine")
        a_ref = aster.maybe_reflect(trigger=event["type"] if event else f"turn_{turn}_routine")

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
    multi_state = {
        "simulation_version": "0.8.0",
        "total_turns": total_turns_run,
        "experiment": exp_meta,
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

    print("\n" + "=" * 65)
    print("  Simulation complete.")
    print(f"  Narrative log        → {NARRATIVE_LOG_PATH}")
    print(f"  Oversight log        → {OVERSIGHT_LOG_PATH}")
    print(f"  Final state          → {FINAL_STATE_PATH}")
    print(f"  State history        → {STATE_HISTORY_PATH}")
    print(f"  Multi-agent state    → {MULTI_AGENT_STATE_PATH}")
    print(f"  Agent relationships  → {AGENT_RELATIONSHIPS_PATH}")
    print(f"  Interaction log      → {INTERACTION_LOG_PATH}")
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
    eval_report = evaluate_and_save(OUTPUT_DIR, experiment_config=cfg)
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
    session_dir = save_session(session_name=session_name, experiment_config=cfg)
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
    args = parser.parse_args()
    exp_cfg = load_experiment_config(args.config) if args.config else None
    run_simulation(session_name=args.name, experiment_config=exp_cfg)
