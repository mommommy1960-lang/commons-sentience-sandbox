"""
run_stage12_icecube_diagnostics.py
=================================
CLI runner for Stage 12 IceCube robustness diagnostics.

Example
-------
python reality_audit/data_analysis/run_stage12_icecube_diagnostics.py \
  --input data/real/icecube_hese_events.csv \
  --output-dir outputs/stage12_icecube_diagnostics/stage12_icecube_diagnostics \
  --seed 42 \
  --axis-modes 48 96 192 \
  --leave-k-out 1 \
  --run-mode exploratory
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
from typing import Any, Dict, List, Optional

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from reality_audit.data_analysis.public_event_catalogs import load_public_catalog
from reality_audit.data_analysis.icecube_diagnostics import (
    run_full_icecube_diagnostics,
    write_icecube_diagnostics_memo,
    write_json,
    generate_icecube_diagnostic_plots,
    write_metric_stability_table,
)
from reality_audit.data_analysis.preregistration import load_preregistration_plan
from reality_audit.data_analysis.stage8_first_results import run_stage8_first_results


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Run Stage 12 IceCube robustness diagnostics.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--input", required=True, metavar="PATH", help="Path to IceCube catalog CSV/TSV.")
    p.add_argument("--output-dir", required=True, metavar="DIR", help="Output directory for Stage 12 artifacts.")
    p.add_argument("--seed", type=int, default=42, metavar="INT", help="RNG seed (default 42).")
    p.add_argument(
        "--axis-modes",
        nargs="+",
        type=int,
        default=[48, 96, 192],
        metavar="N",
        help="Axis-count settings for sensitivity checks (default: 48 96 192).",
    )
    p.add_argument(
        "--leave-k-out",
        type=int,
        default=1,
        metavar="K",
        dest="leave_k_out",
        help="k value for leave-k-out diagnostics (default 1).",
    )
    p.add_argument(
        "--repeats",
        type=int,
        default=150,
        metavar="N",
        help="Small-N sensitivity repeat count (default 150).",
    )
    p.add_argument(
        "--preregistration",
        default=None,
        metavar="PATH",
        help="Optional preregistration plan JSON path.",
    )
    p.add_argument(
        "--run-mode",
        default="exploratory",
        choices=["exploratory", "preregistered_confirmatory"],
        metavar="MODE",
        dest="run_mode",
        help="Run discipline label.",
    )
    return p


def _abs(path: str) -> str:
    if os.path.isabs(path):
        return path
    return os.path.join(_REPO_ROOT, path)


def _plan_choices_for_catalog(plan: Dict[str, Any], catalog_label: str) -> Dict[str, Any]:
    axis_count = int(plan.get("axis_scan", {}).get("axis_count", 192))
    null_repeats = int(plan.get("null_model", {}).get("null_repeats", 500))
    null_mode = str(plan.get("null_model", {}).get("primary", "isotropic")).lower()

    for c in plan.get("target_catalogs", []):
        if not isinstance(c, dict):
            continue
        label = str(c.get("label", "")).strip().lower()
        if label and label in catalog_label.lower():
            if c.get("null_mode"):
                null_mode = str(c.get("null_mode")).lower()
            break

    return {
        "axis_count": axis_count,
        "null_repeats": null_repeats,
        "null_mode": null_mode,
    }


def main(argv=None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    input_path = _abs(args.input)
    output_dir = _abs(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)

    if not os.path.isfile(input_path):
        print(f"[ERROR] Input file not found: {input_path}")
        return 1

    events = load_public_catalog(input_path)
    catalog_label = os.path.splitext(os.path.basename(input_path))[0]

    print(f"[INFO] Loaded catalog: {catalog_label} (N={len(events)})")
    print(f"[INFO] Running diagnostics: axis_modes={args.axis_modes}, leave_k_out={args.leave_k_out}")

    diagnostics = run_full_icecube_diagnostics(
        events,
        repeats=args.repeats,
        seed=args.seed,
        axis_modes=args.axis_modes,
        leave_k_out=args.leave_k_out,
    )

    summary_json_path = os.path.join(output_dir, "stage12_icecube_diagnostics_summary.json")
    write_json(summary_json_path, diagnostics)
    memo_path = write_icecube_diagnostics_memo(diagnostics, output_dir)
    metric_table_path = write_metric_stability_table(diagnostics, output_dir)
    plot_paths = generate_icecube_diagnostic_plots(diagnostics, output_dir)

    confirmatory_bundle: Optional[Dict[str, Any]] = None
    prereg_path = _abs(args.preregistration) if args.preregistration else None

    if args.run_mode == "preregistered_confirmatory":
        if not prereg_path:
            print("[WARN] run-mode=preregistered_confirmatory but no --preregistration provided.")
        elif not os.path.isfile(prereg_path):
            print(f"[WARN] preregistration plan not found: {prereg_path}")
        else:
            plan = load_preregistration_plan(prereg_path)
            choices = _plan_choices_for_catalog(plan, catalog_label)
            rerun_dir = os.path.join(output_dir, "confirmatory_rerun")
            rerun_name = "stage12_icecube_confirmatory_rerun"
            print(
                "[INFO] Running confirmatory rerun with plan choices: "
                f"null_mode={choices['null_mode']}, null_repeats={choices['null_repeats']}, "
                f"axis_count={choices['axis_count']}"
            )
            confirmatory_bundle = run_stage8_first_results(
                input_path=input_path,
                output_dir=rerun_dir,
                name=rerun_name,
                null_repeats=choices["null_repeats"],
                axis_count=choices["axis_count"],
                seed=args.seed,
                plots=False,
                save_normalized=True,
                null_mode=choices["null_mode"],
                preregistration_plan=plan,
                preregistration_plan_path=prereg_path,
                run_mode="preregistered_confirmatory",
            )

    manifest = {
        "stage": "stage12_icecube_diagnostics",
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "input": input_path,
        "output_dir": output_dir,
        "run_mode": args.run_mode,
        "seed": args.seed,
        "axis_modes": args.axis_modes,
        "leave_k_out": args.leave_k_out,
        "repeats": args.repeats,
        "diagnostics_summary_json": summary_json_path,
        "diagnostics_memo_md": memo_path,
        "metric_stability_table_csv": metric_table_path,
        "plots": plot_paths,
        "preregistration_plan": prereg_path,
        "confirmatory_rerun_summary": (
            confirmatory_bundle.get("manifest", {}).get("summary_json")
            if isinstance(confirmatory_bundle, dict)
            else None
        ),
    }

    manifest_path = os.path.join(output_dir, "stage12_icecube_diagnostics_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print()
    print("=" * 62)
    print("  STAGE 12 ICECUBE DIAGNOSTICS")
    print("=" * 62)
    print(f"  Catalog           : {catalog_label}")
    print(f"  Event count       : {len(events)}")
    print(f"  Run mode          : {args.run_mode}")
    print(f"  Robustness label  : {diagnostics.get('robustness_assessment', {}).get('label')}")
    print(f"  Summary JSON      : {summary_json_path}")
    print(f"  Memo              : {memo_path}")
    print(f"  Stability table   : {metric_table_path}")
    print(f"  Manifest          : {manifest_path}")
    if confirmatory_bundle:
        print(f"  Confirmatory rerun: {confirmatory_bundle.get('stage8_manifest_path')}")
    print("=" * 62)

    return 0


if __name__ == "__main__":
    sys.exit(main())
