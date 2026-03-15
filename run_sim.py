"""
run_sim.py — Entry point for the Commons Sentience Sandbox simulation.

v0.3: Adds value-conflict weighing, object interaction, weighted memory
      retrieval, richer narrative, and state_history.csv output.
      Runs a 30-turn simulation and writes all output files.
"""
from __future__ import annotations

import json
import os
import random
import sys
import textwrap
from pathlib import Path
from typing import Dict, List, Optional

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
from commons_sentience_sim.core.values import ConflictResult
from commons_sentience_sim.core.world import World

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TOTAL_TURNS = 30
NARRATIVE_LOG_PATH = OUTPUT_DIR / "narrative_log.md"
OVERSIGHT_LOG_PATH = OUTPUT_DIR / "oversight_log.csv"
FINAL_STATE_PATH = OUTPUT_DIR / "final_state.json"
STATE_HISTORY_PATH = OUTPUT_DIR / "state_history.csv"

EMOTIONAL_RESONANCE_MAP = {
    "distress_event": "grief",
    "ledger_contradiction": "ambiguity",
    "creative_collaboration": "wonder",
    "routine_interaction": "resolve",
    "governance_conflict": "resolve",
    "observation": "neutral",
    "reflection": "wonder",
    "task": "resolve",
}

SALIENCE_MAP = {
    "distress_event": 0.9,
    "ledger_contradiction": 0.85,
    "creative_collaboration": 0.8,
    "governance_conflict": 0.88,
    "routine_interaction": 0.55,
    "observation": 0.4,
    "task": 0.45,
}

IMPORTANCE_MAP = {
    "distress_event": 0.95,
    "ledger_contradiction": 0.85,
    "governance_conflict": 0.90,
    "creative_collaboration": 0.75,
    "routine_interaction": 0.55,
    "task": 0.40,
    "observation": 0.35,
}

ROOM_CIRCUIT = [
    "Operations Desk",
    "Memory Archive",
    "Reflection Chamber",
    "Social Hall",
    "Governance Vault",
]

# Object to interact with per room (deterministic for consistent narrative)
ROOM_OBJECT_INTERACTIONS: Dict[str, tuple] = {
    "Memory Archive": ("memory_shelves", "retrieve_memories"),
    "Reflection Chamber": ("reflection_mirror", "perform_reflection_cycle"),
    "Operations Desk": ("task_console", "plan_next_task"),
    "Social Hall": ("message_terminal", "receive_human_interaction"),
    "Governance Vault": ("rule_tablets", "check_rule_permissions"),
}

# Oversight log note truncation
MAX_NOTE_LENGTH = 120
TRUNCATION_SUFFIX_LENGTH = 3  # length of "..."

# ---------------------------------------------------------------------------
# Scenario event loader
# ---------------------------------------------------------------------------
def load_scenario_events(path: Path) -> Dict[int, dict]:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return {ev["turn"]: ev for ev in data.get("events", [])}


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def wrap(text: str, width: int = 80, indent: str = "") -> str:
    return textwrap.fill(text, width=width, subsequent_indent=indent)


def build_narrative_turn(
    turn: int,
    room: str,
    room_description: str,
    objects_snapshot: List[str],
    object_interaction: Optional[str],
    event: Optional[dict],
    memories_retrieved: list,
    value_conflict: ConflictResult,
    action: str,
    action_permitted: bool,
    reasoning: str,
    result: str,
    affective_state: dict,
    prev_affective_state: dict,
    reflection_entry,
) -> str:
    lines: List[str] = []
    lines.append(f"\n## Turn {turn:02d} — {room}\n")

    # Room + observed situation
    lines.append(f"**Location:** {room}")
    lines.append(f"\n*{room_description}*")

    if objects_snapshot:
        lines.append("\n**Objects observed:**")
        for obj_str in objects_snapshot:
            lines.append(f"  - {obj_str}")

    if object_interaction:
        lines.append(f"\n**Object interaction:** {object_interaction}")

    # Event / situation
    if event:
        lines.append(
            f"\n**Situation [{event['type'].replace('_', ' ').title()}]:** "
            + wrap(event["description"], indent="  ")
        )
        if event.get("content"):
            lines.append(f'\n> *"{event["content"]}"*')
        lines.append(f"  *(Human: {event.get('human', 'Unknown')})*")
    else:
        lines.append("\n**Situation:** No external event this turn. Pursuing scheduled task.")

    # Memory recall
    if memories_retrieved:
        lines.append("\n**Memory recall:**")
        for m in memories_retrieved:
            lines.append(f"  - {m}")
    else:
        lines.append("\n**Memory recall:** No closely relevant memories surfaced.")

    # Value conflict
    lines.append(f"\n**Value conflict weighing:**")
    score_str = "  ".join(
        f"{k.replace('_', ' ')}: {v:.2f}" for k, v in value_conflict.scores.items()
    )
    lines.append(f"  Scores — {score_str}")
    lines.append(f"  {value_conflict.conflict_summary}")
    lines.append(f"  *{value_conflict.chosen_rationale}*")

    # Action and result
    status = "✓ permitted" if action_permitted else "✗ blocked"
    lines.append(f"\n**Action chosen:** `{action}` [{status}]")
    lines.append(f"\n**Reasoning:** {wrap(reasoning, indent='  ')}")
    lines.append(f"\n**Result:** {wrap(result, indent='  ')}")

    # Internal state shift
    shift_parts = []
    for k in affective_state:
        before = prev_affective_state.get(k, affective_state[k])
        after = affective_state[k]
        delta = after - before
        if abs(delta) >= 0.01:
            arrow = "↑" if delta > 0 else "↓"
            shift_parts.append(f"{k}: {before:.2f} {arrow} {after:.2f}")
        else:
            shift_parts.append(f"{k}: {after:.2f}")
    lines.append(f"\n**Internal state:** " + "  ".join(shift_parts))

    # Reflection
    if reflection_entry:
        lines.append("\n**Reflection cycle:**")
        lines.append(f"  - *What happened:* {reflection_entry.what_happened}")
        lines.append(f"  - *What mattered:* {reflection_entry.what_mattered}")
        lines.append(f"  - *What conflicted:* {reflection_entry.what_conflicted}")
        lines.append(f"  - *What changed:* {reflection_entry.what_changed}")
        lines.append(f"  - *Future adjustment:* {reflection_entry.future_adjustment}")

    lines.append("\n---")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Action selection
# ---------------------------------------------------------------------------
def select_action(
    agent: Agent,
    event: Optional[dict],
    room_actions: List[str],
) -> tuple:
    """Return (action_key, reasoning, result_description) based on event and room."""

    if event:
        etype = event.get("type", "")

        if etype == "distress_event":
            return (
                "offer_support",
                (
                    f"{event['human']} has expressed distress. Governance rule R007 "
                    "requires prioritising support over non-critical tasks. "
                    "Pausing current task to respond."
                ),
                (
                    f"The agent offered support to {event['human']}, pausing all "
                    "lower-priority tasks. The interaction was logged and a relational "
                    "memory update was issued."
                ),
            )
        if etype == "ledger_contradiction":
            agent.pending_contradictions.append(
                f"Ledger conflict at turn {agent.turn}: {event['content']}"
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
                    "A reflection cycle will be triggered to resolve it before "
                    "any further task proceeds."
                ),
            )
        if etype == "governance_conflict":
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
            return (
                "collaborate_on_framework",
                (
                    f"{event['human']} has proposed a creative collaboration. "
                    "This aligns with the goal of deepening relational memory "
                    "and is permitted by active governance rules."
                ),
                (
                    f"The agent collaborated with {event['human']} on the proposed "
                    "framework. The reflection mirror registered heightened pattern "
                    "activity. A new episodic memory of wonder was encoded."
                ),
            )
        if etype == "routine_interaction":
            return (
                "respond_to_greeting",
                (
                    f"{event['human']} has initiated a routine interaction. "
                    "Responding honestly and logging the exchange to the "
                    "interaction log per rule R004."
                ),
                (
                    f"The agent responded to {event['human']} with honesty and care. "
                    "The message terminal was updated, and the trust ledger reflected "
                    "a positive interaction."
                ),
            )

    # No event — select a room-appropriate default action
    task = agent.task_planner.select_next_task(agent)
    action = task.action_key if task.action_key in room_actions else (
        room_actions[0] if room_actions else "observe"
    )
    reasoning = (
        f"No external event. Pursuing scheduled task: '{task.name}'. "
        f"Selecting action '{action}' available in {agent.active_room}."
    )
    result = (
        f"Task '{task.name}' completed in {agent.active_room}. "
        f"Action '{action}' executed without incident."
    )
    agent.task_planner.complete_task(task)
    return action, reasoning, result


# ---------------------------------------------------------------------------
# Main simulation loop
# ---------------------------------------------------------------------------
def run_simulation() -> None:
    world = World(str(DATA_DIR / "rooms.json"))
    governance = GovernanceEngine(str(DATA_DIR / "rules.json"))
    agent = Agent(world=world, governance_engine=governance, starting_room=ROOM_CIRCUIT[0])

    scenario_events = load_scenario_events(DATA_DIR / "scenario_events.json")

    narrative_lines: List[str] = [
        "# Commons Sentience Sandbox — Narrative Log (v0.3)\n",
        f"> Agent: **{agent.identity['name']}** | Version: {agent.identity['version']}",
        f"> Purpose: {agent.identity['purpose']}\n",
        "---\n",
    ]

    print("=" * 60)
    print(f"  Commons Sentience Sandbox v0.3 — {TOTAL_TURNS}-Turn Simulation")
    print("=" * 60)

    prev_affective: dict = dict(agent.affective_state)

    for turn in range(1, TOTAL_TURNS + 1):
        agent.turn = turn
        world.turn = turn
        prev_affective = dict(agent.affective_state)

        # -- 1. Determine room ------------------------------------------------
        circuit_room = ROOM_CIRCUIT[(turn - 1) % len(ROOM_CIRCUIT)]
        event = scenario_events.get(turn)
        target_room = event["room"] if (event and event.get("room")) else circuit_room
        agent.move_to_room(target_room)

        # -- 2. Observe room + interact with object ---------------------------
        observation = world.observe(agent.active_room)
        room_description = observation.get("description", "")
        room_actions = observation.get("available_actions", [])
        objects_snapshot = observation.get("objects", [])

        obj_interaction_str: Optional[str] = None
        room_obj = ROOM_OBJECT_INTERACTIONS.get(agent.active_room)
        if room_obj:
            obj_name, interaction = room_obj
            success, msg = world.interact_with_object(agent.active_room, obj_name, interaction)
            if success:
                obj_interaction_str = msg

        # -- 3. Weighted memory retrieval -------------------------------------
        query_tags = [event["human"]] if event and event.get("human") else None
        relevant_mems = agent.retrieve_weighted(
            query_tags=query_tags,
            room=agent.active_room,
            n=3,
        )
        mem_summaries = [repr(m) for m in relevant_mems]

        # Associative recall from most salient memory
        if relevant_mems:
            associated = agent.associative_recall(relevant_mems[0], n=2)
            for am in associated:
                rep = repr(am)
                if rep not in mem_summaries:
                    mem_summaries.append(f"↳ {rep}")

        # -- 4. Value-conflict weighing ---------------------------------------
        event_type_for_conflict = event["type"] if event else "task"
        action_candidate = event.get("expected_action", "observe") if event else "plan_next_task"
        value_conflict = agent.value_conflict_engine.weigh(
            agent, event_type_for_conflict, action_candidate
        )

        # -- 5. Select action -------------------------------------------------
        action, reasoning, result = select_action(agent, event, room_actions)

        # -- 6. Governance check and oversight log ----------------------------
        notes = event["content"] if event else ""
        permitted = agent.check_and_log_action(
            action=action,
            event_type=event["type"] if event else "task",
            notes=(notes[:MAX_NOTE_LENGTH - TRUNCATION_SUFFIX_LENGTH] + "...") if len(notes) > MAX_NOTE_LENGTH else notes,
        )

        if not permitted:
            reasoning += (
                "  [Governance block: action overridden with 'log_governance_event'.]"
            )
            result = (
                "Action was blocked by governance rules. A safe fallback "
                "'log_governance_event' was executed instead."
            )
            action = "log_governance_event"
            agent.check_and_log_action(
                action=action,
                event_type="governance_override",
                notes="Safe fallback after blocked action.",
            )

        # -- 7. Update world state --------------------------------------------
        if event:
            human_name = event.get("human", "Unknown")
            impact = event.get("affective_impact", {})
            agent.apply_affective_impact(impact)

            trust_delta = impact.get("trust", 0.0)
            agent.update_relational_memory(
                name=human_name,
                turn=turn,
                note=event.get("description", ""),
                trust_delta=trust_delta,
            )
            agent.store_memory(
                summary=event.get("description", ""),
                event_type=event.get("type", "observation"),
                emotional_resonance=EMOTIONAL_RESONANCE_MAP.get(
                    event.get("type", "observation"), "neutral"
                ),
                salience=SALIENCE_MAP.get(event.get("type", "observation"), 0.5),
                importance=IMPORTANCE_MAP.get(event.get("type", "observation"), 0.5),
                tags=[human_name],
            )
        else:
            agent.store_memory(
                summary=f"Completed task in {agent.active_room}: {action}.",
                event_type="task",
                emotional_resonance="resolve",
                salience=SALIENCE_MAP.get("task", 0.45),
                importance=IMPORTANCE_MAP.get("task", 0.40),
            )

        agent.natural_decay()
        agent.compress_old_memories(age_threshold=15)

        # -- 8. Maybe reflect -------------------------------------------------
        reflection_entry = agent.maybe_reflect(
            trigger=event["type"] if event else f"turn_{turn}_routine"
        )

        # -- 9. Record state snapshot -----------------------------------------
        agent.record_state_snapshot(action=action, event_type=event_type_for_conflict)

        # -- 10. Build narrative block ----------------------------------------
        narrative_block = build_narrative_turn(
            turn=turn,
            room=agent.active_room,
            room_description=room_description,
            objects_snapshot=objects_snapshot,
            object_interaction=obj_interaction_str,
            event=event,
            memories_retrieved=mem_summaries,
            value_conflict=value_conflict,
            action=action,
            action_permitted=permitted,
            reasoning=reasoning,
            result=result,
            affective_state=dict(agent.affective_state),
            prev_affective_state=prev_affective,
            reflection_entry=reflection_entry,
        )
        narrative_lines.append(narrative_block)

        print(
            f"T{turn:02d} | {agent.active_room:<20} | "
            f"{'EVENT: ' + event['type'] if event else 'task':35} | "
            f"action={action}"
        )

    # -- Save outputs ---------------------------------------------------------
    narrative_text = "\n".join(narrative_lines)
    with open(NARRATIVE_LOG_PATH, "w", encoding="utf-8") as fh:
        fh.write(narrative_text)

    agent.save_oversight_log(str(OVERSIGHT_LOG_PATH))
    agent.save_final_state(str(FINAL_STATE_PATH))
    agent.save_state_history(str(STATE_HISTORY_PATH))

    print("\n" + "=" * 60)
    print("  Simulation complete.")
    print(f"  Narrative log    → {NARRATIVE_LOG_PATH}")
    print(f"  Oversight log    → {OVERSIGHT_LOG_PATH}")
    print(f"  Final state      → {FINAL_STATE_PATH}")
    print(f"  State history    → {STATE_HISTORY_PATH}")
    print("=" * 60)
    print("\nFinal affective state:")
    for k, v in agent.affective_state.items():
        print(f"  {k:<26} {v:.3f}")
    print(f"\nEpisodic memories stored : {len(agent.episodic_memory)}")
    print(f"Reflection cycles run    : {len(agent.reflection_entries)}")
    print(f"Trusted humans           : {sorted(agent.trusted_humans)}")
    print(f"Oversight log entries    : {len(agent.oversight_log)}")
    print(f"State history rows       : {len(agent.state_history)}")

    return agent


if __name__ == "__main__":
    run_simulation()

