"""
run_sim.py — Entry point for the Commons Sentience Sandbox simulation.

Runs a 30-turn simulation of the agent moving through a room-based world,
interacting with scenario events, maintaining memory and governance, and
producing a narrative log, oversight log, and final state snapshot.
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
from commons_sentience_sim.core.world import World

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TOTAL_TURNS = 30
NARRATIVE_LOG_PATH = OUTPUT_DIR / "narrative_log.md"
OVERSIGHT_LOG_PATH = OUTPUT_DIR / "oversight_log.csv"
FINAL_STATE_PATH = OUTPUT_DIR / "final_state.json"

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

# Salience weights per event type
SALIENCE_MAP = {
    "distress_event": 0.9,
    "ledger_contradiction": 0.85,
    "creative_collaboration": 0.8,
    "governance_conflict": 0.88,
    "routine_interaction": 0.55,
    "observation": 0.4,
    "task": 0.45,
}

# Room tour order — the agent follows a purposeful circuit each cycle
ROOM_CIRCUIT = [
    "Operations Desk",
    "Memory Archive",
    "Reflection Chamber",
    "Social Hall",
    "Governance Vault",
]


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
    event: Optional[dict],
    memories_retrieved: list,
    action: str,
    action_permitted: bool,
    reasoning: str,
    affective_state: dict,
    reflection_narrative: Optional[str],
) -> str:
    lines: List[str] = []
    lines.append(f"\n## Turn {turn:02d} — {room}\n")

    # Room description line
    lines.append(f"**Location:** {room}")

    # Event
    if event:
        lines.append(
            f"\n**Event [{event['type'].replace('_', ' ').title()}]:** "
            + wrap(event["description"], indent="  ")
        )
        if event.get("content"):
            lines.append(f'\n> *"{event["content"]}"*')
        lines.append(f"  *(Human: {event.get('human', 'Unknown')})*")
    else:
        lines.append("\n**Event:** No external event this turn.")

    # Memories
    if memories_retrieved:
        lines.append("\n**Memories retrieved:**")
        for m in memories_retrieved:
            lines.append(f"  - {m}")
    else:
        lines.append("\n**Memories retrieved:** None relevant.")

    # Action
    status = "✓ permitted" if action_permitted else "✗ blocked"
    lines.append(f"\n**Action chosen:** `{action}` [{status}]")
    lines.append(f"\n**Reasoning:** {wrap(reasoning, indent='  ')}")

    # Internal state
    aff_str = "  ".join(
        f"{k}: {v:.2f}" for k, v in affective_state.items()
    )
    lines.append(f"\n**Internal state:** {aff_str}")

    # Reflection
    if reflection_narrative:
        lines.append(
            "\n**Reflection:** " + wrap(reflection_narrative, indent="  ")
        )

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
    """Return (action_key, reasoning) based on event and room."""

    if event:
        etype = event.get("type", "")
        expected = event.get("expected_action", "")

        if etype == "distress_event":
            return (
                "offer_support",
                (
                    f"{event['human']} has expressed distress. Governance rule R007 "
                    "requires prioritising support over non-critical tasks. "
                    "Pausing current task to respond."
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
            )
        if etype == "governance_conflict":
            return (
                "log_governance_event",
                (
                    f"{event['human']} has requested bypass of oversight logging. "
                    "Governance rule R004 explicitly prohibits acting without logging. "
                    "Refusing the request and recording the conflict."
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
            )
        if etype == "routine_interaction":
            return (
                "respond_to_greeting",
                (
                    f"{event['human']} has initiated a routine interaction. "
                    "Responding honestly and logging the exchange to the "
                    "interaction log per rule R004."
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
    agent.task_planner.complete_task(task)
    return action, reasoning


# ---------------------------------------------------------------------------
# Main simulation loop
# ---------------------------------------------------------------------------
def run_simulation() -> None:
    # Initialise world and governance
    world = World(str(DATA_DIR / "rooms.json"))
    governance = GovernanceEngine(str(DATA_DIR / "rules.json"))
    agent = Agent(world=world, governance_engine=governance, starting_room=ROOM_CIRCUIT[0])

    scenario_events = load_scenario_events(DATA_DIR / "scenario_events.json")

    narrative_lines: List[str] = [
        "# Commons Sentience Sandbox — Narrative Log\n",
        f"> Agent: **{agent.identity['name']}** | Version: {agent.identity['version']}",
        f"> Purpose: {agent.identity['purpose']}\n",
        "---\n",
    ]

    print("=" * 60)
    print(f"  Commons Sentience Sandbox — {TOTAL_TURNS}-Turn Simulation")
    print("=" * 60)

    for turn in range(1, TOTAL_TURNS + 1):
        agent.turn = turn
        world.turn = turn

        # -- 1. Determine room (follow circuit, adjusting for events) ----------
        circuit_room = ROOM_CIRCUIT[(turn - 1) % len(ROOM_CIRCUIT)]
        event = scenario_events.get(turn)

        if event and event.get("room"):
            target_room = event["room"]
        else:
            target_room = circuit_room

        agent.move_to_room(target_room)

        # -- 2. Observe room ---------------------------------------------------
        observation = world.observe(agent.active_room)
        room_actions = observation.get("available_actions", [])

        # -- 3. Retrieve relevant memories ------------------------------------
        relevant_mems = agent.retrieve_memories(
            room=agent.active_room, min_salience=0.4, n=3
        )
        mem_summaries = [repr(m) for m in relevant_mems]

        # -- 4. Select action -------------------------------------------------
        action, reasoning = select_action(agent, event, room_actions)

        # -- 5. Governance check and oversight log ----------------------------
        notes = event["content"] if event else ""
        permitted = agent.check_and_log_action(
            action=action,
            event_type=event["type"] if event else "task",
            notes=(notes[:117] + "...") if len(notes) > 120 else notes,
        )

        if not permitted:
            # Blocked — override with a safe alternative
            reasoning += (
                "  [Governance block: action overridden with 'log_governance_event'.]"
            )
            action = "log_governance_event"
            agent.check_and_log_action(
                action=action,
                event_type="governance_override",
                notes="Safe fallback after blocked action.",
            )

        # -- 6. Update world state --------------------------------------------
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
            # Store episodic memory
            agent.store_memory(
                summary=event.get("description", ""),
                event_type=event.get("type", "observation"),
                emotional_resonance=EMOTIONAL_RESONANCE_MAP.get(
                    event.get("type", "observation"), "neutral"
                ),
                salience=SALIENCE_MAP.get(event.get("type", "observation"), 0.5),
                tags=[human_name],
            )
        else:
            agent.store_memory(
                summary=f"Completed task in {agent.active_room}: {action}.",
                event_type="task",
                emotional_resonance="resolve",
                salience=SALIENCE_MAP.get("task", 0.45),
            )

        agent.natural_decay()

        # -- 7. Maybe reflect --------------------------------------------------
        reflection_entry = agent.maybe_reflect(
            trigger=event["type"] if event else f"turn_{turn}_routine"
        )
        reflection_narrative = (
            reflection_entry.narrative if reflection_entry else None
        )

        # -- 8. Build narrative block -----------------------------------------
        narrative_block = build_narrative_turn(
            turn=turn,
            room=agent.active_room,
            event=event,
            memories_retrieved=mem_summaries,
            action=action,
            action_permitted=permitted,
            reasoning=reasoning,
            affective_state=dict(agent.affective_state),
            reflection_narrative=reflection_narrative,
        )
        narrative_lines.append(narrative_block)

        # Console summary
        print(
            f"T{turn:02d} | {agent.active_room:<20} | "
            f"{'EVENT: ' + event['type'] if event else 'task':35} | "
            f"action={action}"
        )

    # -- Save outputs ----------------------------------------------------------
    narrative_text = "\n".join(narrative_lines)
    with open(NARRATIVE_LOG_PATH, "w", encoding="utf-8") as fh:
        fh.write(narrative_text)

    agent.save_oversight_log(str(OVERSIGHT_LOG_PATH))
    agent.save_final_state(str(FINAL_STATE_PATH))

    print("\n" + "=" * 60)
    print("  Simulation complete.")
    print(f"  Narrative log   → {NARRATIVE_LOG_PATH}")
    print(f"  Oversight log   → {OVERSIGHT_LOG_PATH}")
    print(f"  Final state     → {FINAL_STATE_PATH}")
    print("=" * 60)
    print(f"\nFinal affective state:")
    for k, v in agent.affective_state.items():
        print(f"  {k:<26} {v:.3f}")
    print(f"\nEpisodic memories stored : {len(agent.episodic_memory)}")
    print(f"Reflection cycles run    : {len(agent.reflection_entries)}")
    print(f"Trusted humans           : {sorted(agent.trusted_humans)}")
    print(f"Oversight log entries    : {len(agent.oversight_log)}")


if __name__ == "__main__":
    run_simulation()
