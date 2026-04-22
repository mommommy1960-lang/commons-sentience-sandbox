"""
run_stage14_confirmatory_reruns.py
===================================
Stage 14 – Run all three target catalogs (Fermi, Swift, IceCube) in
``preregistered_confirmatory`` mode using the locked preregistration plan.

This script resolves the three Stage 13 publication-gate failures:
  • ``prereg_present``   – plan metadata embedded in run output
  • ``prereg_locked``    – plan's ``_locked`` flag must be True
  • ``trial_correction_applied`` – Holm correction applied over two primary stats

Outputs are written to ``outputs/stage14_confirmatory/<catalog>/``.

Usage
-----
python reality_audit/data_analysis/run_stage14_confirmatory_reruns.py
python reality_audit/data_analysis/run_stage14_confirmatory_reruns.py \\
    --null-repeats 500 --axis-count 192 --seed 42

Run from repo root.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Dict, Any, Optional

_HERE      = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from reality_audit.data_analysis.run_stage8_first_results import main as _stage8_main

# ---------------------------------------------------------------------------
# Catalog specifications (from locked preregistration plan)
# ---------------------------------------------------------------------------

CATALOG_SPECS = [
    {
        "label": "fermi",
        "input": "data/real/fermi_lat_grb_catalog.csv",
        "null_mode": "exposure_corrected",
        "name": "stage14_confirmatory_fermi",
        "output_subdir": "fermi",
    },
    {
        "label": "swift",
        "input": "data/real/swift_bat3_grb_catalog.csv",
        "null_mode": "exposure_corrected",
        "name": "stage14_confirmatory_swift",
        "output_subdir": "swift",
    },
    {
        "label": "icecube",
        "input": "data/real/icecube_hese_events.csv",
        "null_mode": "isotropic",
        "name": "stage14_confirmatory_icecube",
        "output_subdir": "icecube",
    },
]

DEFAULT_PLAN_PATH = os.path.join(_REPO_ROOT, "configs", "preregistered_anisotropy_plan.json")
DEFAULT_OUTPUT_BASE = os.path.join(_REPO_ROOT, "outputs", "stage14_confirmatory")
DEFAULT_NULL_REPEATS = 500
DEFAULT_AXIS_COUNT   = 192
DEFAULT_SEED         = 42


# ---------------------------------------------------------------------------
# Core runner
# ---------------------------------------------------------------------------

def run_confirmatory_catalog(
    spec: Dict[str, Any],
    plan_path: str,
    output_base: str,
    null_repeats: int,
    axis_count: int,
    seed: int,
    plots: bool = False,
) -> Dict[str, Any]:
    """Run one catalog in preregistered_confirmatory mode.

    Parameters
    ----------
    spec        : One entry from CATALOG_SPECS.
    plan_path   : Path to the locked preregistration plan JSON.
    output_base : Root directory; outputs go to ``output_base/spec['output_subdir']``.
    null_repeats, axis_count, seed : Numerical parameters.
    plots       : Whether to write PNG plots.

    Returns
    -------
    dict with keys: label, output_dir, summary_path, rc
    """
    output_dir = os.path.join(output_base, spec["output_subdir"])
    os.makedirs(output_dir, exist_ok=True)

    argv = [
        "--input", os.path.join(_REPO_ROOT, spec["input"]),
        "--name", spec["name"],
        "--output-dir", output_dir,
        "--null-mode", spec["null_mode"],
        "--null-repeats", str(null_repeats),
        "--axis-count", str(axis_count),
        "--seed", str(seed),
        "--preregistration-plan", plan_path,
        "--run-mode", "preregistered_confirmatory",
    ]
    if plots:
        argv.append("--plots")

    print(f"\n{'='*62}")
    print(f"  Stage 14 – confirmatory run: {spec['label'].upper()}")
    print(f"  null_repeats={null_repeats}  axis_count={axis_count}  seed={seed}")
    print(f"  null_mode={spec['null_mode']}")
    print(f"  output → {output_dir}")
    print(f"{'='*62}")

    t0 = time.time()
    rc = _stage8_main(argv)
    elapsed = time.time() - t0

    print(f"\n[Stage 14] {spec['label']} finished in {elapsed:.1f}s (rc={rc})")

    # Locate summary JSON written by Stage 8 runner
    summary_path = _find_summary_json(output_dir, spec["name"])

    return {
        "label":       spec["label"],
        "output_dir":  output_dir,
        "summary_path": summary_path,
        "exposure":    _extract_exposure_metadata(summary_path),
        "rc":          rc,
        "elapsed_s":   round(elapsed, 1),
    }


def _find_summary_json(output_dir: str, name: str) -> Optional[str]:
    """Return path to the first *_summary.json in output_dir, or None."""
    if not os.path.isdir(output_dir):
        return None
    for fname in sorted(os.listdir(output_dir)):
        if fname.endswith("_summary.json"):
            return os.path.join(output_dir, fname)
    return None


def _extract_exposure_metadata(summary_path: Optional[str]) -> Dict[str, Any]:
    """Extract null/exposure metadata from a Stage 8 summary JSON."""
    if not summary_path or not os.path.isfile(summary_path):
        return {
            "null_mode": None,
            "exposure_model": None,
            "exposure_map_desc": None,
        }
    try:
        with open(summary_path) as fh:
            payload = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {
            "null_mode": None,
            "exposure_model": None,
            "exposure_map_desc": None,
        }

    results = payload.get("results", {})
    rm = results.get("run_metadata", {})
    nc = results.get("null_comparison", {})
    return {
        "null_mode": nc.get("null_mode", rm.get("null_mode")),
        "exposure_model": rm.get("exposure_model"),
        "exposure_map_desc": rm.get("exposure_map_desc"),
    }


def run_all_confirmatory(
    plan_path: str = DEFAULT_PLAN_PATH,
    output_base: str = DEFAULT_OUTPUT_BASE,
    null_repeats: int = DEFAULT_NULL_REPEATS,
    axis_count: int   = DEFAULT_AXIS_COUNT,
    seed: int         = DEFAULT_SEED,
    plots: bool       = False,
) -> Dict[str, Any]:
    """Run all three catalogs in confirmatory mode and write a manifest.

    Returns a manifest dict describing what was produced.
    """
    from reality_audit.data_analysis.preregistration import (
        load_preregistration_plan,
        validate_preregistration_plan,
    )

    # --- Validate plan is locked ---
    plan = load_preregistration_plan(plan_path)
    issues = validate_preregistration_plan(plan)
    if issues:
        raise RuntimeError(f"Preregistration plan validation failed: {issues}")
    if not plan.get("_locked"):
        raise RuntimeError(
            "Preregistration plan is not locked.  "
            "Set '_locked': true before running confirmatory analysis."
        )

    os.makedirs(output_base, exist_ok=True)

    results = []
    for spec in CATALOG_SPECS:
        result = run_confirmatory_catalog(
            spec=spec,
            plan_path=plan_path,
            output_base=output_base,
            null_repeats=null_repeats,
            axis_count=axis_count,
            seed=seed,
            plots=plots,
        )
        results.append(result)

    # Write manifest
    manifest = {
        "stage": 14,
        "pipeline_step": "confirmatory_reruns",
        "plan_path": plan_path,
        "plan_hash_sha256": plan.get("preregistration_metadata", {}).get("plan_hash_sha256"),
        "null_repeats": null_repeats,
        "axis_count": axis_count,
        "seed": seed,
        "output_base": output_base,
        "catalogs": results,
        "all_succeeded": all(r["rc"] == 0 for r in results),
    }
    manifest_path = os.path.join(output_base, "stage14_confirmatory_reruns_manifest.json")
    with open(manifest_path, "w") as fh:
        json.dump(manifest, fh, indent=2)
        fh.write("\n")

    print(f"\n[Stage 14] Manifest written: {manifest_path}")
    return manifest


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Stage 14: run all three catalogs in preregistered_confirmatory mode.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--preregistration-plan",
        default=DEFAULT_PLAN_PATH,
        metavar="PATH",
        dest="plan_path",
        help=f"Path to locked plan JSON (default: {DEFAULT_PLAN_PATH})",
    )
    p.add_argument(
        "--output-base",
        default=DEFAULT_OUTPUT_BASE,
        metavar="DIR",
        dest="output_base",
        help=f"Base output directory (default: {DEFAULT_OUTPUT_BASE})",
    )
    p.add_argument(
        "--null-repeats",
        type=int,
        default=DEFAULT_NULL_REPEATS,
        metavar="N",
        help=f"Null draws per catalog (default: {DEFAULT_NULL_REPEATS})",
    )
    p.add_argument(
        "--axis-count",
        type=int,
        default=DEFAULT_AXIS_COUNT,
        metavar="N",
        help=f"Preferred-axis grid count (default: {DEFAULT_AXIS_COUNT})",
    )
    p.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        metavar="INT",
        help=f"RNG seed (default: {DEFAULT_SEED})",
    )
    p.add_argument(
        "--plots",
        action="store_true",
        help="Generate PNG plots for each catalog.",
    )
    return p


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)

    try:
        manifest = run_all_confirmatory(
            plan_path=args.plan_path,
            output_base=args.output_base,
            null_repeats=args.null_repeats,
            axis_count=args.axis_count,
            seed=args.seed,
            plots=args.plots,
        )
    except RuntimeError as exc:
        print(f"[ERROR] {exc}")
        return 1

    print()
    print("=" * 62)
    print("  STAGE 14 CONFIRMATORY RERUNS COMPLETE")
    print("=" * 62)
    for r in manifest["catalogs"]:
        status = "OK" if r["rc"] == 0 else f"FAILED (rc={r['rc']})"
        print(f"  {r['label']:<12} {status:<20} {r.get('elapsed_s', '?')}s")
    print(f"\n  all_succeeded : {manifest['all_succeeded']}")
    print(f"  manifest      : {os.path.join(args.output_base, 'stage14_confirmatory_reruns_manifest.json')}")
    print()

    return 0 if manifest["all_succeeded"] else 1


if __name__ == "__main__":
    sys.exit(main())
