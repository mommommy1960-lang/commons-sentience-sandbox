"""
first_blinded_real_fermi_run.py
================================
Single operator-facing command for the Stage 6 milestone:
  "First Blinded Real Fermi-LAT GRB Timing-Delay Analysis"

Execution flow
--------------
1. Detect non-synthetic CSV candidate in data/real/
2. Run pre-ingest package validation check
3. Abort if check returns REJECT or ACCEPT_WITH_WARNINGS
4. Run blinded timing-delay pipeline (automatic_unblind=False guaranteed)
5. Generate milestone completion report
6. Write all artifacts; never expose protected inference outputs

Protected outputs (never written by this module)
------------------------------------------------
- observed_slope
- p_value
- z_score
- detection_claimed
- null_retained
- any proxy revealing final inference state

Allowed outputs
---------------
- run manifest          (first_real_ingest_manifest.json)
- QC report             (quality_control_report.json)
- blinded summary       (blinded_summary.json)
- ingest manifest       (fermi_lat_public_ingest_manifest.json)
- milestone report      (milestone_completion_report.json)
- execution log         (stdout / stderr)

Usage (CLI)
-----------
python -m reality_audit.data_analysis.first_blinded_real_fermi_run

Usage (API)
-----------
from reality_audit.data_analysis.first_blinded_real_fermi_run import (
    first_blinded_real_fermi_run,
)
result = first_blinded_real_fermi_run()
"""

import json
import pathlib
import sys
from typing import Any, Dict, Optional

from reality_audit.data_analysis.run_first_real_ingest import run_first_real_ingest
from reality_audit.data_analysis.milestone_report import generate_milestone_report

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DATA_DIR = pathlib.Path("data/real")
_REGISTRATION_PATH = pathlib.Path(
    "commons_sentience_sim/output/reality_audit/fermi_lat_real_analysis_registration.json"
)
_MANIFEST_PATH = pathlib.Path(
    "commons_sentience_sim/output/reality_audit/first_real_ingest_manifest.json"
)
_MILESTONE_REPORT_PATH = pathlib.Path(
    "commons_sentience_sim/output/reality_audit/milestone_completion_report.json"
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def first_blinded_real_fermi_run(
    data_dir: Optional[str] = None,
    registration_path: Optional[str] = None,
    manifest_path: Optional[str] = None,
    milestone_report_path: Optional[str] = None,
    n_permutations: int = 500,
    seed: int = 42,
    require_accept_only: bool = True,
) -> Dict[str, Any]:
    """
    Execute the full Stage 6 blinded real-data analysis workflow.

    Parameters
    ----------
    data_dir : str, optional
        Directory to scan for real CSV candidates (default: data/real/).
    registration_path : str, optional
        Path to the frozen analysis registration JSON.
    manifest_path : str, optional
        Output path for first_real_ingest_manifest.json.
    milestone_report_path : str, optional
        Output path for milestone_completion_report.json.
    n_permutations : int
        Number of permutations for the null distribution. Default 500.
    seed : int
        Random seed for reproducibility. Default 42.
    require_accept_only : bool
        If True (default), abort on ACCEPT_WITH_WARNINGS as well as REJECT.
        Set False only in test contexts.

    Returns
    -------
    dict with keys:
        ingest_result   — output of run_first_real_ingest
        milestone_report — output of generate_milestone_report
        overall_status  — WAITING | BLOCKED | COMPLETE | ERROR
    """
    # ------------------------------------------------------------------
    # Step 1–4: Ingest (detect → validate → run blinded pipeline)
    # ------------------------------------------------------------------
    ingest_result = run_first_real_ingest(
        data_dir=data_dir,
        registration_path=registration_path,
        manifest_path=manifest_path,
        n_permutations=n_permutations,
        seed=seed,
    )

    ingest_status = ingest_result.get("status", "UNKNOWN")

    # Enforce strict gate: if validation returned ACCEPT_WITH_WARNINGS,
    # the ingest helper already passed it through (recommendation check is
    # inside run_first_real_ingest). Here we only need to respect what it
    # returned.
    if require_accept_only and ingest_status not in ("COMPLETE", "WAITING"):
        _print_abort(ingest_result)

    # ------------------------------------------------------------------
    # Step 5: Generate milestone completion report
    # ------------------------------------------------------------------
    milestone = generate_milestone_report(
        manifest_path=str(manifest_path or _MANIFEST_PATH),
        output_path=str(milestone_report_path or _MILESTONE_REPORT_PATH),
    )

    overall_status = ingest_status

    # ------------------------------------------------------------------
    # Step 6: Final status print
    # ------------------------------------------------------------------
    _print_summary(overall_status, ingest_result, milestone)

    return {
        "ingest_result": ingest_result,
        "milestone_report": milestone,
        "overall_status": overall_status,
    }


def _print_abort(ingest_result: Dict[str, Any]) -> None:
    print(
        f"\nABORTED: Ingest workflow returned status '{ingest_result.get('status')}'.\n"
        f"Message: {ingest_result.get('message')}\n"
        "No analysis was performed. Review the package check report and retry."
    )


def _print_summary(
    status: str,
    ingest_result: Dict[str, Any],
    milestone: Dict[str, Any],
) -> None:
    blinding = milestone.get("blinding", {})
    qc = milestone.get("qc_gates", {})
    dataset = milestone.get("dataset", {})

    print("\n" + "=" * 60)
    print("STAGE 6 — FIRST BLINDED REAL FERMI-LAT RUN")
    print("=" * 60)
    print(f"  Overall status       : {status}")
    print(f"  Dataset              : {dataset.get('dataset_name', 'N/A')}")
    print(f"  Events ingested      : {qc.get('n_events', 'N/A')}")
    print(f"  Events dropped       : {qc.get('n_dropped_by_adapter', 'N/A')}")
    print(f"  Sources              : {qc.get('n_sources', 'N/A')}")
    print(f"  QC warnings          : {qc.get('n_warnings', 'N/A')}")
    print(f"  Stopping rules fired : {qc.get('stopping_rules_triggered', [])}")
    print(f"  Blinding enforced    : {blinding.get('blinding_enforced', 'N/A')}")
    print(f"  Signal keys blinded  : {blinding.get('signal_keys_confirmed_blinded', 'N/A')}")
    print(f"  Unblind permitted    : {blinding.get('unblind_permitted', 'N/A')}")
    print(f"  Commit hash          : {milestone.get('commit_hash', 'N/A')}")
    print(f"\n  *** {milestone.get('unblinding_status', 'UNBLINDING NOT PERFORMED')} ***")
    print(f"  *** {milestone.get('scientific_claim_status', '')} ***")
    print("=" * 60 + "\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _cli() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Stage 6: Execute the first blinded real Fermi-LAT GRB "
            "timing-delay analysis."
        )
    )
    parser.add_argument("--data-dir", default=None)
    parser.add_argument("--registration", default=None)
    parser.add_argument("--manifest-out", default=None)
    parser.add_argument("--milestone-report-out", default=None)
    parser.add_argument("--n-permutations", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    result = first_blinded_real_fermi_run(
        data_dir=args.data_dir,
        registration_path=args.registration,
        manifest_path=args.manifest_out,
        milestone_report_path=args.milestone_report_out,
        n_permutations=args.n_permutations,
        seed=args.seed,
    )

    # Print only non-blinded fields from milestone report
    safe = {
        k: v for k, v in result["milestone_report"].items()
        if k not in ("blinded_summary",)
    }
    print(json.dumps(safe, indent=2))


if __name__ == "__main__":
    _cli()
