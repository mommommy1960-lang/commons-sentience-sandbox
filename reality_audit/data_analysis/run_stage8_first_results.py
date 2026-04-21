"""
run_stage8_first_results.py
===========================
CLI entrypoint for the Stage 8 first real-catalog results package.

Usage examples
--------------
# Auto-detect a real catalog from data/real/:
python reality_audit/data_analysis/run_stage8_first_results.py --auto-detect

# Auto-detect with full options:
python reality_audit/data_analysis/run_stage8_first_results.py \\
    --auto-detect \\
    --name stage8_real_first_results \\
    --output-dir outputs/stage8_first_results/stage8_real_first_results \\
    --null-repeats 100 --axis-count 48 --seed 42 --plots --save-normalized

# Manual input path:
python reality_audit/data_analysis/run_stage8_first_results.py \\
    --input data/real/fermi_lat_grb_catalog.csv \\
    --name stage8_fermi_lat \\
    --output-dir outputs/stage8_first_results/stage8_fermi_lat \\
    --null-repeats 100 --axis-count 48 --seed 42 --plots --save-normalized
"""

from __future__ import annotations

import argparse
import os
import sys

# Ensure repo root on path when run as a script
_HERE      = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from reality_audit.data_analysis.stage8_first_results import (
    discover_real_catalog,
    run_stage8_first_results,
    build_stage8_status_summary,
    _KNOWN_CATALOG_FILES,
)


def _load_plan_if_given(plan_path):
    """Load a preregistration plan if a path was given; return None otherwise."""
    if not plan_path:
        return None
    try:
        from reality_audit.data_analysis.preregistration import load_preregistration_plan
        return load_preregistration_plan(plan_path)
    except Exception as exc:
        print(f"[WARN] Could not load preregistration plan ({plan_path}): {exc}")
        return None


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Run the Stage 8 first real-catalog results package.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    src = p.add_mutually_exclusive_group()
    src.add_argument(
        "--auto-detect",
        action="store_true",
        help=(
            "Automatically detect a real catalog from data/real/. "
            "Known catalog names are preferred; falls back to any CSV/TSV."
        ),
    )
    src.add_argument(
        "--input",
        metavar="PATH",
        help="Explicit path to the catalog CSV/TSV file.",
    )
    p.add_argument(
        "--output-dir",
        default=None,
        metavar="DIR",
        help=(
            "Directory for all artifacts. "
            "Defaults to outputs/stage8_first_results/<name>."
        ),
    )
    p.add_argument(
        "--name",
        default="stage8_first_results",
        metavar="NAME",
        help="Run name used in output filenames (default: stage8_first_results).",
    )
    p.add_argument(
        "--null-repeats",
        type=int,
        default=100,
        metavar="N",
        help="Number of isotropic null draws (default: 100).",
    )
    p.add_argument(
        "--axis-count",
        type=int,
        default=48,
        metavar="N",
        help="Number of trial axes for preferred-axis scan (default: 48).",
    )
    p.add_argument(
        "--seed",
        type=int,
        default=42,
        metavar="INT",
        help="RNG seed for reproducibility (default: 42).",
    )
    p.add_argument(
        "--plots",
        action="store_true",
        help="Generate PNG plots (requires matplotlib).",
    )
    p.add_argument(
        "--null-mode",
        default=None,
        choices=["isotropic", "exposure_corrected"],
        dest="null_mode",
        metavar="MODE",
        help=(
            "Null model: 'isotropic' (uniform sphere) or "
            "'exposure_corrected' (empirical sky-acceptance proxy). "
            "Default: auto-selected per catalog (Fermi/Swift → 'exposure_corrected', "
            "unknown → 'isotropic')."
        ),
    )
    p.add_argument(
        "--save-normalized",
        action="store_true",
        help="Save a normalised event CSV alongside analysis artifacts.",
    )
    p.add_argument(
        "--preregistration-plan",
        default=None,
        metavar="PATH",
        dest="preregistration_plan",
        help=(
            "Path to a locked preregistration plan JSON file. "
            "When provided, plan metadata is recorded in run output. "
            "See docs/REALITY_AUDIT_PREREGISTRATION_TEMPLATE.md."
        ),
    )
    p.add_argument(
        "--run-mode",
        default="exploratory",
        choices=["exploratory", "preregistered_confirmatory"],
        metavar="MODE",
        dest="run_mode",
        help=(
            "Run discipline label. exploratory = hypothesis-generating. "
            "preregistered_confirmatory = requires preregistration plan and "
            "records plan-match diagnostics in metadata."
        ),
    )
    return p


def _graceful_no_catalog_error() -> int:
    supported = "\n  ".join(k["filename"] for k in _KNOWN_CATALOG_FILES)
    print(
        "\n[ERROR] No real catalog found.\n"
        "\nTo use --auto-detect, place one of the following files in data/real/:\n"
        f"  {supported}\n"
        "\nOr supply an explicit path with --input <path>.\n"
        "\nDownload instructions: data/real/README_public_catalog_ingest.md"
        "\n"
    )
    return 1


def main(argv=None) -> int:
    parser = _build_parser()
    args   = parser.parse_args(argv)

    if not args.auto_detect and not args.input:
        parser.error("Provide either --auto-detect or --input PATH.")

    # Resolve input path
    if args.auto_detect:
        discovery = discover_real_catalog()
        if not discovery["usable"]:
            return _graceful_no_catalog_error()
        input_path    = discovery["detected_path"]
        catalog_label = discovery["detected_catalog_label"]
        print(f"[INFO] Auto-detected catalog: {input_path}")
        print(f"[INFO] Detection method: {discovery['detection_method']}")
    else:
        input_path    = args.input
        catalog_label = os.path.splitext(os.path.basename(input_path))[0]
        if not os.path.isfile(input_path):
            print(f"[ERROR] File not found: {input_path}")
            return 1
        print(f"[INFO] Using manual input: {input_path}")

    # Resolve output directory
    output_dir = args.output_dir
    if output_dir is None:
        output_dir = os.path.join(
            _REPO_ROOT, "outputs", "stage8_first_results", args.name
        )

    print(
        f"[INFO] Starting Stage 8 first-results workflow: "
        f"name={args.name!r}, null_repeats={args.null_repeats}, "
        f"axes={args.axis_count}, seed={args.seed}"
    )

    bundle = run_stage8_first_results(
        input_path=input_path,
        output_dir=output_dir,
        name=args.name,
        null_repeats=args.null_repeats,
        axis_count=args.axis_count,
        seed=args.seed,
        plots=args.plots,
        save_normalized=args.save_normalized,
        null_mode=args.null_mode,
        preregistration_plan=_load_plan_if_given(getattr(args, "preregistration_plan", None)),
        preregistration_plan_path=getattr(args, "preregistration_plan", None),
        run_mode=args.run_mode,
    )

    status = build_stage8_status_summary(bundle)

    # --- Terminal summary ---
    sig    = bundle.get("study_results", {}).get("signal_evaluation", {})
    nc     = bundle.get("study_results", {}).get("null_comparison", {})
    pa     = bundle.get("study_results", {}).get("preferred_axis", {})

    print()
    print("=" * 62)
    print("  STAGE 8 FIRST-RESULTS SUMMARY")
    print("=" * 62)
    print(f"  Catalog          : {bundle.get('catalog_label')}")
    print(f"  Run name         : {args.name}")
    print(f"  Events (total)   : {bundle.get('event_count', 0)}")
    print(
        f"  With position    : {status.get('events_with_position', 'N/A')}"
    )
    print(
        f"  Hemisphere imb.  : "
        f"{bundle['study_results'].get('anisotropy', {}).get('hemisphere_imbalance', 0.0):.4f} "
        f"(pct={nc.get('hemi_percentile', 0.0):.4f})"
    )
    print(
        f"  Preferred-axis   : {pa.get('score', 0.0):.4f} "
        f"({pa.get('num_axes_scanned', '?')} axes, "
        f"pct={nc.get('axis_percentile', 0.0):.4f})"
    )
    print(f"  Signal tier      : {sig.get('tier', 'unknown')}")
    print(f"  Max percentile   : {sig.get('max_percentile', 0.0):.4f}")
    print(f"  Run mode         : {bundle.get('run_metadata', {}).get('run_mode', args.run_mode)}")
    resolved_null_mode = (
        bundle.get("run_metadata", {})
        .get("null_mode", args.null_mode)
    )
    print(f"  Null model       : {resolved_null_mode}")
    print()
    print(f"  Output dir       : {output_dir}")
    print(f"  Memo             : {bundle.get('memo_path')}")
    print(f"  Stage 8 manifest : {bundle.get('stage8_manifest_path')}")
    print("=" * 62)
    print()
    print("NOTE: This is an internal first-results package.")
    print("Anomaly-like deviations are hypothesis-generating results,")
    print("not evidence for any physical or metaphysical claim.")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
