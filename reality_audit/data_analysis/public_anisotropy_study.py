"""
public_anisotropy_study.py
==========================
Public-data anisotropy analysis module for the Reality Audit pipeline.

This module extends the statistical analysis from simulation_signature_analysis.py
to work with ingested public event catalogs.  It adds a denser axis scan
(48 trial axes vs the 12 in the earlier module) for improved preferred-axis
detection sensitivity, and produces a richer set of output artifacts.

What it does
------------
1. Takes a normalized event list (from public_event_catalogs.load_public_catalog)
2. Builds an isotropic null ensemble by generating ``null_repeats`` synthetic
   isotropic datasets of the same size
3. Computes hemisphere imbalance, preferred-axis score (48-axis scan), Pearson r,
   and clustering score on both observed and null data
4. Derives empirical percentile ranks relative to the null ensemble
5. Classifies the result into a signal tier (none / weak / moderate / strong)
6. Writes reproducible output artifacts

Statistical caveat
------------------
Detection of a statistically anomalous pattern is NOT proof of any specific
physical or metaphysical cause.  Results require careful evaluation of
instrument systematics, selection effects, and modeling assumptions before
any scientific claim can be made.

Author: commons-sentience-sandbox
"""

from __future__ import annotations

import csv
import datetime
import json
import math
import os
from typing import Any, Dict, List, Optional, Tuple

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    _HAS_MPL = True
except ImportError:  # pragma: no cover
    _HAS_MPL = False

# Re-use shared statistical helpers from simulation_signature_analysis
from reality_audit.data_analysis.simulation_signature_analysis import (
    _hemisphere_imbalance,
    _pearson_r,
    _clustering_score,
    _empirical_percentile,
    generate_null_events,
    TIER_NONE,
    TIER_WEAK,
    TIER_MODERATE,
    TIER_STRONG,
)

# Exposure-corrected null (lazy import to avoid circular deps)
def _get_exposure_null_module():
    from reality_audit.data_analysis import exposure_corrected_nulls as _ecn
    return _ecn

# =========================================================================
# Axis-scan generation (coarse, dense, and HEALPix planning hook)
# =========================================================================

def _build_axis_grid(n_lon: int, n_lat: int) -> List[Tuple[float, float, float]]:
    """Return unit vectors on a deterministic lon × sin(lat) grid."""
    axes: List[Tuple[float, float, float]] = []
    for i_lat in range(n_lat):
        # sin(lat) uniformly spaced in [-1, 1] — covers both hemispheres
        sin_lat = -1.0 + (2.0 * (i_lat + 0.5)) / n_lat
        cos_lat = math.sqrt(max(0.0, 1.0 - sin_lat ** 2))
        for i_lon in range(n_lon):
            lon = 2.0 * math.pi * i_lon / n_lon
            x = cos_lat * math.cos(lon)
            y = cos_lat * math.sin(lon)
            z = sin_lat
            axes.append((x, y, z))
    return axes


def _build_48_axes() -> List[Tuple[float, float, float]]:
    """Return the legacy 48-axis deterministic scan grid."""
    return _build_axis_grid(n_lon=8, n_lat=6)


def _build_axes_for_count(num_axes: int) -> List[Tuple[float, float, float]]:
    """Build a deterministic grid with at least ``num_axes`` points, then trim."""
    n = max(12, int(num_axes))
    # n_lon*n_lat ~ n with n_lon roughly sqrt(2n) for near-square lon/lat density.
    n_lon = max(4, int(math.ceil(math.sqrt(2.0 * n))))
    n_lat = max(3, int(math.ceil(n / n_lon)))
    axes = _build_axis_grid(n_lon=n_lon, n_lat=n_lat)
    return axes[:n]


def _generate_trial_axes(
    num_axes: int,
    mode: str = "auto",
    seed: Optional[int] = None,
    healpix_nside: Optional[int] = None,
) -> Tuple[List[Tuple[float, float, float]], Dict[str, Any]]:
    """Generate trial axes and return (axes, planning metadata).

    Modes
    -----
    auto
        Use legacy 48-axis grid for <=48 and deterministic dense grid above 48.
    coarse
        Legacy 48-axis grid (trimmed/extended deterministically as needed).
    dense
        Deterministic dense lon/sin(lat) grid with at least ``num_axes`` points.
    healpix_plan
        Planning hook only.  Uses a deterministic dense fallback now while
        recording intended HEALPix target size for future integration.
    """
    mode = (mode or "auto").lower()
    n = max(12, int(num_axes))

    if mode == "healpix_plan":
        nside = int(healpix_nside) if healpix_nside is not None else 8
        planned_npix = 12 * nside * nside
        axes = _build_axes_for_count(max(n, planned_npix))
        axes = axes[:max(n, min(planned_npix, len(axes)))]
        return axes, {
            "mode": "healpix_plan",
            "implemented": False,
            "message": "HEALPix integration pending; using deterministic dense-grid fallback.",
            "planned_healpix_nside": nside,
            "planned_healpix_npix": planned_npix,
            "seed": seed,
        }

    if mode == "dense" or (mode == "auto" and n > 48):
        axes = _build_axes_for_count(n)
        return axes, {
            "mode": "dense",
            "implemented": True,
            "message": "Deterministic dense lon/sin(lat) grid.",
            "planned_healpix_nside": None,
            "planned_healpix_npix": None,
            "seed": seed,
        }

    # coarse or auto with <=48
    fixed = list(_AXES_48)
    if n <= len(fixed):
        axes = fixed[:n]
    else:
        # Extend coarse grid deterministically using the dense builder.
        axes = _build_axes_for_count(n)
    return axes, {
        "mode": "coarse",
        "implemented": True,
        "message": "Legacy 48-axis grid (deterministic).",
        "planned_healpix_nside": None,
        "planned_healpix_npix": None,
        "seed": seed,
    }


_AXES_48: List[Tuple[float, float, float]] = _build_48_axes()


def _null_model_metadata(
    null_mode: str,
    exposure_map: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Return machine-readable null-model metadata for manifests/reports."""
    if null_mode == "exposure_corrected":
        em = (exposure_map or {}).get("exposure_model", {})
        return {
            "name": em.get("name", "empirical_proxy_histogram"),
            "version": em.get("version", "v1"),
            "mode": "exposure_corrected",
            "quality_tier": "proxy_only",
            "mission_grade_ready": False,
            "calibration": em.get("calibration"),
        }
    return {
        "name": "isotropic_uniform",
        "version": "v1",
        "mode": "isotropic",
        "quality_tier": "unmodeled_acceptance",
        "mission_grade_ready": False,
        "calibration": None,
    }


def _time_coverage_refinement(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Summarize time coverage quality for Stage 16 promotion-readiness checks."""
    thresholds = {
        "min_events_with_time": 20,
        "min_time_span_mjd": 30.0,
        "min_occupancy_fraction": 0.50,
        "target_confirmatory_span_mjd": 365.0,
        "target_confirmatory_occupancy_fraction": 0.75,
        "max_missing_time_fraction": 0.20,
    }
    times = []
    for e in events:
        t = e.get("arrival_time")
        if t is None:
            continue
        try:
            times.append(float(t))
        except (TypeError, ValueError):
            continue

    n_events = len(events)
    n_with_time = len(times)
    if not times:
        return {
            "n_events": n_events,
            "n_with_time": 0,
            "missing_time_fraction": 1.0 if n_events else 0.0,
            "time_span_mjd": None,
            "bin_count": 0,
            "occupied_bins": 0,
            "occupancy_fraction": 0.0,
            "uniformity_cv": None,
            "quality_tier": "insufficient",
            "thresholds": thresholds,
            "threshold_pass": {
                "events_with_time": False,
                "time_span": False,
                "occupancy_fraction": False,
                "missing_time_fraction": n_events == 0,
            },
            "confirmatory_readiness": "not_ready",
        }

    t_min = min(times)
    t_max = max(times)
    span = max(0.0, t_max - t_min)
    bin_count = 12
    if span <= 0.0:
        occupied_bins = 1
        uniformity_cv = None
    else:
        bins = [0] * bin_count
        for t in times:
            idx = int((t - t_min) / span * bin_count)
            idx = max(0, min(bin_count - 1, idx))
            bins[idx] += 1
        occupied_bins = sum(1 for b in bins if b > 0)
        mean = sum(bins) / len(bins)
        var = sum((b - mean) ** 2 for b in bins) / len(bins)
        uniformity_cv = (math.sqrt(var) / mean) if mean > 0 else None

    missing_frac = 1.0 - (n_with_time / n_events) if n_events else 0.0
    occupancy_fraction = occupied_bins / bin_count if bin_count else 0.0
    threshold_pass = {
        "events_with_time": n_with_time >= thresholds["min_events_with_time"],
        "time_span": span >= thresholds["min_time_span_mjd"],
        "occupancy_fraction": occupancy_fraction >= thresholds["min_occupancy_fraction"],
        "missing_time_fraction": missing_frac <= thresholds["max_missing_time_fraction"],
    }
    if not all(threshold_pass.values()):
        tier = "insufficient"
    elif uniformity_cv is not None and uniformity_cv > 1.25:
        tier = "limited"
    else:
        tier = "acceptable"
    confirmatory_ready = (
        span >= thresholds["target_confirmatory_span_mjd"]
        and occupancy_fraction >= thresholds["target_confirmatory_occupancy_fraction"]
        and missing_frac <= thresholds["max_missing_time_fraction"]
    )

    return {
        "n_events": n_events,
        "n_with_time": n_with_time,
        "missing_time_fraction": missing_frac,
        "time_span_mjd": span,
        "bin_count": bin_count,
        "occupied_bins": occupied_bins,
        "occupancy_fraction": occupancy_fraction,
        "uniformity_cv": uniformity_cv,
        "quality_tier": tier,
        "thresholds": thresholds,
        "threshold_pass": threshold_pass,
        "confirmatory_readiness": "ready" if confirmatory_ready else "not_ready",
    }


def _mission_grade_promotion_blockers(
    null_mode: str,
    exposure_model: Dict[str, Any],
    time_coverage: Dict[str, Any],
) -> Dict[str, Any]:
    """Return structured blocker list for Stage 16 mission-grade promotion."""
    blockers: List[Dict[str, str]] = []

    if null_mode == "exposure_corrected":
        blockers.append({
            "id": "exposure_empirical_proxy",
            "severity": "high",
            "detail": (
                "Exposure null is still empirical proxy-derived; promote only after "
                "response-informed exposure model integration."
            ),
        })

    if time_coverage.get("quality_tier") in ("insufficient", "limited"):
        blockers.append({
            "id": "time_coverage_refinement_required",
            "severity": "medium",
            "detail": (
                "Time coverage quality is not yet mission-grade for confirmatory "
                "promotion; improve span/occupancy uniformity documentation or model."
            ),
        })
    if time_coverage.get("confirmatory_readiness") != "ready":
        blockers.append({
            "id": "confirmatory_time_readiness_not_met",
            "severity": "medium",
            "detail": (
                "Time-coverage confirmatory thresholds are not met "
                "(span/occupancy/missingness)."
            ),
        })

    if exposure_model.get("mode") == "isotropic":
        blockers.append({
            "id": "instrument_acceptance_not_modeled",
            "severity": "high",
            "detail": (
                "Isotropic null does not include instrument acceptance geometry; "
                "limit claims to exploratory scope unless justified."
            ),
        })

    return {
        "status": "blocked" if blockers else "eligible_for_review",
        "blocker_count": len(blockers),
        "blockers": blockers,
    }


def scan_trial_axes(
    events: List[Dict[str, Any]],
    num_axes: int = 48,
    seed: Optional[int] = None,
    axis_mode: str = "auto",
    healpix_nside: Optional[int] = None,
) -> Dict[str, Any]:
    """Scan ``num_axes`` trial directions and return the preferred-axis score.

    Parameters
    ----------
    events   : normalized event list
    num_axes : number of trial axes (default 48; minimum 12)
    seed     : retained for reproducibility metadata (generation is deterministic)
    axis_mode: "auto", "coarse", "dense", or "healpix_plan"
    healpix_nside : optional planning NSIDE for future HEALPix integration

    Returns
    -------
    Dict with keys:
      best_score       – max |mean cos-projection| across all trial axes
      best_axis_index  – index of the winning axis
      best_axis_xyz    – (x, y, z) unit vector of the winning axis
      all_scores       – list of scores for all trial axes
      num_axes         – number of axes evaluated
    """
    ras  = [e["ra"]  for e in events if e.get("ra")  is not None]
    decs = [e["dec"] for e in events if e.get("dec") is not None]

    if not ras:
        return {
            "best_score":      0.0,
            "best_axis_index": 0,
            "best_axis_xyz":   (1.0, 0.0, 0.0),
            "all_scores":      [],
            "num_axes":        0,
        }

    # Convert to unit vectors
    vecs = []
    for ra, dec in zip(ras, decs):
        ra_r  = math.radians(ra)
        dec_r = math.radians(dec)
        vecs.append((
            math.cos(dec_r) * math.cos(ra_r),
            math.cos(dec_r) * math.sin(ra_r),
            math.sin(dec_r),
        ))

    axes, axis_plan = _generate_trial_axes(
        num_axes=num_axes,
        mode=axis_mode,
        seed=seed,
        healpix_nside=healpix_nside,
    )

    best_score = 0.0
    best_idx   = 0
    all_scores: List[float] = []

    for idx, ax in enumerate(axes):
        norm = math.sqrt(sum(a ** 2 for a in ax))
        ax_unit = tuple(a / norm for a in ax)
        projections = [sum(v[k] * ax_unit[k] for k in range(3)) for v in vecs]
        score = abs(sum(projections) / len(projections))
        all_scores.append(score)
        if score > best_score:
            best_score = score
            best_idx   = idx

    return {
        "best_score":      best_score,
        "best_axis_index": best_idx,
        "best_axis_xyz":   axes[best_idx],
        "all_scores":      all_scores,
        "num_axes":        len(axes),
        "axis_plan":       axis_plan,
    }


# =========================================================================
# Main analysis entry point
# =========================================================================

def run_public_anisotropy_study(
    events: List[Dict[str, Any]],
    null_repeats: int = 100,
    seed: Optional[int] = None,
    config: Optional[Dict[str, Any]] = None,
    num_axes: int = 48,
    null_mode: str = "isotropic",
    axis_mode: str = "auto",
    healpix_nside: Optional[int] = None,
) -> Dict[str, Any]:
    """Run the public-data anisotropy study.

    Parameters
    ----------
    events       : normalized event list (output of load_public_catalog)
    null_repeats : number of null draws for empirical percentile
    seed         : RNG seed for reproducibility
    config       : optional config dict (may override null_repeats, num_axes,
                   null_mode, ra_bins, dec_bins)
    num_axes     : number of trial axes for axis scan
    null_mode    : "isotropic" (default) or "exposure_corrected"
                   "exposure_corrected" builds an empirical sky-acceptance proxy
                   from the observed catalog and samples null positions from it.
    axis_mode    : axis generation mode: "auto", "coarse", "dense", or "healpix_plan"
    healpix_nside: optional NSIDE planning value when using "healpix_plan"

    Returns
    -------
    Structured results dict with keys:
      event_count, energy_stats, anisotropy, preferred_axis, axis_scan,
      energy_time_correlation, cluster_score, null_comparison,
      signal_evaluation, run_metadata
    """
    cfg = config or {}
    if "null_repeats" in cfg:
        null_repeats = int(cfg["null_repeats"])
    if "num_axes" in cfg:
        num_axes = int(cfg["num_axes"])
    if "null_mode" in cfg:
        null_mode = str(cfg["null_mode"])
    if "axis_mode" in cfg:
        axis_mode = str(cfg["axis_mode"]).strip().lower()
    if "healpix_nside" in cfg and cfg.get("healpix_nside") is not None:
        healpix_nside = int(cfg["healpix_nside"])

    rng_seed = seed if seed is not None else cfg.get("seed", None)

    _valid_null_modes = ("isotropic", "exposure_corrected")
    if null_mode not in _valid_null_modes:
        raise ValueError(
            f"null_mode={null_mode!r} is not recognised. "
            f"Choose from: {_valid_null_modes}"
        )

    # Build exposure map once if needed
    exposure_map: Optional[Dict[str, Any]] = None
    exposure_map_desc: Optional[Dict[str, Any]] = None
    null_ensemble: Optional[List[List[Dict[str, Any]]]] = None

    if null_mode == "exposure_corrected":
        ecn = _get_exposure_null_module()
        null_ensemble, exposure_map = ecn.generate_exposure_corrected_null_ensemble(
            events, repeats=null_repeats, seed=rng_seed, config=cfg
        )
        exposure_map_desc = ecn.describe_exposure_map(exposure_map)

    rng_seed = seed if seed is not None else cfg.get("seed", None)

    # Collect field vectors
    energies = [e["energy"]       for e in events if e.get("energy")       is not None]
    times    = [e["arrival_time"] for e in events if e.get("arrival_time") is not None]
    ras      = [e["ra"]           for e in events if e.get("ra")           is not None]
    decs     = [e["dec"]          for e in events if e.get("dec")          is not None]

    # Energy summary
    energy_stats: Dict[str, Any] = {}
    if energies:
        sorted_e   = sorted(energies)
        mid        = len(sorted_e) // 2
        mean_e     = sum(energies) / len(energies)
        energy_stats = {
            "count":  len(energies),
            "min":    sorted_e[0],
            "max":    sorted_e[-1],
            "mean":   mean_e,
            "median": (sorted_e[mid] + sorted_e[mid - 1]) / 2
                      if len(sorted_e) % 2 == 0 else sorted_e[mid],
            "std":    math.sqrt(
                sum((e - mean_e) ** 2 for e in energies) / len(energies)
            ),
        }

    # Primary metrics (observed)
    hemi          = _hemisphere_imbalance(ras, decs)
    axis_scan_obs = scan_trial_axes(
        events,
        num_axes=num_axes,
        seed=rng_seed,
        axis_mode=axis_mode,
        healpix_nside=healpix_nside,
    )
    axis_score    = axis_scan_obs["best_score"]

    et_pairs = [
        (e["energy"], e["arrival_time"])
        for e in events
        if e.get("energy") is not None and e.get("arrival_time") is not None
    ]
    et_r = _pearson_r(
        [p[0] for p in et_pairs], [p[1] for p in et_pairs]
    ) if len(et_pairs) >= 3 else None

    clust = _clustering_score(times) if len(times) >= 2 else 1.0

    # Null ensemble
    null_hemi_vals:  List[float] = []
    null_axis_vals:  List[float] = []
    null_et_r_vals:  List[float] = []
    null_clust_vals: List[float] = []

    for rep in range(null_repeats):
        ns = (rng_seed + rep) if rng_seed is not None else None

        # Generate the null draw
        if null_mode == "exposure_corrected" and null_ensemble is not None:
            null = null_ensemble[rep]
        else:
            null = generate_null_events(events, mode="isotropic", seed=ns)

        n_ras  = [r["ra"]  for r in null if r.get("ra")  is not None]
        n_decs = [r["dec"] for r in null if r.get("dec") is not None]
        n_times = [r["arrival_time"] for r in null if r.get("arrival_time") is not None]

        null_hemi_vals.append(abs(_hemisphere_imbalance(n_ras, n_decs)))

        null_ax_scan = scan_trial_axes(
            null,
            num_axes=num_axes,
            seed=ns,
            axis_mode=axis_mode,
            healpix_nside=healpix_nside,
        )
        null_axis_vals.append(null_ax_scan["best_score"])

        null_pairs = [
            (r["energy"], r["arrival_time"])
            for r in null
            if r.get("energy") is not None and r.get("arrival_time") is not None
        ]
        if len(null_pairs) >= 3:
            null_et_r = _pearson_r([p[0] for p in null_pairs],
                                   [p[1] for p in null_pairs])
            null_et_r_vals.append(abs(null_et_r or 0.0))

        null_clust_vals.append(_clustering_score(n_times) if n_times else 1.0)

    null_comparison = {
        "null_mode":         null_mode,
        "null_repeats":      null_repeats,
        "hemi_percentile":   _empirical_percentile(abs(hemi),         null_hemi_vals),
        "axis_percentile":   _empirical_percentile(axis_score,        null_axis_vals),
        "et_r_percentile":   _empirical_percentile(abs(et_r or 0.0),  null_et_r_vals),
        "clust_percentile":  _empirical_percentile(clust,             null_clust_vals),
        "null_axis_mean":    sum(null_axis_vals) / len(null_axis_vals) if null_axis_vals else None,
        "null_axis_std":     _std(null_axis_vals),
        "null_hemi_mean":    sum(null_hemi_vals) / len(null_hemi_vals) if null_hemi_vals else None,
    }

    signal_eval = _evaluate_signal_strength(null_comparison)
    exposure_model_meta = _null_model_metadata(null_mode, exposure_map)
    time_coverage = _time_coverage_refinement(events)
    promotion_blockers = _mission_grade_promotion_blockers(
        null_mode=null_mode,
        exposure_model=exposure_model_meta,
        time_coverage=time_coverage,
    )

    return {
        "event_count":           len(events),
        "events_with_energy":    len(energies),
        "events_with_position":  len(ras),
        "events_with_time":      len(times),
        "energy_stats":          energy_stats,
        "anisotropy": {
            "hemisphere_imbalance": hemi,
            "interpretation": (
                "Fraction of events in north minus south hemisphere. "
                "0 = balanced, ±1 = all in one hemisphere."
            ),
        },
        "preferred_axis": {
            "score": axis_score,
            "best_axis_xyz": axis_scan_obs["best_axis_xyz"],
            "num_axes_scanned": axis_scan_obs["num_axes"],
            "interpretation": (
                "Max |mean cos-projection| across trial axes. "
                "Isotropic ≈ 0; perfect alignment ≈ 1."
            ),
        },
        "axis_scan": axis_scan_obs,
        "energy_time_correlation": {
            "pearson_r": et_r,
            "interpretation": (
                "Pearson r between energy and arrival_time. "
                "Non-zero may indicate energy-dependent propagation effects."
            ),
        },
        "cluster_score": {
            "value": clust,
            "interpretation": (
                "Mean window count / expected-random. "
                "≈1.0 = uniform; >1.0 = clustered."
            ),
        },
        "null_comparison": null_comparison,
        "signal_evaluation": signal_eval,
        "run_metadata": {
            "seed":              rng_seed,
            "null_repeats":      null_repeats,
            "num_axes":          num_axes,
            "axis_mode":         axis_mode,
            "healpix_nside":     healpix_nside,
            "axis_plan":         axis_scan_obs.get("axis_plan"),
            "null_mode":         null_mode,
            "exposure_model":    exposure_model_meta,
            "time_coverage_refinement": time_coverage,
            "mission_grade_promotion_blockers": promotion_blockers,
            "exposure_map_desc": exposure_map_desc,
            "timestamp":         datetime.datetime.utcnow().isoformat() + "Z",
        },
    }


# =========================================================================
# Signal strength evaluation (mirrors simulation_signature_analysis.py)
# =========================================================================

def _evaluate_signal_strength(null_comparison: Dict[str, Any]) -> Dict[str, Any]:
    """Return a plain-language tier classification from null-comparison percentiles."""
    null_mode = null_comparison.get("null_mode", "isotropic")
    null_label = "exposure-corrected" if null_mode == "exposure_corrected" else "isotropic"

    percentiles = {
        "hemisphere_imbalance": null_comparison.get("hemi_percentile", 0.5),
        "preferred_axis":       null_comparison.get("axis_percentile", 0.5),
        "energy_time_r":        null_comparison.get("et_r_percentile", 0.5),
        "clustering":           null_comparison.get("clust_percentile", 0.5),
    }
    max_pval = max(percentiles.values()) if percentiles else 0.5

    if max_pval >= 0.97:
        tier    = TIER_STRONG
        summary = (
            f"One or more metrics fall in the top 3% of the {null_label} null distribution. "
            "This is a strong anomaly-like deviation; its cause requires further investigation."
        )
    elif max_pval >= 0.90:
        tier    = TIER_MODERATE
        summary = (
            f"One or more metrics fall in the top 10% of the {null_label} null distribution. "
            "Moderate anomaly-like deviation; warrants follow-up."
        )
    elif max_pval >= 0.75:
        tier    = TIER_WEAK
        summary = (
            f"One or more metrics fall in the top 25% of the {null_label} null distribution. "
            "Weak deviation; consistent with statistical fluctuation."
        )
    else:
        tier    = TIER_NONE
        summary = (
            f"All metrics are within the bulk of the {null_label} null distribution. "
            "No significant anomaly detected."
        )

    return {
        "tier":                    tier,
        "max_percentile":          max_pval,
        "per_metric_percentiles":  percentiles,
        "summary": summary,
        "caveat": (
            "Anomaly-like deviations from an isotropic null are hypothesis-generating "
            "results, not proof of any specific physical or cosmological cause. "
            "Systematic effects, selection biases, and incomplete modeling should be "
            "ruled out before drawing any scientific conclusion."
        ),
    }


# =========================================================================
# Artifact writer
# =========================================================================

def write_public_study_artifacts(
    results: Dict[str, Any],
    events: List[Dict[str, Any]],
    null_events_example: Optional[List[Dict[str, Any]]],
    output_dir: str,
    name: str = "public_anisotropy",
    plots_enabled: bool = True,
    config: Optional[Dict[str, Any]] = None,
    catalog_name: str = "unknown",
    coverage: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    """Save all artifact files for a public anisotropy study run.

    Artifacts produced:
      - JSON report (<name>_summary.json)
      - CSV summary row (<name>_results.csv)
      - Markdown summary (<name>_summary.md)
      - Sky plot (<name>_sky_plot.png)       (if plots_enabled and matplotlib)
      - Null comparison plot (<name>_null_comparison.png)
      - Axis scan plot (<name>_axis_scan.png)
      - Manifest (<name>_manifest.json)

    Returns a dict mapping artifact_type → file path.
    """
    os.makedirs(output_dir, exist_ok=True)
    ts        = datetime.datetime.utcnow().isoformat() + "Z"
    manifest: Dict[str, str] = {}

    # ---- JSON summary ----
    json_payload = {
        "experiment":    name,
        "catalog":       catalog_name,
        "written_at":    ts,
        "results":       results,
        "coverage":      coverage or {},
        "config":        config or {},
    }
    json_path = os.path.join(output_dir, f"{name}_summary.json")
    with open(json_path, "w") as f:
        json.dump(json_payload, f, indent=2)
    manifest["json_summary"] = json_path

    # ---- CSV summary ----
    sig_eval = results.get("signal_evaluation", {})
    nc       = results.get("null_comparison", {})
    csv_row  = {
        "name":                    name,
        "catalog":                 catalog_name,
        "written_at":              ts,
        "event_count":             results.get("event_count", 0),
        "hemisphere_imbalance":    results.get("anisotropy", {}).get("hemisphere_imbalance", ""),
        "preferred_axis_score":    results.get("preferred_axis", {}).get("score", ""),
        "energy_time_r":           results.get("energy_time_correlation", {}).get("pearson_r", ""),
        "cluster_score":           results.get("cluster_score", {}).get("value", ""),
        "hemi_percentile":         nc.get("hemi_percentile", ""),
        "axis_percentile":         nc.get("axis_percentile", ""),
        "et_r_percentile":         nc.get("et_r_percentile", ""),
        "clust_percentile":        nc.get("clust_percentile", ""),
        "signal_tier":             sig_eval.get("tier", ""),
        "max_percentile":          sig_eval.get("max_percentile", ""),
    }
    csv_path = os.path.join(output_dir, f"{name}_results.csv")
    write_header = not os.path.exists(csv_path)
    with open(csv_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(csv_row.keys()))
        if write_header:
            writer.writeheader()
        writer.writerow(csv_row)
    manifest["csv_summary"] = csv_path

    # ---- Markdown summary ----
    md_path = os.path.join(output_dir, f"{name}_summary.md")
    _write_markdown_summary(
        md_path, name=name, catalog_name=catalog_name,
        results=results, ts=ts, coverage=coverage,
    )
    manifest["md_summary"] = md_path

    # ---- Plots ----
    if plots_enabled and _HAS_MPL:
        ras  = [e["ra"]  for e in events if e.get("ra")  is not None]
        decs = [e["dec"] for e in events if e.get("dec") is not None]

        # Sky plot
        sky_path = os.path.join(output_dir, f"{name}_sky_plot.png")
        _plot_sky(ras, decs, sky_path, title=f"{name}: event sky positions")
        manifest["sky_plot"] = sky_path

        # Null comparison
        null_path = os.path.join(output_dir, f"{name}_null_comparison.png")
        _plot_null_comparison(results, null_path, name=name)
        manifest["null_comparison_plot"] = null_path

        # Axis scan
        axis_scan = results.get("axis_scan", {})
        if axis_scan.get("all_scores"):
            ax_path = os.path.join(output_dir, f"{name}_axis_scan.png")
            _plot_axis_scan(axis_scan, ax_path, name=name)
            manifest["axis_scan_plot"] = ax_path

    # ---- Manifest ----
    manifest_path = os.path.join(output_dir, f"{name}_manifest.json")
    manifest["manifest"] = manifest_path
    with open(manifest_path, "w") as f:
        json.dump(
            {"experiment": name, "catalog": catalog_name,
             "written_at": ts, "artifacts": manifest},
            f, indent=2,
        )

    return manifest


# =========================================================================
# Plot helpers
# =========================================================================

def _plot_sky(
    ras: List[float],
    decs: List[float],
    path: str,
    title: str = "Event sky positions",
) -> None:
    """Produce a simple equatorial RA/Dec scatter plot."""
    fig, ax = plt.subplots(figsize=(10, 5))
    if ras:
        # Convert RA to [-180, 180] for centred plot
        ra_plot = [(r - 180.0) for r in ras]
        ax.scatter(ra_plot, decs, s=4, alpha=0.5, color="steelblue")
    ax.set_xlabel("RA − 180° (deg)")
    ax.set_ylabel("Dec (deg)")
    ax.set_title(title)
    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    ax.axhline(0, color="gray", linewidth=0.5, linestyle="--")
    ax.axvline(0, color="gray", linewidth=0.5, linestyle="--")
    fig.tight_layout()
    fig.savefig(path, dpi=100)
    plt.close(fig)


def _plot_null_comparison(
    results: Dict[str, Any],
    path: str,
    name: str = "",
) -> None:
    """Bar chart comparing observed metric vs null mean ± std for key metrics."""
    nc    = results.get("null_comparison", {})
    sig   = results.get("signal_evaluation", {})
    percs = sig.get("per_metric_percentiles", {})

    labels  = list(percs.keys())
    obs_pct = [percs[l] for l in labels]

    fig, ax = plt.subplots(figsize=(8, 4))
    x = list(range(len(labels)))
    bars = ax.bar(x, obs_pct, color="steelblue", alpha=0.8)
    ax.axhline(0.90, color="orange", linestyle="--", linewidth=1,
               label="0.90 threshold (moderate)")
    ax.axhline(0.97, color="red", linestyle="--", linewidth=1,
               label="0.97 threshold (strong)")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20, ha="right")
    ax.set_ylabel("Empirical percentile vs isotropic null")
    ax.set_ylim(0, 1.05)
    ax.set_title(f"{name}: metric percentiles vs null")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=100)
    plt.close(fig)


def _plot_axis_scan(
    axis_scan: Dict[str, Any],
    path: str,
    name: str = "",
) -> None:
    """Line plot of axis scores across all trial axes."""
    scores = axis_scan.get("all_scores", [])
    best   = axis_scan.get("best_axis_index", 0)

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(scores, color="steelblue", linewidth=0.8, alpha=0.8)
    if 0 <= best < len(scores):
        ax.axvline(best, color="red", linestyle="--", linewidth=1,
                   label=f"Best axis (idx {best}, score={scores[best]:.4f})")
    ax.set_xlabel("Trial axis index")
    ax.set_ylabel("|mean cos-projection|")
    ax.set_title(f"{name}: axis scan scores")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=100)
    plt.close(fig)


# =========================================================================
# Markdown report writer
# =========================================================================

def _write_markdown_summary(
    path: str,
    name: str,
    catalog_name: str,
    results: Dict[str, Any],
    ts: str,
    coverage: Optional[Dict[str, Any]] = None,
) -> None:
    sig_eval = results.get("signal_evaluation", {})
    nc       = results.get("null_comparison", {})
    pa       = results.get("preferred_axis", {})
    ani      = results.get("anisotropy", {})
    cs       = results.get("cluster_score", {})
    etcor    = results.get("energy_time_correlation", {})
    percs    = sig_eval.get("per_metric_percentiles", {})

    lines = [
        f"# Public Anisotropy Study: {name}",
        "",
        f"**Catalog:** {catalog_name}  ",
        f"**Generated:** {ts}  ",
        f"**Events:** {results.get('event_count', 0)}  ",
        f"**Signal tier:** `{sig_eval.get('tier', 'unknown')}`  ",
        f"**Max percentile:** {sig_eval.get('max_percentile', 0.0):.4f}",
        "",
        "## Summary",
        "",
        sig_eval.get("summary", ""),
        "",
        "## Metric values",
        "",
        "| Metric | Observed | Percentile vs null |",
        "|--------|----------|--------------------|",
        f"| Hemisphere imbalance | {ani.get('hemisphere_imbalance', '')!s:.6} | {percs.get('hemisphere_imbalance', '')!s:.4} |",
        f"| Preferred-axis score ({pa.get('num_axes_scanned', '?')} axes) | {pa.get('score', '')!s:.6} | {percs.get('preferred_axis', '')!s:.4} |",
        f"| Energy–time Pearson r | {etcor.get('pearson_r', '')!s:.6} | {percs.get('energy_time_r', '')!s:.4} |",
        f"| Clustering score | {cs.get('value', '')!s:.6} | {percs.get('clustering', '')!s:.4} |",
        "",
        "## Null model",
        "",
        f"- Mode: {nc.get('null_mode', 'isotropic')}",
        f"- Repeats: {nc.get('null_repeats', '?')}",
        f"- Null axis score mean: {nc.get('null_axis_mean', '?')!s:.4}",
        "",
    ]

    if coverage:
        lines += [
            "## Catalog coverage",
            "",
            f"- Events: {coverage.get('event_count', '?')}",
            f"- Instruments: {', '.join(str(x) for x in coverage.get('instrument_labels', []))}",
        ]
        time_span = coverage.get("time_span_mjd", {})
        if time_span.get("n_with_time"):
            lines.append(
                f"- Time span: MJD {time_span.get('t_min_mjd', '?'):.2f} – "
                f"{time_span.get('t_max_mjd', '?'):.2f} "
                f"({time_span.get('span_days', '?'):.1f} days)"
            )
        lines.append("")

    lines += [
        "## Caveat",
        "",
        sig_eval.get("caveat", ""),
        "",
    ]

    with open(path, "w") as f:
        f.write("\n".join(lines))


# =========================================================================
# Utility
# =========================================================================

def _std(values: List[float]) -> Optional[float]:
    if not values:
        return None
    mean = sum(values) / len(values)
    var  = sum((v - mean) ** 2 for v in values) / len(values)
    return math.sqrt(var)
