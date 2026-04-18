"""
double_slit.py — Minimal double-slit interference benchmark.

PURPOSE
-------
This module is a **benchmark model**, not a quantum simulator.  Its purpose
is to provide a known observer-sensitive signal that the Reality Audit
framework can detect and characterise.

The model reproduces the qualitative behaviour of the double-slit experiment
using classical wave optics formulae:

    I(y) ∝ cos²(π · d · y / (λ · L))   [interference term]
         × sinc²(π · a · y / (λ · L))   [single-slit diffraction envelope]

where d = slit separation, a = slit width, λ = wavelength parameter,
L = screen distance, y = screen position.

Three experimental conditions are supported:

  ONE_SLIT      — one slit open; single-slit diffraction only.
  TWO_SLIT      — both slits open, no which-path measurement.
                  Full wave-optics intensity including interference term.
  TWO_SLIT_MEASURED — both slits open, which-path detector active.
                  Each photon/particle is assigned to one slit before
                  combining; cross-interference term is suppressed.
                  The resulting pattern is the incoherent sum of two
                  single-slit patterns, shifted by ±d/2.

LIMITATIONS
-----------
- This is a classical-wave approximation, not a full quantum simulation.
- Particle detection is simulated by Poisson-sampling integer hit counts
  from the intensity profile.
- The "which-path measurement" is implemented by suppressing the
  cosine interference term — it models the qualitative effect (pattern
  collapse) without simulating actual quantum decoherence.
- Results are deterministic given a fixed seed.

HONEST FRAMING
--------------
This benchmark is suitable for validating observer-sensitive audit logic.
It is NOT a claim about quantum mechanics in the real universe.
"""

from __future__ import annotations

import json
import math
import random
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Condition enum
# ---------------------------------------------------------------------------

class SlitCondition(str, Enum):
    ONE_SLIT = "one_slit"
    TWO_SLIT = "two_slit"
    TWO_SLIT_MEASURED = "two_slit_measured"


# ---------------------------------------------------------------------------
# Default parameters
# ---------------------------------------------------------------------------

DEFAULT_N_TRIALS: int = 50_000
DEFAULT_SLIT_SEPARATION: float = 4.0   # d  (arbitrary units)
DEFAULT_SLIT_WIDTH: float = 1.0        # a  (a < d always)
DEFAULT_WAVELENGTH: float = 1.0        # λ  (arbitrary units)
DEFAULT_SCREEN_DISTANCE: float = 100.0 # L
DEFAULT_SCREEN_WIDTH: float = 40.0     # half-width of screen (−W to +W)
DEFAULT_N_BINS: int = 100              # number of screen bins

# ---------------------------------------------------------------------------
# Intensity functions
# ---------------------------------------------------------------------------

def _sinc(x: float) -> float:
    """Normalised sinc: sinc(x) = sin(πx)/(πx), sinc(0) = 1."""
    if abs(x) < 1e-12:
        return 1.0
    return math.sin(math.pi * x) / (math.pi * x)


def single_slit_intensity(
    y: float,
    slit_width: float,
    wavelength: float,
    screen_distance: float,
) -> float:
    """Single-slit diffraction intensity at screen position y."""
    beta = slit_width * y / (wavelength * screen_distance)
    return _sinc(beta) ** 2


def two_slit_intensity(
    y: float,
    slit_separation: float,
    slit_width: float,
    wavelength: float,
    screen_distance: float,
) -> float:
    """Double-slit intensity with full interference (no which-path)."""
    # Interference term: cos²(π·d·y / λ·L)
    cos_arg = math.pi * slit_separation * y / (wavelength * screen_distance)
    interference = math.cos(cos_arg) ** 2
    # Single-slit envelope
    envelope = single_slit_intensity(y, slit_width, wavelength, screen_distance)
    # Combined (factor of 4 normalised away; relative shape only)
    return interference * envelope


def two_slit_measured_intensity(
    y: float,
    slit_separation: float,
    slit_width: float,
    wavelength: float,
    screen_distance: float,
) -> float:
    """Double-slit WITH which-path measurement — incoherent sum.

    Cross-interference term is suppressed.  Each slit contributes an
    independent single-slit pattern shifted by ±d/2.
    """
    y_plus  = y - slit_separation / 2.0
    y_minus = y + slit_separation / 2.0
    i_plus  = single_slit_intensity(y_plus,  slit_width, wavelength, screen_distance)
    i_minus = single_slit_intensity(y_minus, slit_width, wavelength, screen_distance)
    return (i_plus + i_minus) / 2.0


def compute_intensity_profile(
    condition: SlitCondition,
    screen_positions: List[float],
    slit_separation: float,
    slit_width: float,
    wavelength: float,
    screen_distance: float,
) -> List[float]:
    """Compute intensity at each screen position for the given condition."""
    intensities: List[float] = []
    for y in screen_positions:
        if condition == SlitCondition.ONE_SLIT:
            intensities.append(
                single_slit_intensity(y, slit_width, wavelength, screen_distance)
            )
        elif condition == SlitCondition.TWO_SLIT:
            intensities.append(
                two_slit_intensity(y, slit_separation, slit_width, wavelength, screen_distance)
            )
        elif condition == SlitCondition.TWO_SLIT_MEASURED:
            intensities.append(
                two_slit_measured_intensity(y, slit_separation, slit_width, wavelength, screen_distance)
            )
        else:
            raise ValueError(f"Unknown condition: {condition}")
    return intensities


# ---------------------------------------------------------------------------
# Sampling — convert intensity profile to hit histogram
# ---------------------------------------------------------------------------

def sample_hits(
    intensities: List[float],
    n_trials: int,
    seed: int = 0,
) -> List[int]:
    """Sample integer hit counts from an intensity profile.

    Uses Poisson sampling (or multinomial assignment) with the normalised
    intensity as the probability distribution.

    Parameters
    ----------
    intensities : list of float
        Unnormalised intensity values per bin.
    n_trials : int
        Total number of particle/photon trials to distribute.
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    list of int
        Hit counts per bin, summing to approximately n_trials.
    """
    rng = random.Random(seed)

    total = sum(intensities)
    if total <= 0:
        return [0] * len(intensities)

    probs = [i / total for i in intensities]

    # Multinomial sampling via cumulative CDF
    hits = [0] * len(probs)
    cumulative = []
    acc = 0.0
    for p in probs:
        acc += p
        cumulative.append(acc)

    for _ in range(n_trials):
        r = rng.random()
        # Binary search for bin
        lo, hi = 0, len(cumulative) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if cumulative[mid] < r:
                lo = mid + 1
            else:
                hi = mid
        hits[lo] += 1

    return hits


# ---------------------------------------------------------------------------
# Main run function
# ---------------------------------------------------------------------------

def run_condition(
    condition: SlitCondition,
    n_trials: int = DEFAULT_N_TRIALS,
    slit_separation: float = DEFAULT_SLIT_SEPARATION,
    slit_width: float = DEFAULT_SLIT_WIDTH,
    wavelength: float = DEFAULT_WAVELENGTH,
    screen_distance: float = DEFAULT_SCREEN_DISTANCE,
    screen_width: float = DEFAULT_SCREEN_WIDTH,
    n_bins: int = DEFAULT_N_BINS,
    seed: int = 0,
) -> Dict[str, Any]:
    """Run one experimental condition and return raw results.

    Returns
    -------
    dict with keys:
        condition, params, screen_positions, intensity_profile,
        hit_counts, n_trials, seed, summary
    """
    # Screen positions: n_bins evenly spaced in [-screen_width, +screen_width]
    if n_bins < 2:
        raise ValueError("n_bins must be >= 2")
    step = (2.0 * screen_width) / (n_bins - 1)
    screen_positions = [
        round(-screen_width + i * step, 8)
        for i in range(n_bins)
    ]

    intensities = compute_intensity_profile(
        condition=condition,
        screen_positions=screen_positions,
        slit_separation=slit_separation,
        slit_width=slit_width,
        wavelength=wavelength,
        screen_distance=screen_distance,
    )

    hits = sample_hits(intensities, n_trials, seed=seed)

    # Summary statistics
    total_hits = sum(hits)
    center_bin = n_bins // 2
    center_intensity = intensities[center_bin]
    max_intensity = max(intensities)
    peak_bin = intensities.index(max_intensity)

    summary: Dict[str, Any] = {
        "condition": str(condition),
        "n_trials": n_trials,
        "seed": seed,
        "total_hits": total_hits,
        "center_intensity": round(center_intensity, 6),
        "max_intensity": round(max_intensity, 6),
        "peak_bin": peak_bin,
        "center_bin": center_bin,
        "n_bins": n_bins,
        "screen_width": screen_width,
    }

    params: Dict[str, Any] = {
        "condition": str(condition),
        "n_trials": n_trials,
        "slit_separation": slit_separation,
        "slit_width": slit_width,
        "wavelength": wavelength,
        "screen_distance": screen_distance,
        "screen_width": screen_width,
        "n_bins": n_bins,
        "seed": seed,
    }

    return {
        "condition": str(condition),
        "params": params,
        "screen_positions": screen_positions,
        "intensity_profile": [round(v, 8) for v in intensities],
        "hit_counts": hits,
        "n_trials": n_trials,
        "seed": seed,
        "summary": summary,
    }


def run_all_conditions(
    n_trials: int = DEFAULT_N_TRIALS,
    slit_separation: float = DEFAULT_SLIT_SEPARATION,
    slit_width: float = DEFAULT_SLIT_WIDTH,
    wavelength: float = DEFAULT_WAVELENGTH,
    screen_distance: float = DEFAULT_SCREEN_DISTANCE,
    screen_width: float = DEFAULT_SCREEN_WIDTH,
    n_bins: int = DEFAULT_N_BINS,
    seed: int = 0,
) -> Dict[str, Dict[str, Any]]:
    """Run all three conditions and return a dict keyed by condition name."""
    results: Dict[str, Dict[str, Any]] = {}
    for cond in SlitCondition:
        results[cond.value] = run_condition(
            condition=cond,
            n_trials=n_trials,
            slit_separation=slit_separation,
            slit_width=slit_width,
            wavelength=wavelength,
            screen_distance=screen_distance,
            screen_width=screen_width,
            n_bins=n_bins,
            seed=seed,
        )
    return results
