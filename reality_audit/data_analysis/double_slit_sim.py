"""
double_slit_sim.py
==================
Physics-inspired simulation of a 1-D double-slit experiment with
controllable decoherence and measurement effects.

The model is intentionally simple and explainable — it is a robust
computational benchmark, NOT a laboratory-grade quantum solver.

Physics model
-------------
* Coherent case:
    I(x) = A(x)^2 * [1 + cos(phi(x))]
  where A(x) is the single-slit diffraction envelope and phi(x) is the
  phase difference between the two slits.

* Decoherence / measurement:
    I_classical(x) = sum of two independent single-slit patterns
    I_mixed(x) = (1 - alpha) * I_coherent(x) + alpha * I_classical(x)
  where alpha = clip(decoherence_strength + (1 if measurement_on else 0), 0, 1).

* Noise: additive Gaussian noise of strength noise_level * mean(I).

Visibility (fringe contrast) is used as the primary coherence metric:
    V = (I_max - I_min) / (I_max + I_min)

Usage
-----
    from reality_audit.data_analysis.double_slit_sim import run_double_slit_sim
    result = run_double_slit_sim(wavelength=500e-9, slit_separation=1e-4, ...)
"""
from __future__ import annotations

import csv
import datetime
import json
import math
import os
import random
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Optional numpy – gracefully fall back to pure math
# ---------------------------------------------------------------------------
try:
    import numpy as np
    _HAS_NUMPY = True
except ImportError:  # pragma: no cover
    _HAS_NUMPY = False


# ---------------------------------------------------------------------------
# Simulation core
# ---------------------------------------------------------------------------

def _linspace(start: float, stop: float, n: int) -> List[float]:
    """Pure-Python linspace replacement when numpy is absent."""
    if n < 2:
        return [start]
    step = (stop - start) / (n - 1)
    return [start + i * step for i in range(n)]


def _sinc_squared(x: float) -> float:
    """sin(x)^2 / x^2; equals 1 at x=0."""
    if abs(x) < 1e-15:
        return 1.0
    return (math.sin(x) / x) ** 2


def _compute_intensity(
    positions: List[float],
    wavelength: float,
    slit_separation: float,
    slit_width: float,
    screen_distance: float,
    alpha: float,
) -> List[float]:
    """
    Compute mixed interference intensity at each screen position.

    Parameters
    ----------
    positions         : 1-D list of screen positions (metres)
    wavelength        : photon/particle wavelength (metres)
    slit_separation   : centre-to-centre slit distance (metres)
    slit_width        : individual slit width (metres)
    screen_distance   : distance from slits to screen (metres)
    alpha             : decoherence mixing parameter in [0, 1].
                        0 = fully coherent, 1 = fully classical/decohered.

    Returns
    -------
    List of normalised intensities (peak = 1 at centre for coherent case).
    """
    k = 2.0 * math.pi / wavelength
    intensities: List[float] = []

    for x in positions:
        theta = math.atan(x / screen_distance) if screen_distance > 0 else 0.0
        # Single-slit diffraction envelope (beta = half-argument of sinc)
        beta = (k * slit_width * math.sin(theta)) / 2.0
        envelope = _sinc_squared(beta)

        # Two-slit interference term
        delta = (k * slit_separation * math.sin(theta)) / 2.0
        interference_factor = math.cos(delta) ** 2  # (1 + cos(2*delta))/2

        # Coherent double-slit: 4 * I_single * cos^2(delta/2) * sinc^2(beta)
        # Simplified so that centre = 1 for coherent case:
        i_coherent = 4.0 * envelope * interference_factor

        # Classical (incoherent) sum of two single slits
        i_classical = 2.0 * envelope

        # Mix
        i_mixed = (1.0 - alpha) * i_coherent + alpha * i_classical
        intensities.append(i_mixed)

    # Normalise to peak = 1
    peak = max(intensities) if intensities else 1.0
    if peak <= 0.0:
        peak = 1.0
    return [v / peak for v in intensities]


def _fringe_visibility(intensities: List[float]) -> float:
    """
    Compute Michelson fringe visibility V = (I_max - I_min) / (I_max + I_min).
    Returns value in [0, 1].
    """
    i_max = max(intensities)
    i_min = min(intensities)
    denom = i_max + i_min
    if denom <= 0.0:
        return 0.0
    return (i_max - i_min) / denom


def _sample_hits(
    positions: List[float],
    intensities: List[float],
    num_particles: int,
    rng_seed: Optional[int],
) -> List[float]:
    """
    Sample particle hit positions from the intensity distribution.

    Uses simple rejection-style weighted sampling with the intensity as
    a probability weight.
    """
    rstate = random.Random(rng_seed)
    total = sum(intensities)
    if total <= 0.0:
        return [0.0] * num_particles
    weights = [v / total for v in intensities]
    n = len(positions)

    hits: List[float] = []
    for _ in range(num_particles):
        r = rstate.random()
        cumulative = 0.0
        idx = n - 1
        for i, w in enumerate(weights):
            cumulative += w
            if r <= cumulative:
                idx = i
                break
        # Add sub-bin jitter
        if n > 1:
            half_bin = (positions[-1] - positions[0]) / (2.0 * (n - 1))
        else:
            half_bin = 0.0
        hits.append(positions[idx] + rstate.uniform(-half_bin, half_bin))

    return hits


# ---------------------------------------------------------------------------
# Public simulation entry point
# ---------------------------------------------------------------------------

def run_double_slit_sim(
    wavelength: float = 500e-9,
    slit_separation: float = 1e-4,
    slit_width: float = 2e-5,
    screen_distance: float = 1.0,
    num_particles: int = 5000,
    screen_points: int = 500,
    coherence: float = 1.0,
    decoherence_strength: float = 0.0,
    measurement_on: bool = False,
    noise_level: float = 0.0,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Run a 1-D double-slit simulation.

    Parameters
    ----------
    wavelength          : de Broglie / optical wavelength in metres (default 500 nm)
    slit_separation     : centre-to-centre slit spacing in metres (default 100 µm)
    slit_width          : individual slit width in metres (default 20 µm)
    screen_distance     : slit-to-screen distance in metres (default 1 m)
    num_particles       : number of particle hits to sample
    screen_points       : number of discrete positions on the screen
    coherence           : coherence factor in [0, 1]; 1=fully coherent (not
                          directly alpha, but modifies it)
    decoherence_strength: additional decoherence towards classical [0, 1]
    measurement_on      : if True, fully classicalise (measurement destroys
                          which-path ambiguity, alpha → 1)
    noise_level         : fractional additive Gaussian noise on intensity
    seed                : RNG seed for reproducibility (None = non-deterministic)

    Returns
    -------
    dict with keys:
      run_id, timestamp, parameters, positions, intensity,
      hit_positions, visibility, coherence_score,
      interference_detected, notes, summary_stats
    """
    run_id = str(uuid.uuid4())
    timestamp = datetime.datetime.utcnow().isoformat() + "Z"

    # -----------------------------------------------------------------------
    # Determine effective alpha (decoherence mixing parameter)
    # -----------------------------------------------------------------------
    # coherence=1 → no extra decoherence from coherence parameter
    # coherence=0 → full decoherence (alpha += 1)
    coherence_decoherence = 1.0 - max(0.0, min(1.0, coherence))
    measurement_addend = 1.0 if measurement_on else 0.0
    alpha = min(1.0, coherence_decoherence + decoherence_strength + measurement_addend)
    alpha = max(0.0, alpha)

    # -----------------------------------------------------------------------
    # Screen positions
    # -----------------------------------------------------------------------
    # Span ±5 * first fringe spacing from centre for a representative view
    max_x = min(
        5.0 * wavelength * screen_distance / slit_separation,
        screen_distance * 0.5,  # cap at ±50% of screen distance
    )
    positions = _linspace(-max_x, max_x, screen_points)

    # -----------------------------------------------------------------------
    # Compute intensity
    # -----------------------------------------------------------------------
    intensities = _compute_intensity(
        positions, wavelength, slit_separation, slit_width, screen_distance, alpha
    )

    # Additive noise
    if noise_level > 0.0:
        rstate = random.Random(seed if seed is not None else 0)
        mean_i = sum(intensities) / len(intensities) if intensities else 1.0
        sigma = noise_level * mean_i
        intensities = [max(0.0, v + rstate.gauss(0.0, sigma)) for v in intensities]
        # Re-normalise
        peak = max(intensities) if intensities else 1.0
        if peak > 0.0:
            intensities = [v / peak for v in intensities]

    # -----------------------------------------------------------------------
    # Fringe visibility
    # -----------------------------------------------------------------------
    visibility = _fringe_visibility(intensities)

    # -----------------------------------------------------------------------
    # Sample particle hits
    # -----------------------------------------------------------------------
    hit_noise_seed = (seed + 1) if seed is not None else None
    hit_positions = _sample_hits(positions, intensities, num_particles, hit_noise_seed)

    # -----------------------------------------------------------------------
    # Coherence score & interference detection
    # -----------------------------------------------------------------------
    # coherence_score mirrors visibility but is labelled distinctly to
    # clarify it comes from the simulation geometry, not raw visibility.
    coherence_score = visibility

    # Interference detected if visibility > 0.1 (threshold) and
    # coherence score is statistically meaningful
    interference_threshold = 0.15
    interference_detected = (visibility > interference_threshold)

    # -----------------------------------------------------------------------
    # Notes / classification
    # -----------------------------------------------------------------------
    if alpha < 0.2:
        regime = "coherent"
        notes = (
            "Strong interference fringe pattern. Alpha < 0.2: wave-like regime. "
            "Result classified as COHERENT."
        )
    elif alpha < 0.7:
        regime = "partially_decohered"
        notes = (
            f"Reduced fringe contrast. Alpha={alpha:.2f}: partial decoherence. "
            "Result classified as PARTIALLY DECOHERED."
        )
    else:
        regime = "classicalized"
        notes = (
            f"Fringe pattern suppressed. Alpha={alpha:.2f}: strongly decohered or "
            "measurement active. Result classified as CLASSICALIZED (particle-like)."
        )

    if measurement_on:
        notes += " measurement_on=True: which-path information extracted."

    # -----------------------------------------------------------------------
    # Summary stats
    # -----------------------------------------------------------------------
    n_hits = len(hit_positions)
    mean_pos = sum(hit_positions) / n_hits if n_hits else 0.0
    spread = math.sqrt(
        sum((h - mean_pos) ** 2 for h in hit_positions) / n_hits
    ) if n_hits > 1 else 0.0

    summary_stats = {
        "num_hits": n_hits,
        "mean_hit_position_m": round(mean_pos, 9),
        "hit_spread_std_m": round(spread, 9),
        "alpha_effective": round(alpha, 4),
        "max_intensity": round(max(intensities), 6),
        "min_intensity": round(min(intensities), 6),
    }

    parameters = {
        "wavelength_m": wavelength,
        "slit_separation_m": slit_separation,
        "slit_width_m": slit_width,
        "screen_distance_m": screen_distance,
        "num_particles": num_particles,
        "screen_points": screen_points,
        "coherence": coherence,
        "decoherence_strength": decoherence_strength,
        "measurement_on": measurement_on,
        "noise_level": noise_level,
        "seed": seed,
    }

    return {
        "run_id": run_id,
        "timestamp": timestamp,
        "parameters": parameters,
        "positions": positions,
        "intensity": intensities,
        "hit_positions": hit_positions,
        "visibility": round(visibility, 6),
        "coherence_score": round(coherence_score, 6),
        "interference_detected": interference_detected,
        "regime": regime,
        "notes": notes,
        "summary_stats": summary_stats,
    }


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def plot_double_slit(
    result: Dict[str, Any],
    output_path: str,
    title: Optional[str] = None,
) -> str:
    """
    Save a PNG plot of the intensity distribution with a hit histogram overlay.

    Parameters
    ----------
    result      : dict returned by run_double_slit_sim
    output_path : full path to the output PNG file
    title       : optional plot title override

    Returns
    -------
    Absolute path to the saved PNG.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("matplotlib is required for plotting.") from exc

    positions = result["positions"]
    intensities = result["intensity"]
    hits = result["hit_positions"]
    visibility = result["visibility"]
    regime = result["regime"]
    params = result["parameters"]

    # Scale positions to mm for readability
    pos_mm = [p * 1e3 for p in positions]
    hits_mm = [h * 1e3 for h in hits]

    fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True)

    # Top panel: intensity curve
    axes[0].plot(pos_mm, intensities, color="steelblue", linewidth=1.5, label="Intensity")
    axes[0].set_ylabel("Normalised Intensity")
    axes[0].set_title(
        title
        or (
            f"Double-Slit Simulation | λ={params['wavelength_m']*1e9:.0f} nm | "
            f"d={params['slit_separation_m']*1e6:.0f} µm | "
            f"Regime: {regime} | Visibility={visibility:.3f}"
        )
    )
    axes[0].axhline(0, color="gray", linewidth=0.5, linestyle="--")
    axes[0].legend(loc="upper right", fontsize=8)
    axes[0].set_ylim(-0.05, 1.15)

    # Bottom panel: hit histogram
    if hits_mm:
        n_bins = min(100, max(20, len(hits_mm) // 50))
        axes[1].hist(
            hits_mm, bins=n_bins, density=True, color="coral", alpha=0.7,
            label=f"Hits (n={len(hits_mm)})"
        )
    axes[1].set_xlabel("Screen position (mm)")
    axes[1].set_ylabel("Hit density")
    axes[1].legend(loc="upper right", fontsize=8)

    fig.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    fig.savefig(output_path, dpi=120)
    plt.close(fig)
    return str(Path(output_path).resolve())


# ---------------------------------------------------------------------------
# Audit artifact writers
# ---------------------------------------------------------------------------

def write_json_report(result: Dict[str, Any], output_path: str) -> str:
    """Write the simulation result as a JSON report (positions/hits omitted for size)."""
    report = {
        "run_id": result["run_id"],
        "timestamp": result["timestamp"],
        "parameters": result["parameters"],
        "visibility": result["visibility"],
        "coherence_score": result["coherence_score"],
        "interference_detected": result["interference_detected"],
        "regime": result["regime"],
        "measurement_on": result["parameters"]["measurement_on"],
        "decoherence_strength": result["parameters"]["decoherence_strength"],
        "notes": result["notes"],
        "summary_stats": result["summary_stats"],
        "WARNING": (
            "This is a computational simulation. It does not by itself constitute "
            "evidence that reality is a simulation."
        ),
    }
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    return output_path


def write_csv_data(result: Dict[str, Any], output_path: str) -> str:
    """Write screen positions and intensities to a CSV file."""
    positions = result["positions"]
    intensities = result["intensity"]
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["position_m", "normalised_intensity"])
        for pos, inten in zip(positions, intensities):
            writer.writerow([f"{pos:.9e}", f"{inten:.6f}"])
    return output_path


def write_markdown_summary(result: Dict[str, Any], output_path: str) -> str:
    """Write a human-readable Markdown summary of the simulation run."""
    p = result["parameters"]
    lines = [
        "# Double-Slit Simulation Run Summary",
        "",
        f"**Run ID:** `{result['run_id']}`  ",
        f"**Timestamp:** {result['timestamp']}  ",
        "",
        "## Parameters",
        "",
        f"| Parameter | Value |",
        f"|-----------|-------|",
        f"| Wavelength | {p['wavelength_m']*1e9:.1f} nm |",
        f"| Slit separation | {p['slit_separation_m']*1e6:.1f} µm |",
        f"| Slit width | {p['slit_width_m']*1e6:.1f} µm |",
        f"| Screen distance | {p['screen_distance_m']:.2f} m |",
        f"| Num particles | {p['num_particles']:,} |",
        f"| Coherence | {p['coherence']:.2f} |",
        f"| Decoherence strength | {p['decoherence_strength']:.2f} |",
        f"| Measurement on | {p['measurement_on']} |",
        f"| Noise level | {p['noise_level']:.3f} |",
        f"| Seed | {p['seed']} |",
        "",
        "## Results",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Visibility (fringe contrast) | {result['visibility']:.4f} |",
        f"| Coherence score | {result['coherence_score']:.4f} |",
        f"| Interference detected | {result['interference_detected']} |",
        f"| Regime | **{result['regime']}** |",
        f"| Alpha (effective decoherence) | {result['summary_stats']['alpha_effective']:.4f} |",
        "",
        "## Notes",
        "",
        result["notes"],
        "",
        "---",
        "",
        "> **Warning:** This is a computational simulation model. It does not by itself ",
        "> constitute evidence that reality is a simulation.",
    ]
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    return output_path


def write_all_artifacts(
    result: Dict[str, Any],
    output_dir: str,
    name: str = "double_slit",
) -> Dict[str, str]:
    """
    Write all audit artifacts for a single simulation run.

    Returns a dict mapping artifact type to file path.
    """
    os.makedirs(output_dir, exist_ok=True)
    paths = {}
    paths["json"] = write_json_report(result, os.path.join(output_dir, f"{name}_report.json"))
    paths["csv"] = write_csv_data(result, os.path.join(output_dir, f"{name}_intensity.csv"))
    paths["markdown"] = write_markdown_summary(result, os.path.join(output_dir, f"{name}_summary.md"))
    try:
        paths["plot"] = plot_double_slit(result, os.path.join(output_dir, f"{name}_plot.png"))
    except Exception as exc:
        paths["plot"] = f"SKIPPED: {exc}"
    return paths
