"""
plot_double_slit.py — Visualisation for double-slit benchmark results.

Generates four figures:
  1. one_slit_distribution.png
  2. two_slit_distribution.png
  3. two_slit_measured_distribution.png
  4. overlay_comparison.png

Output: commons_sentience_sim/output/reality_audit/double_slit/figures/
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_RESULTS_DIR = (
    _REPO_ROOT / "commons_sentience_sim" / "output" / "reality_audit" / "double_slit"
)
_FIGURES_DIR = _DEFAULT_RESULTS_DIR / "figures"

# Condition display names
_DISPLAY = {
    "one_slit":           "One Slit Open",
    "two_slit":           "Two Slits Open (No Measurement)",
    "two_slit_measured":  "Two Slits Open (With Measurement)",
}

_COLORS = {
    "one_slit":          "#2196F3",
    "two_slit":          "#4CAF50",
    "two_slit_measured": "#F44336",
}


def _load_results(results_dir: Path) -> Optional[Dict[str, Any]]:
    raw_path = results_dir / "raw_results.json"
    if not raw_path.exists():
        return None
    with open(raw_path, encoding="utf-8") as fh:
        return json.load(fh)


def _plot_single_condition(
    ax: Any,
    positions: List[float],
    intensities: List[float],
    hits: List[int],
    label: str,
    color: str,
) -> None:
    """Plot intensity profile + hit histogram on one axis."""
    import matplotlib.pyplot as plt

    total_hits = sum(hits)
    hit_norm = [h / total_hits if total_hits > 0 else 0 for h in hits]
    max_intensity = max(intensities) if intensities else 1.0

    ax.bar(positions, hit_norm, width=(positions[1] - positions[0]) if len(positions) > 1 else 0.4,
           alpha=0.35, color=color, label="Sampled hits (normalised)")
    ax.plot(positions, [v / max_intensity * max(hit_norm) if max_intensity > 0 else 0
                        for v in intensities],
            color=color, linewidth=2, label="Intensity profile (scaled)")
    ax.set_title(label, fontsize=11)
    ax.set_xlabel("Screen position")
    ax.set_ylabel("Intensity / Hit rate")
    ax.legend(fontsize=8)


def generate_all_double_slit_figures(
    results_dir: Optional[Path] = None,
    figures_dir: Optional[Path] = None,
    results: Optional[Dict[str, Any]] = None,
) -> List[Path]:
    """Generate all four double-slit figures.

    Parameters
    ----------
    results_dir : Path, optional
        Directory containing raw_results.json.  Defaults to standard output path.
    figures_dir : Path, optional
        Output directory for figures.
    results : dict, optional
        Pre-loaded results dict (skips loading from disk if provided).

    Returns
    -------
    list of Path
        Paths to all figure files written.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    res_dir = results_dir or _DEFAULT_RESULTS_DIR
    fig_dir = figures_dir or _FIGURES_DIR
    fig_dir.mkdir(parents=True, exist_ok=True)

    data = results or _load_results(res_dir)

    # If no live data, generate with default parameters (synthetic)
    if data is None:
        print("  [plot_double_slit] No live data found — generating synthetic results", flush=True)
        from reality_audit.benchmarks.double_slit import run_all_conditions
        data = run_all_conditions(n_trials=10_000, n_bins=100)

    written: List[Path] = []

    conditions = ["one_slit", "two_slit", "two_slit_measured"]

    # ── Figures 1–3: per-condition ────────────────────────────────────────
    for cond_key in conditions:
        if cond_key not in data:
            continue
        result = data[cond_key]
        positions = result["screen_positions"]
        intensities = result["intensity_profile"]
        hits = result["hit_counts"]

        fig, ax = plt.subplots(figsize=(8, 4))
        _plot_single_condition(
            ax, positions, intensities, hits,
            label=_DISPLAY.get(cond_key, cond_key),
            color=_COLORS.get(cond_key, "#777"),
        )
        fig.tight_layout()
        out = fig_dir / f"{cond_key}_distribution.png"
        fig.savefig(out, dpi=120)
        plt.close(fig)
        written.append(out)
        print(f"  [plot_double_slit] Wrote {out.name}", flush=True)

    # ── Figure 4: overlay comparison ─────────────────────────────────────
    fig, ax = plt.subplots(figsize=(10, 5))
    for cond_key in conditions:
        if cond_key not in data:
            continue
        result = data[cond_key]
        positions = result["screen_positions"]
        intensities = result["intensity_profile"]
        max_i = max(intensities) if intensities else 1.0
        norm_i = [v / max_i for v in intensities]
        ax.plot(
            positions, norm_i,
            color=_COLORS.get(cond_key, "#777"),
            label=_DISPLAY.get(cond_key, cond_key),
            linewidth=2,
        )

    ax.set_title("Double-Slit Benchmark: Overlay Comparison", fontsize=12)
    ax.set_xlabel("Screen position")
    ax.set_ylabel("Normalised intensity")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    out = fig_dir / "overlay_comparison.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    written.append(out)
    print(f"  [plot_double_slit] Wrote {out.name}", flush=True)

    return written
