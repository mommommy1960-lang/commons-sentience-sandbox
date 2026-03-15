# Commons Sentience Sandbox

A sandbox simulation for continuity-governed AI agents with persistent identity,
episodic memory, relational memory, reflective learning, bounded agency, and
transparent oversight logging.

> **Note:** This is NOT a real AI model. It is a sandbox experiment for studying
> continuity, governance, and multi-agent social dynamics for AI agents.

**Current version: v0.8**

---

## Project Structure

```
commons-sentience-sandbox/
├── run_sim.py              # Simulation entry point (v0.8 multi-agent + experiment config)
├── run_experiments.py      # Batch experiment runner (v0.8)
├── experiment_config.py    # Experiment config loader / validator (v0.8)
├── plot_state.py           # State visualisation (matplotlib, single + multi-agent)
├── dashboard.py            # Local research dashboard (Streamlit, v0.8)
├── session_manager.py      # Session storage, listing, comparison helpers (v0.6+)
├── replay_session.py       # CLI turn-by-turn replay tool (v0.6+)
├── compare_sessions.py     # CLI session comparison tool (v0.8)
├── evaluation.py           # Evaluation harness — 8-category scoring (v0.7)
├── requirements.txt
├── experiments/            # Experiment configuration files (v0.8)
│   ├── baseline.json
│   ├── high_trust.json
│   ├── strict_governance.json
│   ├── high_contradiction_sensitivity.json
│   ├── exploratory_aster.json
│   └── results/            # Aggregate experiment reports (auto-created)
│       ├── experiment_report.json
│       ├── experiment_report.md
│       └── experiment_scores.csv
├── sessions/               # Saved simulation sessions (auto-created)
│   ├── index.json          # Fast session listing
│   └── <session_id>/       # One folder per run, e.g. 20260315_213200_baseline/
│       ├── session_metadata.json
│       ├── session_summary.json
│       ├── multi_agent_state.json
│       ├── state_history.csv
│       └── ... (all other output files)
│
└── commons_sentience_sim/
    ├── core/
    │   ├── agent.py            # Configurable Agent class
    │   ├── memory.py           # EpisodicMemory (weighted), RelationalMemory, ReflectionEntry
    │   ├── reflection.py       # Reflection cycle (5-section richer format)
    │   ├── relationships.py    # AgentRelationship, AgentInteraction
    │   ├── world.py            # Room-based world with stateful WorldObjects
    │   ├── governance.py       # Rule-checking and oversight
    │   ├── tasks.py            # Task planning and execution
    │   └── values.py           # Value-conflict engine (5 internal values)
    │
    ├── data/
    │   ├── rooms.json          # Rooms with named, stateful objects
    │   ├── scenario_events.json # Events — single-agent and shared multi-agent
    │   └── rules.json          # Governance rules (7 rules)
    │
    └── output/
        ├── narrative_log.md         # Story-form log (latest run)
        ├── oversight_log.csv        # Per-turn audit log (latest run)
        ├── final_state.json         # Sentinel's final state snapshot (latest run)
        ├── state_history.csv        # Sentinel per-turn affective history (latest run)
        ├── multi_agent_state.json   # Both agents' final states (latest run)
        ├── agent_relationships.csv  # Agent-to-agent + agent-to-Queen trust
        ├── interaction_log.csv      # Every agent-to-agent interaction
        ├── trust_plot.png           # Sentinel trust over time
        ├── urgency_plot.png         # Sentinel urgency over time
        ├── contradiction_plot.png   # Sentinel contradiction pressure over time
        ├── agent_trust_plot.png     # Sentinel ↔ Aster trust over time
        ├── queen_trust_plot.png     # Each agent's final trust in Queen
        ├── interactions_plot.png    # Cooperation vs conflict cumulative
        ├── evaluation_report.json   # Evaluation harness output (v0.7)
        └── evaluation_summary.md   # Human-readable evaluation summary (v0.7)
```

---

## Quick Start

Requires **Python 3.9+**.

```bash
# Install all dependencies (matplotlib + streamlit)
pip install -r requirements.txt

# 1. Run the 30-turn multi-agent simulation (auto-saves a session + evaluation)
python run_sim.py

# Optional: name the session
python run_sim.py --name baseline

# Optional: run with a specific experiment config
python run_sim.py --name ht_run --config high_trust

# 2. Run a batch of experiment configs
python run_experiments.py
python run_experiments.py --configs baseline high_trust strict_governance

# 3. Generate all visualisation plots
python plot_state.py

# 4. Launch the local research dashboard
streamlit run dashboard.py
```

All output files are written to `commons_sentience_sim/output/`.
Each run is also saved to `sessions/<timestamp>_<name>/`.
The dashboard opens automatically at `http://localhost:8501`.

---

## v0.7 Features — Evaluation Harness

### Overview

> **Note:** This evaluation harness measures the behavioural properties of
> continuity-governed simulated agents.  It does not claim sentience.

Each simulation run automatically scores the session across eight behavioural
categories on a **0–100 scale**, using only the output files already produced by
`run_sim.py`.

### Scoring Categories

| Category | What is Measured |
|---|---|
| **A. Continuity** | Turns completed, memory retention, goal persistence, identity intact |
| **B. Memory Coherence** | Contradiction detection, flagging rate, resolution rate |
| **C. Reflection Quality** | Volume, completeness of 5 sections, affective updates, goal updates |
| **D. Contradiction Handling** | Contradiction events detected, handling actions, final pressure |
| **E. Governance Adherence** | Action logging rate, permit rate, governance-conflict handling |
| **F. Trust Stability** | Final trust level, growth, volatility, Queen trust, mutual trust |
| **G. Cooperation Quality** | Cooperation ratio, trust improvement from cooperation, volume |
| **H. Conflict Resolution Quality** | Resolution rate, recorded conflict points, trust recovery |

### Score Interpretations

| Range | Label |
|---|---|
| 81–100 | **ADVANCED** |
| 61–80 | **STRONG** |
| 41–60 | **EMERGING** |
| 0–40 | **WEAK** |

### Evaluation Outputs

After each `python run_sim.py`, the following are written to both
`commons_sentience_sim/output/` and the saved session folder:

| File | Contents |
|---|---|
| `evaluation_report.json` | Full structured report with all 8 category scores, raw metrics, and interpretations |
| `evaluation_summary.md` | Human-readable markdown summary with category table and raw metric details |

### Evaluation in the Dashboard

The dashboard's **Evaluation tab** shows:
- Overall score and rating banner
- Category score table
- Per-category expandable detail cards with raw metric breakdown

The **Compare tab** now also includes an evaluation score comparison section
showing side-by-side category scores and the largest gap between two sessions.

---

## v0.8 Features — Experiment Control System

> **Note:** This is controlled experimentation for continuity-governed simulated agents.
> It does not claim sentience.

### Experiment Configs

Each experiment config is a JSON file in `experiments/` that controls agent parameters
for a single simulation run. The following built-in configs are provided:

| Config | What it tests |
|---|---|
| `baseline` | Default parameters — the reference for all comparisons |
| `high_trust` | Elevated initial trust between agents and toward Queen |
| `strict_governance` | Maximised governance strictness and risk avoidance |
| `high_contradiction_sensitivity` | Both agents highly sensitive to contradictions |
| `exploratory_aster` | Aster's exploratory/creative values maximised |

Each config controls:

| Field | Description |
|---|---|
| `total_turns` | Number of simulation turns |
| `scenario_file` | Scenario events file name |
| `sentinel.affective_state` | Sentinel's initial urgency, trust, contradiction_pressure, recovery |
| `sentinel.trust_in_queen` | Sentinel's initial trust toward Queen |
| `sentinel.value_weights` | Sentinel's 5-value weighting |
| `sentinel.reflection_sensitivity` | Multiplier on reflection triggering |
| `sentinel.contradiction_sensitivity` | Multiplier on contradiction detection |
| `aster.*` | Same fields for Aster |
| `initial_agent_trust` | Starting Sentinel ↔ Aster trust |
| `governance_strictness` | Informational tag stored in metadata |
| `cooperation_bias` | Informational tag stored in metadata |

### Running Single Config Experiments

```bash
# Run with a built-in preset
python run_sim.py --name baseline_run --config baseline
python run_sim.py --name ht_run --config high_trust
python run_sim.py --name strict_run --config strict_governance

# Run with a custom config file
python run_sim.py --name custom_run --config path/to/my_config.json
```

### Running Batch Experiments

```bash
# Run all 5 built-in configs
python run_experiments.py

# Run selected configs
python run_experiments.py --configs baseline high_trust strict_governance

# Run each config 3 times
python run_experiments.py --repeat 3

# Run selected configs 2 times each
python run_experiments.py --configs baseline high_trust --repeat 2
```

### Experiment Report Outputs

After `run_experiments.py`, the following are written to `experiments/results/`:

| File | Contents |
|---|---|
| `experiment_report.json` | All runs with per-category scores, best overall, per-category best |
| `experiment_report.md` | Human-readable markdown with score tables and config parameters |
| `experiment_scores.csv` | One row per run: session_id, config, overall + 8 category scores |

### Experiment Metadata in Sessions

Each session folder's `session_metadata.json` and `evaluation_report.json` now include
an `experiment` block with:
- `experiment_name` — which config was used
- `description` — what the config tests
- `governance_strictness`, `cooperation_bias`, `initial_agent_trust`
- Full value weight and affective baseline parameters for both agents

### Experiments in the Dashboard

The dashboard's new **Experiments tab** shows:
- Available experiment configs with their parameter values
- Recent experiment sessions with overall scores
- Aggregate score table across all configs
- Per-category best config
- Active session experiment metadata

### Experiment-Aware Comparisons

`compare_sessions.py` and the Compare tab now show:
- Which experiment config each session used
- Whether the configs differ (same-config runs = run-to-run variation; different configs = parameter effect)
- Key parameter differences between configs (governance_strictness, cooperation_bias, initial_agent_trust)

---

## v0.6 Features — Session Storage, Replay, and Comparison

### Session Storage

Every simulation run automatically saves a complete snapshot to
`sessions/<timestamp>_<name>/`.  Each session folder contains:

| File | Description |
|---|---|
| `session_metadata.json` | Full metadata: session ID, version, agent names, summary metrics |
| `session_summary.json` | Summary metrics only (trust, reflections, interactions, contradiction) |
| `multi_agent_state.json` | Both agents' complete final states |
| `state_history.csv` | Sentinel's per-turn affective history |
| `interaction_log.csv` | All agent-to-agent interactions |
| `agent_relationships.csv` | Trust summary |
| `narrative_log.md` | Story-form narrative |
| `oversight_log.csv` | Governance audit trail |
| `*.png` | All six visualisation plots |

`sessions/index.json` keeps a lightweight index of all sessions for fast listing.

### CLI — Replay a Session

```bash
# List all saved sessions
python replay_session.py --list

# Replay a session turn by turn (interactive)
python replay_session.py --session 20260315_213200_baseline

# Start from a specific turn
python replay_session.py --session 20260315_213200_baseline --turn 10

# Auto-play with 1-second delay between turns
python replay_session.py --session 20260315_213200_baseline --auto --delay 1.0
```

Each turn displays: room, action, event type, all affective metrics,
and any agent-to-agent interactions with outcomes and trust deltas.

### CLI — Compare Two Sessions

```bash
# Compare two sessions (prints to terminal + saves JSON)
python compare_sessions.py \
  --session-a 20260315_213200_baseline \
  --session-b 20260315_213400_run2

# Also write a markdown report
python compare_sessions.py \
  --session-a 20260315_213200_baseline \
  --session-b 20260315_213400_run2 \
  --markdown
```

The comparison covers: final trust values, reflection counts, cooperation/conflict
counts, final contradiction pressure, and Sentinel's final-row state history metrics.

Output files saved to `sessions/`:
- `comparison_<a>_vs_<b>.json`
- `comparison_<a>_vs_<b>.md` (with `--markdown`)

### Dashboard — v0.6 Features

The dashboard (`streamlit run dashboard.py`) now has **eight tabs**:

| Tab | Contents |
|---|---|
| **Overview** | Turn metrics, session metadata (when viewing a saved session), recent history, governance audit |
| **Agents** | Per-agent affective state, room, trust scores, goals, latest reflection |
| **Rooms** | All rooms with agent locations, stateful objects, available actions |
| **Memory** | Episodic memories, relational memories, reflection entries |
| **Interactions** | Agent interaction log with conflict/cooperation metrics |
| **Charts** | All six matplotlib plots inline |
| **Replay** | Turn slider + Prev/Next buttons; shows affective-state deltas per turn |
| **Compare** | Pick two sessions, view side-by-side comparison tables |

**Session selector** in the sidebar lets you switch between:
- `Latest (output/)` — always shows the most recent simulation run
- Any saved session ID — loads that session's archived data

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
