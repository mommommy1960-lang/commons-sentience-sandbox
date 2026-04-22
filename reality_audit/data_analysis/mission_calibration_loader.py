"""
mission_calibration_loader.py
==============================
Loads calibration product JSON files from ``data/calibration_products/``
and assembles the per-catalog exposure quality tier information needed by
the Stage 14 pipeline manifest and publication gate.

File convention
---------------
- data/calibration_products/fermi_calibration_v1.json
- data/calibration_products/swift_calibration_v1.json
- data/calibration_products/icecube_calibration_v1.json

When a file is absent the loader returns ``load_status="file_not_found"``
and falls back to building a provenance record with only the flags registered
in ``_CALIBRATION_DEFAULTS`` for that catalog.

Author: commons-sentience-sandbox
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

_HERE      = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
_CAL_DIR   = os.path.join(_REPO_ROOT, "data", "calibration_products")

from reality_audit.data_analysis.calibration_provenance_schema import (
    SOURCE_EMPIRICAL_PROXY,
    SOURCE_SYNTHETIC,
    make_provenance_record,
)
from reality_audit.data_analysis.exposure_quality_tiers import (
    TIER_NONE,
    TIER_PARTIAL,
    assess_exposure_quality,
    worst_tier,
    best_tier,
    TIER_CANDIDATE,
    TIER_GRADE,
)

_DEFAULT_CATALOGS = ["fermi", "swift", "icecube"]

# Per-catalog fallback metadata when no calibration file is found
_CALIBRATION_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "fermi": {
        "source_type":                    SOURCE_EMPIRICAL_PROXY,
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


def _cal_path(catalog_label: str, version: str) -> str:
    return os.path.join(_CAL_DIR, f"{catalog_label}_calibration_{version}.json")


def _exposure_meta_from_cal(cal_data: dict, defaults: dict) -> dict:
    """Extract boolean quality flags from a calibration JSON record."""
    flag_keys = [
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
    meta = {}
    for k in flag_keys:
        if k in cal_data:
            meta[k] = bool(cal_data[k])
        else:
            meta[k] = bool(defaults.get(k, False))
    return meta


# ---------------------------------------------------------------------------
# Core loader
# ---------------------------------------------------------------------------

def load_calibration_product(
    catalog_label: str,
    version: str = "v1",
) -> Dict[str, Any]:
    """Load a calibration product JSON for a catalog.

    Parameters
    ----------
    catalog_label : str
        One of ``fermi``, ``swift``, ``icecube``.
    version : str

    Returns
    -------
    dict with keys:
      - catalog_label
      - version
      - calibration_data                       : dict
      - provenance                             : dict
      - exposure_quality_tier                  : str
      - exposure_quality_requirements_met      : list
      - exposure_quality_missing_requirements  : list
      - exposure_quality_evidence_summary      : str
      - load_status                            : "ok" | "file_not_found" | "format_error"
    """
    label    = catalog_label.lower()
    path     = _cal_path(label, version)
    defaults = _CALIBRATION_DEFAULTS.get(label, {})
    src_type = defaults.get("source_type", SOURCE_EMPIRICAL_PROXY)

    cal_data: dict = {}
    load_status = "ok"

    if not os.path.isfile(path):
        load_status = "file_not_found"
    else:
        try:
            with open(path) as fh:
                cal_data = json.load(fh)
        except Exception as exc:
            load_status = "format_error"
            cal_data    = {"_load_error": str(exc)}

    # Build provenance from loaded data or defaults
    if cal_data and load_status == "ok":
        prov_src = cal_data.get("source_type", src_type)
        prov_kw  = {k: v for k, v in cal_data.items()
                    if k not in ("source_type", "catalog_label", "version")}
        provenance = make_provenance_record(label, prov_src, version=version, **prov_kw)
    else:
        kw = {k: v for k, v in defaults.items() if k != "source_type"}
        provenance = make_provenance_record(label, src_type, version=version, **kw)

    exposure_meta = _exposure_meta_from_cal(cal_data, defaults)
    quality       = assess_exposure_quality(label, exposure_meta)

    return {
        "catalog_label":    label,
        "version":          version,
        "calibration_data": cal_data,
        "provenance":       provenance,
        "load_status":      load_status,
        **{k: v for k, v in quality.items()},
    }


# ---------------------------------------------------------------------------
# Multi-catalog helpers
# ---------------------------------------------------------------------------

def get_all_catalog_quality_tiers(
    catalogs: Optional[List[str]] = None,
    version: str = "v1",
) -> Dict[str, Dict[str, Any]]:
    """Return a dict mapping *catalog_label* → quality assessment result.

    Parameters
    ----------
    catalogs : list[str], optional
        Labels to assess.  Defaults to ``["fermi", "swift", "icecube"]``.
    version : str

    Returns
    -------
    dict[str, dict]
    """
    if catalogs is None:
        catalogs = _DEFAULT_CATALOGS
    return {label: load_calibration_product(label, version) for label in catalogs}


def build_exposure_quality_summary_for_manifest(
    catalogs: Optional[List[str]] = None,
    version: str = "v1",
) -> Dict[str, Any]:
    """Build per-catalog exposure quality dict for embedding in a Stage 14 manifest.

    Parameters
    ----------
    catalogs : list[str], optional
    version : str

    Returns
    -------
    dict with keys:
      - exposure_quality_tier_by_catalog
      - exposure_quality_requirements_met_by_catalog
      - exposure_quality_missing_requirements_by_catalog
      - exposure_quality_evidence_summary_by_catalog
      - worst_exposure_quality_tier
      - any_catalog_at_analysis_candidate
      - confirmatory_exposure_quality_readiness : "ready" | "not_ready"
      - confirmatory_exposure_quality_readiness_reason : str
    """
    if catalogs is None:
        catalogs = _DEFAULT_CATALOGS

    all_results = get_all_catalog_quality_tiers(catalogs, version)

    tier_by_catalog: Dict[str, str]       = {}
    reqs_met_by:     Dict[str, List[str]] = {}
    reqs_missing_by: Dict[str, List[str]] = {}
    summary_by:      Dict[str, str]       = {}

    for label, result in all_results.items():
        tier_by_catalog[label] = result.get("exposure_quality_tier", TIER_NONE)
        reqs_met_by[label]     = result.get("exposure_quality_requirements_met", [])
        reqs_missing_by[label] = result.get("exposure_quality_missing_requirements", [])
        summary_by[label]      = result.get("exposure_quality_evidence_summary", "")

    all_tiers = list(tier_by_catalog.values())
    _worst = worst_tier(all_tiers) if all_tiers else TIER_NONE

    # Any catalog at analysis_candidate or above?
    from reality_audit.data_analysis.exposure_quality_tiers import TIER_ORDER
    _candidate_idx = TIER_ORDER.index(TIER_CANDIDATE)
    any_at_candidate = any(
        TIER_ORDER.index(t) >= _candidate_idx for t in all_tiers
    )

    # Readiness: "ready" only if every catalog is at least analysis_candidate
    not_ready_labels = [
        label for label, t in tier_by_catalog.items()
        if TIER_ORDER.index(t) < _candidate_idx
    ]

    if not_ready_labels:
        readiness        = "not_ready"
        readiness_reason = (
            f"Catalog(s) below analysis_candidate: "
            + ", ".join(f"{l}={tier_by_catalog[l]}" for l in not_ready_labels)
        )
    else:
        readiness        = "ready"
        readiness_reason = (
            "All catalogs meet analysis_candidate or better exposure quality."
        )

    return {
        "exposure_quality_tier_by_catalog":               tier_by_catalog,
        "exposure_quality_requirements_met_by_catalog":   reqs_met_by,
        "exposure_quality_missing_requirements_by_catalog": reqs_missing_by,
        "exposure_quality_evidence_summary_by_catalog":   summary_by,
        "worst_exposure_quality_tier":                    _worst,
        "any_catalog_at_analysis_candidate":              any_at_candidate,
        "confirmatory_exposure_quality_readiness":        readiness,
        "confirmatory_exposure_quality_readiness_reason": readiness_reason,
    }
