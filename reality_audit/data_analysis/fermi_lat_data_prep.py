"""
fermi_lat_data_prep.py
======================
Prepare and normalise raw Fermi-LAT GRB event data for the Reality Audit
blinded analysis pipeline.

Real Fermi-LAT event files (downloaded from FSSC / HEASARC) typically do
NOT contain per-event redshifts.  Redshift comes from a companion GRB
metadata catalog.  This module handles:

  1. Loading and schema-normalising a raw event CSV (photon arrivaltimes,
     energies, GRB source identifier).
  2. Joining to a GRB metadata CSV that supplies redshift and T90 per event.
  3. Emitting a normalised output CSV ready for the blinded pipeline.
  4. Returning a PrepReport documenting exactly what was found, joined, and
     dropped, including any sources that still lack redshift.

Missing redshifts are NEVER fabricated.  Sources without a redshift match
are counted, recorded in the PrepReport, and excluded from the joined output.
If the resulting joined dataset has fewer than 5 sources with redshift the
prep step emits a INSUFFICIENT_REDSHIFT_COVERAGE warning and the run should
be treated as REHEARSAL.

GRB metadata CSV columns (required)
-------------------------------------
  grb_name   — e.g. "GRB090902B"
  redshift   — float

GRB metadata CSV columns (optional)
-------------------------------------
  t90_s      — duration [seconds]
  ra_deg     — RA [deg]
  dec_deg    — Dec [deg]
  z_source   — reference for redshift value

Raw event CSV required columns  (case-insensitive, aliases resolved)
----------------------------------------------------------------------
  grb_name or source_name  — GRB identifier matching metadata table
  arrival_time             — photon arrival time (any recognised alias)
  energy_gev               — photon energy in GeV (or energy_mev alias)
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

import pandas as pd

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Minimum sources with redshift for the run to qualify as AUTHENTIC_PUBLIC
MIN_REDSHIFT_SOURCES = 5

# Recognised aliases for the arrival-time column
_ARRIVAL_TIME_ALIASES = [
    "arrival_time", "photon_arrival_time_s", "arrival_time_s",
    "time_s", "time", "t", "t_s", "mjd", "time_mjd", "arrival_mjd",
]

# Recognised aliases for the source/GRB name column
_GRB_NAME_ALIASES = ["grb_name", "source_name", "grb", "name", "burst_name"]

# Recognised aliases for the energy column
_ENERGY_GEV_ALIASES = ["energy_gev", "energy"]
_ENERGY_MEV_ALIASES = ["energy_mev"]

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class PrepReport:
    """Outcome of a data preparation run."""
    n_events_raw: int
    n_events_output: int
    n_events_dropped: int
    n_sources_raw: int
    n_sources_with_redshift: int
    n_sources_without_redshift: int
    missing_redshift_grbs: List[str]
    column_map_applied: Dict[str, str]
    warnings: List[str]
    status: str  # OK | INSUFFICIENT_REDSHIFT_COVERAGE | SCHEMA_ERROR

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def write_json(self, output_path: str) -> None:
        pathlib.Path(output_path).write_text(json.dumps(self.to_dict(), indent=2))


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _resolve_column(
    df: pd.DataFrame,
    aliases: List[str],
    canonical_name: str,
    required: bool = True,
) -> tuple:  # (DataFrame, str | None, str | None)
    """
    Find the first alias that exists in df columns (case-insensitive).

    Returns (df, found_col, error_message_or_None).
    If the column is found under an alias other than canonical_name,
    df is returned with that column renamed.
    """
    lower_map = {c.lower(): c for c in df.columns}
    for alias in aliases:
        if alias.lower() in lower_map:
            original = lower_map[alias.lower()]
            if original != canonical_name:
                df = df.rename(columns={original: canonical_name})
            return df, original, None
    if required:
        return df, None, (
            f"MISSING_REQUIRED_COLUMN: none of {aliases} found; "
            f"available columns: {list(df.columns)}"
        )
    return df, None, None


def _load_event_csv(event_csv: str) -> tuple:  # (DataFrame | None, errors)
    """Load and normalise the raw event CSV."""
    errors: List[str] = []
    try:
        df = pd.read_csv(event_csv)
    except Exception as exc:
        return None, [f"EVENT_CSV_READ_ERROR: {exc}"]

    # Resolve GRB name column
    df, found_grb, err = _resolve_column(df, _GRB_NAME_ALIASES, "grb_name")
    if err:
        errors.append(err)
        return df, errors

    # Resolve arrival time column
    df, found_arr, err = _resolve_column(df, _ARRIVAL_TIME_ALIASES, "arrival_time")
    if err:
        errors.append(err)
        return df, errors

    # Resolve energy column — try GeV first, then MeV
    df, found_gev, _ = _resolve_column(
        df, _ENERGY_GEV_ALIASES, "energy_gev", required=False
    )
    if found_gev is None:
        df, found_mev, _ = _resolve_column(
            df, _ENERGY_MEV_ALIASES, "energy_mev", required=False
        )
        if found_mev is not None:
            df["energy_gev"] = df["energy_mev"] / 1000.0
        # No energy column at all — allow; the QC gate will catch it later.

    return df, errors


def _load_grb_metadata(metadata_csv: str) -> tuple:  # (DataFrame | None, errors)
    errors: List[str] = []
    try:
        meta = pd.read_csv(metadata_csv)
    except Exception as exc:
        return None, [f"METADATA_CSV_READ_ERROR: {exc}"]

    # Normalise grb_name column
    meta, _, err = _resolve_column(meta, _GRB_NAME_ALIASES, "grb_name")
    if err:
        errors.append(err)
        return meta, errors

    if "redshift" not in meta.columns:
        errors.append("MISSING_REQUIRED_COLUMN: 'redshift' not in metadata CSV")
        return meta, errors

    return meta, []


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def prepare_fermi_lat_real_data(
    event_csv: str,
    metadata_csv: str,
    output_csv: str,
    overwrite: bool = False,
) -> PrepReport:
    """
    Normalise event_csv, join redshifts from metadata_csv, write output_csv.

    Parameters
    ----------
    event_csv : str
        Path to the raw Fermi-LAT event CSV.
    metadata_csv : str
        Path to the GRB metadata CSV with redshifts.
    output_csv : str
        Path where the prepared output CSV will be written.
    overwrite : bool
        If False and output_csv already exists, raise FileExistsError.

    Returns
    -------
    PrepReport
    """
    output_path = pathlib.Path(output_csv)
    if output_path.exists() and not overwrite:
        raise FileExistsError(
            f"Output file already exists: {output_csv}. "
            "Set overwrite=True to allow replacement."
        )

    warnings: List[str] = []
    column_map: Dict[str, str] = {}

    # Load event CSV
    df, schema_errors = _load_event_csv(event_csv)
    if schema_errors:
        return PrepReport(
            n_events_raw=0,
            n_events_output=0,
            n_events_dropped=0,
            n_sources_raw=0,
            n_sources_with_redshift=0,
            n_sources_without_redshift=0,
            missing_redshift_grbs=[],
            column_map_applied={},
            warnings=schema_errors,
            status="SCHEMA_ERROR",
        )

    n_events_raw = len(df)
    sources_raw = df["grb_name"].unique().tolist()
    n_sources_raw = len(sources_raw)

    # Load metadata
    meta, meta_errors = _load_grb_metadata(metadata_csv)
    if meta_errors:
        return PrepReport(
            n_events_raw=n_events_raw,
            n_events_output=0,
            n_events_dropped=n_events_raw,
            n_sources_raw=n_sources_raw,
            n_sources_with_redshift=0,
            n_sources_without_redshift=n_sources_raw,
            missing_redshift_grbs=sources_raw,
            column_map_applied={},
            warnings=meta_errors,
            status="SCHEMA_ERROR",
        )

    # Bring over only redshift (and optional columns) for the join
    meta_keep = ["grb_name", "redshift"]
    for optional_col in ["t90_s", "ra_deg", "dec_deg", "z_source"]:
        if optional_col in meta.columns:
            meta_keep.append(optional_col)
    meta_slim = meta[meta_keep].drop_duplicates(subset="grb_name")

    # Left-join events → metadata to identify which GRBs have redshift
    merged = df.merge(meta_slim, on="grb_name", how="left")

    # Identify sources with/without redshift
    has_redshift_mask = merged["redshift"].notna()
    missing_redshift_grbs = sorted(
        merged.loc[~has_redshift_mask, "grb_name"].unique().tolist()
    )
    n_missing = len(missing_redshift_grbs)
    n_sources_with_redshift = n_sources_raw - n_missing

    # Keep only events that have a redshift — never fabricate values
    output_df = merged[has_redshift_mask].copy()
    n_events_output = len(output_df)
    n_events_dropped = n_events_raw - n_events_output

    if missing_redshift_grbs:
        warnings.append(
            f"REDSHIFT_MISSING_FOR_GRBS: {missing_redshift_grbs} "
            f"({n_events_dropped} events dropped)"
        )

    # Determine status
    if n_sources_with_redshift < MIN_REDSHIFT_SOURCES:
        status = "INSUFFICIENT_REDSHIFT_COVERAGE"
        warnings.append(
            f"INSUFFICIENT_REDSHIFT_COVERAGE: only {n_sources_with_redshift} "
            f"sources with redshift (minimum required: {MIN_REDSHIFT_SOURCES}). "
            "This run will be labelled REHEARSAL-equivalent."
        )
    else:
        status = "OK"

    # Write output CSV
    if n_events_output > 0:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_df.to_csv(output_path, index=False)
    else:
        warnings.append("NO_EVENTS_IN_OUTPUT: output CSV not written")

    return PrepReport(
        n_events_raw=n_events_raw,
        n_events_output=n_events_output,
        n_events_dropped=n_events_dropped,
        n_sources_raw=n_sources_raw,
        n_sources_with_redshift=n_sources_with_redshift,
        n_sources_without_redshift=n_missing,
        missing_redshift_grbs=missing_redshift_grbs,
        column_map_applied=column_map,
        warnings=warnings,
        status=status,
    )


def describe_required_formats() -> Dict[str, Any]:
    """Return a description of the required input formats for documentation."""
    return {
        "event_csv_required_columns": {
            "grb_name": f"GRB identifier (aliases: {_GRB_NAME_ALIASES})",
            "arrival_time": f"Photon arrival time in seconds (aliases: {_ARRIVAL_TIME_ALIASES})",
            "energy_gev": f"Photon energy in GeV (aliases: {_ENERGY_GEV_ALIASES} or {_ENERGY_MEV_ALIASES} + auto-convert)",
        },
        "metadata_csv_required_columns": {
            "grb_name": "GRB identifier matching event CSV",
            "redshift": "Spectroscopic redshift (float)",
        },
        "metadata_csv_optional_columns": {
            "t90_s": "T90 burst duration [seconds]",
            "ra_deg": "Right ascension [degrees]",
            "dec_deg": "Declination [degrees]",
            "z_source": "Reference for redshift measurement",
        },
        "notes": (
            "Redshifts are NEVER fabricated. Events without a matching redshift "
            "in the metadata catalog are excluded from the joined output. "
            f"At least {MIN_REDSHIFT_SOURCES} distinct GRBs with redshift are "
            "required for the run to qualify as AUTHENTIC_PUBLIC."
        ),
    }
