"""
run_public_anisotropy_study.py
==============================
CLI entrypoint for the Stage 7 public-data anisotropy analysis.

Usage examples
--------------
# Synthetic isotropic baseline (no real data required):
python reality_audit/data_analysis/run_public_anisotropy_study.py \\
    --catalog synthetic_isotropic \\
    --name stage7_synth_baseline \\
    --output-dir outputs/public_anisotropy/synth_baseline \\
    --null-repeats 50 --axis-count 48 --seed 42 --plots

# Synthetic preferred-axis recovery test:
python reality_audit/data_analysis/run_public_anisotropy_study.py \\
    --catalog synthetic_preferred_axis \\
    --name stage7_synth_preferred_axis \\
    --output-dir outputs/public_anisotropy/synth_preferred_axis \\
    --null-repeats 50 --axis-count 48 --seed 42 --plots

# Manual-ingest real catalog:
python reality_audit/data_analysis/run_public_anisotropy_study.py \\
    --input data/real/my_catalog.csv \\
    --name stage7_real_catalog \\
    --output-dir outputs/public_anisotropy/real_catalog \\
    --null-repeats 100 --axis-count 48 --seed 42 --plots --save-normalized
"""

from __future__ import annotations

import argparse
import csv
import os
import sys

# Ensure repo root on path when run as a script
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from reality_audit.data_analysis.public_event_catalogs import (
    load_public_catalog,
    describe_catalog_coverage,
)
from reality_audit.data_analysis.public_anisotropy_study import (
    run_public_anisotropy_study,
    write_public_study_artifacts,
)
from reality_audit.data_analysis.simulation_signature_analysis import standardize_events


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Run the Stage 7 public-data anisotropy study.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    src = p.add_mutually_exclusive_group()
    src.add_argument(
        "--catalog",
        metavar="NAME",
        help=(
            "Built-in catalog name or known alias: "
            "synthetic_isotropic, synthetic_preferred_axis, "
            "fermi_lat_grb, swift_bat3_grb, icecube_hese"
        ),
    )
    src.add_argument(
        "--input",
        metavar="PATH",
        help="Path to a manually placed local CSV/TSV event catalog file.",
    )
    p.add_argument(
        "--output-dir",
        default="outputs/public_anisotropy/default",
        metavar="DIR",
        help="Directory to write artifacts into (created if absent).",
    )
    p.add_argument(
        "--name",
        default="public_anisotropy",
        metavar="NAME",
        help="Run name used in output filenames and report headers.",
    )
    p.add_argument(
        "--null-repeats",
        type=int,
        default=100,
        metavar="N",
        help="Number of isotropic null draws (default: 100).",
    )
    p.add_argument(
        "--seed",
        type=int,
        default=None,
        metavar="INT",
        help="RNG seed for reproducibility.",
    )
    p.add_argument(
        "--axis-count",
        type=int,
        default=48,
        metavar="N",
        help="Number of trial axes for preferred-axis scan (default: 48).",
    )
    p.add_argument(
        "--plots",
        action="store_true",
        help="Generate PNG plots (requires matplotlib).",
    )
    p.add_argument(
        "--save-normalized",
        action="store_true",
        help="Save normalized event CSV alongside analysis artifacts.",
    )
    p.add_argument(
        "--config",
        metavar="PATH",
        help="Path to optional JSON config file.",
    )
    return p


def main(argv=None) -> int:
    parser = _build_parser()
    args   = parser.parse_args(argv)

    # At least one source required
    if not args.catalog and not args.input:
        parser.error("Provide either --catalog or --input.")

    # Load optional config
    config = {}
    if args.config:
        import json
        with open(args.config) as f:
            config = json.load(f)

    # Determine catalog label for reporting
    if args.catalog:
        catalog_name = args.catalog
        ingest_source = args.catalog
    else:
        ingest_source = args.input
        catalog_name  = os.path.splitext(os.path.basename(args.input))[0]

    print(f"[INFO] Loading catalog: {ingest_source}")
    events = load_public_catalog(ingest_source)
    print(f"[INFO] Loaded {len(events)} events.")

    # For real CSV files, standardize_events provides type coercion already done
    # in _normalize_records; call standardize again only to add _b_proxy if absent
    for e in events:
        if e.get("dec") is not None and "_b_proxy" not in e:
            import math
            e["_b_proxy"] = abs(float(e["dec"]))
        if "_parse_warnings" not in e:
            e["_parse_warnings"] = []

    # Describe coverage
    coverage = describe_catalog_coverage(events)
    print(
        f"[INFO] Coverage: {coverage['event_count']} events, "
        f"{coverage['ra_dec_coverage'].get('n_with_position', 0)} with position, "
        f"instruments: {', '.join(str(x) for x in coverage['instrument_labels'][:5])}"
    )

    # Optionally save normalized CSV
    if args.save_normalized:
        norm_path = os.path.join(
            args.output_dir, f"{args.name}_normalized_events.csv"
        )
        os.makedirs(args.output_dir, exist_ok=True)
        schema_fields = [
            "event_id", "energy", "arrival_time", "ra", "dec", "instrument", "epoch"
        ]
        with open(norm_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=schema_fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(events)
        print(f"[INFO] Normalized events saved to: {norm_path}")

    # Merge CLI args into config
    run_config = dict(config)
    run_config.setdefault("null_repeats", args.null_repeats)
    run_config.setdefault("num_axes", args.axis_count)

    # Run the study
    print(
        f"[INFO] Running anisotropy study "
        f"(null_repeats={args.null_repeats}, axes={args.axis_count}, seed={args.seed})..."
    )
    results = run_public_anisotropy_study(
        events,
        null_repeats=args.null_repeats,
        seed=args.seed,
        config=run_config,
        num_axes=args.axis_count,
    )

    # Write artifacts
    manifest = write_public_study_artifacts(
        results=results,
        events=events,
        null_events_example=None,
        output_dir=args.output_dir,
        name=args.name,
        plots_enabled=args.plots,
        config=run_config,
        catalog_name=catalog_name,
        coverage=coverage,
    )

    # Terminal summary
    sig_eval = results.get("signal_evaluation", {})
    nc       = results.get("null_comparison", {})
    pa       = results.get("preferred_axis", {})
    ani      = results.get("anisotropy", {})

    print()
    print("=" * 60)
    print("  PUBLIC ANISOTROPY STUDY SUMMARY")
    print("=" * 60)
    print(f"  Catalog          : {catalog_name}")
    print(f"  Run name         : {args.name}")
    print(f"  Events           : {results.get('event_count', 0)}")
    print(f"  Hemisphere imb.  : {ani.get('hemisphere_imbalance', 0.0):.4f}")
    print(f"  Preferred-axis   : {pa.get('score', 0.0):.4f} "
          f"({pa.get('num_axes_scanned', '?')} axes, "
          f"pct={nc.get('axis_percentile', 0.0):.4f})")
    print(f"  Signal tier      : {sig_eval.get('tier', 'unknown')}")
    print(f"  Max percentile   : {sig_eval.get('max_percentile', 0.0):.4f}")
    print()
    print(f"  Output dir       : {args.output_dir}")
    print(f"  Artifacts:")
    for k, v in manifest.items():
        print(f"    {k:25s}: {v}")
    print("=" * 60)
    print()
    print("NOTE: Anomaly-like deviations are hypothesis-generating results,")
    print("not proof of any physical or metaphysical claim.")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
