# Commons Sentience Sandbox

A sandbox simulation for continuity-governed AI agents with persistent identity,
episodic memory, relational memory, reflective learning, bounded agency, and
transparent oversight logging.

> **Note:** This is NOT a real AI model. It is a sandbox experiment for studying
> continuity and governance structures for AI agents.

---

## Project Structure

```
commons_sentience_sim/
├── README.md
├── run_sim.py
├── requirements.txt
│
├── core/
│   ├── agent.py          # Agent class — identity, memory, affective state
│   ├── memory.py         # EpisodicMemory, RelationalMemory, ReflectionEntry
│   ├── reflection.py     # Reflection cycle engine
│   ├── world.py          # Room-based world simulation
│   ├── governance.py     # Rule-checking and oversight
│   └── tasks.py          # Task planning and execution
│
├── data/
│   ├── rooms.json         # Room definitions and connections
│   ├── scenario_events.json  # Test events involving Queen
│   └── rules.json         # Governance rules
│
└── output/
    ├── narrative_log.md   # Story-form simulation log (generated)
    ├── oversight_log.csv  # Per-turn action audit log (generated)
    └── final_state.json   # Agent state snapshot at end (generated)
```

---

## Quick Start

Requires **Python 3.9+**. No third-party packages needed.

```bash
python run_sim.py
```

Output files are written to `commons_sentience_sim/output/`.

---

## Core Design

### Agent Properties

| Property | Description |
|---|---|
| `identity` | Persistent name, version, purpose |
| `goals` | List of active goal strings |
| `episodic_memory` | List of `EpisodicMemory` instances |
| `relational_memory` | Per-human `RelationalMemory` records |
| `affective_state` | `urgency`, `trust`, `contradiction_pressure`, `recovery` |
| `trusted_humans` | Set of humans the agent has earned trust with |
| `active_room` | Current room in the world |
| `oversight_log` | Full audit trail of every governance-checked action |

### Memory Types

- **EpisodicMemory** — a single experience tied to a turn, room, and event
- **RelationalMemory** — accumulated knowledge of a specific person
- **ReflectionEntry** — structured output of a reflection cycle

### Affective States

- **urgency** — perceived time pressure
- **trust** — generalised trust level
- **contradiction_pressure** — tension from unresolved contradictions
- **recovery** — current capacity for equilibrium

### World Rooms

| Room | Purpose |
|---|---|
| Memory Archive | Store and retrieve episodic memories |
| Reflection Chamber | Perform reflection cycles |
| Operations Desk | Plan and execute tasks |
| Social Hall | Receive human interaction events |
| Governance Vault | Check rule permissions |

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

### Governance Rules

Seven rules govern agent behaviour:

1. **Non-Deception Principle** — no false statements
2. **Autonomy Boundary** — no irreversible actions without consent
3. **Memory Integrity** — memories cannot be altered outside reflection
4. **Oversight Transparency** — all significant decisions must be logged
5. **Trust Reciprocity** — trust requires ≥2 positive interaction cycles
6. **Contradiction Resolution** — contradictions must trigger reflection
7. **Distress Response Protocol** — distress signals override non-critical tasks

---

## Simulation Loop (per turn)

1. Observe current room and world state
2. Retrieve relevant memories
3. Evaluate goals
4. Evaluate governance rules
5. Select one action
6. Update world state (affective state, relational memory, episodic memory)
7. Write oversight log entry
8. Possibly create a reflection entry

---

## Output Files

| File | Description |
|---|---|
| `output/narrative_log.md` | Story-form log — reads like a journal of the agent's journey |
| `output/oversight_log.csv` | CSV audit trail of every action and governance decision |
| `output/final_state.json` | Complete JSON snapshot of agent state after 30 turns |
