"""
first_results_package.py
========================
Build a candidate first-results package from the current three-catalog
anisotropy pipeline state.

Purpose
-------
This module collects per-catalog run summaries, the cross-catalog comparison
result, and Stage 12 IceCube robustness diagnostics into a single structured
package.  It then writes a sober internal brief stating:

- what was tested
- current evidence status
- which catalogs support / do not support replication
- whether the current state is publishable
- what must be fixed next

This is an internal decision document, not a paper.

Usage
-----
::

    from reality_audit.data_analysis.first_results_package import (
        collect_stage_results,
        build_first_results_package,
        write_first_results_brief,
    )

    package = build_first_results_package(
        fermi_path="outputs/.../fermi_summary.json",
        swift_path="outputs/.../swift_summary.json",
        icecube_path="outputs/.../icecube_summary.json",
        comparison_path="outputs/.../comparison.json",
        diagnostics_path="outputs/.../diagnostics_summary.json",
    )
    brief_path = write_first_results_brief(package, "outputs/stage13")

Author: commons-sentience-sandbox
"""

from __future__ import annotations

import datetime
import json
import os
from typing import Any, Dict, List, Optional


_HERE      = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_json_if_present(path: Optional[str]) -> Optional[Dict[str, Any]]:
    if not path:
        return None
    p = path if os.path.isabs(path) else os.path.join(_REPO_ROOT, path)
    if os.path.isfile(p):
        with open(p) as f:
            return json.load(f)
    return None


def _fmt_float(v: Any, digits: int = 4) -> str:
    if v is None:
        return "N/A"
    try:
        return f"{float(v):.{digits}f}"
    except (TypeError, ValueError):
        return str(v)


# ===========================================================================
# 1. Collect stage results
# ===========================================================================

def collect_stage_results(
    fermi_path:       Optional[str] = None,
    swift_path:       Optional[str] = None,
    icecube_path:     Optional[str] = None,
    comparison_path:  Optional[str] = None,
    diagnostics_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Gather available pipeline outputs into a raw collection dict.

    Parameters
    ----------
    fermi_path, swift_path, icecube_path : str, optional
        Paths to per-catalog Stage 8 summary JSON files.
    comparison_path : str, optional
        Path to Stage 10/11/12 three-catalog comparison JSON.
    diagnostics_path : str, optional
        Path to Stage 12 IceCube diagnostics summary JSON.

    Returns
    -------
    dict with keys: fermi, swift, icecube, comparison, diagnostics
        Each is the loaded dict or None if not available.
    """
    return {
        "fermi":       _load_json_if_present(fermi_path),
        "swift":       _load_json_if_present(swift_path),
        "icecube":     _load_json_if_present(icecube_path),
        "comparison":  _load_json_if_present(comparison_path),
        "diagnostics": _load_json_if_present(diagnostics_path),
    }


# ===========================================================================
# 2. Build package
# ===========================================================================

def build_first_results_package(
    fermi_path:       Optional[str] = None,
    swift_path:       Optional[str] = None,
    icecube_path:     Optional[str] = None,
    comparison_path:  Optional[str] = None,
    diagnostics_path: Optional[str] = None,
    gate_result:      Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build the first-results package from available pipeline outputs.

    Parameters
    ----------
    *_path : str, optional
        Input JSON file paths.  None → not available.
    gate_result : dict, optional
        Output of ``evaluate_publication_gate`` to embed readiness verdict.

    Returns
    -------
    dict with structured package summary.
    """
    raw = collect_stage_results(
        fermi_path=fermi_path,
        swift_path=swift_path,
        icecube_path=icecube_path,
        comparison_path=comparison_path,
        diagnostics_path=diagnostics_path,
    )

    fermi      = raw["fermi"]
    swift      = raw["swift"]
    icecube    = raw["icecube"]
    comparison = raw["comparison"]
    diagnostics = raw["diagnostics"]

    # -----------------------------------------------------------------------
    # Catalog rows
    # -----------------------------------------------------------------------
    catalog_entries: List[Dict[str, Any]] = []

    def _cat_entry(r: Optional[Dict], label: str) -> None:
        if r is None:
            catalog_entries.append({"label": label, "available": False})
            return
        catalog_entries.append({
            "label":          label,
            "available":      True,
            "catalog":        r.get("catalog", label),
            "event_count":    r.get("event_count"),
            "null_mode":      r.get("null_mode"),
            "hemi_percentile": r.get("hemi_percentile"),
            "axis_percentile": r.get("axis_percentile"),
            "tier":            r.get("tier"),
            "trial_correction_method": r.get("trial_correction_method"),
            "run_mode":        r.get("run_mode"),
            "preregistration_hash": r.get("preregistration_hash"),
        })

    _cat_entry(fermi,   "fermi")
    _cat_entry(swift,   "swift")
    _cat_entry(icecube, "icecube")

    n_available = sum(1 for e in catalog_entries if e["available"])

    # -----------------------------------------------------------------------
    # Replication summary
    # -----------------------------------------------------------------------
    replication_verdict = "unknown"
    interpretation = ""
    caveats: List[str] = []
    icecube_robustness: Optional[Dict] = None

    if comparison:
        replication_verdict = comparison.get("consistency_verdict", "unknown")
        interpretation      = comparison.get("interpretation", "")
        caveats             = comparison.get("caveats", [])
        icecube_robustness  = comparison.get("icecube_robustness")

    # Augment with diagnostics
    diag_label: Optional[str] = None
    if diagnostics:
        diag_label = (diagnostics.get("robustness_label")
                      or diagnostics.get("label"))

    # -----------------------------------------------------------------------
    # Preregistration status
    # -----------------------------------------------------------------------
    any_prereg = any(e.get("preregistration_hash") for e in catalog_entries if e.get("available"))
    any_locked = False  # Cannot determine from summary JSON alone; gate handles this

    # -----------------------------------------------------------------------
    # Publishability assessment
    # -----------------------------------------------------------------------
    gate_verdict = (gate_result or {}).get("verdict", "not_evaluated")
    failing_required = (gate_result or {}).get("failing_required", [])

    publishable = gate_verdict in ("candidate_first_results_note", "ready_for_external_review")

    # -----------------------------------------------------------------------
    # What must be fixed
    # -----------------------------------------------------------------------
    blockers: List[str] = []
    if "prereg_locked" in failing_required or not any_prereg:
        blockers.append("Lock the preregistration plan (_locked: true) before confirmatory reruns.")
    if "trial_correction_applied" in failing_required:
        blockers.append("Apply Holm or Bonferroni trial-factor correction.")
    if n_available < 2:
        blockers.append("Obtain at least two independent catalog results.")
    if replication_verdict == "unknown":
        blockers.append("Run cross-catalog comparison.")
    if icecube and (icecube.get("event_count") or 0) < 50:
        blockers.append("IceCube HESE is small-N; supplement with a larger independent catalog.")
    blockers.append("External scientific review is required before public circulation.")

    # Add gate-specific failing gates that are not already covered
    standard_covered = {"prereg_locked", "trial_correction_applied"}
    for g in failing_required:
        if g not in standard_covered:
            blockers.append(f"Resolve gate failure: {g}")

    return {
        "package_version":        "stage13_v1",
        "generated_at":           datetime.datetime.utcnow().isoformat() + "Z",
        "catalogs_available":     n_available,
        "catalog_entries":        catalog_entries,
        "replication_verdict":    replication_verdict,
        "interpretation":         interpretation,
        "caveats":                caveats,
        "icecube_robustness":     icecube_robustness,
        "icecube_diagnostics_label": diag_label,
        "preregistration_recorded": any_prereg,
        "gate_verdict":           gate_verdict,
        "failing_required_gates": failing_required,
        "publishable_internal":   publishable,
        "blockers":               blockers,
    }


# ===========================================================================
# 3. Write brief
# ===========================================================================

def write_first_results_brief(
    package: Dict[str, Any],
    output_dir: str,
    name: str = "stage13_first_results_brief",
) -> str:
    """Write an internal first-results brief from the package.

    Parameters
    ----------
    package : dict
        Output of ``build_first_results_package``.
    output_dir : str
        Directory to write the brief.
    name : str
        Base filename.

    Returns
    -------
    str : path to the Markdown brief.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Save JSON version
    json_path = os.path.join(output_dir, f"{name}.json")
    with open(json_path, "w") as f:
        json.dump(package, f, indent=2)

    # Markdown brief
    md_path = os.path.join(output_dir, f"{name}.md")
    lines: List[str] = [
        "# Internal First-Results Brief",
        "",
        "> This is an internal pipeline decision document.",
        "> It is not a scientific paper and does not constitute a publishable claim.",
        "",
        f"Generated: {package.get('generated_at', 'unknown')}",
        "",
        "---",
        "",
        "## What Was Tested",
        "",
        "The Reality Audit public anisotropy program tests whether high-energy "
        "astrophysical event arrival directions show a statistically significant "
        "sky-position anisotropy that persists across independent instrument catalogs, "
        "after correcting for known instrument acceptance geometry.",
        "",
        "The primary null hypothesis is that event arrival directions are consistent "
        "with isotropic (or acceptance-corrected isotropic) sky coverage.",
        "",
        "Two primary statistics are evaluated: hemisphere imbalance and preferred-axis "
        "score. Both are corrected for multiple testing using the Holm method.",
        "",
        "---",
        "",
        "## Current Evidence Status",
        "",
        f"Catalogs available: **{package['catalogs_available']}**",
        "",
    ]

    lines.append("| Catalog | N | Null model | Hemi pct | Axis pct | Tier | Run mode |")
    lines.append("|---|---|---|---|---|---|---|")
    for e in package["catalog_entries"]:
        if not e["available"]:
            lines.append(f"| {e['label']} | — | — | — | — | _not available_ | — |")
        else:
            lines.append(
                f"| {e.get('catalog', e['label'])} "
                f"| {e.get('event_count', 'N/A')} "
                f"| {e.get('null_mode', 'N/A')} "
                f"| {_fmt_float(e.get('hemi_percentile'))} "
                f"| {_fmt_float(e.get('axis_percentile'))} "
                f"| `{e.get('tier', 'N/A')}` "
                f"| {e.get('run_mode', 'N/A')} |"
            )

    lines += [
        "",
        f"**Cross-catalog replication verdict: `{package['replication_verdict'].upper()}`**",
        "",
    ]

    if package["interpretation"]:
        lines += ["### Interpretation", "", package["interpretation"], ""]

    if package.get("icecube_diagnostics_label"):
        lines += [
            f"IceCube Stage 12 robustness diagnostic label: **{package['icecube_diagnostics_label']}**",
            "",
        ]

    if package["caveats"]:
        lines += ["### Caveats", ""]
        for c in package["caveats"]:
            lines.append(f"- {c}")
        lines.append("")

    lines += [
        "---",
        "",
        "## Which Catalogs Support / Do Not Support Replication",
        "",
    ]

    for e in package["catalog_entries"]:
        if not e["available"]:
            lines.append(f"- **{e['label']}**: _not available_")
            continue
        tier = (e.get("tier") or "unknown").lower()
        if "anomaly" in tier and "no_anomaly" not in tier:
            lines.append(f"- **{e.get('catalog', e['label'])}**: shows anomaly-like deviation (`{tier}`)")
        else:
            lines.append(f"- **{e.get('catalog', e['label'])}**: does NOT show anomaly-like deviation (`{tier}`)")
    lines.append("")

    lines += [
        "---",
        "",
        "## Is the Current State Publishable?",
        "",
        f"**Gate verdict: `{package['gate_verdict'].upper()}`**",
        "",
        "Publishable internally: " + ("**Yes** — suitable as a candidate internal first-results note." if package["publishable_internal"] else "**No** — the following required conditions are not yet met."),
        "",
    ]

    if package["failing_required_gates"]:
        lines += ["Failing required gates:", ""]
        for g in package["failing_required_gates"]:
            lines.append(f"- `{g}`")
        lines.append("")

    lines += [
        "---",
        "",
        "## What Must Be Fixed Next",
        "",
    ]
    for b in package["blockers"]:
        lines.append(f"1. {b}")

    lines += [
        "",
        "---",
        "",
        "This brief is generated automatically from pipeline outputs.",
        "Do not circulate outside the immediate project team without external review.",
    ]

    with open(md_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    return md_path
