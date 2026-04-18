# Reality Audit ↔ Commons Sentience Sim — Integration Plan

## Status: Plan only. No code implemented.

---

## 1. What exists in commons_sentience_sim

| Component | File | Role |
|---|---|---|
| `World` | `core/world.py` | Room-graph navigation. `observe(room)` returns a dict of visible objects and actions. |
| `Agent` | `core/agent.py` | Narrative/deliberative agent. Chooses actions, stores episodic memories, tracks goals. |
| `GovernanceEngine` | `core/governance.py` | Per-action oversight log. |
| `WorldState` | `core/world_state.py` | Persistent JSON snapshot of rooms/tensions/contradictions across runs. |
| `run_sim.py` | root | Orchestration: loads agents, world, runs turn loop, evaluates, saves. |

The sim is turn-based and text-oriented. It has **no physics, no 2D positions, no velocity, no numeric control loop**. `World.observe()` returns {"room_name": ..., "actions": [...], "objects": [...]} — discrete, not continuous.

---

## 2. Where Reality Audit could connect

### Option A — Wrap the existing World as a RealityAudit WorldAdapter

**Idea:** Implement a `CommonsWorldAdapter` that wraps `commons_sentience_sim.core.world.World` and exposes the `RealityWorld` step interface. Physical state becomes room-graph state.

**What it would map:**
- `position` → numeric encoding of room index (e.g. room index in adjacency list)
- `velocity` → net displacement between turns (rooms traversed per turn)
- `measured_position` → agent's self-reported room (can diverge if memory is wrong)
- `control_input` → the chosen action/room-move proposed by the agent
- `hidden_state` → world's true room conditions (tension level, object states)

**Required new file:** `reality_audit/adapters/commons_world_adapter.py`

**Risks:**
- Room-graph positions are categorical, not continuous. Metrics like `position_error` lose meaning unless a numeric room-distance function is defined.
- The relationship `position → measured_position` doesn't exist in the existing World; measurement fidelity would have to be mocked.
- The World doesn't have `dt` or time — turns are discrete. `convergence_time` would measure turns, not seconds.

**Feasibility: Medium.** Viable with a thin adapter + redefined metric semantics.

---

### Option B — Hook Reality Audit experiments into the turn loop

**Idea:** Inside `run_sim.py`, after each agent turn, inject a Reality Audit probe step that records world + measurement state.

**Where to add it in run_sim.py:**
```python
# After line ~241 where agent.check_and_log_action(...) is called:
if reality_audit_runner:
    reality_audit_runner.probe(agent, world, turn)
```

**Required new file:** `reality_audit/adapters/sim_probe.py`

`SimProbe.probe(agent, world, turn)` would:
1. Extract room-index as position.
2. Extract agent.retrieve_memories() as a proxy for measured state.
3. Compare against world.observe(room).
4. Append to a raw_log.
5. After the run, call `MeasurementSuite` on the log.

**Risks:**
- `agent.retrieve_memories()` returns semantic strings, not numeric positions. A feature extraction step is needed.
- Memory retrieval is weighted probabilistic — the same state can be perceived differently each call. This is a feature for observer-dependence tests but makes baselines noisy.
- Governance oversight logs (`agent.check_and_log_action`) don't expose control effort numerically.

**Feasibility: High** for qualitative metrics (convergence, stability score). Low for physical metrics (position error, path smoothness).

---

### Option C — Replace commons_sentience_sim World with a RealityWorld backend

**Idea:** For specific audit experiments, substitute the room-based World with `RealityWorld` as the environment, and use an `Agent`-compatible wrapper that produces action text from controller output.

**Required new files:**
- `reality_audit/adapters/agent_controller_bridge.py` — converts `Agent.choose_action()` output to a `Vector2` control input.
- `reality_audit/adapters/physics_world_room.py` — implements Room-like interface backed by `RealityWorld.step()`.

**Risks:**
- Agent's LLM-style action selection ("explore the archive room") cannot be trivially mapped to a 2D vector without a translation layer.
- Agent internal state (goals, identity, memory) depends on room names and narrative context — replacing the world breaks agent coherence.

**Feasibility: Low** without significant agent refactoring.

---

## 3. Required adapters (actionable file list)

| File | Purpose | Depends on |
|---|---|---|
| `reality_audit/adapters/__init__.py` | Package init | — |
| `reality_audit/adapters/commons_world_adapter.py` | Maps `World` rooms to `RealityWorld`-compatible state at each turn | `commons_sentience_sim.core.world.World`, `reality_audit.world.WorldState` |
| `reality_audit/adapters/sim_probe.py` | Attaches to `run_sim.py` turn loop; records per-turn state + measurements | `commons_sentience_sim.core.agent.Agent`, `reality_audit.measurement.MeasurementSuite` |
| `reality_audit/adapters/room_distance.py` | Numeric distance function over room graph (BFS shortest path) | `commons_sentience_sim.core.world.World` |
| `reality_audit/adapters/agent_observation_tap.py` | Intercepts `Agent.retrieve_memories()` to produce numeric fidelity score | `commons_sentience_sim.core.agent.Agent` |

---

## 4. Shared interfaces needed

1. **Turn-timestep alignment:** Reality Audit uses `dt`-based continuous time; commons_sentience_sim uses integer turns. Adapter must define `dt = turn_duration_seconds` (suggested: 1.0 s/turn for plotting).

2. **Position encoding:** A `RoomPositionEncoder` that assigns a stable (x, y) coordinate to each room based on adjacency-graph layout. BFS-derived layout or manual coordinate file.

3. **Observation fidelity model:** A function `perceived_state(agent, world, room)` that returns what the agent "sees" vs. what is objectively true — enabling observer-dependence scoring.

4. **Metric adapter:** `MeasurementSuite` expects dicts with `measured_position`, `measured_velocity`, `hidden_state`. The sim probe adapter must construct these dicts from agent + world state each turn.

---

## 5. Risks and open questions

| Risk | Severity | Notes |
|---|---|---|
| Categorical room positions break continuous metrics | High | Must define a room coordinate system before any metric is meaningful |
| Agent memory is non-deterministic even with fixed seed | Medium | `retrieve_weighted()` uses salience decay — may introduce irreproducible jitter |
| No velocity in the existing sim | Medium | Could proxy as rooms-per-turn; physically meaningless for path smoothness |
| Observer-dependence test is trivially True in existing sim | Low | Agent already has imperfect memory of world state — distinction from physics may be lost |
| run_sim.py has no test coverage | Medium | Injecting probe hooks risks silent failures |

---

## 6. Recommended first step

Implement **Option B** (SimProbe) with a `RoomPositionEncoder` first, because:
- It requires the fewest changes to existing code.
- It only adds read-only hooks to the turn loop.
- It produces a real-time measurement log that can immediately feed `MeasurementSuite`.
- It is reversible: remove the probe and run_sim.py is unchanged.

Estimated files to create: 3 (`sim_probe.py`, `room_distance.py`, `commons_world_adapter.py`).
Estimated files to modify: 1 (`run_sim.py`, ~10 lines added inside the turn loop).
