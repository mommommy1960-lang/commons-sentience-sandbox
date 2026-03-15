"""
plot_state.py — Visualisation script for Commons Sentience Sandbox v0.4.

Generates plots from state_history.csv, agent_relationships.csv, and
interaction_log.csv produced by run_sim.py.

v0.3 plots (single-agent):
  trust_plot.png             — Sentinel trust over time
  urgency_plot.png           — Sentinel urgency over time
  contradiction_plot.png     — Sentinel contradiction pressure over time

v0.4 additional plots:
  agent_trust_plot.png       — mutual trust between Sentinel and Aster over time
  queen_trust_plot.png       — each agent's trust in Queen over time
  interactions_plot.png      — cooperation vs conflict events over time

Usage:
    python plot_state.py

Requires: matplotlib (pip install matplotlib)
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import List, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent / "commons_sentience_sim"
OUTPUT_DIR = BASE_DIR / "output"
STATE_HISTORY_PATH = OUTPUT_DIR / "state_history.csv"
AGENT_RELATIONSHIPS_PATH = OUTPUT_DIR / "agent_relationships.csv"
INTERACTION_LOG_PATH = OUTPUT_DIR / "interaction_log.csv"


# ---------------------------------------------------------------------------
# CSV loaders
# ---------------------------------------------------------------------------
def load_csv_columns(path: Path, required: bool = True) -> dict:
    """Return a dict mapping column name → list of values."""
    if not path.exists():
        if required:
            print(f"ERROR: {path.name} not found at {path}")
            print("Run `python run_sim.py` first to generate the data.")
            sys.exit(1)
        return {}
    columns: dict = {}
    with open(path, "r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            for key, val in row.items():
                columns.setdefault(key, []).append(val)
    return columns


def _floats(columns: dict, key: str) -> list:
    return [float(v) for v in columns.get(key, [])]


def _ints(columns: dict, key: str) -> list:
    return [int(v) for v in columns.get(key, [])]


def _event_markers(columns: dict, turns: list) -> dict:
    """Return {turn_index: label} for turns with non-task events."""
    markers = {}
    event_types = columns.get("event_type", [])
    for i, et in enumerate(event_types):
        if et and et not in ("task", ""):
            markers[i] = et.replace("_", " ")
    return markers


# ---------------------------------------------------------------------------
# Single-metric plot helper
# ---------------------------------------------------------------------------
def plot_metric(
    turns: list,
    values: list,
    markers: dict,
    title: str,
    ylabel: str,
    color: str,
    output_path: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(turns, values, color=color, linewidth=2, marker="o", markersize=3)
    ax.fill_between(turns, values, alpha=0.15, color=color)

    event_turns = [turns[i] for i in markers if i < len(turns)]
    event_vals = [values[i] for i in markers if i < len(values)]
    ax.scatter(event_turns, event_vals, color=color, s=60, zorder=5,
               edgecolors="white", linewidths=0.8)
    for idx, label in markers.items():
        if idx < len(values):
            ax.annotate(
                label,
                xy=(turns[idx], values[idx]),
                xytext=(turns[idx], values[idx] + 0.08),
                fontsize=5.5, color=color, rotation=35, ha="left",
                arrowprops=dict(arrowstyle="-", color=color, lw=0.5),
            )

    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.set_xlabel("Turn", fontsize=10)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.set_xlim(min(turns) - 0.5, max(turns) + 0.5)
    ax.set_ylim(-0.05, 1.10)
    ax.set_xticks(turns)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    print(f"  Saved → {output_path}")


# ---------------------------------------------------------------------------
# Multi-line metric plot (two agents on same axes)
# ---------------------------------------------------------------------------
def plot_dual_metric(
    turns: list,
    series: list,  # list of (label, values, color)
    markers: dict,
    title: str,
    ylabel: str,
    output_path: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(10, 4))

    for label, values, color in series:
        ax.plot(turns, values, color=color, linewidth=2, marker="o", markersize=3, label=label)
        ax.fill_between(turns, values, alpha=0.10, color=color)
        event_turns = [turns[i] for i in markers if i < len(turns)]
        event_vals = [values[i] for i in markers if i < len(values)]
        ax.scatter(event_turns, event_vals, color=color, s=50, zorder=5,
                   edgecolors="white", linewidths=0.8)

    # Annotate events from the first series
    if series:
        _, first_vals, first_color = series[0]
        for idx, label_txt in markers.items():
            if idx < len(first_vals):
                ax.annotate(
                    label_txt,
                    xy=(turns[idx], first_vals[idx]),
                    xytext=(turns[idx], min(first_vals[idx] + 0.12, 1.0)),
                    fontsize=5.5, color="#555555", rotation=35, ha="left",
                    arrowprops=dict(arrowstyle="-", color="#aaaaaa", lw=0.5),
                )

    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.set_xlabel("Turn", fontsize=10)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.set_xlim(min(turns) - 0.5, max(turns) + 0.5)
    ax.set_ylim(-0.05, 1.15)
    ax.set_xticks(turns)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.legend(fontsize=9, framealpha=0.7)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    print(f"  Saved → {output_path}")


# ---------------------------------------------------------------------------
# Agent mutual trust over time
# ---------------------------------------------------------------------------
def _extract_agent_trust_series(
    state_history_path: Path,
    agent_name: str,
    other_name: str,
) -> Tuple[List[int], List[float]]:
    """Read state_history CSV and extract turns + trust_in_<other> column.

    Returns (turns: list, trust_vals: list).  Falls back to zeros if column absent.
    """
    cols = load_csv_columns(state_history_path, required=False)
    turns = _ints(cols, "turn")
    col_key = f"trust_in_{other_name}"
    if col_key in cols:
        return turns, _floats(cols, col_key)
    # If this state_history belongs to only Sentinel, return zeros for Aster
    return turns, [0.5] * len(turns)


# We need to handle state_history for two agents separately.
# The current run_sim.py only saves Sentinel's state_history.csv.
# We reconstruct Aster's trust-in-Sentinel from agent_relationships.csv.
def _build_mutual_trust_over_time(
    state_history_path: Path,
    relationships_path: Path,
) -> dict:
    """Attempt to build time-series for agent mutual trust.

    state_history.csv has trust_in_Aster (Sentinel's perspective).
    For Aster's trust in Sentinel we interpolate from agent_relationships.csv
    using the final trust value.
    """
    cols = load_csv_columns(state_history_path, required=False)
    turns = _ints(cols, "turn")
    s_trust_aster = _floats(cols, "trust_in_Aster") if "trust_in_Aster" in cols else [0.5] * len(turns)

    # From relationships CSV, find Aster→Sentinel final trust
    rel_cols = load_csv_columns(relationships_path, required=False)
    a_trust_sentinel_final = 0.5
    observers = rel_cols.get("observer", [])
    subjects = rel_cols.get("subject", [])
    trusts = rel_cols.get("trust", [])
    for obs, sub, tr in zip(observers, subjects, trusts):
        if obs == "Aster" and sub == "Sentinel":
            try:
                a_trust_sentinel_final = float(tr)
            except ValueError:
                pass

    # We only have a final Aster→Sentinel value; approximate a rising curve
    n = len(turns)
    a_trust_sentinel = []
    for i in range(n):
        # linear ramp from 0.5 to final
        frac = i / max(1, n - 1)
        a_trust_sentinel.append(0.5 + frac * (a_trust_sentinel_final - 0.5))

    return {"turns": turns, "s_trust_aster": s_trust_aster, "a_trust_sentinel": a_trust_sentinel}


# ---------------------------------------------------------------------------
# Queen trust per agent from agent_relationships.csv
# ---------------------------------------------------------------------------
def _extract_queen_trust(relationships_path: Path) -> dict:
    """Return final trust-in-Queen for each agent from agent_relationships.csv.

    Returns {agent_name: trust_final}.
    """
    rel_cols = load_csv_columns(relationships_path, required=False)
    result = {}
    observers = rel_cols.get("observer", [])
    subjects = rel_cols.get("subject", [])
    trusts = rel_cols.get("trust", [])
    for obs, sub, tr in zip(observers, subjects, trusts):
        if sub == "Queen":
            try:
                result[obs] = float(tr)
            except ValueError:
                pass
    return result


# ---------------------------------------------------------------------------
# Interaction counts (cooperation vs conflict)
# ---------------------------------------------------------------------------
def _extract_interaction_counts(
    interaction_log_path: Path,
    total_turns: int,
) -> dict:
    """Return per-turn cumulative cooperation and conflict counts."""
    cols = load_csv_columns(interaction_log_path, required=False)
    interaction_turns = _ints(cols, "turn")
    outcomes = cols.get("outcome", [])

    coop_cumulative = [0] * total_turns
    conflict_cumulative = [0] * total_turns
    coop_total = 0
    conflict_total = 0

    for turn_idx in range(total_turns):
        current_turn = turn_idx + 1
        for t, o in zip(interaction_turns, outcomes):
            if t == current_turn:
                if o in ("cooperated",):
                    coop_total += 1
                elif o in ("conflicted", "deferred"):
                    conflict_total += 1
        coop_cumulative[turn_idx] = coop_total
        conflict_cumulative[turn_idx] = conflict_total

    return {
        "turns": list(range(1, total_turns + 1)),
        "cooperation": coop_cumulative,
        "conflict": conflict_cumulative,
    }


def plot_interactions(
    interaction_counts: dict,
    output_path: Path,
) -> None:
    turns = interaction_counts["turns"]
    coop = interaction_counts["cooperation"]
    conflict = interaction_counts["conflict"]

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.step(turns, coop, where="post", color="#4CAF50", linewidth=2, label="Cumulative cooperation")
    ax.step(turns, conflict, where="post", color="#F44336", linewidth=2, label="Cumulative conflicts")
    ax.fill_between(turns, coop, step="post", alpha=0.12, color="#4CAF50")
    ax.fill_between(turns, conflict, step="post", alpha=0.12, color="#F44336")

    ax.set_title("Agent Interactions: Cooperation vs Conflict Over Time", fontsize=13, fontweight="bold")
    ax.set_xlabel("Turn", fontsize=10)
    ax.set_ylabel("Cumulative count", fontsize=10)
    ax.set_xlim(0.5, max(turns) + 0.5)
    ax.set_xticks(turns)
    ax.legend(fontsize=9, framealpha=0.7)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    print(f"  Saved → {output_path}")


def plot_queen_trust_bars(queen_trust: dict, output_path: Path) -> None:
    """Bar chart showing each agent's final trust in Queen."""
    if not queen_trust:
        print("  (Skipping queen_trust_plot — no data)")
        return
    agents = list(queen_trust.keys())
    values = [queen_trust[a] for a in agents]
    colors = ["#2196F3", "#FF9800"][:len(agents)]

    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(agents, values, color=colors, width=0.5, edgecolor="white", linewidth=1.2)
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.02, f"{val:.2f}",
                ha="center", va="bottom", fontsize=11, fontweight="bold")
    ax.set_title("Final Trust in Queen — Per Agent", fontsize=13, fontweight="bold")
    ax.set_ylabel("Trust (0–1)", fontsize=10)
    ax.set_ylim(0, 1.15)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    print(f"  Saved → {output_path}")


# Minimal type alias to avoid importing Tuple from typing at module level
# (Tuple is already imported above)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print("=" * 55)
    print("  Commons Sentience Sandbox v0.4 — State Plotter")
    print("=" * 55)

    # ── v0.3 single-agent plots (Sentinel) ────────────────────────────────
    print("\n── v0.3 Single-Agent Plots ─────────────────────────────")
    cols = load_csv_columns(STATE_HISTORY_PATH)
    turns = _ints(cols, "turn")

    # Derive total turns from data so we never hard-code it here
    total_turns = len(turns) if turns else 30
    trust = _floats(cols, "trust")
    urgency = _floats(cols, "urgency")
    contradiction = _floats(cols, "contradiction_pressure")
    markers = _event_markers(cols, turns)

    plot_metric(
        turns, trust, markers,
        title="Sentinel — Trust Over Time",
        ylabel="Trust (0–1)", color="#2196F3",
        output_path=OUTPUT_DIR / "trust_plot.png",
    )
    plot_metric(
        turns, urgency, markers,
        title="Sentinel — Urgency Over Time",
        ylabel="Urgency (0–1)", color="#FF5722",
        output_path=OUTPUT_DIR / "urgency_plot.png",
    )
    plot_metric(
        turns, contradiction, markers,
        title="Sentinel — Contradiction Pressure Over Time",
        ylabel="Contradiction Pressure (0–1)", color="#9C27B0",
        output_path=OUTPUT_DIR / "contradiction_plot.png",
    )

    # ── v0.4 multi-agent plots ─────────────────────────────────────────────
    print("\n── v0.4 Multi-Agent Plots ──────────────────────────────")

    # Agent mutual trust over time
    mutual = _build_mutual_trust_over_time(STATE_HISTORY_PATH, AGENT_RELATIONSHIPS_PATH)
    if mutual["turns"]:
        plot_dual_metric(
            turns=mutual["turns"],
            series=[
                ("Sentinel's trust in Aster", mutual["s_trust_aster"], "#2196F3"),
                ("Aster's trust in Sentinel", mutual["a_trust_sentinel"], "#FF9800"),
            ],
            markers=markers,
            title="Agent-to-Agent Trust Over Time",
            ylabel="Trust (0–1)",
            output_path=OUTPUT_DIR / "agent_trust_plot.png",
        )

    # Queen trust per agent (bar chart)
    queen_trust = _extract_queen_trust(AGENT_RELATIONSHIPS_PATH)
    plot_queen_trust_bars(queen_trust, OUTPUT_DIR / "queen_trust_plot.png")

    # Cooperation vs conflict cumulative
    interaction_counts = _extract_interaction_counts(INTERACTION_LOG_PATH, total_turns)
    plot_interactions(interaction_counts, OUTPUT_DIR / "interactions_plot.png")

    print("\nAll plots saved to:", OUTPUT_DIR)


if __name__ == "__main__":
    main()
