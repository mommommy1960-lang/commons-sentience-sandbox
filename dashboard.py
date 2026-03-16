"""
Commons Sentience Sandbox — Local Research Dashboard (v0.9)

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
st.sidebar.markdown("**Local Research Dashboard \u2014 v0.9**")
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

st.title("Commons Sentience Sandbox \u2014 Research Dashboard")
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

# ---------------------------------------------------------------------------
# Auto-refresh (must be last)
# ---------------------------------------------------------------------------

if auto_refresh:
    st.sidebar.success("Auto-refresh active \u2014 reloading in 10 s\u2026")
    time.sleep(10)
    st.cache_data.clear()
    st.rerun()
