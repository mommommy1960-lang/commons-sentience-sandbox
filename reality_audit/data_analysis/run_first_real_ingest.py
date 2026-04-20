"""
run_first_real_ingest.py
========================
One-shot helper for the first true real-data ingest.

Behaviour
---------
1. Scan data/real/ for candidate CSV files, excluding any file whose name
   contains "synthetic" (case-insensitive).
2. If NO candidate found:
   - Print "No real dataset detected. System ready for ingestion."
   - Write a WAITING manifest and exit 0.
3. If candidate found:
   - Run check_fermi_lat_real_package() on it.
   - If recommendation != ACCEPT_FOR_BLINDED_RUN: write manifest with
     status BLOCKED, print reason, exit 0. (Includes ACCEPT_WITH_WARNINGS —
     human must review before proceeding.)
   - If recommendation == ACCEPT_FOR_BLINDED_RUN: run the blinded pipeline,
     write first_real_ingest_manifest.json, exit 0.

Outputs
-------
commons_sentience_sim/output/reality_audit/first_real_ingest_manifest.json

Constraints
-----------
- automatic_unblind is always False
- synthetic files are never treated as real data
"""

import json
import pathlib
import sys
from typing import Any, Dict, List, Optional

from reality_audit.data_analysis.check_fermi_lat_real_package import check_real_package
from reality_audit.data_analysis.run_fermi_lat_real_blinded import (
    run_fermi_lat_real_blinded,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DATA_DIR = pathlib.Path("data/real")
_MANIFEST_PATH = pathlib.Path(
    "commons_sentience_sim/output/reality_audit/first_real_ingest_manifest.json"
)
_REGISTRATION_PATH = pathlib.Path(
    "commons_sentience_sim/output/reality_audit/fermi_lat_real_analysis_registration.json"
)
_SYNTHETIC_MARKER = "synthetic"  # files whose name contains this are excluded


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _find_real_candidates(data_dir: pathlib.Path = _DATA_DIR) -> List[pathlib.Path]:
    """Return CSV files in data_dir that are not synthetic fixtures."""
    if not data_dir.exists():
        return []
    return [
        f for f in sorted(data_dir.glob("*.csv"))
        if _SYNTHETIC_MARKER not in f.name.lower()
    ]


def _write_manifest(manifest: Dict[str, Any], path: pathlib.Path = _MANIFEST_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_first_real_ingest(
    data_dir: Optional[str] = None,
    registration_path: Optional[str] = None,
    manifest_path: Optional[str] = None,
    n_permutations: int = 500,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Discover, validate, and (if accepted) run the blinded pipeline on the
    first real CSV in data/real/.

    Parameters
    ----------
    data_dir : str, optional
        Override for data/real/.
    registration_path : str, optional
        Override for the registration JSON path.
    manifest_path : str, optional
        Override for first_real_ingest_manifest.json path.
    n_permutations : int
    seed : int

    Returns
    -------
    dict with keys:
        status          — WAITING | BLOCKED | COMPLETE | ERROR
        candidate       — path of candidate file (or None)
        check_report    — output of check_real_package (or None)
        blinded_result  — output of run_fermi_lat_real_blinded (or None)
        manifest_path   — path manifest was written to
        message         — human-readable summary
    """
    d_dir = pathlib.Path(data_dir) if data_dir else _DATA_DIR
    reg_path = str(registration_path or _REGISTRATION_PATH)
    mfst_path = pathlib.Path(manifest_path or _MANIFEST_PATH)

    # -----------------------------------------------------------------------
    # Step 1 — Find candidate
    # -----------------------------------------------------------------------
    candidates = _find_real_candidates(d_dir)

    if not candidates:
        msg = "No real dataset detected. System ready for ingestion."
        print(msg)
        manifest: Dict[str, Any] = {
            "status": "WAITING",
            "candidate": None,
            "check_report": None,
            "blinded_result": None,
            "manifest_path": str(mfst_path),
            "message": msg,
        }
        _write_manifest(manifest, mfst_path)
        return manifest

    candidate = candidates[0]  # use the first discovered file
    print(f"Candidate real file found: {candidate}")

    # -----------------------------------------------------------------------
    # Step 2 — Package check
    # -----------------------------------------------------------------------
    check_out = str(mfst_path.parent / "fermi_lat_real_package_check.json")
    check_report = check_real_package(str(candidate), output_path=check_out)
    recommendation = check_report.get("recommendation", "REJECT")

    if recommendation != "ACCEPT_FOR_BLINDED_RUN":
        reason = (
            f"Package check returned '{recommendation}'. "
            f"Hard failures: {check_report.get('hard_failures', [])}. "
            f"Warnings: {check_report.get('warnings', [])}."
        )
        print(f"BLOCKED: {reason}")
        manifest = {
            "status": "BLOCKED",
            "candidate": str(candidate),
            "check_report": check_report,
            "blinded_result": None,
            "manifest_path": str(mfst_path),
            "message": reason,
        }
        _write_manifest(manifest, mfst_path)
        return manifest

    print(f"Package check: {recommendation} — proceeding to blinded run.")

    # -----------------------------------------------------------------------
    # Step 3 — Blinded run
    # -----------------------------------------------------------------------
    try:
        blinded_result = run_fermi_lat_real_blinded(
            source_file=str(candidate),
            registration_path=reg_path,
            n_permutations=n_permutations,
            seed=seed,
        )
    except Exception as exc:  # noqa: BLE001
        msg = f"Blinded run raised an exception: {exc}"
        print(f"ERROR: {msg}")
        manifest = {
            "status": "ERROR",
            "candidate": str(candidate),
            "check_report": check_report,
            "blinded_result": None,
            "manifest_path": str(mfst_path),
            "message": msg,
        }
        _write_manifest(manifest, mfst_path)
        return manifest

    run_ok = blinded_result.get("run_ok", False)
    status = "COMPLETE" if run_ok else "BLOCKED"
    msg = (
        f"Blinded run {'completed successfully' if run_ok else 'was blocked'}. "
        f"Stop reasons: {blinded_result.get('stop_reasons', [])}. "
        "Unblinding requires explicit human approval."
    )
    print(msg)

    manifest = {
        "status": status,
        "candidate": str(candidate),
        "check_report": check_report,
        "blinded_result": {
            k: v for k, v in blinded_result.items()
            if k not in ("blinded_summary",)  # don't duplicate large nested dict
        },
        "manifest_path": str(mfst_path),
        "message": msg,
    }
    _write_manifest(manifest, mfst_path)
    return manifest


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _cli() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="One-shot helper: discover, validate, and run the first real ingest."
    )
    parser.add_argument("--data-dir", default=None)
    parser.add_argument("--registration", default=None)
    parser.add_argument("--manifest-out", default=None)
    parser.add_argument("--n-permutations", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    result = run_first_real_ingest(
        data_dir=args.data_dir,
        registration_path=args.registration,
        manifest_path=args.manifest_out,
        n_permutations=args.n_permutations,
        seed=args.seed,
    )
    print(json.dumps({k: v for k, v in result.items() if k != "blinded_result"}, indent=2))


if __name__ == "__main__":
    _cli()
