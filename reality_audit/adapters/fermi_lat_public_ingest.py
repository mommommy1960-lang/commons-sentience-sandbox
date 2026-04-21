"""
fermi_lat_public_ingest.py
===========================
Ingest and validate a real local public-data file (CSV or JSON) for the
Fermi-LAT GRB timing-delay analysis.

This module is a stricter wrapper around fermi_lat_grb_adapter.py that:
  1. Validates the schema against the registered analysis plan
  2. Runs all pre-ingest quality-control checks
  3. Produces an ingest manifest with validation report
  4. STOPS SAFELY if any stopping rule is triggered

If no real file is available, it can be used in dry-run mode with
a strict-mock-public-schema file (same columns/types as the real dataset).

Design principles:
  - Read-only: never modifies source file (P01)
  - Fails loudly: raises IngestError with a clear message if checks fail
  - All decisions recorded in the manifest
  - Does not auto-unblind

Usage:
    from reality_audit.adapters.fermi_lat_public_ingest import (
        IngestConfig, ingest_public_file, load_ingest_manifest
    )
    config = IngestConfig(source_file="path/to/real_grb_events.csv")
    result = ingest_public_file(config)
"""

from __future__ import annotations

import csv
import datetime
import json
import pathlib
import os
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Imports from existing adapter
# ---------------------------------------------------------------------------

import sys
_REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from reality_audit.adapters.fermi_lat_grb_adapter import (
    load_grb_events,
    to_timing_pipeline_format,
)

# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class IngestError(RuntimeError):
    """Raised when ingest is blocked by a stopping rule or schema violation."""


# ---------------------------------------------------------------------------
# Ingest configuration
# ---------------------------------------------------------------------------


@dataclass
class IngestConfig:
    """
    Configuration for one public-data ingest pass.

    Parameters
    ----------
    source_file : str
        Absolute or relative path to the local data file (CSV, JSON, NDJSON).
    energy_unit : str
        Unit of photon_energy column ("GeV", "MeV", "TeV", "keV").
    time_unit : str
        Unit of arrival_time column ("s" or "MJD").
    column_map : dict
        Override auto-detection: {"photon_energy": "ENERGY", ...}.
    min_events_per_source : int
        Minimum events per GRB source; sources below this are dropped.
    min_total_events : int
        Minimum total events after all quality cuts; triggers STOP.
    min_sources_with_redshift : int
        Minimum GRBs with a known redshift; triggers STOP.
    max_duplicate_fraction : float
        Maximum fraction of duplicate event IDs before STOP.
    output_dir : str
        Directory to write the ingest manifest.
    experiment_name : str
        Label for this ingest pass.
    dry_run : bool
        If True, use relaxed thresholds and add dry_run flag to manifest.
    """
    source_file: str = ""
    energy_unit: str = "GeV"
    time_unit: str = "s"
    column_map: Dict[str, str] = field(default_factory=dict)
    min_events_per_source: int = 5
    min_total_events: int = 30
    min_sources_with_redshift: int = 5
    max_duplicate_fraction: float = 0.001
    output_dir: str = str(
        _REPO_ROOT
        / "commons_sentience_sim"
        / "output"
        / "reality_audit"
        / "fermi_lat_public_ingest"
    )
    experiment_name: str = "fermi_lat_grb_timing_v1"
    dry_run: bool = False


# ---------------------------------------------------------------------------
# Quality-control checks
# ---------------------------------------------------------------------------


def _check_schema(raw: Dict[str, Any], config: IngestConfig) -> List[str]:
    """Validate schema completeness.  Returns list of warning strings."""
    warnings = []

    for ev in raw["events"]:
        if ev.get("energy") is None or not isinstance(ev.get("energy"), (int, float)):
            warnings.append(f"Event {ev.get('event_id')} missing or non-numeric energy.")
        if ev.get("time") is None:
            warnings.append(f"Event {ev.get('event_id')} missing time.")
        if ev.get("source") is None or str(ev.get("source", "")).strip() == "":
            warnings.append(f"Event {ev.get('event_id')} missing source_id.")

    return warnings[:20]  # cap at 20 warnings


def _check_energy_units(raw: Dict[str, Any]) -> List[str]:
    """Check for implausible energy values given the declared unit."""
    warnings = []
    energies = [ev["energy"] for ev in raw["events"] if ev.get("energy") is not None]
    if not energies:
        warnings.append("No valid energy values found.")
        return warnings
    max_e = max(energies)
    min_e = min(energies)
    if max_e > 1e6:
        warnings.append(
            f"Maximum energy {max_e:.2e} GeV is implausibly large — "
            "possible unit mismatch (MeV ingested as GeV?)."
        )
    if min_e < 1e-6:
        warnings.append(
            f"Minimum energy {min_e:.2e} GeV is implausibly small — "
            "possible unit mismatch (eV ingested as GeV?)."
        )
    return warnings


def _check_timestamps(raw: Dict[str, Any]) -> List[str]:
    """Check for negative times or impossibly large time spans."""
    warnings = []
    for src, grp in raw["by_source"].items():
        span = grp.get("time_span_s", 0.0)
        if span < 0:
            warnings.append(f"Source {src}: negative time span {span}.")
        if span > 86400:  # > 1 day in seconds — odd for a GRB
            warnings.append(
                f"Source {src}: time span {span:.0f} s > 86400 s (1 day). "
                "Check time_unit or trigger reference."
            )
    return warnings


def _check_duplicates(raw: Dict[str, Any], max_fraction: float) -> List[str]:
    """Check for duplicate event IDs."""
    ids = [ev["event_id"] for ev in raw["events"]]
    n_total = len(ids)
    n_unique = len(set(ids))
    n_dup = n_total - n_unique
    frac = n_dup / n_total if n_total > 0 else 0.0
    if frac > max_fraction:
        return [
            f"Duplicate event IDs: {n_dup}/{n_total} ({frac:.2%}) exceeds "
            f"threshold {max_fraction:.2%}. STOPPING."
        ]
    return []


def _check_redshift_coverage(raw: Dict[str, Any], min_sources: int) -> List[str]:
    """Check that enough sources have a known redshift."""
    n_with_z = sum(
        1 for src_data in raw["by_source"].values()
        if any(ev.get("redshift") is not None for ev in src_data["events"])
    )
    if n_with_z < min_sources:
        return [
            f"Only {n_with_z} sources have redshift; minimum required is {min_sources}. "
            "STOPPING."
        ]
    return []


def _check_outlier_energies(raw: Dict[str, Any]) -> List[str]:
    """Flag energies more than 10× the inter-quartile range above Q3."""
    energies = sorted(ev["energy"] for ev in raw["events"] if ev.get("energy"))
    n = len(energies)
    if n < 4:
        return []
    q1 = energies[n // 4]
    q3 = energies[3 * n // 4]
    iqr = q3 - q1
    fence = q3 + 10 * iqr
    outliers = [e for e in energies if e > fence]
    if outliers:
        return [
            f"{len(outliers)} energy outlier(s) above 10×IQR fence "
            f"({fence:.2f} GeV): max = {max(outliers):.2f} GeV. Flag for review."
        ]
    return []


# ---------------------------------------------------------------------------
# Stopping rules
# ---------------------------------------------------------------------------

STOPPING_RULES = [
    ("duplicate_ids", lambda raw, cfg: bool(_check_duplicates(raw, cfg.max_duplicate_fraction))),
    ("redshift_coverage", lambda raw, cfg: bool(_check_redshift_coverage(raw, cfg.min_sources_with_redshift))),
    ("too_few_total_events", lambda raw, cfg: raw["metadata"]["n_events"] < cfg.min_total_events),
    ("energy_implausible", lambda raw, cfg: any(
        "implausibly" in w for w in _check_energy_units(raw)
    )),
]


def _evaluate_stopping_rules(
    raw: Dict[str, Any],
    config: IngestConfig,
    warnings: List[str],
) -> List[str]:
    """Return list of triggered stopping rule names (empty = proceed)."""
    triggered = []
    for rule_name, rule_fn in STOPPING_RULES:
        try:
            if rule_fn(raw, config):
                triggered.append(rule_name)
        except Exception as exc:
            warnings.append(f"Stopping rule '{rule_name}' raised: {exc}")
    return triggered


# ---------------------------------------------------------------------------
# Core ingest function
# ---------------------------------------------------------------------------


def ingest_public_file(config: IngestConfig) -> Dict[str, Any]:
    """
    Ingest a local public-data file through the Fermi-LAT adapter with
    full quality-control validation.

    Parameters
    ----------
    config : IngestConfig

    Returns
    -------
    Dict with keys:
        raw           : adapter raw output (events, by_source, metadata)
        pipeline_fmt  : to_timing_pipeline_format() output
        manifest      : dict written to ingest manifest JSON
        stopped       : True if a stopping rule was triggered
        stop_reasons  : list of stopping rule names triggered

    Raises
    ------
    IngestError
        If a hard stopping rule is triggered AND config.dry_run is False.
    FileNotFoundError
        If source_file does not exist.
    """
    source = pathlib.Path(config.source_file)
    if not source.exists():
        raise FileNotFoundError(
            f"Source file not found: {source}. "
            "Provide a local public-data file before ingesting."
        )

    os.makedirs(config.output_dir, exist_ok=True)

    # --- 1. Load through adapter -------------------------------------------
    raw = load_grb_events(
        str(source),
        column_map=config.column_map if config.column_map else None,
        energy_unit=config.energy_unit,
        time_unit=config.time_unit,
        min_events_per_source=config.min_events_per_source,
    )

    # --- 2. Quality-control checks ----------------------------------------
    all_warnings: List[str] = []

    all_warnings += _check_schema(raw, config)
    all_warnings += _check_energy_units(raw)
    all_warnings += _check_timestamps(raw)
    all_warnings += _check_duplicates(raw, config.max_duplicate_fraction)
    all_warnings += _check_redshift_coverage(raw, config.min_sources_with_redshift)
    all_warnings += _check_outlier_energies(raw)

    # --- 3. Evaluate stopping rules ----------------------------------------
    stopped_rules = _evaluate_stopping_rules(raw, config, all_warnings)
    stopped = bool(stopped_rules)

    # --- 4. Build ingest manifest ------------------------------------------
    manifest = {
        "ingest_timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "experiment_name": config.experiment_name,
        "source_file": str(source),
        "dry_run": config.dry_run,
        "config": {k: v for k, v in asdict(config).items() if k != "column_map"},
        "metadata": raw["metadata"],
        "n_events_after_qc": raw["metadata"]["n_events"],
        "n_sources_after_qc": raw["metadata"]["n_sources"],
        "n_dropped_by_adapter": raw["metadata"]["n_dropped"],
        "warnings": all_warnings,
        "n_warnings": len(all_warnings),
        "stopping_rules_triggered": stopped_rules,
        "stopped": stopped,
        "status": "STOPPED" if (stopped and not config.dry_run) else "OK",
        "by_source_summary": {
            src: {
                "n_events": grp["n_events"],
                "mean_energy_GeV": round(grp["mean_energy_GeV"], 4),
                "time_span_s": round(grp["time_span_s"], 3),
                "has_redshift": any(
                    ev.get("redshift") is not None for ev in grp["events"]
                ),
            }
            for src, grp in raw["by_source"].items()
        },
    }

    # Write manifest
    manifest_path = pathlib.Path(config.output_dir) / "fermi_lat_public_ingest_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    # --- 5. Convert to pipeline format (always, even if stopped) -----------
    pipeline_fmt = to_timing_pipeline_format(raw)

    # --- 6. Raise if stopped and not dry_run ------------------------------
    if stopped and not config.dry_run:
        rules_str = ", ".join(stopped_rules)
        raise IngestError(
            f"Ingest blocke by stopping rule(s): [{rules_str}]. "
            f"See manifest: {manifest_path}. "
            "Do not proceed to analysis until stopping conditions are resolved."
        )

    return {
        "raw": raw,
        "pipeline_fmt": pipeline_fmt,
        "manifest": manifest,
        "stopped": stopped,
        "stop_reasons": stopped_rules,
        "manifest_path": str(manifest_path),
    }


def load_ingest_manifest(output_dir: str | None = None) -> Dict[str, Any]:
    """Load and return the latest ingest manifest."""
    d = pathlib.Path(output_dir) if output_dir else (
        _REPO_ROOT
        / "commons_sentience_sim"
        / "output"
        / "reality_audit"
        / "fermi_lat_public_ingest"
    )
    manifest_path = d / "fermi_lat_public_ingest_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Ingest manifest not found at {manifest_path}.")
    with open(manifest_path) as f:
        return json.load(f)
