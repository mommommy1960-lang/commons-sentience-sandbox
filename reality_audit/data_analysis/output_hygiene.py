"""
output_hygiene.py
=================
Output-directory classification and hygiene reporting for the Reality Audit
public anisotropy program.

Purpose
-------
Separate meaningful deliverables from smoke artifacts, transient test outputs,
and unrelated clutter — without auto-deleting or auto-moving anything.

This module:
  1. Walks the outputs directory and classifies each item by pattern.
  2. Produces a JSON + Markdown report with classification and path list.
  3. Optionally suggests .gitignore additions to suppress smoke directories.

Classifications
---------------
- ``deliverable``     : tracked pipeline output tied to a named stage run
- ``smoke``           : output from exploratory/smoke test runs (not for tracking)
- ``transient_plot``  : PNG images that regenerate on demand
- ``benchmark``       : synthetic or benchmark run output (not real-data result)
- ``legacy``          : outputs from pre-Stage-8 experiments unrelated to the
                        current anisotropy program
- ``unknown``         : unclassified

Safety
------
This module does NOT delete or move files.
All modifications to the workspace must be performed by the user manually.

Author: commons-sentience-sandbox
"""

from __future__ import annotations

import datetime
import json
import os
from typing import Any, Dict, List, Optional, Tuple

_HERE      = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))

# ---------------------------------------------------------------------------
# Classification patterns
# ---------------------------------------------------------------------------

# Deliverable directory-name substrings
_DELIVERABLE_PATTERNS = [
    "stage9_fermi_exposure_corrected",
    "stage10_swift_first_results",
    "stage11_icecube_first_results",
    "stage11_icecube_final",
    "stage11_icecube_trialcorr",
    "stage12_icecube_diagnostics",
    "stage12_icecube_confirmatory",
    "stage10_first_results/comparison",
    "stage10_first_results\\comparison",
]

# Deliverable file-extension and name patterns
_DELIVERABLE_FILE_SUFFIXES = (
    "_summary.json",
    "_memo.md",
    "_comparison.json",
    "_manifest.json",
    "_results.csv",
    "_brief.md",
    "_brief.json",
    "publication_gate.json",
    "publication_gate_report.md",
    "metric_stability_table.csv",
    "first_results_brief",
)

# Smoke / exploratory directory-name substrings
_SMOKE_PATTERNS = [
    "smoke",
    "_test_dataset",
    "stage8_real_first_results",
    "stage8_first_results/stage8_first_results",
    "stage8_first_results\\stage8_first_results",
    "stage9_fermi_isotropic_compare",
    "stage11_first_results/stage11_icecube_first",   # exploratory variant
    "stage8_real_test",
]

# Benchmark directories
_BENCHMARK_PATTERNS = [
    "public_anisotropy_benchmark",
    "synth_baseline",
    "synth_isotropic",
    "synth_preferred_axis",
    "simulation_signature",
    "toy_experiments",
]

# Legacy / unrelated directories (pre-Stage-8)
_LEGACY_PATTERNS = [
    "baselines/",
    "discretization_audit",
    "observer_effect_audit",
    "preferred_frame_audit",
    "public_anisotropy/real_fermi_lat_grb",
]

# Transient plot extensions
_PLOT_EXTENSIONS = {".png", ".svg", ".pdf"}


def _classify_path(rel_path: str, is_dir: bool) -> str:
    """Return classification label for a relative path."""
    norm = rel_path.replace("\\", "/")

    # Legacy first (these overlap with many keywords)
    for pat in _LEGACY_PATTERNS:
        if pat in norm:
            return "legacy"

    # Benchmark
    for pat in _BENCHMARK_PATTERNS:
        if pat in norm:
            return "benchmark"

    # Smoke
    for pat in _SMOKE_PATTERNS:
        if pat in norm:
            return "smoke"

    # Deliverable directories
    for pat in _DELIVERABLE_PATTERNS:
        if pat in norm:
            return "deliverable"

    # Deliverable files
    if not is_dir:
        _, ext = os.path.splitext(norm.lower())
        if ext in _PLOT_EXTENSIONS:
            return "transient_plot"
        for suffix in _DELIVERABLE_FILE_SUFFIXES:
            if norm.endswith(suffix):
                return "deliverable"

    return "unknown"


# ===========================================================================
# 1. Classify output paths
# ===========================================================================

def classify_output_paths(base_dir: Optional[str] = None) -> Dict[str, Any]:
    """Walk the outputs directory and classify every file and subdirectory.

    Parameters
    ----------
    base_dir : str, optional
        Root directory to classify. Defaults to ``outputs/`` under repo root.

    Returns
    -------
    dict with keys:
        base_dir : str
        deliverable : list[str]
        smoke : list[str]
        transient_plot : list[str]
        benchmark : list[str]
        legacy : list[str]
        unknown : list[str]
        summary : dict
    """
    if base_dir is None:
        base_dir = os.path.join(_REPO_ROOT, "outputs")

    base_dir = os.path.abspath(base_dir)

    result: Dict[str, List[str]] = {
        "deliverable":    [],
        "smoke":          [],
        "transient_plot": [],
        "benchmark":      [],
        "legacy":         [],
        "unknown":        [],
    }

    for dirpath, dirnames, filenames in os.walk(base_dir):
        # Classify this directory
        rel_dir = os.path.relpath(dirpath, _REPO_ROOT)
        dir_cls = _classify_path(rel_dir, is_dir=True)

        # Classify files in this directory
        for fname in sorted(filenames):
            rel_file = os.path.join(rel_dir, fname).replace("\\", "/")
            file_cls = _classify_path(rel_file, is_dir=False)
            # If parent dir already classified as smoke/benchmark/legacy, inherit
            if dir_cls in ("smoke", "benchmark", "legacy") and file_cls == "unknown":
                file_cls = dir_cls
            result[file_cls].append(rel_file)

    # Sort each list
    for k in result:
        result[k] = sorted(result[k])

    summary = {cat: len(paths) for cat, paths in result.items()}
    summary["total_files"] = sum(summary.values())

    return {
        "base_dir":       base_dir,
        "generated_at":   datetime.datetime.utcnow().isoformat() + "Z",
        "deliverable":    result["deliverable"],
        "smoke":          result["smoke"],
        "transient_plot": result["transient_plot"],
        "benchmark":      result["benchmark"],
        "legacy":         result["legacy"],
        "unknown":        result["unknown"],
        "summary":        summary,
    }


# ===========================================================================
# 2. Write hygiene report
# ===========================================================================

def write_output_hygiene_report(
    classification: Dict[str, Any],
    output_dir: str,
    name: str = "stage13_output_hygiene",
) -> str:
    """Write the output hygiene classification as JSON and Markdown.

    Parameters
    ----------
    classification : dict
        Output of ``classify_output_paths``.
    output_dir : str
        Directory to write reports.
    name : str
        Base filename.

    Returns
    -------
    str : path to the Markdown report.
    """
    os.makedirs(output_dir, exist_ok=True)

    # JSON
    json_path = os.path.join(output_dir, f"{name}.json")
    with open(json_path, "w") as f:
        json.dump(classification, f, indent=2)

    # Suggested .gitignore additions
    gitignore_suggestions = _suggest_gitignore(classification.get("smoke", []))

    # Markdown
    md_path = os.path.join(output_dir, f"{name}_report.md")
    s = classification["summary"]
    lines: List[str] = [
        "# Output Hygiene Report",
        "",
        f"Generated: {classification.get('generated_at', 'unknown')}",
        f"Base directory: `{classification['base_dir']}`",
        "",
        "## Summary",
        "",
        "| Category | Count |",
        "|---|---|",
        f"| deliverable | {s['deliverable']} |",
        f"| smoke | {s['smoke']} |",
        f"| transient_plot | {s['transient_plot']} |",
        f"| benchmark | {s['benchmark']} |",
        f"| legacy | {s['legacy']} |",
        f"| unknown | {s['unknown']} |",
        f"| **total** | **{s['total_files']}** |",
        "",
        "---",
        "",
    ]

    for cat, label in [
        ("deliverable",    "Deliverable Files (keep, track)"),
        ("smoke",          "Smoke / Exploratory Outputs (can be ignored or removed)"),
        ("transient_plot", "Transient Plots (regeneratable — can be .gitignored)"),
        ("benchmark",      "Benchmark / Synthetic Outputs"),
        ("legacy",         "Legacy Outputs (pre-Stage-8, unrelated to current program)"),
        ("unknown",        "Unclassified Files"),
    ]:
        paths = classification.get(cat, [])
        if not paths:
            continue
        lines += [f"## {label}", "", f"_{len(paths)} file(s)_", ""]
        for p in paths[:60]:   # cap to avoid enormous reports
            lines.append(f"- `{p}`")
        if len(paths) > 60:
            lines.append(f"- … and {len(paths) - 60} more (see JSON for full list)")
        lines.append("")

    if gitignore_suggestions:
        lines += [
            "---",
            "",
            "## Suggested .gitignore Additions",
            "",
            "The following smoke output directories are not currently tracked",
            "and could be added to `.gitignore` to prevent accidental staging:",
            "",
        ]
        for s_line in gitignore_suggestions:
            lines.append(f"```")
            lines.append(s_line)
            lines.append(f"```")
        lines.append("")

    lines += [
        "---",
        "",
        "**No files have been deleted or moved by this report.**",
        "All actions are the responsibility of the project maintainer.",
    ]

    with open(md_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    return md_path


def _suggest_gitignore(smoke_paths: List[str]) -> List[str]:
    """Return top-level smoke directory patterns suitable for .gitignore."""
    dirs: set = set()
    for p in smoke_paths:
        parts = p.replace("\\", "/").split("/")
        if len(parts) >= 2:
            # outputs/<dir>/<...>
            dirs.add("/".join(parts[:3]) + "/")
    return sorted(dirs)
