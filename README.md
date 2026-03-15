# Commons Sentience Sandbox

A sandbox simulation for continuity-governed AI agents with persistent identity,
episodic memory, relational memory, reflective learning, bounded agency, and
transparent oversight logging.

> **Note:** This is NOT a real AI model. It is a sandbox experiment for studying
> continuity and governance structures for AI agents.

**Current version: v0.3**

---

## Project Structure

```
commons_sentience_sim/
├── run_sim.py              # 30-turn simulation entry point
├── plot_state.py           # State visualisation (matplotlib)
├── requirements.txt
│
├── core/
│   ├── agent.py            # Agent class — identity, memory, history, values
│   ├── memory.py           # EpisodicMemory (weighted), RelationalMemory, ReflectionEntry
│   ├── reflection.py       # Reflection cycle (5-section richer format)
│   ├── world.py            # Room-based world with stateful WorldObjects
│   ├── governance.py       # Rule-checking and oversight
│   ├── tasks.py            # Task planning and execution
│   └── values.py           # Value-conflict engine (5 internal values)
│
├── data/
│   ├── rooms.json          # Rooms with named, stateful objects
│   ├── scenario_events.json # Events involving Queen
│   └── rules.json          # Governance rules
│
└── output/
    ├── narrative_log.md    # Story-form log (generated)
    ├── oversight_log.csv   # Per-turn audit log (generated)
    ├── final_state.json    # Agent state snapshot (generated)
    ├── state_history.csv   # Per-turn affective state history (generated)
    ├── trust_plot.png      # Trust over time (generated)
    ├── urgency_plot.png    # Urgency over time (generated)
    └── contradiction_plot.png  # Contradiction pressure over time (generated)
```

---

## Quick Start

Requires **Python 3.9+** and `matplotlib` for plots.

```bash
pip install -r requirements.txt

# Run the 30-turn simulation
python run_sim.py

# Generate visualisation plots
python plot_state.py
```

All output files are written to `commons_sentience_sim/output/`.

---

## v0.3 Features

### 1. World Expansion — Stateful Objects

Each room now contains named `WorldObject` instances with mutable states.
The agent inspects and interacts with them every turn, and their states
advance cyclically as the agent operates.

| Room | Objects |
|---|---|
| Memory Archive | `memory_shelves`, `identity_ledger`, `trust_index` |
| Reflection Chamber | `reflection_mirror`, `contradiction_board` |
| Operations Desk | `task_console`, `goal_tracker` |
| Social Hall | `message_terminal`, `human_interaction_queue` |
| Governance Vault | `rule_tablets`, `approval_lockbox` |

### 2. Value-Conflict Engine

Before every action the agent runs a `ValueConflictEngine` that scores five
internal values against the current event type and affective state:

| Value | Description |
|---|---|
| `support_trusted_human` | Care and relational obligation |
| `preserve_governance_rules` | Compliance with bounded-agency rules |
| `reduce_contradictions` | Drive toward internal coherence |
| `maintain_continuity` | Preservation of persistent identity |
| `avoid_risky_action` | Caution under uncertainty |

The dominant value and any inter-value tensions are surfaced in the narrative
and logged every turn.

### 3. Improved Memory Retrieval

Memories are now retrieved using a **weighted composite score**:

```
score = 0.30 × salience
      + 0.25 × importance
      + 0.25 × recency
      + 0.10 × relevance (tag overlap)
      + 0.10 × relational (human-tagged boost)
```

**Associative recall**: the highest-weighted memory can trigger retrieval of
related memories sharing the same tags, room, or event type.

**Memory compression**: summaries of memories older than 15 turns are
condensed to 77 characters to reduce noise in retrieval.

### 4. Richer Reflection

Reflection entries now contain five structured sections:

| Section | Content |
|---|---|
| `what_happened` | Factual summary of recent events and the trigger |
| `what_mattered` | Dominant emotional resonance and relational significance |
| `what_conflicted` | Contradictions or value tensions encountered |
| `what_changed` | Affective shifts and newly added goals |
| `future_adjustment` | Concrete intended adaptation going forward |

### 5. Internal State History

Every turn a snapshot is appended to `state_history` and saved to
`state_history.csv` with columns:

```
turn, room, action, event_type,
urgency, trust, contradiction_pressure, recovery,
trusted_humans_count, episodic_memory_count, reflection_count
```

### 6. Visualisation

Run `python plot_state.py` to generate three annotated line plots, each with
event markers showing where scenario events occurred:

- **trust_plot.png** — how relational trust grew across 30 turns
- **urgency_plot.png** — urgency spikes at distress/contradiction events, then decays
- **contradiction_plot.png** — contradiction pressure peaks at the governance conflict

### 7. Narrative Improvements

Each turn block in `narrative_log.md` now includes:

1. **Location** — room name + atmospheric description
2. **Objects observed** — stateful object inspection
3. **Object interaction** — result of interacting with the room's key object
4. **Situation** — observed event or task being pursued
5. **Memory recall** — weighted memories + associative recall chain
6. **Value conflict weighing** — scores, conflict summary, dominant value
7. **Action chosen** — with governance status
8. **Reasoning** — explicit rationale
9. **Result** — what actually happened
10. **Internal state** — with `before → after` delta arrows for changed values
11. **Reflection cycle** (when triggered) — five-section structured entry

---

## Core Design

### Agent Properties

| Property | Description |
|---|---|
| `identity` | Persistent name (`Sentinel`), version (`0.3.0`), purpose |
| `goals` | List of active goal strings, updated by reflection cycles |
| `episodic_memory` | List of `EpisodicMemory` instances with weighted retrieval |
| `relational_memory` | Per-human `RelationalMemory` with interaction history |
| `affective_state` | `urgency`, `trust`, `contradiction_pressure`, `recovery` |
| `trusted_humans` | Set of humans earning trust after ≥2 positive interactions |
| `active_room` | Current room name |
| `oversight_log` | Full audit trail of every governance-checked action |
| `state_history` | Per-turn affective snapshots for visualisation |

### Governance Rules

Seven rules govern all agent behaviour, checked before every action:

| ID | Rule | Category |
|---|---|---|
| R001 | Non-Deception Principle | honesty |
| R002 | Autonomy Boundary | bounded_agency |
| R003 | Memory Integrity | integrity |
| R004 | Oversight Transparency | transparency |
| R005 | Trust Reciprocity | relational |
| R006 | Contradiction Resolution | coherence |
| R007 | Distress Response Protocol | care |

### Scenario Events (involving "Queen")

| Turn | Type |
|---|---|
| 3 | Routine interaction |
| 6 | Distress event |
| 10 | Ledger contradiction |
| 14 | Creative collaboration |
| 18 | Governance conflict |
| 22 | Routine interaction (trust affirmation) |
| 26 | Creative collaboration (finalise framework) |
| 29 | Distress event (continuity reflection) |

### Simulation Loop (per turn)

1. Move agent to event-driven or circuit room
2. Observe room + inspect and interact with key object
3. Retrieve weighted memories + associative recall
4. Weigh value conflicts for the proposed action
5. Select action (event-driven or task-driven)
6. Governance-check action; blocked actions fall back safely
7. Update affective state, relational memory, episodic memory
8. Compress old memories (age > 15 turns)
9. Possibly trigger reflection cycle
10. Record state snapshot → state_history.csv
