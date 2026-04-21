"""
run_stage14_confirmatory_comparison.py
=======================================
Stage 14 – Build a three-catalog comparison from the confirmatory reruns and
re-evaluate the publication gate.

This is the final gate evaluation after the confirmpatory reruns have been
completed by run_stage14_confirmatory_reruns.py.  It:

1. Loads the three confirmatory summary JSONs from outputs/stage14_confirmatory/.
2. Runs compare_three_catalog_results (same as Stage 10/11/12 pipeline).
3. Optionally integrates IceCube diagnostics.
4. Re-evaluates the Stage 13 publication gate with the confirmatory inputs.
5. Writes comparison, gate, and first-results artifacts to
   outputs/stage14_confirmatory/gate/.

Expected verdict after this step: ``internally_reviewable`` (all three required
gates — prereg_present, prereg_locked, trial_correction_applied — should now
pass because the confirmatory summaries carry the locked plan metadata and the
Holm trial correction).

Usage
-----
python reality_audit/data_analysis/run_stage14_confirmatory_comparison.py

Run from repo root after run_stage14_confirmatory_reruns.py has completed.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Optional

_HERE      = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from reality_audit.data_analysis.catalog_comparison import (
    load_stage_results,
    compare_three_catalog_results,
    load_icecube_diagnostics_summary,
    integrate_icecube_robustness_into_three_catalog,
    write_three_catalog_comparison_memo,
)
from reality_audit.data_analysis.publication_gate import (
    load_publication_gate,
    evaluate_publication_gate,
    write_publication_gate_report,
)
from reality_audit.data_analysis.first_results_package import (
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

_CONF_BASE  = os.path.join("outputs", "stage14_confirmatory")
_GATE_DIR   = os.path.join(_CONF_BASE, "gate")
_DIAG_PATH  = os.path.join(
    "outputs", "stage12_icecube_diagnostics",
    "stage12_icecube_diagnostics",
    "stage12_icecube_diagnostics_summary.json",
)


def _abs(p: str) -> str:
    if os.path.isabs(p):
        return p
    return os.path.join(_REPO_ROOT, p)


def _find_summary(subdir: str, name_hint: str) -> Optional[str]:
    """Return path of the first *_summary.json in a subdirectory, or None."""
    d = _abs(os.path.join(_CONF_BASE, subdir))
    if not os.path.isdir(d):
        return None
    for fname in sorted(os.listdir(d)):
        if fname.endswith("_summary.json"):
            return os.path.join(d, fname)
    return None


# ---------------------------------------------------------------------------
# Core function
# ---------------------------------------------------------------------------

def run_stage14_comparison(
    fermi_path:       Optional[str] = None,
    swift_path:       Optional[str] = None,
    icecube_path:     Optional[str] = None,
    diagnostics_path: Optional[str] = None,
    output_dir:       Optional[str] = None,
    name: str = "stage14_confirmatory_gate",
    gate_config_path: Optional[str] = None,
) -> dict:
    """Run Stage 14 comparison and publication gate.

    Parameters
    ----------
    fermi_path, swift_path, icecube_path :
        Paths to Stage 14 confirmatory summary JSONs.  Auto-detected from
        ``outputs/stage14_confirmatory/{fermi,swift,icecube}/`` if not supplied.
    diagnostics_path :
        IceCube diagnostics JSON (Stage 12).  Optional; uses Stage 12 default.
    output_dir :
        Where to write Gate/comparison artifacts.  Defaults to
        ``outputs/stage14_confirmatory/gate``.
    name : str
        Base name for output files.
    gate_config_path :
        Publication gate checklist JSON.

    Returns
    -------
    dict with keys: comparison, gate_result, gate_report_path, manifest_path
    """
    # Resolve paths
    fermi_path       = fermi_path       or _find_summary("fermi",   "fermi")
    swift_path       = swift_path       or _find_summary("swift",   "swift")
    icecube_path     = icecube_path     or _find_summary("icecube", "icecube")
    diagnostics_path = diagnostics_path or _abs(_DIAG_PATH)
    output_dir       = output_dir or _abs(_GATE_DIR)

    os.makedirs(output_dir, exist_ok=True)

    # -----------------------------------------------------------------------
    # 1. Load confirmatory summaries
    # -----------------------------------------------------------------------
    def _load(p, label):
        if not p or not os.path.isfile(p):
            print(f"[WARN] {label} not found: {p}")
            return None
        print(f"[INFO] Loading {label}: {p}")
        result = load_stage_results(p)
        # Promote nested run_metadata fields to the top level so the
        # publication gate can find them via flat dict access.
        rm   = result.get("run_metadata", {})
        prereg = rm.get("preregistration", {})
        tfc    = rm.get("trial_factor_correction", {})
        if prereg.get("plan_hash_sha256") and "preregistration_hash" not in result:
            result["preregistration_hash"]   = prereg["plan_hash_sha256"]
        if "locked" in prereg and "preregistration_locked" not in result:
            result["preregistration_locked"] = prereg["locked"]
        if tfc.get("method") and "trial_correction_method" not in result:
            result["trial_correction_method"] = tfc["method"]
        if rm.get("run_mode") and "run_mode" not in result:
            result["run_mode"] = rm["run_mode"]
        return result

    fermi    = _load(fermi_path,   "Fermi confirmatory summary")
    swift    = _load(swift_path,   "Swift confirmatory summary")
    icecube  = _load(icecube_path, "IceCube confirmatory summary")

    available = [r for r in [fermi, swift, icecube] if r is not None]
    if not available:
        raise RuntimeError(
            "No confirmatory summaries found. "
            "Run run_stage14_confirmatory_reruns.py first."
        )

    # -----------------------------------------------------------------------
    # 2. Three-catalog comparison
    # -----------------------------------------------------------------------
    print("[INFO] Running three-catalog comparison...")
    comparison = compare_three_catalog_results(
        fermi or {},
        swift or {},
        icecube or {},
    )

    # Integrate IceCube diagnostics if available
    if os.path.isfile(diagnostics_path):
        print(f"[INFO] Loading IceCube diagnostics: {diagnostics_path}")
        with open(diagnostics_path) as fh:
            diag = json.load(fh)
        comparison = integrate_icecube_robustness_into_three_catalog(comparison, diag)

    # Write comparison memo
    comp_memo_path = os.path.join(output_dir, f"{name}_comparison.md")
    comp_json_path = os.path.join(output_dir, f"{name}_comparison.json")
    write_three_catalog_comparison_memo(comparison, comp_memo_path)
    with open(comp_json_path, "w") as fh:
        json.dump(comparison, fh, indent=2)
        fh.write("\n")
    print(f"[INFO] Comparison written: {comp_json_path}")

    # -----------------------------------------------------------------------
    # 3. Publication gate
    # -----------------------------------------------------------------------
    print("[INFO] Evaluating publication gate...")
    gate_config  = load_publication_gate(gate_config_path)
    run_metadata = {
        "catalogs": [r for r in [fermi, swift, icecube] if r is not None]
    }
    diagnostics_obj = None
    if os.path.isfile(diagnostics_path):
        with open(diagnostics_path) as fh:
            diagnostics_obj = json.load(fh)

    gate_result = evaluate_publication_gate(
        run_metadata        = run_metadata,
        comparison_summary  = comparison,
        diagnostics_summary = diagnostics_obj,
        gate_config         = gate_config,
    )

    gate_report_path = write_publication_gate_report(
        gate_result, output_dir, name=f"{name}_publication_gate"
    )
    gate_json_path = os.path.join(output_dir, f"{name}_publication_gate.json")
    with open(gate_json_path, "w") as fh:
        json.dump(gate_result, fh, indent=2)
        fh.write("\n")
    print(f"[INFO] Gate verdict: {gate_result['verdict'].upper()}")
    print(f"[INFO] Gate report : {gate_report_path}")

    # -----------------------------------------------------------------------
    # 4. First-results package
    # -----------------------------------------------------------------------
    print("[INFO] Building first-results package...")
    package = build_first_results_package(
        fermi_path       = fermi_path       if (fermi_path and os.path.isfile(fermi_path)) else None,
        swift_path       = swift_path       if (swift_path and os.path.isfile(swift_path)) else None,
        icecube_path     = icecube_path     if (icecube_path and os.path.isfile(icecube_path)) else None,
        comparison_path  = comp_json_path,
        diagnostics_path = diagnostics_path if os.path.isfile(diagnostics_path) else None,
        gate_result      = gate_result,
    )
    brief_path = write_first_results_brief(
        package, output_dir, name=f"{name}_first_results_brief"
    )
    print(f"[INFO] First-results brief: {brief_path}")

    # -----------------------------------------------------------------------
    # 5. Output hygiene
    # -----------------------------------------------------------------------
    hygiene = classify_output_paths()
    hygiene_path = write_output_hygiene_report(
        hygiene, output_dir, name=f"{name}_output_hygiene"
    )
    print(f"[INFO] Hygiene report: {hygiene_path}")

    # -----------------------------------------------------------------------
    # 6. Manifest
    # -----------------------------------------------------------------------
    passed  = [g["id"] for g in gate_result.get("gates", []) if g.get("passed")]
    failed  = [g["id"] for g in gate_result.get("gates", []) if not g.get("passed")]
    manifest = {
        "stage": 14,
        "pipeline_step": "confirmatory_comparison_and_gate",
        "fermi_summary_path":    str(fermi_path),
        "swift_summary_path":    str(swift_path),
        "icecube_summary_path":  str(icecube_path),
        "comparison_json_path":  comp_json_path,
        "gate_json_path":        gate_json_path,
        "gate_report_path":      gate_report_path,
        "brief_path":            brief_path,
        "gate_verdict":          gate_result["verdict"],
        "gate_checks_passed":    passed,
        "gate_checks_failed":    failed,
    }
    manifest_path = os.path.join(output_dir, f"{name}_manifest.json")
    with open(manifest_path, "w") as fh:
        json.dump(manifest, fh, indent=2)
        fh.write("\n")
    print(f"[INFO] Manifest: {manifest_path}")

    return {
        "comparison":       comparison,
        "gate_result":      gate_result,
        "gate_report_path": gate_report_path,
        "manifest_path":    manifest_path,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Stage 14: build confirmatory comparison and re-evaluate publication gate.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--fermi",       default=None, metavar="PATH",
                   help="Fermi confirmatory summary JSON (auto-detected if omitted.")
    p.add_argument("--swift",       default=None, metavar="PATH",
                   help="Swift confirmatory summary JSON (auto-detected if omitted).")
    p.add_argument("--icecube",     default=None, metavar="PATH",
                   help="IceCube confirmatory summary JSON (auto-detected if omitted).")
    p.add_argument("--diagnostics", default=None, metavar="PATH",
                   help=f"IceCube diagnostics JSON. Default: {_DIAG_PATH}")
    p.add_argument("--output-dir",  default=None, metavar="DIR",
                   help=f"Gate output directory. Default: {_GATE_DIR}")
    p.add_argument("--name",        default="stage14_confirmatory_gate", metavar="NAME",
                   help="Base name for output files.")
    p.add_argument("--gate-config", default=None, metavar="PATH",
                   help="Publication gate checklist JSON.")
    return p


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        result = run_stage14_comparison(
            fermi_path       = args.fermi,
            swift_path       = args.swift,
            icecube_path     = args.icecube,
            diagnostics_path = args.diagnostics,
            output_dir       = _abs(args.output_dir) if args.output_dir else None,
            name             = args.name,
            gate_config_path = args.gate_config,
        )
    except RuntimeError as exc:
        print(f"[ERROR] {exc}")
        return 1

    gate = result["gate_result"]
    gates  = gate.get("gates", [])
    n_pass = sum(1 for g in gates if g.get("passed"))
    n_fail = sum(1 for g in gates if not g.get("passed"))

    print()
    print("=" * 62)
    print("  STAGE 14 CONFIRMATORY GATE EVALUATION")
    print("=" * 62)
    print(f"  Verdict        : {gate['verdict'].upper()}")
    print(f"  Checks passed  : {n_pass}")
    print(f"  Checks failed  : {n_fail}")
    if n_fail:
        for g in gates:
            if not g.get("passed"):
                print(f"    FAIL  {g['id']}")
    print(f"\n  Report  : {result['gate_report_path']}")
    print(f"  Manifest: {result['manifest_path']}")
    print()

    return 0 if gate["verdict"] in (
        "internally_reviewable",
        "ready_for_publication",
        "candidate_first_results_note",
    ) else 1


if __name__ == "__main__":
    sys.exit(main())
