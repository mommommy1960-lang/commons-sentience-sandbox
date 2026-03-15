"""
Commons Sentience Sandbox — Local Research Dashboard (v0.6)

A lightweight Streamlit dashboard for observing simulation state.
Supports:
  - session selection (saved runs or latest output)
  - turn-by-turn replay
  - side-by-side session comparison
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
st.sidebar.markdown("**Local Research Dashboard \u2014 v0.6**")
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
    "python run_sim.py --name baseline\n\n"
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

            json_path = SESSIONS_DIR / f"comparison_{a_id}_vs_{b_id}.json"
            if json_path.exists():
                st.success(f"Comparison report saved: `{json_path}`")

# ---------------------------------------------------------------------------
# Auto-refresh (must be last)
# ---------------------------------------------------------------------------

if auto_refresh:
    st.sidebar.success("Auto-refresh active \u2014 reloading in 10 s\u2026")
    time.sleep(10)
    st.cache_data.clear()
    st.rerun()
