"""
trial_factor_correction.py
==========================
Multiple-testing correction utilities for the Reality Audit public anisotropy pipeline.

Background
----------
The pipeline currently tests several statistics against a common null ensemble:
  1. hemisphere_imbalance   — asymmetry between sky halves
  2. preferred_axis_score   — strongest directional clustering across trial axes
  3. energy_time_pearson_r  — correlation between energy and arrival time
  4. clustering_score       — spatial clustering excess

Testing multiple statistics and reporting the most significant one inflates the
false-positive rate.  Simple corrections such as Bonferroni and Holm bound the
family-wise error rate (FWER) by accounting for the number of simultaneous tests.

This module provides:
  - ``correct_pvalues_bonferroni`` : Bonferroni FWER correction
  - ``correct_pvalues_holm``       : Holm step-down FWER correction (more powerful)
  - ``apply_trial_correction``     : convenience wrapper — applies a named method
    to a dict of {metric_name: percentile_or_pvalue} and returns corrected flags
  - ``interpret_corrected_result`` : returns a concise, labeled interpretation dict

Terminology
-----------
The pipeline produces empirical percentile ranks, not frequentist p-values.
For correction purposes, ``p = 1 - percentile`` is used to convert them.
Results are always labeled so the distinction is traceable.

Author: commons-sentience-sandbox
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Supported correction methods
# ---------------------------------------------------------------------------
SUPPORTED_METHODS = ("bonferroni", "holm", "none")

# Ordered list of standard metrics the pipeline may report
STANDARD_METRICS: List[str] = [
    "hemisphere_imbalance",
    "preferred_axis_score",
    "energy_time_pearson_r",
    "clustering_score",
]


# ===========================================================================
# 1. Basic correction functions
# ===========================================================================

def correct_pvalues_bonferroni(
    pvalues: Dict[str, float],
) -> Dict[str, float]:
    """Apply Bonferroni correction to a dict of {name: p_value}.

    Bonferroni: multiply each p-value by the number of tests, capped at 1.0.

    Parameters
    ----------
    pvalues : dict mapping metric name to uncorrected p-value in [0, 1].

    Returns
    -------
    Dict of corrected p-values with the same keys.
    """
    n = len(pvalues)
    if n == 0:
        return {}
    return {
        name: min(1.0, p * n)
        for name, p in pvalues.items()
    }


def correct_pvalues_holm(
    pvalues: Dict[str, float],
) -> Dict[str, float]:
    """Apply Holm step-down correction to a dict of {name: p_value}.

    Holm correction is uniformly more powerful than Bonferroni while still
    controlling the FWER.  It sorts p-values ascending and applies:
        corrected[i] = p[i] * (n - i)   (with sequential max to ensure monotonicity)

    Parameters
    ----------
    pvalues : dict mapping metric name to uncorrected p-value in [0, 1].

    Returns
    -------
    Dict of corrected p-values with the same keys, capped at 1.0.
    """
    if not pvalues:
        return {}

    n = len(pvalues)
    # Sort by ascending p-value (smallest first = most significant first)
    sorted_items: List[Tuple[str, float]] = sorted(pvalues.items(), key=lambda kv: kv[1])

    corrected_sorted: List[float] = []
    running_max = 0.0
    for i, (name, p) in enumerate(sorted_items):
        c = min(1.0, p * (n - i))
        # Enforce monotonicity: corrected p-values must be non-decreasing
        running_max = max(running_max, c)
        corrected_sorted.append(running_max)

    return {
        name: corrected_sorted[i]
        for i, (name, _) in enumerate(sorted_items)
    }


# ===========================================================================
# 2. Convenience wrapper
# ===========================================================================

def apply_trial_correction(
    metric_percentiles: Dict[str, Optional[float]],
    method: str = "holm",
    exclusion_threshold: float = 0.95,
    discovery_threshold: float = 0.999,
    primary_metrics: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Apply a multiple-testing correction to a set of metric percentiles.

    Converts percentiles to p-values, applies the correction, and returns
    corrected p-values, corrected percentile equivalents, and per-metric flags.

    Parameters
    ----------
    metric_percentiles  : dict of {metric_name: percentile_float_or_None}.
                          Metrics with None values are skipped.
    method              : "bonferroni", "holm", or "none" (pass-through).
    exclusion_threshold : uncorrected percentile above which a metric is flagged
                          as "notable" before correction (default 0.95).
    discovery_threshold : uncorrected percentile above which a metric would be
                          "discovery-level" before correction (default 0.999).
    primary_metrics     : list of metric names to use for correction.  Defaults
                          to all metrics with non-None values.

    Returns
    -------
    Dict with keys:
        method                  – correction method used
        n_tests                 – number of metrics tested
        uncorrected_percentiles – {name: float}
        uncorrected_pvalues     – {name: float}
        corrected_pvalues       – {name: float}
        corrected_percentiles   – {name: float}  (= 1 - corrected_p)
        flags                   – {name: "notable" | "discovery" | "null" | "insufficient_data"}
        any_corrected_notable   – bool: any corrected p < (1 - exclusion_threshold)
        any_corrected_discovery – bool: any corrected p < (1 - discovery_threshold)
        summary_verdict         – str: "corrected_discovery" | "corrected_notable" | "corrected_null"
        caveats                 – list[str]
    """
    if method not in SUPPORTED_METHODS:
        raise ValueError(f"Unsupported method '{method}'. Valid: {SUPPORTED_METHODS}")

    # Filter to metrics with valid values
    valid: Dict[str, float] = {}
    for name, pct in metric_percentiles.items():
        if primary_metrics is not None and name not in primary_metrics:
            continue
        if pct is None:
            continue
        try:
            f = float(pct)
            # Clamp to avoid log(0) or p=0/1 issues
            f = max(0.0, min(1.0, f))
            valid[name] = f
        except (TypeError, ValueError):
            pass

    # Convert percentiles to p-values  (p = 1 - percentile)
    uncorrected_p: Dict[str, float] = {
        name: max(1e-10, 1.0 - pct)   # floor to avoid exactly 0
        for name, pct in valid.items()
    }

    # Apply correction
    if method == "bonferroni":
        corrected_p = correct_pvalues_bonferroni(uncorrected_p)
    elif method == "holm":
        corrected_p = correct_pvalues_holm(uncorrected_p)
    else:  # "none"
        corrected_p = dict(uncorrected_p)

    # Convert corrected p back to percentile-equivalent
    corrected_pct: Dict[str, float] = {
        name: 1.0 - p
        for name, p in corrected_p.items()
    }

    # Per-metric flags using CORRECTED percentiles
    flags: Dict[str, str] = {}
    for name in valid:
        cp = corrected_pct[name]
        if cp >= discovery_threshold:
            flags[name] = "discovery"
        elif cp >= exclusion_threshold:
            flags[name] = "notable"
        else:
            flags[name] = "null"

    # Metrics without values get insufficient_data
    for name, pct in metric_percentiles.items():
        if name not in flags:
            flags[name] = "insufficient_data"

    any_notable    = any(v == "notable"    for v in flags.values())
    any_discovery  = any(v == "discovery"  for v in flags.values())

    if any_discovery:
        verdict = "corrected_discovery"
    elif any_notable:
        verdict = "corrected_notable"
    else:
        verdict = "corrected_null"

    caveats = [
        f"Correction method: {method} over {len(valid)} metrics.",
        "Empirical percentile resolution floor = 1/null_repeats; "
        "with 100 repeats the floor is 0.01.",
        "Secondary statistics (energy_time_pearson_r, clustering_score) "
        "are exploratory; correction was applied but threshold for discovery "
        "claims applies only to primary statistics "
        "(hemisphere_imbalance, preferred_axis_score).",
    ]
    if len(valid) < 2:
        caveats.append(
            "Fewer than 2 metrics available; multiple-testing correction "
            "is trivial but is applied for consistency."
        )

    return {
        "method":                  method,
        "n_tests":                 len(valid),
        "uncorrected_percentiles": dict(valid),
        "uncorrected_pvalues":     uncorrected_p,
        "corrected_pvalues":       corrected_p,
        "corrected_percentiles":   corrected_pct,
        "flags":                   flags,
        "any_corrected_notable":   any_notable,
        "any_corrected_discovery": any_discovery,
        "summary_verdict":         verdict,
        "caveats":                 caveats,
    }


# ===========================================================================
# 3. Interpret corrected result as human-readable output
# ===========================================================================

def interpret_corrected_result(correction: Dict[str, Any]) -> str:
    """Return a short human-readable interpretation of a correction result.

    Parameters
    ----------
    correction : dict from apply_trial_correction

    Returns
    -------
    Multi-line string suitable for embedding in memos or terminal output.
    """
    method  = correction.get("method", "unknown")
    n_tests = correction.get("n_tests", 0)
    verdict = correction.get("summary_verdict", "unknown")
    flags   = correction.get("flags", {})
    corr_p  = correction.get("corrected_pvalues", {})
    corr_pct = correction.get("corrected_percentiles", {})

    lines = [
        f"Multiple-testing correction ({method} over {n_tests} metrics):",
        "",
    ]
    for name in sorted(flags):
        flag = flags[name]
        if name in corr_pct:
            cp   = corr_pct[name]
            raw  = correction.get("uncorrected_percentiles", {}).get(name)
            raw_str = f"{raw:.4f}" if raw is not None else "N/A"
            cp_str  = f"{cp:.4f}"
            lines.append(
                f"  {name:<30s}  uncorr_pct={raw_str}  corr_pct={cp_str}  [{flag.upper()}]"
            )
        else:
            lines.append(f"  {name:<30s}  [INSUFFICIENT DATA]")

    lines.append("")
    if verdict == "corrected_discovery":
        lines.append("VERDICT: CORRECTED DISCOVERY-LEVEL deviation (≥ discovery_threshold after correction)")
    elif verdict == "corrected_notable":
        lines.append("VERDICT: CORRECTED NOTABLE deviation (≥ exclusion_threshold after correction)")
    else:
        lines.append("VERDICT: CORRECTED NULL — no metric exceeds exclusion_threshold after correction")

    lines.append("")
    lines.append("Caveats:")
    for c in correction.get("caveats", []):
        lines.append(f"  - {c}")

    return "\n".join(lines)
