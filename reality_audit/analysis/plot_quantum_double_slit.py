"""
plot_quantum_double_slit.py — Visualisation for quantum double-slit benchmark.

Produces six PNG figures in the provided output directory:
  1. one_slit_distribution.png
  2. two_slit_coherent_distribution.png
  3. two_slit_decohered_distribution.png
  4. decoherence_sweep.png
  5. overlay_comparison.png
  6. visibility_vs_gamma.png
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.cm as cm


# ---------------------------------------------------------------------------
# Individual condition plots
# ---------------------------------------------------------------------------

def _fringe_visibility(probs: Sequence[float]) -> float:
    p_max = max(probs) if probs else 0.0
    p_min = min(probs) if probs else 0.0
    denom = p_max + p_min
    return (p_max - p_min) / denom if denom else 0.0


def plot_single_condition(
    result: Dict[str, Any],
    title: str,
    output_path: Path,
) -> None:
    """Plot probability profile and hit histogram for a single condition."""
    positions = result["screen_positions"]
    probs = result["probability_profile"]
    hits = result["hit_counts"]
    n_trials = result["n_trials"]
    gamma = result.get("decoherence_gamma", 0.0)

    fig, (ax_prob, ax_hit) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)

    ax_prob.plot(positions, probs, lw=1.5, color="steelblue", label="P(y) theory")
    ax_prob.set_ylabel("Probability")
    ax_prob.set_title(title)
    vis = _fringe_visibility(probs)
    ax_prob.text(
        0.98, 0.95,
        f"Visibility={vis:.3f}\nγ={gamma:.2f}",
        transform=ax_prob.transAxes,
        ha="right", va="top",
        fontsize=8, style="italic",
        bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.7),
    )
    ax_prob.legend(fontsize=8)

    hit_probs = [h / n_trials for h in hits] if n_trials else [0.0] * len(hits)
    ax_hit.bar(positions, hit_probs, width=(positions[1] - positions[0]) if len(positions) > 1 else 1.0,
               color="coral", alpha=0.7, label="Sampled (Born-rule)")
    ax_hit.set_xlabel("Screen position y")
    ax_hit.set_ylabel("Empirical frequency")
    ax_hit.legend(fontsize=8)

    fig.tight_layout()
    fig.savefig(output_path, dpi=120)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Decoherence sweep plot
# ---------------------------------------------------------------------------

def plot_decoherence_sweep(
    sweep_results: List[Dict[str, Any]],
    output_path: Path,
) -> None:
    """Plot probability profiles for each gamma value in the decoherence sweep."""
    if not sweep_results:
        return

    gammas = [r["decoherence_gamma"] for r in sweep_results]
    n = len(gammas)
    colours = cm.plasma([i / max(n - 1, 1) for i in range(n)])

    fig, ax = plt.subplots(figsize=(9, 5))

    for r, colour in zip(sweep_results, colours):
        g = r["decoherence_gamma"]
        positions = r["screen_positions"]
        probs = r["probability_profile"]
        ax.plot(positions, probs, lw=1.2, color=colour, alpha=0.85, label=f"γ={g:.2f}")

    ax.set_xlabel("Screen position y")
    ax.set_ylabel("Probability")
    ax.set_title("Quantum double-slit — decoherence sweep")
    ax.legend(fontsize=7, loc="upper right", ncol=2)

    sm = cm.ScalarMappable(cmap="plasma",
                           norm=plt.Normalize(vmin=min(gammas), vmax=max(gammas)))
    sm.set_array([])
    fig.colorbar(sm, ax=ax, label="Decoherence γ")

    fig.tight_layout()
    fig.savefig(output_path, dpi=120)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Overlay comparison
# ---------------------------------------------------------------------------

def plot_overlay_comparison(
    results_dict: Dict[str, Any],
    output_path: Path,
) -> None:
    """Overlay one_slit, two_slit_coherent, two_slit_decohered probability profiles."""
    labels = [
        ("one_slit", "One slit", "grey"),
        ("two_slit_decohered", "Two slits (decohered)", "coral"),
        ("two_slit_coherent", "Two slits (coherent)", "steelblue"),
    ]

    fig, ax = plt.subplots(figsize=(9, 5))

    for key, label, colour in labels:
        r = results_dict.get(key)
        if r is None:
            continue
        ax.plot(r["screen_positions"], r["probability_profile"],
                lw=1.5, color=colour, label=label)

    ax.set_xlabel("Screen position y")
    ax.set_ylabel("Probability")
    ax.set_title("Quantum double-slit — condition comparison")
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(output_path, dpi=120)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Visibility vs gamma
# ---------------------------------------------------------------------------

def plot_visibility_vs_gamma(
    sweep_results: List[Dict[str, Any]],
    output_path: Path,
) -> None:
    """Plot fringe visibility as a function of decoherence parameter γ."""
    gammas: List[float] = []
    visibilities: List[float] = []

    for r in sweep_results:
        g = r.get("decoherence_gamma")
        probs = r.get("probability_profile", [])
        if g is not None and probs:
            p_max = max(probs)
            p_min = min(probs)
            denom = p_max + p_min
            v = (p_max - p_min) / denom if denom else 0.0
            gammas.append(g)
            visibilities.append(v)

    if not gammas:
        return

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(gammas, visibilities, "o-", color="steelblue", lw=1.8, ms=6)
    ax.set_xlabel("Decoherence parameter γ")
    ax.set_ylabel("Fringe visibility V")
    ax.set_title("Fringe visibility vs decoherence")
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)
    ax.axhline(0, color="grey", lw=0.7, ls="--")
    ax.axhline(1, color="grey", lw=0.7, ls="--")
    ax.text(0.02, 0.08, "γ=0: fully coherent  |  γ=1: fully decohered",
            transform=ax.transAxes, fontsize=8, color="grey", style="italic")
    fig.tight_layout()
    fig.savefig(output_path, dpi=120)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Master entry point
# ---------------------------------------------------------------------------

def plot_quantum_double_slit(
    results_dict: Dict[str, Any],
    output_dir: Optional[Path] = None,
) -> List[Path]:
    """Generate all six figures for the quantum double-slit benchmark.

    Args:
        results_dict: return value of run_all_conditions()
        output_dir: directory to write PNG files; defaults to CWD

    Returns:
        List of Paths to created PNG files.
    """
    out = Path(output_dir) if output_dir else Path.cwd()
    out.mkdir(parents=True, exist_ok=True)

    created: List[Path] = []

    # 1-3: individual condition plots
    for cond_key, title in [
        ("one_slit", "Quantum one-slit distribution"),
        ("two_slit_coherent", "Quantum two-slit coherent (γ=0)"),
        ("two_slit_decohered", "Quantum two-slit decohered (γ=1)"),
    ]:
        r = results_dict.get(cond_key)
        fname = f"{cond_key}_distribution.png"
        if r is not None:
            p = out / fname
            plot_single_condition(r, title, p)
            created.append(p)

    # 4: decoherence sweep
    sweep = results_dict.get("decoherence_sweep", [])
    if sweep:
        p = out / "decoherence_sweep.png"
        plot_decoherence_sweep(sweep, p)
        created.append(p)

    # 5: overlay
    p = out / "overlay_comparison.png"
    plot_overlay_comparison(results_dict, p)
    created.append(p)

    # 6: visibility vs gamma
    if sweep:
        p = out / "visibility_vs_gamma.png"
        plot_visibility_vs_gamma(sweep, p)
        created.append(p)

    print(f"  [plot_quantum] Wrote {len(created)} figures to {out}", flush=True)
    return created
