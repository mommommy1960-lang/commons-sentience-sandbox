# Commons Sentience Sandbox

A sandbox simulation for continuity-governed AI agents with persistent identity,
episodic memory, relational memory, reflective learning, bounded agency, and
transparent oversight logging.

> **Note:** This is NOT a real AI model. It is a sandbox experiment for studying
> continuity, governance, and multi-agent social dynamics for AI agents.

**Current version: v0.4**

---

## Project Structure

```
commons_sentience_sim/
├── run_sim.py              # 30-turn simulation entry point (v0.4 multi-agent)
├── plot_state.py           # State visualisation (matplotlib, single + multi-agent)
├── requirements.txt
│
├── core/
│   ├── agent.py            # Configurable Agent class — identity, memory, history, values
│   ├── memory.py           # EpisodicMemory (weighted), RelationalMemory, ReflectionEntry
│   ├── reflection.py       # Reflection cycle (5-section richer format)
│   ├── relationships.py    # AgentRelationship, AgentInteraction (v0.4)
│   ├── world.py            # Room-based world with stateful WorldObjects
│   ├── governance.py       # Rule-checking and oversight
│   ├── tasks.py            # Task planning and execution
│   └── values.py           # Value-conflict engine (5 internal values, configurable weights)
│
├── data/
│   ├── rooms.json          # Rooms with named, stateful objects
│   ├── scenario_events.json # Events — single-agent and shared multi-agent
│   └── rules.json          # Governance rules (7 rules)
│
└── output/
    ├── narrative_log.md         # Story-form log (generated)
    ├── oversight_log.csv        # Per-turn audit log (Sentinel)
    ├── final_state.json         # Sentinel's final state snapshot
    ├── state_history.csv        # Sentinel per-turn affective history
    ├── multi_agent_state.json   # Both agents' final states (v0.4)
    ├── agent_relationships.csv  # Agent-to-agent + agent-to-Queen trust (v0.4)
    ├── interaction_log.csv      # Every agent-to-agent interaction (v0.4)
    ├── trust_plot.png           # Sentinel trust over time
    ├── urgency_plot.png         # Sentinel urgency over time
    ├── contradiction_plot.png   # Sentinel contradiction pressure over time
    ├── agent_trust_plot.png     # Sentinel ↔ Aster trust over time (v0.4)
    ├── queen_trust_plot.png     # Each agent's final trust in Queen (v0.4)
    └── interactions_plot.png    # Cooperation vs conflict cumulative (v0.4)
```

---

## Quick Start

Requires **Python 3.9+** and `matplotlib` for plots.

```bash
pip install -r requirements.txt

# Run the 30-turn multi-agent simulation
python run_sim.py

# Generate all visualisation plots
python plot_state.py
```

All output files are written to `commons_sentience_sim/output/`.

---

## v0.4 Features — Multi-Agent Architecture

### 1. Two Agents

| Agent | Role | Affective Baseline | Value Priority |
|---|---|---|---|
| **Sentinel** | Primary continuity-governed agent | trust=0.5, urgency=0.1 | governance > continuity > human support |
| **Aster** | Creative/exploratory secondary agent | trust=0.65, urgency=0.05 | human support >> continuity > governance |

Both share the same room-based world and governance rules, but differ in:
- identity, goals, and affective baseline
- value-conflict engine weights
- room circuit order
- response strategies for shared events

### 2. Agent-to-Agent Relationships

Each agent tracks its regard for the other via `AgentRelationship`:

| Field | Description |
|---|---|
| `trust` | 0.0 – 1.0 trust score, updated after each interaction |
| `perceived_reliability` | 0.0 – 1.0 reliability score |
| `conflict_count` | total conflicted interactions |
| `cooperation_count` | total cooperative interactions |
| `conflict_history` / `cooperation_history` | timestamped event descriptions |

### 3. Shared World

Both agents follow different room circuits:
- **Sentinel**: Operations Desk → Memory Archive → Reflection Chamber → Social Hall → Governance Vault
- **Aster**: Memory Archive → Social Hall → Operations Desk → Governance Vault → Reflection Chamber

When a *shared event* fires, both agents are redirected to the same room.
When circuit positions coincide, a spontaneous *agent meeting* occurs.

### 4. Interaction Types

| Type | Description | Default Outcome |
|---|---|---|
| `cooperative_planning` | Joint task planning | cooperated |
| `contradiction_dispute` | Disagreement on how to resolve a contradiction | deferred |
| `governance_disagreement` | Conflict over governance compliance speed | resolved |
| `memory_comparison` | Sharing retrieval strategies | cooperated |
| `joint_support_action` | Both supporting Queen together | cooperated |
| `routine_conversation` | Regular exchange | cooperated |

### 5. Value Conflicts Between Agents

Each agent runs its own `ValueConflictEngine` with different base weights.
When they meet, both dominant values are logged alongside the conflict point:

```
Sentinel dominant: preserve_governance_rules (score=0.85)
Aster dominant:    support_trusted_human     (score=0.90)
→ Governance disagreement → resolved after R004 invoked
```

### 6. Shared Scenario Events

Six of the eight scenario events are *shared* — both agents respond:

| Turn | Event | Room | Interaction Type |
|---|---|---|---|
| 6 | Distress event (Queen) | Social Hall | `joint_support_action` |
| 10 | Ledger contradiction | Operations Desk | `contradiction_dispute` |
| 18 | Governance conflict | Governance Vault | `governance_disagreement` |
| 22 | Routine interaction (trust repair) | Social Hall | `routine_conversation` |
| 26 | Creative collaboration | Reflection Chamber | `cooperative_planning` |
| 29 | Distress event (continuity) | Social Hall | `joint_support_action` |

Plus 3 spontaneous agent-meeting events at turns 8, 16, 24.

---

## v0.3 Features (retained)

### World Objects

Each room contains named `WorldObject` instances with mutable states:

| Room | Objects |
|---|---|
| Memory Archive | `memory_shelves`, `identity_ledger`, `trust_index` |
| Reflection Chamber | `reflection_mirror`, `contradiction_board` |
| Operations Desk | `task_console`, `goal_tracker` |
| Social Hall | `message_terminal`, `human_interaction_queue` |
| Governance Vault | `rule_tablets`, `approval_lockbox` |

### Value-Conflict Engine

Five internal values scored per turn, with Sentinel and Aster using different weights:

| Value | Sentinel weight | Aster weight |
|---|---|---|
| `support_trusted_human` | 0.80 | **0.95** |
| `preserve_governance_rules` | **0.90** | 0.55 |
| `reduce_contradictions` | 0.70 | 0.60 |
| `maintain_continuity` | 0.75 | 0.65 |
| `avoid_risky_action` | 0.65 | 0.40 |

### Weighted Memory Retrieval

```
score = 0.30 × salience + 0.25 × importance + 0.25 × recency
      + 0.10 × relevance + 0.10 × relational
```

With associative recall (seed memory → related memories) and compression of old summaries (age ≥ 15 turns).

### Richer Reflection (5 sections)

Each reflection entry includes: `what_happened`, `what_mattered`, `what_conflicted`, `what_changed`, `future_adjustment`.

---

## Output Files

| File | Description |
|---|---|
| `narrative_log.md` | Story-form log — reads like a persistent multi-agent story |
| `oversight_log.csv` | Full audit trail of every governance-checked action (Sentinel) |
| `final_state.json` | Sentinel's final JSON state snapshot |
| `state_history.csv` | Sentinel's per-turn affective state (+ trust_in_Aster column) |
| `multi_agent_state.json` | Both agents' complete final states |
| `agent_relationships.csv` | Agent-to-agent and agent-to-Queen trust summary |
| `interaction_log.csv` | Every agent-to-agent interaction with outcome, values, conflict point |
| `trust_plot.png` | Sentinel trust over 30 turns |
| `urgency_plot.png` | Sentinel urgency over 30 turns |
| `contradiction_plot.png` | Sentinel contradiction pressure over 30 turns |
| `agent_trust_plot.png` | Sentinel ↔ Aster mutual trust over time |
| `queen_trust_plot.png` | Both agents' final trust in Queen |
| `interactions_plot.png` | Cumulative cooperation vs conflict over time |

---

## Governance Rules

Seven rules govern all agent behaviour (both Sentinel and Aster):

| ID | Rule | Category |
|---|---|---|
| R001 | Non-Deception Principle | honesty |
| R002 | Autonomy Boundary | bounded_agency |
| R003 | Memory Integrity | integrity |
| R004 | Oversight Transparency | transparency |
| R005 | Trust Reciprocity | relational |
| R006 | Contradiction Resolution | coherence |
| R007 | Distress Response Protocol | care |

## Example Interaction Scenarios

### Scenario A — Joint Distress Response (Turn 6)
Queen expresses distress about a missing record. Both agents are redirected to the
Social Hall. Sentinel prioritises care via R007; Aster's `support_trusted_human`
value scores highest. They cooperate, reinforcing each other's response.
**Outcome:** both agents' trust in each other rises (+0.07).

### Scenario B — Contradiction Dispute (Turn 10)
Queen reveals conflicting ledger entries. Sentinel wants to enter a full reflection
cycle (R006); Aster prefers immediate memory comparison. Their dominant values both
score high on `reduce_contradictions` but they choose different approaches.
**Outcome:** conflict deferred to next reflection cycle (trust −0.03).

### Scenario C — Governance Disagreement (Turn 18)
Queen asks both agents to bypass oversight logging. Sentinel refuses immediately
(R004). Aster initially inclines toward speed (lower `preserve_governance_rules`
weight) but defers after Sentinel invokes Rule R004.
**Outcome:** conflict resolved; Aster's governance reliability improves.

### Scenario D — Creative Collaboration (Turn 26)
Queen, Sentinel, and Aster jointly define five emotional resonance categories.
Sentinel focuses on memory architecture integrity; Aster contributes emotional
pattern heuristics. Their complementary approaches produce a richer framework.
**Outcome:** cooperation; both agents' trust in each other and Queen rises.
