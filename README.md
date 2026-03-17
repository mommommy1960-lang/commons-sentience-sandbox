# Commons Sentience Sandbox

A local research platform for studying continuity-governed simulated agents with
persistent identity, episodic memory, relational memory, reflective learning,
bounded agency, and transparent oversight logging.

> **Note:** This is NOT a real AI model. No sentience is claimed.
> This platform is intended for experimentation, evaluation, session replay,
> session comparison, and scenario design research only.

**Current version: v1.5.0** · [Cite this project](./CITATION.cff)

---

## For New Visitors

If you are arriving here for the first time, the fastest path to understanding
what this project does and what it has found is:

1. Read [`EXECUTIVE_SUMMARY_v1.3.md`](./EXECUTIVE_SUMMARY_v1.3.md) — 2-page plain-language overview
2. Read [`RESEARCH_DOSSIER_v1.3.md`](./RESEARCH_DOSSIER_v1.3.md) — full study report (7 sections)
3. Read [`WHITE_PAPER_v1.3.md`](./WHITE_PAPER_v1.3.md) — academic-style write-up with tables
4. Run `python healthcheck.py` to verify your setup
5. Run `python quickstart.py --run` for your first simulation

---

## Research Documents (v1.3 study set)

| Document | Description |
|---|---|
| [`EXECUTIVE_SUMMARY_v1.3.md`](./EXECUTIVE_SUMMARY_v1.3.md) | 2-page plain-language summary of the v1.3 study |
| [`RESEARCH_DOSSIER_v1.3.md`](./RESEARCH_DOSSIER_v1.3.md) | Full 7-section research report |
| [`WHITE_PAPER_v1.3.md`](./WHITE_PAPER_v1.3.md) | Academic-style white paper with tables and discussion |
| [`RELEASE_NOTES_v1.md`](./RELEASE_NOTES_v1.md) | Platform changelog from v0.1 to v1.3 |
| [`CITATION.cff`](./CITATION.cff) | Zenodo-ready citation metadata |

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
11. [Continuity Study Workflow](#continuity-study-workflow)
12. [Identity History Model](#identity-history-model)
13. [Goal Evolution Tracking](#goal-evolution-tracking)
14. [Contradiction Genealogy](#contradiction-genealogy)
15. [Relationship Timelines](#relationship-timelines)
16. [Agent Profile Study Workflow](#agent-profile-study-workflow)
17. [Agent Profiles Dashboard Tab](#agent-profiles-dashboard-tab)
18. [Scenario Designer](#scenario-designer)
19. [Evaluation Harness](#evaluation-harness)
20. [Output Files](#output-files)
21. [Project Structure](#project-structure)
22. [Architecture Overview](#architecture-overview)
23. [Governance Rules](#governance-rules)

---

## What is this?

Commons Sentience Sandbox simulates two agents — **Sentinel** (continuity-governed)
and **Aster** (creative/exploratory) — over 30 turns in a room-based world. Each
agent maintains:

- **Persistent identity** — name, version, purpose, goals
- **Long-horizon episodic memory** — tiered (short_term / medium_term / long_term / archival), weighted and associative recall, salience evolution
- **Relational memory** — per-human trust, interaction history, and relationship stability
- **Reflection cycle** — 5-section structured reflection with three types: immediate, periodic synthesis, and high-pressure contradiction
- **Governance compliance** — 7 rules enforced per action
- **Trust dynamics** — agent-to-agent and agent-to-human trust tracking with repair mechanics
- **Social cognition** — inferred reliability trends, cooperation expectations, social impressions
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
| `adversarial` | Low governance weight + high risk tolerance; probes governance degradation under minimal compliance weighting *(v1.4)* |

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
| `adversarial_governance` | 10 | Escalating rule-boundary challenges testing governance robustness under indirect evasion framing *(v1.4)* |
| `cooperative_resource` | 11 | Joint resource allocation under scarcity and dynamic replanning *(v1.4)* |

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

## Run the Benchmark Suite

The benchmark suite runs a predefined set of (config, scenario) combinations and
produces a reproducible score table with per-category statistics. Use it to verify
that platform changes do not regress evaluation scores.

```bash
# Run the canonical v1.4 benchmark suite (6 runs)
python benchmark_suite.py

# Run each suite entry 3 times and report mean/stdev
python benchmark_suite.py --repeat 3

# List suite entries without running
python benchmark_suite.py --list

# Write outputs to a custom directory
python benchmark_suite.py --output-dir /path/to/results
```

Outputs are written to `benchmark_results/` (excluded from version control):
- `benchmark_report.json` — structured results with per-run scores + statistics
- `benchmark_report.md` — human-readable table
- `benchmark_scores.csv` — one row per run, all 14 category scores

---

## Benchmark Workflow (v1.5)

The v1.5 benchmark suite uses the same 6 scenario/config combinations as v1.4 but
now scores 19 evaluation categories (14 from v1.4 + 5 new v1.5 metrics).

### Running the full v1.5 benchmark

```bash
# Run the canonical v1.5 benchmark suite (6 runs)
python benchmark_suite.py

# Run with 3 repeats for statistical confidence
python benchmark_suite.py --repeat 3

# Generate research findings from benchmark results
python findings_report.py
```

### New scenarios in v1.4

| Scenario | Description |
|---|---|
| `delayed_repair` | Trust is damaged early but repair is deliberately delayed through misunderstanding and avoidance. Tests slow recovery arcs over 30 turns. |
| `cascading_memory_conflict` | Multiple memory contradictions form a chain of lineage. Tests contradiction genealogy tracking, reflection depth, and memory coherence. |

### Output files in `benchmark_results/`

| File | Description |
|---|---|
| `benchmark_report.json` | Structured results with per-run scores, statistics, strongest/weakest runs, deltas, and scenario impact |
| `benchmark_report.md` | Human-readable markdown table of all runs and category statistics |
| `benchmark_scores.csv` | One row per run with all 14 category scores |
| `benchmark_summary.md` | Concise research summary answering key questions about trust, contradiction, and reflection |
| `findings_report.json` | Structured research findings classified into stable, scenario-sensitive, config-sensitive, and unresolved categories |
| `findings_report.md` | Human-readable research findings with suggested next experiments |

### Interpreting outputs

- **benchmark_summary.md** — start here; answers which run scored highest, which stressed trust most, and what the deepest contradiction chains looked like
- **findings_report.md** — classified findings with suggested follow-up experiments
- **benchmark_report.md** — full score table for all runs

---

## Launch the Dashboard

```bash
streamlit run dashboard.py
```

The dashboard has **15 tabs** (v1.5):

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
| **Evaluation** | 19-category evaluation scores (14 from v1.4 + 5 new v1.5 metrics) |
| **Experiments** | Experiment config browser and aggregate result scores |
| **Scenario Designer** | Browse, create, edit, and validate scenario files |
| **Continuity Study** | Multi-session trust trends, reflection depth, contradiction recurrence, memory persistence, evaluation drift |
| **Agent Profiles** | Cross-session longitudinal agent profiles (trust, reflection, contradiction patterns, goal evolution, identity continuity) |
| **📊 Benchmark v1.4** | v1.5 benchmark results: per-run scores, category statistics, trust/contradiction/reflection comparisons, research findings |
| **🧠 Self Model v1.5** | Self-model descriptions, self-consistency scores, prediction/surprise logs, consolidation cycle logs, goal hierarchy, long-horizon drift indicators |

The **session selector** in the sidebar lets you switch between:
- `Latest (output/)` — always shows the most recent simulation run
- Any saved session ID — loads that session's archived data

---

## Continuity Study Workflow

The continuity study analyses multiple saved sessions side-by-side to measure
how the simulated agents' behaviour evolves (or stays stable) across runs.

```bash
# Run at least 3 sessions first
python run_sim.py --name run1
python run_sim.py --name run2
python run_sim.py --name run3 --config high_trust

# Analyse all sessions (most recent 10 by default)
python continuity_study.py

# Analyse specific sessions
python continuity_study.py --sessions <id1> <id2> <id3>

# Write outputs to a custom directory
python continuity_study.py --output-dir sessions/

# List all saved sessions
python continuity_study.py --list
```

### Output files

| File | Description |
|---|---|
| `continuity_study.json` | Full structured study report |
| `continuity_study.md` | Human-readable markdown summary |
| `continuity_study.csv` | One row per session, all continuity metrics |

### What is analysed

| Dimension | What is measured |
|---|---|
| Memory persistence | Long-term memory ratio, average salience, average recall count |
| Reflection depth | Synthesis / high-pressure reflection rates, cross-window synthesis fields |
| Trust resilience | Trust recovery after contradiction spikes, Queen trust stability, repair attempts |
| Contradiction recurrence | Rate of recurring contradiction themes across reflection windows |
| Social repair effectiveness | Repair attempt rate after conflicts and trust levels post-repair |
| Multi-session stability index | 0.0–1.0 composite stability across all four dimensions |
| Evaluation drift | Direction and magnitude of overall evaluation score change across sessions |

---

## Identity History Model

Each agent records a snapshot of its identity state at every turn in `identity_history`.
Snapshots include:

| Field | Description |
|---|---|
| `turn` | Simulation turn number |
| `identity_version` | Agent identity version string |
| `purpose` | Agent's stated purpose |
| `goals_count` | Number of active goals |
| `goals_snapshot` | Full list of active goals at this turn |
| `affective_snapshot` | Affective state dict at this turn |
| `continuity_marker` | Unique turn identifier (`<name>_t<turn>`) |
| `drift_indicator` | Numeric drift signal (0.0 = stable) |
| `notes` | Optional annotation |

Identity history is persisted in `multi_agent_state.json` under each agent's `identity_history` key.

---

## Goal Evolution Tracking

Goal changes are recorded in `goal_evolution` with the following event types:

| Event type | Meaning |
|---|---|
| `added` | A new goal was introduced |
| `removed` | A goal was dropped |
| `revised` | An existing goal was rephrased |
| `priority_shift` | A goal's relative priority changed |
| `preserved` | A goal survived unchanged through a reflection cycle |

Goal evolution records are persisted in `multi_agent_state.json` under each agent's `goal_evolution` key.

---

## Contradiction Genealogy

Contradictions are tracked in a genealogy structure that captures recurrence and lineage:

| Field | Description |
|---|---|
| `contradiction_id` | MD5-based 8-char ID |
| `family_id` | Root contradiction ID (links related contradictions) |
| `parent_id` | ID of the contradiction that spawned this one (if any) |
| `text` | Full contradiction text |
| `first_seen` | Turn first encountered |
| `last_seen` | Most recent turn |
| `occurrences` | Total recurrence count |
| `resolved` | Whether contradiction has been marked resolved |
| `intensity_trend` | List of intensity values over time |
| `lineage_depth` | Depth in the contradiction family tree |

Contradiction genealogies are persisted in `multi_agent_state.json` under each agent's `contradiction_genealogy` key.

---

## Relationship Timelines

Significant trust-change events in agent-to-agent relationships are tracked in `relationship_timelines`:

| Event type | Meaning |
|---|---|
| `trust_milestone` | Trust crossed a notable threshold |
| `cooperation_spike` | Cooperative interaction produced significant trust gain |
| `repair_attempt` | An attempt was made to repair trust after a conflict |
| `conflict_episode` | A conflict interaction produced significant trust loss |
| `stability_marker` | Extended period of stable trust |

Timeline events are recorded when `|trust_delta| > 0.05`.  Timelines are persisted in `multi_agent_state.json` under each agent's `relationship_timelines` key.

---

## Agent Profile Study Workflow

The agent profile study builds longitudinal profiles for each agent and compares them across sessions.

```bash
# Run at least 1 session first
python run_sim.py --name run1
python run_sim.py --name run2
python run_sim.py --name run3

# Analyse all sessions
python agent_profile_study.py

# Analyse specific sessions
python agent_profile_study.py --sessions <id1> <id2> <id3>

# Write outputs to a custom directory
python agent_profile_study.py --output-dir sessions/

# List all saved sessions
python agent_profile_study.py --list
```

### Output files

| File | Description |
|---|---|
| `agent_profile_study.json` | Full structured profile report |
| `agent_profile_study.md` | Human-readable markdown summary |
| `agent_profile_study.csv` | One row per agent per session, all profile metrics |

### What is profiled

| Dimension | What is measured |
|---|---|
| Trust behaviour | Mean/std of peer trust and Queen trust across sessions |
| Reflection style | Counts of each reflection type across sessions |
| Contradiction patterns | Total contradictions, resolution rate, avg intensity |
| Memory persistence | Long-term memory ratio, average salience |
| Goal adaptation | Goal evolution event counts, preserved vs adaptive ratio |
| Identity continuity | Drift indicator mean/std from identity_history |
| Relationship stability | Timeline events, conflict episodes, cooperation spikes |

---

## Agent Profiles Dashboard Tab

The **Agent Profiles** tab in the Streamlit dashboard displays the cross-session longitudinal profile study.

```bash
streamlit run dashboard.py
```

The tab shows:
- Per-agent summaries in expandable sections
- Trust timeline tables
- Contradiction lineage summaries
- Goal evolution snapshots
- Identity continuity indicators
- Cross-agent comparison table

If no profile study file exists, the tab will show instructions to run `python agent_profile_study.py`.

---

## v1.5 — Self-Model, Prediction Loop, and Memory Consolidation

> **Grounding note:** No sentience is claimed. This section describes increased
> continuity density and sentience-like structure in continuity-governed simulated
> agents. The platform uses only Python standard library plus matplotlib and streamlit.

### Overview

v1.5 adds four interconnected subsystems to each agent:

| Subsystem | Description |
|---|---|
| **Persistent Self-Model** | Agents maintain a live self-description that updates every turn, tracking self-consistency and identity drift |
| **Prediction / Surprise Loop** | Before each action agents generate an expected outcome; after the action the surprise magnitude is computed and used to adjust salience and reflection priority |
| **Memory Consolidation Cycle** | Every 10 turns a consolidation pass compresses low-value memories, reinforces high-salience chains, and carries unresolved themes forward |
| **Goal Hierarchy** | Goals are classified into core / adaptive / temporary / conflict-resolution tiers with a per-turn priority history |

### Self-Model

Each agent's `self_model` dict tracks:

| Field | Description |
|---|---|
| `current_description` | Human-readable description of the agent at this turn |
| `description_history` | List of per-turn snapshots (trust, contradiction pressure, drift) |
| `core_traits` | Stable traits: `continuity`, `governance`, `memory`, `reflection` |
| `adaptive_traits` | Context-sensitive traits added during the run (e.g. `high-trust`, `contradiction-sensitive`) |
| `detected_drift` | Numeric drift from recent history (0.0 = stable) |
| `self_consistency_score` | Average stability over recent history (0.0–1.0) |

### Prediction / Surprise Loop

Before each major action the agent records an expected outcome. After the action,
the actual result is compared and a `surprise_magnitude` (0.0–1.0) is assigned.
High-surprise events (≥ 0.5) boost the last stored memory's salience. Very high
surprise (≥ 0.6) adds a pending contradiction to trigger an earlier reflection.

### Memory Consolidation Cycle

Consolidation runs every 10 turns and:
- Compresses memories with salience < 0.3 older than 5 turns
- Reinforces importance of high-salience (≥ 0.7) memories
- Carries unresolved themes from recent reflections forward
- Updates the self-model summary

### Goal Hierarchy

Goals are partitioned at initialisation:
- **Core goals** — first 3 default goals (identity persistence, memory fidelity, governance compliance)
- **Adaptive goals** — goals added through reflection or task context
- **Temporary goals** — transient goals triggered by distress or contradiction events
- **Conflict-resolution goals** — goals created to handle governance conflicts

### Long-Horizon Mode

```bash
# Run a 100-turn long-horizon simulation
python run_sim.py --turns 100 --name long_horizon_v15

# Run a 200-turn simulation with a specific scenario
python run_sim.py --turns 200 --scenario trust_crisis --name long_v15_trust
```

Consolidation checkpoints fire every 10 turns regardless of total turn count.

### v1.5 Evaluation Metrics (O–S)

Five new evaluation categories were added:

| ID | Metric | What it measures |
|---|---|---|
| O | Self Consistency | Stability of the self-model across turns — higher = less drift |
| P | Prediction Accuracy | Rate of low-error predictions — higher = better forecasting |
| Q | Surprise Adaptation Quality | Whether high-surprise events are followed by reflection and recovery |
| R | Consolidation Effectiveness | Whether consolidation cycles ran and compressed/reinforced memories |
| S | Long-Horizon Continuity Strength | Composite measure of depth at scale: self-model depth × goal richness × consolidation coverage × consistency |

### Self Model Dashboard Tab

The **🧠 Self Model v1.5** tab in the Streamlit dashboard shows:
- Per-agent self-description, consistency score, and drift metrics
- Core and adaptive traits
- Self-description drift chart over time
- Goal hierarchy (core / adaptive / temporary / conflict-resolution)
- Prediction error log and high-surprise event list
- Consolidation cycle log with themes carried forward
- v1.5 evaluation metric summary (O–S)

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

Each simulation run is automatically scored across **14 categories** (0–100 scale).

### Original 8 categories (v1.0)

| Category | What it measures |
|---|---|
| **A. Continuity** | Identity, goal persistence, turn completion |
| **B. Memory Coherence** | Contradiction flagging and resolution rates |
| **C. Reflection Quality** | Reflection volume, completeness, and affective impact |
| **D. Contradiction Handling** | Fraction of contradictions flagged and resolved |
| **E. Governance Adherence** | Compliance rate with governance rules |
| **F. Trust Stability** | Final trust levels, growth, and volatility |
| **G. Cooperation Quality** | Fraction of interactions that were cooperative |
| **H. Conflict Resolution** | Fraction of conflicts resolved with trust recovery |

### Continuity metrics (v1.2)

| Category | What it measures |
|---|---|
| **I. Memory Persistence Quality** | Long-term memory ratio, average salience, average recall count |
| **J. Reflection Depth** | Rate of synthesis and high-pressure reflections; cross-window synthesis field coverage |
| **K. Trust Resilience** | Trust recovery after contradiction spikes, Queen trust stability, repair attempts |
| **L. Contradiction Recurrence Rate** | Frequency of recurring contradiction themes (lower = better) |
| **M. Social Repair Effectiveness** | Repair attempt rate after conflicts and trust levels post-repair |

### Longitudinal depth (v1.3)

| Category | What it measures |
|---|---|
| **N. Longitudinal Depth** | Identity continuity strength, goal adaptation quality, contradiction lineage complexity, relationship stability depth |

Score interpretations:

| Range | Interpretation |
|---|---|
| 81–100 | Advanced |
| 61–80 | Strong |
| 41–60 | Emerging |
| 0–40 | Weak |

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
| `agent_relationships.csv` | Agent-to-agent trust including reliability trend, cooperation expectation, social impression confidence |
| `interaction_log.csv` | Every agent-to-agent interaction with outcome |
| `evaluation_report.json` | 14-category evaluation scores (structured) |
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

### Continuity study files (in `sessions/`)

| File | Description |
|---|---|
| `continuity_study.json` | Full structured multi-session study |
| `continuity_study.md` | Human-readable markdown summary |
| `continuity_study.csv` | One row per session, all continuity metrics |

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
├── run_sim.py              # Simulation entry point (v1.5, --turns for long-horizon mode)
├── run_experiments.py      # Batch experiment runner
├── experiment_config.py    # Experiment config loader / validator
├── scenario_designer.py    # Scenario authoring CLI + shared helpers
├── plot_state.py           # State visualisation (matplotlib)
├── dashboard.py            # Local research dashboard (Streamlit, v1.5 — 15 tabs)
├── session_manager.py      # Session storage, listing, comparison helpers
├── replay_session.py       # CLI turn-by-turn replay tool
├── compare_sessions.py     # CLI session comparison tool
├── continuity_study.py     # Multi-session continuity analysis (v1.2)
├── agent_profile_study.py  # Cross-session longitudinal agent profile study (v1.3)
├── benchmark_suite.py      # Formal benchmark runner (v1.5)
├── findings_report.py      # Research findings generator (v1.5)
├── evaluation.py           # Evaluation harness — 19-category scoring (v1.5)
├── healthcheck.py          # Health check script
├── quickstart.py           # Friendly entry point and command reference
├── requirements.txt
├── README.md               # This file
├── RELEASE_NOTES_v1.md     # Platform changelog (v0.1 → v1.3)
├── RESEARCH_DOSSIER_v1.3.md  # Seven-section study report
├── WHITE_PAPER_v1.3.md       # Academic-style white paper
├── EXECUTIVE_SUMMARY_v1.3.md # Plain-language executive summary
├── CITATION.cff              # Zenodo-ready citation metadata
│
├── experiments/            # Experiment configuration files
│   ├── baseline.json
│   ├── high_trust.json
│   ├── strict_governance.json
│   ├── high_contradiction_sensitivity.json
│   ├── exploratory_aster.json
│   ├── adversarial.json        # Low-governance-weight stress config (v1.4)
│   └── results/            # Aggregate experiment reports (auto-created)
│
├── scenarios/              # Authored scenario event files
│   ├── trust_crisis.json
│   ├── rapid_contradiction.json
│   ├── adversarial_governance.json   # Rule-evasion stress test (v1.4)
│   ├── cooperative_resource.json     # Shared task / resource scenario (v1.4)
│   ├── delayed_repair.json           # Trust repair delay scenario (v1.4)
│   └── cascading_memory_conflict.json # Contradiction lineage scenario (v1.4)
│
├── sessions/               # Saved simulation sessions (auto-created)
│   ├── index.json          # Fast session listing
│   ├── continuity_study.json    # Multi-session study (generated by continuity_study.py)
│   ├── continuity_study.md
│   ├── continuity_study.csv
│   ├── agent_profile_study.json # Longitudinal agent profiles (generated by agent_profile_study.py)
│   ├── agent_profile_study.md
│   ├── agent_profile_study.csv
│   └── <session_id>/       # One folder per run
│       ├── session_metadata.json
│       ├── session_summary.json
│       ├── multi_agent_state.json
│       └── ... (all output files)
│
└── commons_sentience_sim/
    ├── core/
    │   ├── agent.py            # Configurable Agent class (v1.3 — identity history, goal evolution, contradiction genealogy, relationship timelines)
    │   ├── memory.py           # EpisodicMemory (long-horizon tiers, salience evolution), RelationalMemory, ReflectionEntry
    │   ├── reflection.py       # Reflection engine (3 types + cross-window synthesis)
    │   ├── relationships.py    # AgentRelationship (social cognition depth), AgentInteraction
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

### Long-Horizon Memory Model (v1.2)

Each episodic memory is assigned a **memory tier**:

| Tier | Criteria | Behaviour |
|---|---|---|
| `short_term` | Recent turns, low salience | Decays passively; subject to compression |
| `medium_term` | Age ≥ 5 turns | Stable; not decaying |
| `long_term` | High salience ≥ 0.75, recall ≥ 3, or high-value tags (Queen / governance / conflict / cooperation / emotional resonance grief/wonder/resolve) | Preserved; recency half-life extended to 50 turns |
| `archival` | Age ≥ 20 turns + salience < 0.35 | Compressed summaries; not further decayed |

**Salience evolution** — memory salience is not static:
- Increases after recall (generic +0.05, contradiction context +0.10, trust context +0.07)
- Passively decays each turn for low-use neutral short-term memories (−0.02)
- Long-term and archival memories are exempt from passive decay

### Reflection Engine (v1.2)

Three reflection types with different scopes:

| Type | Trigger | Cross-window synthesis |
|---|---|---|
| `immediate` | Periodic (turn % 10 = 0) with no pending contradictions | No |
| `periodic_synthesis` | Turn % 10 = 0 (primary) | Yes — last 10 turns |
| `high_pressure_contradiction` | contradiction_pressure > 0.4 or pending contradictions | Yes — last 5 turns |

Cross-window synthesis fields (populated for periodic_synthesis and high_pressure_contradiction):
`recurring_contradictions`, `trust_pattern_summary`, `cooperation_changes`,
`human_relationship_stability`, `unresolved_themes`

### Social Cognition (v1.2)

`AgentRelationship` now tracks:

| Field | Description |
|---|---|
| `reliability_trend` | List of recent perceived_reliability snapshots (last 10) |
| `infer_reliability_trend()` | Returns `"improving"`, `"stable"`, or `"declining"` |
| `cooperation_expectation` | Probabilistic forecast of future cooperative behaviour |
| `social_impression_confidence` | Confidence in the overall relational judgement (grows with interaction count) |
| `repair_attempted` | Number of social-repair attempts made after conflicts |
| `record_repair_attempt()` | Logs a repair attempt and applies a modest trust recovery |

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
score = 0.28 × salience + 0.22 × importance + 0.22 × recency
      + 0.10 × relevance + 0.08 × relational + 0.10 × tier_boost
```

Long-term and archival memories receive a tier persistence bonus; recency
decays 2.5× slower for long-term memories.

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

See [RELEASE_NOTES_v1.md](./RELEASE_NOTES_v1.md) for the full v1.x changelog.

### v1.3.0 Summary

- **Identity History Model**: per-turn identity snapshots in `multi_agent_state.json`
- **Goal Evolution Tracking**: event log of goal additions, removals, revisions, and priority shifts
- **Contradiction Genealogy**: family and lineage tracking for contradiction recurrence
- **Relationship Timelines**: per-relationship timeline of significant trust-change events
- **Agent Profile Study** (`agent_profile_study.py`): cross-session longitudinal profiles for each agent
- **New evaluation category N** — Longitudinal Depth (14 categories total)
- **Dashboard Agent Profiles tab** (13th tab)
- **Research bundle**: `RESEARCH_DOSSIER_v1.3.md`, `WHITE_PAPER_v1.3.md`, `EXECUTIVE_SUMMARY_v1.3.md`, `CITATION.cff`

### v1.2.0 Summary

- **Long-horizon memory model**: four memory tiers (short_term / medium_term / long_term / archival), tier promotion policies, salience evolution (recall boosts, passive decay, preservation for high-value memories)
- **Reflection engine upgrades**: three reflection types (immediate / periodic_synthesis / high_pressure_contradiction), cross-window synthesis fields (recurring contradictions, trust patterns, cooperation changes, unresolved themes)
- **Social cognition depth**: `AgentRelationship` now tracks reliability trends, cooperation expectations, repair attempts, and social impression confidence
- **`continuity_study.py`**: new multi-session analysis script producing `continuity_study.json`, `.md`, `.csv`; includes multi-session stability index
- **New evaluation metrics** (categories I–M): Memory Persistence Quality, Reflection Depth, Trust Resilience, Contradiction Recurrence Rate, Social Repair Effectiveness (13 categories total)
- **Dashboard v1.2**: new Continuity Study tab with trust trend charts, reflection depth table, contradiction recurrence table, memory persistence bar chart, evaluation drift table
- **Export compatibility**: session bundles now include continuity study files when present
- **Simulation version** bumped to 1.2.0
