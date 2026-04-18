"""
double_slit_metrics.py — Interference audit metrics for double-slit benchmark.

Computes quantitative measures of interference pattern presence/absence
and observer sensitivity for the double-slit benchmark output.

Metrics
-------
fringe_visibility
    Michelson visibility: (I_max - I_min) / (I_max + I_min).
    Near 1.0 → strong fringes present.  Near 0.0 → no fringes.

peak_count
    Number of local maxima in the intensity profile above a threshold.
    Two-slit unmeasured should return more peaks than the measured or
    one-slit conditions.

center_intensity
    Normalised intensity at the screen centre (bin 0).
    In the two-slit unmeasured case this is a constructive-interference
    maximum (large).  In the measured case it is an incoherent mean
    (smaller).

distribution_entropy
    Shannon entropy of the normalised hit-count histogram.
    Higher entropy → more spread-out distribution.

measured_vs_unmeasured_kl
    KL divergence D_KL(unmeasured || measured) — measures how much the
    which-path measurement changes the observed distribution.

one_slit_vs_two_slit_kl
    KL divergence D_KL(two_slit || one_slit).

fringe_suppression_ratio
    fringe_visibility(two_slit_measured) / fringe_visibility(two_slit).
    Near 0.0 → measurement fully suppresses interference.
    Near 1.0 → measurement has no effect (unexpected).
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Single-condition metrics
# ---------------------------------------------------------------------------

def fringe_visibility(intensities: List[float]) -> float:
    """Michelson fringe visibility over the intensity profile.

    Returns a value in [0, 1].  Returns 0.0 if profile is flat.
    """
    if not intensities:
        return 0.0
    i_max = max(intensities)
    i_min = min(intensities)
    denom = i_max + i_min
    if denom < 1e-12:
        return 0.0
    return (i_max - i_min) / denom


def peak_count(
    intensities: List[float],
    threshold_fraction: float = 0.1,
) -> int:
    """Count local maxima above threshold_fraction * max_intensity."""
    if len(intensities) < 3:
        return 0
    i_max = max(intensities)
    threshold = threshold_fraction * i_max
    count = 0
    for i in range(1, len(intensities) - 1):
        if (
            intensities[i] > intensities[i - 1]
            and intensities[i] > intensities[i + 1]
            and intensities[i] >= threshold
        ):
            count += 1
    return count


def center_intensity_normalised(intensities: List[float]) -> float:
    """Intensity at the screen centre, normalised by max intensity."""
    if not intensities:
        return 0.0
    i_max = max(intensities)
    if i_max < 1e-12:
        return 0.0
    center = intensities[len(intensities) // 2]
    return center / i_max


def distribution_entropy(hits: List[int]) -> float:
    """Shannon entropy of the hit-count distribution (nats, base-e)."""
    total = sum(hits)
    if total == 0:
        return 0.0
    entropy = 0.0
    for h in hits:
        if h > 0:
            p = h / total
            entropy -= p * math.log(p)
    return round(entropy, 6)


# ---------------------------------------------------------------------------
# Cross-condition metrics
# ---------------------------------------------------------------------------

def _safe_kl(p_list: List[float], q_list: List[float], eps: float = 1e-9) -> float:
    """KL divergence D_KL(P || Q) with Laplace smoothing epsilon."""
    assert len(p_list) == len(q_list), "Distributions must have same length"
    total_p = sum(p_list)
    total_q = sum(q_list)
    kl = 0.0
    n = len(p_list)
    for p_i, q_i in zip(p_list, q_list):
        p_norm = (p_i / total_p + eps) if total_p > 0 else eps
        q_norm = (q_i / total_q + eps) if total_q > 0 else eps
        # Renormalise after adding eps
        p_norm = p_norm / (1 + n * eps)
        q_norm = q_norm / (1 + n * eps)
        kl += p_norm * math.log(p_norm / q_norm)
    return round(max(kl, 0.0), 6)


def measured_vs_unmeasured_kl(
    two_slit_hits: List[int],
    two_slit_measured_hits: List[int],
) -> float:
    """KL divergence D_KL(two_slit || two_slit_measured)."""
    return _safe_kl(
        [float(h) for h in two_slit_hits],
        [float(h) for h in two_slit_measured_hits],
    )


def one_slit_vs_two_slit_kl(
    two_slit_hits: List[int],
    one_slit_hits: List[int],
) -> float:
    """KL divergence D_KL(two_slit || one_slit)."""
    return _safe_kl(
        [float(h) for h in two_slit_hits],
        [float(h) for h in one_slit_hits],
    )


def fringe_suppression_ratio(
    visibility_unmeasured: float,
    visibility_measured: float,
) -> float:
    """Ratio of fringe visibility: measured / unmeasured.

    Near 0.0 → measurement suppresses fringes completely.
    Near 1.0 → no suppression effect.
    """
    if visibility_unmeasured < 1e-12:
        return 1.0  # undefined; no baseline fringes
    return round(visibility_measured / visibility_unmeasured, 6)


# ---------------------------------------------------------------------------
# Full metric suite
# ---------------------------------------------------------------------------

def compute_all_metrics(
    results: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """Compute the full interference metric suite from benchmark results.

    Parameters
    ----------
    results : dict
        Output of ``run_all_conditions()`` or ``run_double_slit_benchmark()``.
        Keys are condition names; values contain 'intensity_profile' and
        'hit_counts'.

    Returns
    -------
    dict with keys:
        per_condition   — single-condition metrics per condition
        cross_condition — cross-condition comparison metrics
        interpretation  — plain-text summary
    """
    per_cond: Dict[str, Dict[str, Any]] = {}
    for cond_name, result in results.items():
        intensities = result["intensity_profile"]
        hits = result["hit_counts"]
        per_cond[cond_name] = {
            "fringe_visibility": round(fringe_visibility(intensities), 6),
            "peak_count": peak_count(intensities),
            "center_intensity_normalised": round(center_intensity_normalised(intensities), 6),
            "distribution_entropy": distribution_entropy(hits),
        }

    # Cross-condition metrics (require all three conditions)
    cross: Dict[str, Any] = {}
    ts_key = "two_slit"
    tsm_key = "two_slit_measured"
    os_key = "one_slit"

    if ts_key in results and tsm_key in results:
        cross["measured_vs_unmeasured_kl"] = measured_vs_unmeasured_kl(
            results[ts_key]["hit_counts"],
            results[tsm_key]["hit_counts"],
        )
        vis_unmeasured = per_cond[ts_key]["fringe_visibility"]
        vis_measured = per_cond[tsm_key]["fringe_visibility"]
        cross["fringe_suppression_ratio"] = fringe_suppression_ratio(
            vis_unmeasured, vis_measured
        )
        cross["visibility_drop"] = round(vis_unmeasured - vis_measured, 6)

    if ts_key in results and os_key in results:
        cross["one_slit_vs_two_slit_kl"] = one_slit_vs_two_slit_kl(
            results[ts_key]["hit_counts"],
            results[os_key]["hit_counts"],
        )

    # Interpretation
    lines: List[str] = ["=== Double-Slit Metric Summary ==="]
    for cond, mc in per_cond.items():
        lines.append(
            f"  {cond}: visibility={mc['fringe_visibility']:.4f}  "
            f"peaks={mc['peak_count']}  "
            f"center_norm={mc['center_intensity_normalised']:.4f}  "
            f"entropy={mc['distribution_entropy']:.4f}"
        )
    if "visibility_drop" in cross:
        lines.append(
            f"\n  Measurement suppresses fringe visibility by {cross['visibility_drop']:.4f} "
            f"(suppression ratio={cross.get('fringe_suppression_ratio', 'N/A'):.4f})"
        )
    if "measured_vs_unmeasured_kl" in cross:
        lines.append(
            f"  KL(two_slit || measured)  = {cross['measured_vs_unmeasured_kl']:.4f}"
        )
    if "one_slit_vs_two_slit_kl" in cross:
        lines.append(
            f"  KL(two_slit || one_slit)  = {cross['one_slit_vs_two_slit_kl']:.4f}"
        )

    # Verdict
    if ts_key in per_cond and tsm_key in per_cond and os_key in per_cond:
        v_ts  = per_cond[ts_key]["fringe_visibility"]
        v_tsm = per_cond[tsm_key]["fringe_visibility"]
        p_ts  = per_cond[ts_key]["peak_count"]
        p_tsm = per_cond[tsm_key]["peak_count"]
        p_os  = per_cond[os_key]["peak_count"]

        # Visibility is the primary criterion — works regardless of screen width
        interference_present = v_ts > 0.3
        measurement_suppresses = v_tsm < v_ts * 0.7
        one_slit_distinct = p_os < p_ts or abs(per_cond[ts_key]["center_intensity_normalised"] - per_cond[os_key]["center_intensity_normalised"]) > 0.05

        if interference_present and measurement_suppresses and one_slit_distinct:
            verdict = "BENCHMARK_BEHAVED_CORRECTLY: interference present, measurement suppresses, one-slit distinct"
        elif interference_present and not measurement_suppresses:
            verdict = "UNEXPECTED: interference present but measurement did not suppress it"
        elif not interference_present:
            verdict = "UNEXPECTED: no interference pattern in two-slit unmeasured condition"
        else:
            verdict = "PARTIAL: some expected features present; check parameters"

        lines.append(f"\n  VERDICT: {verdict}")
        cross["verdict"] = verdict
    else:
        cross["verdict"] = "incomplete_conditions"

    return {
        "per_condition": per_cond,
        "cross_condition": cross,
        "interpretation": "\n".join(lines),
    }
