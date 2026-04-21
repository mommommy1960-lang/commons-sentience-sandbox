"""
run_stage10_catalog_comparison.py
==================================
CLI for the Stage 10 cross-catalog comparison of two real anisotropy results.

Usage
-----
Run with default paths (Fermi Stage 9 and Swift Stage 10):
    python reality_audit/data_analysis/run_stage10_catalog_comparison.py

Run with explicit summary JSON paths:
    python reality_audit/data_analysis/run_stage10_catalog_comparison.py \\
        --summary-a outputs/stage9_first_results/stage9_fermi_exposure_corrected/stage9_fermi_exposure_corrected_summary.json \\
        --summary-b outputs/stage10_first_results/stage10_swift_first_results/stage10_swift_first_results_summary.json \\
        --output-dir outputs/stage10_first_results/comparison \\
        --name stage10_catalog_comparison
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_HERE      = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from reality_audit.data_analysis.catalog_comparison import (
    load_stage_results,
    compare_catalog_results,
    compare_three_catalog_results,
    load_icecube_diagnostics_summary,
    integrate_icecube_robustness_into_three_catalog,
    write_catalog_comparison_memo,
    write_three_catalog_comparison_memo,
)

# Default summary JSON locations (relative to repo root)
_DEFAULT_SUMMARY_A = os.path.join(
    "outputs", "stage9_first_results",
    "stage9_fermi_exposure_corrected",
    "stage9_fermi_exposure_corrected_summary.json",
)
_DEFAULT_SUMMARY_B = os.path.join(
    "outputs", "stage10_first_results",
    "stage10_swift_first_results",
    "stage10_swift_first_results_summary.json",
)
_DEFAULT_OUTPUT_DIR  = os.path.join("outputs", "stage10_first_results", "comparison")
_DEFAULT_OUTPUT_NAME = "stage10_catalog_comparison"
_DEFAULT_SUMMARY_C = os.path.join(
    "outputs", "stage8_first_results",
    "stage11_icecube_first_results",
    "stage11_icecube_first_results_summary.json",
)
_DEFAULT_ICECUBE_DIAGNOSTICS = os.path.join(
    "outputs", "stage12_icecube_diagnostics",
    "stage12_icecube_diagnostics",
    "stage12_icecube_diagnostics_summary.json",
)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Stage 10: Compare anisotropy results from two real catalogs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--summary-a",
        default=None,
        metavar="PATH",
        help=(
            f"Path to the first catalog summary JSON. "
            f"Default: {_DEFAULT_SUMMARY_A}"
        ),
    )
    p.add_argument(
        "--summary-b",
        default=None,
        metavar="PATH",
        help=(
            f"Path to the second catalog summary JSON. "
            f"Default: {_DEFAULT_SUMMARY_B}"
        ),
    )
    p.add_argument(
        "--summary-c",
        default=None,
        metavar="PATH",
        help=(
            f"Optional third catalog summary JSON (Stage 11). "
            f"Default: {_DEFAULT_SUMMARY_C} if file exists."
        ),
    )
    p.add_argument(
        "--require-three",
        action="store_true",
        help=(
            "Require three-catalog comparison. If true and summary C is missing, fail."
        ),
    )
    p.add_argument(
        "--icecube-diagnostics",
        default=None,
        metavar="PATH",
        help=(
            "Optional Stage 12 IceCube diagnostics summary JSON. "
            f"Default candidate: {_DEFAULT_ICECUBE_DIAGNOSTICS}"
        ),
    )
    p.add_argument(
        "--output-dir",
        default=None,
        metavar="DIR",
        help=f"Output directory. Default: {_DEFAULT_OUTPUT_DIR}",
    )
    p.add_argument(
        "--name",
        default=_DEFAULT_OUTPUT_NAME,
        metavar="NAME",
        help=f"Base name for output files. Default: {_DEFAULT_OUTPUT_NAME}",
    )
    return p


def main(argv=None) -> int:
    parser = _build_parser()
    args   = parser.parse_args(argv)

    # Resolve paths relative to repo root when relative
    def _abs(p: str) -> str:
        if os.path.isabs(p):
            return p
        return os.path.join(_REPO_ROOT, p)

    path_a      = _abs(args.summary_a or _DEFAULT_SUMMARY_A)
    path_b      = _abs(args.summary_b or _DEFAULT_SUMMARY_B)
    c_candidate = args.summary_c or _DEFAULT_SUMMARY_C
    path_c      = _abs(c_candidate) if c_candidate else None
    diag_candidate = args.icecube_diagnostics or _DEFAULT_ICECUBE_DIAGNOSTICS
    diag_path = _abs(diag_candidate) if diag_candidate else None
    output_dir  = _abs(args.output_dir or _DEFAULT_OUTPUT_DIR)

    # Check prerequisites
    missing = []
    if not os.path.isfile(path_a):
        missing.append(("Catalog A summary", path_a))
    if not os.path.isfile(path_b):
        missing.append(("Catalog B summary", path_b))
    has_c = bool(path_c and os.path.isfile(path_c))
    if args.require_three and not has_c:
        missing.append(("Catalog C summary", path_c or _DEFAULT_SUMMARY_C))

    if missing:
        print("\n[ERROR] Missing prerequisite files for Stage 10 comparison:")
        for label, p in missing:
            print(f"  {label}: {p}")
        print()
        print("To generate the missing summaries, run:")
        if not os.path.isfile(path_a):
            print(
                "  python reality_audit/data_analysis/run_stage8_first_results.py \\\n"
                "    --input data/real/fermi_lat_grb_catalog.csv \\\n"
                "    --name stage9_fermi_exposure_corrected \\\n"
                "    --output-dir outputs/stage9_first_results/stage9_fermi_exposure_corrected \\\n"
                "    --null-mode exposure_corrected --null-repeats 100 --axis-count 48 --seed 42"
            )
        if not os.path.isfile(path_b):
            print(
                "  python reality_audit/data_analysis/run_stage8_first_results.py \\\n"
                "    --input data/real/swift_bat3_grb_catalog.csv \\\n"
                "    --name stage10_swift_first_results \\\n"
                "    --output-dir outputs/stage10_first_results/stage10_swift_first_results \\\n"
                "    --null-mode exposure_corrected --null-repeats 100 --axis-count 48 --seed 42"
            )
        if args.require_three and not has_c:
            print(
                "  python reality_audit/data_analysis/run_stage8_first_results.py \\\n"
                "    --input data/real/icecube_hese_events.csv \\\n"
                "    --name stage11_icecube_first_results \\\n"
                "    --output-dir outputs/stage8_first_results/stage11_icecube_first_results \\\n"
                "    --null-mode isotropic --null-repeats 100 --axis-count 48 --seed 42"
            )
        return 1

    # Load results
    print(f"[INFO] Loading catalog A: {path_a}")
    result_a = load_stage_results(path_a)
    print(
        f"[INFO]   {result_a['catalog']} | N={result_a['event_count']} | "
        f"null={result_a['null_mode']} | tier={result_a['tier']}"
    )

    print(f"[INFO] Loading catalog B: {path_b}")
    result_b = load_stage_results(path_b)
    print(
        f"[INFO]   {result_b['catalog']} | N={result_b['event_count']} | "
        f"null={result_b['null_mode']} | tier={result_b['tier']}"
    )

    result_c = None
    if has_c:
        print(f"[INFO] Loading catalog C: {path_c}")
        result_c = load_stage_results(path_c)
        print(
            f"[INFO]   {result_c['catalog']} | N={result_c['event_count']} | "
            f"null={result_c['null_mode']} | tier={result_c['tier']}"
        )

    # Compare
    if result_c is not None:
        comparison = compare_three_catalog_results(result_a, result_b, result_c)
        if diag_path and os.path.isfile(diag_path):
            diag = load_icecube_diagnostics_summary(diag_path)
            comparison = integrate_icecube_robustness_into_three_catalog(comparison, diag)
            print(
                f"[INFO] Integrated IceCube robustness diagnostics: "
                f"label={comparison.get('icecube_robustness', {}).get('label')}"
            )
        memo_path = write_three_catalog_comparison_memo(comparison, output_dir, name=args.name)
    else:
        comparison = compare_catalog_results(result_a, result_b)
        memo_path = write_catalog_comparison_memo(comparison, output_dir, name=args.name)
    json_path = os.path.join(output_dir, f"{args.name}.json")

    # Terminal summary
    print()
    print("=" * 62)
    if result_c is not None:
        print("  STAGE 11 THREE-CATALOG COMPARISON")
    else:
        print("  STAGE 10 CROSS-CATALOG COMPARISON")
    print("=" * 62)
    if result_c is not None:
        rows = comparison.get("catalog_rows", [])
        for i, row in enumerate(rows):
            label = chr(ord("A") + i)
            print(f"  Catalog {label}        : {row.get('catalog')}")
            print(f"    Events         : {row.get('event_count')}")
            print(f"    Null model     : {row.get('null_mode')}")
            print(f"    Hemi pct       : {row.get('hemi_percentile')}")
            print(f"    Axis pct       : {row.get('axis_percentile')}")
            print(f"    Tier           : {row.get('tier')}")
            if i < len(rows) - 1:
                print()
    else:
        print(f"  Catalog A        : {comparison['catalog_a']}")
        print(f"    Events         : {comparison['event_count_a']}")
        print(f"    Null model     : {comparison['null_mode_a']}")
        print(f"    Hemi pct       : {comparison['hemi_percentile_a']}")
        print(f"    Axis pct       : {comparison['axis_percentile_a']}")
        print(f"    Tier           : {comparison['tier_a']}")
        print()
        print(f"  Catalog B        : {comparison['catalog_b']}")
        print(f"    Events         : {comparison['event_count_b']}")
        print(f"    Null model     : {comparison['null_mode_b']}")
        print(f"    Hemi pct       : {comparison['hemi_percentile_b']}")
        print(f"    Axis pct       : {comparison['axis_percentile_b']}")
        print(f"    Tier           : {comparison['tier_b']}")
    print()
    print(f"  Verdict          : {comparison['consistency_verdict'].upper()}")
    print()
    print(f"  Memo             : {memo_path}")
    print(f"  JSON             : {json_path}")
    print("=" * 62)
    print()
    print(comparison["interpretation"])
    print()
    print("NOTE: This is an internal cross-catalog comparison.")
    print("Results are hypothesis-generating only, not a scientific claim.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
