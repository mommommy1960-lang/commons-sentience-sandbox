"""
fermi_lat_grb_adapter.py
=========================
First real-data adapter for Fermi-LAT GRB-style event catalogs.

Reads a local JSON, CSV, or newline-delimited JSON file containing
photon-level event records from gamma-ray burst observations and returns
a standardized structure compatible with run_timing_pipeline().

Supported input schemas
-----------------------
Minimal required columns (any naming convention, mapped via column_map):
  - event_id        : any unique row identifier (str or int)
  - photon_energy   : photon energy, converted to GeV
  - arrival_time    : seconds since trigger or MJD float
  - source_id       : GRB name / transient identifier

Optional columns:
  - redshift        : cosmological redshift z
  - distance_Mpc    : luminosity distance in Mpc (derived from z if absent)
  - energy_unit     : override unit for energy ("GeV", "MeV", "TeV", "keV")
  - time_unit       : override unit for time ("s", "MJD")
  - time_ref_MJD    : reference MJD for relative-time columns

Output format (compatible with real_timing_pipeline and mock_timing_pipeline)
--------------------------
{
    "events": [
        {
            "event_id": str,
            "energy": float,          # GeV
            "time": float,            # seconds since first event in source group
            "source": str,
            "redshift": float | None,
            "distance_Mpc": float | None,
        },
        ...
    ],
    "by_source": {
        "<source_id>": {
            "events": [...],          # subset of events for this source
            "n_events": int,
            "mean_energy_GeV": float,
            "time_span_s": float,
        },
        ...
    },
    "metadata": {
        "n_events": int,
        "n_sources": int,
        "n_dropped": int,
        "energy_unit_in": str,
        "time_unit_in": str,
        "has_distance": bool,
        "source_file": str,
        "schema_version": str,
    },
}

Design principles (from benchmark transfer P01, P08):
  - Read-only:  adapter never modifies the source file.
  - Reproducible: all dropped rows are counted and logged.
  - Explicit:  energy/time units must be declared or detected.
  - Validated: minimum event count per source is enforced.
"""

from __future__ import annotations

import csv
import io
import json
import math
import os
import warnings
from typing import Any, Dict, Iterable, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCHEMA_VERSION = "1.0"

_ENERGY_TO_GEV: Dict[str, float] = {
    "GeV": 1.0,
    "MeV": 1e-3,
    "TeV": 1e3,
    "keV": 1e-6,
    "eV":  1e-9,
}

_KNOWN_TIME_UNITS = {"s", "MJD"}

# Hubble constant for z → Mpc conversion (simple flat ΛCDM estimate)
_H0_KM_S_MPC = 67.4          # km/s/Mpc (Planck 2018)
_C_KM_S = 2.998e5             # km/s
_MPC_PER_Z_SMALL = _C_KM_S / _H0_KM_S_MPC  # ~4450 Mpc per unit z (small-z approx)

# Minimum events per source to retain that source
DEFAULT_MIN_EVENTS_PER_SOURCE = 2


# ---------------------------------------------------------------------------
# Distance helper
# ---------------------------------------------------------------------------


def _z_to_distance_Mpc(z: float) -> float:
    """
    Approximate luminosity distance in Mpc from redshift z.
    Uses a simple flat ΛCDM approximation valid for z < 2:
        D_L ≈ (c/H0) × z × (1 + z/2)   [Pen 1999 low-z expansion]
    This is good to ~5% up to z~1 and is adequate for a first-pass
    timing-delay slope estimate.  A proper comoving-distance integral
    should be used for publication-quality results.
    """
    if z <= 0.0:
        return 0.0
    return _MPC_PER_Z_SMALL * z * (1.0 + z / 2.0)


# ---------------------------------------------------------------------------
# Column-map helpers
# ---------------------------------------------------------------------------


def _canonical_column_map(
    headers: List[str],
    column_map: Optional[Dict[str, str]] = None,
) -> Dict[str, Optional[str]]:
    """
    Return a mapping from canonical field name → actual column name.

    The `column_map` parameter lets callers override auto-detection:
        column_map = {
            "photon_energy": "energy_mev",
            "source_id":     "grb_name",
        }

    Auto-detection: try common synonyms (case-insensitive).
    """
    synonyms: Dict[str, List[str]] = {
        "event_id":     ["event_id", "id", "row_id", "index"],
        "photon_energy": [
            "photon_energy", "energy", "energy_gev", "energy_mev",
            "energy_tev", "energy_kev", "e_gev", "e_mev",
        ],
        "arrival_time": [
            "arrival_time", "time", "t", "time_s", "t_s",
            "mjd", "time_mjd", "arrival_mjd",
        ],
        "source_id":    ["source_id", "source", "grb_id", "grb_name", "name", "burst"],
        "redshift":     ["redshift", "z", "z_spec", "z_photo"],
        "distance_Mpc": ["distance_mpc", "distance", "d_mpc", "dl_mpc", "dist_mpc"],
        "energy_unit":  ["energy_unit", "e_unit", "unit"],
        "time_unit":    ["time_unit", "t_unit"],
    }
    header_lower = {h.lower(): h for h in headers}
    result: Dict[str, Optional[str]] = {}

    for field, candidates in synonyms.items():
        # User override takes precedence
        if column_map and field in column_map:
            result[field] = column_map[field]
            continue
        # Auto-detect
        found = None
        for candidate in candidates:
            if candidate.lower() in header_lower:
                found = header_lower[candidate.lower()]
                break
        result[field] = found

    return result


# ---------------------------------------------------------------------------
# Raw readers
# ---------------------------------------------------------------------------


def _read_csv(path: str) -> Tuple[List[str], List[Dict[str, str]]]:
    """Read CSV → (headers, list-of-row-dicts)."""
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = list(reader.fieldnames or [])
        rows = [dict(row) for row in reader]
    return headers, rows


def _read_json(path: str) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Read JSON.  Supports:
      - array of objects: [{...}, {...}]
      - newline-delimited JSON: one object per line
    """
    with open(path, encoding="utf-8") as f:
        content = f.read().strip()

    # Try array first
    try:
        data = json.loads(content)
        if isinstance(data, list) and data:
            headers = list(data[0].keys())
            return headers, data
    except json.JSONDecodeError:
        pass

    # Try newline-delimited
    rows = []
    for line in content.splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    if rows:
        headers = list(rows[0].keys())
        return headers, rows

    return [], []


# ---------------------------------------------------------------------------
# Value parsers
# ---------------------------------------------------------------------------


def _try_float(val: Any) -> Optional[float]:
    if val is None or (isinstance(val, str) and val.strip() in ("", "nan", "NaN", "NULL", "null")):
        return None
    try:
        result = float(val)
        if math.isnan(result) or math.isinf(result):
            return None
        return result
    except (TypeError, ValueError):
        return None


def _try_str(val: Any) -> Optional[str]:
    if val is None:
        return None
    s = str(val).strip()
    return s if s else None


# ---------------------------------------------------------------------------
# Energy normalisation
# ---------------------------------------------------------------------------


def _normalize_energy(
    raw_energy: float,
    declared_unit: str,
    col_name: str,
) -> float:
    """Convert raw energy value to GeV."""
    unit = declared_unit.strip()
    if unit not in _ENERGY_TO_GEV:
        # Try to infer from column name
        col_lower = col_name.lower()
        for u in _ENERGY_TO_GEV:
            if u.lower() in col_lower:
                unit = u
                break
        else:
            unit = "GeV"   # fallback
    return raw_energy * _ENERGY_TO_GEV[unit]


# ---------------------------------------------------------------------------
# Time normalisation
# ---------------------------------------------------------------------------

_MJD_EPOCH_S = 0.0   # We convert MJD to seconds by subtracting group minimum MJD


def _normalize_time(
    raw_time: float,
    time_unit: str,
) -> float:
    """
    Normalise time to seconds (float).
    For MJD, we return the raw MJD float; relative offsets are computed
    per-source in the grouping step.
    """
    if time_unit == "s":
        return raw_time
    if time_unit == "MJD":
        # MJD to seconds: keep as MJD for now; converted to relative seconds in grouping
        return raw_time * 86400.0   # approximate: MJD → seconds since MJD 0
    return raw_time


# ---------------------------------------------------------------------------
# Main adapter
# ---------------------------------------------------------------------------


def load_grb_events(
    path: str,
    column_map: Optional[Dict[str, str]] = None,
    energy_unit: str = "GeV",
    time_unit: str = "s",
    time_ref_mjd: float = 0.0,
    min_events_per_source: int = DEFAULT_MIN_EVENTS_PER_SOURCE,
    min_energy_GeV: float = 0.0,
    max_energy_GeV: float = float("inf"),
    verbose: bool = False,
) -> Dict[str, Any]:
    """
    Load and normalise GRB-style photon events from a local file.

    Parameters
    ----------
    path                  : path to JSON or CSV file
    column_map            : optional override mapping canonical→actual field names
    energy_unit           : default energy unit if not in the data
    time_unit             : default time unit ("s" or "MJD")
    time_ref_mjd          : reference MJD for relative-time columns (MJD only)
    min_events_per_source : sources with fewer events are dropped
    min_energy_GeV        : drop events below this energy (GeV)
    max_energy_GeV        : drop events above this energy (GeV)
    verbose               : emit warnings for every dropped row

    Returns
    -------
    Standardized event dict (see module docstring).

    Raises
    ------
    FileNotFoundError if path does not exist.
    ValueError if no required columns are found.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Data file not found: {path}")

    ext = os.path.splitext(path)[1].lower()
    if ext in (".json", ".jsonl", ".ndjson"):
        headers, raw_rows = _read_json(path)
    elif ext in (".csv", ".tsv"):
        headers, raw_rows = _read_csv(path)
    else:
        # Try JSON first, then CSV
        try:
            headers, raw_rows = _read_json(path)
        except Exception:
            headers, raw_rows = _read_csv(path)

    if not headers:
        raise ValueError(f"Could not parse any columns from {path}")

    cmap = _canonical_column_map(headers, column_map)

    # Require at least energy and time
    if cmap["photon_energy"] is None:
        raise ValueError(
            f"Could not find a photon_energy column in {path}. "
            f"Headers: {headers}. Use column_map to specify."
        )
    if cmap["arrival_time"] is None:
        raise ValueError(
            f"Could not find an arrival_time column in {path}. "
            f"Headers: {headers}. Use column_map to specify."
        )

    # Determine per-row energy unit override column
    energy_unit_col = cmap.get("energy_unit")
    time_unit_col = cmap.get("time_unit")

    events: List[Dict[str, Any]] = []
    n_dropped = 0

    for i, row in enumerate(raw_rows):
        # --- energy ---
        raw_e = _try_float(row.get(cmap["photon_energy"]))
        if raw_e is None:
            if verbose:
                warnings.warn(f"Row {i}: missing/invalid energy — dropped.")
            n_dropped += 1
            continue

        row_energy_unit = energy_unit
        if energy_unit_col:
            eu = _try_str(row.get(energy_unit_col))
            if eu and eu in _ENERGY_TO_GEV:
                row_energy_unit = eu

        e_GeV = _normalize_energy(raw_e, row_energy_unit, cmap["photon_energy"])

        if e_GeV < min_energy_GeV or e_GeV > max_energy_GeV:
            if verbose:
                warnings.warn(f"Row {i}: energy {e_GeV:.3f} GeV out of range — dropped.")
            n_dropped += 1
            continue

        # --- time ---
        raw_t = _try_float(row.get(cmap["arrival_time"]))
        if raw_t is None:
            if verbose:
                warnings.warn(f"Row {i}: missing/invalid time — dropped.")
            n_dropped += 1
            continue

        row_time_unit = time_unit
        if time_unit_col:
            tu = _try_str(row.get(time_unit_col))
            if tu and tu in _KNOWN_TIME_UNITS:
                row_time_unit = tu

        t_raw = _normalize_time(raw_t, row_time_unit)

        # --- source ---
        src_col = cmap.get("source_id")
        source = _try_str(row.get(src_col)) if src_col else None
        if source is None:
            source = "unknown"

        # --- optional fields ---
        z = None
        dist_Mpc = None
        z_col = cmap.get("redshift")
        if z_col:
            z = _try_float(row.get(z_col))
        dist_col = cmap.get("distance_Mpc")
        if dist_col:
            dist_Mpc = _try_float(row.get(dist_col))
        if dist_Mpc is None and z is not None and z > 0:
            dist_Mpc = _z_to_distance_Mpc(z)

        # --- event_id ---
        eid_col = cmap.get("event_id")
        event_id = _try_str(row.get(eid_col)) if eid_col else str(i)
        if event_id is None:
            event_id = str(i)

        events.append({
            "event_id": event_id,
            "energy": e_GeV,
            "time_raw": t_raw,    # seconds (or MJD×86400)
            "source": source,
            "redshift": z,
            "distance_Mpc": dist_Mpc,
        })

    # --- group by source; compute relative times ---
    by_source: Dict[str, Dict[str, Any]] = {}
    for ev in events:
        src = ev["source"]
        by_source.setdefault(src, []).append(ev)

    # Sort each group by time_raw and compute relative times
    final_events: List[Dict[str, Any]] = []
    final_by_source: Dict[str, Any] = {}
    n_dropped_source = 0

    for src, grp in sorted(by_source.items()):
        if len(grp) < min_events_per_source:
            if verbose:
                warnings.warn(
                    f"Source '{src}' has only {len(grp)} event(s) "
                    f"(min={min_events_per_source}) — dropped."
                )
            n_dropped += len(grp)
            n_dropped_source += len(grp)
            continue

        grp.sort(key=lambda e: e["time_raw"])
        t0 = grp[0]["time_raw"]
        energies = []
        source_events = []
        for ev in grp:
            ev_norm = {
                "event_id": ev["event_id"],
                "energy": ev["energy"],
                "time": ev["time_raw"] - t0,  # relative seconds from first photon
                "source": src,
                "redshift": ev["redshift"],
                "distance_Mpc": ev["distance_Mpc"],
            }
            final_events.append(ev_norm)
            source_events.append(ev_norm)
            energies.append(ev["energy"])

        time_span = grp[-1]["time_raw"] - t0
        final_by_source[src] = {
            "events": source_events,
            "n_events": len(source_events),
            "mean_energy_GeV": sum(energies) / len(energies),
            "time_span_s": time_span,
        }

    has_distance = any(
        ev.get("distance_Mpc") is not None for ev in final_events
    )

    return {
        "events": final_events,
        "by_source": final_by_source,
        "metadata": {
            "n_events": len(final_events),
            "n_sources": len(final_by_source),
            "n_dropped": n_dropped,
            "energy_unit_in": energy_unit,
            "time_unit_in": time_unit,
            "has_distance": has_distance,
            "source_file": os.path.abspath(path),
            "schema_version": SCHEMA_VERSION,
        },
    }


# ---------------------------------------------------------------------------
# Pipeline-compatible format converter
# ---------------------------------------------------------------------------


def to_timing_pipeline_format(
    adapter_output: Dict[str, Any],
    distance_fallback_Mpc: float = 1000.0,
) -> Dict[str, Any]:
    """
    Convert adapter output to the exact format expected by
    run_timing_pipeline() and real_timing_pipeline.run_real_timing_pipeline().

    Events without a distance estimate are assigned `distance_fallback_Mpc`.

    Returns dict with:
        energy_GeV      : List[float]
        distance_Mpc    : List[float]
        timing_offset_s : List[float]  (= ev["time"], relative to source t0)
        n_events        : int
        n_sources       : int
        metadata        : dict (passthrough of adapter metadata)
    """
    events = adapter_output["events"]
    energy_GeV = [ev["energy"] for ev in events]
    distance_Mpc = [
        ev["distance_Mpc"] if ev.get("distance_Mpc") is not None
        else distance_fallback_Mpc
        for ev in events
    ]
    timing_offset_s = [ev["time"] for ev in events]

    return {
        "energy_GeV": energy_GeV,
        "distance_Mpc": distance_Mpc,
        "timing_offset_s": timing_offset_s,
        "n_events": len(events),
        "n_sources": adapter_output["metadata"]["n_sources"],
        "metadata": adapter_output["metadata"],
    }


# ---------------------------------------------------------------------------
# Convenience: load + convert in one call
# ---------------------------------------------------------------------------


def load_and_convert(
    path: str,
    distance_fallback_Mpc: float = 1000.0,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    load_grb_events() → to_timing_pipeline_format() in one call.
    All kwargs are forwarded to load_grb_events().
    """
    raw = load_grb_events(path, **kwargs)
    return to_timing_pipeline_format(raw, distance_fallback_Mpc=distance_fallback_Mpc)
