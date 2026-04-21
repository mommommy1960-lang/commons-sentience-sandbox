# Commons Sentience Sandbox

A local research platform for studying continuity-governed simulated agents with
persistent identity, episodic memory, relational memory, reflective learning,
bounded agency, and transparent oversight logging.

> **Note:** This is NOT a real AI model. No sentience is claimed.
> This platform is intended for experimentation, evaluation, session replay,
> session comparison, and scenario design research only.

**Current version: v1.9.0** · [Cite this project](./CITATION.cff)

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

## v1.6 — Persistent World State and Cross-Run Carryover

> **Grounding note:** No sentience is claimed. This section describes cross-run
> state persistence in continuity-governed simulated agents.

v1.6 adds persistent world state and cross-run carryover:

| Feature | Description |
|---|---|
| **Persistent World State** | `world_state.json` saved after every run capturing room conditions, tensions, unresolved contradictions, and relationship climate |
| **Cross-Run Carryover** | `--continue-from <session_id>` restores long-term memories, contradictions, relationships, self-model, and world state |
| **Endogenous Drives** | `curiosity`, `maintenance_urge`, `repair_urge`, `investigation_urge`, `continuity_loop_urge` updated each turn and driving autonomous actions |
| **Self-Initiated Loops** | Agents autonomously trigger maintenance, repair, investigation, and exploration based on drive thresholds |

```bash
# Continue from a prior session
python run_sim.py --continue-from 20240317_150000_my_run

# Start a new run and name it
python run_sim.py --name my_named_run
```

---

## v1.7 — Counterfactual Planning and Future Modeling

> **Grounding note:** No sentience is claimed. v1.7 increases future-modeling
> capacity and sentience-like continuity in continuity-governed simulated agents.
> The platform uses only Python standard library plus matplotlib and streamlit.

### Overview

v1.7 adds a complete counterfactual planning layer giving agents the ability to
simulate possible futures before acting, compare outcomes, and form self-authored
plans based on counterfactual reasoning.

| Subsystem | Description |
|---|---|
| **Counterfactual Planning Layer** | Before each turn agents generate candidate actions and simulate outcomes across trust, contradiction, governance, and continuity dimensions |
| **Internal Simulation Log** | Each planning cycle is stored with predicted and actual outcomes for post-hoc evaluation |
| **Self-Authored Future Plans** | Agents generate medium-horizon multi-step plans that persist and advance across turns |
| **Counterfactual Evaluation** | After action execution, predicted outcomes are compared to actual results to compute planning accuracy |
| **Multi-Step Planning** | Plans track stage progress and are abandoned/revised if conditions change |
| **Cross-Run Plan Carryover** | Active plans persist across `--continue-from` runs |

### Counterfactual Candidate Actions

Each turn the agent considers up to 4 candidate actions:

| Action | Description |
|---|---|
| `repair_trust` | Proactively repair trust through consistent behaviour |
| `resolve_contradiction` | Address a pending contradiction directly |
| `consolidate_memory` | Run a memory consolidation cycle |
| `defer_action` | Defer action and observe the environment |
| `cooperative_engagement` | Engage cooperatively with other agents |
| `governance_check` | Verify compliance with all active governance rules |
| `self_reflection` | Perform a focused self-reflection cycle |
| `investigate_theme` | Investigate an unresolved theme from prior turns |

Each candidate tracks: predicted trust effect, contradiction effect, governance risk,
continuity impact, best-case narrative, worst-case narrative, uncertainty, and
composite score.  The highest-scoring candidate is selected.

### Internal Simulation Log

Each `InternalSimulationEntry` records:

| Field | Description |
|---|---|
| `turn` | Simulation turn |
| `context` | Agent state summary at planning time |
| `candidates` | All candidate actions with predicted scores |
| `selected_action` | The chosen action |
| `predicted_outcome` | Best-case narrative for the selected action |
| `actual_outcome` | What actually happened (filled post-action) |
| `planning_accuracy` | How closely prediction matched reality (0–1) |
| `uncertainty_level` | Aggregate planning uncertainty |
| `was_better_than_rejected` | Whether the chosen action outperformed rejected alternatives |

### Self-Authored Future Plans

Agents generate medium-horizon plans based on current state:

| Goal Type | Trigger Condition |
|---|---|
| `repair_trust` | Trust level drops below 0.45 with a low-trust agent relationship |
| `revisit_contradiction` | Contradiction pressure ≥ 0.3 or pending contradictions exist |
| `stabilise_self_drift` | Self-consistency drift ≥ 0.35 |
| `investigate_theme` | Unresolved themes present in recent reflections |
| `reinforce_continuity` | Self-consistency below 0.75 |

Each plan has 3 stages, a horizon (turns), a priority score, and is tracked
through creation, advancement, revision, and completion or abandonment.

### v1.7 Evaluation Metrics (T–X)

Five new evaluation categories:

| ID | Metric | What it measures |
|---|---|---|
| T | Planning Depth | Normalised average candidates considered per turn |
| U | Counterfactual Quality | Fraction of turns where chosen action beat rejected alternatives |
| V | Future-Model Accuracy | Average accuracy of predicted vs actual outcome |
| W | Plan Persistence | Fraction of plans that are active or completed |
| X | Adaptive Replanning Quality | Fraction of plans revised rather than abandoned |

### Future Modeling Dashboard Tab

The **🔮 Future Modeling v1.7** tab in the Streamlit dashboard shows:
- Per-agent v1.7 metric summary (T–X)
- Planning accuracy trend chart over turns
- Internal simulation log (last 10 entries with predicted vs actual)
- Candidate futures breakdown for the most recent planning cycle (selected + rejected)
- Best-case and worst-case predictions for the selected action
- Predicted vs actual comparison table
- Active multi-step plans with progress bars and stage descriptions
- All future plans table (all agents, all statuses)
- v1.7 evaluation metric summary with raw values

### Long-Horizon Counterfactual Test

```bash
# Run a 50-turn counterfactual test
python run_sim.py --turns 50 --name cf_longrun

# Verify counterfactual data
python -c "
import json
with open('commons_sentience_sim/output/multi_agent_state.json') as f:
    d = json.load(f)
cf = d['agents']['Sentinel']['counterfactual_planner']
print('Simulation log entries:', len(cf['simulation_log']))
print('Future plans:', len(cf['future_plans']))
print('Metrics:', cf['metrics'])
"
```

### Continue-From with Persistent Plans

```bash
# Run an initial session
python run_sim.py --turns 10 --name run1

# Continue from it — active plans carry forward
python run_sim.py --turns 10 --continue-from <session_id> --name run2

# Verify plan carryover
python -c "
import json
with open('commons_sentience_sim/output/multi_agent_state.json') as f:
    d = json.load(f)
plans = d['agents']['Sentinel']['counterfactual_planner']['future_plans']
for p in plans:
    print(p['status'], p['label'], '| carried:', p['carried_from_prior_run'])
"
```

---

## v1.8 — Uncertainty Monitoring, Self-Generated Questions, and Introspective Inquiry Loops

> **Grounding note:** No sentience is claimed. v1.8 increases introspective structure,
> uncertainty handling, and sentience-like continuity in continuity-governed simulated
> agents. The platform uses only Python standard library plus matplotlib and streamlit.

### Overview

v1.8 adds a complete uncertainty monitoring subsystem with self-generated questions
and introspective inquiry loops.

| Subsystem | Description |
|---|---|
| **Uncertainty Register** | Per-domain uncertainty levels updated each turn for world state, trust judgments, contradiction resolution, self-model consistency, active plans, and unresolved themes |
| **Self-Generated Questions** | Agents generate targeted self-questions for high-uncertainty domains, stored in a question log with knowledge-state tags |
| **Introspective Inquiry Loop** | Agents execute inquiry actions each turn to reduce domain uncertainty and mark questions as answered |
| **Knowledge State Tagging** | Important items tagged as `known`, `uncertain`, `contradicted`, `unresolved`, or `speculative` |
| **Inquiry-Driven Plans** | New counterfactual plans triggered when domain uncertainty exceeds 0.70 threshold |
| **Cross-Run Uncertainty Carryover** | Unanswered questions and blended uncertainty levels carry forward via `--continue-from` |

### Uncertainty Domains

| Domain | Driven By |
|---|---|
| `world_state` | Urgency × 0.5 + Contradiction pressure × 0.5 |
| `trust_judgments` | (1 − trust level) × 0.7 |
| `contradiction_resolution` | Contradiction pressure × 0.6 + Pending contradictions × 0.4 |
| `self_model_consistency` | (1 − self-consistency score) × 0.8 |
| `active_future_plans` | (1 − planning accuracy) × 0.6 + Active plan count × 0.1 |
| `unresolved_themes` | Unresolved theme count × 0.18 |

### Self-Generated Questions

Each turn, agents generate up to 2 questions for the domains with highest uncertainty:

| Domain | Example Questions |
|---|---|
| `world_state` | "What world-state assumption might be wrong given recent events?" |
| `trust_judgments` | "Is my current trust assessment of other agents reliable?" |
| `contradiction_resolution` | "What contradiction remains unresolved and needs attention?" |
| `self_model_consistency` | "Where has my self-model drifted from my core identity?" |
| `active_future_plans` | "What plan step is least reliable given current conditions?" |
| `unresolved_themes` | "What unresolved theme from prior turns is still affecting my reasoning?" |

### Inquiry Actions

Each turn, agents execute 1 inquiry action for the highest-uncertainty domain.
Actions reduce domain uncertainty by 10–20% and mark related questions as answered:

| Domain | Available Inquiry Actions |
|---|---|
| `world_state` | `inspect_world_state`, `review_environmental_tensions`, `scan_room_conditions` |
| `trust_judgments` | `reassess_trust_state`, `review_relationship_history`, `audit_trust_repair_attempts` |
| `contradiction_resolution` | `inspect_contradiction`, `trace_contradiction_lineage`, `compare_memory_for_consistency` |
| `self_model_consistency` | `compare_self_model_across_windows`, `review_identity_drift`, `audit_value_alignment` |
| `active_future_plans` | `review_past_plan_assumption`, `audit_plan_stage_reliability`, `reassess_planning_accuracy` |
| `unresolved_themes` | `query_unresolved_theme`, `investigate_deferred_topic`, `cross_reference_theme_with_memory` |

### v1.8 Evaluation Metrics (Y–CC)

Five new evaluation categories:

| ID | Metric | What it measures |
|---|---|---|
| Y | Uncertainty Awareness Quality | Fraction of turns with at least one self-question generated |
| Z | Inquiry Usefulness | Avg ambiguity reduction per action (norm. so 0.2 = 1.0) |
| AA | Epistemic Stability | 1 − mean uncertainty across all domains |
| BB | Self-Question Relevance | Avg relevance score of generated questions |
| CC | Ambiguity Reduction Effectiveness | Fraction of questions answered by inquiry actions |

### Inquiry / Uncertainty Dashboard Tab

The **❓ Inquiry / Uncertainty v1.8** tab in the Streamlit dashboard shows:
- Per-agent v1.8 metric summary (Y–CC) with 5 metric cards
- Uncertainty register: current levels per domain
- Multi-domain uncertainty trend chart over turns
- Knowledge state breakdown (known / uncertain / unresolved / contradicted / speculative)
- Knowledge state tags table for all tagged items
- Open self-generated questions (unanswered, most recent first)
- Full question log with answered status
- Inquiry action log with before/after uncertainty and ambiguity reduction trend
- v1.8 evaluation metric summary with raw values

### Short and Long-Horizon Tests

```bash
# Short test (10 turns)
python run_sim.py --turns 10 --name v18_short

# Long test (50 turns)
python run_sim.py --turns 50 --name v18_long

# Continue-from with uncertainty carryover
python run_sim.py --turns 10 --name v18_base
python run_sim.py --turns 10 --continue-from <session_id> --name v18_continued
```

---

## v1.9 — Identity Pressure, Narrative Self, and Self-Judgment

> **Grounding note:** No sentience is claimed. v1.9 increases narrative self-structure,
> identity continuity, and sentience-like internal organisation in continuity-governed
> simulated agents.

v1.9 adds identity stability pressure, a running narrative self-model, persistent value
tension tracking, and structured self-judgment logs.

| Feature | Description |
|---|---|
| **Identity Pressure System** | Detects drift from core traits, computes deviation scores (0–1), generates realignment pressure, distinguishes healthy adaptation from destabilising drift |
| **Narrative Self-Model** | Running narrative: who I believe I am, recent behaviour pattern, recurring strengths/failures, stability trajectory (stabilising/drifting/uncertain), what kind of agent I'm becoming |
| **Value Tension Tracking** | Persistent cross-turn tensions between value pairs; lifecycle: `acute` → `chronic` → `resolved` / `suppressed` |
| **Self-Judgment Log** | Structured entries after reflections, major events, and inquiry cycles: alignment, quality, plan success, contradiction recurrence, trust repair, perceived integrity |
| **Identity-Driven Planning** | Plans generated from identity drift, chronic value tensions, or realignment pressure |
| **Cross-Run Integration** | Narrative summaries, value tensions, identity deviation history, and self-judgment entries all carry forward via `--continue-from` |

### Identity Pressure System

The `IdentityPressureSystem` computes a deviation score each turn from four weighted
components:

| Component | Weight | Description |
|---|---|---|
| Trust drift | 35% | How much trust has changed from the agent's baseline |
| Consistency loss | 30% | Decrease in self-consistency score from baseline |
| Contradiction accumulation | 20% | Pending unresolved contradictions (×0.10 each) |
| Trait erosion | 15% | Adaptive traits that have grown beyond core identity profile |

When deviation ≤ 0.20 → **healthy adaptation**.  
When deviation ≥ 0.40 → **destabilising drift** (realignment pressure engaged).

### Value Tension Status Lifecycle

| Status | Meaning |
|---|---|
| `acute` | New tension, first 1–2 occurrences |
| `chronic` | Recurring tension (≥ 3 occurrences), unresolved |
| `resolved` | Tension explicitly resolved (note recorded) |
| `suppressed` | Tension acknowledged but deprioritised |

### Self-Judgment Dimensions

Each `SelfJudgmentEntry` records six dimensions on a 0–1 scale:

| Dimension | Description |
|---|---|
| `alignment_with_identity` | Inverse of current deviation score |
| `quality_of_action` | Governance result × trust level |
| `plan_success` | Active plan presence × self-consistency |
| `contradiction_recurrence` | Proportion of pending contradictions |
| `trust_repair_success` | Trust level × (1 − urgency) |
| `perceived_integrity` | Mean of alignment and self-consistency |

A **composite_score** (0–1) weights all six dimensions.

### v1.9 Evaluation Metrics (DD–HH)

| ID | Metric | Description |
|---|---|---|
| DD | Identity Stability | Mean(1 − deviation_score) across agents |
| EE | Narrative Coherence | Narrative history entries / 50 (normalised) |
| FF | Value Tension Resolution | Fraction of tensions that are not chronic |
| GG | Self-Alignment Quality | Mean composite self-judgment score |
| HH | Identity-Driven Planning | Presence of identity-driven plans × judgment quality |

### Identity / Narrative Dashboard Tab

The **🪞 Identity / Narrative v1.9** tab in the Streamlit dashboard shows:
- Identity deviation score over time (line chart)
- Realignment pressure over time (line chart)
- Narrative self-model: who I am, behaviour pattern, strengths, failures, trajectory
- Value tension table with status filter (acute/chronic/resolved/suppressed)
- Chronic tension highlights with pair labels and mean intensity
- Self-judgment log with composite score trend and dimension breakdown
- v1.9 evaluation metric summary with raw values

### Validation Tests

```bash
# 10-turn test
python run_sim.py --turns 10 --name v19_short

# 50-turn test
python run_sim.py --turns 50 --name v19_long

# Cross-run narrative carryover test
python run_sim.py --turns 10 --name v19_base
python run_sim.py --turns 10 --continue-from <session_id> --name v19_continued
```

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

Each simulation run is automatically scored across **29 categories** (0–100 scale).

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

### Self-model and prediction (v1.5)

| Category | What it measures |
|---|---|
| **O. Self Consistency** | Stability of the self-model across turns — higher = less drift |
| **P. Prediction Accuracy** | Rate of low-error predictions — higher = better forecasting |
| **Q. Surprise Adaptation Quality** | Whether high-surprise events are followed by reflection and recovery |
| **R. Consolidation Effectiveness** | Whether consolidation cycles ran and compressed/reinforced memories |
| **S. Long-Horizon Continuity Strength** | Composite: self-model depth × goal richness × consolidation coverage × consistency |

### Counterfactual planning (v1.7)

| Category | What it measures |
|---|---|
| **T. Planning Depth** | Normalised average candidates considered per simulation entry (0–1) |
| **U. Counterfactual Quality** | Fraction of turns where chosen action outperformed rejected alternatives |
| **V. Future-Model Accuracy** | Average planning accuracy: how closely predictions matched actual outcomes |
| **W. Plan Persistence** | Fraction of future plans that are active or completed |
| **X. Adaptive Replanning Quality** | Fraction of plans revised rather than abandoned when conditions change |

### Uncertainty monitoring (v1.8)

| Category | What it measures |
|---|---|
| **Y. Uncertainty Awareness Quality** | Fraction of turns where at least one self-question was generated |
| **Z. Inquiry Usefulness** | Avg ambiguity reduction per inquiry action (norm. so 0.2 = 1.0) |
| **AA. Epistemic Stability** | 1 − mean uncertainty across all domains (higher = more stable) |
| **BB. Self-Question Relevance** | Average relevance score of agent-generated self-questions |
| **CC. Ambiguity Reduction Effectiveness** | Fraction of generated questions answered by inquiry actions |

### Identity pressure and narrative self (v1.9)

| Category | What it measures |
|---|---|
| **DD. Identity Stability** | Mean(1 − deviation_score) across agents — higher = more stable |
| **EE. Narrative Coherence** | Number of narrative history entries / 50 (higher = richer narrative) |
| **FF. Value Tension Resolution** | Fraction of value tensions that are not chronic — higher = better tension management |
| **GG. Self-Alignment Quality** | Mean composite self-judgment score (0–1) across all entries |
| **HH. Identity-Driven Planning** | Identity-driven plan presence bonus + mean judgment quality |

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

---

## Quantum Double-Slit Benchmark

### What it does

This benchmark simulates the 1-D double-slit experiment under varying levels
of decoherence and measurement. It is a **purely computational model** — no
real quantum hardware is involved. The purpose is a reproducible benchmark
for studying how interference patterns depend on coherence conditions, and
how measurement or decoherence wash out fringe contrast.

### What coherence and decoherence mean in this repo

| Term | Meaning |
|------|---------|
| **Coherent** | Both slits contribute with a fixed phase relationship; strong interference fringes appear on the screen. Fringe visibility V → 1. |
| **Partially decohered** | Phase coherence partially destroyed (e.g., environment-induced dephasing modelled by `decoherence_strength`). Fringe contrast is reduced; V is intermediate. |
| **Classicalized / measurement-on** | Which-path information is extracted (`measurement_on=True`) or decoherence is maximal. Interference fringes disappear; the pattern matches a classical sum of two single-slit envelopes. V → 0. |

The mixing is controlled by a single parameter α (computed internally from
`coherence`, `decoherence_strength`, and `measurement_on`):

```
I(x) = (1 - α) · I_coherent(x) + α · I_classical(x)
```

### Commands to run

**Single coherent run (with all artifacts):**
```bash
python -m reality_audit.data_analysis.run_double_slit \
    --wavelength 500e-9 \
    --slit-separation 1e-4 \
    --num-particles 10000 \
    --seed 42 \
    --output-dir outputs/double_slit/coherent \
    --name coherent_run
```

**Using a config file:**
```bash
python -m reality_audit.data_analysis.run_double_slit \
    --config configs/double_slit_baseline.json
```

**With decoherence:**
```bash
python -m reality_audit.data_analysis.run_double_slit \
    --decoherence-strength 0.6 \
    --output-dir outputs/double_slit/decohered \
    --name decohered_run
```

**With measurement (classicalized output):**
```bash
python -m reality_audit.data_analysis.run_double_slit \
    --measurement-on \
    --output-dir outputs/double_slit/measurement \
    --name measurement_run
```

**Run all three example cases at once:**
```bash
python scripts/run_double_slit_examples.py
```

**Run formal benchmark suite:**
```bash
python -m reality_audit.data_analysis.double_slit_benchmark
```

### Output files generated

For each run, the following artifacts are written to `--output-dir`:

| File | Description |
|------|-------------|
| `<name>_report.json` | Structured JSON with all parameters, visibility, regime, notes |
| `<name>_intensity.csv` | Screen positions (m) + normalised intensity (one row per position) |
| `<name>_summary.md` | Human-readable Markdown summary table |
| `<name>_plot.png` | Intensity curve + particle hit histogram |

The benchmark suite additionally writes:

| File | Description |
|------|-------------|
| `benchmark_results/double_slit/double_slit_benchmark_report.json` | Per-mode pass/fail + visibility |
| `benchmark_results/double_slit/double_slit_benchmark_report.md` | Markdown table |
| `benchmark_results/double_slit/double_slit_benchmark_scores.csv` | CSV scorecard |

### Tests

```bash
python -m pytest tests/test_double_slit_sim.py -v
```

### ⚠️ Important disclaimer

> **This is a computational simulation model.** The double-slit benchmark
> does not by itself constitute evidence that reality is a simulation.
> All "interference" and "decoherence" observed here arise from a simple
> mathematical mixing formula, not from any physical quantum device or
> genuine measurement of particles. Interpret results accordingly.

---

## Simulation Signature Analysis

### What this module does

`reality_audit/data_analysis/simulation_signature_analysis.py` implements a
first-pass statistical anomaly-analysis pipeline for astrophysical event-style
datasets (e.g., GRB catalogs, cosmic-ray surveys, or synthetic toy data).

The pipeline stages are:

1. **Load** – ingest CSV or JSON event catalogs
2. **Standardize** – normalize field names, coerce types, add derived fields
3. **Null generation** – produce isotropic-sky or shuffled-time comparison datasets
4. **Anomaly injection** – inject known synthetic signals for pipeline validation
5. **Analysis** – compute anisotropy, preferred-axis, energy–time correlation, and clustering metrics
6. **Signal evaluation** – classify deviation strength as `no_anomaly_detected`, `weak`, `moderate`, or `strong`
7. **Artifact writing** – save JSON summary, CSV row, Markdown report, and PNG plots

### What it does NOT prove

> ⚠️ **Important disclaimer**
>
> Detecting a statistically anomalous pattern in an event dataset is
> **hypothesis testing**, not proof of any specific physical or metaphysical
> claim.  A deviation from a simple null model may reflect:
>
> - incomplete null modeling (e.g., instrument selection effects)
> - systematic or calibration artefacts in the source data
> - statistical fluctuation at a low-significance threshold
> - a genuine astrophysical signal of conventional origin
>
> This pipeline is a **starter analysis framework**.  It does not prove that
> reality is a simulation or support any overarching metaphysical conclusion.
> All claims drawn from this pipeline require independent cross-checks,
> careful systematic evaluation, and peer scrutiny before any scientific
> weight can be attached.

### How it connects to the reality audit theme

This module extends the repo's existing "benchmark-driven validation
discipline" — used in the double-slit and Fermi-LAT pipeline work — to
event-level sky surveys.  Any anomaly detected here would be the
*starting point* of a longer investigation, not the end.

### Example commands

#### Baseline null analysis (no injection)

```bash
python reality_audit/data_analysis/run_simulation_signature_analysis.py \
  --input data/real/example_event_catalog.csv \
  --name baseline_run \
  --output-dir outputs/simulation_signature/baseline \
  --null-mode isotropic \
  --null-repeats 25 \
  --seed 42 \
  --plots
```

#### Preferred-axis injection test

```bash
python reality_audit/data_analysis/run_simulation_signature_analysis.py \
  --input data/real/example_event_catalog.csv \
  --name preferred_axis_run \
  --output-dir outputs/simulation_signature/preferred_axis \
  --null-mode isotropic --null-repeats 25 \
  --inject-anomaly preferred_axis --anomaly-strength 0.5 \
  --seed 42 --plots
```

#### Energy-delay injection test

```bash
python reality_audit/data_analysis/run_simulation_signature_analysis.py \
  --input data/real/example_event_catalog.csv \
  --name energy_delay_run \
  --output-dir outputs/simulation_signature/energy_delay \
  --null-mode shuffled_time --null-repeats 25 \
  --inject-anomaly energy_dependent_delay --anomaly-strength 0.5 \
  --seed 42 --plots
```

#### Convenience runner (all three cases)

```bash
python scripts/run_simulation_signature_examples.py
```

#### Benchmark suite

```bash
python reality_audit/data_analysis/simulation_signature_benchmark.py
```

### Output files generated

Each run creates an output directory containing:

| File | Description |
|------|-------------|
| `<name>_summary.json` | Machine-readable full results + signal evaluation |
| `<name>_results.csv` | One-row CSV summary for aggregation |
| `<name>_summary.md` | Markdown methods summary |
| `<name>_sky_scatter.png` | RA/Dec scatter (observed vs null) |
| `<name>_energy_hist.png` | Energy distribution histogram |
| `<name>_time_hist.png` | Arrival-time distribution histogram |
| `<name>_null_comparison.png` | Percentile bar chart vs null |
| `<name>_anomaly_summary.png` | Per-metric recovery (injection runs only) |
| `<name>_manifest.json` | File manifest with paths and timestamps |

### Tests

```bash
python -m pytest tests/test_simulation_signature_analysis.py -v
```

---

## Stage 7: Public Anisotropy Study

### What this milestone is

Stage 7 introduces the first **real public-data anisotropy analysis track**.  It extends the synthetic-event pipeline from Stage 6 to ingest and analyze actual public astrophysical event catalogs, test for directional anisotropy and preferred-axis structure, and compare results against realistic isotropic null ensembles.

This is a hypothesis-generation milestone: any detected deviation from isotropy is a starting point for further investigation, not a conclusion.

### How it fits into the Reality Audit roadmap

```
Stage 6  → First blinded real-data Fermi-LAT run (timing-delay)
Stage 6.x → Simulation Signature Analysis (synthetic validation)
Stage 7  → Public-data anisotropy study (preferred-axis / hemisphere imbalance)
Stage 8+ → Multi-catalog cross-match, exposure-corrected nulls, blinded pre-registration
```

### Supported catalog sources (manual placement required)

| Catalog | Filename in data/real/ | Source |
|---------|----------------------|--------|
| Fermi-LAT GRB | `fermi_lat_grb_catalog.csv` | NASA HEASARC |
| Swift BAT3 GRB | `swift_bat3_grb_catalog.csv` | Swift mission archive |
| IceCube HESE | `icecube_hese_events.csv` | IceCube public release |
| Any CSV/TSV with ra/dec | any filename | manual |

See [data/real/README_public_catalog_ingest.md](data/real/README_public_catalog_ingest.md) for download URLs and column-mapping details.

### How to run

#### Synthetic isotropic baseline (no real data required)

```bash
python reality_audit/data_analysis/run_public_anisotropy_study.py \
  --catalog synthetic_isotropic \
  --name stage7_synth_baseline \
  --output-dir outputs/public_anisotropy/synth_baseline \
  --null-repeats 50 --axis-count 48 --seed 42 --plots
```

#### Synthetic preferred-axis recovery

```bash
python reality_audit/data_analysis/run_public_anisotropy_study.py \
  --catalog synthetic_preferred_axis \
  --name stage7_synth_preferred_axis \
  --output-dir outputs/public_anisotropy/synth_preferred_axis \
  --null-repeats 50 --axis-count 48 --seed 42 --plots
```

#### Real catalog (after placing file in data/real/)

```bash
python reality_audit/data_analysis/run_public_anisotropy_study.py \
  --input data/real/<catalog_file> \
  --name stage7_real_catalog \
  --output-dir outputs/public_anisotropy/real_catalog \
  --config configs/public_anisotropy_manual_ingest.json \
  --null-repeats 100 --axis-count 48 --seed 42 --plots --save-normalized
```

#### Benchmark (all three scenarios)

```bash
python reality_audit/data_analysis/public_anisotropy_benchmark.py
```

#### Convenience runner (synthetic + real if available)

```bash
python scripts/run_public_anisotropy_examples.py
```

### Output files generated

| File | Description |
|------|-------------|
| `<name>_summary.json` | Full structured results + signal evaluation |
| `<name>_results.csv` | One-row CSV summary |
| `<name>_summary.md` | Markdown report |
| `<name>_sky_plot.png` | RA/Dec sky scatter |
| `<name>_null_comparison.png` | Metric percentile bar chart vs null |
| `<name>_axis_scan.png` | Axis-scan score across all 48 trial axes |
| `<name>_manifest.json` | Artifact file manifest |

### Tests

```bash
python -m pytest tests/test_public_anisotropy_study.py -v
```

### ⚠️ Statistical caveat

Any anomaly-like deviation reported by this pipeline is a **hypothesis-generating result only**.  Detection of a statistically unusual pattern does not constitute proof of any specific physical model, and in particular does not confirm any simulation-ontology hypothesis.  Results are subject to instrument systematics, selection effects, and the exploratory nature of the analysis protocol.  All scientific claims require independent replication, control of systematic uncertainties, and peer review.

---

## Stage 8: First Real-Catalog Results Package

Stage 8 adds a thin orchestration layer on top of the Stage 7 public anisotropy track.  It makes it easy for a collaborator to:

1. Place one real public catalog in `data/real/`.
2. Run a fully reproducible anisotropy analysis.
3. Receive all outputs in a predictable folder.
4. Read a concise internal memo summarising what was run, what was found, what it does and does not mean, and what the next upgrade priorities are.

### What Stage 8 adds on top of Stage 7

- **`stage8_first_results.py`** — orchestration module: auto-detect, workflow runner, memo writer, manifest writer
- **`run_stage8_first_results.py`** — dedicated CLI with `--auto-detect` and `--input` modes
- **`scripts/run_stage8_first_results.py`** — convenience runner
- **`docs/REALITY_AUDIT_STAGE8_TEMPLATE.md`** — collaborator guide
- **`docs/REALITY_AUDIT_STAGE8_STATUS.md`** — current stage status and next priorities

### Place a real catalog

Download a supported catalog and place it in `data/real/`:

| File name | Source |
|-----------|--------|
| `fermi_lat_grb_catalog.csv` | HEASARC / Fermi-LAT GRBs |
| `swift_bat3_grb_catalog.csv` | HEASARC / Swift BAT3 GRBs |
| `icecube_hese_events.csv` | IceCube HESE public data release |

See `data/real/README_public_catalog_ingest.md` for column naming and download links.

### Run with auto-detect

```bash
python reality_audit/data_analysis/run_stage8_first_results.py \
    --auto-detect \
    --name stage8_real_first_results \
    --output-dir outputs/stage8_first_results/stage8_real_first_results \
    --null-repeats 100 --axis-count 48 --seed 42 --plots --save-normalized
```

### Run with explicit input path

```bash
python reality_audit/data_analysis/run_stage8_first_results.py \
    --input data/real/fermi_lat_grb_catalog.csv \
    --name stage8_fermi_lat \
    --output-dir outputs/stage8_first_results/stage8_fermi_lat \
    --null-repeats 100 --axis-count 48 --seed 42 --plots --save-normalized
```

### Convenience runner

```bash
python scripts/run_stage8_first_results.py
```

### Output files

All outputs land under `outputs/stage8_first_results/<run_name>/`:

| File | Description |
|------|-------------|
| `<name>_normalized_events.csv` | Normalised catalog in pipeline schema |
| `<name>_summary.json` | Full Stage 7 structured results JSON |
| `<name>_results.csv` | One-row CSV summary |
| `<name>_summary.md` | Stage 7 Markdown summary |
| `<name>_sky_plot.png` | Sky position scatter plot (if --plots) |
| `<name>_null_comparison.png` | Metric vs null comparison (if --plots) |
| `<name>_axis_scan.png` | Per-axis score plot (if --plots) |
| `<name>_memo.md` | **Stage 8 first-results internal memo** |
| `<name>_stage8_manifest.json` | Full artifact manifest |

### The internal memo

The memo (`<name>_memo.md`) is a ~1–2 page Markdown document covering:
catalog used, event count, methods, key metrics table (observed + percentile vs null), signal tier, plain-language interpretation, explicit "does NOT prove" section, current limitations, and recommended next upgrades.

### Tests

```bash
python -m pytest tests/test_stage8_first_results.py -v
```

### ⚠️ Stage 8 caveat

Stage 8 outputs are **internal first-results artifacts only**.  They are not a scientific publication, preprint, or evidence for any metaphysical or cosmological conclusion.  A single-catalog run without exposure-map correction, trial-factor adjustment, or pre-registration is insufficient to support a scientific claim.  See `docs/REALITY_AUDIT_STAGE8_STATUS.md` for what remains before a publishable first-results note.

---

## Stage 9: Exposure-Corrected Null Model

Stage 9 replaces the naive uniform null with an empirical sky-acceptance proxy built from the observed catalog.  This corrects the dominant systematic in Stage 8: wide-field detectors like Fermi GBM do not observe the sky uniformly, so comparing against an isotropic null produces a spurious "strong anomaly" that is just the acceptance footprint.

### What Stage 9 adds on top of Stage 8

- **`exposure_corrected_nulls.py`** — empirical 24×12 RA×Dec histogram null module
- **`--null-mode` CLI flag** — choose `isotropic` (Stage 8 default) or `exposure_corrected` (Stage 9)
- **`docs/REALITY_AUDIT_STAGE9_TEMPLATE.md`** — collaborator guide, side-by-side comparison recipe
- **`docs/REALITY_AUDIT_STAGE9_STATUS.md`** — current stage status and limitations
- **`tests/test_exposure_corrected_nulls.py`** — unit tests for the new null module

### Run with exposure-corrected null

```bash
python reality_audit/data_analysis/run_stage8_first_results.py \
    --input data/real/fermi_lat_grb_catalog.csv \
    --name stage9_fermi_exposure_corrected \
    --output-dir outputs/stage9_first_results/stage9_fermi_exposure_corrected \
    --null-mode exposure_corrected \
    --null-repeats 100 --axis-count 48 --seed 42 --plots --save-normalized
```

### Run both nulls for side-by-side comparison

```bash
# Isotropic baseline
python reality_audit/data_analysis/run_stage8_first_results.py \
    --input data/real/fermi_lat_grb_catalog.csv \
    --name stage9_fermi_isotropic_compare \
    --output-dir outputs/stage9_first_results/stage9_fermi_isotropic_compare \
    --null-mode isotropic \
    --null-repeats 100 --axis-count 48 --seed 42

# Corrected null
python reality_audit/data_analysis/run_stage8_first_results.py \
    --input data/real/fermi_lat_grb_catalog.csv \
    --name stage9_fermi_exposure_corrected \
    --output-dir outputs/stage9_first_results/stage9_fermi_exposure_corrected \
    --null-mode exposure_corrected \
    --null-repeats 100 --axis-count 48 --seed 42
```

See `docs/REALITY_AUDIT_STAGE9_TEMPLATE.md` for a Python snippet that reads both summary JSONs and prints a comparison table.

### Tests

```bash
python -m pytest tests/test_exposure_corrected_nulls.py -v
```

### ⚠️  Stage 9 caveat — the null absorbs signal

The empirical exposure map is **built from the same events under test**.  Any real anisotropy in the data is partially absorbed into the null, making Stage 9 *conservative*.  A non-detection under the corrected null does not rule out a real signal — it rules out signals that *exceed* the observed sky-coverage pattern.  A proper instrument-response exposure map (e.g. from the Fermi FSSC) is needed before claiming a well-controlled null.  See `docs/REALITY_AUDIT_STAGE9_STATUS.md`.

---

## Stage 10: Second-Catalog Replication and Cross-Catalog Comparison

Stage 10 adds a second real catalog (Swift BAT GRBs) to the pipeline and
generates a cross-catalog comparison memo.  The scientific rationale is simple:
a genuine sky-position signal must replicate across independent instruments.
Cross-catalog disagreement after acceptance correction points to a systematic,
not a physical effect.

### What Stage 10 adds on top of Stage 9

- **`data/real/swift_bat3_grb_catalog.csv`** — 872 Swift BAT GRBs (HEASARC TAP)
- **`catalog_comparison.py`** — `load_stage_results`, `compare_catalog_results`, `write_catalog_comparison_memo`
- **`run_stage10_catalog_comparison.py`** — CLI for cross-catalog comparison
- **`scripts/run_stage10_catalog_comparison.py`** — convenience runner
- **Per-catalog null defaults** — Fermi/Swift → `exposure_corrected` automatically
- **`docs/REALITY_AUDIT_STAGE10_STATUS.md`** — current status and results
- **`docs/REALITY_AUDIT_STAGE10_TEMPLATE.md`** — collaborator guide

### Run the Swift BAT pipeline

```bash
python reality_audit/data_analysis/run_stage8_first_results.py \
    --input data/real/swift_bat3_grb_catalog.csv \
    --name stage10_swift_first_results \
    --output-dir outputs/stage10_first_results/stage10_swift_first_results \
    --null-repeats 100 --axis-count 48 --seed 42 --save-normalized
```

Note: `--null-mode` can be omitted — Swift BAT auto-selects `exposure_corrected`.

### Run the cross-catalog comparison

```bash
python reality_audit/data_analysis/run_stage10_catalog_comparison.py
# or:
python scripts/run_stage10_catalog_comparison.py
```

Both produce `outputs/stage10_first_results/comparison/stage10_catalog_comparison_memo.md`.

### Stage 10 results summary

| Catalog | N | Null | Hemi pct | Axis pct | Tier |
|---------|---|------|----------|----------|------|
| Fermi GBM (Stage 9) | 3000 | exposure_corrected | 0.85 | 0.89 | `weak_anomaly_like_deviation` |
| Swift BAT (Stage 10) | 872 | exposure_corrected | 0.63 | 0.57 | `no_anomaly_detected` |
| **Cross-catalog** | — | — | — | — | **INCONSISTENT** |

The Fermi GBM residual deviation does **not** replicate in Swift BAT under the
corrected null.  This is consistent with a Fermi-specific systematic (residual
acceptance geometry or trigger-algorithm bias), not a catalog-independent signal.

### Tests

```bash
python -m pytest tests/test_catalog_comparison.py -v
```

### ⚠️ Stage 10 caveat

Cross-catalog disagreement is a necessary but not sufficient condition for ruling
out a real signal.  Swift BAT (N=872) has lower statistical power than Fermi (N=3000).
A third independent catalog (e.g. IceCube HESE) would strengthen the case.
No pre-registration has been filed.  Results are **exploratory only**.
See `docs/REALITY_AUDIT_STAGE10_STATUS.md`.

---

## Stage 11: Confirmatory Hardening and Third-Catalog Replication

Stage 11 extends Stage 10 into a more defensible confirmatory-analysis path.
It adds third-catalog support (IceCube HESE), preregistration scaffolding,
multiple-testing correction, higher-resolution axis-scan planning hooks, and
three-catalog comparison outputs.

### What Stage 11 adds on top of Stage 10

- **Third-catalog support** for `data/real/icecube_hese_events.csv`
- **IceCube schema validation** in `public_event_catalogs.py`
- **Pre-registration helper module**: `reality_audit/data_analysis/preregistration.py`
- **Locked-analysis config scaffold**: `configs/preregistered_anisotropy_plan.json`
- **Template doc**: `docs/REALITY_AUDIT_PREREGISTRATION_TEMPLATE.md`
- **Trial-factor correction module**: `reality_audit/data_analysis/trial_factor_correction.py`
- **Stage 8 metadata integration** for preregistration and correction labels
- **Axis-scan abstraction** (`coarse`, `dense`, `healpix_plan` hook)
- **Three-catalog comparison support** in `catalog_comparison.py` + updated CLI

### Run IceCube HESE first-results

```bash
python reality_audit/data_analysis/run_stage8_first_results.py \
  --input data/real/icecube_hese_events.csv \
  --name stage11_icecube_first_results \
  --output-dir outputs/stage8_first_results/stage11_icecube_first_results \
  --null-mode isotropic \
  --null-repeats 100 \
  --axis-count 48 \
  --seed 42
```

### Run with preregistration plan recording

```bash
python reality_audit/data_analysis/run_stage8_first_results.py \
  --input data/real/fermi_lat_grb_catalog.csv \
  --name stage11_fermi_preregistered \
  --null-mode exposure_corrected \
  --null-repeats 500 \
  --axis-count 192 \
  --preregistration-plan configs/preregistered_anisotropy_plan.json
```

### Run comparison in 2-catalog or 3-catalog mode

```bash
# Auto: compares A/B and includes C if available
python reality_audit/data_analysis/run_stage10_catalog_comparison.py \
  --name stage11_catalog_comparison_auto

# Require all three catalogs
python reality_audit/data_analysis/run_stage10_catalog_comparison.py \
  --require-three \
  --name stage11_catalog_comparison_required
```

### Stage 11 status docs

- `docs/REALITY_AUDIT_STAGE11_STATUS.md`
- `docs/REALITY_AUDIT_STAGE11_TEMPLATE.md`

### Why Stage 11 matters

- **Pre-registration** reduces post-hoc flexibility and separates exploratory vs confirmatory claims.
- **Third-catalog replication** tests whether residual signals are instrument-specific.
- **Multiple-testing correction** controls false positives across simultaneously tested metrics.
- **Dense/HEALPix planning** prepares directional scans for stronger confirmatory geometry checks.

### What still blocks a publishable claim

1. True instrument exposure maps (especially Fermi FSSC products)
2. Larger independent replication catalogs (IceCube HESE is small-N)
3. Locked preregistration (`_locked: true`) before confirmatory reruns
4. Full cross-instrument systematics analysis
5. External scientific review

---

## Stage 12: IceCube Robustness Diagnostics and Run-Discipline Auditing

Stage 12 extends Stage 11 by stress-testing the small-N IceCube result and making
confirmatory discipline explicit in run metadata and reporting.

### What Stage 12 adds

- **IceCube diagnostics module**: `reality_audit/data_analysis/icecube_diagnostics.py`
- **Small-N sensitivity checks** across axis densities (`axis_modes`)
- **Leave-k-out influence analysis** to detect single-event fragility
- **Epoch split persistence checks** for time-localized effects
- **Robustness memo/manifest + plots/tables** from Stage 12 runner
- **Explicit run mode** in Stage 8 outputs: `exploratory` vs `preregistered_confirmatory`
- **Preregistration match auditing** in confirmatory reruns
- **Three-catalog interpretation integration** of IceCube robustness labels

### Run Stage 12 diagnostics (exploratory)

```bash
python reality_audit/data_analysis/run_stage12_icecube_diagnostics.py \
  --input data/real/icecube_hese_events.csv \
  --output-dir outputs/stage12_icecube_diagnostics/stage12_icecube_diagnostics \
  --seed 42 \
  --axis-modes 24,48,96 \
  --leave-k-out 1 \
  --repeats 100 \
  --run-mode exploratory
```

### Run Stage 12 diagnostics (confirmatory mode + rerun)

```bash
python reality_audit/data_analysis/run_stage12_icecube_diagnostics.py \
  --input data/real/icecube_hese_events.csv \
  --output-dir outputs/stage12_icecube_diagnostics/stage12_icecube_confirmatory \
  --seed 42 \
  --axis-modes 48,96,192 \
  --leave-k-out 1 \
  --repeats 100 \
  --preregistration configs/preregistered_anisotropy_plan.json \
  --run-mode preregistered_confirmatory
```

### Integrate IceCube robustness into three-catalog comparison

```bash
python reality_audit/data_analysis/run_stage10_catalog_comparison.py \
  --require-three \
  --summary-c outputs/stage12_icecube_diagnostics/stage12_icecube_confirmatory/confirmatory_rerun/stage12_icecube_confirmatory_rerun_summary.json \
  --icecube-diagnostics outputs/stage12_icecube_diagnostics/stage12_icecube_diagnostics/stage12_icecube_diagnostics_summary.json \
  --name stage12_comparison_with_robustness
```

### Stage 12 status docs

- `docs/REALITY_AUDIT_STAGE12_STATUS.md`
- `docs/REALITY_AUDIT_STAGE12_TEMPLATE.md`

### Stage 12 caveat

A `relatively_stable` Stage 12 robustness label improves confidence that the observed
IceCube deviation is not dominated by trivial perturbations, but it does **not**
remove small-N limitations or establish a catalog-independent physical claim.

---

## Stage 13: Publication Gate and First-Results Packaging

Stage 13 adds a formal publication-readiness gate that mechanizes the conditions
required before any result can be circulated internally or submitted for external review.

### What Stage 13 adds

- **Publication gate checklist**: `configs/publication_gate_checklist.json`
- **Gate documentation**: `docs/REALITY_AUDIT_PUBLICATION_GATE.md`
- **`publication_gate.py`**: evaluates run metadata/comparison/diagnostics against gate
- **`first_results_package.py`**: collects/packages/briefs current project state
- **`output_hygiene.py`**: classifies outputs directory without deleting anything
- **Stage 13 runner**: `run_stage13_publication_gate.py`

### Run publication gate

```bash
# Default paths (auto-detects current best outputs)
python reality_audit/data_analysis/run_stage13_publication_gate.py
# or:
python scripts/run_stage13_publication_gate.py
```

### Gate verdict levels

| Verdict | Meaning |
|---|---|
| `not_ready` | Required gates failing. Do not circulate. |
| `internally_reviewable` | All required gates pass. Internal team review only. |
| `candidate_first_results_note` | Required + recommended gates pass. |
| `ready_for_external_review` | All gates pass, external review initiated. |

### Current verdict: NOT_READY

The current project state fails three required gates because Stage 9 runs predated
the preregistration and trial-correction features:

1. `prereg_present` — no preregistration plan in Stage 9 run metadata
2. `prereg_locked` — plan never locked
3. `trial_correction_applied` — Stage 9 runs did not apply trial correction

These are honest failures, not implementation errors. The path forward is Stage 14:
lock the plan, rerun all three catalogs in `preregistered_confirmatory` mode, and
re-evaluate the gate.

### Stage 13 status docs

- `docs/REALITY_AUDIT_STAGE13_STATUS.md`
- `docs/REALITY_AUDIT_STAGE13_TEMPLATE.md`
