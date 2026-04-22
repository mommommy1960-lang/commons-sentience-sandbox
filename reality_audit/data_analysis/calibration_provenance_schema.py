"""
calibration_provenance_schema.py
=================================
Schema definitions and helpers for calibration provenance records used in the
Reality Audit exposure quality tiers system.

A provenance record documents *where* an exposure histogram or calibration
product came from, which quality-requirement flags are satisfied, and which are
not.  Records are plain dicts that can be serialised as JSON.

Author: commons-sentience-sandbox
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Source type constants
# ---------------------------------------------------------------------------

SOURCE_SYNTHETIC          = "synthetic"
SOURCE_EMPIRICAL_PROXY    = "empirical_proxy"
SOURCE_PUBLIC_CATALOG     = "public_catalog"
SOURCE_INSTRUMENT_MODEL   = "instrument_model"
SOURCE_VALIDATED_PIPELINE = "validated_pipeline"

_ALL_SOURCE_TYPES = [
    SOURCE_SYNTHETIC,
    SOURCE_EMPIRICAL_PROXY,
    SOURCE_PUBLIC_CATALOG,
    SOURCE_INSTRUMENT_MODEL,
    SOURCE_VALIDATED_PIPELINE,
]

# ---------------------------------------------------------------------------
# Schema field definitions (documentary only)
# ---------------------------------------------------------------------------

CALIBRATION_PROVENANCE_FIELDS: Dict[str, str] = {
    "source_type":                    "str — one of the SOURCE_* constants",
    "catalog_label":                  "str — fermi|swift|icecube",
    "version":                        "str — e.g. v1, v2",
    "creation_date":                  "str — ISO date",
    "notes":                          "str — human-readable provenance notes",
    "is_synthetic":                   "bool — True if derived from synthetic data",
    "non_synthetic_source":           "bool — True if from real observations",
    "minimum_event_count_present":    "bool — enough events to build a histogram",
    "sufficient_observation_window":  "bool — multi-year or documented window",
    "explicit_provenance_documented": "bool — creation chain recorded",
    "bounded_caveats_documented":     "bool — known limitations enumerated",
    "instrument_response_modeled":    "bool — explicit IRF used",
    "livetime_validated":             "bool — livetime cross-checked",
    "sky_coverage_assessed":          "bool — sky coverage fraction documented",
}

# Fields that must be present in a valid record
_REQUIRED_FIELDS = [
    "source_type",
    "catalog_label",
    "version",
    "creation_date",
]

# Boolean flag fields (subset of CALIBRATION_PROVENANCE_FIELDS)
_BOOL_FIELDS = [
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

# Default values for a new provenance record
_DEFAULTS: Dict[str, Any] = {
    "source_type":                    SOURCE_EMPIRICAL_PROXY,
    "catalog_label":                  "unknown",
    "version":                        "v1",
    "creation_date":                  "",
    "notes":                          "",
    "is_synthetic":                   False,
    "non_synthetic_source":           False,
    "minimum_event_count_present":    False,
    "sufficient_observation_window":  False,
    "explicit_provenance_documented": False,
    "bounded_caveats_documented":     False,
    "instrument_response_modeled":    False,
    "livetime_validated":             False,
    "sky_coverage_assessed":          False,
}


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_provenance_record(record: dict) -> List[str]:
    """Return a list of missing or invalid field names in *record*.

    Parameters
    ----------
    record : dict
        A calibration provenance dict (as returned by ``make_provenance_record``
        or loaded from JSON).

    Returns
    -------
    list[str]
        Names of fields that are absent or have the wrong type.  Empty list
        means the record is valid.
    """
    issues: List[str] = []

    for field in _REQUIRED_FIELDS:
        if field not in record or record[field] is None or record[field] == "":
            issues.append(field)

    if "source_type" in record and record["source_type"] not in _ALL_SOURCE_TYPES:
        issues.append("source_type")

    for field in _BOOL_FIELDS:
        if field in record and not isinstance(record[field], bool):
            issues.append(field)

    return sorted(set(issues))


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def make_provenance_record(
    catalog_label: str,
    source_type: str,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Build a provenance record with sensible defaults.

    Parameters
    ----------
    catalog_label : str
        Short label for the catalog (fermi / swift / icecube).
    source_type : str
        One of the SOURCE_* constants.
    **kwargs
        Override any field from CALIBRATION_PROVENANCE_FIELDS.

    Returns
    -------
    dict
    """
    record: Dict[str, Any] = dict(_DEFAULTS)
    record["catalog_label"] = catalog_label
    record["source_type"]   = source_type
    record["creation_date"] = datetime.date.today().isoformat()

    # Synthetic convenience flag
    if source_type == SOURCE_SYNTHETIC:
        record["is_synthetic"]         = True
        record["non_synthetic_source"] = False
    elif source_type in (
        SOURCE_EMPIRICAL_PROXY,
        SOURCE_PUBLIC_CATALOG,
        SOURCE_INSTRUMENT_MODEL,
        SOURCE_VALIDATED_PIPELINE,
    ):
        record["is_synthetic"]         = False
        record["non_synthetic_source"] = True

    record.update(kwargs)
    return record
