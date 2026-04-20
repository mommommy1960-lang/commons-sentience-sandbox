"""
check_fermi_lat_real_package.py
================================
Pre-ingest validation check for a real Fermi-LAT GRB event CSV.

Runs lightweight checks on a candidate data file *before* the full ingest
pipeline is invoked, and produces a human-readable JSON recommendation.

Outputs
-------
commons_sentience_sim/output/reality_audit/fermi_lat_real_package_check.json

Recommendations
---------------
ACCEPT_FOR_BLINDED_RUN  — all hard gates pass, no warnings
ACCEPT_WITH_WARNINGS    — hard gates pass, soft issues present
REJECT                  — at least one hard stopping rule violated

Usage (CLI)
-----------
python reality_audit/data_analysis/check_fermi_lat_real_package.py \
    --input data/real/your_file.csv

Usage (API)
-----------
from reality_audit.data_analysis.check_fermi_lat_real_package import check_real_package
report = check_real_package("data/real/your_file.csv")
"""

import csv
import json
import pathlib
import sys
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MIN_TOTAL_EVENTS = 30
_MIN_SOURCES_WITH_REDSHIFT = 5
_MAX_DUPLICATE_FRACTION = 0.001  # 0.1 %
_MIN_ENERGY_GEV = 0.01
_MAX_ENERGY_GEV = 1000.0

_REQUIRED_HEADERS = {"event_id", "grb_name", "energy_gev", "redshift", "grb_t90_s"}
_ARRIVAL_TIME_ALIASES = {
    "photon_arrival_time_s", "arrival_time_s", "arrival_time",
    "time_s", "time", "t", "t_s",
}

_DEFAULT_OUTPUT_PATH = pathlib.Path(
    "commons_sentience_sim/output/reality_audit/fermi_lat_real_package_check.json"
)

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _find_arrival_time_col(headers: List[str]) -> Optional[str]:
    lower = {h.lower(): h for h in headers}
    for alias in _ARRIVAL_TIME_ALIASES:
        if alias in lower:
            return lower[alias]
    return None


def _try_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _load_csv(path: str) -> List[Dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader), list(reader.fieldnames or [])


# reload properly to get both rows and fieldnames
def _load_csv_with_headers(path: str):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])
    return rows, fieldnames


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def check_real_package(
    path: str,
    output_path: Optional[str] = None,
    min_total_events: int = _MIN_TOTAL_EVENTS,
    min_sources_with_redshift: int = _MIN_SOURCES_WITH_REDSHIFT,
    max_duplicate_fraction: float = _MAX_DUPLICATE_FRACTION,
) -> Dict[str, Any]:
    """
    Validate a candidate real-data CSV file without running the full pipeline.

    Parameters
    ----------
    path : str
        Path to the CSV file to check.
    output_path : str, optional
        Override output JSON path. Defaults to _DEFAULT_OUTPUT_PATH.
    min_total_events : int
    min_sources_with_redshift : int
    max_duplicate_fraction : float

    Returns
    -------
    dict with keys:
        path, n_events, n_sources, n_sources_with_redshift,
        n_missing_redshift, duplicate_fraction, schema_valid,
        missing_columns, warnings, hard_failures,
        recommendation, output_path
    """
    p = pathlib.Path(path)

    # -----------------------------------------------------------------------
    # Safe execution guard — no file, no run
    # -----------------------------------------------------------------------
    if not p.exists():
        report = {
            "path": str(path),
            "file_found": False,
            "n_events": 0,
            "n_sources": 0,
            "n_sources_with_redshift": 0,
            "n_missing_redshift": 0,
            "duplicate_fraction": 0.0,
            "schema_valid": False,
            "missing_columns": [],
            "warnings": [],
            "hard_failures": ["FILE_NOT_FOUND"],
            "recommendation": "REJECT",
            "message": "No real dataset detected. System ready for ingestion.",
        }
        _write_report(report, output_path)
        return report

    rows, fieldnames = _load_csv_with_headers(str(p))
    headers_lower = {h.lower() for h in fieldnames}

    hard_failures: List[str] = []
    warnings: List[str] = []

    # -----------------------------------------------------------------------
    # Schema check
    # -----------------------------------------------------------------------
    missing_cols = []
    for col in _REQUIRED_HEADERS:
        if col not in headers_lower:
            missing_cols.append(col)

    arrival_col = _find_arrival_time_col(fieldnames)
    if arrival_col is None:
        missing_cols.append("arrival_time (no recognised alias found)")

    schema_valid = len(missing_cols) == 0
    if not schema_valid:
        hard_failures.append(f"MISSING_REQUIRED_COLUMNS: {missing_cols}")

    # -----------------------------------------------------------------------
    # Event count
    # -----------------------------------------------------------------------
    n_events = len(rows)
    if n_events < min_total_events:
        hard_failures.append(
            f"TOO_FEW_EVENTS: {n_events} < {min_total_events}"
        )

    # -----------------------------------------------------------------------
    # Duplicate fraction
    # -----------------------------------------------------------------------
    id_col = next(
        (h for h in fieldnames if h.lower() == "event_id"),
        None,
    )
    if id_col and n_events > 0:
        ids = [r.get(id_col, "") for r in rows]
        n_dup = n_events - len(set(ids))
        dup_fraction = n_dup / n_events
    else:
        n_dup = 0
        dup_fraction = 0.0

    if dup_fraction > max_duplicate_fraction:
        hard_failures.append(
            f"DUPLICATE_FRACTION_EXCEEDED: {dup_fraction:.4%} > {max_duplicate_fraction:.4%}"
        )

    # -----------------------------------------------------------------------
    # Redshift coverage
    # -----------------------------------------------------------------------
    source_col = next(
        (h for h in fieldnames if h.lower() in {"grb_name", "source_id", "source"}),
        None,
    )
    redshift_col = next(
        (h for h in fieldnames if h.lower() in {"redshift", "z", "z_spec", "z_photo"}),
        None,
    )

    sources_all: set = set()
    sources_with_z: set = set()
    n_missing_redshift = 0

    for row in rows:
        src = row.get(source_col, "") if source_col else ""
        sources_all.add(src)
        z_raw = row.get(redshift_col, "") if redshift_col else ""
        z = _try_float(z_raw)
        if z is not None and z >= 0:
            sources_with_z.add(src)
        else:
            n_missing_redshift += 1

    n_sources = len(sources_all)
    n_sources_with_redshift = len(sources_with_z)

    if n_sources_with_redshift < min_sources_with_redshift:
        hard_failures.append(
            f"INSUFFICIENT_REDSHIFT_COVERAGE: {n_sources_with_redshift} "
            f"sources with z < {min_sources_with_redshift}"
        )

    # -----------------------------------------------------------------------
    # Energy range soft check
    # -----------------------------------------------------------------------
    energy_col = next(
        (h for h in fieldnames if h.lower() in {"energy_gev", "energy", "photon_energy", "e_gev"}),
        None,
    )
    n_implausible_energy = 0
    if energy_col:
        for row in rows:
            e = _try_float(row.get(energy_col, ""))
            if e is not None and not (_MIN_ENERGY_GEV <= e <= _MAX_ENERGY_GEV):
                n_implausible_energy += 1

    if n_implausible_energy > 0:
        warnings.append(
            f"ENERGY_OUT_OF_RANGE: {n_implausible_energy} events have energy "
            f"outside [{_MIN_ENERGY_GEV}, {_MAX_ENERGY_GEV}] GeV"
        )

    # -----------------------------------------------------------------------
    # Recommendation
    # -----------------------------------------------------------------------
    if hard_failures:
        recommendation = "REJECT"
    elif warnings:
        recommendation = "ACCEPT_WITH_WARNINGS"
    else:
        recommendation = "ACCEPT_FOR_BLINDED_RUN"

    # -----------------------------------------------------------------------
    # Build report
    # -----------------------------------------------------------------------
    out_path = str(output_path or _DEFAULT_OUTPUT_PATH)
    report = {
        "path": str(path),
        "file_found": True,
        "n_events": n_events,
        "n_sources": n_sources,
        "n_sources_with_redshift": n_sources_with_redshift,
        "n_missing_redshift": n_missing_redshift,
        "duplicate_fraction": round(dup_fraction, 6),
        "schema_valid": schema_valid,
        "missing_columns": missing_cols,
        "warnings": warnings,
        "hard_failures": hard_failures,
        "recommendation": recommendation,
        "output_path": out_path,
    }

    _write_report(report, output_path)
    return report


def _write_report(report: Dict[str, Any], output_path: Optional[str] = None) -> None:
    out = pathlib.Path(output_path or _DEFAULT_OUTPUT_PATH)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _cli() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Pre-ingest validation check for a real Fermi-LAT GRB event CSV."
    )
    parser.add_argument("--input", required=False, help="Path to CSV file to check.")
    parser.add_argument("--output", default=None, help="Override output JSON path.")
    args = parser.parse_args()

    data_dir = pathlib.Path("data/real")
    if not args.input:
        # Safe execution guard — look for any non-synthetic CSV
        candidates = [
            f for f in data_dir.glob("*.csv")
            if "synthetic" not in f.name.lower()
        ]
        if not candidates:
            print("No real dataset detected. System ready for ingestion.")
            _write_report(
                {
                    "path": str(data_dir),
                    "file_found": False,
                    "n_events": 0,
                    "n_sources": 0,
                    "n_sources_with_redshift": 0,
                    "n_missing_redshift": 0,
                    "duplicate_fraction": 0.0,
                    "schema_valid": False,
                    "missing_columns": [],
                    "warnings": [],
                    "hard_failures": ["NO_REAL_FILE_FOUND"],
                    "recommendation": "REJECT",
                    "message": "No real dataset detected. System ready for ingestion.",
                },
                args.output,
            )
            sys.exit(0)
        input_path = str(candidates[0])
    else:
        input_path = args.input

    report = check_real_package(input_path, output_path=args.output)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    _cli()
