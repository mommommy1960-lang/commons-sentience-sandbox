"""
exposure_corrected_nulls.py
============================
Empirical exposure-proxy null model for the Reality Audit public anisotropy
pipeline.

Background
----------
A naive isotropic null places events uniformly on the whole sphere.  The
Fermi GBM and similar wide-field detectors do NOT observe the sky uniformly:
Earth occultation, detector orientation, LAT trigger bias, and other effects
create a non-uniform sky acceptance.  When the null is isotropic but the
detector is not, the null comparison is misleading — effectively comparing
the real data against a sky it was never designed to observe uniformly.

This module provides an empirical first-order correction: construct a simple
sky-acceptance *proxy* map by histogramming the observed events themselves,
then re-sample that map to produce null realisations.  This is conceptually
similar to "bootstrap" null generation, except that we sample from the
spatial distribution rather than from the data directly, and we re-randomise
the non-position fields.

IMPORTANT LIMITATIONS (explicitly stated)
------------------------------------------
1. The map is built from the data under test, so it absorbs both instrument
   acceptance *and* any genuine anisotropy signal.  It is a conservative but
   self-consistent correction: it tests whether a pattern is stronger than
   expected given the *observed* spatial distribution, not whether it deviates
   from uniform.
2. It is NOT a mission-grade exposure model.  It does not account for
   time-varying orientation, spectral selection, trigger efficiency curves, or
   Earth-limb effects.
3. The correction is sufficient for internal first-results work (Stage 9
   robustness check), but should be replaced with an instrument-response-
   weighted null before any publishable results claim.
4. Results from this null are usefully interpreted as: "is there a pattern
   beyond what the observed sky coverage would predict?"

Author: commons-sentience-sandbox
"""

from __future__ import annotations

import math
import random
from typing import Any, Dict, List, Optional, Tuple


# =========================================================================
# 1. Build empirical exposure proxy map
# =========================================================================

def build_empirical_exposure_map(
    events: List[Dict[str, Any]],
    ra_bins: int = 24,
    dec_bins: int = 12,
    floor_value: Optional[float] = None,
    calibration_name: str = "empirical_floor_v1",
) -> Dict[str, Any]:
    """Build a coarse empirical sky-acceptance proxy map from the observed events.

    Method
    ------
    The sky is divided into ``ra_bins × dec_bins`` rectangular cells in RA
    (0–360°) and Dec (−90–+90°).  Each cell is assigned a weight equal to
    the number of observed events it contains.  The weight array is normalised
    to sum to 1 for use as a sampling probability distribution.

    Empty cells are assigned a floor weight of
    ``floor_fraction / (ra_bins * dec_bins)`` of the total count, so that
    sky regions near the edge of coverage are not completely excluded.

    Parameters
    ----------
    events   : normalised event list with 'ra' and 'dec' keys (degrees)
    ra_bins  : number of RA bins (default 24 → 15°/bin)
    dec_bins : number of Dec bins (default 12 → 15°/bin)

    Returns
    -------
    Dict with keys:
        ra_bins         – int
        dec_bins        – int
        weights         – flat list of (ra_bins × dec_bins) normalised weights
        cell_counts     – corresponding raw event counts per cell
        n_events_used   – number of events with valid RA/Dec
        ra_edges        – list of ra_bins+1 bin edges (degrees)
        dec_edges       – list of dec_bins+1 bin edges (degrees)
        description     – human-readable summary
        limitations     – explicit list of limitations
    """
    if ra_bins < 2 or dec_bins < 2:
        raise ValueError("ra_bins and dec_bins must each be ≥ 2.")
    if floor_value is None:
        floor_value = 0.5
    try:
        floor_value = float(floor_value)
    except (TypeError, ValueError):
        raise ValueError("floor_value must be numeric.")
    if floor_value < 0.0:
        raise ValueError("floor_value must be >= 0.")

    ra_edges  = [360.0 * i / ra_bins  for i in range(ra_bins + 1)]
    dec_edges = [-90.0 + 180.0 * i / dec_bins for i in range(dec_bins + 1)]

    # Count events per cell
    counts = [[0] * ra_bins for _ in range(dec_bins)]
    n_used = 0
    for e in events:
        ra  = e.get("ra")
        dec = e.get("dec")
        if ra is None or dec is None:
            continue
        try:
            ra_f  = float(ra)  % 360.0
            dec_f = float(dec)
        except (TypeError, ValueError):
            continue
        if not (-90.0 <= dec_f <= 90.0):
            continue
        # Bin lookup
        ra_idx  = min(int(ra_f  / 360.0 * ra_bins),  ra_bins  - 1)
        dec_idx = min(int((dec_f + 90.0) / 180.0 * dec_bins), dec_bins - 1)
        counts[dec_idx][ra_idx] += 1
        n_used += 1

    if n_used == 0:
        # Fallback: uniform weights (isotropic)
        total_cells = ra_bins * dec_bins
        flat_weights = [1.0 / total_cells] * total_cells
        flat_counts  = [0] * total_cells
        return {
            "ra_bins":       ra_bins,
            "dec_bins":      dec_bins,
            "weights":       flat_weights,
            "cell_counts":   flat_counts,
            "n_events_used": 0,
            "ra_edges":      ra_edges,
            "dec_edges":     dec_edges,
            "description":   "Fallback uniform weights (no events with RA/Dec).",
            "limitations":   _LIMITATIONS,
            "exposure_model": {
                "name": "empirical_proxy_histogram",
                "version": "v1",
                "calibration": {
                    "name": calibration_name,
                    "floor_value": floor_value,
                    "notes": "Uniform fallback due to no valid RA/Dec.",
                },
            },
        }

    flat_counts: List[float] = []
    for di in range(dec_bins):
        for ri in range(ra_bins):
            flat_counts.append(float(counts[di][ri]))

    # Apply floor
    floored = [c + floor_value for c in flat_counts]
    total   = sum(floored)
    weights = [w / total for w in floored]

    return {
        "ra_bins":       ra_bins,
        "dec_bins":      dec_bins,
        "weights":       weights,
        "cell_counts":   [int(c) for c in flat_counts],
        "n_events_used": n_used,
        "ra_edges":      ra_edges,
        "dec_edges":     dec_edges,
        "description": (
            f"Empirical sky-acceptance proxy built from {n_used} events "
            f"in a {ra_bins}×{dec_bins} RA×Dec grid "
            f"(floor_value={floor_value} per cell)."
        ),
        "limitations": _LIMITATIONS,
        "exposure_model": {
            "name": "empirical_proxy_histogram",
            "version": "v1",
            "calibration": {
                "name": calibration_name,
                "floor_value": floor_value,
            },
        },
    }


_LIMITATIONS = [
    "Map is built from the data under test: absorbs instrument acceptance "
    "AND any genuine signal.",
    "Conservative test: 'is pattern stronger than the observed sky coverage?'",
    "Does not model time-varying orientation, trigger efficiency, or spectral selection.",
    "Not a mission-grade exposure model; suitable for Stage 9 internal robustness only.",
    "Empty-cell floor weight prevents complete exclusion of sparsely observed regions.",
]


# =========================================================================
# 2. Sample exposure-weighted null events
# =========================================================================

def sample_exposure_weighted_null_events(
    events: List[Dict[str, Any]],
    exposure_map: Dict[str, Any],
    seed: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Generate one null realisation by sampling sky positions from the exposure map.

    Each null event is a copy of a randomly chosen real event with its RA and
    Dec replaced by a position drawn from the exposure-map distribution.  The
    non-position fields (energy, arrival_time, instrument, etc.) are preserved
    as-is.  This keeps the energy and time distributions identical to the real
    data, isolating the test to the spatial dimension only.

    Parameters
    ----------
    events       : normalised event list
    exposure_map : output of build_empirical_exposure_map
    seed         : RNG seed

    Returns
    -------
    List of dicts in the same schema as the input events.
    """
    rng        = random.Random(seed)
    ra_bins    = exposure_map["ra_bins"]
    dec_bins   = exposure_map["dec_bins"]
    weights    = exposure_map["weights"]
    ra_edges   = exposure_map["ra_edges"]
    dec_edges  = exposure_map["dec_edges"]

    # Pre-build cumulative distribution for fast sampling
    cum = []
    running = 0.0
    for w in weights:
        running += w
        cum.append(running)

    n_cells = ra_bins * dec_bins
    assert len(cum) == n_cells

    null_events: List[Dict[str, Any]] = []
    for orig in events:
        # Sample a cell index using the CDF
        u = rng.random()
        cell_idx = _bisect(cum, u)
        cell_idx = min(cell_idx, n_cells - 1)

        dec_i = cell_idx // ra_bins
        ra_i  = cell_idx %  ra_bins

        # Uniform within the chosen cell
        ra_lo  = ra_edges[ra_i];   ra_hi  = ra_edges[ra_i  + 1]
        dec_lo = dec_edges[dec_i]; dec_hi = dec_edges[dec_i + 1]

        new_ra  = rng.uniform(ra_lo,  ra_hi)
        new_dec = rng.uniform(dec_lo, dec_hi)

        null_event = dict(orig)
        null_event["ra"]  = new_ra
        null_event["dec"] = new_dec
        null_events.append(null_event)

    return null_events


def _bisect(cum: List[float], u: float) -> int:
    """Return index i such that cum[i-1] <= u < cum[i] (binary search)."""
    lo, hi = 0, len(cum) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if cum[mid] < u:
            lo = mid + 1
        else:
            hi = mid
    return lo


# =========================================================================
# 3. Generate ensemble
# =========================================================================

def generate_exposure_corrected_null_ensemble(
    events: List[Dict[str, Any]],
    repeats: int = 100,
    seed: Optional[int] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Tuple[List[List[Dict[str, Any]]], Dict[str, Any]]:
    """Produce ``repeats`` exposure-corrected null realisations.

    Parameters
    ----------
    events  : normalised event list
    repeats : number of null draws
    seed    : RNG seed (each draw uses seed+rep for reproducibility)
    config  : optional dict with keys:
              - ra_bins (int, default 24)
              - dec_bins (int, default 12)
              - null_repeats (int, overrides repeats)

    Returns
    -------
    (ensemble, exposure_map) where:
      ensemble     – list of ``repeats`` null event lists
      exposure_map – the exposure map used (for reporting)
    """
    cfg       = config or {}
    ra_bins   = int(cfg.get("ra_bins",  24))
    dec_bins  = int(cfg.get("dec_bins", 12))
    floor_value = cfg.get("exposure_floor_value", cfg.get("floor_value", None))
    calibration_name = str(cfg.get("exposure_calibration", "empirical_floor_v1"))
    if "null_repeats" in cfg:
        repeats = int(cfg["null_repeats"])

    exposure_map = build_empirical_exposure_map(
        events,
        ra_bins=ra_bins,
        dec_bins=dec_bins,
        floor_value=floor_value,
        calibration_name=calibration_name,
    )

    ensemble: List[List[Dict[str, Any]]] = []
    for rep in range(repeats):
        ns = (seed + rep) if seed is not None else None
        null = sample_exposure_weighted_null_events(events, exposure_map, seed=ns)
        ensemble.append(null)

    return ensemble, exposure_map


# =========================================================================
# 4. Describe exposure map
# =========================================================================

def describe_exposure_map(exposure_map: Dict[str, Any]) -> Dict[str, Any]:
    """Summarise an exposure map for reporting.

    Returns a dict with:
      ra_bins, dec_bins, total_cells, n_events_used,
      n_occupied_cells, n_empty_cells, max_cell_weight,
      min_cell_weight, description, limitations
    """
    counts   = exposure_map.get("cell_counts", [])
    weights  = exposure_map.get("weights", [])
    n_occ    = sum(1 for c in counts if c > 0)
    n_empty  = sum(1 for c in counts if c == 0)
    total    = len(counts)

    return {
        "ra_bins":          exposure_map.get("ra_bins"),
        "dec_bins":         exposure_map.get("dec_bins"),
        "total_cells":      total,
        "n_events_used":    exposure_map.get("n_events_used", 0),
        "n_occupied_cells": n_occ,
        "n_empty_cells":    n_empty,
        "occupancy_fraction": n_occ / total if total > 0 else 0.0,
        "max_cell_weight":  max(weights) if weights else None,
        "min_cell_weight":  min(weights) if weights else None,
        "description":      exposure_map.get("description", ""),
        "limitations":      exposure_map.get("limitations", []),
        "exposure_model":   exposure_map.get("exposure_model"),
    }
