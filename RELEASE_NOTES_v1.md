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

### v1.0.0 (current)
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
