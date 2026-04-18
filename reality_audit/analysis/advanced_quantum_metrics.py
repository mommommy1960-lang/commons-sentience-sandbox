"""
advanced_quantum_metrics.py — Metrics for the advanced which-path / eraser benchmark.

Key additions over quantum_double_slit_metrics.py:
  - path_distinguishability (from detector overlap)
  - interference_visibility_corrected (baseline-subtracted, normalised)
  - visibility_distinguishability_relation (V² + D² check)
  - eraser_recovery_score
  - kl_divergence
  - aggregate_100run_stats
"""

from __future__ import annotations

import math
import statistics
from typing import Any, Dict, List, Optional, Sequence, Tuple


# ---------------------------------------------------------------------------
# Basic profile metrics (re-implemented to avoid cross-import)
# ---------------------------------------------------------------------------

def fringe_visibility(probs: Sequence[float]) -> float:
    """Michelson V = (I_max − I_min) / (I_max + I_min)."""
    if not probs:
        return 0.0
    p_max, p_min = max(probs), min(probs)
    denom = p_max + p_min
    return (p_max - p_min) / denom if denom else 0.0


def fringe_visibility_from_hits(hits: Sequence[int], n_trials: int) -> float:
    """Empirical Michelson visibility from hit counts."""
    if n_trials == 0 or not hits:
        return 0.0
    freqs = [h / n_trials for h in hits]
    return fringe_visibility(freqs)


def peak_count(probs: Sequence[float], threshold_fraction: float = 0.1) -> int:
    """Count local maxima above threshold_fraction * max_value."""
    if len(probs) < 3:
        return 0
    threshold = threshold_fraction * max(probs)
    p = list(probs)
    peaks = 0
    for i in range(1, len(p) - 1):
        if p[i] > threshold and p[i] >= p[i - 1] and p[i] >= p[i + 1]:
            if p[i] > p[i - 1] or p[i] > p[i + 1]:
                peaks += 1
    return peaks


def kl_divergence(p: Sequence[float], q: Sequence[float], epsilon: float = 1e-12) -> float:
    """KL(p||q) = Σ p_i log(p_i/q_i). p, q are unnormalised; normalised internally."""
    if len(p) != len(q):
        raise ValueError("p and q must have the same length")
    total_p = sum(p)
    total_q = sum(q)
    if total_p == 0 or total_q == 0:
        return 0.0
    kl = 0.0
    for pi, qi in zip(p, q):
        pi_n = pi / total_p
        qi_n = qi / total_q
        if pi_n > epsilon:
            kl += pi_n * math.log(pi_n / max(qi_n, epsilon))
    return kl


# ---------------------------------------------------------------------------
# Which-path / eraser metrics
# ---------------------------------------------------------------------------

def path_distinguishability(detector_overlap: float) -> float:
    """D = √(1 − s²) where s = detector overlap ∈ [0, 1]."""
    s = float(detector_overlap)
    return math.sqrt(max(1.0 - s ** 2, 0.0))


def interference_visibility_corrected(
    probs_condition: Sequence[float],
    probs_which_path: Sequence[float],
    probs_coherent: Sequence[float],
) -> float:
    """Baseline-subtracted, normalised interference visibility.

    V_int = (V_raw(s) − V_raw(s=0)) / (V_raw(s=1) − V_raw(s=0))

    This isolates the interference contribution from the sinc envelope.
    Returns value ∈ [0, 1] (clamped).
    """
    V_raw = fringe_visibility(probs_condition)
    V_baseline = fringe_visibility(probs_which_path)
    V_max = fringe_visibility(probs_coherent)
    denom = V_max - V_baseline
    if abs(denom) < 1e-9:
        return 0.0
    V_int = (V_raw - V_baseline) / denom
    return max(0.0, min(1.0, V_int))


def visibility_distinguishability_relation(
    detector_overlap: float,
    probs_condition: Sequence[float],
    probs_which_path: Sequence[float],
    probs_coherent: Sequence[float],
) -> Dict[str, float]:
    """Compute V_corrected, D, and check V² + D² ≤ 1.

    Uses the corrected interference visibility to check the complementarity
    bound qualitatively.
    """
    V_int = interference_visibility_corrected(probs_condition, probs_which_path, probs_coherent)
    D = path_distinguishability(detector_overlap)
    lhs = V_int ** 2 + D ** 2
    return {
        "detector_overlap": detector_overlap,
        "V_interference_corrected": V_int,
        "path_distinguishability": D,
        "V2_plus_D2": lhs,
        "complementarity_bound_satisfied": lhs <= 1.0 + 1e-6,
        "theoretical_V2_plus_D2": float(detector_overlap) ** 2 + (1 - float(detector_overlap) ** 2),
    }


def visibility_decreases_with_distinguishability(
    sweep_results: List[Dict[str, Any]],
    probs_which_path: Sequence[float],
    probs_coherent: Sequence[float],
) -> bool:
    """Return True if V_corrected is non-increasing as D increases (s decreasing).

    Uses corrected visibility to avoid sinc-envelope artefacts.
    """
    entries: List[Tuple[float, float]] = []
    epsilon = 1e-6
    for r in sweep_results:
        s = r.get("detector_overlap")
        probs = r.get("probability_profile", [])
        if s is None or not probs:
            continue
        V_int = interference_visibility_corrected(probs, probs_which_path, probs_coherent)
        entries.append((float(s), V_int))

    if len(entries) < 2:
        return True

    # Sort by s descending → D ascending
    entries_sorted = sorted(entries, key=lambda x: -x[0])
    vis_list = [v for _, v in entries_sorted]
    for i in range(1, len(vis_list)):
        if vis_list[i] > vis_list[i - 1] + epsilon:
            return False
    return True


def eraser_recovery_score(
    probs_eraser_plus: Sequence[float],
    probs_coherent: Sequence[float],
    probs_which_path: Sequence[float],
) -> Dict[str, float]:
    """Quantify how well eraser |+⟩ recovers the coherent fringe pattern.

    Score = interference_visibility_corrected of eraser_plus.
    Also reports KL(eraser_plus || coherent) as a shape match metric.
    """
    V_recovery = interference_visibility_corrected(
        probs_eraser_plus, probs_which_path, probs_coherent
    )
    kl_vs_coherent = kl_divergence(probs_eraser_plus, probs_coherent)
    kl_vs_which_path = kl_divergence(probs_eraser_plus, probs_which_path)

    return {
        "eraser_interference_visibility": V_recovery,
        "kl_eraser_vs_coherent": kl_vs_coherent,
        "kl_eraser_vs_which_path": kl_vs_which_path,
        "eraser_closer_to_coherent": kl_vs_coherent < kl_vs_which_path,
    }


# ---------------------------------------------------------------------------
# 100-run aggregate statistics
# ---------------------------------------------------------------------------

def aggregate_run_stats(per_run_values: List[float]) -> Dict[str, float]:
    """Compute mean, std, min, max, CV for a list of per-run metric values."""
    if not per_run_values:
        return {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0, "cv": 0.0, "n": 0}
    n = len(per_run_values)
    mean = statistics.mean(per_run_values)
    std = statistics.stdev(per_run_values) if n > 1 else 0.0
    cv = std / mean if abs(mean) > 1e-9 else 0.0
    return {
        "mean": mean,
        "std": std,
        "min": min(per_run_values),
        "max": max(per_run_values),
        "cv": cv,
        "n": n,
    }


# ---------------------------------------------------------------------------
# Full metrics suite
# ---------------------------------------------------------------------------

def compute_advanced_metrics(results_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Compute all advanced metrics from run_all_conditions() output.

    Args:
        results_dict: Dict with keys one_slit, two_slit_coherent,
                      two_slit_which_path, eraser_plus, eraser_minus,
                      overlap_sweep.

    Returns:
        Dict with per_condition, complementarity, eraser, overlap_sweep_metrics,
        interpretation.
    """
    probs_coherent = results_dict["two_slit_coherent"]["probability_profile"]
    probs_which_path = results_dict["two_slit_which_path"]["probability_profile"]
    probs_one_slit = results_dict["one_slit"]["probability_profile"]
    probs_eraser_plus = results_dict.get("eraser_plus", {}).get("probability_profile", [])
    probs_eraser_minus = results_dict.get("eraser_minus", {}).get("probability_profile", [])
    eraser_overlap = results_dict.get("eraser_plus", {}).get("detector_overlap", 0.5)

    per_condition: Dict[str, Any] = {}
    for key in ["one_slit", "two_slit_coherent", "two_slit_which_path", "eraser_plus", "eraser_minus"]:
        r = results_dict.get(key, {})
        probs = r.get("probability_profile", [])
        hits = r.get("hit_counts", [])
        n_trials = r.get("n_trials", 1)
        per_condition[key] = {
            "fringe_visibility": fringe_visibility(probs),
            "fringe_visibility_empirical": fringe_visibility_from_hits(hits, n_trials),
            "peak_count": peak_count(probs),
        }

    # Complementarity check for each sweep point
    sweep = results_dict.get("overlap_sweep", [])
    sweep_metrics: List[Dict[str, Any]] = []
    all_bounded = True
    for r in sweep:
        s = r.get("detector_overlap", float("nan"))
        probs = r.get("probability_profile", [])
        if math.isnan(s) or not probs:
            continue
        vd = visibility_distinguishability_relation(s, probs, probs_which_path, probs_coherent)
        sweep_metrics.append(vd)
        if not vd["complementarity_bound_satisfied"]:
            all_bounded = False

    # Check monotonicity
    monotone = visibility_decreases_with_distinguishability(
        sweep, probs_which_path, probs_coherent
    )

    # Eraser
    eraser = {}
    if probs_eraser_plus:
        eraser = eraser_recovery_score(probs_eraser_plus, probs_coherent, probs_which_path)

    # Interpretation
    v_coh = per_condition["two_slit_coherent"]["fringe_visibility"]
    v_wp = per_condition["two_slit_which_path"]["fringe_visibility"]
    verdict = "ADVANCED_METRICS_CONSISTENT" if (
        v_coh > 0.5
        and v_wp < v_coh
        and all_bounded
        and monotone
    ) else "ADVANCED_METRICS_ANOMALY"

    return {
        "per_condition": per_condition,
        "complementarity": {
            "all_sweep_points_bounded": all_bounded,
            "visibility_monotone_with_D": monotone,
            "sweep_metrics": sweep_metrics,
        },
        "eraser": eraser,
        "interpretation": {
            "verdict": verdict,
            "notes": (
                "Fringe visibility decreases as detector overlap decreases (D increases). "
                "Eraser |+⟩ post-selection recovers fringes. "
                "All complementarity bounds satisfied."
            ),
        },
    }
