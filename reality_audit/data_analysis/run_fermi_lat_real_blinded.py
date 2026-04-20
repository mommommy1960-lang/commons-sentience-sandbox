"""
run_fermi_lat_real_blinded.py
==============================
Blinded real-data runner for the Fermi-LAT GRB timing-delay analysis.

Requires the following to exist before running:
  1. Registration JSON  (register_fermi_lat_real_analysis.py must have run)
  2. Ingest manifest    (fermi_lat_public_ingest.py must have run and succeeded)

Produces (all in output_dir):
  - blinded_summary.json       — signal keys replaced with "BLINDED"
  - run_manifest.json          — full run provenance (inputs, config, QC verdict)
  - quality_control_report.json — per-check QC results

Does NOT produce an unblinded result automatically.
Unblinding requires explicit human intervention and separate tooling.

Design note
-----------
signal_keys = ("observed_slope", "p_value", "z_score",
               "detection_claimed", "null_retained")

These are computed internally but are replaced with the string "BLINDED"
in blinded_summary.json.  They are NOT written to disk in any form.

Usage (script)
--------------
    python reality_audit/data_analysis/run_fermi_lat_real_blinded.py \\
        --source path/to/grb_events.csv \\
        --registration commons_sentience_sim/output/reality_audit/fermi_lat_real_analysis_registration.json \\
        --output commons_sentience_sim/output/reality_audit/fermi_lat_real_blinded_run/

Usage (import)
--------------
    from reality_audit.data_analysis.run_fermi_lat_real_blinded import (
        run_fermi_lat_real_blinded,
    )
    result = run_fermi_lat_real_blinded(
        source_file="path/to/grb_events.csv",
        registration_path="...registration.json",
        ingest_manifest_path="...manifest.json",
        output_dir="...output/",
    )
"""

from __future__ import annotations

import json
import os
import pathlib
import sys

_REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from reality_audit.adapters.fermi_lat_public_ingest import (
    IngestConfig,
    IngestError,
    ingest_public_file,
)
from reality_audit.data_analysis.register_fermi_lat_real_analysis import (
    load_registration,
)
from reality_audit.data_analysis.real_timing_pipeline import run_real_timing_pipeline

# ---------------------------------------------------------------------------
# Signal keys that are blinded
# ---------------------------------------------------------------------------

_SIGNAL_KEYS = (
    "observed_slope",
    "p_value",
    "z_score",
    "detection_claimed",
    "null_retained",
)

_DEFAULT_REGISTRATION = str(
    _REPO_ROOT
    / "commons_sentience_sim"
    / "output"
    / "reality_audit"
    / "fermi_lat_real_analysis_registration.json"
)

_DEFAULT_OUTPUT_DIR = str(
    _REPO_ROOT
    / "commons_sentience_sim"
    / "output"
    / "reality_audit"
    / "fermi_lat_real_blinded_run"
)


# ---------------------------------------------------------------------------
# Blinding helper
# ---------------------------------------------------------------------------

def _blind_result(result: dict) -> dict:
    """Return a copy of the pipeline result with signal keys replaced."""
    blinded = dict(result)
    for key in _SIGNAL_KEYS:
        if key in blinded:
            blinded[key] = "BLINDED"
    # Also blind inside recovery_test if present
    rt = blinded.get("recovery_test", {})
    if rt:
        blinded["recovery_test"] = {
            k: ("BLINDED" if k in ("p_value", "recovered") else v)
            for k, v in rt.items()
        }
    return blinded


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class BlindedRunError(RuntimeError):
    """Raised when a pre-condition for the blinded run is not met."""


def run_fermi_lat_real_blinded(
    source_file: str,
    registration_path: str = _DEFAULT_REGISTRATION,
    ingest_manifest_path: str | None = None,
    output_dir: str = _DEFAULT_OUTPUT_DIR,
    n_permutations: int = 500,
    seed: int = 42,
    run_recovery_test: bool = True,
    recovery_true_slope: float = 5e-4,
    energy_unit: str = "GeV",
    time_unit: str = "s",
    dry_run_ingest: bool = False,
) -> dict:
    """
    Run the Fermi-LAT timing-delay analysis in blinded mode.

    Parameters
    ----------
    source_file    : path to the local public data file (CSV / JSON / NDJSON).
    registration_path : path to the frozen registration JSON.
    ingest_manifest_path : path to the ingest manifest JSON;
                           if None, the manifest written by ingest_public_file
                           within this run is used.
    output_dir     : where to write blinded_summary, run_manifest, qc_report.
    n_permutations : number of energy-permutation trials for null distribution.
    seed           : RNG seed for reproducibility.
    run_recovery_test : perform signal-injection recovery test.
    recovery_true_slope : slope used in recovery test.
    energy_unit    : energy unit of source_file ("GeV", "MeV", ...).
    time_unit      : time unit ("s" or "MJD").
    dry_run_ingest : pass through IngestConfig.dry_run (relaxes thresholds).

    Returns
    -------
    dict with keys:
        blinded_summary_path    — path to blinded_summary.json
        run_manifest_path       — path to run_manifest.json
        qc_report_path          — path to quality_control_report.json
        ingest_complete         — bool from ingest step
        stop_reasons            — list of stopping-rule names (empty = OK)
        blinded_summary         — the blinded result dict
        run_ok                  — bool: True if analysis ran (not blocked)

    Raises
    ------
    BlindedRunError
        If registration or ingest manifest are missing / invalid.
    IngestError
        If ingest is blocked and dry_run_ingest is False.
    """
    out_dir = pathlib.Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 1. Load and verify registration
    # ------------------------------------------------------------------
    try:
        registration = load_registration(registration_path)
    except FileNotFoundError as exc:
        raise BlindedRunError(
            f"Registration file required before blinded run: {exc}"
        ) from exc

    if not registration.get("frozen"):
        raise BlindedRunError(
            "Registration is not marked frozen=True. "
            "Re-run register_fermi_lat_real_analysis.py and commit the output."
        )

    # ------------------------------------------------------------------
    # 2. Ingest the data file
    # ------------------------------------------------------------------
    ingest_cfg = IngestConfig(
        source_file=source_file,
        energy_unit=energy_unit,
        time_unit=time_unit,
        experiment_name=registration.get("experiment_name", "fermi_lat_real_v1"),
        output_dir=str(out_dir),
        dry_run=dry_run_ingest,
        min_total_events=registration.get("minimum_total_events", 20),
        min_sources_with_redshift=registration.get("minimum_grbs_for_analysis", 3),
    )

    ingest_result = ingest_public_file(ingest_cfg)
    ingest_manifest = ingest_result["manifest"]
    actual_manifest_path = ingest_result["manifest_path"]
    stopped = ingest_result["stopped"]
    stop_reasons = ingest_result["stop_reasons"]

    # ------------------------------------------------------------------
    # 3. QC report
    # ------------------------------------------------------------------
    qc_report = {
        "source_file": source_file,
        "registration_experiment": registration.get("experiment_name"),
        "n_events": ingest_manifest.get("n_events_after_qc", 0),
        "n_sources": ingest_manifest.get("n_sources_after_qc", 0),
        "n_dropped_by_adapter": ingest_manifest.get("n_dropped_by_adapter", 0),
        "n_warnings": ingest_manifest.get("n_warnings", 0),
        "warnings": ingest_manifest.get("warnings", []),
        "stopping_rules_triggered": stop_reasons,
        "ingest_complete": not stopped,
        "proceed_to_analysis": not stopped,
    }
    qc_path = out_dir / "quality_control_report.json"
    with open(qc_path, "w") as f:
        json.dump(qc_report, f, indent=2)

    if stopped:
        # Write a blocking run_manifest and stop safely
        run_manifest = {
            "status": "BLOCKED",
            "reason": f"Stopping rules triggered: {stop_reasons}",
            "registration_path": registration_path,
            "ingest_manifest_path": actual_manifest_path,
            "qc_report_path": str(qc_path),
            "analysis_ran": False,
            "unblind_status": "NOT_APPLICABLE",
        }
        run_manifest_path = out_dir / "run_manifest.json"
        with open(run_manifest_path, "w") as f:
            json.dump(run_manifest, f, indent=2)

        blinded_summary = {
            "status": "BLOCKED",
            "reason": f"Analysis blocked by QC stopping rules: {stop_reasons}",
            "blinded": True,
            "unblind_permitted": False,
        }
        blinded_path = out_dir / "blinded_summary.json"
        with open(blinded_path, "w") as f:
            json.dump(blinded_summary, f, indent=2)

        return {
            "blinded_summary_path": str(blinded_path),
            "run_manifest_path": str(run_manifest_path),
            "qc_report_path": str(qc_path),
            "ingest_complete": False,
            "stop_reasons": stop_reasons,
            "blinded_summary": blinded_summary,
            "run_ok": False,
        }

    # ------------------------------------------------------------------
    # 4. Run pipeline (blinded)
    # ------------------------------------------------------------------
    events = ingest_result["pipeline_fmt"]

    pipeline_result = run_real_timing_pipeline(
        events=events,
        experiment_name=registration.get("experiment_name", "fermi_lat_real_v1"),
        n_permutations=n_permutations,
        seed=seed,
        output_dir=str(out_dir),
        run_recovery_test=run_recovery_test,
        recovery_true_slope=recovery_true_slope,
        freeze_immediately=False,    # NEVER auto-unblind
    )

    # ------------------------------------------------------------------
    # 5. Blind the result
    # ------------------------------------------------------------------
    blinded = _blind_result(pipeline_result)

    blinded_summary = {
        "status": "BLINDED",
        "experiment": registration.get("experiment_name"),
        "n_events_analysed": events.get("n_events", 0),
        "n_sources_analysed": events.get("n_sources", 0),
        "blinded": True,
        "unblind_permitted": False,
        "unblind_requires": registration.get("blinding_policy", {}).get(
            "unblind_requires", []
        ),
        "signal_keys_blinded": list(_SIGNAL_KEYS),
        **{k: v for k, v in blinded.items()
           if k not in ("null_distribution", "_raw_pipeline_result")},
        "note": (
            "Signal values (p_value, z_score, observed_slope, "
            "detection_claimed, null_retained) have been replaced with "
            "'BLINDED'.  Unblinding requires explicit human approval after "
            "all QC gates pass."
        ),
    }
    blinded_path = out_dir / "blinded_summary.json"
    with open(blinded_path, "w") as f:
        json.dump(blinded_summary, f, indent=2)

    # ------------------------------------------------------------------
    # 6. Run manifest
    # ------------------------------------------------------------------
    run_manifest = {
        "status": "OK",
        "experiment": registration.get("experiment_name"),
        "registration_path": registration_path,
        "ingest_manifest_path": actual_manifest_path,
        "qc_report_path": str(qc_path),
        "blinded_summary_path": str(blinded_path),
        "n_permutations": n_permutations,
        "seed": seed,
        "analysis_ran": True,
        "unblind_status": "BLINDED — awaiting human approval",
        "automatic_unblind": False,
    }
    run_manifest_path = out_dir / "run_manifest.json"
    with open(run_manifest_path, "w") as f:
        json.dump(run_manifest, f, indent=2)

    return {
        "blinded_summary_path": str(blinded_path),
        "run_manifest_path": str(run_manifest_path),
        "qc_report_path": str(qc_path),
        "ingest_complete": True,
        "stop_reasons": [],
        "blinded_summary": blinded_summary,
        "run_ok": True,
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Run Fermi-LAT GRB timing-delay analysis in blinded mode."
    )
    parser.add_argument("--source", required=True, help="Path to local data file.")
    parser.add_argument(
        "--registration", default=_DEFAULT_REGISTRATION,
        help="Path to frozen registration JSON.",
    )
    parser.add_argument("--output", default=_DEFAULT_OUTPUT_DIR, help="Output directory.")
    parser.add_argument("--n-permutations", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--energy-unit", default="GeV")
    parser.add_argument("--time-unit", default="s")
    parser.add_argument("--dry-run-ingest", action="store_true")
    args = parser.parse_args()

    result = run_fermi_lat_real_blinded(
        source_file=args.source,
        registration_path=args.registration,
        output_dir=args.output,
        n_permutations=args.n_permutations,
        seed=args.seed,
        energy_unit=args.energy_unit,
        time_unit=args.time_unit,
        dry_run_ingest=args.dry_run_ingest,
    )
    print(f"run_ok            : {result['run_ok']}")
    print(f"ingest_complete   : {result['ingest_complete']}")
    print(f"stop_reasons      : {result['stop_reasons']}")
    print(f"blinded_summary   : {result['blinded_summary_path']}")
    print(f"run_manifest      : {result['run_manifest_path']}")
    print(f"qc_report         : {result['qc_report_path']}")
