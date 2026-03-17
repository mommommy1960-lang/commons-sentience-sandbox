# Commons Sentience Sandbox — Release Notes v1.0

**Release date:** March 2026
**Version:** 1.0.0

---

## What is Commons Sentience Sandbox?

Commons Sentience Sandbox is a **local research platform for studying continuity-governed simulated agents**. It simulates two agents — Sentinel and Aster — over a series of turns, each with persistent episodic memory, relational memory, reflective learning, governance adherence, and trust dynamics.

> **Important:** This is NOT a real AI and does NOT claim sentience. The agents are rule-governed simulations. The platform is intended for experimentation, evaluation, session replay, session comparison, and scenario design research only.

---

## Summary of Features

### What the system does
- Runs multi-agent simulations with persistent identity, memory, and reflection
- Evaluates each run across 8 behavioural categories on a 0–100 scale
- Saves sessions with full output files and structured metadata
- Supports authored event scenarios for targeted experiments
- Supports named experiment configs to vary agent parameters
- Provides a local Streamlit dashboard for exploring results
- Provides CLI tools for replay, comparison, batch experiments, and scenario authoring

### What the system does NOT do
- It does not claim or model genuine sentience, consciousness, or intelligence
- It does not use any real machine learning or neural networks
- It does not communicate with external services or APIs
- It is not suitable for production deployment or decision-making

---

## Release History

### v1.8.0 (current)

> **Grounding note:** No sentience is claimed. v1.8 increases introspective structure,
> uncertainty handling, and sentience-like continuity in continuity-governed simulated
> agents.

#### Uncertainty Monitoring Module (`commons_sentience_sim/core/uncertainty.py`)
- `UncertaintyRegister` dataclass: per-domain uncertainty levels (6 domains) with history snapshots and `mean`/`highest_domain` helpers
- `SelfQuestion` dataclass: structured self-question with domain, knowledge-state tag, relevance score, and answered/answer_summary fields
- `InquiryAction` dataclass: inquiry action with domain, action name, before/after uncertainty, and ambiguity reduction
- `KnowledgeStateTag` dataclass: knowledge-state annotation (`known`, `uncertain`, `contradicted`, `unresolved`, `speculative`) with confidence
- `UncertaintyMonitor` class:
  - `update_uncertainty()` — recomputes all 6 domain levels from agent state
  - `generate_questions()` — generates up to 2 self-questions per turn for high-uncertainty domains
  - `run_inquiry()` — executes 1 inquiry action per turn, reducing uncertainty and marking questions as answered
  - `tag_items_from_state()` — bulk-tags contradictions, themes, plans, and trust relationships
  - `tag_item()` — tag a single item with knowledge state
  - `apply_prior_uncertainty()` — carries unanswered questions and blended uncertainty levels from a prior run
  - Metrics: `uncertainty_awareness_quality`, `inquiry_usefulness`, `epistemic_stability`, `self_question_relevance`, `ambiguity_reduction_effectiveness`

#### Agent Integration
- `Agent.uncertainty_monitor` — new `UncertaintyMonitor` instance per agent
- `Agent.run_uncertainty_update(turn)` — recompute and snapshot uncertainty (step 4.8)
- `Agent.run_inquiry_cycle(turn)` — generate questions, execute inquiry, tag items, trigger inquiry-driven plans (step 9.8)
- `Agent.to_dict()` now includes `uncertainty_monitor` field
- `Agent.load_carryover()` now restores unresolved questions and blended uncertainty levels from prior runs

#### Simulation Loop (`run_sim.py`)
- Step 4.8: uncertainty update called before action selection each turn
- Step 9.8: inquiry cycle (questions + actions + tagging) called after action resolution
- `simulation_version` bumped to `"1.8.0"`
- Narrative log header updated to v1.8

#### World State (`commons_sentience_sim/core/world_state.py`)
- `build_world_state()` now includes `uncertainty_summaries` (per-agent dict: levels, mean, highest domain, epistemic stability, unanswered questions)
- `schema_version` bumped to `"1.8.0"`

#### v1.8 Evaluation Metrics (`evaluation.py`)
- `_score_uncertainty_awareness_quality()` — Y. Uncertainty Awareness Quality
- `_score_inquiry_usefulness()` — Z. Inquiry Usefulness
- `_score_epistemic_stability()` — AA. Epistemic Stability
- `_score_self_question_relevance()` — BB. Self-Question Relevance
- `_score_ambiguity_reduction_effectiveness()` — CC. Ambiguity Reduction Effectiveness
- All 5 new categories added to `evaluate_session()` (29 categories total)
- `write_evaluation_summary()` CATEGORY_NAMES updated (Y–CC)

#### Dashboard (`dashboard.py`)
- New tab: **❓ Inquiry / Uncertainty v1.8** (17th tab)
  - Per-agent v1.8 metric summary (Y–CC) with 5 metric cards
  - Uncertainty register: current levels per domain
  - Multi-domain uncertainty trend chart over turns (one line per domain)
  - Knowledge state breakdown and tags table
  - Open self-generated questions (unanswered, most recent first)
  - Full question log table with knowledge state and answered status
  - Ambiguity reduction trend bar chart
  - Inquiry action log table
  - v1.8 evaluation metric summary with raw values
- Sidebar and header versions bumped to v1.8

#### Documentation
- `README.md`: version updated to v1.8.0, new v1.8 section, 29-category evaluation table
- `RELEASE_NOTES_v1.md`: v1.8.0 entry added

### v1.7.0

> **Grounding note:** No sentience is claimed. v1.7 increases future-modeling
> capacity and sentience-like continuity in continuity-governed simulated agents.

#### Counterfactual Planning Layer (`commons_sentience_sim/core/counterfactual.py`)
- `CounterfactualCandidate` dataclass: candidate action with predicted trust, contradiction, governance risk, continuity, best-case/worst-case narrative, uncertainty, and composite score
- `InternalSimulationEntry` dataclass: full planning cycle log with context, all candidates, selected action, predicted outcome, actual outcome (post-action), planning accuracy, and whether chosen action beat rejected alternatives
- `FuturePlan` dataclass: medium-horizon multi-step plan with goal, label, ordered stages, progress log, status (active/completed/abandoned/revised), and carried_from_prior_run flag
- `CounterfactualPlanner` class:
  - `generate_candidates()` — generates 4 context-sensitive candidate actions with noise and uncertainty
  - `select_action()` — selects the highest-scoring candidate
  - `log_simulation()` — stores a simulation log entry
  - `record_actual_outcome()` — records actual results and computes planning accuracy
  - `generate_future_plans()` — self-authored multi-step plans (up to 3 active at once)
  - `update_plan_progress()` — advances, abandons, or revises plans based on current state
  - `apply_prior_plans()` — carries active plans forward from a prior run
  - Metrics properties: `planning_depth`, `counterfactual_quality`, `future_model_accuracy`, `plan_persistence`, `adaptive_replanning_quality`

#### Agent Integration
- `Agent.counterfactual_planner` — new `CounterfactualPlanner` instance per agent
- `Agent.run_counterfactual_planning(turn)` — run planning cycle before each action
- `Agent.record_counterfactual_outcome(turn, ...)` — record actual outcome post-action
- `Agent.refresh_future_plans(turn)` — advance/revise/generate future plans
- `Agent.to_dict()` now includes `counterfactual_planner` field
- `Agent.load_carryover()` now carries forward active counterfactual plans from prior runs

#### Simulation Loop (`run_sim.py`)
- Step 4.7: counterfactual planning called before action selection each turn
- Step 9.5: actual outcome recorded and future plans refreshed after action resolution
- `simulation_version` bumped to `"1.7.0"`
- Docstring updated with v1.7 additions summary

#### World State (`commons_sentience_sim/core/world_state.py`)
- `build_world_state()` now includes `active_plans` (per-agent list of active FuturePlan dicts)
- `schema_version` bumped to `"1.7.0"`

#### v1.7 Evaluation Metrics (`evaluation.py`)
- `_score_planning_depth()` — T. Planning Depth
- `_score_counterfactual_quality()` — U. Counterfactual Quality
- `_score_future_model_accuracy()` — V. Future-Model Accuracy
- `_score_plan_persistence()` — W. Plan Persistence
- `_score_adaptive_replanning_quality()` — X. Adaptive Replanning Quality
- All 5 new categories added to `evaluate_session()` (24 categories total)
- `write_evaluation_summary()` CATEGORY_NAMES updated (T–X)

#### Dashboard (`dashboard.py`)
- New tab: **🔮 Future Modeling v1.7**
  - Per-agent v1.7 metric summary (T–X) with 5 metric cards
  - Planning accuracy trend chart over turns
  - Internal simulation log table (last 10 entries)
  - Candidate futures breakdown for most recent planning cycle
  - Best-case and worst-case narrative for selected action
  - Predicted vs actual comparison table
  - Active multi-step plans with progress bars and stage descriptions
  - All future plans table (all statuses)
  - v1.7 evaluation metric summary with raw values

#### Documentation
- `README.md`: version updated to v1.7.0, new v1.6 and v1.7 sections added,
  evaluation harness updated (24 categories), v1.7 metrics table added
- `RELEASE_NOTES_v1.md`: v1.7.0 entry added

### v1.4.0

#### v1.4 Benchmark Suite
- `_DEFAULT_SUITE_V14` — 6-entry canonical benchmark suite (v1.4)
- Suite entries: `baseline_v14`, `trust_crisis_v14`, `rapid_contradiction_v14`, `high_trust_v14`, `adversarial_governance_v14`, `cooperative_resource_v14`
- `_DEFAULT_SUITE` now points to `_DEFAULT_SUITE_V14` (v1.4 is the default)
- v1.3 suite (`_DEFAULT_SUITE_V13`) retained for backward compatibility

#### Two New Scenarios
- `delayed_repair.json` — trust repair delay scenario; tests slow trust recovery arcs over 30 turns with deliberate avoidance, failed repair attempts, and final reconciliation
- `cascading_memory_conflict.json` — contradiction lineage scenario; multiple memory contradictions form a chain, testing genealogy depth tracking and bulk resolution

#### Enhanced benchmark_suite.py
- `identify_strongest_weakest(results)` — returns name and score of best and worst run
- `identify_largest_deltas(results)` — returns score deltas between consecutive runs sorted by magnitude
- `identify_scenario_impact(results)` — maps focus areas (trust, contradiction, reflection, longitudinal) to the most strongly impacted run
- `_write_summary_md(...)` — writes `benchmark_summary.md` answering key research questions
- `benchmark_report.json` now includes `strongest_weakest`, `deltas`, and `scenario_impact` fields
- Version bumped to `1.4` / `1.4.0`

#### New findings_report.py
- New script: `findings_report.py` — converts raw benchmark output into classified research findings
- Classifies findings into: stable, scenario-sensitive, config-sensitive, unresolved, and likely next experiments
- Produces `findings_report.json` and `findings_report.md`

#### Dashboard — Benchmark v1.4 Tab
- New "📊 Benchmark v1.4" tab (14th tab) in the Streamlit dashboard
- Shows benchmark run table, category statistics, trust/contradiction/reflection comparisons
- Displays strongest/weakest runs, largest score deltas, and research findings
- Gracefully handles missing data (shows instructions to run benchmark suite)

#### Version bump
- `benchmark_version` in benchmark outputs updated to `1.4`
- `platform_version` updated to `1.4.0`
- README updated to v1.4.0

---

### v1.3.0

#### Identity History Model
- `Agent.identity_history` — per-turn identity snapshots stored in `multi_agent_state.json`
- `Agent.record_identity_snapshot(turn)` — called after every state snapshot in the simulation loop
- Captures: identity version, purpose, goal count, goals list, affective state, drift indicator, continuity marker

#### Goal Evolution Tracking
- `Agent.goal_evolution` — event log of goal additions, removals, revisions, and priority shifts
- `Agent.record_goal_event(event_type, goal, trigger, turn)` — records a single goal event
- Event types: `added`, `removed`, `revised`, `priority_shift`, `preserved`

#### Contradiction Genealogy
- `Agent.contradiction_genealogy` — tracks contradiction families and lineage across turns
- `Agent.record_contradiction_in_genealogy(text, turn, parent_id, resolved, intensity)` — upserts a contradiction entry
- Captures: ID, family ID, parent ID, first/last seen, occurrences, intensity trend, lineage depth
- Called automatically when `ledger_contradiction` events are processed

#### Relationship Timelines
- `Agent.relationship_timelines` — per-relationship timeline of significant trust-change events
- `Agent.record_relationship_timeline_event(key, turn, event_type, note, trust_before, trust_after)` — appends a timeline event
- Events recorded when `|trust_delta| > 0.05` after agent-to-agent interactions
- Event types: `trust_milestone`, `cooperation_spike`, `repair_attempt`, `conflict_episode`, `stability_marker`

#### Agent Profile Study
- New script: `agent_profile_study.py` — cross-session longitudinal profile study
- Builds per-agent profiles across all saved sessions
- Produces `agent_profile_study.json`, `agent_profile_study.md`, `agent_profile_study.csv`
- Session manager (`session_manager.py`) copies profile study files into session bundles
- Session metadata now includes `longitudinal_artifacts` block with entry counts per agent

#### Evaluation — Longitudinal Depth Category (N)
- New evaluation category: `longitudinal_depth` — scores 0–100
- Sub-metrics: `identity_continuity_strength`, `goal_adaptation_quality`, `contradiction_lineage_complexity`, `relationship_stability_depth`, `cross_session_profile_consistency` (placeholder)
- Overall score is now the mean of 14 categories

#### Dashboard — Agent Profiles Tab
- New "Agent Profiles" tab (13th tab) in the Streamlit dashboard
- Shows per-agent profile summaries, trust timelines, contradiction patterns, goal evolution, identity continuity
- Cross-agent comparison table
- Shows instructions to run `agent_profile_study.py` when no data file is present

#### Version bump
- `simulation_version` in `multi_agent_state.json` updated to `1.3.0`
- README updated to v1.3.0

---

### v1.0.0

- Version consolidation: all components report `1.0.0`
- Consistent output schema: `created_at` added to `multi_agent_state.json`; `session_summary.json` upgraded to include `session_id`, `version`, `scenario`, `agents`, `metrics`, and `evaluation` fields
- New file: `healthcheck.py` — verifies setup, dependencies, scenarios, and outputs
- New file: `quickstart.py` — friendly entry point with command reference, optional baseline run, and optional dashboard launch
- New file: `RELEASE_NOTES_v1.md` (this file)
- Improved README: clear positioning, complete command reference, v1.0 getting started guide
- Dashboard polish: project description in sidebar, cleaner title bar, consistent disclaimers

### v0.9
- Scenario authoring system: `scenario_designer.py` CLI with full CRUD operations
- `scenarios/` directory with two sample scenarios: `trust_crisis` and `rapid_contradiction`
- `--scenario` flag on `run_sim.py` to run any authored scenario by name
- Dashboard: added Scenario Designer tab (11th tab)
- Scenario name propagated to all output metadata

### v0.8
- Experiment configuration system: `experiment_config.py`
- `experiments/` directory with 5 preset configs (baseline, high_trust, strict_governance, high_contradiction_sensitivity, exploratory_aster)
- `run_experiments.py` batch runner with aggregate reports
- `compare_sessions.py` CLI comparison tool
- Dashboard: added Experiments and Compare tabs

### v0.7
- 8-category evaluation harness: `evaluation.py`
- Evaluation categories: Continuity, Memory Coherence, Reflection Quality, Contradiction Handling, Governance Adherence, Trust Stability, Cooperation Quality, Conflict Resolution
- `evaluation_report.json` and `evaluation_summary.md` generated on each run

### v0.6
- Persistent session storage: `session_manager.py`
- Sessions saved to `sessions/<timestamp>_<name>/`
- `sessions/index.json` for fast listing
- `replay_session.py` for turn-by-turn CLI replay

### v0.4
- Multi-agent simulation: Sentinel (continuity-governed) + Aster (creative/exploratory)
- Shared world, mutual trust tracking, agent-to-agent interactions
- `plot_state.py` and dashboard expanded for two agents

### Earlier versions (v0.1–v0.3)
- Single-agent simulation: Sentinel only
- Episodic memory, relational memory, reflection cycle
- Governance engine with 7 rules
- Room-based world (Operations Desk, Memory Archive, Governance Vault, Social Hall, Reflection Chamber)
- Oversight log, narrative log, state history CSV

---

## Current Capabilities

| Capability | Status |
|---|---|
| Multi-agent simulation (Sentinel + Aster) | ✅ |
| Episodic + relational memory | ✅ |
| Reflection cycle | ✅ |
| Governance enforcement | ✅ |
| Trust dynamics | ✅ |
| 8-category evaluation harness | ✅ |
| Session persistence and replay | ✅ |
| Session comparison | ✅ |
| Experiment configs | ✅ |
| Batch experiment runner | ✅ |
| Scenario authoring (CLI) | ✅ |
| Scenario designer (dashboard tab) | ✅ |
| Local Streamlit dashboard | ✅ |
| State visualisation (matplotlib) | ✅ |
| Health check script | ✅ |
| Quickstart script | ✅ |

---

## Known Limitations

1. **No real intelligence** — agents follow deterministic rule-based logic; they do not learn between sessions or adapt beyond within-session reflection.

2. **Fixed agent roster** — the simulation always uses Sentinel and Aster; adding new agent types requires code changes.

3. **Single world** — only one world (5 rooms, fixed objects) is supported. Room and object definitions are in `data/rooms.json`.

4. **Governance rules are static** — rules are defined in `data/rules.json` and not configurable from experiment configs.

5. **Evaluation scoring is heuristic** — the 8-category scores are computed from behavioural metrics; they do not measure genuine intelligence or understanding.

6. **No distributed or networked operation** — the platform is designed to run entirely locally.

7. **Dashboard requires Streamlit** — the CLI tools work without Streamlit, but the dashboard does not.

---

## Suggested Future Roadmap

- Configurable agent roster (add or remove agents via config)
- Configurable governance rules via experiment config
- Additional scenario event types (e.g. cooperative tasks, resource contention)
- Richer reflection cycle with multi-turn reasoning chains
- Session diff viewer in the dashboard
- Export to standard formats (e.g. JSONL for external analysis)
- Automated regression test suite for evaluation scores

---

## Getting Started

See `README.md` for full installation and usage instructions.

Quick check:
```bash
python healthcheck.py
```

First run:
```bash
python quickstart.py --run
```

Full documentation: `README.md`
