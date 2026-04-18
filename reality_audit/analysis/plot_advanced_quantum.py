"""
plot_advanced_quantum.py — Visualisation for advanced which-path / eraser benchmark.

Figures written to <output_dir>/figures/:
  1. one_slit_distribution.png
  2. two_slit_coherent_distribution.png
  3. two_slit_which_path_distribution.png
  4. eraser_plus_distribution.png
  5. eraser_minus_distribution.png
  6. visibility_vs_distinguishability.png
  7. overlap_sweep.png
  8. hundred_run_stability.png
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.cm as cm

from reality_audit.analysis.advanced_quantum_metrics import (
    fringe_visibility,
    path_distinguishability,
    interference_visibility_corrected,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _positions_and_probs(result: Dict[str, Any]):
    return result["screen_positions"], result["probability_profile"], result["hit_counts"], result["n_trials"]


def _plot_condition(result: Dict[str, Any], title: str, path: Path) -> None:
    positions, probs, hits, n_trials = _positions_and_probs(result)
    fig, (ax_p, ax_h) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)

    ax_p.plot(positions, probs, lw=1.5, color="steelblue", label="P(y) theory")
    s_ov = result.get("detector_overlap")
    label_extra = f"s={s_ov:.2f}" if (s_ov is not None and not (isinstance(s_ov, float) and math.isnan(s_ov))) else ""
    vis = fringe_visibility(probs)
    ax_p.text(0.98, 0.95, f"V={vis:.3f}  {label_extra}",
              transform=ax_p.transAxes, ha="right", va="top", fontsize=8,
              bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.7))
    ax_p.set_ylabel("Probability")
    ax_p.set_title(title)
    ax_p.legend(fontsize=8)

    hit_probs = [h / n_trials for h in hits] if n_trials else [0.0] * len(hits)
    width = (positions[1] - positions[0]) if len(positions) > 1 else 1.0
    ax_h.bar(positions, hit_probs, width=width, color="coral", alpha=0.7, label="Sampled")
    ax_h.set_xlabel("Screen position y")
    ax_h.set_ylabel("Empirical frequency")
    ax_h.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Individual condition plots
# ---------------------------------------------------------------------------

def plot_single_condition(result: Dict[str, Any], title: str, output_path: Path) -> None:
    _plot_condition(result, title, output_path)


# ---------------------------------------------------------------------------
# Overlap sweep
# ---------------------------------------------------------------------------

def plot_overlap_sweep(
    sweep_results: List[Dict[str, Any]],
    output_path: Path,
) -> None:
    if not sweep_results:
        return
    n = len(sweep_results)
    colours = cm.plasma([i / max(n - 1, 1) for i in range(n)])

    fig, ax = plt.subplots(figsize=(9, 5))
    for r, col in zip(sweep_results, colours):
        s = r.get("detector_overlap", "?")
        ax.plot(r["screen_positions"], r["probability_profile"],
                lw=1.2, color=col, alpha=0.85, label=f"s={s:.2f}")
    ax.set_xlabel("Screen position y")
    ax.set_ylabel("Probability")
    ax.set_title("Advanced quantum: detector overlap sweep")
    ax.legend(fontsize=7, ncol=2)
    sm = cm.ScalarMappable(cmap="plasma",
                           norm=plt.Normalize(vmin=0, vmax=1))
    sm.set_array([])
    fig.colorbar(sm, ax=ax, label="Detector overlap s")
    fig.tight_layout()
    fig.savefig(output_path, dpi=120)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Visibility vs distinguishability
# ---------------------------------------------------------------------------

def plot_visibility_vs_distinguishability(
    sweep_results: List[Dict[str, Any]],
    probs_which_path: List[float],
    probs_coherent: List[float],
    output_path: Path,
) -> None:
    overlaps, d_vals, v_raw, v_int = [], [], [], []

    for r in sweep_results:
        s = r.get("detector_overlap")
        probs = r.get("probability_profile", [])
        if s is None or not probs:
            continue
        overlaps.append(s)
        d_vals.append(path_distinguishability(s))
        v_raw.append(fringe_visibility(probs))
        v_int.append(interference_visibility_corrected(probs, probs_which_path, probs_coherent))

    if not d_vals:
        return

    # Sort by D
    order = sorted(range(len(d_vals)), key=lambda i: d_vals[i])
    d_s = [d_vals[i] for i in order]
    v_r_s = [v_raw[i] for i in order]
    v_i_s = [v_int[i] for i in order]

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(d_s, v_r_s, "o-", color="steelblue", lw=1.8, ms=6, label="V_raw (Michelson)")
    ax.plot(d_s, v_i_s, "s--", color="orange", lw=1.5, ms=5, label="V_corrected (baseline-subtracted)")

    # V^2 + D^2 = 1 reference curve
    import numpy as np
    d_ref = [i / 100 for i in range(101)]
    v_ref = [math.sqrt(max(1 - d ** 2, 0)) for d in d_ref]
    ax.plot(d_ref, v_ref, "k:", lw=1, label="V²+D²=1 bound")

    ax.set_xlabel("Path distinguishability D")
    ax.set_ylabel("Fringe visibility V")
    ax.set_title("Visibility vs distinguishability — complementarity")
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=120)
    plt.close(fig)


# ---------------------------------------------------------------------------
# 100-run stability
# ---------------------------------------------------------------------------

def plot_hundred_run_stability(
    aggregate_summary: Dict[str, Any],
    output_path: Path,
) -> None:
    coh = aggregate_summary.get("two_slit_coherent", {}).get("fringe_visibility_empirical", {})
    wp = aggregate_summary.get("two_slit_which_path", {}).get("fringe_visibility_empirical", {})

    if not coh or not wp:
        return

    conditions = ["two_slit_coherent", "two_slit_which_path"]
    means = [coh.get("mean", 0), wp.get("mean", 0)]
    stds = [coh.get("std", 0), wp.get("std", 0)]
    colours = ["steelblue", "coral"]

    fig, ax = plt.subplots(figsize=(6, 4))
    x = [0, 1]
    bars = ax.bar(x, means, yerr=stds, capsize=8, color=colours, alpha=0.75, width=0.5, ecolor="black")
    ax.set_xticks(x)
    ax.set_xticklabels(["Coherent (s=1)", "Which-path (s=0)"])
    ax.set_ylabel("Empirical fringe visibility")
    n_runs = aggregate_summary.get("n_repeated_runs", "?")
    ax.set_title(f"100-run stability: mean±std  (n={n_runs} runs)")
    ax.set_ylim(0, 1.1)
    for i, (m, s) in enumerate(zip(means, stds)):
        ax.text(i, m + s + 0.02, f"{m:.3f}±{s:.3f}", ha="center", fontsize=9)
    fig.tight_layout()
    fig.savefig(output_path, dpi=120)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Master entry point
# ---------------------------------------------------------------------------

def plot_advanced_quantum(
    results: Dict[str, Any],
    aggregate_summary: Optional[Dict[str, Any]] = None,
    output_dir: Optional[Path] = None,
) -> List[Path]:
    """Generate all figures for the advanced quantum benchmark.

    Returns list of created PNG paths.
    """
    out = Path(output_dir) if output_dir else Path.cwd()
    out.mkdir(parents=True, exist_ok=True)

    created: List[Path] = []

    _cond_titles = [
        ("one_slit", "Advanced quantum: one slit"),
        ("two_slit_coherent", "Advanced quantum: coherent (s=1)"),
        ("two_slit_which_path", "Advanced quantum: which-path (s=0)"),
        ("eraser_plus", "Advanced quantum: eraser |+⟩"),
        ("eraser_minus", "Advanced quantum: eraser |−⟩"),
    ]

    for key, title in _cond_titles:
        r = results.get(key)
        if r is None:
            continue
        p = out / f"{key}_distribution.png"
        _plot_condition(r, title, p)
        created.append(p)

    sweep = results.get("overlap_sweep", [])
    probs_wp = results["two_slit_which_path"]["probability_profile"]
    probs_coh = results["two_slit_coherent"]["probability_profile"]

    if sweep:
        p = out / "overlap_sweep.png"
        plot_overlap_sweep(sweep, p)
        created.append(p)

        p = out / "visibility_vs_distinguishability.png"
        plot_visibility_vs_distinguishability(sweep, probs_wp, probs_coh, p)
        created.append(p)

    if aggregate_summary:
        p = out / "hundred_run_stability.png"
        plot_hundred_run_stability(aggregate_summary, p)
        created.append(p)

    print(f"  [plot_advanced] Wrote {len(created)} figures to {out}", flush=True)
    return created
