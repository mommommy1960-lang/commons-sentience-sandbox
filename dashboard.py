"""
Commons Sentience Sandbox — Local Research Dashboard (v0.5)

A lightweight Streamlit dashboard for observing the simulation in real time.
Reads from commons_sentience_sim/output/ and displays all key state, memory,
interaction, and chart data in a structured multi-tab layout.

Run with:
    streamlit run dashboard.py
"""

import csv
import json
import os
import time
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).parent
OUTPUT_DIR = ROOT / "commons_sentience_sim" / "output"

MULTI_AGENT_STATE = OUTPUT_DIR / "multi_agent_state.json"
FINAL_STATE = OUTPUT_DIR / "final_state.json"
STATE_HISTORY_CSV = OUTPUT_DIR / "state_history.csv"
OVERSIGHT_LOG_CSV = OUTPUT_DIR / "oversight_log.csv"
AGENT_RELATIONSHIPS_CSV = OUTPUT_DIR / "agent_relationships.csv"
INTERACTION_LOG_CSV = OUTPUT_DIR / "interaction_log.csv"
NARRATIVE_LOG_MD = OUTPUT_DIR / "narrative_log.md"

PLOTS = {
    "Trust over time (Sentinel)": OUTPUT_DIR / "trust_plot.png",
    "Urgency over time (Sentinel)": OUTPUT_DIR / "urgency_plot.png",
    "Contradiction pressure over time (Sentinel)": OUTPUT_DIR / "contradiction_plot.png",
    "Mutual trust between agents": OUTPUT_DIR / "agent_trust_plot.png",
    "Trust in Queen (per agent)": OUTPUT_DIR / "queen_trust_plot.png",
    "Cooperation vs conflict over time": OUTPUT_DIR / "interactions_plot.png",
}

# ---------------------------------------------------------------------------
# Data loading helpers
# ---------------------------------------------------------------------------


def _mtime(path: Path) -> float:
    """Return file mtime or 0 if missing."""
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


# Cache data keyed by file mtime so it reloads automatically when files change.
# A manual refresh clears the cache via st.cache_data.clear().
def _mtimes() -> tuple:
    return tuple(_mtime(p) for p in (
        MULTI_AGENT_STATE, STATE_HISTORY_CSV, OVERSIGHT_LOG_CSV,
        AGENT_RELATIONSHIPS_CSV, INTERACTION_LOG_CSV, NARRATIVE_LOG_MD,
    ))


@st.cache_data
def get_multi_agent_state(_mtimes: tuple) -> dict:
    return load_json(MULTI_AGENT_STATE)


@st.cache_data
def get_state_history(_mtimes: tuple) -> list[dict]:
    return load_csv(STATE_HISTORY_CSV)


@st.cache_data
def get_oversight_log(_mtimes: tuple) -> list[dict]:
    return load_csv(OVERSIGHT_LOG_CSV)


@st.cache_data
def get_agent_relationships(_mtimes: tuple) -> list[dict]:
    return load_csv(AGENT_RELATIONSHIPS_CSV)


@st.cache_data
def get_interaction_log(_mtimes: tuple) -> list[dict]:
    return load_csv(INTERACTION_LOG_CSV)


@st.cache_data
def get_narrative_log(_mtimes: tuple) -> str:
    return load_text(NARRATIVE_LOG_MD)


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Commons Sentience Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Sidebar — refresh controls
# ---------------------------------------------------------------------------

st.sidebar.title("🧠 Commons Sentience Sandbox")
st.sidebar.markdown("**Local Research Dashboard — v0.5**")
st.sidebar.divider()

if st.sidebar.button("🔄 Refresh now"):
    st.cache_data.clear()
    st.rerun()

auto_refresh = st.sidebar.checkbox("⏱ Auto-refresh every 10 s", value=False)
st.sidebar.divider()
st.sidebar.markdown(
    "**Run commands**\n"
    "```\n"
    "# Simulation\n"
    "python run_sim.py\n\n"
    "# Plots\n"
    "python plot_state.py\n\n"
    "# Dashboard\n"
    "streamlit run dashboard.py\n"
    "```"
)

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

_file_mtimes = _mtimes()
state_data = get_multi_agent_state(_file_mtimes)
state_history = get_state_history(_file_mtimes)
oversight_log = get_oversight_log(_file_mtimes)
agent_relationships = get_agent_relationships(_file_mtimes)
interaction_log = get_interaction_log(_file_mtimes)
narrative_log = get_narrative_log(_file_mtimes)

simulation_version = state_data.get("simulation_version", "unknown")
total_turns = state_data.get("total_turns", "?")
agents_data: dict = state_data.get("agents", {})

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.title("Commons Sentience Sandbox — Research Dashboard")
st.caption(f"v{simulation_version}  ·  Output directory: `{OUTPUT_DIR}`")

if not state_data:
    st.error(
        "No simulation data found. Run `python run_sim.py` to generate output files, "
        "then refresh the dashboard."
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
) = st.tabs(
    [
        "📊 Overview",
        "🤖 Agents",
        "🏠 Rooms",
        "🧩 Memory",
        "🔗 Interactions",
        "📈 Charts",
    ]
)

# ===========================================================================
# TAB A — Simulation Overview
# ===========================================================================

with tab_overview:
    st.header("Simulation Overview")

    # derive values from state and history
    current_turn = total_turns  # final turn from state file
    if state_history:
        last_row = state_history[-1]
        current_turn = last_row.get("turn", total_turns)
        last_action = last_row.get("action", "—")
        last_event = last_row.get("event_type", "—")
    else:
        last_action = "—"
        last_event = "—"

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Current Turn", current_turn)
    col2.metric("Total Turns", total_turns)
    col3.metric("Last Action", last_action)
    col4.metric("Last Event Type", last_event)

    st.divider()

    st.subheader("Recent Turn History (last 10 turns)")
    if state_history:
        recent = state_history[-10:][::-1]
        display_rows = []
        for row in recent:
            display_rows.append(
                {
                    "Turn": row.get("turn", ""),
                    "Room": row.get("room", ""),
                    "Action": row.get("action", ""),
                    "Event Type": row.get("event_type", ""),
                    "Urgency": row.get("urgency", ""),
                    "Trust": row.get("trust", ""),
                    "Contradiction Pressure": row.get("contradiction_pressure", ""),
                }
            )
        st.table(display_rows)
    else:
        st.info("No state history available.")

    st.divider()

    st.subheader("Governance Audit — Recent Actions")
    if oversight_log:
        recent_oversight = oversight_log[-10:][::-1]
        display_rows = []
        for row in recent_oversight:
            display_rows.append(
                {
                    "Turn": row.get("turn", ""),
                    "Room": row.get("room", ""),
                    "Action": row.get("action", ""),
                    "Permitted": row.get("permitted", ""),
                    "Reason": row.get("reason", ""),
                    "Event Type": row.get("event_type", ""),
                }
            )
        st.table(display_rows)
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

            # Most recent action from state_history (only Sentinel recorded there)
            recent_action = "—"
            recent_reasoning = "—"
            dominant_value = "—"
            if agent_name == "Sentinel" and state_history:
                last = state_history[-1]
                recent_action = last.get("action", "—")

            with col:
                st.subheader(f"🤖 {agent_name}")
                purpose = identity.get("purpose", "")
                st.caption(purpose[:120] + ("…" if len(purpose) > 120 else ""))

                st.markdown(f"**Room:** `{agent.get('active_room', '—')}`")
                st.markdown(f"**Turn:** {agent.get('turn', '—')}  |  **Memories:** {agent.get('episodic_memory_count', 0)}")

                st.markdown("**Affective State**")
                m1, m2 = st.columns(2)
                m1.metric("Urgency", f"{affective.get('urgency', 0):.2f}")
                m2.metric("Trust", f"{affective.get('trust', 0):.2f}")
                m3, m4 = st.columns(2)
                m3.metric("Contradiction Pressure", f"{affective.get('contradiction_pressure', 0):.2f}")
                m4.metric("Recovery", f"{affective.get('recovery', 0):.2f}")

                st.divider()

                # Trust in Queen
                queen_trust = relational_memory.get("Queen", {}).get("trust_level", None)
                if queen_trust is not None:
                    st.markdown(f"**Trust in Queen:** `{queen_trust:.2f}`")
                else:
                    st.markdown("**Trust in Queen:** —")

                # Trust in other agent
                for other_name, rel in relationships.items():
                    st.markdown(
                        f"**Trust in {other_name}:** `{rel.get('trust', 0):.2f}`  "
                        f"(coop: {rel.get('cooperation_count', 0)}, "
                        f"conflict: {rel.get('conflict_count', 0)})"
                    )

                st.divider()

                # Most recent action
                st.markdown(f"**Most Recent Action:** `{recent_action}`")

                st.divider()

                # Goals
                with st.expander("Goals", expanded=False):
                    for g in goals:
                        st.markdown(f"- {g}")

                # Latest reflection
                reflections = agent.get("reflection_entries", [])
                if reflections:
                    latest_ref = reflections[-1]
                    with st.expander("Latest Reflection", expanded=False):
                        st.markdown(f"**Turn {latest_ref.get('turn', '?')} — {latest_ref.get('trigger', '')}**")
                        for field in (
                            "what_happened",
                            "what_mattered",
                            "what_conflicted",
                            "what_changed",
                            "future_adjustment",
                        ):
                            val = latest_ref.get(field)
                            if val:
                                st.markdown(f"**{field.replace('_', ' ').title()}:** {val}")

# ===========================================================================
# TAB C — Room View
# ===========================================================================

with tab_rooms:
    st.header("Room View")

    # Build agent-to-room mapping
    agent_room_map: dict[str, list[str]] = {}
    for agent_name, agent in agents_data.items():
        room = agent.get("active_room", "—")
        agent_room_map.setdefault(room, []).append(agent_name)

    # Load rooms data
    rooms_path = ROOT / "commons_sentience_sim" / "data" / "rooms.json"
    rooms_data: dict = {}
    try:
        rooms_raw = load_json(rooms_path)
        # rooms.json is a dict keyed by room name
        rooms_data = rooms_raw
    except Exception:
        rooms_data = {}

    # Display each room
    room_names = list(rooms_data.keys()) if rooms_data else list(agent_room_map.keys())
    if not room_names:
        st.info("No room data available.")
    else:
        for room_name in room_names:
            agents_here = agent_room_map.get(room_name, [])
            agent_badge = " · ".join(f"🤖 **{a}**" for a in agents_here) if agents_here else ""
            header_text = f"🏠 {room_name}"
            if agent_badge:
                header_text += f"  —  {agent_badge}"

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
                            state = obj_data.get("state", "—")
                            desc = obj_data.get("description", "")
                            obj_rows.append(
                                {
                                    "Object": obj_name,
                                    "State": state,
                                    "Description": (desc[:80] + "…") if len(desc) > 80 else desc,
                                }
                            )
                        else:
                            obj_rows.append({"Object": obj_name, "State": str(obj_data), "Description": ""})
                    st.table(obj_rows)

                interactions = room_info.get("actions", room_info.get("interactions", []))
                if interactions:
                    st.markdown("**Available Actions:** " + " · ".join(f"`{i}`" for i in interactions))

                connected = room_info.get("connected_rooms", [])
                if connected:
                    st.markdown("**Connected Rooms:** " + " → ".join(connected))

# ===========================================================================
# TAB D — Memory View
# ===========================================================================

with tab_memory:
    st.header("Memory View")

    if not agents_data:
        st.info("No agent data found.")
    else:
        for agent_name, agent in agents_data.items():
            st.subheader(f"🤖 {agent_name}")

            # Episodic memories (most recent first)
            episodic = agent.get("episodic_memory", [])
            with st.expander(f"Episodic Memories ({len(episodic)} total — showing last 10)", expanded=False):
                if episodic:
                    recent_ep = episodic[-10:][::-1]
                    for mem in recent_ep:
                        turn_label = f"T{mem.get('turn', '?')}"
                        st.markdown(
                            f"**{turn_label}** `{mem.get('room', '')}` — "
                            f"{mem.get('summary', '')}  \n"
                            f"*Resonance:* `{mem.get('emotional_resonance', '')}` · "
                            f"*Salience:* {mem.get('salience', 0):.2f} · "
                            f"*Importance:* {mem.get('importance', 0):.2f}"
                            + (" *(compressed)*" if mem.get("compressed") else "")
                        )
                        st.divider()
                else:
                    st.info("No episodic memories recorded.")

            # Relational memories
            relational = agent.get("relational_memory", {})
            with st.expander(f"Relational Memories ({len(relational)} relationships)", expanded=False):
                if relational:
                    for human_name, rel in relational.items():
                        st.markdown(f"**{human_name}**")
                        st.markdown(
                            f"- Interactions: {rel.get('interaction_count', 0)}  "
                            f"| Trust: {rel.get('trust_level', 0):.2f}  "
                            f"| Last seen turn: {rel.get('last_seen_turn', '—')}"
                        )
                        notes = rel.get("notes", [])
                        if notes:
                            st.markdown("*Recent notes:*")
                            for note in notes[-3:]:
                                st.markdown(f"> {note}")
                        st.divider()
                else:
                    st.info("No relational memories recorded.")

            # Reflections
            reflections = agent.get("reflection_entries", [])
            with st.expander(f"Reflection Entries ({len(reflections)} total)", expanded=False):
                if reflections:
                    for ref in reversed(reflections):
                        st.markdown(f"**Turn {ref.get('turn', '?')} — Trigger:** `{ref.get('trigger', '')}`")
                        for field in (
                            "what_happened",
                            "what_mattered",
                            "what_conflicted",
                            "what_changed",
                            "future_adjustment",
                        ):
                            val = ref.get(field)
                            if val:
                                st.markdown(f"- **{field.replace('_', ' ').title()}:** {val}")
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
        # Summary metrics
        st.subheader("Summary")

        coop_count = sum(1 for r in interaction_log if r.get("outcome") == "cooperated")
        conflict_count = sum(1 for r in interaction_log if r.get("outcome") in ("deferred", "conflict", "resolved"))
        total_interactions = len(interaction_log)

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Interactions", total_interactions)
        col2.metric("Cooperative", coop_count)
        col3.metric("Conflict / Deferred", conflict_count)

        # Latest conflict point
        conflict_points = [r.get("conflict_point", "") for r in interaction_log if r.get("conflict_point")]
        if conflict_points:
            st.markdown(f"**Latest Conflict Point:** {conflict_points[-1]}")

        st.divider()

        # Agent relationship table
        st.subheader("Agent Relationships")
        if agent_relationships:
            display_rows = []
            for row in agent_relationships:
                display_rows.append(
                    {
                        "Observer": row.get("observer", ""),
                        "Subject": row.get("subject", ""),
                        "Trust": row.get("trust", ""),
                        "Reliability": row.get("perceived_reliability", ""),
                        "Conflicts": row.get("conflict_count", ""),
                        "Cooperations": row.get("cooperation_count", ""),
                        "Last Interaction Turn": row.get("last_interaction_turn", ""),
                    }
                )
            st.table(display_rows)

        st.divider()

        # Full interaction log
        st.subheader("Interaction Log (most recent first)")
        if interaction_log:
            for row in reversed(interaction_log):
                outcome = row.get("outcome", "")
                badge = (
                    "🟢" if outcome == "cooperated" else ("🔴" if outcome in ("deferred", "conflict") else "🟡")
                )
                with st.expander(
                    f"{badge} Turn {row.get('turn', '?')} · {row.get('interaction_type', '')} "
                    f"({row.get('initiator', '')} ↔ {row.get('respondent', '')})",
                    expanded=False,
                ):
                    col_a, col_b = st.columns(2)
                    col_a.markdown(f"**Room:** {row.get('room', '—')}")
                    col_b.markdown(f"**Outcome:** `{outcome}`")

                    col_c, col_d = st.columns(2)
                    col_c.markdown(
                        f"**{row.get('initiator', '')} dominant value:** `{row.get('initiator_dominant_value', '—')}`"
                    )
                    col_d.markdown(
                        f"**{row.get('respondent', '')} dominant value:** `{row.get('respondent_dominant_value', '—')}`"
                    )

                    trust_i = row.get("trust_delta_i_to_r", "")
                    trust_r = row.get("trust_delta_r_to_i", "")
                    if trust_i or trust_r:
                        st.markdown(
                            f"**Trust delta:** {row.get('initiator', '')} → {row.get('respondent', '')}: `{trust_i}` | "
                            f"{row.get('respondent', '')} → {row.get('initiator', '')}: `{trust_r}`"
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
    st.caption("Generated by `plot_state.py`. Re-run it to refresh the images after a new simulation.")

    available_plots = {title: path for title, path in PLOTS.items() if path.exists()}
    missing_plots = [title for title, path in PLOTS.items() if not path.exists()]

    if missing_plots:
        st.warning(
            "Some plots are missing. Run `python plot_state.py` to generate them:\n"
            + "\n".join(f"- {t}" for t in missing_plots)
        )

    if not available_plots:
        st.info("No plots available yet. Run `python plot_state.py` first.")
    else:
        # Show plots in a 2-column grid
        plot_items = list(available_plots.items())
        for i in range(0, len(plot_items), 2):
            row_cols = st.columns(2)
            for col, (title, path) in zip(row_cols, plot_items[i : i + 2]):
                with col:
                    st.subheader(title)
                    st.image(str(path), use_container_width=True)

# ---------------------------------------------------------------------------
# Auto-refresh (must be last to avoid interfering with tab rendering)
# ---------------------------------------------------------------------------

if auto_refresh:
    st.sidebar.success("Auto-refresh active — reloading in 10 s…")
    time.sleep(10)
    st.cache_data.clear()
    st.rerun()
