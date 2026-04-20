"""
run_local_fermi_lat_dry_run.py
==============================
Runs the Fermi-LAT GRB adapter and real timing pipeline end-to-end on the
local sample dataset (data/sample_fermi_lat_grb_events.csv).

This is the FIRST TRUE LOCAL DATA INGEST DRY RUN for Experiment 1.

Usage:
    python reality_audit/data_analysis/run_local_fermi_lat_dry_run.py

Outputs to:
    commons_sentience_sim/output/reality_audit/local_fermi_lat_dry_run/
      config.json
      adapted_events.json
      summary.json
      blinded_summary.json
      unblinded_summary.json

Design notes:
  - Uses freeze_immediately=False (blinded by default), then explicitly unfreezes
    by calling the pipeline a second time with freeze_immediately=True to confirm
    the full protocol works end-to-end.
  - Does NOT claim scientific detection from sample data (synthetic).
  - N_PERMUTATIONS is set to 500 for publication-quality null distribution.
"""

import json
import os
import pathlib
import sys

# Ensure repo root is on path when run directly
_REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from reality_audit.adapters.fermi_lat_grb_adapter import (
    load_grb_events,
    to_timing_pipeline_format,
    load_and_convert,
)
from reality_audit.data_analysis.real_timing_pipeline import run_real_timing_pipeline

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SAMPLE_CSV = _REPO_ROOT / "data" / "sample_fermi_lat_grb_events.csv"
OUTPUT_DIR = _REPO_ROOT / "commons_sentience_sim" / "output" / "reality_audit" / "local_fermi_lat_dry_run"

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

CONFIG = {
    "experiment_name": "local_fermi_lat_dry_run_v1",
    "source_file": str(SAMPLE_CSV),
    "energy_unit": "GeV",
    "time_unit": "s",
    "n_permutations": 500,
    "seed": 42,
    "recovery_true_slope": 5e-4,
    "output_dir": str(OUTPUT_DIR),
    "note": (
        "First true local data ingest dry run. "
        "Sample data is synthetic-but-realistic; no real public FITS data ingested. "
        "Null retained result is expected and correct."
    ),
}


def run_dry_run() -> dict:
    """Execute the full local end-to-end dry run and return summary dict."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Write config
    config_path = OUTPUT_DIR / "config.json"
    with open(config_path, "w") as f:
        json.dump(CONFIG, f, indent=2)
    print(f"[1/5] Config written: {config_path}")

    # 2. Load and adapt sample data (raw adapter output)
    raw_events = load_grb_events(
        str(SAMPLE_CSV),
        energy_unit=CONFIG["energy_unit"],
        time_unit=CONFIG["time_unit"],
    )
    # Convert to pipeline format for use with run_real_timing_pipeline
    events = to_timing_pipeline_format(raw_events)
    print(
        f"[2/5] Adapted: n_events={raw_events['metadata']['n_events']}, "
        f"n_sources={raw_events['metadata']['n_sources']}"
    )

    # 3. Write adapted_events.json (first 10 events + metadata as excerpt)
    adapted_excerpt = {
        "metadata": raw_events["metadata"],
        "events_first_10": raw_events["events"][:10],
        "by_source_names": list(raw_events["by_source"].keys()),
    }
    adapted_path = OUTPUT_DIR / "adapted_events.json"
    with open(adapted_path, "w") as f:
        json.dump(adapted_excerpt, f, indent=2)
    print(f"[3/5] Adapted events excerpt written: {adapted_path}")

    # 4. Blinded run (freeze_immediately=False — signal results hidden)
    print("[4/5] Running blinded pipeline ...")
    blinded_result = run_real_timing_pipeline(
        events,
        experiment_name=CONFIG["experiment_name"],
        n_permutations=CONFIG["n_permutations"],
        seed=CONFIG["seed"],
        output_dir=str(OUTPUT_DIR),
        run_recovery_test=True,
        recovery_true_slope=CONFIG["recovery_true_slope"],
        freeze_immediately=False,   # blinded
    )

    # 5. Unblinded run (freeze_immediately=True — for dry-run validation only)
    print("[5/5] Running unblinded pipeline (dry-run validation) ...")
    unblinded_result = run_real_timing_pipeline(
        events,
        experiment_name=CONFIG["experiment_name"] + "_unblinded",
        n_permutations=CONFIG["n_permutations"],
        seed=CONFIG["seed"],
        output_dir=str(OUTPUT_DIR),
        run_recovery_test=True,
        recovery_true_slope=CONFIG["recovery_true_slope"],
        freeze_immediately=True,    # unblinded for dry-run output
    )

    # Build summary
    summary = {
        "experiment": CONFIG["experiment_name"],
        "source_file": str(SAMPLE_CSV),
        "n_events": raw_events["metadata"]["n_events"],
        "n_sources": raw_events["metadata"]["n_sources"],
        "n_dropped": raw_events["metadata"]["n_dropped"],
        "observed_slope": unblinded_result["observed_slope"],
        "p_value": unblinded_result["p_value"],
        "z_score": unblinded_result["z_score"],
        "null_retained": unblinded_result["null_retained"],
        "detection_claimed": unblinded_result["detection_claimed"],
        "recovery_test": unblinded_result.get("recovery_test", {}),
        "note": CONFIG["note"],
        "statistical_caveat": (
            "CAUTION: sample dataset has only 50 events across 5 GRBs. "
            "Random fluctuations at this scale can produce any p-value. "
            "Any slope or p-value result here is NOT a scientific claim. "
            "This run proves infrastructure works end-to-end only."
        ),
    }

    summary_path = OUTPUT_DIR / "summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print("\n--- DRY RUN SUMMARY ---")
    print(f"  n_events         : {summary['n_events']}")
    print(f"  n_sources        : {summary['n_sources']}")
    print(f"  observed_slope   : {summary['observed_slope']:.4e}  [s / (GeV·Mpc)]")
    print(f"  p_value          : {summary['p_value']:.4f}")
    print(f"  z_score          : {summary['z_score']:.3f}")
    print(f"  null_retained    : {summary['null_retained']}")
    print(f"  detection_claimed: {summary['detection_claimed']}")
    rt = summary["recovery_test"]
    if rt:
        print(f"  recovery p_value : {rt.get('p_value', 'N/A')}")
        print(f"  recovery ok      : {rt.get('recovered', 'N/A')}")
    print(f"\nOutputs: {OUTPUT_DIR}")

    return summary


if __name__ == "__main__":
    run_dry_run()
