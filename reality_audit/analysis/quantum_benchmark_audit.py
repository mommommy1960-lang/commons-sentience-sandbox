"""
quantum_benchmark_audit.py — Audit integration for quantum double-slit benchmark.

Answers three audit questions:
  Q1: Can the auditor distinguish coherent from decohered interference?
  Q2: Is partial decoherence trend correctly detected?
  Q3: Is the benchmark stable across seed variations?

Writes:
  audit_summary.json
  audit_comparison_report.json
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any, Dict, List, Optional

from reality_audit.benchmarks.quantum_double_slit import (
    run_all_conditions,
    DEFAULT_N_TRIALS,
    DEFAULT_SLIT_SEPARATION,
    DEFAULT_SLIT_WIDTH,
    DEFAULT_WAVELENGTH,
    DEFAULT_SCREEN_DISTANCE,
    DEFAULT_SCREEN_WIDTH,
    DEFAULT_N_BINS,
)
from reality_audit.analysis.quantum_double_slit_metrics import (
    fringe_visibility,
    partial_decoherence_monotonicity,
    coherence_sensitivity,
)

_SEED_STABILITY_SEEDS: List[int] = [0, 1, 2]
_SEED_STABILITY_CV_THRESHOLD: float = 0.05


# ---------------------------------------------------------------------------
# Q1 — Coherent vs decohered distinguishability
# ---------------------------------------------------------------------------

def _q1_audit_coherent_vs_decohered(results: Dict[str, Any]) -> Dict[str, Any]:
    """Determine if coherent and decohered conditions are distinguishable."""
    v_coherent = fringe_visibility(results["two_slit_coherent"]["probability_profile"])
    v_decohered = fringe_visibility(results["two_slit_decohered"]["probability_profile"])
    ratio = v_coherent / v_decohered if v_decohered > 1e-9 else None

    distinguishable = (
        v_coherent > 0.5
        and v_decohered < 0.5
        and (ratio is not None and ratio > 2.0)
    )

    return {
        "question": "Can auditor distinguish coherent from decohered interference?",
        "v_coherent": v_coherent,
        "v_decohered": v_decohered,
        "ratio_coherent_over_decohered": ratio,
        "PASS": distinguishable,
        "note": (
            "Coherent condition must have V > 0.5 and decohered V < 0.5 "
            "and ratio > 2 for clear audit distinguishability."
        ),
    }


# ---------------------------------------------------------------------------
# Q2 — Partial decoherence trend detection
# ---------------------------------------------------------------------------

def _q2_audit_decoherence_trend(results: Dict[str, Any]) -> Dict[str, Any]:
    """Check that visibility decreases monotonically with gamma."""
    sweep = results.get("decoherence_sweep", [])
    monotone = partial_decoherence_monotonicity(sweep)
    slope = coherence_sensitivity(sweep)

    trend_detected = monotone and slope < 0.0

    return {
        "question": "Is the partial decoherence trend correctly detected?",
        "n_gamma_values": len(sweep),
        "is_monotone_non_increasing": monotone,
        "visibility_vs_gamma_slope": slope,
        "PASS": trend_detected,
        "note": (
            "Expects visibility to decrease monotonically as gamma increases (0 → 1). "
            "Slope should be negative."
        ),
    }


# ---------------------------------------------------------------------------
# Q3 — Seed stability
# ---------------------------------------------------------------------------

def _q3_audit_seed_stability(
    n_trials: int = DEFAULT_N_TRIALS,
    slit_separation: float = DEFAULT_SLIT_SEPARATION,
    slit_width: float = DEFAULT_SLIT_WIDTH,
    wavelength: float = DEFAULT_WAVELENGTH,
    screen_distance: float = DEFAULT_SCREEN_DISTANCE,
    screen_width: float = DEFAULT_SCREEN_WIDTH,
    n_bins: int = DEFAULT_N_BINS,
    seeds: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """Run benchmark with multiple seeds; check fringe_visibility CV < threshold."""
    seeds = seeds or _SEED_STABILITY_SEEDS
    visibilities_coherent: List[float] = []
    visibilities_decohered: List[float] = []

    for seed in seeds:
        r = run_all_conditions(
            n_trials=n_trials,
            slit_separation=slit_separation,
            slit_width=slit_width,
            wavelength=wavelength,
            screen_distance=screen_distance,
            screen_width=screen_width,
            n_bins=n_bins,
            seed=seed,
            partial_gammas=[],
        )
        visibilities_coherent.append(
            fringe_visibility(r["two_slit_coherent"]["probability_profile"])
        )
        visibilities_decohered.append(
            fringe_visibility(r["two_slit_decohered"]["probability_profile"])
        )

    def _cv(vals: List[float]) -> float:
        mean = statistics.mean(vals)
        if mean == 0.0:
            return 0.0
        std = statistics.stdev(vals) if len(vals) > 1 else 0.0
        return std / mean

    cv_coherent = _cv(visibilities_coherent)
    cv_decohered = _cv(visibilities_decohered)
    stable = cv_coherent < _SEED_STABILITY_CV_THRESHOLD and cv_decohered < _SEED_STABILITY_CV_THRESHOLD

    return {
        "question": "Is the benchmark stable under seed variation?",
        "seeds": seeds,
        "v_coherent_per_seed": visibilities_coherent,
        "v_decohered_per_seed": visibilities_decohered,
        "cv_coherent": cv_coherent,
        "cv_decohered": cv_decohered,
        "cv_threshold": _SEED_STABILITY_CV_THRESHOLD,
        "PASS": stable,
        "note": (
            f"Coefficient of variation (CV = σ/μ) must be < {_SEED_STABILITY_CV_THRESHOLD} "
            "for both conditions to declare seed-stable."
        ),
    }


# ---------------------------------------------------------------------------
# Master audit runner
# ---------------------------------------------------------------------------

def run_quantum_benchmark_audit(
    results: Dict[str, Any],
    output_dir: Optional[Path] = None,
    run_seed_stability: bool = True,
    seed_stability_kwargs: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Run three audit questions and write JSON reports.

    Args:
        results: Return value of run_all_conditions().
        output_dir: Where to write JSON output. If None, outputs not written to disk.
        run_seed_stability: If False, skip the multi-seed run (much faster).
        seed_stability_kwargs: Extra kwargs for _q3 (e.g. n_trials for smaller run).

    Returns:
        Full audit report dict.
    """
    q1 = _q1_audit_coherent_vs_decohered(results)
    q2 = _q2_audit_decoherence_trend(results)

    if run_seed_stability:
        kwargs = seed_stability_kwargs or {}
        q3 = _q3_audit_seed_stability(**kwargs)
    else:
        q3 = {
            "question": "Seed stability (skipped)",
            "PASS": None,
            "note": "run_seed_stability=False",
        }

    all_pass = all(
        q["PASS"] is True for q in [q1, q2, q3]
    )

    audit_summary = {
        "benchmark": "quantum_double_slit",
        "audit_version": "1.0",
        "Q1_coherent_vs_decohered": q1,
        "Q2_decoherence_trend": q2,
        "Q3_seed_stability": q3,
        "overall_PASS": all_pass,
        "verdict": "AUDIT_PASSED" if all_pass else "AUDIT_FAILED",
    }

    comparison_report = {
        "benchmark": "quantum_double_slit",
        "comparisons": {
            "Q1_PASS": q1["PASS"],
            "Q2_PASS": q2["PASS"],
            "Q3_PASS": q3["PASS"],
            "fringe_visibility_coherent": q1.get("v_coherent"),
            "fringe_visibility_decohered": q1.get("v_decohered"),
            "visibility_ratio": q1.get("ratio_coherent_over_decohered"),
            "decoherence_monotone": q2.get("is_monotone_non_increasing"),
            "decoherence_slope": q2.get("visibility_vs_gamma_slope"),
            "seed_cv_coherent": q3.get("cv_coherent"),
            "seed_cv_decohered": q3.get("cv_decohered"),
        },
    }

    if output_dir is not None:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "audit_summary.json").write_text(
            json.dumps(audit_summary, indent=2), encoding="utf-8"
        )
        (out / "audit_comparison_report.json").write_text(
            json.dumps(comparison_report, indent=2), encoding="utf-8"
        )
        print(f"  [audit] Wrote audit outputs to {out}", flush=True)

    return audit_summary
