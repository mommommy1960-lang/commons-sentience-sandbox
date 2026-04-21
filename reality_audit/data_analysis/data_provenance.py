"""
data_provenance.py
==================
Provenance tracking and authenticity certification for Fermi-LAT GRB event
datasets entering the Reality Audit analysis pipeline.

A dataset is classified into one of four authenticity tiers:

  AUTHENTIC_PUBLIC  — has a verified provenance sidecar, is not a known
                      synthetic fixture, and passes content checks.
  REHEARSAL         — a known synthetic fixture file (name or hash match).
  UNVERIFIED        — a CSV exists but no provenance sidecar is present;
                      the run proceeds as REHEARSAL-equivalent and is not
                      eligible for scientific interpretation.
  MISSING           — no candidate file found.

Provenance sidecar format
--------------------------
For each data file at  data/real/<name>.csv
place a companion file  data/real/<name>.provenance.json  containing:

  {
    "source_description": "Fermi-LAT GRB event data from FSSC public archive",
    "data_origin": "Fermi FSSC / HEASARC",
    "acquisition_date": "2026-04-20",
    "source_url": "https://fermi.gsfc.nasa.gov/cgi-bin/ssc/LAT/...",  // optional
    "file_format": "CSV derived from FITS event file",
    "grb_list": ["GRB090902B", "GRB090510", ...],
    "notes": "..."  // optional
  }

Required fields: source_description, data_origin, acquisition_date.
"""

import hashlib
import json
import pathlib
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# SHA-256 prefix of known synthetic fixtures (first 16 hex chars).
# Add new fixtures here whenever a new rehearsal file is generated.
_KNOWN_SYNTHETIC_HASHES: List[str] = [
    "c03d4e648948b933",  # synthetic_fermi_lat_grb_events.csv / real_test_dataset.csv
]

# Name fragments that unambiguously identify a synthetic fixture.
_SYNTHETIC_NAME_MARKERS: List[str] = ["synthetic"]

_REQUIRED_PROVENANCE_FIELDS: List[str] = [
    "source_description",
    "data_origin",
    "acquisition_date",
]


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


class AuthenticityTier(str, Enum):
    AUTHENTIC_PUBLIC = "AUTHENTIC_PUBLIC"
    REHEARSAL        = "REHEARSAL"
    UNVERIFIED       = "UNVERIFIED"
    MISSING          = "MISSING"


@dataclass
class ProvenanceRecord:
    """Parsed and validated provenance sidecar for a data file."""
    source_description: str
    data_origin: str
    acquisition_date: str
    source_url: Optional[str] = None
    file_format: Optional[str] = None
    grb_list: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    sidecar_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AuthenticityReport:
    """Full authenticity assessment for a candidate data file."""
    candidate_path: Optional[str]
    authenticity_tier: AuthenticityTier
    sha256_prefix: Optional[str]
    is_known_synthetic: bool
    provenance_sidecar_found: bool
    provenance_valid: bool
    provenance: Optional[ProvenanceRecord]
    provenance_missing_fields: List[str]
    failure_reasons: List[str]
    eligible_for_scientific_run: bool

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["authenticity_tier"] = self.authenticity_tier.value
        if self.provenance:
            d["provenance"] = self.provenance.to_dict()
        return d


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _sha256_prefix(path: pathlib.Path, n: int = 16) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:n]


def _is_known_synthetic(path: pathlib.Path) -> bool:
    """Return True if file is a known synthetic fixture by name or hash."""
    name_lower = path.name.lower()
    if any(marker in name_lower for marker in _SYNTHETIC_NAME_MARKERS):
        return True
    try:
        prefix = _sha256_prefix(path)
        if prefix in _KNOWN_SYNTHETIC_HASHES:
            return True
    except OSError:
        pass
    return False


def _sidecar_path(csv_path: pathlib.Path) -> pathlib.Path:
    return csv_path.with_suffix(".provenance.json")


def _load_provenance_sidecar(
    csv_path: pathlib.Path,
) -> tuple:  # (ProvenanceRecord | None, list[str])
    """
    Load and validate the provenance sidecar for csv_path.

    Returns (ProvenanceRecord, missing_fields).
    If file not found or parse error, returns (None, [reason]).
    """
    sp = _sidecar_path(csv_path)
    if not sp.exists():
        return None, ["SIDECAR_FILE_NOT_FOUND"]
    try:
        raw = json.loads(sp.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        return None, [f"SIDECAR_PARSE_ERROR: {exc}"]

    missing = [f for f in _REQUIRED_PROVENANCE_FIELDS if not raw.get(f)]
    if missing:
        return None, [f"MISSING_REQUIRED_PROVENANCE_FIELDS: {missing}"]

    record = ProvenanceRecord(
        source_description=raw["source_description"],
        data_origin=raw["data_origin"],
        acquisition_date=raw["acquisition_date"],
        source_url=raw.get("source_url"),
        file_format=raw.get("file_format"),
        grb_list=raw.get("grb_list", []),
        notes=raw.get("notes"),
        sidecar_path=str(sp),
    )
    return record, []


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def assess_authenticity(candidate_path: str) -> AuthenticityReport:
    """
    Assess the authenticity and provenance of a candidate data file.

    Parameters
    ----------
    candidate_path : str
        Path to the CSV file to assess.

    Returns
    -------
    AuthenticityReport
    """
    path = pathlib.Path(candidate_path)
    failure_reasons: List[str] = []

    # -----------------------------------------------------------------------
    # Missing file
    # -----------------------------------------------------------------------
    if not path.exists():
        return AuthenticityReport(
            candidate_path=str(path),
            authenticity_tier=AuthenticityTier.MISSING,
            sha256_prefix=None,
            is_known_synthetic=False,
            provenance_sidecar_found=False,
            provenance_valid=False,
            provenance=None,
            provenance_missing_fields=["FILE_NOT_FOUND"],
            failure_reasons=["FILE_NOT_FOUND"],
            eligible_for_scientific_run=False,
        )

    # -----------------------------------------------------------------------
    # Hash / name check
    # -----------------------------------------------------------------------
    try:
        sha256_prefix = _sha256_prefix(path)
    except OSError as exc:
        sha256_prefix = None
        failure_reasons.append(f"HASH_ERROR: {exc}")

    is_synthetic = _is_known_synthetic(path)
    if is_synthetic:
        failure_reasons.append(
            "KNOWN_SYNTHETIC_FIXTURE: file is a rehearsal dataset and is not eligible "
            "for scientific analysis"
        )

    # -----------------------------------------------------------------------
    # Provenance sidecar
    # -----------------------------------------------------------------------
    sidecar_exists = _sidecar_path(path).exists()
    provenance: Optional[ProvenanceRecord] = None
    provenance_missing: List[str] = []
    provenance_valid = False

    if sidecar_exists:
        provenance, provenance_missing = _load_provenance_sidecar(path)
        if provenance is not None and not provenance_missing:
            provenance_valid = True
        else:
            failure_reasons.extend(provenance_missing)
    else:
        failure_reasons.append("MISSING_PROVENANCE_SIDECAR")
        provenance_missing = ["SIDECAR_FILE_NOT_FOUND"]

    # -----------------------------------------------------------------------
    # Determine tier
    # -----------------------------------------------------------------------
    if is_synthetic:
        tier = AuthenticityTier.REHEARSAL
    elif not sidecar_exists or not provenance_valid:
        tier = AuthenticityTier.UNVERIFIED
    else:
        tier = AuthenticityTier.AUTHENTIC_PUBLIC

    eligible = tier == AuthenticityTier.AUTHENTIC_PUBLIC

    return AuthenticityReport(
        candidate_path=str(path),
        authenticity_tier=tier,
        sha256_prefix=sha256_prefix,
        is_known_synthetic=is_synthetic,
        provenance_sidecar_found=sidecar_exists,
        provenance_valid=provenance_valid,
        provenance=provenance,
        provenance_missing_fields=provenance_missing,
        failure_reasons=failure_reasons,
        eligible_for_scientific_run=eligible,
    )


def write_provenance_sidecar(
    csv_path: str,
    source_description: str,
    data_origin: str,
    acquisition_date: str,
    source_url: Optional[str] = None,
    file_format: Optional[str] = None,
    grb_list: Optional[List[str]] = None,
    notes: Optional[str] = None,
) -> str:
    """
    Write a provenance sidecar JSON next to csv_path.

    Returns the sidecar file path as a string.
    """
    sp = _sidecar_path(pathlib.Path(csv_path))
    record = {
        "source_description": source_description,
        "data_origin": data_origin,
        "acquisition_date": acquisition_date,
        "source_url": source_url,
        "file_format": file_format,
        "grb_list": grb_list or [],
        "notes": notes,
    }
    sp.write_text(json.dumps(record, indent=2))
    return str(sp)
