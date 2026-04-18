"""
quantum_double_slit.py — Quantum-style two-path interferometer benchmark.

PURPOSE
-------
This module implements a minimal but scientifically honest quantum-style
interferometer using complex probability amplitudes and Born-rule sampling.

It is an UPGRADE over the wave-inspired benchmark in double_slit.py:

  double_slit.py (Stage 1)          → classical intensity formula directly
  quantum_double_slit.py (Stage 2)  → complex amplitudes, density-matrix
                                       decoherence, Born-rule sampling

The module simulates the double-slit / two-path interferometer using:

  1. Complex path amplitudes
     Each slit contributes a complex amplitude at every screen bin.
     The amplitude encodes both magnitude (single-slit diffraction envelope)
     and phase (path-length difference between slit and screen point).

  2. Coherent superposition
     Without which-path information, the total amplitude is the sum of
     the two path amplitudes.  Screen probability = |Ψ_tot|².
     This is equivalent to the quantummechanical result for a pure state.

  3. Density-matrix decoherence model
     A decoherence parameter γ ∈ [0, 1] interpolates between pure coherent
     and fully mixed states:

         P(y) = |A_L + A_R|² + 2(γ-1)·Re(A_L · A_R*)
              = |A_L|² + |A_R|² + 2(1-γ)·Re(A_L · A_R*)

     γ = 0   → fully coherent (maximum fringes)
     γ = 1   → fully decohered (incoherent sum; equivalent to which-path)
     0 < γ < 1 → partial decoherence (intermediate fringe visibility)

  4. Born-rule sampling
     Integer hit counts are drawn from the normalised probability distribution
     using seeded multinomial sampling.

WHY A CLASSICAL COMPUTER CAN SIMULATE THIS
-------------------------------------------
A two-path interferometer has a Hilbert space of dimension 2 (two paths)
tensored with the screen position register.  For a fixed screen, each
screen bin's probability is independent.  The interference effect arises
from a single complex cross-term Re(A_L · A_R*) that any computer can
evaluate exactly.  No exponential scaling occurs because we have only two
paths and we compute probabilities, not wavefunctions of many particles.

LIMITATIONS
-----------
- Exact Fraunhofer (far-field) approximation; no near-field correction.
- Independent screen bins; no spatial correlations across bins.
- Decoherence is phenomenological (γ-weighted mixture), not derived from
  a specific environment model (no Lindblad dynamics).
- Single-mode (monochromatic).
- Does not model detector back-action or measurement dynamics.
- Not a full quantum computer simulation — only two path modes.
"""

from __future__ import annotations

import cmath
import json
import math
import random
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional, Tuple

# ---------------------------------------------------------------------------
# Condition enum
# ---------------------------------------------------------------------------

class QSlitCondition(str, Enum):
    ONE_SLIT             = "one_slit"
    TWO_SLIT_COHERENT    = "two_slit_coherent"
    TWO_SLIT_DECOHERED   = "two_slit_decohered"
    TWO_SLIT_PARTIAL     = "two_slit_partial"   # uses decoherence_gamma param


# ---------------------------------------------------------------------------
# Default parameters
# ---------------------------------------------------------------------------

DEFAULT_N_TRIALS:         int   = 50_000
DEFAULT_SLIT_SEPARATION:  float = 4.0
DEFAULT_SLIT_WIDTH:       float = 1.0
DEFAULT_WAVELENGTH:       float = 1.0
DEFAULT_SCREEN_DISTANCE:  float = 100.0
DEFAULT_SCREEN_WIDTH:     float = 40.0
DEFAULT_N_BINS:           int   = 200
DEFAULT_DECOHERENCE:      float = 0.0    # 0 = coherent


# ---------------------------------------------------------------------------
# Complex amplitude functions (Fraunhofer far-field)
# ---------------------------------------------------------------------------

def _sinc(x: float) -> float:
    """Normalised sinc(x) = sin(πx)/(πx), sinc(0) = 1."""
    if abs(x) < 1e-12:
        return 1.0
    return math.sin(math.pi * x) / (math.pi * x)


def slit_amplitude(
    y_screen: float,
    y_slit: float,
    slit_width: float,
    wavelength: float,
    screen_distance: float,
) -> complex:
    """Compute the complex amplitude contribution from one slit at screen y.

    Uses the Fraunhofer far-field approximation:

        A(y) = sinc(a·y / (λL)) · exp(i · 2π · y_slit · y / (λL))

    The sinc factor is the diffraction envelope from finite slit width a.
    The complex exponential encodes the path-length phase from slit
    position y_slit to screen position y_screen.

    Parameters
    ----------
    y_screen : float
        Screen position at which to evaluate the amplitude.
    y_slit : float
        Transverse position of the slit centre.
    slit_width : float
        Slit width parameter a.
    wavelength : float
        Wavelength-equivalent parameter λ.
    screen_distance : float
        Slit-to-screen distance L.

    Returns
    -------
    complex
    """
    k_over_L = 1.0 / (wavelength * screen_distance)

    # Single-slit diffraction envelope (centred on slit position)
    beta = slit_width * (y_screen - y_slit) * k_over_L
    magnitude = _sinc(beta)

    # Phase from path length: phase ∝ y_slit·y_screen / (λL)
    phase = 2.0 * math.pi * y_slit * y_screen * k_over_L

    return magnitude * cmath.exp(1j * phase)


# ---------------------------------------------------------------------------
# Screen probability functions
# ---------------------------------------------------------------------------

def coherent_probability(
    y: float,
    slit_separation: float,
    slit_width: float,
    wavelength: float,
    screen_distance: float,
) -> float:
    """P(y) for coherent two-slit superposition.

    P = |A_L(y) + A_R(y)|²

    Normalisation: returns absolute probability density (not normalised
    to 1 over the screen; normalisation is handled at the histogram level).
    """
    y_L = -slit_separation / 2.0
    y_R = +slit_separation / 2.0
    A_L = slit_amplitude(y, y_L, slit_width, wavelength, screen_distance)
    A_R = slit_amplitude(y, y_R, slit_width, wavelength, screen_distance)
    psi_total = A_L + A_R
    return abs(psi_total) ** 2


def decohered_probability(
    y: float,
    slit_separation: float,
    slit_width: float,
    wavelength: float,
    screen_distance: float,
) -> float:
    """P(y) for fully decohered (which-path measured) two-slit case.

    P = |A_L(y)|² + |A_R(y)|²   (incoherent sum)

    Equivalent to γ=1 in the partial decoherence formula.
    """
    y_L = -slit_separation / 2.0
    y_R = +slit_separation / 2.0
    A_L = slit_amplitude(y, y_L, slit_width, wavelength, screen_distance)
    A_R = slit_amplitude(y, y_R, slit_width, wavelength, screen_distance)
    return abs(A_L) ** 2 + abs(A_R) ** 2


def partial_decoherence_probability(
    y: float,
    slit_separation: float,
    slit_width: float,
    wavelength: float,
    screen_distance: float,
    gamma: float,
) -> float:
    """P(y) with partial decoherence parameter γ ∈ [0.0, 1.0].

    P(y) = |A_L|² + |A_R|² + 2·(1-γ)·Re(A_L · A_R*)

    γ = 0  → fully coherent:  includes full interference cross-term
    γ = 1  → fully decohered: incoherent sum (no cross-term)
    0<γ<1  → partial coherence: reduced but non-zero fringe visibility

    Parameters
    ----------
    gamma : float
        Decoherence strength in [0.0, 1.0].
    """
    if not (0.0 <= gamma <= 1.0):
        raise ValueError(f"gamma must be in [0, 1]; got {gamma}")

    y_L = -slit_separation / 2.0
    y_R = +slit_separation / 2.0
    A_L = slit_amplitude(y, y_L, slit_width, wavelength, screen_distance)
    A_R = slit_amplitude(y, y_R, slit_width, wavelength, screen_distance)

    diagonal = abs(A_L) ** 2 + abs(A_R) ** 2
    cross_term = 2.0 * (1.0 - gamma) * (A_L * A_R.conjugate()).real

    p = diagonal + cross_term
    # Clamp to avoid tiny negative values from floating-point error
    return max(p, 0.0)


def one_slit_probability(
    y: float,
    slit_width: float,
    wavelength: float,
    screen_distance: float,
) -> float:
    """P(y) for single-slit diffraction only (slit at y=0)."""
    A = slit_amplitude(y, 0.0, slit_width, wavelength, screen_distance)
    return abs(A) ** 2


# ---------------------------------------------------------------------------
# Profile computation
# ---------------------------------------------------------------------------

def compute_probability_profile(
    condition: QSlitCondition,
    screen_positions: List[float],
    slit_separation: float,
    slit_width: float,
    wavelength: float,
    screen_distance: float,
    decoherence_gamma: float = 0.0,
) -> List[float]:
    """Compute probability (unnormalised) at each screen position.

    Returns a list aligned with ``screen_positions``.
    """
    probs: List[float] = []
    for y in screen_positions:
        if condition == QSlitCondition.ONE_SLIT:
            p = one_slit_probability(y, slit_width, wavelength, screen_distance)
        elif condition == QSlitCondition.TWO_SLIT_COHERENT:
            p = coherent_probability(y, slit_separation, slit_width, wavelength, screen_distance)
        elif condition == QSlitCondition.TWO_SLIT_DECOHERED:
            p = decohered_probability(y, slit_separation, slit_width, wavelength, screen_distance)
        elif condition == QSlitCondition.TWO_SLIT_PARTIAL:
            p = partial_decoherence_probability(
                y, slit_separation, slit_width, wavelength, screen_distance, decoherence_gamma
            )
        else:
            raise ValueError(f"Unknown condition: {condition!r}")
        probs.append(p)
    return probs


# ---------------------------------------------------------------------------
# Born-rule sampling
# ---------------------------------------------------------------------------

def born_sample(
    probabilities: List[float],
    n_trials: int,
    seed: int = 0,
) -> List[int]:
    """Sample integer hit counts from probability distribution (Born rule).

    Uses seeded multinomial sampling.

    Parameters
    ----------
    probabilities : list of float
        Unnormalised probability weights (must not all be zero).
    n_trials : int
        Total number of particles/photons to distribute.
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    list of int
        Hit counts per bin, summing to n_trials.
    """
    rng = random.Random(seed)
    n = len(probabilities)
    total = sum(probabilities)
    if total <= 0:
        return [0] * n

    # Build CDF
    cumulative: List[float] = []
    acc = 0.0
    for p in probabilities:
        acc += p / total
        cumulative.append(acc)
    cumulative[-1] = 1.0  # ensure last bin catches all

    hits = [0] * n
    for _ in range(n_trials):
        r = rng.random()
        lo, hi = 0, n - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if cumulative[mid] < r:
                lo = mid + 1
            else:
                hi = mid
        hits[lo] += 1
    return hits


# ---------------------------------------------------------------------------
# Main run functions
# ---------------------------------------------------------------------------

def run_condition(
    condition: QSlitCondition,
    n_trials: int = DEFAULT_N_TRIALS,
    slit_separation: float = DEFAULT_SLIT_SEPARATION,
    slit_width: float = DEFAULT_SLIT_WIDTH,
    wavelength: float = DEFAULT_WAVELENGTH,
    screen_distance: float = DEFAULT_SCREEN_DISTANCE,
    screen_width: float = DEFAULT_SCREEN_WIDTH,
    n_bins: int = DEFAULT_N_BINS,
    decoherence_gamma: float = DEFAULT_DECOHERENCE,
    seed: int = 0,
) -> Dict[str, Any]:
    """Run one experimental condition and return results dict.

    Returns
    -------
    dict with keys:
        condition, decoherence_gamma, params,
        screen_positions, probability_profile, hit_counts,
        n_trials, seed, summary
    """
    if n_bins < 2:
        raise ValueError("n_bins must be >= 2")

    step = (2.0 * screen_width) / (n_bins - 1)
    screen_positions = [
        round(-screen_width + i * step, 8)
        for i in range(n_bins)
    ]

    probs = compute_probability_profile(
        condition=condition,
        screen_positions=screen_positions,
        slit_separation=slit_separation,
        slit_width=slit_width,
        wavelength=wavelength,
        screen_distance=screen_distance,
        decoherence_gamma=decoherence_gamma,
    )

    hits = born_sample(probs, n_trials, seed=seed)

    total_hits = sum(hits)
    center_bin = n_bins // 2
    center_prob = probs[center_bin]
    max_prob = max(probs)
    min_prob = min(probs)
    peak_bin = probs.index(max_prob)

    # Fringe visibility from probability profile
    denom = max_prob + min_prob
    visibility = (max_prob - min_prob) / denom if denom > 0 else 0.0

    summary: Dict[str, Any] = {
        "condition": str(condition),
        "decoherence_gamma": decoherence_gamma,
        "n_trials": n_trials,
        "seed": seed,
        "total_hits": total_hits,
        "center_prob": round(center_prob, 8),
        "max_prob": round(max_prob, 8),
        "min_prob": round(min_prob, 8),
        "peak_bin": peak_bin,
        "center_bin": center_bin,
        "fringe_visibility": round(visibility, 8),
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
        "decoherence_gamma": decoherence_gamma,
        "seed": seed,
    }

    return {
        "condition": str(condition),
        "decoherence_gamma": decoherence_gamma,
        "params": params,
        "screen_positions": screen_positions,
        "probability_profile": [round(p, 10) for p in probs],
        "hit_counts": hits,
        "n_trials": n_trials,
        "seed": seed,
        "summary": summary,
    }


def run_decoherence_sweep(
    gamma_values: Optional[List[float]] = None,
    n_trials: int = DEFAULT_N_TRIALS,
    slit_separation: float = DEFAULT_SLIT_SEPARATION,
    slit_width: float = DEFAULT_SLIT_WIDTH,
    wavelength: float = DEFAULT_WAVELENGTH,
    screen_distance: float = DEFAULT_SCREEN_DISTANCE,
    screen_width: float = DEFAULT_SCREEN_WIDTH,
    n_bins: int = DEFAULT_N_BINS,
    seed: int = 0,
) -> List[Dict[str, Any]]:
    """Run TWO_SLIT_PARTIAL across a range of gamma values.

    Returns a list of result dicts ordered by gamma (ascending).
    """
    gammas = gamma_values or [0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0]
    return [
        run_condition(
            QSlitCondition.TWO_SLIT_PARTIAL,
            n_trials=n_trials,
            slit_separation=slit_separation,
            slit_width=slit_width,
            wavelength=wavelength,
            screen_distance=screen_distance,
            screen_width=screen_width,
            n_bins=n_bins,
            decoherence_gamma=g,
            seed=seed,
        )
        for g in gammas
    ]


def run_all_conditions(
    n_trials: int = DEFAULT_N_TRIALS,
    slit_separation: float = DEFAULT_SLIT_SEPARATION,
    slit_width: float = DEFAULT_SLIT_WIDTH,
    wavelength: float = DEFAULT_WAVELENGTH,
    screen_distance: float = DEFAULT_SCREEN_DISTANCE,
    screen_width: float = DEFAULT_SCREEN_WIDTH,
    n_bins: int = DEFAULT_N_BINS,
    seed: int = 0,
    partial_gammas: Optional[List[float]] = None,
) -> Dict[str, Any]:
    """Run the four required conditions for the audit benchmark.

    Returns
    -------
    dict with keys:
        one_slit, two_slit_coherent, two_slit_decohered,
        decoherence_sweep  (list ordered by gamma)
    """
    partial_gammas = partial_gammas or [0.0, 0.25, 0.5, 0.75, 1.0]
    kwargs = dict(
        n_trials=n_trials,
        slit_separation=slit_separation,
        slit_width=slit_width,
        wavelength=wavelength,
        screen_distance=screen_distance,
        screen_width=screen_width,
        n_bins=n_bins,
        seed=seed,
    )
    return {
        "one_slit": run_condition(QSlitCondition.ONE_SLIT, **kwargs),
        "two_slit_coherent": run_condition(QSlitCondition.TWO_SLIT_COHERENT, **kwargs),
        "two_slit_decohered": run_condition(QSlitCondition.TWO_SLIT_DECOHERED, **kwargs),
        "decoherence_sweep": run_decoherence_sweep(gamma_values=partial_gammas, **kwargs),
    }
