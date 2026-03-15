"""
plot_state.py — Visualisation script for Commons Sentience Sandbox v0.3.

Reads state_history.csv produced by run_sim.py and generates three plots:
  - trust over time
  - urgency over time
  - contradiction_pressure over time

Saves PNG files into the output folder.

Usage:
    python plot_state.py

Requires: matplotlib (pip install matplotlib)
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Matplotlib backend — use non-interactive 'Agg' to avoid display issues
# ---------------------------------------------------------------------------
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent / "commons_sentience_sim"
OUTPUT_DIR = BASE_DIR / "output"
STATE_HISTORY_PATH = OUTPUT_DIR / "state_history.csv"


def load_state_history(path: Path) -> dict:
    """Return a dict mapping column name → list of values."""
    if not path.exists():
        print(f"ERROR: state_history.csv not found at {path}")
        print("Run `python run_sim.py` first to generate the data.")
        sys.exit(1)

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
    """Return {turn_index: event_type} for turns that have non-task events."""
    markers = {}
    event_types = columns.get("event_type", [])
    for i, (t, et) in enumerate(zip(turns, event_types)):
        if et and et not in ("task", ""):
            markers[i] = et.replace("_", " ")
    return markers


def _annotate_events(ax, turns: list, markers: dict, y_values: list, color: str) -> None:
    """Add small vertical annotations for notable events."""
    for idx, label in markers.items():
        if idx < len(y_values):
            ax.annotate(
                label,
                xy=(turns[idx], y_values[idx]),
                xytext=(turns[idx], y_values[idx] + 0.08),
                fontsize=5.5,
                color=color,
                rotation=35,
                ha="left",
                arrowprops=dict(arrowstyle="-", color=color, lw=0.5),
            )


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

    # Mark event turns
    event_turns = [turns[i] for i in markers]
    event_vals = [values[i] for i in markers if i < len(values)]
    ax.scatter(event_turns, event_vals, color=color, s=60, zorder=5, edgecolors="white", linewidths=0.8)
    _annotate_events(ax, turns, markers, values, color)

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


def main() -> None:
    print("=" * 50)
    print("  Commons Sentience Sandbox — State Plotter")
    print("=" * 50)

    columns = load_state_history(STATE_HISTORY_PATH)
    turns = _ints(columns, "turn")
    trust = _floats(columns, "trust")
    urgency = _floats(columns, "urgency")
    contradiction = _floats(columns, "contradiction_pressure")
    markers = _event_markers(columns, turns)

    plot_metric(
        turns, trust, markers,
        title="Agent Trust Over Time",
        ylabel="Trust (0–1)",
        color="#2196F3",
        output_path=OUTPUT_DIR / "trust_plot.png",
    )

    plot_metric(
        turns, urgency, markers,
        title="Agent Urgency Over Time",
        ylabel="Urgency (0–1)",
        color="#FF5722",
        output_path=OUTPUT_DIR / "urgency_plot.png",
    )

    plot_metric(
        turns, contradiction, markers,
        title="Contradiction Pressure Over Time",
        ylabel="Contradiction Pressure (0–1)",
        color="#9C27B0",
        output_path=OUTPUT_DIR / "contradiction_plot.png",
    )

    print("\nAll plots saved to:", OUTPUT_DIR)


if __name__ == "__main__":
    main()
