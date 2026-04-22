"""
time_exposure_loader.py
========================
Loads exposure window files from ``data/exposure_samples/`` and attaches
calibration provenance and exposure quality tier assessments.

Supported catalogs and file conventions
----------------------------------------
- fermi  v1 : data/exposure_samples/fermi_public_window_v1.csv
- fermi  v2 : data/exposure_samples/fermi_public_window_v2.csv
- swift  v1 : data/exposure_samples/swift_public_window_v1.json
- swift  v2 : data/exposure_samples/swift_public_window_v2.json
- icecube v1: data/exposure_samples/icecube_exposure_notes.json

When a file is not present the loader returns ``load_status="file_not_found"``
and defaults to ``TIER_NONE`` — this is the expected state for IceCube and for
any catalog that has not yet had exposure data deposited.

Author: commons-sentience-sandbox
"""

from __future__ import annotations

import csv
import io
import json
import os
from typing import Any, Dict, List, Optional

_HERE      = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
_EXPOSURE_DIR = os.path.join(_REPO_ROOT, "data", "exposure_samples")

from reality_audit.data_analysis.calibration_provenance_schema import (
    SOURCE_EMPIRICAL_PROXY,
    SOURCE_SYNTHETIC,
    make_provenance_record,
)
from reality_audit.data_analysis.exposure_quality_tiers import (
    TIER_NONE,
    assess_exposure_quality,
)

# ---------------------------------------------------------------------------
# Per-catalog provenance defaults
# ---------------------------------------------------------------------------

_PROVENANCE_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "fermi": {
        "source_type":                    SOURCE_EMPIRICAL_PROXY,
        "notes":                          (
            "Empirical proxy window file from Fermi-LAT GRB catalog. "
            "Not instrument-response-corrected."
        ),
        "non_synthetic_source":           True,
        "minimum_event_count_present":    True,
        "sufficient_observation_window":  False,
        "explicit_provenance_documented": True,
        "bounded_caveats_documented":     True,
        "instrument_response_modeled":    False,
        "livetime_validated":             False,
        "sky_coverage_assessed":          False,
    },
    "swift": {
        "source_type":                    SOURCE_EMPIRICAL_PROXY,
        "notes":                          (
            "Empirical proxy window file from Swift BAT3 GRB catalog. "
            "Not instrument-response-corrected."
        ),
        "non_synthetic_source":           True,
        "minimum_event_count_present":    True,
        "sufficient_observation_window":  False,
        "explicit_provenance_documented": True,
        "bounded_caveats_documented":     True,
        "instrument_response_modeled":    False,
        "livetime_validated":             False,
        "sky_coverage_assessed":          False,
    },
    "icecube": {
        "source_type":                    SOURCE_SYNTHETIC,
        "notes":                          (
            "IceCube HESE has no public livetime table accessible to this pipeline. "
            "Exposure correction is not applicable; isotropic null is used instead."
        ),
        "is_synthetic":                   False,
        "non_synthetic_source":           False,
        "minimum_event_count_present":    False,
        "sufficient_observation_window":  False,
        "explicit_provenance_documented": False,
        "bounded_caveats_documented":     False,
        "instrument_response_modeled":    False,
        "livetime_validated":             False,
        "sky_coverage_assessed":          False,
    },
}


# ---------------------------------------------------------------------------
# File registry
# ---------------------------------------------------------------------------

def _exposure_filename(catalog_label: str, version: str) -> Optional[str]:
    """Return the filename (not full path) for a catalog/version pair, or None."""
    mapping = {
        ("fermi",    "v1"): "fermi_public_window_v1.csv",
        ("fermi",    "v2"): "fermi_public_window_v2.csv",
        ("swift",    "v1"): "swift_public_window_v1.json",
        ("swift",    "v2"): "swift_public_window_v2.json",
        ("icecube",  "v1"): "icecube_exposure_notes.json",
    }
    return mapping.get((catalog_label.lower(), version.lower()))


def list_available_exposure_files(catalog_label: str) -> List[str]:
    """List exposure sample file *paths* that exist for *catalog_label*.

    Parameters
    ----------
    catalog_label : str
        One of ``fermi``, ``swift``, ``icecube``.

    Returns
    -------
    list[str]
        Absolute paths to files that are present on disk.
    """
    if not os.path.isdir(_EXPOSURE_DIR):
        return []
    prefix = catalog_label.lower()
    return [
        os.path.join(_EXPOSURE_DIR, f)
        for f in sorted(os.listdir(_EXPOSURE_DIR))
        if f.startswith(prefix)
    ]


# ---------------------------------------------------------------------------
# CSV helpers
# ---------------------------------------------------------------------------

def _parse_csv(path: str) -> List[Dict[str, str]]:
    """Parse a CSV file, skipping comment lines that start with '#'."""
    rows: List[Dict[str, str]] = []
    with open(path, newline="") as fh:
        content = "".join(line for line in fh if not line.lstrip().startswith("#"))
    reader = csv.DictReader(io.StringIO(content))
    for row in reader:
        rows.append(dict(row))
    return rows


# ---------------------------------------------------------------------------
# Main loader
# ---------------------------------------------------------------------------

def load_exposure_window(
    catalog_label: str,
    version: str = "v1",
) -> Dict[str, Any]:
    """Load an exposure window file for a catalog.

    Parameters
    ----------
    catalog_label : str
        One of ``fermi``, ``swift``, ``icecube``.
    version : str
        ``v1`` or ``v2``.

    Returns
    -------
    dict with keys:
      - catalog_label                          : str
      - version                                : str
      - file_path                              : str or None
      - records                                : list[dict]
      - provenance                             : dict
      - exposure_quality_tier                  : str
      - exposure_quality_requirements_met      : list[str]
      - exposure_quality_missing_requirements  : list[str]
      - exposure_quality_evidence_summary      : str
      - load_status                            : "ok" | "file_not_found" | "format_error"
      - load_notes                             : str
    """
    label   = catalog_label.lower()
    fname   = _exposure_filename(label, version)
    prov_kw = dict(_PROVENANCE_DEFAULTS.get(label, {}))
    source_type = prov_kw.pop("source_type", SOURCE_EMPIRICAL_PROXY)
    provenance  = make_provenance_record(label, source_type, version=version, **prov_kw)

    if fname is None:
        quality = assess_exposure_quality(label, {})
        return {
            "catalog_label": label,
            "version": version,
            "file_path": None,
            "records": [],
            "provenance": provenance,
            "load_status": "file_not_found",
            "load_notes": f"No exposure file registered for catalog={label!r}, version={version!r}.",
            **{k: v for k, v in quality.items()},
        }

    file_path = os.path.join(_EXPOSURE_DIR, fname)

    if not os.path.isfile(file_path):
        quality = assess_exposure_quality(label, {})
        return {
            "catalog_label": label,
            "version": version,
            "file_path": file_path,
            "records": [],
            "provenance": provenance,
            "load_status": "file_not_found",
            "load_notes": f"Exposure file not found: {file_path}",
            **{k: v for k, v in quality.items()},
        }

    # Load the file
    records: List[Dict[str, Any]] = []
    load_status = "ok"
    load_notes  = ""
    try:
        if fname.endswith(".csv"):
            records = _parse_csv(file_path)
        elif fname.endswith(".json"):
            with open(file_path) as fh:
                data = json.load(fh)
            # Normalise JSON to a list of records
            if isinstance(data, list):
                records = data
            elif isinstance(data, dict):
                records = data.get("windows", [data])
        else:
            load_status = "format_error"
            load_notes  = f"Unrecognised file extension: {fname}"
    except Exception as exc:
        load_status = "format_error"
        load_notes  = str(exc)
        records     = []

    # Build quality assessment from provenance flags (include is_synthetic for tier logic)
    exposure_meta = {
        k: provenance.get(k)
        for k in [
            "is_synthetic",
            "non_synthetic_source",
            "minimum_event_count_present",
            "sufficient_observation_window",
            "explicit_provenance_documented",
            "bounded_caveats_documented",
            "instrument_response_modeled",
            "livetime_validated",
            "sky_coverage_assessed",
        ]
    }
    quality = assess_exposure_quality(label, exposure_meta)

    return {
        "catalog_label": label,
        "version": version,
        "file_path": file_path,
        "records": records,
        "provenance": provenance,
        "load_status": load_status,
        "load_notes": load_notes if load_notes else f"Loaded {len(records)} record(s).",
        **{k: v for k, v in quality.items()},
    }


# ---------------------------------------------------------------------------
# Convenience accessor
# ---------------------------------------------------------------------------

def get_exposure_quality_for_catalog(
    catalog_label: str,
    version: str = "v1",
) -> Dict[str, Any]:
    """Load exposure window and return only the quality assessment subset.

    Parameters
    ----------
    catalog_label : str
    version : str

    Returns
    -------
    dict with keys: exposure_quality_tier, exposure_quality_requirements_met,
    exposure_quality_missing_requirements, exposure_quality_evidence_summary,
    tier_rationale, load_status.
    """
    full = load_exposure_window(catalog_label, version)
    return {
        "catalog_label":                         full["catalog_label"],
        "version":                               full["version"],
        "exposure_quality_tier":                 full["exposure_quality_tier"],
        "exposure_quality_requirements_met":     full["exposure_quality_requirements_met"],
        "exposure_quality_missing_requirements": full["exposure_quality_missing_requirements"],
        "exposure_quality_evidence_summary":     full["exposure_quality_evidence_summary"],
        "tier_rationale":                        full.get("tier_rationale", ""),
        "load_status":                           full["load_status"],
    }
