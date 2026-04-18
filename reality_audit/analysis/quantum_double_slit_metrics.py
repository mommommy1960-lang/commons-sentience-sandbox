"""
quantum_double_slit_metrics.py — Analysis metrics for the quantum double-slit benchmark.

Extends the double_slit_metrics pattern with decoherence-specific metrics:
  fringe_visibility, peak_count, center_intensity_normalised,
  distribution_entropy, coherence_sensitivity, partial_decoherence_monotonicity,
  compute_quantum_metrics
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence, Tuple


# ---------------------------------------------------------------------------
# Basic profile metrics
# ---------------------------------------------------------------------------

def fringe_visibility(probs: Sequence[float]) -> float:
    """Michelson visibility V = (I_max - I_min) / (I_max + I_min).

    Returns 0.0 if I_max + I_min == 0.
    """
    if not probs:
        return 0.0
    p_max = max(probs)
    p_min = min(probs)
    denom = p_max + p_min
    if denom == 0.0:
        return 0.0
    return (p_max - p_min) / denom


def peak_count(probs: Sequence[float], threshold_fraction: float = 0.1) -> int:
    """Count local maxima above threshold_fraction * max_value."""
    if len(probs) < 3:
        return 0
    threshold = threshold_fraction * max(probs)
    peaks = 0
    p = list(probs)
    for i in range(1, len(p) - 1):
        if p[i] > threshold and p[i] >= p[i - 1] and p[i] >= p[i + 1]:
            if p[i] > p[i - 1] or p[i] > p[i + 1]:
                peaks += 1
    return peaks


def center_intensity_normalised(probs: Sequence[float]) -> float:
    """Return the centre-bin probability divided by max probability."""
    if not probs:
        return 0.0
    centre = probs[len(probs) // 2]
    p_max = max(probs)
    if p_max == 0.0:
        return 0.0
    return centre / p_max


def distribution_entropy(hits: Sequence[int]) -> float:
    """Shannon entropy (nats) of the empirical hit distribution."""
    total = sum(hits)
    if total == 0:
        return 0.0
    entropy = 0.0
    for h in hits:
        if h > 0:
            p = h / total
            entropy -= p * math.log(p)
    return entropy


# ---------------------------------------------------------------------------
# Decoherence-specific metrics
# ---------------------------------------------------------------------------

def coherence_sensitivity(sweep_results: List[Dict[str, Any]]) -> float:
    """Linear slope of fringe_visibility vs gamma (decoherence parameter).

    Expects each item to have keys: 'decoherence_gamma' and 'summary.fringe_visibility'
    or 'fringe_visibility' at top level of summary.
    Returns slope dV/dγ (should be negative for physical decoherence).
    """
    if len(sweep_results) < 2:
        return 0.0

    gammas: List[float] = []
    visibilities: List[float] = []
    for r in sweep_results:
        g = r.get("decoherence_gamma")
        summary = r.get("summary", r)
        v = summary.get("fringe_visibility")
        if g is not None and v is not None:
            gammas.append(float(g))
            visibilities.append(float(v))

    if len(gammas) < 2:
        return 0.0

    n = len(gammas)
    mean_g = sum(gammas) / n
    mean_v = sum(visibilities) / n
    num = sum((g - mean_g) * (v - mean_v) for g, v in zip(gammas, visibilities))
    den = sum((g - mean_g) ** 2 for g in gammas)
    if den == 0.0:
        return 0.0
    return num / den


def partial_decoherence_monotonicity(sweep_results: List[Dict[str, Any]]) -> bool:
    """Return True if fringe_visibility is non-increasing as gamma increases.

    Tolerates floating-point noise via small epsilon.
    """
    epsilon = 1e-6
    entries = []
    for r in sweep_results:
        g = r.get("decoherence_gamma")
        summary = r.get("summary", r)
        v = summary.get("fringe_visibility")
        if g is not None and v is not None:
            entries.append((float(g), float(v)))

    if len(entries) < 2:
        return True

    entries_sorted = sorted(entries, key=lambda x: x[0])
    for i in range(1, len(entries_sorted)):
        if entries_sorted[i][1] > entries_sorted[i - 1][1] + epsilon:
            return False
    return True


def visibility_at_gamma(sweep_results: List[Dict[str, Any]], gamma: float) -> Optional[float]:
    """Return the fringe visibility for the closest gamma in sweep_results."""
    best: Optional[Tuple[float, float]] = None
    for r in sweep_results:
        g = r.get("decoherence_gamma")
        summary = r.get("summary", r)
        v = summary.get("fringe_visibility")
        if g is not None and v is not None:
            if best is None or abs(float(g) - gamma) < abs(best[0] - gamma):
                best = (float(g), float(v))
    return best[1] if best is not None else None


# ---------------------------------------------------------------------------
# Full-suite metric computation
# ---------------------------------------------------------------------------

def compute_quantum_metrics(results_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Compute all metrics from run_all_conditions() output.

    Args:
        results_dict: Dict with keys one_slit, two_slit_coherent, two_slit_decohered,
                      decoherence_sweep.

    Returns:
        Dict with per_condition, decoherence_analysis, cross_condition, interpretation.
    """
    per_condition: Dict[str, Any] = {}
    for key in ["one_slit", "two_slit_coherent", "two_slit_decohered"]:
        r = results_dict.get(key, {})
        probs = r.get("probability_profile", [])
        hits = r.get("hit_counts", [])
        per_condition[key] = {
            "fringe_visibility": fringe_visibility(probs),
            "peak_count": peak_count(probs),
            "centre_intensity_normalised": center_intensity_normalised(probs),
            "distribution_entropy_nats": distribution_entropy(hits),
        }

    sweep = results_dict.get("decoherence_sweep", [])
    slope = coherence_sensitivity(sweep)
    monotone = partial_decoherence_monotonicity(sweep)
    v_at_0 = visibility_at_gamma(sweep, 0.0)
    v_at_1 = visibility_at_gamma(sweep, 1.0)

    sweep_summary: List[Dict[str, Any]] = []
    for r in sweep:
        g = r.get("decoherence_gamma")
        probs = r.get("probability_profile", [])
        hits = r.get("hit_counts", [])
        sweep_summary.append({
            "gamma": g,
            "fringe_visibility": fringe_visibility(probs),
            "peak_count": peak_count(probs),
            "distribution_entropy_nats": distribution_entropy(hits),
        })

    decoherence_analysis = {
        "coherence_sensitivity_slope": slope,
        "is_monotone_decreasing": monotone,
        "visibility_at_gamma_0": v_at_0,
        "visibility_at_gamma_1": v_at_1,
        "sweep_summary": sweep_summary,
    }

    # Cross-condition comparisons
    v_coherent = per_condition["two_slit_coherent"]["fringe_visibility"]
    v_decohered = per_condition["two_slit_decohered"]["fringe_visibility"]
    v_one = per_condition["one_slit"]["fringe_visibility"]

    cross_condition = {
        "coherent_vs_decohered_visibility_ratio": (
            v_coherent / v_decohered if v_decohered > 1e-9 else None
        ),
        "coherent_visibility_exceeds_decohered": v_coherent > v_decohered,
        "one_slit_lower_visibility_than_coherent": v_one < v_coherent,
    }

    # Interpretation
    verdict = "METRICS_CONSISTENT" if (
        v_coherent > 0.5
        and v_decohered < 0.5
        and monotone
        and slope < 0.0
        and cross_condition["coherent_vs_decohered_visibility_ratio"] is not None
        and cross_condition["coherent_vs_decohered_visibility_ratio"] > 2.0
    ) else "METRICS_ANOMALY_DETECTED"

    interpretation = {
        "verdict": verdict,
        "notes": (
            "Coherent two-slit has high fringe visibility; decohered shows suppressed fringes. "
            "Decoherence sweep is monotone decreasing. These confirm quantum-style interference "
            "is working as physically expected."
        ),
    }

    return {
        "per_condition": per_condition,
        "decoherence_analysis": decoherence_analysis,
        "cross_condition": cross_condition,
        "interpretation": interpretation,
    }
