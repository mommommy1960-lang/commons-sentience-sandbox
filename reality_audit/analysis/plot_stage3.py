"""Stage 3 visualization extensions.

Extends the Stage 2 plot_audit_results.py with four new plot types:

1. ``plot_long_run_metric_timeline``   — metric trajectory for a single long-run
2. ``plot_mean_variance_across_seeds`` — mean + shaded variance bands across seeds
3. ``plot_baseline_vs_real_agents``    — baseline vs real-agent comparison bar chart
4. ``plot_false_positive_detection``   — threshold check visualization

All figures are saved to:
  <output_dir>/reality_audit/figures_stage3/

Backend: matplotlib Agg (no display required).
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional

# Use Agg backend — no display required
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

_DEFAULT_OUTPUT_DIR = (
    Path(__file__).resolve().parents[2]
    / "commons_sentience_sim"
    / "output"
    / "reality_audit"
    / "figures_stage3"
)

_FIGURE_SIZE = (10, 5)
_MULTI_FIG_SIZE = (12, 6)
_DPI = 100

# Metrics shown in multi-metric plots
_DISPLAY_METRICS = [
    "position_error",
    "stability_score",
    "anisotropy_score",
    "observer_dependence_score",
    "bandwidth_bottleneck_score",
    "quantization_artifact_score",
]


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _ensure_dir(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _safe(v: Any) -> float:
    try:
        f = float(v)
        return 0.0 if math.isnan(f) else f
    except (TypeError, ValueError):
        return 0.0


# ---------------------------------------------------------------------------
# 1. Long-run metric timeline
# ---------------------------------------------------------------------------

def plot_long_run_metric_timeline(
    raw_log: List[Dict[str, Any]],
    metrics_of_interest: Optional[List[str]] = None,
    title: str = "Long-Run Metric Timeline",
    output_dir: Optional[Path] = None,
    filename: str = "long_run_metric_timeline.png",
) -> Path:
    """Plot per-step metric values over a long run.

    ``raw_log`` is expected to be the standard raw_log list from
    ``ExperimentRunner``, with each entry containing ``time``,
    ``position``, ``measured_position``, etc.

    We derive simple scalar metrics per step:
    - ``position_tracking_error``: distance(position, measured_position)
    - ``velocity_tracking_error``: distance(velocity, measured_velocity)
    - ``observed``: 1 if step was observed, 0 if not
    """
    output_dir = _ensure_dir(output_dir or _DEFAULT_OUTPUT_DIR)

    times = [entry["time"] for entry in raw_log]

    def _dist(a: Any, b: Any) -> float:
        try:
            return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)
        except Exception:
            return 0.0

    pos_errs = [_dist(e["position"], e["measured_position"]) for e in raw_log]
    vel_errs = [_dist(e["velocity"], e["measured_velocity"]) for e in raw_log]
    observed = [1.0 if e.get("observed", True) else 0.0 for e in raw_log]

    fig, axes = plt.subplots(3, 1, figsize=(12, 8), sharex=True)
    fig.suptitle(title, fontsize=13)

    axes[0].plot(times, pos_errs, color="#2196F3", linewidth=1.2, label="pos tracking error")
    axes[0].set_ylabel("Position Error")
    axes[0].legend(fontsize=8)
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(times, vel_errs, color="#FF9800", linewidth=1.2, label="vel tracking error")
    axes[1].set_ylabel("Velocity Error")
    axes[1].legend(fontsize=8)
    axes[1].grid(True, alpha=0.3)

    axes[2].fill_between(times, observed, step="pre", alpha=0.5, color="#4CAF50", label="observed")
    axes[2].set_ylabel("Observed Flag")
    axes[2].set_xlabel("Time (s)")
    axes[2].set_ylim(-0.1, 1.5)
    axes[2].legend(fontsize=8)
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    out_path = output_dir / filename
    fig.savefig(out_path, dpi=_DPI)
    plt.close(fig)
    return out_path


# ---------------------------------------------------------------------------
# 2. Mean + variance across seeds
# ---------------------------------------------------------------------------

def plot_mean_variance_across_seeds(
    aggregated_by_scenario: Dict[str, Dict[str, Any]],
    metric: str = "stability_score",
    title: Optional[str] = None,
    output_dir: Optional[Path] = None,
    filename: str = "mean_variance_across_seeds.png",
) -> Path:
    """Bar chart with error bars showing mean ± std across seeds per scenario.

    ``aggregated_by_scenario`` maps scenario_name → aggregated_summary dict
    (as returned by ``aggregate_runs``).
    """
    output_dir = _ensure_dir(output_dir or _DEFAULT_OUTPUT_DIR)
    title = title or f"Mean ± Std: {metric}"

    scenarios = list(aggregated_by_scenario.keys())
    means = []
    stds = []
    for sc in scenarios:
        m = aggregated_by_scenario[sc].get("metrics", {}).get(metric, {})
        means.append(_safe(m.get("mean")))
        stds.append(_safe(m.get("std")))

    x = np.arange(len(scenarios))
    fig, ax = plt.subplots(figsize=_MULTI_FIG_SIZE)
    bars = ax.bar(x, means, yerr=stds, capsize=5, color="#2196F3", alpha=0.75,
                  error_kw={"elinewidth": 1.5, "ecolor": "#1565C0"})
    ax.set_xticks(x)
    ax.set_xticklabels(scenarios, rotation=25, ha="right", fontsize=9)
    ax.set_ylabel(metric)
    ax.set_title(title)
    ax.grid(True, axis="y", alpha=0.3)

    # Annotate each bar with n
    for bar, sc in zip(bars, scenarios):
        n = aggregated_by_scenario[sc].get("metrics", {}).get(metric, {}).get("n", "?")
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(stds) * 0.05 + 0.001,
            f"n={n}",
            ha="center", va="bottom", fontsize=7,
        )

    plt.tight_layout()
    out_path = output_dir / filename
    fig.savefig(out_path, dpi=_DPI)
    plt.close(fig)
    return out_path


# ---------------------------------------------------------------------------
# 3. Baseline vs real-agent comparison
# ---------------------------------------------------------------------------

def plot_baseline_vs_real_agents(
    baseline_results: Dict[str, List[Dict[str, Any]]],
    real_agent_results: Dict[str, List[Dict[str, Any]]],
    metrics: Optional[List[str]] = None,
    output_dir: Optional[Path] = None,
    filename: str = "stage3_baseline_vs_real.png",
) -> Path:
    """Side-by-side bar chart comparing baselines and real-agent scenarios.

    Parameters
    ----------
    baseline_results : dict {label: list of run dicts}
    real_agent_results : dict {label: list of run dicts}
    metrics : list of metric names to plot (default: _DISPLAY_METRICS[:4])
    """
    output_dir = _ensure_dir(output_dir or _DEFAULT_OUTPUT_DIR)
    metrics = metrics or _DISPLAY_METRICS[:4]

    from reality_audit.analysis.aggregate_experiments import aggregate_runs

    def _extract_means(results_dict: Dict[str, List]) -> Dict[str, Dict[str, float]]:
        out: Dict[str, Dict[str, float]] = {}
        for label, runs in results_dict.items():
            agg = aggregate_runs(runs, experiment_name=label)
            out[label] = {m: _safe(agg["metrics"].get(m, {}).get("mean")) for m in metrics}
        return out

    baseline_means = _extract_means(baseline_results)
    real_means = _extract_means(real_agent_results)

    all_labels = list(baseline_means) + list(real_means)
    n_labels = len(all_labels)
    n_metrics = len(metrics)
    x = np.arange(n_metrics)
    width = 0.8 / n_labels

    fig, ax = plt.subplots(figsize=(max(10, n_metrics * 2), 6))
    colors_b = plt.cm.Blues(np.linspace(0.4, 0.8, len(baseline_means)))
    colors_r = plt.cm.Oranges(np.linspace(0.4, 0.8, len(real_means)))

    offsets = np.linspace(-(n_labels - 1) * width / 2, (n_labels - 1) * width / 2, n_labels)
    for i, (label, color) in enumerate(
        list(zip(baseline_means, colors_b)) + list(zip(real_means, colors_r))
    ):
        means_dict = baseline_means.get(label) or real_means.get(label, {})
        vals = [means_dict.get(m, 0.0) for m in metrics]
        is_baseline = label in baseline_means
        hatch = "//" if is_baseline else ""
        ax.bar(x + offsets[i], vals, width * 0.9, label=label, color=color,
               hatch=hatch, alpha=0.85)

    ax.set_xticks(x)
    ax.set_xticklabels(metrics, rotation=25, ha="right", fontsize=9)
    ax.set_title("Baseline vs Real-Agent Metric Comparison")
    ax.set_ylabel("Metric Value")
    ax.legend(fontsize=8, bbox_to_anchor=(1.01, 1), loc="upper left")
    ax.grid(True, axis="y", alpha=0.3)

    plt.tight_layout()
    out_path = output_dir / filename
    fig.savefig(out_path, dpi=_DPI)
    plt.close(fig)
    return out_path


# ---------------------------------------------------------------------------
# 4. False-positive detection plot
# ---------------------------------------------------------------------------

def plot_false_positive_detection(
    fp_report: Dict[str, Any],
    output_dir: Optional[Path] = None,
    filename: str = "false_positive_detection.png",
) -> Path:
    """Horizontal bar chart showing metric values vs their FP thresholds."""
    output_dir = _ensure_dir(output_dir or _DEFAULT_OUTPUT_DIR)

    checks = fp_report.get("threshold_checks", {})
    if not checks:
        raise ValueError("fp_report must contain 'threshold_checks'")

    metrics = list(checks.keys())
    values = []
    thresholds = []
    colors = []
    for m in metrics:
        c = checks[m]
        key = "mean_value" if "mean_value" in c else "max_value"
        values.append(_safe(c.get(key)))
        thresholds.append(_safe(c.get("threshold")))
        colors.append("#4CAF50" if c.get("passed", False) else "#F44336")

    y = np.arange(len(metrics))
    fig, ax = plt.subplots(figsize=(9, max(4, len(metrics) * 1.2)))

    bars = ax.barh(y, values, color=colors, alpha=0.8, label="actual value")
    ax.scatter(thresholds, y, marker="|", s=500, color="#212121",
               linewidths=2, label="threshold", zorder=5)

    ax.set_yticks(y)
    ax.set_yticklabels(metrics, fontsize=9)
    ax.set_xlabel("Metric Value")
    ax.set_title("False-Positive Detection: Actual vs Threshold")
    ax.legend(fontsize=9)
    ax.grid(True, axis="x", alpha=0.3)

    # Legend patches
    pass_patch = mpatches.Patch(color="#4CAF50", alpha=0.8, label="pass")
    fail_patch = mpatches.Patch(color="#F44336", alpha=0.8, label="fail (FP risk)")
    ax.legend(handles=[pass_patch, fail_patch], fontsize=9)

    plt.tight_layout()
    out_path = output_dir / filename
    fig.savefig(out_path, dpi=_DPI)
    plt.close(fig)
    return out_path


# ---------------------------------------------------------------------------
# Top-level: generate all Stage 3 figures
# ---------------------------------------------------------------------------

def generate_stage3_plots(
    long_run_results: Optional[Dict[str, Any]] = None,
    aggregated_by_scenario: Optional[Dict[str, Dict[str, Any]]] = None,
    fp_report: Optional[Dict[str, Any]] = None,
    output_dir: Optional[Path] = None,
    verbose: bool = False,
) -> List[Path]:
    """Generate all Stage 3 figures from available data.

    Parameters
    ----------
    long_run_results : {scenario: {n_turns: [run_results]}} (from long_horizon_runs)
    aggregated_by_scenario : {scenario: aggregated_summary}
    fp_report : false_positive_report dict
    output_dir : target directory (default: figures_stage3/)

    Returns
    -------
    list of Path
        Paths to all generated figures.
    """
    from reality_audit.analysis.aggregate_experiments import aggregate_runs

    out_dir = Path(output_dir or _DEFAULT_OUTPUT_DIR)
    figures: List[Path] = []

    # Plot 2: mean + variance per metric for each scenario (if available)
    if aggregated_by_scenario:
        for metric in ["stability_score", "anisotropy_score", "position_error"]:
            fig_path = plot_mean_variance_across_seeds(
                aggregated_by_scenario=aggregated_by_scenario,
                metric=metric,
                output_dir=out_dir,
                filename=f"mean_variance_{metric}.png",
            )
            figures.append(fig_path)
            if verbose:
                print(f"  Saved: {fig_path.name}")

    # Plot 3: Baseline vs real agents (if long_run_results available)
    if long_run_results:
        baseline_scenarios = {
            k: v for k, v in long_run_results.items()
            if k in ("random_baseline_agent",)
        }
        real_scenarios = {
            k: v for k, v in long_run_results.items()
            if k in ("baseline", "anisotropy", "observer_divergence", "bandwidth_limited")
        }
        # Flatten turn-count runs into single list per scenario
        def _flatten(scenario_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
            flat = []
            for runs_by_turn in scenario_dict.values():
                if isinstance(runs_by_turn, list):
                    flat.extend(runs_by_turn)
                elif isinstance(runs_by_turn, dict):
                    for v in runs_by_turn.values():
                        if isinstance(v, list):
                            flat.extend(v)
            return flat

        b_flat = {k: _flatten(v) for k, v in baseline_scenarios.items()}
        r_flat = {k: _flatten(v) for k, v in real_scenarios.items()}
        if b_flat and r_flat:
            fig_path = plot_baseline_vs_real_agents(
                baseline_results=b_flat,
                real_agent_results=r_flat,
                output_dir=out_dir,
            )
            figures.append(fig_path)
            if verbose:
                print(f"  Saved: {fig_path.name}")

    # Plot 4: False-positive detection
    if fp_report:
        fig_path = plot_false_positive_detection(
            fp_report=fp_report,
            output_dir=out_dir,
        )
        figures.append(fig_path)
        if verbose:
            print(f"  Saved: {fig_path.name}")

    return figures
