"""
advanced_quantum_double_slit.py — Advanced which-path / quantum eraser benchmark.

UPGRADE OVER quantum_double_slit.py
------------------------------------
The previous module introduced decoherence via a phenomenological γ parameter.
This module is more physically faithful:

  - Explicit path-detector entangled state |Ψ⟩ = (1/√2)(|L⟩|d_L⟩ + |R⟩|d_R⟩)
  - Detector states |d_L⟩, |d_R⟩ with real overlap s = ⟨d_L|d_R⟩ ∈ [0, 1]
  - Marginal screen probability obtained by tracing over the detector
  - Optional quantum eraser: post-select on |±⟩ = (|d_L⟩ ± |d_R⟩)/√(2±2s)
  - Path distinguishability D = √(1 − s²), V_theoretical = s
  - Exact complementarity: V_theoretical² + D² = 1 (pure state, equal slits)

PHYSICAL MODEL
--------------
Full entangled state (unnormalised):

    |Ψ⟩ = A_L(y)|L⟩|d_L⟩ + A_R(y)|R⟩|d_R⟩

Marginal screen probability (tracing out detector):

    P(y) = ½(|A_L|² + |A_R|² + 2s·Re(A_L · A_R*))

where s = ⟨d_L|d_R⟩ is the detector overlap parameter.

Eraser probabilities (post-select on ±):

    P(y|+) ∝ ((1+s)/2)·|A_L + A_R|²   ← restores coherent fringes
    P(y|−) ∝ ((1-s)/2)·|A_L − A_R|²   ← anti-fringes (dark at y=0)

The screen amplitudes A_L, A_R are Fraunhofer far-field complex amplitudes
(same formulation as quantum_double_slit.py).

RELATIONSHIP TO PREVIOUS MODEL
-------------------------------
The detector overlap s maps to the decoherence parameter from the prior
module: s = 1 − γ.  However this module explicitly maintains the
path-detector state, enabling the eraser conditions and the precise
complementarity checks.

LIMITATIONS
-----------
- Exact Fraunhofer far-field approximation only.
- Detector modelled as a two-state system (pure overlap parameter).
- No Lindblad dynamics; decoherence is via partial-trace of static state.
- Single-particle, single-mode.
- Eraser is ideal (perfect post-selection, no timing jitter).
- Not a full quantum computer simulation.
"""

from __future__ import annotations

import cmath
import math
from enum import Enum
from typing import Any, Dict, List, Optional

from reality_audit.benchmarks.quantum_double_slit import (
    slit_amplitude,
    born_sample,
    DEFAULT_SLIT_SEPARATION,
    DEFAULT_SLIT_WIDTH,
    DEFAULT_WAVELENGTH,
    DEFAULT_SCREEN_DISTANCE,
    DEFAULT_SCREEN_WIDTH,
    DEFAULT_N_BINS,
    DEFAULT_N_TRIALS,
)


# ---------------------------------------------------------------------------
# Condition enum
# ---------------------------------------------------------------------------

class AQCondition(str, Enum):
    ONE_SLIT           = "one_slit"
    TWO_SLIT_COHERENT  = "two_slit_coherent"    # s = 1.0
    TWO_SLIT_PARTIAL   = "two_slit_partial"      # 0 < s < 1  (uses detector_overlap)
    TWO_SLIT_WHICH_PATH = "two_slit_which_path"  # s = 0.0 (D = 1)
    ERASER_PLUS        = "eraser_plus"           # post-select |+⟩
    ERASER_MINUS       = "eraser_minus"          # post-select |−⟩


# ---------------------------------------------------------------------------
# Default parameters
# ---------------------------------------------------------------------------

DEFAULT_DETECTOR_OVERLAP   = 0.5   # partial distinguishability for eraser runs
DEFAULT_OVERLAP_SWEEP      = [1.0, 0.9, 0.75, 0.5, 0.25, 0.1, 0.0]


# ---------------------------------------------------------------------------
# Core probability formulas
# ---------------------------------------------------------------------------

def marginal_probability(
    y: float,
    detector_overlap: float,
    slit_separation: float,
    slit_width: float,
    wavelength: float,
    screen_distance: float,
) -> float:
    """P(y) after tracing detector:  ½(|A_L|² + |A_R|²) + s·Re(A_L·A_R*).

    Parameters
    ----------
    detector_overlap : float
        s = ⟨d_L|d_R⟩ ∈ [0, 1].  s=1 → coherent; s=0 → which-path.
    """
    if not (0.0 <= detector_overlap <= 1.0):
        raise ValueError(f"detector_overlap must be in [0, 1]; got {detector_overlap}")
    s = float(detector_overlap)
    y_L = -slit_separation / 2.0
    y_R = +slit_separation / 2.0
    A_L = slit_amplitude(y, y_L, slit_width, wavelength, screen_distance)
    A_R = slit_amplitude(y, y_R, slit_width, wavelength, screen_distance)
    diagonal = (abs(A_L) ** 2 + abs(A_R) ** 2) / 2.0
    cross = s * (A_L * A_R.conjugate()).real
    return max(diagonal + cross, 0.0)


def eraser_probability(
    y: float,
    detector_overlap: float,
    slit_separation: float,
    slit_width: float,
    wavelength: float,
    screen_distance: float,
    eraser_sign: int = +1,
) -> float:
    """Conditional P(y | eraser outcome) after post-selecting on |±⟩.

    |+⟩ = (|d_L⟩ + |d_R⟩) / √(2+2s)  → restores constructive fringes
    |−⟩ = (|d_L⟩ − |d_R⟩) / √(2−2s)  → produces anti-fringes

    P(y|+) ∝ ((1+s)/2)·|A_L + A_R|²
    P(y|−) ∝ ((1−s)/2)·|A_L − A_R|²

    Parameters
    ----------
    eraser_sign : int
        +1 for |+⟩ post-selection, -1 for |−⟩.
    """
    if eraser_sign not in (+1, -1):
        raise ValueError("eraser_sign must be +1 or -1")
    s = float(detector_overlap)
    y_L = -slit_separation / 2.0
    y_R = +slit_separation / 2.0
    A_L = slit_amplitude(y, y_L, slit_width, wavelength, screen_distance)
    A_R = slit_amplitude(y, y_R, slit_width, wavelength, screen_distance)
    if eraser_sign == +1:
        amplitude = A_L + A_R
        weight = (1.0 + s) / 2.0
    else:
        amplitude = A_L - A_R
        weight = max((1.0 - s) / 2.0, 0.0)
    return max(weight * abs(amplitude) ** 2, 0.0)


def one_slit_probability(
    y: float,
    slit_width: float,
    wavelength: float,
    screen_distance: float,
) -> float:
    """P(y) for single slit at y=0."""
    A = slit_amplitude(y, 0.0, slit_width, wavelength, screen_distance)
    return abs(A) ** 2


# ---------------------------------------------------------------------------
# Complementarity quantities
# ---------------------------------------------------------------------------

def path_distinguishability(detector_overlap: float) -> float:
    """D = √(1 − s²) — quantum information-theoretic path distinguishability."""
    s = float(detector_overlap)
    return math.sqrt(max(1.0 - s ** 2, 0.0))


def theoretical_max_visibility(detector_overlap: float) -> float:
    """V_theoretical = s — maximum fringe visibility for this detector overlap.

    Holds for equal-amplitude, far-field, sinc≈1 case.
    Complementarity: V_theoretical² + D² = 1 (exactly, for pure state).
    """
    return float(detector_overlap)


def complementarity_bound_check(detector_overlap: float) -> Dict[str, float]:
    """Verify V_theoretical² + D² = 1 (should be exactly satisfied)."""
    s = float(detector_overlap)
    V = theoretical_max_visibility(s)
    D = path_distinguishability(s)
    lhs = V ** 2 + D ** 2
    return {
        "detector_overlap": s,
        "V_theoretical": V,
        "path_distinguishability": D,
        "V2_plus_D2": lhs,
        "complementarity_satisfied": abs(lhs - 1.0) < 1e-10,
    }


# ---------------------------------------------------------------------------
# Profile computation
# ---------------------------------------------------------------------------

def compute_profile(
    condition: AQCondition,
    screen_positions: List[float],
    slit_separation: float,
    slit_width: float,
    wavelength: float,
    screen_distance: float,
    detector_overlap: float = 1.0,
) -> List[float]:
    """Compute unnormalised probability at each screen bin."""
    probs: List[float] = []
    for y in screen_positions:
        if condition == AQCondition.ONE_SLIT:
            p = one_slit_probability(y, slit_width, wavelength, screen_distance)
        elif condition == AQCondition.TWO_SLIT_COHERENT:
            p = marginal_probability(y, 1.0, slit_separation, slit_width, wavelength, screen_distance)
        elif condition == AQCondition.TWO_SLIT_WHICH_PATH:
            p = marginal_probability(y, 0.0, slit_separation, slit_width, wavelength, screen_distance)
        elif condition == AQCondition.TWO_SLIT_PARTIAL:
            p = marginal_probability(y, detector_overlap, slit_separation, slit_width, wavelength, screen_distance)
        elif condition == AQCondition.ERASER_PLUS:
            p = eraser_probability(y, detector_overlap, slit_separation, slit_width, wavelength, screen_distance, +1)
        elif condition == AQCondition.ERASER_MINUS:
            p = eraser_probability(y, detector_overlap, slit_separation, slit_width, wavelength, screen_distance, -1)
        else:
            raise ValueError(f"Unknown condition: {condition!r}")
        probs.append(p)
    return probs


# ---------------------------------------------------------------------------
# Single condition run
# ---------------------------------------------------------------------------

def run_condition(
    condition: AQCondition,
    n_trials: int = DEFAULT_N_TRIALS,
    slit_separation: float = DEFAULT_SLIT_SEPARATION,
    slit_width: float = DEFAULT_SLIT_WIDTH,
    wavelength: float = DEFAULT_WAVELENGTH,
    screen_distance: float = DEFAULT_SCREEN_DISTANCE,
    screen_width: float = DEFAULT_SCREEN_WIDTH,
    n_bins: int = DEFAULT_N_BINS,
    detector_overlap: float = DEFAULT_DETECTOR_OVERLAP,
    seed: int = 0,
) -> Dict[str, Any]:
    """Run one condition and return full result dict."""
    if n_bins < 2:
        raise ValueError("n_bins must be >= 2")

    step = (2.0 * screen_width) / (n_bins - 1)
    screen_positions = [round(-screen_width + i * step, 8) for i in range(n_bins)]

    probs = compute_profile(
        condition=condition,
        screen_positions=screen_positions,
        slit_separation=slit_separation,
        slit_width=slit_width,
        wavelength=wavelength,
        screen_distance=screen_distance,
        detector_overlap=detector_overlap,
    )

    hits = born_sample(probs, n_trials, seed=seed)

    p_max = max(probs)
    p_min = min(probs)
    denom = p_max + p_min
    fringe_vis = (p_max - p_min) / denom if denom > 0 else 0.0

    D = path_distinguishability(
        detector_overlap if condition not in (AQCondition.TWO_SLIT_COHERENT, AQCondition.ONE_SLIT) else
        (0.0 if condition == AQCondition.TWO_SLIT_COHERENT else float("nan"))
    )
    # Resolve effective detector_overlap for summary
    eff_overlap = {
        AQCondition.ONE_SLIT: float("nan"),
        AQCondition.TWO_SLIT_COHERENT: 1.0,
        AQCondition.TWO_SLIT_WHICH_PATH: 0.0,
    }.get(condition, detector_overlap)

    return {
        "condition": str(condition),
        "detector_overlap": eff_overlap,
        "path_distinguishability": path_distinguishability(eff_overlap) if not math.isnan(eff_overlap) else float("nan"),
        "params": {
            "slit_separation": slit_separation,
            "slit_width": slit_width,
            "wavelength": wavelength,
            "screen_distance": screen_distance,
            "screen_width": screen_width,
            "n_bins": n_bins,
        },
        "screen_positions": screen_positions,
        "probability_profile": probs,
        "hit_counts": hits,
        "n_trials": n_trials,
        "seed": seed,
        "summary": {
            "condition": str(condition),
            "detector_overlap": eff_overlap,
            "path_distinguishability": path_distinguishability(eff_overlap) if not math.isnan(eff_overlap) else float("nan"),
            "fringe_visibility": fringe_vis,
            "theoretical_max_visibility": theoretical_max_visibility(eff_overlap) if not math.isnan(eff_overlap) else float("nan"),
            "n_trials": n_trials,
            "seed": seed,
            "total_hits": sum(hits),
        },
    }


# ---------------------------------------------------------------------------
# Overlap sweep
# ---------------------------------------------------------------------------

def run_overlap_sweep(
    overlap_values: Optional[List[float]] = None,
    n_trials: int = DEFAULT_N_TRIALS,
    slit_separation: float = DEFAULT_SLIT_SEPARATION,
    slit_width: float = DEFAULT_SLIT_WIDTH,
    wavelength: float = DEFAULT_WAVELENGTH,
    screen_distance: float = DEFAULT_SCREEN_DISTANCE,
    screen_width: float = DEFAULT_SCREEN_WIDTH,
    n_bins: int = DEFAULT_N_BINS,
    seed: int = 0,
) -> List[Dict[str, Any]]:
    """Run TWO_SLIT_PARTIAL for each detector overlap value."""
    values = overlap_values if overlap_values is not None else DEFAULT_OVERLAP_SWEEP
    results = []
    for s in values:
        r = run_condition(
            AQCondition.TWO_SLIT_PARTIAL,
            n_trials=n_trials,
            slit_separation=slit_separation,
            slit_width=slit_width,
            wavelength=wavelength,
            screen_distance=screen_distance,
            screen_width=screen_width,
            n_bins=n_bins,
            detector_overlap=s,
            seed=seed,
        )
        results.append(r)
    return results


# ---------------------------------------------------------------------------
# All conditions
# ---------------------------------------------------------------------------

def run_all_conditions(
    n_trials: int = DEFAULT_N_TRIALS,
    slit_separation: float = DEFAULT_SLIT_SEPARATION,
    slit_width: float = DEFAULT_SLIT_WIDTH,
    wavelength: float = DEFAULT_WAVELENGTH,
    screen_distance: float = DEFAULT_SCREEN_DISTANCE,
    screen_width: float = DEFAULT_SCREEN_WIDTH,
    n_bins: int = DEFAULT_N_BINS,
    seed: int = 0,
    eraser_overlap: float = 0.5,
    overlap_values: Optional[List[float]] = None,
) -> Dict[str, Any]:
    """Run all benchmark conditions.

    Returns dict with keys:
        one_slit, two_slit_coherent, two_slit_which_path,
        eraser_plus, eraser_minus, overlap_sweep
    """
    kwargs = dict(
        n_trials=n_trials, slit_separation=slit_separation,
        slit_width=slit_width, wavelength=wavelength,
        screen_distance=screen_distance, screen_width=screen_width,
        n_bins=n_bins, seed=seed,
    )
    return {
        "one_slit": run_condition(AQCondition.ONE_SLIT, **kwargs),
        "two_slit_coherent": run_condition(AQCondition.TWO_SLIT_COHERENT, **kwargs),
        "two_slit_which_path": run_condition(AQCondition.TWO_SLIT_WHICH_PATH, **kwargs),
        "eraser_plus": run_condition(AQCondition.ERASER_PLUS, detector_overlap=eraser_overlap, **kwargs),
        "eraser_minus": run_condition(AQCondition.ERASER_MINUS, detector_overlap=eraser_overlap, **kwargs),
        "overlap_sweep": run_overlap_sweep(overlap_values=overlap_values, **kwargs),
    }
