"""
milestone_report.py
====================
Generates the Stage 6 milestone completion report for the first blinded
real Fermi-LAT GRB timing-delay analysis run.

The report collects provenance from existing pipeline outputs and assembles
a single structured JSON document suitable for human review before any
unblinding decision is made.

Protected inference outputs (slope, p-value, z-score, detection status) are
never included. The report explicitly records "UNBLINDING NOT PERFORMED".

Output
------
commons_sentience_sim/output/reality_audit/milestone_completion_report.json
"""

import datetime
import json
import pathlib
import subprocess
from typing import Any, Dict, Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_BASE = pathlib.Path("commons_sentience_sim/output/reality_audit")
_MANIFEST_PATH       = _BASE / "first_real_ingest_manifest.json"
_QC_REPORT_PATH      = _BASE / "fermi_lat_real_blinded_run" / "quality_control_report.json"
_BLINDED_SUMMARY_PATH = _BASE / "fermi_lat_real_blinded_run" / "blinded_summary.json"
_INGEST_MANIFEST_PATH = _BASE / "fermi_lat_real_blinded_run" / "fermi_lat_public_ingest_manifest.json"
_DEFAULT_OUTPUT_PATH = _BASE / "milestone_completion_report.json"

_PROTECTED_KEYS = frozenset(
    ["observed_slope", "p_value", "z_score", "detection_claimed", "null_retained"]
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _git_commit_hash() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def _load_json(path: pathlib.Path) -> Optional[Dict[str, Any]]:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return None
    return None


def _qc_gate_summary(qc: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if qc is None:
        return {"available": False}
    return {
        "available": True,
        "n_events": qc.get("n_events"),
        "n_sources": qc.get("n_sources"),
        "n_dropped_by_adapter": qc.get("n_dropped_by_adapter"),
        "n_warnings": qc.get("n_warnings"),
        "stopping_rules_triggered": qc.get("stopping_rules_triggered", []),
        "ingest_complete": qc.get("ingest_complete"),
        "proceed_to_analysis": qc.get("proceed_to_analysis"),
        "source_file": qc.get("source_file"),
    }


def _ingest_summary(ingest: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if ingest is None:
        return {"available": False}
    meta = ingest.get("metadata", {})
    return {
        "available": True,
        "status": ingest.get("status"),
        "n_events": meta.get("n_events"),
        "n_dropped": meta.get("n_dropped"),
        "n_sources": meta.get("n_sources"),
        "n_sources_with_redshift": meta.get("n_sources_with_redshift"),
        "drop_reasons": ingest.get("dropped_events", {}).get("reasons", []),
        "warnings": ingest.get("warnings", []),
    }


def _blinding_status(blinded: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if blinded is None:
        return {"available": False, "blinding_enforced": False}
    # Verify no protected keys leaked
    leaked = [k for k in _PROTECTED_KEYS if blinded.get(k) not in (None, "BLINDED")]
    return {
        "available": True,
        "blinding_enforced": blinded.get("blinded", False),
        "unblind_permitted": blinded.get("unblind_permitted", False),
        "signal_keys_confirmed_blinded": leaked == [],
        "leaked_keys": leaked,
        "unblind_requires": blinded.get("unblind_requires", []),
        "n_events_analysed": blinded.get("n_events_analysed"),
        "n_sources_analysed": blinded.get("n_sources_analysed"),
        "primary_statistic": blinded.get("primary_statistic"),
        "n_permutations": blinded.get("n_permutations"),
        "seed": blinded.get("seed"),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_milestone_report(
    manifest_path: Optional[str] = None,
    qc_report_path: Optional[str] = None,
    blinded_summary_path: Optional[str] = None,
    ingest_manifest_path: Optional[str] = None,
    output_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Assemble the Stage 6 milestone completion report.

    Reads existing pipeline output files; does not re-run the pipeline.
    Protected inference outputs are never included.

    Returns
    -------
    dict — the milestone report (also written to output_path as JSON)
    """
    mfst     = _load_json(pathlib.Path(manifest_path     or _MANIFEST_PATH))
    qc       = _load_json(pathlib.Path(qc_report_path    or _QC_REPORT_PATH))
    blinded  = _load_json(pathlib.Path(blinded_summary_path or _BLINDED_SUMMARY_PATH))
    ingest   = _load_json(pathlib.Path(ingest_manifest_path or _INGEST_MANIFEST_PATH))

    # -----------------------------------------------------------------------
    # Dataset provenance
    # -----------------------------------------------------------------------
    candidate = None
    check_report = None
    if mfst:
        candidate = mfst.get("candidate")
        check_report = mfst.get("check_report")

    dataset_name = pathlib.Path(candidate).name if candidate else "UNKNOWN"

    dataset_section: Dict[str, Any] = {
        "dataset_name": dataset_name,
        "source_path": candidate,
        "pre_ingest_check": {
            "available": check_report is not None,
            "schema_valid": check_report.get("schema_valid") if check_report else None,
            "recommendation": check_report.get("recommendation") if check_report else None,
            "hard_failures": check_report.get("hard_failures", []) if check_report else [],
            "warnings": check_report.get("warnings", []) if check_report else [],
        } if check_report else {"available": False},
    }

    # -----------------------------------------------------------------------
    # Artifact paths
    # -----------------------------------------------------------------------
    artifact_paths = {
        "first_ingest_manifest": str(manifest_path or _MANIFEST_PATH),
        "qc_report": str(qc_report_path or _QC_REPORT_PATH),
        "blinded_summary": str(blinded_summary_path or _BLINDED_SUMMARY_PATH),
        "ingest_manifest": str(ingest_manifest_path or _INGEST_MANIFEST_PATH),
        "milestone_report": str(output_path or _DEFAULT_OUTPUT_PATH),
    }

    # -----------------------------------------------------------------------
    # Assemble report
    # -----------------------------------------------------------------------
    pipeline_status = (mfst.get("status") if mfst else "UNKNOWN") or "UNKNOWN"

    report: Dict[str, Any] = {
        "milestone": "Stage 6 — First Blinded Real Fermi-LAT GRB Timing-Delay Analysis",
        "unblinding_status": "UNBLINDING NOT PERFORMED",
        "scientific_claim_status": "NO SCIENTIFIC CLAIM PERMITTED BEFORE UNBLINDING APPROVAL",
        "run_timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "commit_hash": _git_commit_hash(),
        "pipeline_status": pipeline_status,
        "dataset": dataset_section,
        "ingestion": _ingest_summary(ingest),
        "qc_gates": _qc_gate_summary(qc),
        "blinding": _blinding_status(blinded),
        "artifact_paths": artifact_paths,
    }

    # -----------------------------------------------------------------------
    # Write
    # -----------------------------------------------------------------------
    out = pathlib.Path(output_path or _DEFAULT_OUTPUT_PATH)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2))

    return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _cli() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate the Stage 6 milestone completion report."
    )
    parser.add_argument("--output", default=None, help="Override output JSON path.")
    args = parser.parse_args()

    report = generate_milestone_report(output_path=args.output)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    _cli()
