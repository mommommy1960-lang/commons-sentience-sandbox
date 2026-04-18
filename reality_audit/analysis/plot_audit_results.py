"""Visualisation utilities for Reality Audit logs.

Generates four standard plots from a completed audit run:

1. ``metric_timeline.png``     — selected metric values across turns for one
                                 sample run (from ``raw_log.json``).
2. ``scenario_comparison.png`` — bar chart comparing all metrics across
                                 the four toy scenarios.
3. ``baseline_vs_scenarios.png`` — comparison of random-walk and
                                 uniform-policy baselines against the four
                                 audit scenarios on key metrics.
4. ``probe_mode_comparison.png`` — side-by-side bars of passive vs
                                 active_measurement_model (if both are
                                 available in the supplied summary dicts).

All plots are saved to ``<output_dir>/figures/``.

Usage
-----
    from reality_audit.analysis.plot_audit_results import generate_all_plots
    generate_all_plots(output_dir="commons_sentience_sim/output")

Or from the command line:
    python -m reality_audit.analysis.plot_audit_results
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib
matplotlib.use("Agg")  # non-interactive backend — safe in all environments
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_KEY_METRICS = [
    "position_error",
    "stability_score",
    "avg_control_effort",
    "path_smoothness",
    "observer_dependence_score",
    "audit_bandwidth",
    "mean_position_error",
]

# Toy-scenario metric keys as produced by ExperimentRunner (not SimProbe)
_TOY_KEY_METRICS = [
    "position_error",
    "stability_score",
    "anisotropy_score",
    "bandwidth_bottleneck_score",
    "observer_dependence_score",
    "quantization_artifact_score",
]


def _load_json(path: Path) -> Optional[Dict]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


# ---------------------------------------------------------------------------
# Plot 1: metric timeline from raw_log.json
# ---------------------------------------------------------------------------

def plot_metric_timeline(
    raw_log: List[Dict[str, Any]],
    agent_name: str,
    figures_dir: Path,
) -> Path:
    """Plot per-turn position_error and control_effort for one agent."""
    records = [r for r in raw_log if r.get("agent_name") == agent_name]
    if not records:
        records = raw_log  # fallback: use all records

    turns = [r["step"] for r in records]
    pos_errors = [r.get("position_error", 0.0) for r in records]
    control_efforts = [r.get("control_effort", 0.0) for r in records]

    fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    fig.suptitle(f"Metric Timeline — {agent_name}", fontsize=13)

    axes[0].plot(turns, pos_errors, color="#2196F3", linewidth=1.5, label="position_error")
    axes[0].set_ylabel("Position Error")
    axes[0].legend(loc="upper right", fontsize=9)
    axes[0].grid(True, alpha=0.35)

    axes[1].bar(turns, control_efforts, color="#FF9800", alpha=0.8, label="control_effort")
    axes[1].set_ylabel("Action Blocked (0/1)")
    axes[1].set_xlabel("Turn")
    axes[1].set_ylim(-0.1, 1.3)
    axes[1].legend(loc="upper right", fontsize=9)
    axes[1].grid(True, alpha=0.35)

    plt.tight_layout()
    out = figures_dir / "metric_timeline.png"
    fig.savefig(out, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return out


# ---------------------------------------------------------------------------
# Plot 2: scenario comparison bar chart
# ---------------------------------------------------------------------------

def plot_scenario_comparison(
    scenario_metrics: Dict[str, Dict[str, Any]],
    figures_dir: Path,
    metric_keys: Optional[List[str]] = None,
) -> Path:
    """Bar chart comparing metric values across multiple scenarios."""
    if metric_keys is None:
        metric_keys = _TOY_KEY_METRICS

    # Filter to keys that exist in at least one scenario
    available_keys = [
        k for k in metric_keys
        if any(k in m for m in scenario_metrics.values())
    ]

    n_scenarios = len(scenario_metrics)
    n_metrics = len(available_keys)
    if n_scenarios == 0 or n_metrics == 0:
        return figures_dir / "scenario_comparison_empty.png"

    scenario_names = list(scenario_metrics.keys())
    x = np.arange(n_metrics)
    width = 0.8 / n_scenarios
    colors = ["#2196F3", "#4CAF50", "#FF9800", "#9C27B0", "#F44336"]

    fig, ax = plt.subplots(figsize=(max(10, n_metrics * 1.5), 6))
    for i, name in enumerate(scenario_names):
        values = [scenario_metrics[name].get(k, 0.0) for k in available_keys]
        offset = (i - n_scenarios / 2 + 0.5) * width
        ax.bar(x + offset, values, width * 0.9, label=name, color=colors[i % len(colors)], alpha=0.85)

    ax.set_xticks(x)
    ax.set_xticklabels(available_keys, rotation=30, ha="right", fontsize=9)
    ax.set_ylabel("Metric value")
    ax.set_title("Scenario Comparison — Key Metrics")
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(True, axis="y", alpha=0.35)
    plt.tight_layout()

    out = figures_dir / "scenario_comparison.png"
    fig.savefig(out, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return out


# ---------------------------------------------------------------------------
# Plot 3: baseline vs scenarios
# ---------------------------------------------------------------------------

def plot_baseline_vs_scenarios(
    baseline_metrics: Dict[str, Dict[str, Any]],
    scenario_metrics: Dict[str, Dict[str, Any]],
    figures_dir: Path,
) -> Path:
    """Compare baselines vs scenarios on a small set of key metrics."""
    comparison_keys = [
        "position_error",
        "stability_score",
        "convergence_time",
        "bandwidth_bottleneck_score",
    ]
    all_entries = {**{f"[baseline] {k}": v for k, v in baseline_metrics.items()},
                   **scenario_metrics}

    available_keys = [
        k for k in comparison_keys
        if any(k in m for m in all_entries.values())
    ]

    names = list(all_entries.keys())
    x = np.arange(len(available_keys))
    width = 0.8 / len(names)
    colors = plt.cm.tab10(np.linspace(0, 0.9, len(names)))  # type: ignore[attr-defined]

    fig, ax = plt.subplots(figsize=(max(10, len(available_keys) * 2), 6))
    for i, name in enumerate(names):
        values = [all_entries[name].get(k, 0.0) for k in available_keys]
        offset = (i - len(names) / 2 + 0.5) * width
        ax.bar(x + offset, values, width * 0.9, label=name, color=colors[i], alpha=0.85)

    ax.set_xticks(x)
    ax.set_xticklabels(available_keys, rotation=20, ha="right", fontsize=10)
    ax.set_ylabel("Metric value")
    ax.set_title("Baseline vs Scenarios — Key Metrics")
    ax.legend(loc="upper right", fontsize=8, ncol=2)
    ax.grid(True, axis="y", alpha=0.35)
    plt.tight_layout()

    out = figures_dir / "baseline_vs_scenarios.png"
    fig.savefig(out, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return out


# ---------------------------------------------------------------------------
# Plot 4: probe-mode comparison
# ---------------------------------------------------------------------------

def plot_probe_mode_comparison(
    summaries: Dict[str, Dict[str, Any]],
    figures_dir: Path,
) -> Path:
    """Compare probe-off / passive / active_measurement_model summaries."""
    metric_keys = [
        "mean_position_error",
        "stability_score",
        "avg_control_effort",
        "observer_dependence_score",
        "audit_bandwidth",
    ]
    available_keys = [
        k for k in metric_keys
        if any(k in s for s in summaries.values())
    ]

    names = list(summaries.keys())
    x = np.arange(len(available_keys))
    width = 0.8 / max(len(names), 1)
    colors = ["#2196F3", "#4CAF50", "#FF9800"]

    fig, ax = plt.subplots(figsize=(max(8, len(available_keys) * 1.8), 5))
    for i, name in enumerate(names):
        values = [summaries[name].get(k, 0.0) for k in available_keys]
        offset = (i - len(names) / 2 + 0.5) * width
        ax.bar(x + offset, values, width * 0.9, label=name, color=colors[i % 3], alpha=0.85)

    ax.set_xticks(x)
    ax.set_xticklabels(available_keys, rotation=20, ha="right", fontsize=10)
    ax.set_ylabel("Metric value")
    ax.set_title("Probe Mode Comparison")
    ax.legend(fontsize=9)
    ax.grid(True, axis="y", alpha=0.35)
    plt.tight_layout()

    out = figures_dir / "probe_mode_comparison.png"
    fig.savefig(out, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return out


# ---------------------------------------------------------------------------
# Public top-level entry point
# ---------------------------------------------------------------------------

def generate_all_plots(
    output_dir: str | Path = "commons_sentience_sim/output",
    verbose: bool = False,
) -> List[Path]:
    """Generate all four standard plots from whatever data is available.

    If a data source is missing the corresponding plot is silently skipped.
    Returns a list of the PNG paths that were actually written.
    """
    output_dir = Path(output_dir)
    audit_dir = output_dir / "reality_audit"
    figures_dir = _ensure_dir(audit_dir / "figures")
    generated: List[Path] = []

    # ── Plot 1: metric timeline ──────────────────────────────────────────
    raw_log = _load_json(audit_dir / "raw_log.json")
    if raw_log:
        # Use the first agent name found
        agent_names = list({r.get("agent_name", "Agent") for r in raw_log})
        agent_names.sort()
        p = plot_metric_timeline(raw_log, agent_names[0], figures_dir)
        generated.append(p)
        if verbose:
            print(f"  ✓ metric_timeline.png → {p}")

    # ── Plot 2: scenario comparison ──────────────────────────────────────
    # Load toy experiment summaries if available
    toy_dir = Path("outputs/toy_experiments")
    toy_summaries: Dict[str, Dict] = {}
    label_map = {
        "toy_continuous_baseline": "A_baseline",
        "toy_anisotropic_preferred_axis": "B_anisotropy",
        "toy_observer_triggered_updates": "C_observer_divergence",
        "toy_bandwidth_limited": "D_bandwidth_staleness",
    }
    for folder_name, label in label_map.items():
        summary_path = toy_dir / folder_name / "summary.json"
        data = _load_json(summary_path)
        if data:
            # The toy runner writes a summary with a "results" list
            if "results" in data:
                first = data["results"][0] if data["results"] else {}
                toy_summaries[label] = first.get("metrics", {})
            else:
                toy_summaries[label] = data

    if len(toy_summaries) >= 2:
        p = plot_scenario_comparison(toy_summaries, figures_dir)
        generated.append(p)
        if verbose:
            print(f"  ✓ scenario_comparison.png → {p}")

    # ── Plot 3: baseline vs scenarios ────────────────────────────────────
    baseline_dir = Path("outputs/baselines")
    baseline_summaries: Dict[str, Dict] = {}
    for bname in ["random_walk", "uniform_policy"]:
        bpath = baseline_dir / f"baseline_{bname}_summary.json"
        data = _load_json(bpath)
        if data:
            baseline_summaries[bname] = data

    if baseline_summaries and toy_summaries:
        p = plot_baseline_vs_scenarios(baseline_summaries, toy_summaries, figures_dir)
        generated.append(p)
        if verbose:
            print(f"  ✓ baseline_vs_scenarios.png → {p}")

    # ── Plot 4: probe mode comparison ────────────────────────────────────
    # Look for summary.json in reality_audit/; use probe_mode as key
    summary = _load_json(audit_dir / "summary.json")
    if summary:
        mode_label = summary.get("probe_mode", "passive")
        mode_summaries = {mode_label: summary}
        if len(mode_summaries) >= 1:
            p = plot_probe_mode_comparison(mode_summaries, figures_dir)
            generated.append(p)
            if verbose:
                print(f"  ✓ probe_mode_comparison.png → {p}")

    return generated


if __name__ == "__main__":
    paths = generate_all_plots(verbose=True)
    if not paths:
        print("No data found to plot. Run some experiments first.")
    else:
        print(f"\nGenerated {len(paths)} figure(s):")
        for p in paths:
            print(f"  {p}")
