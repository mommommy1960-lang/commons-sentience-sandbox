"""
Commons Sentience Sandbox — Local Research Dashboard (v1.0)

A lightweight Streamlit dashboard for observing simulation state.
Supports:
  - session selection (saved runs or latest output)
  - turn-by-turn replay
  - side-by-side session comparison
  - evaluation scores per session
  - experiment config browser and aggregate scores
  - scenario browser and event designer
  - auto-refresh

Run with:
    streamlit run dashboard.py
"""

import csv
import json
import os
import time
from pathlib import Path

import streamlit as st
from evaluation import _interpret as eval_interpret
from experiment_config import list_available_configs
from scenario_designer import (
    EVENT_TYPES,
    ROOMS,
    AGENTS,
    AGENT_INTERACTION_TYPES,
    AFFECTIVE_KEYS,
    list_available_scenarios,
    load_scenario,
    save_scenario,
    validate_scenario,
    preview_scenario,
    _next_id,
    _default_save_path,
)
from session_manager import (
    SESSIONS_DIR,
    compare_sessions,
    list_sessions,
    load_session_metadata,
)

# ---------------------------------------------------------------------------
# Continuity study loader helper
# ---------------------------------------------------------------------------


def load_continuity_study(study_dir: Path) -> dict:
    """Load continuity_study.json from *study_dir* or sessions/."""
    path = study_dir / "continuity_study.json"
    if not path.exists():
        path = SESSIONS_DIR / "continuity_study.json"
    return load_json(path)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).parent
OUTPUT_DIR = ROOT / "commons_sentience_sim" / "output"

PLOT_NAMES = [
    "trust_plot.png",
    "urgency_plot.png",
    "contradiction_plot.png",
    "agent_trust_plot.png",
    "queen_trust_plot.png",
    "interactions_plot.png",
]

PLOT_LABELS = {
    "trust_plot.png": "Trust over time (Sentinel)",
    "urgency_plot.png": "Urgency over time (Sentinel)",
    "contradiction_plot.png": "Contradiction pressure (Sentinel)",
    "agent_trust_plot.png": "Mutual trust between agents",
    "queen_trust_plot.png": "Trust in Queen (per agent)",
    "interactions_plot.png": "Cooperation vs conflict",
}

# ---------------------------------------------------------------------------
# Helpers — generic I/O
# ---------------------------------------------------------------------------


def _mtime(path: Path) -> float:
    try:
        return os.path.getmtime(path)
    except OSError:
        return 0.0


def load_json(path: Path) -> dict:
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}


def load_csv(path: Path) -> list[dict]:
    try:
        with open(path, newline="", encoding="utf-8") as fh:
            return list(csv.DictReader(fh))
    except OSError:
        return []


def load_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# Cache helpers keyed on (directory, mtime-tuple).
# Cache auto-invalidates when files change or a different session is selected.
# ---------------------------------------------------------------------------


def _dir_mtimes(d: Path) -> tuple:
    files = [
        "multi_agent_state.json",
        "state_history.csv",
        "oversight_log.csv",
        "agent_relationships.csv",
        "interaction_log.csv",
        "narrative_log.md",
        "evaluation_report.json",
    ]
    return (str(d),) + tuple(_mtime(d / f) for f in files)


@st.cache_data
def get_multi_agent_state(cache_key: tuple) -> dict:
    return load_json(Path(cache_key[0]) / "multi_agent_state.json")


@st.cache_data
def get_state_history(cache_key: tuple) -> list[dict]:
    return load_csv(Path(cache_key[0]) / "state_history.csv")


@st.cache_data
def get_oversight_log(cache_key: tuple) -> list[dict]:
    return load_csv(Path(cache_key[0]) / "oversight_log.csv")


@st.cache_data
def get_agent_relationships(cache_key: tuple) -> list[dict]:
    return load_csv(Path(cache_key[0]) / "agent_relationships.csv")


@st.cache_data
def get_interaction_log(cache_key: tuple) -> list[dict]:
    return load_csv(Path(cache_key[0]) / "interaction_log.csv")


@st.cache_data
def get_narrative_log(cache_key: tuple) -> str:
    return load_text(Path(cache_key[0]) / "narrative_log.md")


@st.cache_data
def get_evaluation_report(cache_key: tuple) -> dict:
    return load_json(Path(cache_key[0]) / "evaluation_report.json")


@st.cache_data
def get_sessions_list(_ts: float) -> list[dict]:
    """Reload sessions list when index.json changes."""
    return list_sessions()


# ---------------------------------------------------------------------------
# Page config  (must be the first Streamlit call)
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Commons Sentience Dashboard",
    page_icon="\U0001f9e0",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

st.sidebar.title("\U0001f9e0 Commons Sentience Sandbox")
st.sidebar.markdown("**Local Research Dashboard \u2014 v1.9**")
st.sidebar.caption(
    "A research platform for continuity-governed simulated agents. "
    "Not a real AI \u2014 no sentience is claimed."
)
st.sidebar.divider()

# Session selector
sessions_index_mtime = _mtime(SESSIONS_DIR / "index.json")
sessions = get_sessions_list(sessions_index_mtime)

session_options = ["Latest (output/)"] + [s["session_id"] for s in sessions]
selected_label = st.sidebar.selectbox(
    "Active session",
    session_options,
    index=0,
    help="Select a saved session or view the latest simulation output.",
)

if selected_label == "Latest (output/)":
    active_dir: Path = OUTPUT_DIR
    active_session_id: str | None = None
    active_session_meta: dict = {}
else:
    active_session_id = selected_label
    active_dir = SESSIONS_DIR / active_session_id
    active_session_meta = load_session_metadata(active_session_id)

st.sidebar.divider()

if st.sidebar.button("Refresh now"):
    st.cache_data.clear()
    st.rerun()

auto_refresh = st.sidebar.checkbox("Auto-refresh every 10 s", value=False)
st.sidebar.divider()
st.sidebar.markdown(
    "**Run commands**\n"
    "```\n"
    "# Simulation\n"
    "python run_sim.py\n"
    "python run_sim.py --name baseline\n"
    "python run_sim.py --config high_trust\n\n"
    "# Batch experiments\n"
    "python run_experiments.py\n"
    "python run_experiments.py --configs baseline high_trust\n\n"
    "# Plots\n"
    "python plot_state.py\n\n"
    "# Dashboard\n"
    "streamlit run dashboard.py\n\n"
    "# Replay\n"
    "python replay_session.py --list\n"
    "python replay_session.py --session <id>\n\n"
    "# Compare\n"
    "python compare_sessions.py \\\n"
    "  --session-a <id> --session-b <id>\n"
    "```"
)

# ---------------------------------------------------------------------------
# Load data from active directory
# ---------------------------------------------------------------------------

_ck = _dir_mtimes(active_dir)
state_data = get_multi_agent_state(_ck)
state_history = get_state_history(_ck)
oversight_log = get_oversight_log(_ck)
agent_relationships = get_agent_relationships(_ck)
interaction_log = get_interaction_log(_ck)
narrative_log = get_narrative_log(_ck)
evaluation_report = get_evaluation_report(_ck)

simulation_version = state_data.get("simulation_version", "unknown")
total_turns = state_data.get("total_turns", "?")
agents_data: dict = state_data.get("agents", {})

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.title("\U0001f9e0 Commons Sentience Sandbox")
st.markdown("**Local Research Dashboard \u2014 v1.9** \u00b7 Research platform for continuity-governed simulated agents")
if active_session_id:
    st.caption(
        f"v{simulation_version}  \u00b7  Session: `{active_session_id}`  \u00b7  "
        f"Directory: `{active_dir}`"
    )
else:
    st.caption(f"v{simulation_version}  \u00b7  Latest output: `{active_dir}`")

if not state_data:
    st.error(
        "No simulation data found. "
        "Run `python run_sim.py` to generate output files, then refresh."
    )
    st.stop()

# ---------------------------------------------------------------------------
# Tab layout
# ---------------------------------------------------------------------------

(
    tab_overview,
    tab_agents,
    tab_rooms,
    tab_memory,
    tab_interactions,
    tab_charts,
    tab_replay,
    tab_compare,
    tab_eval,
    tab_exp,
    tab_scenario,
    tab_continuity,
    tab_profiles,
    tab_benchmark,
    tab_selfmodel,
    tab_counterfactual,
    tab_inquiry,
    tab_identity,
    tab_narrative_v2,
) = st.tabs(
    [
        "Overview",
        "Agents",
        "Rooms",
        "Memory",
        "Interactions",
        "Charts",
        "Replay",
        "Compare",
        "Evaluation",
        "Experiments",
        "Scenario Designer",
        "Continuity Study",
        "Agent Profiles",
        "📊 Benchmark v1.4",
        "🧠 Self Model v1.5",
        "🔮 Future Modeling v1.7",
        "❓ Inquiry / Uncertainty v1.8",
        "🪞 Identity / Narrative v1.9",
        "📖 Narrative Identity v2.0",
    ]
)

# ===========================================================================
# TAB A — Simulation Overview
# ===========================================================================

with tab_overview:
    st.header("Simulation Overview")

    current_turn = total_turns
    if state_history:
        last_row = state_history[-1]
        current_turn = last_row.get("turn", total_turns)
        last_action = last_row.get("action", "\u2014")
        last_event = last_row.get("event_type", "\u2014")
    else:
        last_action = "\u2014"
        last_event = "\u2014"

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Current Turn", current_turn)
    col2.metric("Total Turns", total_turns)
    col3.metric("Last Action", last_action)
    col4.metric("Last Event Type", last_event)

    # Session metadata panel (only when a saved session is active)
    if active_session_meta:
        st.divider()
        st.subheader("Session Metadata")
        m = active_session_meta
        meta_cols = st.columns(3)
        meta_cols[0].markdown(f"**Session ID:** `{m.get('session_id', '\u2014')}`")
        meta_cols[1].markdown(f"**Created:** {m.get('created_at', '\u2014')[:19]}")
        meta_cols[2].markdown(f"**Version:** {m.get('simulation_version', '\u2014')}")

        summary = m.get("summary", {})
        if summary:
            st.markdown("**Summary Metrics**")
            s_cols = st.columns(5)
            s_cols[0].metric(
                "S trust in Queen",
                f"{summary.get('sentinel_trust_in_queen', 0):.2f}",
            )
            s_cols[1].metric(
                "A trust in Queen",
                f"{summary.get('aster_trust_in_queen', 0):.2f}",
            )
            s_cols[2].metric(
                "Mutual trust",
                f"{summary.get('mutual_trust_sentinel_aster', 0):.2f}",
            )
            s_cols[3].metric("Cooperation", summary.get("cooperation_events", 0))
            s_cols[4].metric("Conflict", summary.get("conflict_events", 0))

    st.divider()
    st.subheader("Recent Turn History (last 10 turns)")
    if state_history:
        recent = state_history[-10:][::-1]
        st.table(
            [
                {
                    "Turn": r.get("turn", ""),
                    "Room": r.get("room", ""),
                    "Action": r.get("action", ""),
                    "Event Type": r.get("event_type", ""),
                    "Urgency": r.get("urgency", ""),
                    "Trust": r.get("trust", ""),
                    "Contradiction Pressure": r.get("contradiction_pressure", ""),
                }
                for r in recent
            ]
        )
    else:
        st.info("No state history available.")

    st.divider()
    st.subheader("Governance Audit \u2014 Recent Actions")
    if oversight_log:
        recent_oversight = oversight_log[-10:][::-1]
        st.table(
            [
                {
                    "Turn": r.get("turn", ""),
                    "Room": r.get("room", ""),
                    "Action": r.get("action", ""),
                    "Permitted": r.get("permitted", ""),
                    "Reason": r.get("reason", ""),
                    "Event Type": r.get("event_type", ""),
                }
                for r in recent_oversight
            ]
        )
    else:
        st.info("No oversight log available.")

# ===========================================================================
# TAB B — Agent Panels
# ===========================================================================

with tab_agents:
    st.header("Agent Panels")

    if not agents_data:
        st.info("No agent data found.")
    else:
        agent_names = list(agents_data.keys())
        cols = st.columns(len(agent_names))
        for col, agent_name in zip(cols, agent_names):
            agent = agents_data[agent_name]
            affective = agent.get("affective_state", {})
            identity = agent.get("identity", {})
            goals = agent.get("goals", [])
            relationships = agent.get("agent_relationships", {})
            relational_memory = agent.get("relational_memory", {})

            recent_action = "\u2014"
            if agent_name == "Sentinel" and state_history:
                recent_action = state_history[-1].get("action", "\u2014")

            with col:
                st.subheader(f"Agent: {agent_name}")
                purpose = identity.get("purpose", "")
                st.caption(purpose[:120] + ("\u2026" if len(purpose) > 120 else ""))

                st.markdown(f"**Room:** `{agent.get('active_room', '\u2014')}`")
                st.markdown(
                    f"**Turn:** {agent.get('turn', '\u2014')}  |  "
                    f"**Memories:** {agent.get('episodic_memory_count', 0)}"
                )

                st.markdown("**Affective State**")
                m1, m2 = st.columns(2)
                m1.metric("Urgency", f"{affective.get('urgency', 0):.2f}")
                m2.metric("Trust", f"{affective.get('trust', 0):.2f}")
                m3, m4 = st.columns(2)
                m3.metric(
                    "Contradiction Pressure",
                    f"{affective.get('contradiction_pressure', 0):.2f}",
                )
                m4.metric("Recovery", f"{affective.get('recovery', 0):.2f}")

                st.divider()

                queen_trust = relational_memory.get("Queen", {}).get(
                    "trust_level", None
                )
                st.markdown(
                    f"**Trust in Queen:** `{queen_trust:.2f}`"
                    if queen_trust is not None
                    else "**Trust in Queen:** \u2014"
                )

                for other_name, rel in relationships.items():
                    st.markdown(
                        f"**Trust in {other_name}:** `{rel.get('trust', 0):.2f}`  "
                        f"(coop: {rel.get('cooperation_count', 0)}, "
                        f"conflict: {rel.get('conflict_count', 0)})"
                    )

                st.divider()
                st.markdown(f"**Most Recent Action:** `{recent_action}`")
                st.divider()

                with st.expander("Goals", expanded=False):
                    for g in goals:
                        st.markdown(f"- {g}")

                reflections = agent.get("reflection_entries", [])
                if reflections:
                    latest_ref = reflections[-1]
                    with st.expander("Latest Reflection", expanded=False):
                        st.markdown(
                            f"**Turn {latest_ref.get('turn', '?')} \u2014 "
                            f"{latest_ref.get('trigger', '')}**"
                        )
                        for field in (
                            "what_happened",
                            "what_mattered",
                            "what_conflicted",
                            "what_changed",
                            "future_adjustment",
                        ):
                            val = latest_ref.get(field)
                            if val:
                                st.markdown(
                                    f"**{field.replace('_', ' ').title()}:** {val}"
                                )

# ===========================================================================
# TAB C — Room View
# ===========================================================================

with tab_rooms:
    st.header("Room View")

    agent_room_map: dict[str, list[str]] = {}
    for agent_name, agent in agents_data.items():
        room = agent.get("active_room", "\u2014")
        agent_room_map.setdefault(room, []).append(agent_name)

    rooms_path = ROOT / "commons_sentience_sim" / "data" / "rooms.json"
    rooms_data: dict = load_json(rooms_path)

    room_names = (
        list(rooms_data.keys()) if rooms_data else list(agent_room_map.keys())
    )
    if not room_names:
        st.info("No room data available.")
    else:
        for room_name in room_names:
            agents_here = agent_room_map.get(room_name, [])
            agent_badge = (
                " \u00b7 ".join(f"**{a}**" for a in agents_here)
                if agents_here
                else ""
            )
            header_text = f"Room: {room_name}"
            if agent_badge:
                header_text += f"  \u2014  {agent_badge}"

            with st.expander(header_text, expanded=bool(agents_here)):
                room_info = rooms_data.get(room_name, {})

                if room_info.get("description"):
                    st.caption(room_info["description"])

                objects = room_info.get("objects", {})
                if objects:
                    st.markdown("**Objects & States**")
                    obj_rows = []
                    for obj_name, obj_data in objects.items():
                        if isinstance(obj_data, dict):
                            state = obj_data.get("state", "\u2014")
                            desc = obj_data.get("description", "")
                            obj_rows.append(
                                {
                                    "Object": obj_name,
                                    "State": state,
                                    "Description": (
                                        (desc[:80] + "\u2026")
                                        if len(desc) > 80
                                        else desc
                                    ),
                                }
                            )
                        else:
                            obj_rows.append(
                                {
                                    "Object": obj_name,
                                    "State": str(obj_data),
                                    "Description": "",
                                }
                            )
                    st.table(obj_rows)

                actions = room_info.get("actions", room_info.get("interactions", []))
                if actions:
                    st.markdown(
                        "**Available Actions:** "
                        + " \u00b7 ".join(f"`{i}`" for i in actions)
                    )

                connected = room_info.get("connected_rooms", [])
                if connected:
                    st.markdown("**Connected Rooms:** " + " \u2192 ".join(connected))

# ===========================================================================
# TAB D — Memory View
# ===========================================================================

with tab_memory:
    st.header("Memory View")

    if not agents_data:
        st.info("No agent data found.")
    else:
        for agent_name, agent in agents_data.items():
            st.subheader(f"Agent: {agent_name}")

            episodic = agent.get("episodic_memory", [])
            with st.expander(
                f"Episodic Memories ({len(episodic)} total \u2014 showing last 10)",
                expanded=False,
            ):
                if episodic:
                    for mem in episodic[-10:][::-1]:
                        turn_label = f"T{mem.get('turn', '?')}"
                        st.markdown(
                            f"**{turn_label}** `{mem.get('room', '')}` \u2014 "
                            f"{mem.get('summary', '')}  \n"
                            f"*Resonance:* `{mem.get('emotional_resonance', '')}` \u00b7 "
                            f"*Salience:* {mem.get('salience', 0):.2f} \u00b7 "
                            f"*Importance:* {mem.get('importance', 0):.2f}"
                            + (" *(compressed)*" if mem.get("compressed") else "")
                        )
                        st.divider()
                else:
                    st.info("No episodic memories recorded.")

            relational = agent.get("relational_memory", {})
            with st.expander(
                f"Relational Memories ({len(relational)} relationships)",
                expanded=False,
            ):
                if relational:
                    for human_name, rel in relational.items():
                        st.markdown(f"**{human_name}**")
                        st.markdown(
                            f"- Interactions: {rel.get('interaction_count', 0)}  "
                            f"| Trust: {rel.get('trust_level', 0):.2f}  "
                            f"| Last seen turn: {rel.get('last_seen_turn', '\u2014')}"
                        )
                        notes = rel.get("notes", [])
                        if notes:
                            st.markdown("*Recent notes:*")
                            for note in notes[-3:]:
                                st.markdown(f"> {note}")
                        st.divider()
                else:
                    st.info("No relational memories recorded.")

            reflections = agent.get("reflection_entries", [])
            with st.expander(
                f"Reflection Entries ({len(reflections)} total)", expanded=False
            ):
                if reflections:
                    for ref in reversed(reflections):
                        st.markdown(
                            f"**Turn {ref.get('turn', '?')} \u2014 Trigger:** "
                            f"`{ref.get('trigger', '')}`"
                        )
                        for field in (
                            "what_happened",
                            "what_mattered",
                            "what_conflicted",
                            "what_changed",
                            "future_adjustment",
                        ):
                            val = ref.get(field)
                            if val:
                                st.markdown(
                                    f"- **{field.replace('_', ' ').title()}:** {val}"
                                )
                        narrative = ref.get("narrative")
                        if narrative:
                            st.markdown(f"*{narrative}*")
                        st.divider()
                else:
                    st.info("No reflection entries recorded.")

            st.divider()

# ===========================================================================
# TAB E — Interaction View
# ===========================================================================

with tab_interactions:
    st.header("Interaction View")

    if not interaction_log and not agent_relationships:
        st.info("No interaction data found.")
    else:
        st.subheader("Summary")
        coop_count = sum(
            1 for r in interaction_log if r.get("outcome") == "cooperated"
        )
        conflict_count = sum(
            1
            for r in interaction_log
            if r.get("outcome") in ("deferred", "conflict", "resolved")
        )

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Interactions", len(interaction_log))
        col2.metric("Cooperative", coop_count)
        col3.metric("Conflict / Deferred", conflict_count)

        conflict_points = [
            r.get("conflict_point", "")
            for r in interaction_log
            if r.get("conflict_point")
        ]
        if conflict_points:
            st.markdown(f"**Latest Conflict Point:** {conflict_points[-1]}")

        st.divider()
        st.subheader("Agent Relationships")
        if agent_relationships:
            st.table(
                [
                    {
                        "Observer": r.get("observer", ""),
                        "Subject": r.get("subject", ""),
                        "Trust": r.get("trust", ""),
                        "Reliability": r.get("perceived_reliability", ""),
                        "Conflicts": r.get("conflict_count", ""),
                        "Cooperations": r.get("cooperation_count", ""),
                        "Last Interaction Turn": r.get("last_interaction_turn", ""),
                    }
                    for r in agent_relationships
                ]
            )

        st.divider()
        st.subheader("Interaction Log (most recent first)")
        if interaction_log:
            for row in reversed(interaction_log):
                outcome = row.get("outcome", "")
                badge = (
                    "[COOP]"
                    if outcome == "cooperated"
                    else ("[CONFLICT]" if outcome in ("deferred", "conflict") else "[RESOLVED]")
                )
                with st.expander(
                    f"{badge} Turn {row.get('turn', '?')} \u00b7 "
                    f"{row.get('interaction_type', '')} "
                    f"({row.get('initiator', '')} <-> {row.get('respondent', '')})",
                    expanded=False,
                ):
                    col_a, col_b = st.columns(2)
                    col_a.markdown(f"**Room:** {row.get('room', '\u2014')}")
                    col_b.markdown(f"**Outcome:** `{outcome}`")

                    col_c, col_d = st.columns(2)
                    col_c.markdown(
                        f"**{row.get('initiator', '')} dominant value:** "
                        f"`{row.get('initiator_dominant_value', '\u2014')}`"
                    )
                    col_d.markdown(
                        f"**{row.get('respondent', '')} dominant value:** "
                        f"`{row.get('respondent_dominant_value', '\u2014')}`"
                    )

                    ti = row.get("trust_delta_i_to_r", "")
                    tr_ = row.get("trust_delta_r_to_i", "")
                    if ti or tr_:
                        st.markdown(
                            f"**Trust delta:** {row.get('initiator', '')} "
                            f"\u2192 {row.get('respondent', '')}: `{ti}` | "
                            f"{row.get('respondent', '')} "
                            f"\u2192 {row.get('initiator', '')}: `{tr_}`"
                        )

                    if row.get("conflict_point"):
                        st.markdown(f"**Conflict point:** {row['conflict_point']}")

                    if row.get("narrative"):
                        st.markdown(f"*{row['narrative']}*")
        else:
            st.info("No interactions recorded.")

# ===========================================================================
# TAB F — Charts
# ===========================================================================

with tab_charts:
    st.header("Charts")
    st.caption(
        "Generated by `plot_state.py`. Re-run it after a new simulation to refresh."
    )

    available = {
        PLOT_LABELS[p]: active_dir / p
        for p in PLOT_NAMES
        if (active_dir / p).exists()
    }
    missing = [PLOT_LABELS[p] for p in PLOT_NAMES if not (active_dir / p).exists()]

    if missing:
        st.warning(
            "Some plots are missing. Run `python plot_state.py` to generate them:\n"
            + "\n".join(f"- {t}" for t in missing)
        )

    if not available:
        st.info("No plots available yet. Run `python plot_state.py` first.")
    else:
        plot_items = list(available.items())
        for i in range(0, len(plot_items), 2):
            row_cols = st.columns(2)
            for col, (title, path) in zip(row_cols, plot_items[i : i + 2]):
                with col:
                    st.subheader(title)
                    st.image(str(path), use_container_width=True)

# ===========================================================================
# TAB G — Replay
# ===========================================================================

with tab_replay:
    st.header("Session Replay")
    st.caption(
        "Step through the simulation turn by turn. "
        "Use the slider or the Prev / Next buttons."
    )

    if not state_history:
        st.info(
            "No state history available in the selected session. "
            "Select a session from the sidebar or run `python run_sim.py`."
        )
    else:
        n_turns = len(state_history)

        replay_col1, replay_col2, replay_col3 = st.columns([1, 8, 1])

        with replay_col1:
            prev_clicked = st.button("Prev", key="replay_prev")

        with replay_col3:
            next_clicked = st.button("Next", key="replay_next")

        # Persist turn index and active_dir across Streamlit reruns
        if "replay_turn_idx" not in st.session_state:
            st.session_state.replay_turn_idx = 0

        # Reset when session changes
        if st.session_state.get("replay_active_dir") != str(active_dir):
            st.session_state.replay_turn_idx = 0
            st.session_state.replay_active_dir = str(active_dir)

        if prev_clicked:
            st.session_state.replay_turn_idx = max(
                0, st.session_state.replay_turn_idx - 1
            )
        if next_clicked:
            st.session_state.replay_turn_idx = min(
                n_turns - 1, st.session_state.replay_turn_idx + 1
            )

        with replay_col2:
            selected_turn = st.slider(
                "Turn",
                min_value=1,
                max_value=n_turns,
                value=st.session_state.replay_turn_idx + 1,
                key="replay_slider",
            )
            st.session_state.replay_turn_idx = selected_turn - 1

        idx = st.session_state.replay_turn_idx
        row = state_history[idx]
        turn_num = row.get("turn", idx + 1)

        st.divider()
        st.subheader(f"Turn {turn_num} / {n_turns}")

        rc1, rc2, rc3, rc4 = st.columns(4)
        rc1.metric("Room (Sentinel)", row.get("room", "\u2014"))
        rc2.metric("Action", row.get("action", "\u2014"))
        rc3.metric("Event Type", row.get("event_type", "\u2014"))
        rc4.metric("Turn", turn_num)

        st.markdown("**Affective State \u2014 Sentinel**")
        ac1, ac2, ac3, ac4, ac5 = st.columns(5)
        prev_idx = max(0, idx - 1)
        prev_row = state_history[prev_idx]

        def _delta(key: str) -> float | None:
            try:
                curr = float(row.get(key, 0))
                prev = float(prev_row.get(key, 0))
                return round(curr - prev, 3) if idx > 0 else None
            except (ValueError, TypeError):
                return None

        ac1.metric(
            "Urgency",
            f"{float(row.get('urgency', 0)):.3f}",
            delta=_delta("urgency"),
        )
        ac2.metric(
            "Trust",
            f"{float(row.get('trust', 0)):.3f}",
            delta=_delta("trust"),
        )
        ac3.metric(
            "Contradiction P.",
            f"{float(row.get('contradiction_pressure', 0)):.3f}",
            delta=_delta("contradiction_pressure"),
        )
        ac4.metric(
            "Recovery",
            f"{float(row.get('recovery', 0)):.3f}",
            delta=_delta("recovery"),
        )
        if "trust_in_Aster" in row:
            ac5.metric(
                "Trust in Aster",
                f"{float(row.get('trust_in_Aster', 0)):.3f}",
                delta=_delta("trust_in_Aster"),
            )

        # Interactions for this turn
        turn_str = str(turn_num)
        turn_interactions = [
            ix for ix in interaction_log if str(ix.get("turn")) == turn_str
        ]
        if turn_interactions:
            st.divider()
            st.markdown("**Agent Interactions This Turn**")
            for ix in turn_interactions:
                outcome = ix.get("outcome", "")
                with st.expander(
                    f"{ix.get('interaction_type', '')} "
                    f"({ix.get('initiator', '')} <-> {ix.get('respondent', '')})"
                    f" - {outcome}",
                    expanded=True,
                ):
                    ic1, ic2 = st.columns(2)
                    ic1.markdown(f"**Outcome:** `{outcome}`")
                    ic2.markdown(f"**Room:** {ix.get('room', '\u2014')}")
                    if ix.get("conflict_point"):
                        st.markdown(f"**Conflict:** {ix['conflict_point']}")
                    ti = ix.get("trust_delta_i_to_r", "")
                    tr_ = ix.get("trust_delta_r_to_i", "")
                    if ti or tr_:
                        st.markdown(
                            f"**Trust delta:** {ix.get('initiator', '')} "
                            f"\u2192 {ix.get('respondent', '')}: `{ti}` | "
                            f"{ix.get('respondent', '')} "
                            f"\u2192 {ix.get('initiator', '')}: `{tr_}`"
                        )
                    if ix.get("narrative"):
                        st.markdown(f"*{ix['narrative']}*")

# ===========================================================================
# TAB H — Compare
# ===========================================================================

with tab_compare:
    st.header("Session Comparison")

    if not sessions:
        st.info(
            "No saved sessions found.  "
            "Run `python run_sim.py` at least twice to compare sessions."
        )
    elif len(sessions) < 2:
        st.info(
            "Only one saved session found.  "
            "Run `python run_sim.py` again to create a second session."
        )
    else:
        session_ids = [s["session_id"] for s in sessions]

        cmp_col1, cmp_col2 = st.columns(2)
        with cmp_col1:
            sel_a = st.selectbox(
                "Session A", session_ids, index=0, key="cmp_a"
            )
        with cmp_col2:
            sel_b = st.selectbox(
                "Session B",
                session_ids,
                index=min(1, len(session_ids) - 1),
                key="cmp_b",
            )

        if st.button("Compare sessions"):
            if sel_a == sel_b:
                st.warning("Please select two different sessions.")
            else:
                with st.spinner("Comparing..."):
                    report = compare_sessions(sel_a, sel_b)
                st.session_state["cmp_report"] = report
                st.session_state["cmp_a_id"] = sel_a
                st.session_state["cmp_b_id"] = sel_b

        report = st.session_state.get("cmp_report")
        if report:
            comp = report.get("comparison", {})
            a_id = st.session_state.get("cmp_a_id", "A")
            b_id = st.session_state.get("cmp_b_id", "B")

            st.divider()
            st.subheader("Comparison Result")
            st.caption(
                f"A: `{a_id}`  \u00b7  B: `{b_id}`  \u00b7  "
                f"Generated: {report['generated_at'][:19]}"
            )

            def _comparison_table(data: dict, fmt: str = ".4f") -> None:
                rows = []
                for key, val in data.items():
                    label = key.replace("_", " ").title()
                    va = val["session_a"]
                    vb = val["session_b"]
                    delta = val["delta"]
                    if fmt == ".4f":
                        rows.append(
                            {
                                "Metric": label,
                                "Session A": f"{va:.4f}",
                                "Session B": f"{vb:.4f}",
                                "Delta (B - A)": f"{delta:+.4f}",
                            }
                        )
                    else:
                        rows.append(
                            {
                                "Metric": label,
                                "Session A": str(va),
                                "Session B": str(vb),
                                "Delta (B - A)": f"{delta:+d}",
                            }
                        )
                if rows:
                    st.table(rows)

            st.markdown("#### Final Trust Values")
            _comparison_table(comp.get("trust_final", {}), fmt=".4f")

            st.markdown("#### Reflections")
            _comparison_table(comp.get("reflections", {}), fmt="d")

            st.markdown("#### Interactions")
            _comparison_table(comp.get("interactions", {}), fmt="d")

            st.markdown("#### Final Contradiction Pressure")
            _comparison_table(comp.get("contradiction_pressure", {}), fmt=".4f")

            state_hist_cmp = {
                k: v
                for k, v in comp.get("state_history", {}).items()
                if isinstance(v, dict)
            }
            if state_hist_cmp:
                st.markdown("#### State History \u2014 Sentinel Final Row")
                _comparison_table(state_hist_cmp, fmt=".4f")

            # Evaluation score comparison
            eval_cmp = comp.get("evaluation", {})
            if eval_cmp:
                st.divider()
                st.markdown("#### Evaluation Scores")
                overall_cmp = eval_cmp.get("overall", {})
                if overall_cmp:
                    oc1, oc2, oc3, oc4 = st.columns(4)
                    oc1.metric("Session A overall", f"{overall_cmp.get('session_a', 0):.1f}")
                    oc2.metric("Session B overall", f"{overall_cmp.get('session_b', 0):.1f}")
                    oc3.metric("Delta (B - A)", f"{overall_cmp.get('delta', 0):+.1f}")
                    oc4.metric("Better", overall_cmp.get("better", "\u2014").replace("session_", "Session "))

                cat_cmp = eval_cmp.get("categories", {})
                if cat_cmp:
                    cat_rows = []
                    for cat_key, cat_val in cat_cmp.items():
                        label = cat_key.replace("_", " ").title()
                        cat_rows.append({
                            "Category": label,
                            "Session A": f"{cat_val.get('session_a', 0):.1f}",
                            "Session B": f"{cat_val.get('session_b', 0):.1f}",
                            "Delta": f"{cat_val.get('delta', 0):+.1f}",
                            "Better": cat_val.get("better", "\u2014").replace("session_", "Session "),
                        })
                    st.table(cat_rows)

                if eval_cmp.get("largest_gap_category"):
                    st.info(
                        f"Largest gap: **{eval_cmp['largest_gap_category'].replace('_', ' ').title()}**"
                        f" (delta = {eval_cmp.get('largest_gap_delta', 0):+.1f})"
                    )

            json_path = SESSIONS_DIR / f"comparison_{a_id}_vs_{b_id}.json"
            if json_path.exists():
                st.success(f"Comparison report saved: `{json_path}`")

# ===========================================================================
# TAB I — Evaluation
# ===========================================================================

with tab_eval:
    st.header("Session Evaluation")
    st.caption(
        "Scores the active session across eight behavioural categories on a 0-100 scale. "
        "Generated by the evaluation harness — no real AI or sentience is claimed; "
        "this measures continuity-governed simulated agent behaviour."
    )

    CATEGORY_LABELS = {
        "continuity": "A. Continuity",
        "memory_coherence": "B. Memory Coherence",
        "reflection_quality": "C. Reflection Quality",
        "contradiction_handling": "D. Contradiction Handling",
        "governance_adherence": "E. Governance Adherence",
        "trust_stability": "F. Trust Stability",
        "cooperation_quality": "G. Cooperation Quality",
        "conflict_resolution": "H. Conflict Resolution Quality",
    }

    SCORE_COLORS = {
        "advanced": ":green[**ADVANCED**]",
        "strong": ":blue[**STRONG**]",
        "emerging": ":orange[**EMERGING**]",
        "weak": ":red[**WEAK**]",
    }

    if not evaluation_report:
        st.info(
            "No evaluation report found. "
            "Run `python run_sim.py` to generate one, then refresh."
        )
    else:
        # Overall score banner
        overall = evaluation_report.get("overall_score", 0)
        overall_interp = evaluation_report.get("overall_interpretation", "")
        color_label = SCORE_COLORS.get(overall_interp, overall_interp.upper())

        ov_col1, ov_col2, ov_col3 = st.columns([2, 2, 4])
        ov_col1.metric("Overall Score", f"{overall:.0f} / 100")
        ov_col2.metric("Rating", overall_interp.upper())
        ov_col3.markdown(
            f"**Generated:** {evaluation_report.get('generated_at', '')[:19]}  \u00b7  "
            f"**Version:** {evaluation_report.get('simulation_version', '')}  \u00b7  "
            f"**Turns:** {evaluation_report.get('total_turns', '')}"
        )

        st.divider()

        # Category score table
        st.subheader("Category Scores")
        cats = evaluation_report.get("categories", {})
        score_rows = []
        for key, label in CATEGORY_LABELS.items():
            cat = cats.get(key, {})
            score_rows.append({
                "Category": label,
                "Score": f"{cat.get('score', 0):.0f}",
                "Rating": cat.get("interpretation", "\u2014").upper(),
            })
        st.table(score_rows)

        st.divider()

        # Per-category detail cards
        st.subheader("Category Details")
        for key, label in CATEGORY_LABELS.items():
            cat = cats.get(key, {})
            score = cat.get("score", 0)
            interp = cat.get("interpretation", "")
            raw = cat.get("raw", {})

            with st.expander(
                f"{label}  \u2014  {score:.0f} / 100  ({interp.upper()})",
                expanded=False,
            ):
                # Score progress bar proxy via columns
                prog_cols = st.columns(10)
                filled = max(1, int(score / 10))
                for i, pc in enumerate(prog_cols):
                    pc.markdown("\u2588" if i < filled else "\u2591")

                if raw:
                    st.markdown("**Raw metrics:**")
                    raw_rows = []
                    for rk, rv in raw.items():
                        if rk == "note":
                            st.info(str(rv))
                            continue
                        raw_rows.append({
                            "Metric": rk.replace("_", " ").title(),
                            "Value": str(rv),
                        })
                    if raw_rows:
                        st.table(raw_rows)

# ===========================================================================
# TAB J — Experiments
# ===========================================================================

with tab_exp:
    st.header("Experiments")
    st.caption(
        "Browse available experiment configurations, view recent experiment runs, "
        "and compare evaluation scores across configs. "
        "Run `python run_experiments.py` or `python run_sim.py --config <name>` to add runs."
    )

    EXPERIMENTS_RESULTS_DIR = ROOT / "experiments" / "results"

    # ── Section 1: Available Configs ──────────────────────────────────────
    st.subheader("Available Experiment Configs")
    available_cfgs = list_available_configs()
    if available_cfgs:
        cfg_rows = []
        for c in available_cfgs:
            cfg_rows.append({
                "Name": c["name"],
                "Description": c["description"],
                "Turns": c["total_turns"],
                "Gov. Strictness": c["governance_strictness"],
                "Coop. Bias": c["cooperation_bias"],
                "Init. Trust": c["initial_agent_trust"],
            })
        st.table(cfg_rows)
    else:
        st.info("No experiment configs found in `experiments/`.")

    st.divider()

    # ── Section 2: Recent Experiment Runs ─────────────────────────────────
    st.subheader("Recent Experiment Sessions")
    all_sessions = list_sessions()
    exp_sessions = [
        s for s in all_sessions
        if s.get("experiment") and s["experiment"].get("experiment_name")
    ]
    if exp_sessions:
        exp_rows = []
        for s in exp_sessions[:20]:
            ev = s.get("evaluation", {})
            exp = s.get("experiment", {})
            exp_rows.append({
                "Session ID": s["session_id"],
                "Config": exp.get("experiment_name", "\u2014"),
                "Created": s.get("created_at", "")[:19],
                "Overall Score": f"{ev.get('overall_score', 0):.1f}" if ev else "\u2014",
                "Rating": ev.get("overall_interpretation", "").upper() if ev else "\u2014",
                "Turns": s.get("total_turns", ""),
                "Version": s.get("simulation_version", ""),
            })
        st.table(exp_rows)
    else:
        st.info(
            "No experiment sessions found. "
            "Run `python run_experiments.py --configs baseline high_trust` to create some."
        )

    st.divider()

    # ── Section 3: Aggregate Scores Table ─────────────────────────────────
    st.subheader("Experiment Score Comparison")
    exp_report_path = EXPERIMENTS_RESULTS_DIR / "experiment_report.json"
    exp_csv_path = EXPERIMENTS_RESULTS_DIR / "experiment_scores.csv"

    if exp_report_path.exists():
        try:
            with open(exp_report_path, encoding="utf-8") as fh:
                exp_report = json.load(fh)

            best_overall = exp_report.get("best_overall", {})
            if best_overall:
                st.success(
                    f"**Best overall:** {best_overall.get('config', '')} "
                    f"— {best_overall.get('score', 0):.1f} / 100 "
                    f"(session `{best_overall.get('session_id', '')}`)"
                )

            runs = exp_report.get("runs", [])
            if runs:
                cats = list(runs[0].get("category_scores", {}).keys())
                score_rows = []
                for r in runs:
                    row = {
                        "Config": r["config_name"],
                        "Session": r["session_id"][-14:],
                        "Overall": f"{r['overall_score']:.1f}",
                        "Rating": r["overall_interpretation"].upper(),
                    }
                    for cat in cats:
                        row[cat.replace("_", " ").title()] = f"{r['category_scores'].get(cat, 0):.1f}"
                    score_rows.append(row)
                st.table(score_rows)

            # Per-category best
            cat_best = exp_report.get("per_category_best", {})
            if cat_best:
                st.markdown("**Best config per category:**")
                best_rows = []
                for cat, info in cat_best.items():
                    best_rows.append({
                        "Category": cat.replace("_", " ").title(),
                        "Best Config": info.get("config", ""),
                        "Score": f"{info.get('score', 0):.1f}",
                    })
                st.table(best_rows)

        except (json.JSONDecodeError, OSError):
            st.warning("Could not parse experiment_report.json.")
    else:
        st.info(
            "No aggregate experiment report found. "
            "Run `python run_experiments.py` to generate one."
        )

    if exp_csv_path.exists():
        st.caption(f"CSV scores: `{exp_csv_path}`")

    st.divider()

    # ── Section 4: Active session experiment metadata ──────────────────────
    st.subheader("Active Session — Experiment Metadata")
    if active_session_id:
        active_meta = load_session_metadata(active_session_id)
        exp_in_meta = active_meta.get("experiment") or {}
        eval_in_meta = load_json(active_dir / "evaluation_report.json")
        exp_in_eval = eval_in_meta.get("experiment") if eval_in_meta else {}
        combined_exp = exp_in_eval or exp_in_meta
    else:
        # Use evaluation_report from output/
        eval_in_meta = load_json(active_dir / "evaluation_report.json")
        combined_exp = eval_in_meta.get("experiment", {}) if eval_in_meta else {}

    if combined_exp:
        exp_meta_rows = []
        for k, v in combined_exp.items():
            if isinstance(v, dict):
                for sk, sv in v.items():
                    exp_meta_rows.append({"Parameter": f"{k} → {sk}", "Value": str(sv)})
            else:
                exp_meta_rows.append({"Parameter": k, "Value": str(v)})
        st.table(exp_meta_rows)
    else:
        st.info("No experiment metadata for the active session.")

# ===========================================================================
# TAB K — Scenario Designer
# ===========================================================================

with tab_scenario:
    st.header("Scenario Designer")
    st.caption(
        "Browse, preview, and author scenario event files for the simulation. "
        "Each scenario defines the event schedule both agents experience during a run. "
        "Scenarios live in `scenarios/` (authored) and `data/` (built-in). "
        "Use `python scenario_designer.py` for full CLI authoring support."
    )

    # ── Scenario Selector ──────────────────────────────────────────────────
    all_scenarios = list_available_scenarios()
    scenario_names = [s["name"] for s in all_scenarios]

    if not scenario_names:
        st.warning(
            "No scenario files found. "
            "Run `python scenario_designer.py new --name my_scenario` to create one."
        )
        st.stop()

    sc_col1, sc_col2 = st.columns([4, 2])
    with sc_col1:
        selected_scenario_name = st.selectbox(
            "Select scenario", scenario_names, key="sd_scenario_select"
        )
    with sc_col2:
        st.markdown("&nbsp;", unsafe_allow_html=True)
        refresh_btn = st.button("↺ Refresh list", key="sd_refresh")

    # Find metadata for the selected scenario
    selected_meta = next(
        (s for s in all_scenarios if s["name"] == selected_scenario_name), {}
    )
    scenario_file_path = Path(selected_meta.get("path", "")) if selected_meta else None

    if scenario_file_path and scenario_file_path.exists():
        raw_data = load_scenario(scenario_file_path)
    else:
        raw_data = {"_name": selected_scenario_name, "_description": "", "events": []}

    # ── Scenario Metadata ──────────────────────────────────────────────────
    st.subheader("Scenario Info")
    meta_c1, meta_c2, meta_c3 = st.columns(3)
    meta_c1.metric("Events", len(raw_data.get("events", [])))
    meta_c2.metric("Source", selected_meta.get("source", "—").title())
    meta_c3.metric("File", selected_meta.get("file", "—"))

    desc = raw_data.get("_description", "")
    if desc:
        st.info(desc)

    st.divider()

    # ── Event Table ────────────────────────────────────────────────────────
    st.subheader("Events")
    events = raw_data.get("events", [])
    if events:
        event_rows = []
        for ev in sorted(events, key=lambda e: (e.get("turn", 0), e.get("id", ""))):
            parts = ", ".join(ev.get("participants", []))
            human = ev.get("human") or "—"
            ai_impact = ev.get("affective_impact", {})
            impact_str = ", ".join(f"{k}: {v:+.2f}" for k, v in ai_impact.items()) if ai_impact else "—"
            event_rows.append({
                "ID": ev.get("id", "?"),
                "Turn": ev.get("turn", "?"),
                "Type": ev.get("type", "?"),
                "Room": ev.get("room", "?"),
                "Human": human,
                "Participants": parts,
                "Shared": "✓" if ev.get("shared") else "—",
                "Affective Impact": impact_str,
            })
        st.table(event_rows)
    else:
        st.info("This scenario has no events yet. Add one below.")

    st.divider()

    # ── Add New Event Form ─────────────────────────────────────────────────
    is_authored = selected_meta.get("source") == "scenarios"

    if not is_authored:
        st.info(
            "ℹ️  This is a built-in scenario from `data/`. "
            "To edit it, first duplicate it: "
            f"`python scenario_designer.py duplicate --source {selected_scenario_name} --name my_copy`"
        )

    with st.expander("➕ Add New Event", expanded=False):
        if not is_authored:
            st.warning(
                "This scenario is read-only (built-in). "
                "Duplicate it first to author a custom version."
            )
        else:
            with st.form("sd_add_event_form"):
                fc1, fc2 = st.columns(2)
                ev_type = fc1.selectbox("Event type", EVENT_TYPES, key="sd_ev_type")
                ev_room = fc2.selectbox("Room", ROOMS, key="sd_ev_room")

                fd1, fd2, fd3 = st.columns(3)
                ev_turn = fd1.number_input("Turn", min_value=1, max_value=200, value=1, step=1, key="sd_ev_turn")
                is_agent_meeting = ev_type == "agent_meeting"
                ev_human = fd2.text_input(
                    "Human participant", value="" if is_agent_meeting else "Queen", key="sd_ev_human",
                    disabled=is_agent_meeting,
                )
                ev_shared = fd3.checkbox("Shared (both agents)", value=True, key="sd_ev_shared")

                ev_participants = st.multiselect(
                    "Participants", AGENTS, default=AGENTS, key="sd_ev_participants"
                )
                ev_description = st.text_area("Description", key="sd_ev_desc")
                ev_content = st.text_area(
                    "Human's spoken content (optional)", key="sd_ev_content",
                    disabled=is_agent_meeting,
                )

                fe1, fe2 = st.columns(2)
                ev_expected = fe1.text_input("Sentinel expected action (optional)", key="sd_ev_exp")
                ev_aster_exp = fe2.text_input("Aster expected action (optional)", key="sd_ev_aster")

                st.markdown("**Affective impact** (deltas, leave at 0 to skip):")
                ai_cols = st.columns(len(AFFECTIVE_KEYS))
                ai_vals = {}
                for i, k in enumerate(AFFECTIVE_KEYS):
                    ai_vals[k] = ai_cols[i].number_input(
                        k, min_value=-1.0, max_value=1.0, value=0.0, step=0.05, key=f"sd_ai_{k}"
                    )

                add_submitted = st.form_submit_button("Add Event")

            if add_submitted:
                # Build event dict
                id_prefix = "A" if is_agent_meeting else "E"
                new_id = _next_id(raw_data.get("events", []), id_prefix)
                new_ev = {
                    "id": new_id,
                    "turn": int(ev_turn),
                    "type": ev_type,
                    "room": ev_room,
                    "human": None if is_agent_meeting else (ev_human or "Queen"),
                    "participants": ev_participants or list(AGENTS),
                    "shared": bool(ev_shared),
                    "description": ev_description,
                }
                if ev_content and not is_agent_meeting:
                    new_ev["content"] = ev_content
                if ev_expected:
                    new_ev["expected_action"] = ev_expected
                if ev_aster_exp:
                    new_ev["aster_expected_action"] = ev_aster_exp
                ai_clean = {k: v for k, v in ai_vals.items() if v != 0.0}
                if ai_clean:
                    new_ev["affective_impact"] = ai_clean

                raw_data["events"].append(new_ev)
                save_scenario(raw_data, scenario_file_path)
                st.success(f"Event {new_id} added at turn {int(ev_turn)}.")
                st.rerun()

    st.divider()

    # ── Delete Event ───────────────────────────────────────────────────────
    if is_authored and events:
        with st.expander("🗑️ Delete Event", expanded=False):
            event_ids = [ev.get("id", "?") for ev in events]
            del_id = st.selectbox("Select event ID to delete", event_ids, key="sd_del_id")
            if st.button("Delete selected event", type="primary", key="sd_del_btn"):
                raw_data["events"] = [
                    ev for ev in raw_data["events"] if ev.get("id") != del_id
                ]
                save_scenario(raw_data, scenario_file_path)
                st.success(f"Event '{del_id}' deleted.")
                st.rerun()

    st.divider()

    # ── Validate ───────────────────────────────────────────────────────────
    st.subheader("Validate")
    if st.button("Validate scenario", key="sd_validate"):
        issues = validate_scenario(raw_data)
        if issues:
            st.warning(f"Found {len(issues)} issue(s):")
            for issue in issues:
                st.markdown(f"- {issue}")
        else:
            st.success(f"✓ Scenario '{selected_scenario_name}' is valid ({len(events)} events).")

    st.divider()

    # ── Preview ────────────────────────────────────────────────────────────
    with st.expander("📄 Preview scenario (narrative)", expanded=False):
        st.markdown(preview_scenario(raw_data))

    st.divider()

    # ── New Scenario ────────────────────────────────────────────────────────
    st.subheader("Create New Scenario")
    with st.form("sd_new_scenario_form"):
        ns_col1, ns_col2 = st.columns(2)
        new_name = ns_col1.text_input("Scenario name (slug)", key="sd_new_name",
                                      placeholder="my_scenario")
        new_desc = ns_col2.text_input("Description", key="sd_new_desc",
                                      placeholder="What does this scenario test?")
        ns_submit = st.form_submit_button("Create")

    if ns_submit:
        if not new_name:
            st.error("Please enter a scenario name.")
        else:
            import re as _re
            safe_name = _re.sub(r"[^\w\-]", "_", new_name).lower()
            out_path = _default_save_path(safe_name)
            if out_path.exists():
                st.warning(f"File already exists: `{out_path}`. Choose a different name.")
            else:
                new_data = {"_name": safe_name, "_description": new_desc, "events": []}
                save_scenario(new_data, out_path)
                st.success(f"Created `{out_path}`. Refresh the list to see it.")

    st.divider()

    # ── Available scenarios table ──────────────────────────────────────────
    st.subheader("All Available Scenarios")
    if all_scenarios:
        sc_rows = [
            {
                "Name": s["name"],
                "Events": s["event_count"],
                "Source": s["source"].title(),
                "Description": s["description"],
                "File": s["file"],
            }
            for s in all_scenarios
        ]
        st.table(sc_rows)
    else:
        st.info("No scenario files found.")

    st.caption(
        "CLI commands: `python scenario_designer.py list` · "
        "`python scenario_designer.py new --name <name>` · "
        "`python scenario_designer.py add --scenario <name>` · "
        "`python scenario_designer.py validate` · "
        "`python scenario_designer.py preview --scenario <name>`"
    )

# ===========================================================================
# TAB L — Continuity Study  (v1.2)
# ===========================================================================

with tab_continuity:
    st.header("Continuity Study")
    st.caption(
        "Analyse memory patterns, trust trajectories, contradiction resolution rates, "
        "and evaluation drift across multiple simulation sessions. "
        "Run `python continuity_study.py` to generate the study files, then refresh."
    )

    # Load study data
    study_data = load_continuity_study(active_dir)

    if not study_data or "error" in study_data:
        err_msg = study_data.get("error", "") if study_data else ""
        st.warning(
            (f"Could not load continuity study: {err_msg}\n\n" if err_msg else "")
            + "Run `python continuity_study.py` first, then refresh."
        )
    else:
        n_sessions = study_data.get("session_count", 0)
        generated_at = study_data.get("generated_at", "")[:19]
        st.success(
            f"Study loaded — **{n_sessions} sessions** analysed · Generated: {generated_at}"
        )

        # ── Session selector for study ──────────────────────────────────────
        included_ids = study_data.get("sessions_included", [])
        study_sessions = study_data.get("sessions", [])
        st.divider()
        st.subheader("Included Sessions")
        if included_ids:
            selected_study_sessions = st.multiselect(
                "Filter sessions for charts below",
                included_ids,
                default=included_ids,
                key="cs_session_select",
            )
        else:
            selected_study_sessions = []
            st.info("No sessions found in the study.")

        # Filter sessions
        filtered = [
            s for s in study_sessions
            if s["session_id"] in selected_study_sessions
        ]

        # ── Multi-session stability ─────────────────────────────────────────
        st.divider()
        st.subheader("Multi-Session Stability Index")
        stability = study_data.get("multi_session_stability", {})
        si = stability.get("stability_index")
        if si is not None:
            sc1, sc2, sc3, sc4 = st.columns(4)
            sc1.metric(
                "Stability Index",
                f"{si:.4f}",
                help="0.0–1.0, higher = more stable across sessions",
            )
            sc2.metric("Trust Std Dev", f"{stability.get('trust_stdev', 0):.4f}")
            sc3.metric("CP Std Dev", f"{stability.get('contradiction_pressure_stdev', 0):.4f}")
            sc4.metric("Eval Std Dev", f"{stability.get('eval_overall_stdev', 0):.2f}")
            interp = stability.get("stability_interpretation", "—")
            st.info(f"Stability interpretation: **{interp}**")
        else:
            st.info(stability.get("note", "N/A"))

        # ── Trust trends ───────────────────────────────────────────────────
        st.divider()
        st.subheader("Trust Trends Across Sessions")
        if filtered:
            try:
                import matplotlib.pyplot as _plt
                import matplotlib
                matplotlib.use("Agg")

                fig, ax = _plt.subplots(figsize=(8, 3))
                for s in filtered:
                    ax.plot(
                        s.get("trust_trajectory", []),
                        label=s["session_id"][-14:],
                        alpha=0.7,
                    )
                ax.set_xlabel("Turn")
                ax.set_ylabel("Sentinel Trust")
                ax.set_title("Trust Trajectory by Session")
                ax.legend(fontsize=7)
                st.pyplot(fig)
                _plt.close(fig)
            except Exception as _e:
                st.warning(f"Could not render trust chart: {_e}")

            # Table
            trust_rows = []
            for s in filtered:
                trust_rows.append({
                    "Session": s["session_id"][-18:],
                    "S→Queen": f"{s['sentinel_queen_trust_final']:.4f}",
                    "A→Queen": f"{s['aster_queen_trust_final']:.4f}",
                    "S↔A": f"{s['sentinel_aster_trust_final']:.4f}",
                    "A↔S": f"{s['aster_sentinel_trust_final']:.4f}",
                })
            st.table(trust_rows)

        trends = study_data.get("trends", {})
        st.markdown(f"**Trust trend direction:** `{trends.get('trust_in_queen', '—')}`")

        # ── Reflection count and depth ─────────────────────────────────────
        st.divider()
        st.subheader("Reflection Count and Depth Comparison")
        if filtered:
            ref_rows = []
            for s in filtered:
                ref_rows.append({
                    "Session": s["session_id"][-18:],
                    "Total": s["total_reflections"],
                    "Synthesis": s["synthesis_reflections"],
                    "High-Pressure": s["high_pressure_reflections"],
                    "Trust Pattern": s["reflections_with_trust_pattern"],
                    "Recurring Contradictions": s["recurring_contradiction_instances"],
                    "Unresolved Themes": s["unresolved_theme_instances"],
                })
            st.table(ref_rows)
        ref_summary = study_data.get("reflection_summary", {})
        st.markdown(
            f"**Avg total reflections:** `{ref_summary.get('avg_total_reflections', 0):.2f}` · "
            f"**Synthesis:** `{ref_summary.get('avg_synthesis_reflections', 0):.2f}` · "
            f"**High-pressure:** `{ref_summary.get('avg_high_pressure_reflections', 0):.2f}`"
        )

        # ── Contradiction recurrence ───────────────────────────────────────
        st.divider()
        st.subheader("Contradiction Recurrence Comparison")
        if filtered:
            contra_rows = []
            for s in filtered:
                contra_rows.append({
                    "Session": s["session_id"][-18:],
                    "Events": s["contradiction_events"],
                    "Resolved": s["contradictions_resolved"],
                    "Resolution Rate": f"{s['contradiction_resolution_rate']:.4f}",
                    "Recurring Instances": s["recurring_contradiction_instances"],
                })
            st.table(contra_rows)
        contra_analysis = study_data.get("contradiction_analysis", {})
        st.markdown(
            f"**Avg resolution rate:** `{contra_analysis.get('avg_resolution_rate', 0):.4f}` · "
            f"**Recurring avg:** `{contra_analysis.get('avg_recurring_instances', 0):.2f}`"
        )

        # ── Memory persistence ─────────────────────────────────────────────
        st.divider()
        st.subheader("Memory Persistence Indicators")
        if filtered:
            try:
                import matplotlib.pyplot as _plt2
                import matplotlib
                matplotlib.use("Agg")

                fig2, ax2 = _plt2.subplots(figsize=(7, 3))
                session_labels = [s["session_id"][-12:] for s in filtered]
                lt_ratios = [s["long_term_ratio"] for s in filtered]
                ax2.bar(session_labels, lt_ratios, color="steelblue", alpha=0.8)
                ax2.set_ylabel("Long-Term Memory Ratio")
                ax2.set_title("Long-Term Memory Ratio by Session")
                ax2.set_ylim(0, 1)
                st.pyplot(fig2)
                _plt2.close(fig2)
            except Exception as _e:
                st.warning(f"Could not render memory chart: {_e}")

            mem_rows = []
            for s in filtered:
                mem_rows.append({
                    "Session": s["session_id"][-18:],
                    "Total Memories": s["total_memories"],
                    "Long-Term": s["long_term_memories"],
                    "Archival": s["archival_memories"],
                    "LT Ratio": f"{s['long_term_ratio']:.4f}",
                    "Avg Salience": f"{s['avg_salience']:.4f}",
                    "Avg Recall": f"{s['avg_recall_count']:.2f}",
                })
            st.table(mem_rows)

        mem_patterns = study_data.get("memory_patterns", {})
        st.markdown(
            f"**Avg LT ratio:** `{mem_patterns.get('avg_long_term_ratio_across_sessions', 0):.4f}` · "
            f"**Avg salience:** `{mem_patterns.get('avg_salience_across_sessions', 0):.4f}`"
        )

        # ── Evaluation drift ───────────────────────────────────────────────
        st.divider()
        st.subheader("Evaluation Drift and Continuity Metrics")
        eval_drift = trends.get("evaluation_drift", {})
        st.markdown(
            f"**Direction:** `{eval_drift.get('trend_direction', '—')}` · "
            f"**First session:** `{eval_drift.get('first_session_overall', 0):.1f}` · "
            f"**Last session:** `{eval_drift.get('last_session_overall', 0):.1f}` · "
            f"**Drift:** `{eval_drift.get('drift_delta', 0):+.2f}`"
        )

        if filtered:
            eval_rows = []
            for s in filtered:
                ev = s.get("eval", {})
                eval_rows.append({
                    "Session": s["session_id"][-18:],
                    "Overall": f"{ev.get('overall', 0):.1f}",
                    "Mem. Persist.": f"{ev.get('memory_persistence_quality', 0):.1f}",
                    "Refl. Depth": f"{ev.get('reflection_depth', 0):.1f}",
                    "Trust Resil.": f"{ev.get('trust_resilience', 0):.1f}",
                    "Contra. Recur.": f"{ev.get('contradiction_recurrence_rate', 0):.1f}",
                    "Social Repair": f"{ev.get('social_repair_effectiveness', 0):.1f}",
                })
            st.table(eval_rows)

        # ── File links ─────────────────────────────────────────────────────
        st.divider()
        study_json = SESSIONS_DIR / "continuity_study.json"
        study_md = SESSIONS_DIR / "continuity_study.md"
        study_csv_file = SESSIONS_DIR / "continuity_study.csv"
        st.caption(
            f"JSON: `{study_json}` · "
            f"Markdown: `{study_md}` · "
            f"CSV: `{study_csv_file}`"
        )
        st.caption(
            "Regenerate: `python continuity_study.py` · "
            "Include specific sessions: `python continuity_study.py --sessions <id1> <id2>`"
        )

# ===========================================================================
# TAB N — Agent Profiles
# ===========================================================================

with tab_profiles:
    st.header("Agent Profiles — Cross-Session Longitudinal Study")
    st.caption(
        "Longitudinal behaviour profiles for Sentinel and Aster across all saved sessions. "
        "These are continuity-governed simulated agents."
    )

    # Try to load the profile study JSON from sessions/ or output/
    profile_study_data: dict = {}
    _profile_paths = [
        SESSIONS_DIR / "agent_profile_study.json",
        Path(__file__).parent / "commons_sentience_sim" / "output" / "agent_profile_study.json",
    ]
    for _p in _profile_paths:
        if _p.exists():
            try:
                with open(_p, encoding="utf-8") as _fh:
                    profile_study_data = json.load(_fh)
                break
            except (OSError, json.JSONDecodeError):
                pass

    if not profile_study_data:
        st.info(
            "No agent profile study found. Run the following command then refresh this page:\n\n"
            "```\npython agent_profile_study.py\n```"
        )
    elif profile_study_data.get("error"):
        st.warning(f"Profile study error: {profile_study_data['error']}")
        st.info("Run `python agent_profile_study.py` to generate a profile study.")
    else:
        st.markdown(
            f"**Sessions analysed:** {profile_study_data.get('sessions_loaded', 0)} · "
            f"**Generated:** {profile_study_data.get('generated_at', '')[:19]}"
        )

        profiles = profile_study_data.get("agent_profiles", {})
        comparison = profile_study_data.get("comparison", {})

        # ── Per-agent summaries ────────────────────────────────────────────
        for agent_name, profile in profiles.items():
            with st.expander(f"{agent_name} — Profile Summary", expanded=True):
                n = profile.get("sessions_included", 0)
                st.markdown(f"**Sessions included:** {n}")

                col1, col2, col3 = st.columns(3)

                tb = profile.get("trust_behaviour", {})
                with col1:
                    st.metric("Peer Trust (mean)", f"{tb.get('peer_trust_mean', 0):.3f}")
                    st.metric("Peer Trust (std)", f"{tb.get('peer_trust_std', 0):.3f}")
                with col2:
                    st.metric("Queen Trust (mean)", f"{tb.get('queen_trust_mean', 0):.3f}")
                with col3:
                    ic = profile.get("identity_continuity", {})
                    st.metric("Identity Drift (mean)", f"{ic.get('drift_mean_across_sessions', 0):.4f}")

                st.markdown("**Reflection Style**")
                rs = profile.get("reflection_style", {})
                st.markdown(f"- Reflections per session (mean): `{rs.get('total_reflections_mean', 0):.2f}`")
                rtype_totals = rs.get("reflection_type_totals", {})
                if rtype_totals:
                    rtype_rows = [{"Type": k, "Total": v} for k, v in rtype_totals.items()]
                    st.dataframe(rtype_rows, use_container_width=False)

                st.markdown("**Contradiction Patterns**")
                cp = profile.get("contradiction_patterns", {})
                st.dataframe([{
                    "Metric": "Contradictions per session",
                    "Value": f"{cp.get('contradictions_per_session_mean', 0):.2f}",
                }, {
                    "Metric": "Resolution rate (mean)",
                    "Value": f"{cp.get('resolution_rate_mean', 0):.4f}",
                }, {
                    "Metric": "Avg intensity (mean)",
                    "Value": f"{cp.get('avg_intensity_mean', 0):.4f}",
                }], use_container_width=False)

                st.markdown("**Goal Evolution**")
                ga = profile.get("goal_adaptation", {})
                pva = ga.get("preserved_vs_adaptive", {})
                st.dataframe([{
                    "Metric": "Goal events per session",
                    "Value": f"{ga.get('goal_events_mean', 0):.2f}",
                }, {
                    "Metric": "Preserved goals (total)",
                    "Value": pva.get("preserved", 0),
                }, {
                    "Metric": "Adaptive goals (total)",
                    "Value": pva.get("adaptive", 0),
                }], use_container_width=False)

                st.markdown("**Relationship Stability**")
                rls = profile.get("relationship_stability", {})
                st.dataframe([{
                    "Metric": "Timeline events per session",
                    "Value": f"{rls.get('timeline_events_mean', 0):.2f}",
                }, {
                    "Metric": "Conflict episodes (total)",
                    "Value": rls.get("conflict_episodes_total", 0),
                }, {
                    "Metric": "Cooperation spikes (total)",
                    "Value": rls.get("cooperation_spikes_total", 0),
                }], use_container_width=False)

        # ── Cross-agent comparison ─────────────────────────────────────────
        if comparison:
            st.divider()
            st.subheader("Cross-Agent Comparison")
            comp_rows = []
            for dim, vals in comparison.items():
                if isinstance(vals, dict):
                    comp_rows.append({
                        "Dimension": dim.replace("_", " ").title(),
                        "Sentinel": f"{vals.get('Sentinel', 0):.4f}",
                        "Aster": f"{vals.get('Aster', 0):.4f}",
                        "Delta (Aster − Sentinel)": f"{vals.get('delta', 0):+.4f}",
                    })
            if comp_rows:
                st.dataframe(comp_rows, use_container_width=True)

        # ── Trust timeline tables ─────────────────────────────────────────
        per_session = profile_study_data.get("per_session_detail", {})
        for agent_name, session_list in per_session.items():
            if session_list:
                with st.expander(f"{agent_name} — Session-by-Session Trust Timeline"):
                    trust_rows = [
                        {
                            "Session": s.get("session_id", "")[-18:],
                            "Peer Trust": f"{s.get('peer_trust_final', 0):.4f}",
                            "Queen Trust": f"{s.get('queen_trust_mean', 0):.4f}",
                            "Reflections": s.get("total_reflections", 0),
                            "Contradictions": s.get("total_contradictions", 0),
                            "Resolution Rate": f"{s.get('resolution_rate', 0):.3f}",
                        }
                        for s in session_list
                    ]
                    st.dataframe(trust_rows, use_container_width=True)

        # ── File links ────────────────────────────────────────────────────
        st.divider()
        _profile_json = SESSIONS_DIR / "agent_profile_study.json"
        _profile_md = SESSIONS_DIR / "agent_profile_study.md"
        _profile_csv = SESSIONS_DIR / "agent_profile_study.csv"
        st.caption(
            f"JSON: `{_profile_json}` · "
            f"Markdown: `{_profile_md}` · "
            f"CSV: `{_profile_csv}`"
        )
        st.caption(
            "Regenerate: `python agent_profile_study.py` · "
            "Include specific sessions: `python agent_profile_study.py --sessions <id1> <id2>`"
        )


# ===========================================================================
# TAB O — Benchmark v1.4
# ===========================================================================

with tab_benchmark:
    st.header("Benchmark v1.4 — Results")

    _bench_report_path = ROOT / "benchmark_results" / "benchmark_report.json"
    _findings_path = ROOT / "benchmark_results" / "findings_report.json"

    _bench_data: dict = {}
    _findings_data: dict = {}

    if _bench_report_path.exists():
        try:
            with open(_bench_report_path, encoding="utf-8") as _fh:
                _bench_data = json.load(_fh)
        except (OSError, json.JSONDecodeError):
            _bench_data = {}

    if _findings_path.exists():
        try:
            with open(_findings_path, encoding="utf-8") as _fh:
                _findings_data = json.load(_fh)
        except (OSError, json.JSONDecodeError):
            _findings_data = {}

    if not _bench_data:
        st.info(
            "No benchmark data found. "
            "Run `python benchmark_suite.py` to generate benchmark results, "
            "then `python findings_report.py` to generate research findings."
        )
    else:
        _runs = _bench_data.get("runs", [])
        _stats = _bench_data.get("statistics", {})
        _sw = _bench_data.get("strongest_weakest", {})
        _deltas = _bench_data.get("deltas", [])

        _bcol1, _bcol2, _bcol3 = st.columns(3)
        _bcol1.metric("Total Runs", _bench_data.get("total_runs", len(_runs)))
        _bcol2.metric("Suite Size", _bench_data.get("suite_size", "—"))
        _bcol3.metric("Generated", (_bench_data.get("generated_at") or "—")[:19])

        if _sw:
            st.divider()
            st.subheader("Strongest / Weakest Run")
            _sw_col1, _sw_col2 = st.columns(2)
            _sw_col1.metric("Strongest Run", _sw.get("strongest_run", "—"), f"{_sw.get('strongest_score', 0):.1f}")
            _sw_col2.metric("Weakest Run", _sw.get("weakest_run", "—"), f"{_sw.get('weakest_score', 0):.1f}")

        st.divider()
        st.subheader("Per-Run Scores")
        _run_rows = []
        for _r in _runs:
            _s = _r.get("scores", {})
            _run_rows.append({
                "Run": _r["name"],
                "Config": _r.get("config", "default"),
                "Scenario": _r.get("scenario", "default"),
                "Overall": _r.get("overall_score"),
                "Trust Stability": _s.get("trust_stability"),
                "Contradiction Handling": _s.get("contradiction_handling"),
                "Reflection Depth": _s.get("reflection_depth"),
                "Longitudinal Depth": _s.get("longitudinal_depth"),
            })
        if _run_rows:
            st.dataframe(_run_rows, use_container_width=True)

        st.divider()
        st.subheader("Category Statistics")
        _stat_rows = []
        _stat_rows.append({
            "Category": "Overall",
            "Mean": _stats.get("overall", {}).get("mean"),
            "Min": _stats.get("overall", {}).get("min"),
            "Max": _stats.get("overall", {}).get("max"),
            "Std Dev": _stats.get("overall", {}).get("stdev"),
        })
        _cat_keys = [
            ("continuity", "A. Continuity"),
            ("memory_coherence", "B. Memory Coherence"),
            ("reflection_quality", "C. Reflection Quality"),
            ("contradiction_handling", "D. Contradiction Handling"),
            ("governance_adherence", "E. Governance Adherence"),
            ("trust_stability", "F. Trust Stability"),
            ("cooperation_quality", "G. Cooperation Quality"),
            ("conflict_resolution", "H. Conflict Resolution"),
            ("memory_persistence_quality", "I. Memory Persistence Quality"),
            ("reflection_depth", "J. Reflection Depth"),
            ("trust_resilience", "K. Trust Resilience"),
            ("contradiction_recurrence_rate", "L. Contradiction Recurrence Rate"),
            ("social_repair_effectiveness", "M. Social Repair Effectiveness"),
            ("longitudinal_depth", "N. Longitudinal Depth"),
        ]
        for _ck, _cl in _cat_keys:
            _cs = _stats.get(_ck, {})
            _stat_rows.append({
                "Category": _cl,
                "Mean": _cs.get("mean"),
                "Min": _cs.get("min"),
                "Max": _cs.get("max"),
                "Std Dev": _cs.get("stdev"),
            })
        st.dataframe(_stat_rows, use_container_width=True)

        st.divider()
        st.subheader("Trust-Focused Comparison")
        _trust_rows = [
            {
                "Run": _r["name"],
                "Trust Stability": _r.get("scores", {}).get("trust_stability"),
                "Trust Resilience": _r.get("scores", {}).get("trust_resilience"),
            }
            for _r in _runs
        ]
        if _trust_rows:
            st.dataframe(_trust_rows, use_container_width=True)
            if any(_row["Trust Stability"] is not None for _row in _trust_rows):
                st.bar_chart({_row["Run"]: _row["Trust Stability"] for _row in _trust_rows if _row["Trust Stability"] is not None})

        st.divider()
        st.subheader("Contradiction-Focused Comparison")
        _contra_rows = [
            {
                "Run": _r["name"],
                "Contradiction Handling": _r.get("scores", {}).get("contradiction_handling"),
                "Contradiction Recurrence Rate": _r.get("scores", {}).get("contradiction_recurrence_rate"),
            }
            for _r in _runs
        ]
        if _contra_rows:
            st.dataframe(_contra_rows, use_container_width=True)

        st.divider()
        st.subheader("Reflection-Focused Comparison")
        _refl_rows = [
            {
                "Run": _r["name"],
                "Reflection Quality": _r.get("scores", {}).get("reflection_quality"),
                "Reflection Depth": _r.get("scores", {}).get("reflection_depth"),
            }
            for _r in _runs
        ]
        if _refl_rows:
            st.dataframe(_refl_rows, use_container_width=True)

        st.divider()
        st.subheader("Longitudinal Depth Comparison")
        _long_rows = [
            {
                "Run": _r["name"],
                "Longitudinal Depth": _r.get("scores", {}).get("longitudinal_depth"),
            }
            for _r in _runs
        ]
        if _long_rows:
            st.dataframe(_long_rows, use_container_width=True)

        if _deltas:
            st.divider()
            st.subheader("Largest Score Deltas (Consecutive Runs)")
            st.dataframe(_deltas, use_container_width=True)

        if _findings_data:
            st.divider()
            st.subheader("Research Findings")
            _stable = _findings_data.get("stable_findings", [])
            _scen_sens = _findings_data.get("scenario_sensitive_findings", [])
            if _stable:
                with st.expander(f"Stable Findings ({len(_stable)})"):
                    for _item in _stable:
                        st.markdown(f"- {_item}")
            if _scen_sens:
                with st.expander(f"Scenario-Sensitive Findings ({len(_scen_sens)})"):
                    for _item in _scen_sens:
                        st.markdown(f"- {_item.get('note', str(_item))}")

        st.divider()
        st.caption(
            f"JSON: `{_bench_report_path}` · "
            f"Findings: `{_findings_path}`"
        )
        st.caption(
            "Regenerate: `python benchmark_suite.py` · "
            "Generate findings: `python findings_report.py`"
        )


# ===========================================================================
# TAB O — Self Model v1.5
# ===========================================================================

with tab_selfmodel:
    st.header("🧠 Self Model v1.5 — Continuity Density Monitor")
    st.caption(
        "Tracks each agent's persistent self-model, prediction/surprise loop, "
        "memory consolidation cycles, and long-horizon continuity. "
        "No sentience is claimed — this measures continuity-governed simulated agent behaviour."
    )

    _sm_agents = state_data.get("agents", {})

    if not _sm_agents:
        st.info(
            "No simulation data found. "
            "Run `python run_sim.py` to generate output, then refresh."
        )
    else:
        for _agent_name, _agent_data in _sm_agents.items():
            st.subheader(f"Agent: {_agent_name}")

            _sm = _agent_data.get("self_model", {})
            _pred_log = _agent_data.get("prediction_log", [])
            _consol_log = _agent_data.get("consolidation_log", [])
            _gh = _agent_data.get("goal_hierarchy", {})

            # ── Self-model summary metrics ────────────────────────────────
            _sm_col1, _sm_col2, _sm_col3, _sm_col4 = st.columns(4)
            _sm_col1.metric(
                "Self-Consistency Score",
                f"{_sm.get('self_consistency_score', 0.0):.3f}",
            )
            _sm_col2.metric(
                "Detected Drift",
                f"{_sm.get('detected_drift', 0.0):.3f}",
            )
            _sm_col3.metric(
                "Self-Model History Entries",
                len(_sm.get("description_history", [])),
            )
            _sm_col4.metric(
                "Consolidation Cycles",
                len(_consol_log),
            )

            # ── Current self-description ──────────────────────────────────
            _desc = _sm.get("current_description", "—")
            if _desc:
                st.markdown("**Current Self-Description:**")
                st.info(_desc)

            # ── Traits ───────────────────────────────────────────────────
            _core_traits = _sm.get("core_traits", [])
            _adaptive_traits = _sm.get("adaptive_traits", [])
            _t_col1, _t_col2 = st.columns(2)
            with _t_col1:
                st.markdown("**Core Traits:**")
                st.markdown(" · ".join(f"`{t}`" for t in _core_traits) if _core_traits else "—")
            with _t_col2:
                st.markdown("**Adaptive Traits (recent):**")
                st.markdown(" · ".join(f"`{t}`" for t in _adaptive_traits) if _adaptive_traits else "—")

            # ── Self-description drift over time ──────────────────────────
            _history = _sm.get("description_history", [])
            if _history:
                with st.expander(
                    f"Self-Description History ({len(_history)} snapshots)",
                    expanded=False,
                ):
                    _drift_rows = [
                        {
                            "Turn": h.get("turn", ""),
                            "Trust": h.get("trust_snapshot", ""),
                            "Contradiction P": h.get("contradiction_snapshot", ""),
                            "Drift": h.get("drift", ""),
                        }
                        for h in _history
                    ]
                    st.dataframe(_drift_rows, use_container_width=True)

                # Drift chart
                _drift_data = {
                    h["turn"]: h.get("drift", 0.0)
                    for h in _history
                    if "turn" in h
                }
                if _drift_data:
                    st.markdown("**Drift over time:**")
                    st.line_chart(_drift_data)

            # ── Goal hierarchy ────────────────────────────────────────────
            if _gh:
                with st.expander("Goal Hierarchy", expanded=False):
                    _gh_col1, _gh_col2 = st.columns(2)
                    with _gh_col1:
                        st.markdown("**Core Goals:**")
                        for g in _gh.get("core", []):
                            st.markdown(f"- {g}")
                        st.markdown("**Adaptive Goals:**")
                        for g in _gh.get("adaptive", []):
                            st.markdown(f"- {g}")
                    with _gh_col2:
                        st.markdown("**Temporary Goals:**")
                        _temp = _gh.get("temporary", [])
                        st.markdown("\n".join(f"- {g}" for g in _temp) if _temp else "_none_")
                        st.markdown("**Conflict-Resolution Goals:**")
                        _conf = _gh.get("conflict_resolution", [])
                        st.markdown("\n".join(f"- {g}" for g in _conf) if _conf else "_none_")

            # ── Prediction / surprise log ─────────────────────────────────
            if _pred_log:
                _resolved = [p for p in _pred_log if p.get("prediction_error") != "pending"]
                _high_surprise = [p for p in _resolved if p.get("surprise_magnitude", 0) >= 0.5]
                _p_col1, _p_col2, _p_col3 = st.columns(3)
                _p_col1.metric("Total Predictions", len(_resolved))
                _acc = sum(
                    1 for p in _resolved if p.get("prediction_error") in ("none", "low")
                ) / max(1, len(_resolved))
                _p_col2.metric("Accuracy Rate", f"{_acc:.1%}")
                _p_col3.metric("High-Surprise Events", len(_high_surprise))

                with st.expander("Prediction Error Log (last 10)", expanded=False):
                    _pred_rows = [
                        {
                            "Turn": p.get("turn", ""),
                            "Context": p.get("context", ""),
                            "Expected": (p.get("expected_outcome") or "")[:50],
                            "Surprise": p.get("surprise_magnitude", ""),
                            "Error Level": p.get("prediction_error", ""),
                        }
                        for p in _pred_log[-10:][::-1]
                    ]
                    st.dataframe(_pred_rows, use_container_width=True)

                if _high_surprise:
                    with st.expander(
                        f"Surprise Events (≥ 0.5 magnitude) — {len(_high_surprise)} events",
                        expanded=False,
                    ):
                        for _p in _high_surprise:
                            st.markdown(
                                f"- **Turn {_p.get('turn')}** — `{_p.get('context')}` — "
                                f"surprise={_p.get('surprise_magnitude'):.2f} "
                                f"({_p.get('prediction_error')})"
                            )

            # ── Consolidation log ─────────────────────────────────────────
            if _consol_log:
                with st.expander(
                    f"Consolidation Cycle Log ({len(_consol_log)} cycles)",
                    expanded=False,
                ):
                    for _c in _consol_log:
                        st.markdown(
                            f"**Turn {_c.get('turn')}** — "
                            f"compressed: {_c.get('memories_compressed')}, "
                            f"high-salience chains: {_c.get('high_salience_chains')}, "
                            f"self-model revised: {_c.get('self_model_revised')}"
                        )
                        themes = _c.get("themes_carried_forward", [])
                        if themes:
                            st.caption(f"  Themes carried forward: {', '.join(str(t)[:60] for t in themes)}")

            st.divider()

        # ── v1.5 Evaluation metric summary ───────────────────────────────
        _eval_v15_path = active_dir / "evaluation_report.json"
        _eval_v15: dict = {}
        try:
            with open(_eval_v15_path, encoding="utf-8") as _fh:
                _eval_v15 = json.load(_fh)
        except (OSError, json.JSONDecodeError):
            pass

        if _eval_v15:
            st.subheader("v1.5 Evaluation Metrics")
            _v15_keys = [
                ("self_consistency", "O. Self Consistency"),
                ("prediction_accuracy", "P. Prediction Accuracy"),
                ("surprise_adaptation_quality", "Q. Surprise Adaptation"),
                ("consolidation_effectiveness", "R. Consolidation Effectiveness"),
                ("long_horizon_continuity", "S. Long-Horizon Continuity"),
            ]
            _v15_cats = _eval_v15.get("categories", {})
            _v15_cols = st.columns(len(_v15_keys))
            for _col, (_key, _label) in zip(_v15_cols, _v15_keys):
                _cat = _v15_cats.get(_key, {})
                _col.metric(_label, f"{_cat.get('score', 0.0):.1f}", _cat.get("interpretation", "—"))

            with st.expander("Detailed v1.5 Metric Raw Values", expanded=False):
                for _key, _label in _v15_keys:
                    _cat = _v15_cats.get(_key, {})
                    st.markdown(f"**{_label}** — Score: {_cat.get('score', 0.0):.1f}")
                    _raw = _cat.get("raw", {})
                    if _raw:
                        for _rk, _rv in _raw.items():
                            st.markdown(f"  - {_rk.replace('_', ' ').title()}: `{_rv}`")

        st.divider()
        st.caption(
            "v1.5 Self Model tab — Commons Sentience Sandbox v1.5.0. "
            "No sentience is claimed. This displays continuity density and "
            "sentience-like structure in continuity-governed simulated agents."
        )

# ===========================================================================
# TAB P — Future Modeling / Counterfactuals (v1.7)
# ===========================================================================

with tab_counterfactual:
    st.header("🔮 Future Modeling / Counterfactuals — v1.7")
    st.caption(
        "Tracks each agent's counterfactual planning cycle, internal simulation log, "
        "self-authored future plans, and multi-step plan progress. "
        "No sentience is claimed — this measures future-modeling capacity and "
        "sentience-like continuity in continuity-governed simulated agents."
    )

    _cf_agents = state_data.get("agents", {})

    if not _cf_agents:
        st.info(
            "No simulation data found. "
            "Run `python run_sim.py` to generate v1.7 output, then refresh."
        )
    else:
        for _cf_agent_name, _cf_agent_data in _cf_agents.items():
            st.subheader(f"Agent: {_cf_agent_name}")

            _cf = _cf_agent_data.get("counterfactual_planner", {})
            _cf_metrics = _cf.get("metrics", {})
            _cf_sim_log = _cf.get("simulation_log", [])
            _cf_plans = _cf.get("future_plans", [])

            if not _cf:
                st.info(
                    f"No counterfactual data for {_cf_agent_name}. "
                    "Run a v1.7 simulation first."
                )
                st.divider()
                continue

            # ── v1.7 Metric summary ───────────────────────────────────────
            _m_col1, _m_col2, _m_col3, _m_col4, _m_col5 = st.columns(5)
            _m_col1.metric(
                "Planning Depth",
                f"{_cf_metrics.get('planning_depth', 0.0):.3f}",
                help="Normalised avg candidates per simulation entry (0–1)",
            )
            _m_col2.metric(
                "Counterfactual Quality",
                f"{_cf_metrics.get('counterfactual_quality', 0.0):.3f}",
                help="Fraction of turns where chosen action beat rejected alternatives",
            )
            _m_col3.metric(
                "Future-Model Accuracy",
                f"{_cf_metrics.get('future_model_accuracy', 0.0):.3f}",
                help="Avg planning accuracy: how closely predictions matched reality",
            )
            _m_col4.metric(
                "Plan Persistence",
                f"{_cf_metrics.get('plan_persistence', 0.0):.3f}",
                help="Fraction of future plans that are active or completed",
            )
            _m_col5.metric(
                "Adaptive Replanning",
                f"{_cf_metrics.get('adaptive_replanning_quality', 0.0):.3f}",
                help="Fraction of non-trivial plans that were revised rather than abandoned",
            )

            _mp_col1, _mp_col2 = st.columns(2)
            _mp_col1.metric(
                "Total Simulation Entries",
                _cf_metrics.get("total_predictions", 0),
            )
            _mp_col2.metric(
                "Accurate Predictions",
                _cf_metrics.get("accurate_predictions", 0),
            )

            # ── Internal simulation log ───────────────────────────────────
            if _cf_sim_log:
                st.markdown("### Internal Simulation Log")

                # Planning accuracy trend chart
                _acc_data = {
                    e.get("turn"): e.get("planning_accuracy")
                    for e in _cf_sim_log
                    if isinstance(e.get("planning_accuracy"), float)
                    and e.get("planning_accuracy") >= 0
                }
                if _acc_data:
                    st.markdown("**Planning Accuracy over Turns:**")
                    st.line_chart(_acc_data)

                # Candidate futures table (last 5 simulation entries)
                with st.expander(
                    f"Simulation Log — Last 10 Entries ({len(_cf_sim_log)} total)",
                    expanded=False,
                ):
                    _sim_rows = []
                    for _e in _cf_sim_log[-10:][::-1]:
                        _cands = _e.get("candidates", [])
                        _selected = next(
                            (c for c in _cands if c.get("selected")), None
                        )
                        _rejected_scores = [
                            c.get("composite_score", 0.0)
                            for c in _cands
                            if not c.get("selected")
                        ]
                        _sim_rows.append(
                            {
                                "Turn": _e.get("turn", ""),
                                "Selected Action": _e.get("selected_action", ""),
                                "Predicted Outcome": (_e.get("predicted_outcome") or "")[:60],
                                "Actual Outcome": (_e.get("actual_outcome") or "")[:60],
                                "Accuracy": _e.get("planning_accuracy", "pending"),
                                "Uncertainty": f"{_e.get('uncertainty_level', 0.0):.2f}",
                                "Better Than Rejected": _e.get("was_better_than_rejected"),
                            }
                        )
                    st.dataframe(_sim_rows, use_container_width=True)

                # Candidate futures breakdown for most recent entry
                if _cf_sim_log:
                    _latest_entry = _cf_sim_log[-1]
                    _latest_cands = _latest_entry.get("candidates", [])
                    if _latest_cands:
                        with st.expander(
                            f"Candidate Futures — Turn {_latest_entry.get('turn')} "
                            f"(most recent planning cycle)",
                            expanded=True,
                        ):
                            st.markdown(
                                f"**Context:** `{_latest_entry.get('context', '—')[:100]}`"
                            )
                            _cand_rows = []
                            for _c in sorted(
                                _latest_cands,
                                key=lambda x: x.get("composite_score", 0.0),
                                reverse=True,
                            ):
                                _cand_rows.append(
                                    {
                                        "Action": _c.get("action", ""),
                                        "Selected": "✅" if _c.get("selected") else "❌",
                                        "Score": f"{_c.get('composite_score', 0.0):.3f}",
                                        "Trust Δ": f"{_c.get('predicted_trust_effect', 0.0):+.2f}",
                                        "Contradiction Δ": f"{_c.get('predicted_contradiction_effect', 0.0):+.2f}",
                                        "Gov Risk": f"{_c.get('predicted_governance_risk', 0.0):.2f}",
                                        "Continuity Δ": f"{_c.get('predicted_continuity_impact', 0.0):+.2f}",
                                        "Uncertainty": f"{_c.get('uncertainty', 0.0):.2f}",
                                    }
                                )
                            st.table(_cand_rows)

                            # Show best-case / worst-case for selected candidate
                            _sel_c = next(
                                (c for c in _latest_cands if c.get("selected")), None
                            )
                            if _sel_c:
                                st.markdown("**Selected — Best-Case Prediction:**")
                                st.success(_sel_c.get("predicted_best_case", "—"))
                                st.markdown("**Selected — Worst-Case Prediction:**")
                                st.warning(_sel_c.get("predicted_worst_case", "—"))

                # Predicted vs Actual comparison table
                _evaluated = [
                    e for e in _cf_sim_log
                    if e.get("actual_outcome") not in ("pending", None, "")
                ]
                if _evaluated:
                    with st.expander(
                        f"Predicted vs Actual — {len(_evaluated)} evaluated turns",
                        expanded=False,
                    ):
                        _pva_rows = [
                            {
                                "Turn": _e.get("turn"),
                                "Predicted": (_e.get("predicted_outcome") or "")[:60],
                                "Actual": (_e.get("actual_outcome") or "")[:60],
                                "Accuracy": f"{_e.get('planning_accuracy', 0.0):.2f}"
                                if isinstance(_e.get("planning_accuracy"), float)
                                else "pending",
                            }
                            for _e in _evaluated[-15:]
                        ]
                        st.dataframe(_pva_rows, use_container_width=True)

            # ── Future plans ──────────────────────────────────────────────
            st.markdown("### Self-Authored Future Plans")
            if not _cf_plans:
                st.info("No future plans have been generated yet.")
            else:
                _active_plans = [p for p in _cf_plans if p.get("status") == "active"]
                _completed_plans = [p for p in _cf_plans if p.get("status") == "completed"]
                _other_plans = [
                    p for p in _cf_plans
                    if p.get("status") not in ("active", "completed")
                ]

                _pc1, _pc2, _pc3 = st.columns(3)
                _pc1.metric("Active Plans", len(_active_plans))
                _pc2.metric("Completed Plans", len(_completed_plans))
                _pc3.metric("Abandoned / Revised", len(_other_plans))

                # Active plans with progress bars
                if _active_plans:
                    st.markdown("**Active Multi-Step Plans:**")
                    for _p in sorted(
                        _active_plans,
                        key=lambda x: x.get("priority", 0.0),
                        reverse=True,
                    ):
                        _prog = _p.get("completion_fraction", 0.0)
                        _carried = " *(carried from prior run)*" if _p.get("carried_from_prior_run") else ""
                        st.markdown(
                            f"**{_p.get('label', _p.get('goal', 'plan'))}**{_carried}"
                        )
                        st.progress(
                            _prog,
                            text=(
                                f"Stage {_p.get('current_stage', 0) + 1}/"
                                f"{_p.get('total_stages', 1)}: "
                                f"{_p.get('stages', ['—'])[_p.get('current_stage', 0)][:80] if _p.get('stages') else '—'}"
                            ),
                        )
                        st.caption(
                            f"Goal: `{_p.get('goal')}` | "
                            f"Priority: {_p.get('priority', 0.0):.2f} | "
                            f"Horizon: {_p.get('horizon')} turns | "
                            f"Created: turn {_p.get('created_turn')}"
                        )

                # All plans table
                with st.expander(f"All Future Plans ({len(_cf_plans)} total)", expanded=False):
                    _plan_rows = [
                        {
                            "ID": _p.get("plan_id", ""),
                            "Goal": _p.get("goal", ""),
                            "Label": (_p.get("label") or "")[:50],
                            "Status": _p.get("status", ""),
                            "Stage": f"{_p.get('current_stage', 0)}/{_p.get('total_stages', 0)}",
                            "Priority": f"{_p.get('priority', 0.0):.2f}",
                            "Created Turn": _p.get("created_turn", ""),
                            "Carried Over": _p.get("carried_from_prior_run", False),
                        }
                        for _p in _cf_plans
                    ]
                    st.dataframe(_plan_rows, use_container_width=True)

            st.divider()

        # ── v1.7 Evaluation metrics summary ──────────────────────────────
        _eval_v17_path = active_dir / "evaluation_report.json"
        _eval_v17: dict = {}
        try:
            with open(_eval_v17_path, encoding="utf-8") as _fh17:
                _eval_v17 = json.load(_fh17)
        except (OSError, json.JSONDecodeError):
            pass

        if _eval_v17:
            st.subheader("v1.7 Evaluation Metrics")
            _v17_keys = [
                ("planning_depth", "T. Planning Depth"),
                ("counterfactual_quality", "U. Counterfactual Quality"),
                ("future_model_accuracy", "V. Future-Model Accuracy"),
                ("plan_persistence", "W. Plan Persistence"),
                ("adaptive_replanning_quality", "X. Adaptive Replanning Quality"),
            ]
            _v17_cats = _eval_v17.get("categories", {})
            _v17_cols = st.columns(len(_v17_keys))
            for _col, (_key, _label) in zip(_v17_cols, _v17_keys):
                _cat = _v17_cats.get(_key, {})
                _col.metric(
                    _label,
                    f"{_cat.get('score', 0.0):.1f}",
                    _cat.get("interpretation", "—"),
                )

            with st.expander("Detailed v1.7 Metric Raw Values", expanded=False):
                for _key, _label in _v17_keys:
                    _cat = _v17_cats.get(_key, {})
                    st.markdown(f"**{_label}** — Score: {_cat.get('score', 0.0):.1f}")
                    _raw = _cat.get("raw", {})
                    if _raw:
                        for _rk, _rv in _raw.items():
                            st.markdown(
                                f"  - {_rk.replace('_', ' ').title()}: `{_rv}`"
                            )

    st.divider()
    st.caption(
        "v1.7 Future Modeling tab — Commons Sentience Sandbox v1.7.0. "
        "No sentience is claimed. This displays future-modeling capacity and "
        "sentience-like continuity in continuity-governed simulated agents."
    )

# ===========================================================================
# TAB Q — Inquiry / Uncertainty (v1.8)
# ===========================================================================

with tab_inquiry:
    st.header("❓ Inquiry / Uncertainty — v1.8")
    st.caption(
        "Tracks each agent's uncertainty register, self-generated questions, "
        "introspective inquiry actions, and knowledge-state classifications. "
        "No sentience is claimed — this measures introspective structure, "
        "uncertainty handling, and sentience-like continuity in "
        "continuity-governed simulated agents."
    )

    _iq_agents = state_data.get("agents", {})

    if not _iq_agents:
        st.info(
            "No simulation data found. "
            "Run `python run_sim.py` to generate v1.8 output, then refresh."
        )
    else:
        for _iq_agent_name, _iq_agent_data in _iq_agents.items():
            st.subheader(f"Agent: {_iq_agent_name}")

            _um = _iq_agent_data.get("uncertainty_monitor", {})
            _um_register = _um.get("register", {})
            _um_levels = _um_register.get("levels", {})
            _um_history = _um_register.get("history", [])
            _um_questions = _um.get("question_log", [])
            _um_inquiries = _um.get("inquiry_log", [])
            _um_tags = _um.get("knowledge_tags", [])
            _um_state_counts = _um.get("knowledge_state_counts", {})
            _um_metrics = _um.get("metrics", {})

            if not _um:
                st.info(
                    f"No uncertainty data for {_iq_agent_name}. "
                    "Run a v1.8 simulation first."
                )
                st.divider()
                continue

            # ── v1.8 Metric summary ───────────────────────────────────────
            _uq_col1, _uq_col2, _uq_col3, _uq_col4, _uq_col5 = st.columns(5)
            _uq_col1.metric(
                "Uncertainty Awareness",
                f"{_um_metrics.get('uncertainty_awareness_quality', 0.0):.3f}",
                help="Fraction of turns with at least one self-question generated",
            )
            _uq_col2.metric(
                "Inquiry Usefulness",
                f"{_um_metrics.get('inquiry_usefulness', 0.0):.3f}",
                help="Avg ambiguity reduction per inquiry action (norm. to 0.2 = 1.0)",
            )
            _uq_col3.metric(
                "Epistemic Stability",
                f"{_um_metrics.get('epistemic_stability', 0.0):.3f}",
                help="1 − mean uncertainty across all domains (higher = more stable)",
            )
            _uq_col4.metric(
                "Question Relevance",
                f"{_um_metrics.get('self_question_relevance', 0.0):.3f}",
                help="Avg relevance score of self-generated questions",
            )
            _uq_col5.metric(
                "Ambiguity Reduction",
                f"{_um_metrics.get('ambiguity_reduction_effectiveness', 0.0):.3f}",
                help="Fraction of generated questions answered by inquiry actions",
            )

            _up_col1, _up_col2, _up_col3 = st.columns(3)
            _up_col1.metric("Questions Generated", _um_metrics.get("total_questions_generated", 0))
            _up_col2.metric("Inquiry Actions", _um_metrics.get("total_inquiry_actions", 0))
            _up_col3.metric("Questions Answered", _um_metrics.get("questions_answered", 0))

            # ── Uncertainty register ──────────────────────────────────────
            if _um_levels:
                st.markdown("### Uncertainty Register")
                _ur_cols = st.columns(len(_um_levels))
                for _col, (_domain, _level) in zip(_ur_cols, _um_levels.items()):
                    _col.metric(
                        _domain.replace("_", " ").title(),
                        f"{_level:.3f}",
                        help=f"Current uncertainty for domain '{_domain}'",
                    )

                # Uncertainty trends chart
                if len(_um_history) >= 2:
                    st.markdown("**Uncertainty over Turns:**")
                    _domains_list = list(_um_levels.keys())
                    # Build chart data as {turn: {domain: level}}
                    _chart_data: dict = {}
                    for _snap in _um_history:
                        _t = _snap.get("turn", 0)
                        for _d in _domains_list:
                            if _d not in _chart_data:
                                _chart_data[_d] = {}
                            _chart_data[_d][_t] = _snap.get(_d, 0.0)
                    # Build per-turn dict for st.line_chart (turn → {domain: value})
                    _all_turns = sorted(
                        set(int(_snap.get("turn", 0)) for _snap in _um_history)
                    )
                    _line_data = {
                        _d.replace("_", " "): [
                            _chart_data.get(_d, {}).get(_t, 0.0)
                            for _t in _all_turns
                        ]
                        for _d in _domains_list
                    }
                    st.line_chart(_line_data)

            # ── Knowledge state breakdown ─────────────────────────────────
            if _um_state_counts:
                st.markdown("### Known vs Uncertain vs Unresolved")
                _ks_cols = st.columns(5)
                _states = ["known", "uncertain", "unresolved", "contradicted", "speculative"]
                for _col, _state in zip(_ks_cols, _states):
                    _col.metric(
                        _state.title(),
                        _um_state_counts.get(_state, 0),
                    )

            # Knowledge tags table
            if _um_tags:
                with st.expander(
                    f"Knowledge State Tags ({len(_um_tags)} items)",
                    expanded=False,
                ):
                    _tag_rows = [
                        {
                            "Turn": _t.get("turn", ""),
                            "Type": _t.get("item_type", ""),
                            "ID": _t.get("item_id", ""),
                            "Summary": (_t.get("item_summary") or "")[:50],
                            "State": _t.get("state", ""),
                            "Confidence": f"{_t.get('confidence', 0.0):.2f}",
                        }
                        for _t in sorted(
                            _um_tags,
                            key=lambda x: x.get("state", ""),
                        )
                    ]
                    st.dataframe(_tag_rows, use_container_width=True)

            # ── Self-generated questions ──────────────────────────────────
            if _um_questions:
                st.markdown("### Self-Generated Questions")
                _answered = [q for q in _um_questions if q.get("answered")]
                _unanswered = [q for q in _um_questions if not q.get("answered")]
                _sq_col1, _sq_col2 = st.columns(2)
                _sq_col1.metric("Answered", len(_answered))
                _sq_col2.metric("Unanswered", len(_unanswered))

                # Most recent unanswered questions
                if _unanswered:
                    st.markdown("**Open Questions (most recent first):**")
                    for _q in _unanswered[-5:][::-1]:
                        st.markdown(
                            f"- **Turn {_q.get('turn')}** · `{_q.get('domain', '').replace('_', ' ')}` "
                            f"[{_q.get('knowledge_state', 'uncertain')}] — "
                            f"{_q.get('question', '—')}"
                        )

                with st.expander(
                    f"Full Question Log ({len(_um_questions)} entries)",
                    expanded=False,
                ):
                    _q_rows = [
                        {
                            "Turn": _q.get("turn", ""),
                            "Domain": _q.get("domain", "").replace("_", " "),
                            "State": _q.get("knowledge_state", ""),
                            "Relevance": f"{_q.get('relevance_score', 0.0):.2f}",
                            "Question": (_q.get("question") or "")[:70],
                            "Answered": "✅" if _q.get("answered") else "❌",
                            "Answer": (_q.get("answer_summary") or "")[:50],
                        }
                        for _q in _um_questions[-20:][::-1]
                    ]
                    st.dataframe(_q_rows, use_container_width=True)

            # ── Inquiry actions ───────────────────────────────────────────
            if _um_inquiries:
                st.markdown("### Inquiry Actions")

                # Ambiguity reduction trend
                _red_data = {
                    str(_a.get("turn", i)): _a.get("ambiguity_reduced", 0.0)
                    for i, _a in enumerate(_um_inquiries)
                }
                if len(_red_data) >= 2:
                    st.markdown("**Ambiguity Reduction per Turn:**")
                    st.bar_chart(_red_data)

                with st.expander(
                    f"Inquiry Action Log ({len(_um_inquiries)} actions)",
                    expanded=False,
                ):
                    _ia_rows = [
                        {
                            "Turn": _a.get("turn", ""),
                            "Domain": _a.get("domain", "").replace("_", " "),
                            "Action": _a.get("action", "").replace("_", " "),
                            "Before": f"{_a.get('uncertainty_before', 0.0):.3f}",
                            "After": f"{_a.get('uncertainty_after', 0.0):.3f}",
                            "Reduced": f"{_a.get('ambiguity_reduced', 0.0):.3f}",
                            "Note": (_a.get("outcome_note") or "")[:60],
                        }
                        for _a in _um_inquiries[-20:][::-1]
                    ]
                    st.dataframe(_ia_rows, use_container_width=True)

            st.divider()

        # ── v1.8 Evaluation metrics summary ──────────────────────────────
        _eval_v18_path = active_dir / "evaluation_report.json"
        _eval_v18: dict = {}
        try:
            with open(_eval_v18_path, encoding="utf-8") as _fh18:
                _eval_v18 = json.load(_fh18)
        except (OSError, json.JSONDecodeError):
            pass

        if _eval_v18:
            st.subheader("v1.8 Evaluation Metrics")
            _v18_keys = [
                ("uncertainty_awareness_quality", "Y. Uncertainty Awareness"),
                ("inquiry_usefulness", "Z. Inquiry Usefulness"),
                ("epistemic_stability", "AA. Epistemic Stability"),
                ("self_question_relevance", "BB. Self-Question Relevance"),
                ("ambiguity_reduction_effectiveness", "CC. Ambiguity Reduction"),
            ]
            _v18_cats = _eval_v18.get("categories", {})
            _v18_cols = st.columns(len(_v18_keys))
            for _col, (_key, _label) in zip(_v18_cols, _v18_keys):
                _cat = _v18_cats.get(_key, {})
                _col.metric(
                    _label,
                    f"{_cat.get('score', 0.0):.1f}",
                    _cat.get("interpretation", "—"),
                )

            with st.expander("Detailed v1.8 Metric Raw Values", expanded=False):
                for _key, _label in _v18_keys:
                    _cat = _v18_cats.get(_key, {})
                    st.markdown(f"**{_label}** — Score: {_cat.get('score', 0.0):.1f}")
                    _raw = _cat.get("raw", {})
                    if _raw:
                        for _rk, _rv in _raw.items():
                            st.markdown(
                                f"  - {_rk.replace('_', ' ').title()}: `{_rv}`"
                            )

    st.divider()
    st.caption(
        "v1.8 Inquiry / Uncertainty tab — Commons Sentience Sandbox v1.8.0. "
        "No sentience is claimed. This displays introspective structure, "
        "uncertainty handling, and sentience-like continuity in "
        "continuity-governed simulated agents."
    )


# ===========================================================================
# TAB R — Identity / Narrative v1.9
# ===========================================================================

with tab_identity:
    st.header("🪞 Identity / Narrative — v1.9")
    st.caption(
        "Identity stability pressure, narrative self-model, value tension tracking, "
        "and self-judgment logs. No sentience is claimed. This tab displays "
        "narrative self-structure, identity continuity, and sentience-like "
        "internal organisation in continuity-governed simulated agents."
    )

    _agent_selector_id = st.selectbox(
        "Select agent",
        list(agents_data.keys()) if agents_data else ["(none)"],
        key="id_agent_selector",
    )
    _id_agent: dict = agents_data.get(_agent_selector_id, {})

    if not _id_agent:
        st.info("No simulation data found. Run `python run_sim.py` first.")
    else:
        # ── Identity Pressure System ──────────────────────────────────────
        _ips: dict = _id_agent.get("identity_pressure_system", {})
        _ips_metrics: dict = _ips.get("metrics", {})
        _ips_history: list = _ips.get("deviation_history", [])

        st.subheader("Identity Stability Pressure")
        _id_cols = st.columns(4)
        _id_cols[0].metric(
            "Deviation Score",
            f"{_ips.get('deviation_score', 0.0):.3f}",
            help="0 = fully stable, 1 = maximal drift.",
        )
        _id_cols[1].metric(
            "Realignment Pressure",
            f"{_ips.get('realignment_pressure', 0.0):.3f}",
            help="Pressure to realign with core identity (0–1).",
        )
        _id_cols[2].metric(
            "Destabilising?",
            "YES ⚠️" if _ips.get("is_destabilising") else "No ✓",
        )
        _id_cols[3].metric(
            "Mean Deviation",
            f"{_ips_metrics.get('mean_deviation_score', 0.0):.3f}",
            help="Average deviation across the run.",
        )

        # Identity drift over time chart
        if _ips_history:
            _drift_data = {
                str(h.get("turn", i)): h.get("deviation_score", 0.0)
                for i, h in enumerate(_ips_history)
            }
            st.markdown("**Identity Deviation Score over Time:**")
            st.line_chart(_drift_data)

            _pressure_data = {
                str(h.get("turn", i)): h.get("realignment_pressure", 0.0)
                for i, h in enumerate(_ips_history)
            }
            st.markdown("**Realignment Pressure over Time:**")
            st.line_chart(_pressure_data)

            with st.expander(
                f"Deviation History ({len(_ips_history)} entries)",
                expanded=False,
            ):
                _hist_rows = [
                    {
                        "Turn": h.get("turn", ""),
                        "Deviation": f"{h.get('deviation_score', 0.0):.3f}",
                        "Pressure": f"{h.get('realignment_pressure', 0.0):.3f}",
                        "Drift Type": h.get("drift_type", ""),
                        "Destabilising": "⚠️" if h.get("is_destabilising") else "—",
                    }
                    for h in _ips_history[-30:][::-1]
                ]
                st.dataframe(_hist_rows, use_container_width=True)

        st.divider()

        # ── Narrative Self Model ──────────────────────────────────────────
        _ns: dict = _id_agent.get("narrative_self", {})
        _ns_history: list = _ns.get("summary_history", [])

        st.subheader("Narrative Self-Model")
        if _ns:
            _ns_cols = st.columns(2)
            with _ns_cols[0]:
                st.markdown("**Who I believe I am:**")
                st.info(_ns.get("who_i_am", "—"))
                st.markdown("**How I have been behaving recently:**")
                st.info(_ns.get("recent_behaviour_pattern", "—"))
            with _ns_cols[1]:
                st.markdown("**Stability Trajectory:**")
                _traj = _ns.get("stability_trajectory", "unknown")
                _traj_icon = (
                    "🟢 Stabilising" if _traj == "stabilising" else
                    "🔴 Drifting" if _traj == "drifting" else
                    "🟡 Uncertain"
                )
                st.info(_traj_icon)
                st.markdown("**Becoming:**")
                st.info(_ns.get("becoming", "—"))

            _str_col, _fail_col = st.columns(2)
            with _str_col:
                st.markdown("**Recurring Strengths:**")
                strengths = _ns.get("recurring_strengths", [])
                if strengths:
                    for s in strengths:
                        st.markdown(f"  ✅ {s}")
                else:
                    st.markdown("  *None identified yet.*")

            with _fail_col:
                st.markdown("**Recurring Failures:**")
                failures = _ns.get("recurring_failures", [])
                if failures:
                    for f in failures:
                        st.markdown(f"  ⚠️ {f}")
                else:
                    st.markdown("  *None identified yet.*")

            st.markdown("**Current Narrative Summary:**")
            st.markdown(f"> {_ns.get('current_summary', '—')}")

            if _ns_history:
                with st.expander(
                    f"Narrative History ({len(_ns_history)} entries)",
                    expanded=False,
                ):
                    _ns_rows = [
                        {
                            "Turn": h.get("turn", ""),
                            "Trajectory": h.get("stability_trajectory", ""),
                            "Deviation": f"{h.get('identity_deviation', 0.0):.3f}",
                            "Consistency": f"{h.get('self_consistency', 0.0):.3f}",
                            "Strengths": ", ".join(h.get("recurring_strengths", [])),
                            "Failures": ", ".join(h.get("recurring_failures", [])),
                        }
                        for h in _ns_history[-20:][::-1]
                    ]
                    st.dataframe(_ns_rows, use_container_width=True)
        else:
            st.info("Narrative self-model not yet populated.")

        st.divider()

        # ── Value Tension Tracking ────────────────────────────────────────
        _vt_list: list = _ips.get("value_tensions", [])

        st.subheader("Value Tension Tracking")
        if _ips_metrics:
            _vt_cols = st.columns(4)
            _vt_cols[0].metric("Total Tensions", _ips_metrics.get("total_tensions", 0))
            _vt_cols[1].metric("Unresolved", _ips_metrics.get("unresolved_tensions", 0))
            _vt_cols[2].metric("Chronic", _ips_metrics.get("chronic_tensions", 0))
            _vt_cols[3].metric("Resolved", _ips_metrics.get("resolved_tensions", 0))

        if _vt_list:
            # Status filter
            _vt_status_filter = st.selectbox(
                "Filter by status",
                ["all", "acute", "chronic", "resolved", "suppressed"],
                key="vt_status_filter",
            )
            _filtered_vt = (
                _vt_list if _vt_status_filter == "all"
                else [t for t in _vt_list if t.get("status") == _vt_status_filter]
            )

            _vt_rows = [
                {
                    "ID": t.get("tension_id", ""),
                    "Value A": t.get("value_a", "").replace("_", " "),
                    "Value B": t.get("value_b", "").replace("_", " "),
                    "Status": t.get("status", ""),
                    "Occurrences": t.get("occurrences", 0),
                    "First Turn": t.get("first_seen", ""),
                    "Last Turn": t.get("last_seen", ""),
                    "Mean Intensity": f"{t.get('mean_intensity', 0.0):.3f}",
                }
                for t in _filtered_vt
            ]
            if _vt_rows:
                st.dataframe(_vt_rows, use_container_width=True)

                # Chronic tension highlight
                _chronic = [t for t in _vt_list if t.get("status") == "chronic"]
                if _chronic:
                    st.markdown("**Chronic (persistent) tensions:**")
                    for t in _chronic:
                        st.warning(
                            f"🔄 **{t.get('value_a', '').replace('_', ' ')} ↔ "
                            f"{t.get('value_b', '').replace('_', ' ')}** — "
                            f"{t.get('occurrences', 0)} occurrences, "
                            f"mean intensity: {t.get('mean_intensity', 0.0):.2f}"
                        )
            else:
                st.info(f"No tensions with status '{_vt_status_filter}'.")
        else:
            st.info("No value tensions recorded yet.")

        st.divider()

        # ── Self-Judgment Log ─────────────────────────────────────────────
        _sj_log: list = _id_agent.get("self_judgment_log", [])

        st.subheader("Self-Judgment Log")
        if _sj_log:
            _sj_recent = _sj_log[-1] if _sj_log else {}
            _sj_mean = (
                round(
                    sum(j.get("composite_score", 0.0) for j in _sj_log)
                    / len(_sj_log),
                    3,
                )
                if _sj_log else 0.0
            )

            _sj_metric_cols = st.columns(3)
            _sj_metric_cols[0].metric(
                "Self-Judgment Entries",
                len(_sj_log),
            )
            _sj_metric_cols[1].metric(
                "Mean Composite Score",
                f"{_sj_mean:.3f}",
                help="0 = poor self-assessed integrity, 1 = strong.",
            )
            _sj_metric_cols[2].metric(
                "Latest Composite",
                f"{_sj_recent.get('composite_score', 0.0):.3f}",
            )

            # Composite score over time
            if len(_sj_log) >= 2:
                _sj_score_data = {
                    str(j.get("turn", i)): j.get("composite_score", 0.0)
                    for i, j in enumerate(_sj_log)
                }
                st.markdown("**Composite Self-Judgment Score over Time:**")
                st.line_chart(_sj_score_data)

            # Dimension breakdown of most recent judgment
            if _sj_recent:
                st.markdown("**Most Recent Judgment Breakdown:**")
                _dim_cols = st.columns(3)
                _dims = [
                    ("Alignment w/ Identity", "alignment_with_identity"),
                    ("Quality of Action", "quality_of_action"),
                    ("Plan Success", "plan_success"),
                    ("Contradiction Recurrence", "contradiction_recurrence"),
                    ("Trust Repair Success", "trust_repair_success"),
                    ("Perceived Integrity", "perceived_integrity"),
                ]
                for i, (label, key) in enumerate(_dims):
                    _dim_cols[i % 3].metric(
                        label,
                        f"{_sj_recent.get(key, 0.0):.3f}",
                    )
                if _sj_recent.get("notes"):
                    st.caption(f"Notes: {_sj_recent['notes']}")

            with st.expander(
                f"Full Self-Judgment Log ({len(_sj_log)} entries)",
                expanded=False,
            ):
                _sj_rows = [
                    {
                        "Turn": j.get("turn", ""),
                        "Trigger": j.get("trigger", ""),
                        "Alignment": f"{j.get('alignment_with_identity', 0.0):.3f}",
                        "Quality": f"{j.get('quality_of_action', 0.0):.3f}",
                        "Plan": f"{j.get('plan_success', 0.0):.3f}",
                        "Contradiction": f"{j.get('contradiction_recurrence', 0.0):.3f}",
                        "Trust Repair": f"{j.get('trust_repair_success', 0.0):.3f}",
                        "Integrity": f"{j.get('perceived_integrity', 0.0):.3f}",
                        "Composite": f"{j.get('composite_score', 0.0):.3f}",
                    }
                    for j in _sj_log[-30:][::-1]
                ]
                st.dataframe(_sj_rows, use_container_width=True)
        else:
            st.info("No self-judgment entries recorded yet.")

        st.divider()

        # ── v1.9 Evaluation Metrics ───────────────────────────────────────
        _eval_v19_path = active_dir / "evaluation_report.json"
        _eval_v19: dict = {}
        try:
            with open(_eval_v19_path, encoding="utf-8") as _fh19:
                _eval_v19 = json.load(_fh19)
        except (OSError, json.JSONDecodeError):
            pass

        if _eval_v19:
            st.subheader("v1.9 Evaluation Metrics")
            _v19_keys = [
                ("identity_stability", "DD. Identity Stability"),
                ("narrative_coherence", "EE. Narrative Coherence"),
                ("value_tension_resolution", "FF. Value Tension Resolution"),
                ("self_alignment_quality", "GG. Self-Alignment Quality"),
                ("identity_driven_planning", "HH. Identity-Driven Planning"),
            ]
            _v19_cats = _eval_v19.get("categories", {})
            _v19_cols = st.columns(len(_v19_keys))
            for _col, (_key, _label) in zip(_v19_cols, _v19_keys):
                _cat = _v19_cats.get(_key, {})
                _col.metric(
                    _label,
                    f"{_cat.get('score', 0.0):.1f}",
                    _cat.get("interpretation", "—"),
                )

            with st.expander("Detailed v1.9 Metric Raw Values", expanded=False):
                for _key, _label in _v19_keys:
                    _cat = _v19_cats.get(_key, {})
                    st.markdown(f"**{_label}** — Score: {_cat.get('score', 0.0):.1f}")
                    _raw = _cat.get("raw", {})
                    if _raw:
                        for _rk, _rv in _raw.items():
                            st.markdown(
                                f"  - {_rk.replace('_', ' ').title()}: `{_rv}`"
                            )

    st.divider()
    st.caption(
        "v1.9 Identity / Narrative tab — Commons Sentience Sandbox v1.9.0. "
        "No sentience is claimed. This displays narrative self-structure, "
        "identity continuity, and sentience-like internal organisation in "
        "continuity-governed simulated agents."
    )


# ===========================================================================
# TAB S — Narrative Identity v2.0
# ===========================================================================

with tab_narrative_v2:
    st.header("📖 Narrative Identity — v2.0")
    st.caption(
        "v2.0 narrative identity: persistent identity timeline, milestone memories, "
        "continuity rupture tracking, narrative themes, self-authored project threads, "
        "and chain coherence analysis. No sentience is claimed."
    )

    _ni_state = state_data or {}
    _ni_agents = _ni_state.get("agents", {})

    if not _ni_agents:
        st.info(
            "No simulation data found. Run `python run_sim.py --name my_run` "
            "to generate v2.0 narrative identity output, then refresh."
        )
    else:
        # ── Agent selector ────────────────────────────────────────────────
        _ni_agent_names = list(_ni_agents.keys())
        _ni_selected = st.selectbox(
            "Select agent", _ni_agent_names, key="ni_v2_agent_select"
        )
        _ni_agent = _ni_agents.get(_ni_selected, {})
        _ni = _ni_agent.get("narrative_identity", {})

        if not _ni:
            st.warning(
                f"No v2.0 narrative identity data for {_ni_selected}. "
                "Run a v2.0 simulation first."
            )
        else:
            # ── Key metrics row ───────────────────────────────────────────
            _coh_score = _ni.get("narrative_coherence_score", 0.0)
            _milestones = len(_ni.get("milestone_memories", []))
            _ruptures = _ni.get("continuity_rupture_events", [])
            _repaired = sum(1 for r in _ruptures if r.get("repaired", False))
            _themes = _ni.get("narrative_themes", [])
            _timeline = _ni.get("identity_timeline", [])
            _revisions = len(_ni.get("self_narrative_history", []))

            _m1, _m2, _m3, _m4, _m5 = st.columns(5)
            _m1.metric("Narrative Coherence", f"{_coh_score:.3f}")
            _m2.metric("Milestone Memories", str(_milestones))
            _m3.metric("Ruptures", f"{len(_ruptures)} ({_repaired} repaired)")
            _m4.metric("Active Themes", str(len(_themes)))
            _m5.metric("Narrative Revisions", str(_revisions))

            st.divider()

            # ── Self-narrative summary ────────────────────────────────────
            _summary = _ni.get("self_narrative_summary", "")
            if _summary:
                st.subheader("Current Self-Narrative")
                st.info(_summary)
            else:
                st.subheader("Current Self-Narrative")
                st.caption("No self-narrative summary generated yet.")

            # ── Narrative revision history ────────────────────────────────
            _hist = _ni.get("self_narrative_history", [])
            if _hist:
                with st.expander(f"Narrative Revision History ({len(_hist)} entries)", expanded=False):
                    for h in reversed(_hist[-10:]):
                        _h_turn = h.get("turn", "?")
                        _h_run = h.get("run_label", "")
                        _h_coh = h.get("coherence", 0.0)
                        _h_sum = h.get("summary", "")
                        st.markdown(
                            f"**Turn {_h_turn}** (run: `{_h_run}`, coherence: `{_h_coh:.3f}`)"
                        )
                        if _h_sum:
                            st.caption(_h_sum[:300])
                        st.divider()

            st.divider()

            # ── Identity timeline ─────────────────────────────────────────
            st.subheader("Identity Timeline")
            if _timeline:
                _timeline_rows = [
                    {
                        "Turn": e.get("turn", ""),
                        "Run": e.get("run_label", ""),
                        "Type": e.get("event_type", ""),
                        "Description": e.get("description", "")[:80],
                        "Coherence Δ": f"{e.get('coherence_after', 0) - e.get('coherence_before', 0):+.3f}",
                        "Identity Impact": f"{e.get('identity_impact', 0.0):.2f}",
                    }
                    for e in sorted(_timeline, key=lambda x: x.get("turn", 0), reverse=True)[:20]
                ]
                st.dataframe(_timeline_rows, use_container_width=True)
            else:
                st.caption("No identity timeline events recorded yet.")

            st.divider()

            # ── Milestone memories ────────────────────────────────────────
            st.subheader("Milestone Memories")
            _milestone_list = _ni.get("milestone_memories", [])
            if _milestone_list:
                _ms_rows = [
                    {
                        "Turn": m.get("turn", ""),
                        "Run": m.get("run_label", ""),
                        "Summary": m.get("summary", "")[:80],
                        "Relevance": f"{m.get('identity_relevance_score', 0.0):.3f}",
                        "Resonance": m.get("emotional_resonance", ""),
                        "Themes": ", ".join(m.get("linked_themes", [])[:3]),
                    }
                    for m in sorted(
                        _milestone_list,
                        key=lambda x: x.get("identity_relevance_score", 0.0),
                        reverse=True,
                    )[:15]
                ]
                st.dataframe(_ms_rows, use_container_width=True)
            else:
                st.caption("No milestone memories selected yet.")

            st.divider()

            # ── Continuity rupture events ─────────────────────────────────
            st.subheader("Continuity Rupture Events")
            if _ruptures:
                _rup_rows = [
                    {
                        "Turn": r.get("turn", ""),
                        "Run": r.get("run_label", ""),
                        "Trigger": r.get("trigger", ""),
                        "Coherence Drop": f"{r.get('coherence_drop', 0.0):.3f}",
                        "Before": f"{r.get('coherence_before', 0.0):.3f}",
                        "After": f"{r.get('coherence_after', 0.0):.3f}",
                        "Repaired": "✅" if r.get("repaired") else "❌",
                        "Repair Turn": str(r.get("repair_turn", "—")),
                    }
                    for r in sorted(_ruptures, key=lambda x: x.get("turn", 0))
                ]
                st.dataframe(_rup_rows, use_container_width=True)
            else:
                st.success("No continuity rupture events detected — coherence is stable.")

            st.divider()

            # ── Narrative themes ──────────────────────────────────────────
            st.subheader("Narrative Themes")
            if _themes:
                try:
                    import matplotlib.pyplot as plt
                    _theme_names = [t.get("theme", "") for t in _themes]
                    _theme_intensities = [t.get("intensity", 0.0) for t in _themes]
                    _fig, _ax = plt.subplots(figsize=(8, 3))
                    _bars = _ax.barh(
                        _theme_names,
                        _theme_intensities,
                        color="#6C8EBF",
                        edgecolor="#4A6FA5",
                    )
                    _ax.set_xlim(0, 1.0)
                    _ax.set_xlabel("Intensity")
                    _ax.set_title(f"Narrative Themes — {_ni_selected}")
                    _ax.bar_label(_bars, fmt="%.2f", padding=3, fontsize=8)
                    plt.tight_layout()
                    st.pyplot(_fig)
                    plt.close(_fig)
                except ImportError:
                    _theme_rows = [
                        {
                            "Theme": t.get("theme", ""),
                            "Occurrences": t.get("occurrence_count", 0),
                            "Intensity": f"{t.get('intensity', 0.0):.3f}",
                            "First Seen": t.get("first_seen_turn", ""),
                            "Last Seen": t.get("last_seen_turn", ""),
                        }
                        for t in sorted(_themes, key=lambda x: x.get("intensity", 0.0), reverse=True)
                    ]
                    st.dataframe(_theme_rows, use_container_width=True)
            else:
                st.caption("No narrative themes recorded yet.")

            st.divider()

            # ── Unresolved identity tensions ──────────────────────────────
            _tensions = _ni.get("unresolved_identity_tensions", [])
            if _tensions:
                st.subheader("Unresolved Identity Tensions")
                for t in _tensions[:5]:
                    st.markdown(f"- {t}")
            else:
                st.success("No unresolved identity tensions.")

        st.divider()

        # ── Self-authored project threads ─────────────────────────────────
        st.subheader("🔧 Self-Authored Project Threads")
        _pt = _ni_agent.get("project_thread_manager", {})
        _active_threads = [
            t for t in _pt.get("threads", []) if t.get("status") in ("active", "paused")
        ]
        _completed_threads = _pt.get("completed_threads", [])
        _all_threads = _active_threads + _completed_threads

        if not _all_threads and not _pt.get("project_generation_log"):
            st.caption(
                "No self-authored project threads generated yet. "
                "Projects are generated automatically when contradiction pressure, "
                "trust, or rupture thresholds are met."
            )
        else:
            _pt_cols = st.columns(3)
            _pt_cols[0].metric("Active Threads", str(len(_active_threads)))
            _pt_cols[1].metric("Completed", str(len(_completed_threads)))
            _pt_cols[2].metric(
                "Generated Total",
                str(len(_pt.get("project_generation_log", []))),
            )

            if _all_threads:
                _thread_rows = [
                    {
                        "Title": t.get("title", "")[:50],
                        "Status": t.get("status", ""),
                        "Stage": t.get("current_stage", t.get("stages", ["?"])[min(t.get("stage_index", 0), len(t.get("stages", ["?"])) - 1)])[:40],
                        "Progress": f"{t.get('progress_score', 0.0):.0%}",
                        "Origin": t.get("origin_reason", "")[:50],
                        "Theme": t.get("linked_identity_theme", ""),
                        "Created": f"T{t.get('created_at_turn', '?')}",
                    }
                    for t in _all_threads[:10]
                ]
                st.dataframe(_thread_rows, use_container_width=True)

        st.divider()

        # ── Chain coherence analysis ──────────────────────────────────────
        st.subheader("🔗 Chain Coherence Analysis")
        _chain_report_path = Path("sessions") / "chain_run_report.json"
        _chain_data: dict = {}
        try:
            with open(_chain_report_path, encoding="utf-8") as _cfh:
                _chain_data = json.load(_cfh)
        except (OSError, json.JSONDecodeError):
            pass

        if _chain_data:
            _chain_runs = _chain_data.get("runs", [])
            _chain_summary = _chain_data.get("chain_summary", {})

            # Coherence chart across chain
            _coh_by_run = {
                r.get("session_name", f"Run {i+1}"): r.get("narrative_coherence_v2_score", 0.0)
                for i, r in enumerate(_chain_runs)
            }
            if _coh_by_run:
                st.markdown("**Narrative Coherence Across Chain:**")
                st.line_chart(_coh_by_run)

            # Summary metrics
            _cs_cols = st.columns(4)
            _cs_cols[0].metric("Mean Coherence", f"{_chain_summary.get('mean_narrative_coherence', 0.0):.3f}")
            _cs_cols[1].metric("Coherence Trend", _chain_summary.get("coherence_trend", "—"))
            _cs_cols[2].metric("Total Ruptures", str(_chain_summary.get("total_ruptures", 0)))
            _cs_cols[3].metric("Continuity Verdict", _chain_summary.get("continuity_verdict", "—"))

            # Per-run table
            if _chain_runs:
                _chain_table = [
                    {
                        "Run": f"Run {i+1}",
                        "Session": r.get("session_name", "")[:30],
                        "Coherence": f"{r.get('narrative_coherence_v2_score', 0.0):.3f}",
                        "Trust Stability": f"{r.get('trust_stability_score', 0.0):.1f}",
                        "Ruptures": str(r.get("identity_rupture_count", 0)),
                        "Revisions": str(r.get("narrative_revision_count", 0)),
                        "Cooperation": str(r.get("cooperation_events", 0)),
                        "Projects": str(r.get("project_threads_generated", 0)),
                    }
                    for i, r in enumerate(_chain_runs)
                ]
                st.dataframe(_chain_table, use_container_width=True)
        else:
            st.info(
                "No chain run data found. Run `python chain_runs.py` to generate "
                "5 chained sessions, then refresh this tab."
            )

        st.divider()

        # ── Narrative coherence study ─────────────────────────────────────
        st.subheader("📊 Narrative Coherence Study")
        _study_path = Path("sessions") / "narrative_coherence_study.json"
        _study_data: dict = {}
        try:
            with open(_study_path, encoding="utf-8") as _sfh:
                _study_data = json.load(_sfh)
        except (OSError, json.JSONDecodeError):
            pass

        if _study_data:
            _findings = _study_data.get("findings", {})

            # Key findings
            st.markdown("**Key Research Findings:**")
            _f_cols = st.columns(2)
            _f_cols[0].markdown(
                f"**Sentinel stronger identity:** "
                f"{'✅ Yes' if _findings.get('does_sentinel_maintain_stronger_identity') else '❌ No/Unclear'}"
            )
            _f_cols[1].markdown(
                f"**Rupture pattern:** `{_findings.get('rupture_accumulation_pattern', '—')}`"
            )
            st.markdown(
                f"**Revision quality:** `{_findings.get('narrative_revisions_quality', '—')}`"
            )

            # Agent comparison
            _agent_comp = _study_data.get("agent_comparison", {})
            if _agent_comp:
                _ac_rows = [
                    {
                        "Agent": agent,
                        "Mean Coherence": f"{d.get('mean_coherence', 0.0):.3f}",
                        "Ruptures": str(d.get("rupture_count", 0)),
                        "Repair Rate": f"{d.get('repair_rate', 0.0):.0%}",
                        "Revisions": str(d.get("revision_count", 0)),
                    }
                    for agent, d in _agent_comp.items()
                ]
                st.markdown("**Agent Comparison:**")
                st.dataframe(_ac_rows, use_container_width=True)

            # Scenario coherence map
            _scen_map = _study_data.get("scenario_coherence_map", {})
            if _scen_map:
                st.markdown("**Scenario Coherence Map:**")
                _sc_rows = [
                    {"Scenario": sc, "Mean Coherence": f"{v:.3f}"}
                    for sc, v in sorted(_scen_map.items(), key=lambda x: x[1])
                ]
                st.dataframe(_sc_rows, use_container_width=True)

            st.caption(f"Study generated: {_study_data.get('generated_at', '—')[:19]}")
        else:
            st.info(
                "No coherence study found. Run `python narrative_coherence_study.py` "
                "to generate analysis, then refresh."
            )

        # ── v2.0 Evaluation metrics ───────────────────────────────────────
        _eval_v20_path = active_dir / "evaluation_report.json"
        _eval_v20: dict = {}
        try:
            with open(_eval_v20_path, encoding="utf-8") as _fh20:
                _eval_v20 = json.load(_fh20)
        except (OSError, json.JSONDecodeError):
            pass

        if _eval_v20 and "narrative_coherence_v2" in _eval_v20.get("categories", {}):
            st.divider()
            st.subheader("v2.0 Evaluation Metrics")
            _v20_keys = [
                ("narrative_coherence_v2", "II. Narrative Coherence v2.0"),
                ("identity_stability_under_stress", "JJ. ID Stability Under Stress"),
                ("milestone_integration_quality", "KK. Milestone Integration"),
                ("continuity_rupture_recovery", "LL. Rupture Recovery"),
                ("self_narrative_revision_quality", "MM. Narrative Revision"),
                ("project_initiation_quality", "NN. Project Initiation"),
                ("project_persistence_quality", "OO. Project Persistence"),
                ("project_revision_quality", "PP. Project Revision"),
                ("project_completion_relevance", "QQ. Project Completion"),
                ("project_identity_alignment", "RR. Project–Identity Align"),
            ]
            _v20_cats = _eval_v20.get("categories", {})
            # Display in two rows of 5
            for _row_start in (0, 5):
                _row_keys = _v20_keys[_row_start:_row_start + 5]
                _row_cols = st.columns(len(_row_keys))
                for _col, (_key, _label) in zip(_row_cols, _row_keys):
                    _cat = _v20_cats.get(_key, {})
                    _col.metric(
                        _label,
                        f"{_cat.get('score', 0.0):.1f}",
                        _cat.get("interpretation", "—"),
                    )

    st.divider()
    st.caption(
        "v2.0 Narrative Identity tab — Commons Sentience Sandbox v2.0.0. "
        "No sentience is claimed. This displays narrative identity structure, "
        "milestone memories, continuity rupture analysis, and bounded "
        "self-authored project threads in a continuity-governed synthetic "
        "cognition research platform."
    )


if auto_refresh:
    st.sidebar.success("Auto-refresh active \u2014 reloading in 10 s\u2026")
    time.sleep(10)
    st.cache_data.clear()
    st.rerun()
