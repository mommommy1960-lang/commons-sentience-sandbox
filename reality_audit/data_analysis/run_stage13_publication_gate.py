"""
run_stage13_publication_gate.py
================================
Stage 13 CLI: evaluate publication readiness for the current three-catalog
anisotropy project state.

Steps
-----
1. Locate current Fermi / Swift / IceCube summaries.
2. Locate current comparison summary.
3. Evaluate publication gate.
4. Build first-results package.
5. Write:
   - publication gate JSON + Markdown report
   - first-results brief (JSON + Markdown)
   - output hygiene report (JSON + Markdown)
   - Stage 13 manifest

Usage
-----
::

    # Default paths (auto-detects current best outputs)
    python reality_audit/data_analysis/run_stage13_publication_gate.py

    # Explicit paths
    python reality_audit/data_analysis/run_stage13_publication_gate.py \\
        --fermi outputs/stage9_first_results/stage9_fermi_exposure_corrected/stage9_fermi_exposure_corrected_summary.json \\
        --swift outputs/stage10_first_results/stage10_swift_first_results/stage10_swift_first_results_summary.json \\
        --icecube outputs/stage8_first_results/stage11_icecube_first_results/stage11_icecube_first_results_summary.json \\
        --comparison outputs/stage10_first_results/comparison/stage12_comparison_with_robustness.json \\
        --diagnostics outputs/stage12_icecube_diagnostics/stage12_icecube_diagnostics/stage12_icecube_diagnostics_summary.json \\
        --output-dir outputs/stage13_publication_gate/stage13_main \\
        --name stage13_main

Author: commons-sentience-sandbox
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys

_HERE       = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT  = os.path.abspath(os.path.join(_HERE, "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from reality_audit.data_analysis.publication_gate import (
    load_publication_gate,
    evaluate_publication_gate,
    write_publication_gate_report,
)
from reality_audit.data_analysis.first_results_package import (
    collect_stage_results,
    build_first_results_package,
    write_first_results_brief,
)
from reality_audit.data_analysis.output_hygiene import (
    classify_output_paths,
    write_output_hygiene_report,
)

# ---------------------------------------------------------------------------
# Default paths
# ---------------------------------------------------------------------------

_DEFAULT_FERMI = os.path.join(
    "outputs", "stage9_first_results",
    "stage9_fermi_exposure_corrected",
    "stage9_fermi_exposure_corrected_summary.json",
)
_DEFAULT_SWIFT = os.path.join(
    "outputs", "stage10_first_results",
    "stage10_swift_first_results",
    "stage10_swift_first_results_summary.json",
)
_DEFAULT_ICECUBE = os.path.join(
    "outputs", "stage8_first_results",
    "stage11_icecube_first_results",
    "stage11_icecube_first_results_summary.json",
)
_DEFAULT_COMPARISON = os.path.join(
    "outputs", "stage10_first_results",
    "comparison",
    "stage12_comparison_with_robustness.json",
)
_DEFAULT_DIAGNOSTICS = os.path.join(
    "outputs", "stage12_icecube_diagnostics",
    "stage12_icecube_diagnostics",
    "stage12_icecube_diagnostics_summary.json",
)
_DEFAULT_OUTPUT_DIR = os.path.join(
    "outputs", "stage13_publication_gate", "stage13_main"
)
_DEFAULT_NAME = "stage13_main"


def _abs(p: str) -> str:
    if os.path.isabs(p):
        return p
    return os.path.join(_REPO_ROOT, p)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Stage 13: evaluate publication readiness for the current pipeline state.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--fermi",      default=None, metavar="PATH",
                   help=f"Fermi summary JSON. Default: {_DEFAULT_FERMI}")
    p.add_argument("--swift",      default=None, metavar="PATH",
                   help=f"Swift summary JSON. Default: {_DEFAULT_SWIFT}")
    p.add_argument("--icecube",    default=None, metavar="PATH",
                   help=f"IceCube summary JSON. Default: {_DEFAULT_ICECUBE}")
    p.add_argument("--comparison", default=None, metavar="PATH",
                   help=f"Comparison JSON. Default: {_DEFAULT_COMPARISON}")
    p.add_argument("--diagnostics",default=None, metavar="PATH",
                   help=f"IceCube diagnostics JSON. Default: {_DEFAULT_DIAGNOSTICS}")
    p.add_argument("--gate-config",default=None, metavar="PATH",
                   help="Publication gate checklist JSON. Default: configs/publication_gate_checklist.json")
    p.add_argument("--output-dir", default=None, metavar="DIR",
                   help=f"Output directory. Default: {_DEFAULT_OUTPUT_DIR}")
    p.add_argument("--name",       default=_DEFAULT_NAME, metavar="NAME",
                   help=f"Base name for output files. Default: {_DEFAULT_NAME}")
    return p


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)

    fermi_path       = _abs(args.fermi      or _DEFAULT_FERMI)
    swift_path       = _abs(args.swift      or _DEFAULT_SWIFT)
    icecube_path     = _abs(args.icecube    or _DEFAULT_ICECUBE)
    comparison_path  = _abs(args.comparison or _DEFAULT_COMPARISON)
    diagnostics_path = _abs(args.diagnostics or _DEFAULT_DIAGNOSTICS)
    output_dir       = _abs(args.output_dir  or _DEFAULT_OUTPUT_DIR)
    name             = args.name

    os.makedirs(output_dir, exist_ok=True)

    # -----------------------------------------------------------------------
    # 1. Load catalog summaries
    # -----------------------------------------------------------------------
    def _load_if_exists(p: str, label: str):
        if os.path.isfile(p):
            print(f"[INFO] Loading {label}: {p}")
            with open(p) as f:
                return json.load(f)
        else:
            print(f"[WARN] {label} not found: {p}")
            return None

    fermi      = _load_if_exists(fermi_path,       "Fermi summary")
    swift      = _load_if_exists(swift_path,       "Swift summary")
    icecube    = _load_if_exists(icecube_path,     "IceCube summary")
    comparison = _load_if_exists(comparison_path,  "Comparison summary")
    diagnostics = _load_if_exists(diagnostics_path,"IceCube diagnostics")

    # -----------------------------------------------------------------------
    # 2. Build run_metadata for gate evaluation
    # -----------------------------------------------------------------------
    catalogs = []
    for r, lbl in [(fermi, "fermi"), (swift, "swift"), (icecube, "icecube")]:
        if r:
            catalogs.append(r)

    if not catalogs:
        print("[ERROR] No catalog summaries found. Run Stage 8 first.")
        return 1

    run_metadata = {"catalogs": catalogs}
    comparison_for_gate = comparison or {}

    # -----------------------------------------------------------------------
    # 3. Evaluate publication gate
    # -----------------------------------------------------------------------
    print("[INFO] Evaluating publication gate...")
    gate_config = load_publication_gate(args.gate_config)
    gate_result = evaluate_publication_gate(
        run_metadata       = run_metadata,
        comparison_summary = comparison_for_gate,
        diagnostics_summary = diagnostics,
        gate_config        = gate_config,
    )

    gate_report_path = write_publication_gate_report(gate_result, output_dir, name=f"{name}_publication_gate")
    gate_json_path   = os.path.join(output_dir, f"{name}_publication_gate.json")
    print(f"[INFO] Gate verdict: {gate_result['verdict'].upper()}")

    # -----------------------------------------------------------------------
    # 4. Build first-results package
    # -----------------------------------------------------------------------
    print("[INFO] Building first-results package...")
    package = build_first_results_package(
        fermi_path       = fermi_path       if os.path.isfile(fermi_path)       else None,
        swift_path       = swift_path       if os.path.isfile(swift_path)       else None,
        icecube_path     = icecube_path     if os.path.isfile(icecube_path)     else None,
        comparison_path  = comparison_path  if os.path.isfile(comparison_path)  else None,
        diagnostics_path = diagnostics_path if os.path.isfile(diagnostics_path) else None,
        gate_result      = gate_result,
    )
    brief_path = write_first_results_brief(package, output_dir, name=f"{name}_first_results_brief")
    print(f"[INFO] First-results brief: {brief_path}")

    # -----------------------------------------------------------------------
    # 5. Output hygiene
    # -----------------------------------------------------------------------
    print("[INFO] Classifying output hygiene...")
    hygiene = classify_output_paths()
    hygiene_report_path = write_output_hygiene_report(hygiene, output_dir, name=f"{name}_output_hygiene")
    print(f"[INFO] Hygiene report: {hygiene_report_path}")

    # -----------------------------------------------------------------------
    # 6. Manifest
    # -----------------------------------------------------------------------
    manifest = {
        "stage":            13,
        "name":             name,
        "generated_at":     datetime.datetime.utcnow().isoformat() + "Z",
        "inputs": {
            "fermi":      fermi_path,
            "swift":      swift_path,
            "icecube":    icecube_path,
            "comparison": comparison_path,
            "diagnostics":diagnostics_path,
        },
        "outputs": {
            "gate_json":         gate_json_path,
            "gate_report":       gate_report_path,
            "brief_json":        os.path.join(output_dir, f"{name}_first_results_brief.json"),
            "brief_md":          brief_path,
            "hygiene_json":      os.path.join(output_dir, f"{name}_output_hygiene.json"),
            "hygiene_report":    hygiene_report_path,
        },
        "gate_verdict":          gate_result["verdict"],
        "replication_verdict":   package.get("replication_verdict"),
        "icecube_robustness":    package.get("icecube_diagnostics_label"),
        "failing_required_gates": gate_result.get("failing_required", []),
        "hygiene_summary":       hygiene["summary"],
    }
    manifest_path = os.path.join(output_dir, f"{name}_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    # -----------------------------------------------------------------------
    # Terminal summary
    # -----------------------------------------------------------------------
    print()
    print("=" * 66)
    print("  STAGE 13 PUBLICATION GATE SUMMARY")
    print("=" * 66)
    print(f"  Gate verdict           : {gate_result['verdict'].upper()}")
    print(f"  Readiness description  : {gate_result.get('readiness_description', '')}")
    print(f"  Replication verdict    : {package.get('replication_verdict', 'N/A').upper()}")
    if package.get("icecube_diagnostics_label"):
        print(f"  IceCube robustness     : {package['icecube_diagnostics_label']}")
    if gate_result["failing_required"]:
        print(f"  Failing required gates : {', '.join(gate_result['failing_required'])}")
    if gate_result["failing_recommended"]:
        print(f"  Failing recommended    : {', '.join(gate_result['failing_recommended'])}")
    print()
    print(f"  Gate report            : {gate_report_path}")
    print(f"  First-results brief    : {brief_path}")
    print(f"  Hygiene report         : {hygiene_report_path}")
    print(f"  Manifest               : {manifest_path}")
    print()
    hs = hygiene["summary"]
    print(f"  Hygiene: {hs['deliverable']} deliverables, {hs['smoke']} smoke, "
          f"{hs['transient_plot']} plots, {hs['legacy']} legacy, {hs['unknown']} unknown")
    print("=" * 66)
    print()

    if package.get("blockers"):
        print("  Next required actions:")
        for b in package["blockers"]:
            print(f"    - {b}")
    print()
    print("NOTE: This is an internal pipeline readiness evaluation.")
    print("Results must not be circulated without external scientific review.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
