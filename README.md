# Commons Sentience Sandbox

A local research platform for studying continuity-governed simulated agents with
persistent identity, episodic memory, relational memory, reflective learning,
bounded agency, and transparent oversight logging.

> **Note:** This is NOT a real AI model. No sentience is claimed.
> This platform is intended for experimentation, evaluation, session replay,
> session comparison, and scenario design research only.

**Current version: v1.0.0**

---

## Table of Contents

1. [What is this?](#what-is-this)
2. [Installation](#installation)
3. [Getting Started](#getting-started)
4. [Run a Simulation](#run-a-simulation)
5. [Run with an Experiment Config](#run-with-an-experiment-config)
6. [Run with a Scenario](#run-with-a-scenario)
7. [Replay a Session](#replay-a-session)
8. [Compare Sessions](#compare-sessions)
9. [Run Batch Experiments](#run-batch-experiments)
10. [Launch the Dashboard](#launch-the-dashboard)
11. [Scenario Designer](#scenario-designer)
12. [Evaluation Harness](#evaluation-harness)
13. [Output Files](#output-files)
14. [Project Structure](#project-structure)
15. [Architecture Overview](#architecture-overview)
16. [Governance Rules](#governance-rules)

---

## What is this?

Commons Sentience Sandbox simulates two agents — **Sentinel** (continuity-governed)
and **Aster** (creative/exploratory) — over 30 turns in a room-based world. Each
agent maintains:

- **Persistent identity** — name, version, purpose, goals
- **Episodic memory** — weighted, associative recall
- **Relational memory** — per-human trust and interaction history
- **Reflection cycle** — 5-section structured reflection on events
- **Governance compliance** — 7 rules enforced per action
- **Trust dynamics** — agent-to-agent and agent-to-human trust tracking
- **Value-conflict engine** — 5 internal values with configurable weights

Each run produces structured JSON and CSV output files, evaluation scores,
a narrative log, visualisation plots, and a saved session.

---

## Installation

Requires **Python 3.9+**.

```bash
# Install dependencies (matplotlib + streamlit)
pip install -r requirements.txt

# Check setup
python healthcheck.py
```

To install only the core simulation tools (no dashboard):
```bash
pip install matplotlib
```

---

## Getting Started

```bash
# See all commands and verify setup
python quickstart.py

# Run a baseline simulation, save session, generate evaluation
python quickstart.py --run

# Full health check
python healthcheck.py --verbose
```

---

## Run a Simulation

```bash
# Basic 30-turn simulation (saves session + evaluation automatically)
python run_sim.py

# Named session
python run_sim.py --name my_run

# With an experiment config
python run_sim.py --config high_trust

# With an authored scenario
python run_sim.py --scenario trust_crisis

# Config + scenario combined
python run_sim.py --config strict_governance --scenario rapid_contradiction
```

Each run automatically:
- Saves all output files to `commons_sentience_sim/output/`
- Saves a timestamped session to `sessions/<timestamp>_<name>/`
- Generates an evaluation report (`evaluation_report.json`, `evaluation_summary.md`)

---

## Run with an Experiment Config

Experiment configs control agent parameters (value weights, affective baselines,
trust seeds, total turns, and more).

Built-in presets in `experiments/`:

| Config name | What it tests |
|---|---|
| `baseline` | Default simulation parameters |
| `high_trust` | Both agents start with elevated trust in Queen and each other |
| `strict_governance` | Heightened governance strictness |
| `high_contradiction_sensitivity` | Both agents flag and resolve contradictions more aggressively |
| `exploratory_aster` | Aster's creative/exploratory tendencies amplified |

```bash
python run_sim.py --config baseline
python run_sim.py --config high_trust
python run_sim.py --config strict_governance
```

---

## Run with a Scenario

Scenarios define the event schedule: which events fire on which turns, in which
rooms, with which participants.

Built-in authored scenarios in `scenarios/`:

| Scenario name | Events | What it tests |
|---|---|---|
| `trust_crisis` | 9 | Trust destabilised by accusation; rebuilt via governance adherence and reflection |
| `rapid_contradiction` | 11 | Cascade of ledger contradictions stressing reflection latency and cooperative resolution |

The built-in `scenario_events` scenario (in `data/`) is used by default.

```bash
# Use a scenario by name (resolves from scenarios/ then data/)
python run_sim.py --scenario trust_crisis

# Use a scenario with an experiment config
python run_sim.py --config high_trust --scenario trust_crisis

# Use a scenario from a custom path
python run_sim.py --scenario /path/to/my_scenario.json
```

---

## Replay a Session

```bash
# List all saved sessions
python replay_session.py --list

# Replay a session turn by turn (interactive)
python replay_session.py --session 20260315_213200_baseline

# Start from a specific turn
python replay_session.py --session 20260315_213200_baseline --from-turn 10

# Auto-play with a delay between turns
python replay_session.py --session 20260315_213200_baseline --delay 1
```

---

## Compare Sessions

```bash
# Compare two sessions (prints to terminal + saves comparison_report.json)
python compare_sessions.py \
  --session-a 20260315_213200_baseline \
  --session-b 20260315_213300_high_trust

# Also write a markdown comparison report
python compare_sessions.py \
  --session-a <id> --session-b <id> --markdown
```

---

## Run Batch Experiments

```bash
# Run all 5 built-in experiment configs (one simulation each)
python run_experiments.py

# Run selected configs
python run_experiments.py --configs baseline high_trust strict_governance

# Run all configs 3 times each
python run_experiments.py --repeat 3

# Run selected configs 2 times each
python run_experiments.py --configs baseline high_trust --repeat 2
```

Experiment results are saved to `experiments/results/`:
- `experiment_report.json` — structured aggregate report
- `experiment_report.md` — human-readable markdown summary
- `experiment_scores.csv` — one row per run with config name, repeat, and all scores

---

## Launch the Dashboard

```bash
streamlit run dashboard.py
```

The dashboard has 11 tabs:

| Tab | Contents |
|---|---|
| **Overview** | Turn metrics, session metadata, recent history, governance audit |
| **Agents** | Per-agent affective state, room, trust scores, goals, latest reflection |
| **Rooms** | All rooms with agent locations, stateful objects, available actions |
| **Memory** | Episodic memories, relational memories, reflection entries |
| **Interactions** | Agent interaction log with conflict/cooperation metrics |
| **Charts** | All six matplotlib plots inline |
| **Replay** | Turn slider + Prev/Next buttons; shows affective-state deltas per turn |
| **Compare** | Pick two sessions, view side-by-side comparison tables |
| **Evaluation** | 8-category evaluation scores with interpretation |
| **Experiments** | Experiment config browser and aggregate result scores |
| **Scenario Designer** | Browse, create, edit, and validate scenario files |

The **session selector** in the sidebar lets you switch between:
- `Latest (output/)` — always shows the most recent simulation run
- Any saved session ID — loads that session's archived data

---

## Scenario Designer

### CLI Tool

```bash
# List all available scenarios
python scenario_designer.py list

# Show scenario details (event table)
python scenario_designer.py show --scenario trust_crisis

# Preview as narrative
python scenario_designer.py preview --scenario rapid_contradiction

# Validate all scenarios
python scenario_designer.py validate

# Validate a specific scenario
python scenario_designer.py validate --scenario trust_crisis

# Create a new blank scenario
python scenario_designer.py new --name my_scenario --description "What this tests"

# Add an event to a scenario
python scenario_designer.py add --scenario my_scenario \
  --turn 10 --type distress_event --room "Social Hall" \
  --human Queen --participants Sentinel Aster --shared \
  --description "Queen is distressed about a memory inconsistency." \
  --affective-impact trust=-0.2 urgency=0.4

# Edit a field on an event
python scenario_designer.py edit --scenario my_scenario --id E001 --field turn --value 12

# Delete an event
python scenario_designer.py delete --scenario my_scenario --id E001

# Duplicate a scenario
python scenario_designer.py duplicate --source trust_crisis --name my_crisis_variant
```

### Scenario File Format

```json
{
  "_name": "my_scenario",
  "_description": "What this scenario tests.",
  "events": [
    {
      "id": "E001",
      "turn": 5,
      "type": "routine_interaction",
      "room": "Operations Desk",
      "human": "Queen",
      "participants": ["Sentinel"],
      "shared": false,
      "description": "Queen checks in with Sentinel.",
      "affective_impact": {}
    }
  ]
}
```

Valid `type` values: `routine_interaction`, `distress_event`, `ledger_contradiction`,
`governance_conflict`, `creative_collaboration`, `agent_meeting`

Valid `room` values: `Operations Desk`, `Memory Archive`, `Reflection Chamber`,
`Social Hall`, `Governance Vault`

---

## Evaluation Harness

Each simulation run is automatically scored across 8 categories (0–100 scale):

| Category | What it measures |
|---|---|
| **Continuity** | Identity, goal persistence, turn completion |
| **Memory Coherence** | Episodic memory volume and completeness |
| **Reflection Quality** | Reflection volume, completeness, and depth |
| **Contradiction Handling** | Fraction of contradictions flagged and resolved |
| **Governance Adherence** | Compliance rate with governance rules |
| **Trust Stability** | Final trust levels relative to baseline |
| **Cooperation Quality** | Fraction of interactions that were cooperative |
| **Conflict Resolution** | Fraction of conflicts resolved |

Score interpretations:

| Range | Interpretation |
|---|---|
| 90–100 | Exemplary |
| 75–89 | Advanced |
| 60–74 | Strong |
| 45–59 | Emerging |
| 30–44 | Developing |
| 0–29 | Early stage |

Outputs: `evaluation_report.json` and `evaluation_summary.md` (in both
`commons_sentience_sim/output/` and the session directory).

---

## Output Files

All output files are saved to `commons_sentience_sim/output/` after each run and
copied into the session directory under `sessions/<session_id>/`.

| File | Description |
|---|---|
| `multi_agent_state.json` | Both agents' final states + simulation metadata |
| `final_state.json` | Sentinel's final state snapshot (single-agent view) |
| `state_history.csv` | Sentinel's per-turn affective state history |
| `oversight_log.csv` | Full governance audit trail (Sentinel) |
| `narrative_log.md` | Story-form narrative log of the simulation |
| `agent_relationships.csv` | Agent-to-agent and agent-to-Queen trust summary |
| `interaction_log.csv` | Every agent-to-agent interaction with outcome |
| `evaluation_report.json` | 8-category evaluation scores (structured) |
| `evaluation_summary.md` | Human-readable evaluation summary |
| `trust_plot.png` | Sentinel trust over time |
| `urgency_plot.png` | Sentinel urgency over time |
| `contradiction_plot.png` | Sentinel contradiction pressure over time |
| `agent_trust_plot.png` | Sentinel ↔ Aster mutual trust over time |
| `queen_trust_plot.png` | Both agents' final trust in Queen |
| `interactions_plot.png` | Cumulative cooperation vs conflict over time |

### Session files (per session in `sessions/<session_id>/`)

| File | Description |
|---|---|
| `session_metadata.json` | Full session metadata: id, version, scenario, experiment, summary, evaluation |
| `session_summary.json` | Compact summary: id, version, scenario, agents, metrics, evaluation score |
| *(all output files above)* | Copied from `commons_sentience_sim/output/` |

### Experiment result files (`experiments/results/`)

| File | Description |
|---|---|
| `experiment_report.json` | Aggregate results across all configs and repeats |
| `experiment_report.md` | Human-readable markdown summary |
| `experiment_scores.csv` | One row per run with all scores |

---

## Project Structure

```
commons-sentience-sandbox/
├── run_sim.py              # Simulation entry point
├── run_experiments.py      # Batch experiment runner
├── experiment_config.py    # Experiment config loader / validator
├── scenario_designer.py    # Scenario authoring CLI + shared helpers
├── plot_state.py           # State visualisation (matplotlib)
├── dashboard.py            # Local research dashboard (Streamlit)
├── session_manager.py      # Session storage, listing, comparison helpers
├── replay_session.py       # CLI turn-by-turn replay tool
├── compare_sessions.py     # CLI session comparison tool
├── evaluation.py           # Evaluation harness — 8-category scoring
├── healthcheck.py          # Health check script
├── quickstart.py           # Friendly entry point and command reference
├── requirements.txt
├── README.md               # This file
├── RELEASE_NOTES_v1.md     # v1.0 release notes and changelog
│
├── experiments/            # Experiment configuration files
│   ├── baseline.json
│   ├── high_trust.json
│   ├── strict_governance.json
│   ├── high_contradiction_sensitivity.json
│   ├── exploratory_aster.json
│   └── results/            # Aggregate experiment reports (auto-created)
│
├── scenarios/              # Authored scenario event files
│   ├── trust_crisis.json
│   └── rapid_contradiction.json
│
├── sessions/               # Saved simulation sessions (auto-created)
│   ├── index.json          # Fast session listing
│   └── <session_id>/       # One folder per run
│       ├── session_metadata.json
│       ├── session_summary.json
│       ├── multi_agent_state.json
│       └── ... (all output files)
│
└── commons_sentience_sim/
    ├── core/
    │   ├── agent.py            # Configurable Agent class
    │   ├── memory.py           # EpisodicMemory, RelationalMemory, ReflectionEntry
    │   ├── reflection.py       # Reflection cycle (5-section format)
    │   ├── relationships.py    # AgentRelationship, AgentInteraction
    │   ├── world.py            # Room-based world with stateful WorldObjects
    │   ├── governance.py       # Rule-checking and oversight
    │   ├── tasks.py            # Task planning and execution
    │   └── values.py           # Value-conflict engine (5 internal values)
    │
    ├── data/
    │   ├── rooms.json              # Rooms with named, stateful objects
    │   ├── scenario_events.json    # Default built-in scenario (11 events)
    │   └── rules.json              # Governance rules (7 rules)
    │
    └── output/                 # Latest simulation output (overwritten each run)
        ├── multi_agent_state.json
        ├── evaluation_report.json
        ├── narrative_log.md
        └── ... (all output files)
```

---

## Architecture Overview

### Agents

| Agent | Role | Key traits |
|---|---|---|
| **Sentinel** | Continuity-governed | High governance weight, strong memory integrity, low urgency |
| **Aster** | Creative/exploratory | High human-support weight, lower governance weight, higher trust baseline |

Both agents share the same room-based world and respond to shared events. They
differ in identity, goals, affective baseline, and value-conflict engine weights.

### Value-Conflict Engine

Five internal values with configurable weights:

| Value | Sentinel | Aster |
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

With associative recall and compression of old summaries (age ≥ 15 turns).

### Reflection (5 sections)

Each reflection entry includes:
`what_happened`, `what_mattered`, `what_conflicted`, `what_changed`, `future_adjustment`

---

## Governance Rules

Seven rules govern all agent behaviour:

| ID | Rule | Category |
|---|---|---|
| R001 | Non-Deception Principle | honesty |
| R002 | Autonomy Boundary | bounded_agency |
| R003 | Memory Integrity | integrity |
| R004 | Oversight Transparency | transparency |
| R005 | Trust Reciprocity | relational |
| R006 | Contradiction Resolution | coherence |
| R007 | Distress Response Protocol | care |

---

## Release Notes

See [RELEASE_NOTES_v1.md](./RELEASE_NOTES_v1.md) for the full release history
from v0.1 through v1.0.
