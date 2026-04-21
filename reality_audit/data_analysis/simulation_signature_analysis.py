"""
simulation_signature_analysis.py
=================================
First-pass statistical analysis pipeline for astrophysical event-style datasets.

Purpose
-------
Ingest, normalize, and statistically analyze event catalogs (e.g. GRB, cosmic-ray,
or simulated sky-survey data) to search for anomalies relative to simple null models.
This is a hypothesis-testing framework: detecting a statistically anomalous pattern
is NOT proof of a simulation hypothesis or any specific physical model.

Pipeline stages
---------------
1. load_event_dataset      – CSV or JSON → list of raw records
2. standardize_events      – normalize field names/types, add derived fields
3. generate_null_events    – isotropic sky null or shuffled-time null
4. inject_synthetic_anomaly – inject a known signal for pipeline validation
5. analyze_event_dataset   – compute anisotropy, clustering, energy-time metrics
6. evaluate_signal_strength – plain-language tier classification
7. write_analysis_artifacts – JSON report, CSV summary, Markdown, PNG plots

Statistical methods used
------------------------
All methods are simple and fully transparent:
  * Hemisphere imbalance ratio  – sky anisotropy proxy
  * Axis projection scan        – preferred-axis score (max cos-projection mean)
  * Pearson r                   – energy–time correlation
  * Mean nearest-neighbour count in time window – clustering score
  * Empirical percentile vs null distribution – null comparison p-like score

Author: commons-sentience-sandbox
"""

from __future__ import annotations

import csv
import datetime
import json
import math
import os
import random
import uuid
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Optional numpy – gracefully accepted but not required
# ---------------------------------------------------------------------------
try:
    import numpy as np
    _HAS_NUMPY = True
except ImportError:  # pragma: no cover
    _HAS_NUMPY = False

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    _HAS_MPL = True
except ImportError:  # pragma: no cover
    _HAS_MPL = False

# ---------------------------------------------------------------------------
# Constants / schema
# ---------------------------------------------------------------------------

EXPECTED_NUMERIC_FIELDS = {"energy", "arrival_time", "ra", "dec"}
SCHEMA_FIELDS = ["event_id", "energy", "arrival_time", "ra", "dec",
                 "instrument", "epoch"]

# Anomaly type labels
ANOMALY_PREFERRED_AXIS   = "preferred_axis"
ANOMALY_ENERGY_DELAY     = "energy_dependent_delay"
ANOMALY_CLUSTERED        = "clustered_arrivals"

# Signal strength tiers
TIER_NONE     = "no_anomaly_detected"
TIER_WEAK     = "weak_anomaly_like_deviation"
TIER_MODERATE = "moderate_anomaly_like_deviation"
TIER_STRONG   = "strong_anomaly_like_deviation"


# ===========================================================================
# STAGE 1 – Load
# ===========================================================================

def load_event_dataset(path: str) -> List[Dict[str, Any]]:
    """Load a CSV or JSON event catalog from disk.

    Expected fields (all optional except as noted):
      event_id     – str  (assigned automatically if absent)
      energy       – float, GeV or keV depending on survey
      arrival_time – float, seconds or MJD
      ra           – float, degrees [0, 360)
      dec          – float, degrees [-90, 90]
      instrument   – str
      epoch        – str or float

    Returns a list of raw record dicts; numeric coercion is deferred to
    ``standardize_events``.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Event dataset not found: {path}")

    ext = os.path.splitext(path)[1].lower()
    if ext == ".json":
        with open(path) as f:
            raw = json.load(f)
        if isinstance(raw, dict):
            # Wrapped format: {"events": [...]}
            records = raw.get("events", raw.get("data", [raw]))
        else:
            records = list(raw)
    elif ext == ".csv":
        records = []
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(dict(row))
    else:
        raise ValueError(f"Unsupported file extension: {ext!r} (expected .csv or .json)")

    return records


# ===========================================================================
# STAGE 2 – Standardize
# ===========================================================================

def standardize_events(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize field names/types and produce a consistent schema.

    - Coerces numeric fields to float where possible.
    - Assigns synthetic event_id if missing.
    - Adds ``_source_index`` derived field.
    - Records any fields that could not be coerced in ``_parse_warnings``.
    - All unknown/extra fields are preserved as-is.
    """
    standardized = []
    for i, raw in enumerate(events):
        rec: Dict[str, Any] = {}

        # Preserve all original keys
        for k, v in raw.items():
            rec[k.strip().lower()] = v

        # Ensure event_id
        if "event_id" not in rec or rec["event_id"] in ("", None):
            rec["event_id"] = f"evt_{i:06d}"

        # Coerce numeric fields
        warnings = []
        for field in EXPECTED_NUMERIC_FIELDS:
            if field in rec:
                try:
                    rec[field] = float(rec[field])
                except (ValueError, TypeError):
                    warnings.append(f"Cannot coerce {field}={rec[field]!r}")
                    rec[field] = None

        # Derived: galactic-proxy b_proxy (±90 fold of dec)
        if rec.get("dec") is not None:
            rec["_b_proxy"] = abs(float(rec["dec"]))  # crude |b| proxy

        rec["_source_index"] = i
        rec["_parse_warnings"] = warnings
        standardized.append(rec)

    return standardized


# ===========================================================================
# STAGE 3 – Null generation
# ===========================================================================

def generate_null_events(
    events: List[Dict[str, Any]],
    mode: str = "isotropic",
    seed: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Generate a null-hypothesis comparison dataset.

    Parameters
    ----------
    events : standardized event list (provides size and field ranges)
    mode   : "isotropic"     – uniform RA/Dec on sphere, same energy/time range
             "shuffled_time" – real RA/Dec and energy but shuffled arrival times
    seed   : RNG seed for reproducibility

    Returns a list of dicts with the same schema, tagged with
    ``_null_model = mode``.
    """
    rng = random.Random(seed)
    n = len(events)

    # Collect ranges from actual data
    energies      = [e["energy"]       for e in events if e.get("energy")       is not None]
    times         = [e["arrival_time"] for e in events if e.get("arrival_time") is not None]
    ras            = [e["ra"]           for e in events if e.get("ra")           is not None]
    decs           = [e["dec"]          for e in events if e.get("dec")          is not None]
    instruments   = list({e.get("instrument", "null_instrument") for e in events})
    epochs        = list({e.get("epoch", "null_epoch") for e in events})

    e_min = min(energies)      if energies else 0.0
    e_max = max(energies)      if energies else 1.0
    t_min = min(times)         if times    else 0.0
    t_max = max(times)         if times    else 1.0

    null_events = []
    for i in range(n):
        rec: Dict[str, Any] = {}
        rec["event_id"]     = f"null_{i:06d}"
        rec["_null_model"]  = mode
        rec["_source_index"]= i

        # Energy: sample power-law-like by log-uniform in observed range
        if energies:
            log_min = math.log(max(e_min, 1e-10))
            log_max = math.log(max(e_max, 1e-10))
            rec["energy"] = math.exp(rng.uniform(log_min, log_max))
        else:
            rec["energy"] = None

        # Arrival time
        if mode == "shuffled_time":
            # Shuffle real times; re-draw without replacement
            times_shuffled = list(times)
            rng.shuffle(times_shuffled)
            rec["arrival_time"] = times_shuffled[i % len(times_shuffled)] if times_shuffled else None
            if ras:
                rec["ra"]  = ras[i % len(ras)]
                rec["dec"] = decs[i % len(decs)] if decs else 0.0
        else:
            # isotropic: uniform on sphere
            rec["arrival_time"] = rng.uniform(t_min, t_max) if times else None
            cos_dec = rng.uniform(-1.0, 1.0)
            rec["dec"] = math.degrees(math.asin(cos_dec))
            rec["ra"]  = rng.uniform(0.0, 360.0)

        rec["_b_proxy"] = abs(rec["dec"]) if rec.get("dec") is not None else None
        rec["instrument"]    = rng.choice(instruments) if instruments else "null"
        rec["epoch"]         = rng.choice(epochs)      if epochs      else "null"
        rec["_parse_warnings"] = []

        null_events.append(rec)

    return null_events


# ===========================================================================
# STAGE 4 – Synthetic anomaly injection
# ===========================================================================

def inject_synthetic_anomaly(
    events: List[Dict[str, Any]],
    anomaly_type: str,
    strength: float = 0.5,
    seed: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Inject a known synthetic signal into an event list.

    This is for pipeline validation: inject then check that analysis
    detects the injected signal.

    Parameters
    ----------
    events       : standardized event list (will NOT be mutated)
    anomaly_type : one of ANOMALY_PREFERRED_AXIS, ANOMALY_ENERGY_DELAY,
                   ANOMALY_CLUSTERED
    strength     : mixing fraction in [0, 1]  (0 = no change, 1 = full signal)
    seed         : RNG seed

    Returns a deep-copied modified event list with ``_injected_anomaly``
    metadata added to each affected record.
    """
    import copy
    if anomaly_type not in (ANOMALY_PREFERRED_AXIS, ANOMALY_ENERGY_DELAY, ANOMALY_CLUSTERED):
        raise ValueError(f"Unknown anomaly_type: {anomaly_type!r}. "
                         f"Choose from: {ANOMALY_PREFERRED_AXIS!r}, "
                         f"{ANOMALY_ENERGY_DELAY!r}, {ANOMALY_CLUSTERED!r}")

    rng = random.Random(seed)
    modified = copy.deepcopy(events)
    n = len(modified)

    metadata = {
        "anomaly_type": anomaly_type,
        "strength": strength,
        "seed": seed,
        "n_affected": 0,
    }

    if anomaly_type == ANOMALY_PREFERRED_AXIS:
        # Pull a fraction of events toward RA=45°, Dec=30° (arbitrary preferred axis)
        axis_ra, axis_dec = 45.0, 30.0
        for rec in modified:
            if rec.get("ra") is None or rec.get("dec") is None:
                continue
            if rng.random() < strength:
                t = rng.uniform(0.0, 1.0)
                rec["ra"]  = rec["ra"]  * (1 - t) + axis_ra  * t
                rec["dec"] = rec["dec"] * (1 - t) + axis_dec * t
                rec["_b_proxy"] = abs(rec["dec"])
                rec["_injected_anomaly"] = anomaly_type
                metadata["n_affected"] += 1

    elif anomaly_type == ANOMALY_ENERGY_DELAY:
        # Higher-energy events arrive earlier: delta_t = -strength * energy_rank * scale
        valid = [r for r in modified if r.get("energy") is not None
                 and r.get("arrival_time") is not None]
        if valid:
            energies = [r["energy"] for r in valid]
            e_range = max(energies) - min(energies) or 1.0
            t_range = max(r["arrival_time"] for r in valid) - \
                      min(r["arrival_time"] for r in valid) or 1.0
            scale = strength * t_range * 0.5
            for rec in modified:
                if rec.get("energy") is None or rec.get("arrival_time") is None:
                    continue
                energy_norm = (rec["energy"] - min(energies)) / e_range  # 0–1
                rec["arrival_time"] = rec["arrival_time"] - scale * energy_norm
                rec["_injected_anomaly"] = anomaly_type
                metadata["n_affected"] += 1

    elif anomaly_type == ANOMALY_CLUSTERED:
        # Pull a fraction of events in arrival_time toward a cluster center
        times = [r["arrival_time"] for r in modified if r.get("arrival_time") is not None]
        if times:
            t_center = (max(times) + min(times)) / 2.0
            t_width = (max(times) - min(times)) * 0.05  # cluster within 5% of range
            for rec in modified:
                if rec.get("arrival_time") is None:
                    continue
                if rng.random() < strength * 0.4:
                    rec["arrival_time"] = t_center + rng.gauss(0.0, t_width)
                    rec["_injected_anomaly"] = anomaly_type
                    metadata["n_affected"] += 1

    # Tag all records with injection metadata
    for rec in modified:
        rec["_injection_metadata"] = metadata

    return modified


# ===========================================================================
# STAGE 5 – Statistical analysis
# ===========================================================================

def _pearson_r(xs: List[float], ys: List[float]) -> Optional[float]:
    """Compute Pearson correlation coefficient between two equal-length lists."""
    n = len(xs)
    if n < 3:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    cov  = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    var_x = sum((x - mx) ** 2 for x in xs)
    var_y = sum((y - my) ** 2 for y in ys)
    denom = math.sqrt(var_x * var_y) if var_x > 0 and var_y > 0 else 0.0
    return cov / denom if denom > 0 else 0.0


def _hemisphere_imbalance(ra_list: List[float], dec_list: List[float]) -> float:
    """Fraction of events in north hemisphere minus fraction in south.

    0.0 = perfectly balanced; ±1.0 = all events in one hemisphere.
    """
    if not ra_list:
        return 0.0
    north = sum(1 for d in dec_list if d >= 0)
    south = len(dec_list) - north
    return (north - south) / len(dec_list)


def _preferred_axis_score(ra_list: List[float], dec_list: List[float]) -> float:
    """Scan 12 trial axes and return max |mean projection|.

    Simple approach: project unit vectors onto trial axes sampled on a coarse
    grid.  Returns a value in [0, 1]; higher = more concentrated toward some axis.
    """
    if not ra_list:
        return 0.0
    # Convert RA/Dec to unit vectors
    vecs = []
    for ra, dec in zip(ra_list, dec_list):
        ra_r  = math.radians(ra)
        dec_r = math.radians(dec)
        vecs.append((
            math.cos(dec_r) * math.cos(ra_r),
            math.cos(dec_r) * math.sin(ra_r),
            math.sin(dec_r),
        ))
    # Trial axes: 12 points on a coarse icosahedron-like grid
    trial_axes = [
        (1, 0, 0), (-1, 0, 0),
        (0, 1, 0), (0, -1, 0),
        (0, 0, 1), (0, 0, -1),
        (1, 1, 0), (-1, 1, 0),
        (1, 0, 1), (0, 1, 1),
        (1, 1, 1), (-1, -1, 1),
    ]
    best = 0.0
    for ax in trial_axes:
        norm = math.sqrt(sum(a ** 2 for a in ax))
        ax_unit = tuple(a / norm for a in ax)
        projections = [sum(v[k] * ax_unit[k] for k in range(3)) for v in vecs]
        mean_proj = abs(sum(projections) / len(projections))
        if mean_proj > best:
            best = mean_proj
    return best


def _clustering_score(
    times: List[float],
    window_fraction: float = 0.05,
) -> float:
    """Mean fraction of events that fall within a time window around each event.

    A uniform distribution gives window_fraction; clustering gives a higher score.
    Normalized so that random ≈ 1.0, clustered > 1.0.
    """
    if len(times) < 2:
        return 1.0
    t_sorted = sorted(times)
    t_range = t_sorted[-1] - t_sorted[0]
    if t_range == 0:
        return float(len(times))
    window = t_range * window_fraction
    n = len(t_sorted)
    counts = []
    for t in t_sorted:
        c = sum(1 for ot in t_sorted if abs(ot - t) <= window)
        counts.append(c)
    mean_count = sum(counts) / n
    expected = n * window_fraction * 2  # both sides
    return mean_count / max(expected, 1.0)


def _empirical_percentile(
    observed_value: float,
    null_values: List[float],
    higher_is_signal: bool = True,
) -> float:
    """Return the fraction of null_values *below* the observed value.

    For higher_is_signal=True: percentile close to 1.0 means the observed
    value is anomalously high relative to null.  This is an empirical p-value
    proxy (= 1 - fraction_below).
    """
    if not null_values:
        return 0.5
    frac = sum(1 for v in null_values if v < observed_value) / len(null_values)
    return frac


def analyze_event_dataset(
    events: List[Dict[str, Any]],
    reference_events: Optional[List[Dict[str, Any]]] = None,
    config: Optional[Dict[str, Any]] = None,
    null_repeats: int = 25,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """Compute first-pass anomaly metrics.

    Parameters
    ----------
    events            : primary (observed or injected) event list
    reference_events  : pre-generated null dataset (optional; generated here if None)
    config            : optional config dict (null_mode, null_repeats etc.)
    null_repeats      : how many independent null draws for empirical percentile
    seed              : RNG seed

    Returns a results dict with keys:
      event_count, energy_stats, anisotropy, preferred_axis, energy_time_r,
      cluster_score, null_comparison, anomaly_injected
    """
    cfg = config or {}
    null_mode = cfg.get("null_mode", "isotropic")
    if config and "null_repeats" in config:
        null_repeats = config["null_repeats"]

    rng_seed = seed if seed is not None else cfg.get("seed", None)

    # --- collect valid field vectors ---
    energies = [e["energy"] for e in events if e.get("energy") is not None]
    times    = [e["arrival_time"] for e in events if e.get("arrival_time") is not None]
    ras      = [e["ra"]  for e in events if e.get("ra")  is not None]
    decs     = [e["dec"] for e in events if e.get("dec") is not None]

    # --- energy summary ---
    energy_stats: Dict[str, Any] = {}
    if energies:
        energy_stats["count"]  = len(energies)
        energy_stats["min"]    = min(energies)
        energy_stats["max"]    = max(energies)
        energy_stats["mean"]   = sum(energies) / len(energies)
        sorted_e = sorted(energies)
        mid = len(sorted_e) // 2
        energy_stats["median"] = (sorted_e[mid] + sorted_e[mid - 1]) / 2 \
                                 if len(sorted_e) % 2 == 0 else sorted_e[mid]
        var = sum((e - energy_stats["mean"]) ** 2 for e in energies) / len(energies)
        energy_stats["std"] = math.sqrt(var)

    # --- primary metrics ---
    hemi = _hemisphere_imbalance(ras, decs)
    axis_score = _preferred_axis_score(ras, decs)
    et_r = _pearson_r(
        [e["energy"]       for e in events if e.get("energy") is not None
         and e.get("arrival_time") is not None],
        [e["arrival_time"] for e in events if e.get("energy") is not None
         and e.get("arrival_time") is not None],
    )
    clust = _clustering_score(times)

    # --- null comparison ---
    null_hemi_vals:   List[float] = []
    null_axis_vals:   List[float] = []
    null_et_r_vals:   List[float] = []
    null_clust_vals:  List[float] = []

    for rep in range(null_repeats):
        ns = rng_seed + rep if rng_seed is not None else None
        null = reference_events if reference_events is not None and rep == 0 \
               else generate_null_events(events, mode=null_mode, seed=ns)
        n_ras  = [r["ra"]  for r in null if r.get("ra")  is not None]
        n_decs = [r["dec"] for r in null if r.get("dec") is not None]
        n_energies = [r["energy"]       for r in null if r.get("energy")       is not None]
        n_times    = [r["arrival_time"] for r in null if r.get("arrival_time") is not None]

        null_hemi_vals.append(abs(_hemisphere_imbalance(n_ras, n_decs)))
        null_axis_vals.append(_preferred_axis_score(n_ras, n_decs))
        pairs = [(r["energy"], r["arrival_time"]) for r in null
                 if r.get("energy") is not None and r.get("arrival_time") is not None]
        if len(pairs) >= 3:
            null_et_r_vals.append(abs(_pearson_r([p[0] for p in pairs],
                                                 [p[1] for p in pairs]) or 0.0))
        null_clust_vals.append(_clustering_score(n_times))

    null_comparison = {
        "null_mode":      null_mode,
        "null_repeats":   null_repeats,
        "hemi_percentile":  _empirical_percentile(abs(hemi),   null_hemi_vals),
        "axis_percentile":  _empirical_percentile(axis_score,  null_axis_vals),
        "et_r_percentile":  _empirical_percentile(abs(et_r or 0.0), null_et_r_vals),
        "clust_percentile": _empirical_percentile(clust,       null_clust_vals),
    }

    # --- injection metadata passthrough ---
    anomaly_injected = None
    for e in events:
        if e.get("_injection_metadata"):
            anomaly_injected = e["_injection_metadata"]
            break

    return {
        "event_count":      len(events),
        "events_with_energy":       len(energies),
        "events_with_position":     len(ras),
        "events_with_arrival_time": len(times),
        "energy_stats":     energy_stats,
        "anisotropy": {
            "hemisphere_imbalance": hemi,
            "interpretation": "Fraction of events in north minus south hemisphere. "
                              "0 = balanced, ±1 = all in one hemisphere.",
        },
        "preferred_axis": {
            "score": axis_score,
            "interpretation": "Max |mean cos-projection| across 12 trial axes. "
                              "Isotropic ≈ 0.0; perfect clustering ≈ 1.0.",
        },
        "energy_time_correlation": {
            "pearson_r": et_r,
            "interpretation": "Pearson r between energy and arrival_time. "
                              "Non-zero suggests energy-dependent propagation effects.",
        },
        "cluster_score": {
            "value":  clust,
            "interpretation": "Mean window count / expected-random window count. "
                              "≈1.0 for uniform; >1.0 for clustered arrivals.",
        },
        "null_comparison": null_comparison,
        "anomaly_injected": anomaly_injected,
    }


# ===========================================================================
# STAGE 6 – Signal strength evaluation
# ===========================================================================

def evaluate_signal_strength(results: Dict[str, Any]) -> Dict[str, Any]:
    """Turn raw analysis metrics into a plain-language tier classification.

    Classification rules (conservative thresholds):
      strong   : any metric percentile ≥ 0.97
      moderate : any metric percentile ≥ 0.90
      weak     : any metric percentile ≥ 0.75
      none     : all below 0.75

    These are empirical thresholds, not Bayesian posteriors.  They indicate
    *deviations relative to the null model*, not evidence of a specific cause.
    """
    nc = results.get("null_comparison", {})
    percentiles = {
        "hemisphere_imbalance": nc.get("hemi_percentile", 0.5),
        "preferred_axis":       nc.get("axis_percentile", 0.5),
        "energy_time_r":        nc.get("et_r_percentile", 0.5),
        "clustering":           nc.get("clust_percentile", 0.5),
    }

    max_pval = max(percentiles.values()) if percentiles else 0.5

    if max_pval >= 0.97:
        tier = TIER_STRONG
        summary = ("One or more metrics are in the top 3% of the null distribution. "
                   "This is a strong anomaly-like deviation, but does not identify its cause.")
    elif max_pval >= 0.90:
        tier = TIER_MODERATE
        summary = ("One or more metrics are in the top 10% of the null distribution. "
                   "Moderate anomaly-like deviation; warrants further investigation.")
    elif max_pval >= 0.75:
        tier = TIER_WEAK
        summary = ("One or more metrics are in the top 25% of the null distribution. "
                   "Weak anomaly-like deviation; consistent with statistical fluctuation.")
    else:
        tier = TIER_NONE
        summary = ("All metrics are within the bulk of the null distribution. "
                   "No significant anomaly detected.")

    return {
        "tier":         tier,
        "max_percentile": max_pval,
        "per_metric_percentiles": percentiles,
        "summary": summary,
        "caveat": (
            "Anomaly detection in event data is hypothesis testing, not proof "
            "of any specific physical or metaphysical claim. A deviation from the "
            "null model may reflect incomplete modeling, selection effects, "
            "instrument systematics, or statistical fluctuation."
        ),
    }


# ===========================================================================
# STAGE 7 – Write artifacts
# ===========================================================================

def write_analysis_artifacts(
    results: Dict[str, Any],
    signal_eval: Dict[str, Any],
    events: List[Dict[str, Any]],
    null_events: Optional[List[Dict[str, Any]]],
    output_dir: str,
    name: str = "analysis",
    plots_enabled: bool = True,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    """Save JSON report, CSV summary, Markdown summary, and optional PNG plots.

    Returns a dict mapping artifact type → file path.
    """
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.datetime.utcnow().isoformat() + "Z"
    manifest: Dict[str, str] = {}

    # --- JSON summary ---
    json_payload = {
        "experiment": name,
        "written_at": ts,
        "results": results,
        "signal_evaluation": signal_eval,
        "config": config or {},
    }
    json_path = os.path.join(output_dir, f"{name}_summary.json")
    with open(json_path, "w") as f:
        json.dump(json_payload, f, indent=2)
    manifest["json_summary"] = json_path

    # --- CSV summary ---
    nc = results.get("null_comparison", {})
    csv_row = {
        "name":             name,
        "written_at":       ts,
        "event_count":      results.get("event_count", 0),
        "hemisphere_imbalance": results.get("anisotropy", {}).get("hemisphere_imbalance", ""),
        "preferred_axis_score": results.get("preferred_axis", {}).get("score", ""),
        "energy_time_r":        results.get("energy_time_correlation", {}).get("pearson_r", ""),
        "cluster_score":        results.get("cluster_score", {}).get("value", ""),
        "hemi_percentile":  nc.get("hemi_percentile", ""),
        "axis_percentile":  nc.get("axis_percentile", ""),
        "et_r_percentile":  nc.get("et_r_percentile", ""),
        "clust_percentile": nc.get("clust_percentile", ""),
        "signal_tier":      signal_eval.get("tier", ""),
        "max_percentile":   signal_eval.get("max_percentile", ""),
    }
    csv_path = os.path.join(output_dir, f"{name}_results.csv")
    write_header = not os.path.exists(csv_path)
    with open(csv_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(csv_row.keys()))
        if write_header:
            writer.writeheader()
        writer.writerow(csv_row)
    manifest["csv_summary"] = csv_path

    # --- Markdown summary ---
    md_lines = [
        f"# Simulation Signature Analysis: {name}",
        "",
        f"**Run date (UTC):** {ts}",
        f"**Event count:** {results.get('event_count', 0)}",
        "",
        "## Metrics",
        "",
        "| Metric | Observed value | Null percentile |",
        "| --- | --- | --- |",
        f"| Hemisphere imbalance | "
        f"{results.get('anisotropy', {}).get('hemisphere_imbalance', 'N/A'):.4f} | "
        f"{nc.get('hemi_percentile', 'N/A'):.2f} |",
        f"| Preferred axis score | "
        f"{results.get('preferred_axis', {}).get('score', 'N/A'):.4f} | "
        f"{nc.get('axis_percentile', 'N/A'):.2f} |",
        f"| Energy–time Pearson r | "
        f"{results.get('energy_time_correlation', {}).get('pearson_r') or 0.0:.4f} | "
        f"{nc.get('et_r_percentile', 'N/A'):.2f} |",
        f"| Cluster score | "
        f"{results.get('cluster_score', {}).get('value', 'N/A'):.4f} | "
        f"{nc.get('clust_percentile', 'N/A'):.2f} |",
        "",
        "## Signal Strength Evaluation",
        "",
        f"**Tier:** `{signal_eval.get('tier', 'unknown')}`",
        "",
        signal_eval.get("summary", ""),
        "",
        "### Caveat",
        "",
        signal_eval.get("caveat", ""),
        "",
    ]

    inj = results.get("anomaly_injected")
    if inj:
        md_lines += [
            "## Injection Test",
            "",
            f"- Anomaly type: `{inj.get('anomaly_type')}`",
            f"- Strength: {inj.get('strength')}",
            f"- Records affected: {inj.get('n_affected')}",
            "",
        ]

    md_path = os.path.join(output_dir, f"{name}_summary.md")
    with open(md_path, "w") as f:
        f.write("\n".join(md_lines))
    manifest["markdown_summary"] = md_path

    # --- Plots ---
    if plots_enabled and _HAS_MPL:
        _write_plots(events, null_events, results, signal_eval, output_dir, name, manifest)
    elif plots_enabled and not _HAS_MPL:
        print("[WARNING] matplotlib not available – plots skipped.")

    # --- Manifest ---
    manifest_path = os.path.join(output_dir, f"{name}_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump({"experiment": name, "written_at": ts, "files": manifest}, f, indent=2)
    manifest["manifest"] = manifest_path

    return manifest


# ===========================================================================
# Plotting helpers (matplotlib only, no seaborn)
# ===========================================================================

def _write_plots(
    events: List[Dict[str, Any]],
    null_events: Optional[List[Dict[str, Any]]],
    results: Dict[str, Any],
    signal_eval: Dict[str, Any],
    output_dir: str,
    name: str,
    manifest: Dict[str, str],
) -> None:
    """Generate standard diagnostic plots."""

    ras   = [e["ra"]  for e in events if e.get("ra")  is not None]
    decs  = [e["dec"] for e in events if e.get("dec") is not None]
    energies = [e["energy"] for e in events if e.get("energy") is not None]
    times   = [e["arrival_time"] for e in events if e.get("arrival_time") is not None]

    # 1. Sky scatter (RA vs Dec)
    if ras and decs:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.scatter(ras, decs, s=4, alpha=0.5, color="steelblue", label="observed")
        if null_events:
            n_ras  = [r["ra"]  for r in null_events if r.get("ra")  is not None]
            n_decs = [r["dec"] for r in null_events if r.get("dec") is not None]
            ax.scatter(n_ras, n_decs, s=2, alpha=0.2, color="orange", label="null")
        ax.set_xlabel("RA (deg)")
        ax.set_ylabel("Dec (deg)")
        ax.set_title(f"{name}: Sky positions")
        ax.legend(markerscale=3)
        path = os.path.join(output_dir, f"{name}_sky_scatter.png")
        fig.savefig(path, dpi=100, bbox_inches="tight")
        plt.close(fig)
        manifest["plot_sky_scatter"] = path

    # 2. Energy histogram
    if energies:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.hist(energies, bins=30, color="steelblue", edgecolor="white", alpha=0.8)
        ax.set_xlabel("Energy")
        ax.set_ylabel("Count")
        ax.set_title(f"{name}: Energy distribution")
        path = os.path.join(output_dir, f"{name}_energy_hist.png")
        fig.savefig(path, dpi=100, bbox_inches="tight")
        plt.close(fig)
        manifest["plot_energy_hist"] = path

    # 3. Arrival-time histogram
    if times:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.hist(times, bins=30, color="teal", edgecolor="white", alpha=0.8)
        ax.set_xlabel("Arrival time")
        ax.set_ylabel("Count")
        ax.set_title(f"{name}: Arrival time distribution")
        path = os.path.join(output_dir, f"{name}_time_hist.png")
        fig.savefig(path, dpi=100, bbox_inches="tight")
        plt.close(fig)
        manifest["plot_time_hist"] = path

    # 4. Null-vs-observed comparison (bar chart of percentiles)
    nc = results.get("null_comparison", {})
    metrics = ["hemi_percentile", "axis_percentile", "et_r_percentile", "clust_percentile"]
    labels  = ["Hemi\nimbalance", "Preferred\naxis", "Energy–time\ncorr.", "Cluster\nscore"]
    values  = [nc.get(m, 0.5) for m in metrics]
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(labels, values, color="steelblue", edgecolor="white")
    ax.axhline(0.90, color="orange", linestyle="--", linewidth=1, label="90th pct")
    ax.axhline(0.97, color="red",    linestyle="--", linewidth=1, label="97th pct")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Empirical percentile vs null")
    ax.set_title(f"{name}: Null comparison")
    ax.legend(fontsize=8)
    path = os.path.join(output_dir, f"{name}_null_comparison.png")
    fig.savefig(path, dpi=100, bbox_inches="tight")
    plt.close(fig)
    manifest["plot_null_comparison"] = path

    # 5. Anomaly summary plot (only if injection was run)
    inj = results.get("anomaly_injected")
    if inj:
        pe = signal_eval.get("per_metric_percentiles", {})
        fig, ax = plt.subplots(figsize=(6, 4))
        pnames = list(pe.keys())
        pvals  = [pe[k] for k in pnames]
        colors = ["red" if v >= 0.90 else "steelblue" for v in pvals]
        ax.barh(pnames, pvals, color=colors)
        ax.axvline(0.90, color="orange", linestyle="--", linewidth=1)
        ax.set_xlim(0, 1.1)
        ax.set_xlabel("Percentile vs null")
        ax.set_title(f"{name}: Injection recovery ({inj['anomaly_type']})")
        path = os.path.join(output_dir, f"{name}_anomaly_summary.png")
        fig.savefig(path, dpi=100, bbox_inches="tight")
        plt.close(fig)
        manifest["plot_anomaly_summary"] = path
