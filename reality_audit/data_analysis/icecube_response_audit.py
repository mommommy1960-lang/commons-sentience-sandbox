"""IceCube HESE provenance and detector-response readiness audit.

This module exists because a statistically impressive result is worthless if the
input catalog is not the catalog we think it is, or if detector acceptance is
modeled incorrectly.

Scientific rule: source provenance first, instrument response second, anomaly
language last.
"""

from __future__ import annotations

import csv
import json
import math
import os
from dataclasses import dataclass, asdict
from typing import Dict, Iterable, List, Optional


# Published HESE track-event anchors. Coordinates/energies reproduce values
# published by the IceCube Collaboration for the 3-year HESE sample and are
# independently tabulated in Brown et al., MNRAS 451 (2015) 323-331.
# Event 37 is also present in the PRL 113, 101101 supplementary table.
OFFICIAL_3YR_TRACK_ANCHORS = {
    "HESE_003": {"energy_tev": 78.7, "ra_deg": 127.9, "dec_deg": -31.2, "event_type": "track"},
    "HESE_005": {"energy_tev": 71.4, "ra_deg": 110.6, "dec_deg": -0.4, "event_type": "track"},
    "HESE_008": {"energy_tev": 32.6, "ra_deg": 182.4, "dec_deg": -21.2, "event_type": "track"},
    "HESE_013": {"energy_tev": 253.0, "ra_deg": 67.9, "dec_deg": 40.3, "event_type": "track"},
    "HESE_018": {"energy_tev": 31.5, "ra_deg": 345.6, "dec_deg": -24.8, "event_type": "track"},
    "HESE_023": {"energy_tev": 82.2, "ra_deg": 208.7, "dec_deg": -13.2, "event_type": "track"},
    "HESE_037": {"energy_tev": 30.8, "ra_deg": 167.3, "dec_deg": 20.7, "event_type": "track"},
}

OFFICIAL_7YR_REQUIRED_MC_FIELDS = {
    "primaryEnergy",
    "primaryZenith",
    "primaryType",
    "recoDepositedEnergy",
    "recoZenith",
    "recoLength",
    "recoMorphology",
    "weightOverFluxOverLivetime",
    "muonWeightOverLivetime",
    "pionFlux",
    "kaonFlux",
    "promptFlux",
    "conventionalSelfVetoCorrection",
    "promptSelfVetoCorrection",
}

OFFICIAL_7YR_MC_FILES = (
    "HESE_mc_observable.json",
    "HESE_mc_flux.json",
    "HESE_mc_truth.json",
)


@dataclass(frozen=True)
class AnchorMismatch:
    event_id: str
    field: str
    observed: object
    expected: object


@dataclass(frozen=True)
class ProvenanceAudit:
    path: str
    anchors_checked: int
    mismatches: List[AnchorMismatch]
    trusted_for_scientific_inference: bool
    status: str

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["mismatches"] = [asdict(m) for m in self.mismatches]
        return payload


def _close(a: object, b: float, tolerance: float) -> bool:
    try:
        return abs(float(a) - b) <= tolerance
    except (TypeError, ValueError):
        return False


def audit_legacy_three_year_csv(
    path: str,
    *,
    angular_tolerance_deg: float = 0.35,
    energy_tolerance_tev: float = 1.5,
) -> ProvenanceAudit:
    """Compare the repository's 37-row HESE CSV against published anchor rows.

    A single serious coordinate/topology mismatch is enough to make the file
    unsuitable for confirmatory inference until provenance is repaired.
    """
    with open(path, newline="", encoding="utf-8") as handle:
        rows = {row.get("event_id", ""): row for row in csv.DictReader(handle)}

    mismatches: List[AnchorMismatch] = []
    for event_id, expected in OFFICIAL_3YR_TRACK_ANCHORS.items():
        row = rows.get(event_id)
        if row is None:
            mismatches.append(AnchorMismatch(event_id, "row", None, "present"))
            continue
        checks = (
            ("ra", row.get("ra"), expected["ra_deg"], angular_tolerance_deg),
            ("dec", row.get("dec"), expected["dec_deg"], angular_tolerance_deg),
            ("energy", row.get("energy"), expected["energy_tev"], energy_tolerance_tev),
        )
        for field, observed, target, tolerance in checks:
            if not _close(observed, target, tolerance):
                mismatches.append(AnchorMismatch(event_id, field, observed, target))
        observed_type = (row.get("event_type") or "").strip().lower()
        if observed_type != expected["event_type"]:
            mismatches.append(
                AnchorMismatch(event_id, "event_type", observed_type, expected["event_type"])
            )

    trusted = not mismatches
    return ProvenanceAudit(
        path=path,
        anchors_checked=len(OFFICIAL_3YR_TRACK_ANCHORS),
        mismatches=mismatches,
        trusted_for_scientific_inference=trusted,
        status="PASS" if trusted else "UNTRUSTED_LEGACY_INPUT",
    )


def south_pole_zenith_to_declination_deg(zenith_rad: float) -> float:
    """Convert reconstructed zenith to equatorial declination at South Pole.

    At geographic latitude -90 deg, zenith=0 points to declination -90 deg and
    zenith=pi points to +90 deg, so dec = degrees(zenith) - 90.
    """
    return math.degrees(float(zenith_rad)) - 90.0


def summarize_official_data_json(
    path: str,
    *,
    emin_gev: Optional[float] = None,
    emax_gev: Optional[float] = None,
) -> dict:
    """Summarize north/south counts in IceCube's official HESE data JSON.

    This is an *observed-sample sanity check*, not an exposure model.
    """
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)

    energies = data["recoDepositedEnergy"]
    zeniths = data["recoZenith"]
    if len(energies) != len(zeniths):
        raise ValueError("IceCube data arrays have inconsistent lengths")

    selected = []
    for energy, zenith in zip(energies, zeniths):
        if emin_gev is not None and float(energy) < emin_gev:
            continue
        if emax_gev is not None and float(energy) > emax_gev:
            continue
        selected.append(south_pole_zenith_to_declination_deg(zenith))

    north = sum(dec >= 0.0 for dec in selected)
    south = len(selected) - north
    return {
        "event_count": len(selected),
        "north": north,
        "south": south,
        "north_fraction": north / len(selected) if selected else None,
        "interpretation": "observed_sample_only_not_detector_acceptance",
    }


def exact_binomial_lower_tail(k: int, n: int, p: float) -> float:
    if not (0 <= k <= n):
        raise ValueError("require 0 <= k <= n")
    if not (0.0 <= p <= 1.0):
        raise ValueError("require 0 <= p <= 1")
    return sum(
        math.comb(n, i) * (p ** i) * ((1.0 - p) ** (n - i))
        for i in range(k + 1)
    )


def legacy_hemisphere_sensitivity(k_north: int = 10, n: int = 37) -> List[dict]:
    """Sensitivity table only. Values of p are hypotheses, not response estimates."""
    return [
        {"assumed_north_acceptance": p, "p_north_le_k": exact_binomial_lower_tail(k_north, n, p)}
        for p in (0.50, 0.45, 0.40, 0.35, 0.30)
    ]


def response_model_readiness(directory: str) -> dict:
    """Refuse 'response-informed' status unless all official MC inputs are present.

    The IceCube release splits required information across three large JSON
    files. Merely having the 102-event data file is not enough.
    """
    paths = [os.path.join(directory, name) for name in OFFICIAL_7YR_MC_FILES]
    missing = [path for path in paths if not os.path.exists(path)]
    if missing:
        return {
            "ready": False,
            "quality_tier": "NO_RESPONSE_MODEL",
            "missing_files": missing,
            "required_fields": sorted(OFFICIAL_7YR_REQUIRED_MC_FIELDS),
        }

    merged: Dict[str, object] = {}
    lengths = set()
    for path in paths:
        with open(path, encoding="utf-8") as handle:
            piece = json.load(handle)
        merged.update(piece)
        lengths.update(len(value) for value in piece.values() if isinstance(value, list))

    missing_fields = sorted(OFFICIAL_7YR_REQUIRED_MC_FIELDS - set(merged))
    length_ok = len(lengths) == 1
    ready = not missing_fields and length_ok
    return {
        "ready": ready,
        "quality_tier": "RESPONSE_INPUTS_PRESENT" if ready else "INVALID_RESPONSE_INPUTS",
        "missing_files": [],
        "missing_fields": missing_fields,
        "consistent_array_lengths": length_ok,
        "event_array_lengths": sorted(lengths),
    }
