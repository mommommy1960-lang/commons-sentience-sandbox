"""
publication_gate.py
===================
Publication-readiness gate for the Reality Audit public anisotropy program.

Purpose
-------
Evaluate whether current run metadata, comparison summaries, and diagnostics
meet the minimum standards to be circulated internally or submitted for external
scientific review.

The gate is intentionally conservative: it flags every missing or weak condition
and provides a labeled readiness verdict.

Readiness verdicts
------------------
- ``not_ready``                  : required gates are failing
- ``internally_reviewable``      : all required gates pass
- ``candidate_first_results_note``: required + recommended gates pass
- ``ready_for_external_review``  : all gates pass, external review initiated

Usage
-----
::

    from reality_audit.data_analysis.publication_gate import (
        load_publication_gate,
        evaluate_publication_gate,
        write_publication_gate_report,
    )

    gate_config = load_publication_gate("configs/publication_gate_checklist.json")
    result = evaluate_publication_gate(run_metadata, comparison_summary,
                                       diagnostics_summary=diag, gate_config=gate_config)
    report_path = write_publication_gate_report(result, "outputs/stage13")

Author: commons-sentience-sandbox
"""

from __future__ import annotations

import datetime
import json
import os
from typing import Any, Dict, List, Optional

from reality_audit.data_analysis.exposure_quality_tiers import (
    TIER_NONE,
    TIER_CANDIDATE,
    TIER_ORDER,
    worst_tier as _worst_tier,
    best_tier as _best_tier,
)

_HERE      = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))

DEFAULT_GATE_PATH = os.path.join(_REPO_ROOT, "configs", "publication_gate_checklist.json")

# ---------------------------------------------------------------------------
# Readiness ordering (higher index = more ready)
# ---------------------------------------------------------------------------
_READINESS_ORDER = [
    "not_ready",
    "internally_reviewable",
    "candidate_first_results_note",
    "ready_for_external_review",
]

# Null modes considered appropriate per instrument keyword
_APPROPRIATE_NULL_MODES: Dict[str, str] = {
    "fermi": "exposure_corrected",
    "swift": "exposure_corrected",
    "icecube": "isotropic",
}

# Metaphysical keyword list (lower-cased)
_METAPHYSICAL_TERMS = [
    "consciousness", "sentience", "intentional", "mind", "psychic",
    "psi", "telekinesis", "entanglement implies", "wavefunction collapse implies",
    "quantum consciousness", "observer effect causes",
]


# ===========================================================================
# 1. Load
# ===========================================================================

def load_publication_gate(path: Optional[str] = None) -> Dict[str, Any]:
    """Load the publication gate checklist JSON.

    Parameters
    ----------
    path : str, optional
        Path to checklist JSON. Defaults to DEFAULT_GATE_PATH.

    Returns
    -------
    dict
    """
    if path is None:
        path = DEFAULT_GATE_PATH
    path = os.path.abspath(path)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Publication gate config not found: {path}")
    with open(path) as f:
        return json.load(f)


# ===========================================================================
# 2. Evaluate
# ===========================================================================

def evaluate_exposure_quality_for_gate(
    catalogs: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Assess exposure quality tier for each catalog and return a summary dict.

    Parameters
    ----------
    catalogs : list[dict]
        Catalog metadata dicts (each entry from the run_metadata "catalogs" list).

    Returns
    -------
    dict with keys:
      - worst_exposure_quality_tier        : str
      - any_catalog_at_analysis_candidate  : bool
      - tier_by_catalog                    : dict[str, str]
      - notes                              : list[str]
    """
    tier_by_catalog: Dict[str, str] = {}

    for cat in catalogs:
        label = (cat.get("catalog") or cat.get("label") or "unknown").lower()
        tier = cat.get("exposure_quality_tier")
        if not tier:
            try:
                from reality_audit.data_analysis.mission_calibration_loader import (
                    load_calibration_product,
                )
                result = load_calibration_product(label)
                tier = result.get("exposure_quality_tier", TIER_NONE)
            except Exception:
                tier = TIER_NONE
        tier_by_catalog[label] = tier or TIER_NONE

    all_tiers = list(tier_by_catalog.values()) or [TIER_NONE]
    _worst = _worst_tier(all_tiers)
    _cand_idx = TIER_ORDER.index(TIER_CANDIDATE)
    any_at_candidate = any(
        TIER_ORDER.index(t) >= _cand_idx for t in all_tiers
    )

    notes: List[str] = []
    synthetic = [l for l, t in tier_by_catalog.items() if t == "synthetic_sample"]
    partial   = [l for l, t in tier_by_catalog.items() if t == "partial_data_derived"]
    candidate = [l for l, t in tier_by_catalog.items() if t == "analysis_candidate"]
    grade     = [l for l, t in tier_by_catalog.items() if t == "analysis_grade"]
    none_cat  = [l for l, t in tier_by_catalog.items() if t == TIER_NONE]

    if synthetic:
        notes.append(f"synthetic sample only: {synthetic}")
    if partial:
        notes.append(f"partial derived exposure: {partial}")
    if candidate:
        notes.append(f"analysis-candidate exposure: {candidate}")
    if grade:
        notes.append(f"analysis-grade exposure: {grade}")
    if none_cat:
        notes.append(f"no exposure data (tier=none): {none_cat}")

    return {
        "worst_exposure_quality_tier":       _worst,
        "any_catalog_at_analysis_candidate": any_at_candidate,
        "tier_by_catalog":                   tier_by_catalog,
        "notes":                             notes,
    }


def evaluate_publication_gate(
    run_metadata: Dict[str, Any],
    comparison_summary: Dict[str, Any],
    diagnostics_summary: Optional[Dict[str, Any]] = None,
    gate_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Evaluate the publication gate against current pipeline outputs.

    Parameters
    ----------
    run_metadata : dict
        Stage 8 run bundle metadata (may include multiple catalogs as a list
        under "catalogs" or just a single run block).
    comparison_summary : dict
        Loaded three-catalog comparison JSON.
    diagnostics_summary : dict, optional
        Stage 12 IceCube diagnostics summary.
    gate_config : dict, optional
        Loaded gate checklist. Loaded from default path if None.

    Returns
    -------
    dict with keys:
        verdict : str
        gates   : list[dict]  — per-gate pass/fail/info records
        failing_required : list[str]
        failing_recommended : list[str]
        notes : list[str]
    """
    if gate_config is None:
        gate_config = load_publication_gate()

    gates_cfg = {g["id"]: g for g in gate_config.get("gates", [])}
    gate_results: List[Dict[str, Any]] = []

    def _gate(gate_id: str, passed: bool, detail: str) -> None:
        cfg = gates_cfg.get(gate_id, {})
        gate_results.append({
            "id": gate_id,
            "severity": cfg.get("severity", "required"),
            "description": cfg.get("description", ""),
            "passed": passed,
            "detail": detail,
        })

    # Flatten catalogs list if present
    catalogs: List[Dict[str, Any]] = run_metadata.get("catalogs", [])
    if not catalogs:
        # Single-catalog bundle
        catalogs = [run_metadata]

    # -----------------------------------------------------------------------
    # Gate: prereg_present
    # -----------------------------------------------------------------------
    any_prereg = any(
        c.get("preregistration_plan") or c.get("preregistration_hash")
        for c in catalogs
    )
    _gate("prereg_present", any_prereg,
          "Found preregistration plan in metadata." if any_prereg
          else "No preregistration plan recorded in any catalog metadata.")

    # -----------------------------------------------------------------------
    # Gate: prereg_locked
    # -----------------------------------------------------------------------
    any_locked = any(
        c.get("preregistration_locked") for c in catalogs
    )
    _gate("prereg_locked", any_locked,
          "At least one run has a locked preregistration plan." if any_locked
          else "No locked preregistration plan (_locked: true) found.")

    # -----------------------------------------------------------------------
    # Gate: null_model_appropriate
    # -----------------------------------------------------------------------
    null_issues: List[str] = []
    for cat in catalogs:
        cname = (cat.get("catalog") or "").lower()
        null  = (cat.get("null_mode") or "").lower()
        for key, expected in _APPROPRIATE_NULL_MODES.items():
            if key in cname and null and null != expected:
                null_issues.append(f"{cname}: got '{null}', expected '{expected}'")
    _gate("null_model_appropriate", not null_issues,
          "All catalogs use appropriate null models." if not null_issues
          else f"Null-model mismatches: {'; '.join(null_issues)}")

    # -----------------------------------------------------------------------
    # Gate: trial_correction_applied
    # -----------------------------------------------------------------------
    correction_ok = any(
        (c.get("trial_correction_method") or "none").lower() != "none"
        for c in catalogs
    )
    methods = [c.get("trial_correction_method") for c in catalogs if c.get("trial_correction_method")]
    _gate("trial_correction_applied", correction_ok,
          f"Trial correction applied: {methods}." if correction_ok
          else "No trial-factor correction applied (method=none or absent).")

    # -----------------------------------------------------------------------
    # Gate: at_least_two_catalogs
    # -----------------------------------------------------------------------
    n_cats = len(comparison_summary.get("catalog_rows", []))
    if n_cats < 2:
        # Try two-catalog fields
        n_cats = 2 if comparison_summary.get("catalog_a") and comparison_summary.get("catalog_b") else n_cats
    _gate("at_least_two_catalogs", n_cats >= 2,
          f"Found {n_cats} catalogs in comparison." if n_cats >= 2
          else "Fewer than two catalogs in comparison summary.")

    # -----------------------------------------------------------------------
    # Gate: replication_status_labeled
    # -----------------------------------------------------------------------
    verdict = (comparison_summary.get("consistency_verdict") or "").lower()
    has_verdict = bool(verdict)
    _gate("replication_status_labeled", has_verdict,
          f"Replication verdict: '{verdict}'." if has_verdict
          else "No consistency_verdict found in comparison summary.")

    # -----------------------------------------------------------------------
    # Gate: systematics_documented
    # -----------------------------------------------------------------------
    caveats = comparison_summary.get("caveats", [])
    has_caveats = bool(caveats)
    _gate("systematics_documented", has_caveats,
          f"{len(caveats)} caveat(s) documented." if has_caveats
          else "No caveats found in comparison summary.")

    # -----------------------------------------------------------------------
    # Gate: output_artifacts_complete
    # -----------------------------------------------------------------------
    all_have_tier = all(cat.get("tier") for cat in catalogs)
    comparison_has_verdict = bool(comparison_summary.get("consistency_verdict"))
    artifacts_ok = all_have_tier and comparison_has_verdict
    _gate("output_artifacts_complete", artifacts_ok,
          "Summary JSON and comparison output appear complete." if artifacts_ok
          else "Some output artifacts appear missing (tier or verdict absent).")

    # -----------------------------------------------------------------------
    # Gate: comparison_memo_present
    # -----------------------------------------------------------------------
    memo_note = comparison_summary.get("memo_path") or comparison_summary.get("interpretation")
    _gate("comparison_memo_present", bool(memo_note),
          "Comparison interpretation/memo is present." if memo_note
          else "No comparison memo or interpretation found.")

    # -----------------------------------------------------------------------
    # Gate: no_metaphysical_language
    # -----------------------------------------------------------------------
    interp_text = (comparison_summary.get("interpretation") or "").lower()
    found_meta = [t for t in _METAPHYSICAL_TERMS if t in interp_text]
    _gate("no_metaphysical_language", not found_meta,
          "No metaphysical language detected in interpretation." if not found_meta
          else f"Metaphysical terms found: {found_meta}")

    # -----------------------------------------------------------------------
    # Gate: external_review_pending (informational)
    # -----------------------------------------------------------------------
    _gate("external_review_pending", False,
          "External review has not yet been initiated (expected — this is a status flag).")

    # -----------------------------------------------------------------------
    # Gate: icecube_small_n_acknowledged (recommended)
    # -----------------------------------------------------------------------
    has_icecube = any("icecube" in (c.get("catalog") or "").lower() for c in catalogs)
    small_n_ok = True
    if has_icecube:
        small_n_ok = any("small" in (c or "").lower() for c in caveats)
    _gate("icecube_small_n_acknowledged", small_n_ok,
          "IceCube small-N limitation acknowledged in caveats." if small_n_ok
          else "IceCube catalog present but no small-N caveat found.")

    # -----------------------------------------------------------------------
    # Gate: exposure_quality_documented (recommended)
    # -----------------------------------------------------------------------
    eq_summary = evaluate_exposure_quality_for_gate(catalogs)
    # A tier is considered undocumented only if the value is literally None
    # (which evaluate_exposure_quality_for_gate never emits — it defaults to
    # TIER_NONE = "none" — but we guard defensively against future changes).
    undocumented = [
        label for label, tier in eq_summary["tier_by_catalog"].items()
        if tier is None or tier == ""
    ]
    _gate(
        "exposure_quality_documented",
        not undocumented,
        "All catalogs have an explicit exposure quality tier (even if 'none')."
        if not undocumented
        else f"Catalogs with undocumented exposure quality: {undocumented}",
    )

    # -----------------------------------------------------------------------
    # Derive readiness verdict
    # -----------------------------------------------------------------------
    required_fails = [g["id"] for g in gate_results
                      if g["severity"] == "required" and g["id"] != "external_review_pending" and not g["passed"]]
    recommended_fails = [g["id"] for g in gate_results
                         if g["severity"] == "recommended" and not g["passed"]]

    if required_fails:
        overall = "not_ready"
    elif recommended_fails:
        overall = "internally_reviewable"
    else:
        # Check informational gate: external review
        ext_passed = any(g for g in gate_results if g["id"] == "external_review_pending" and g["passed"])
        overall = "ready_for_external_review" if ext_passed else "candidate_first_results_note"

    notes: List[str] = []
    if diagnostics_summary:
        label = diagnostics_summary.get("robustness_label") or diagnostics_summary.get("label")
        if label:
            notes.append(f"IceCube robustness diagnostics label: {label}")
    if verdict:
        notes.append(f"Cross-catalog replication verdict: {verdict}")

    return {
        "verdict": overall,
        "readiness_description": gate_config.get("readiness_levels", {}).get(overall, overall),
        "gates": gate_results,
        "failing_required": required_fails,
        "failing_recommended": recommended_fails,
        "notes": notes,
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "exposure_quality_summary": {
            "worst_exposure_quality_tier":       eq_summary["worst_exposure_quality_tier"],
            "any_catalog_at_analysis_candidate": eq_summary["any_catalog_at_analysis_candidate"],
            "tier_by_catalog":                   eq_summary["tier_by_catalog"],
            "notes":                             eq_summary["notes"],
        },
    }


# ===========================================================================
# 3. Write report
# ===========================================================================

def write_publication_gate_report(
    result: Dict[str, Any],
    output_dir: str,
    name: str = "stage13_publication_gate",
) -> str:
    """Write publication gate result as JSON and Markdown report.

    Parameters
    ----------
    result : dict
        Output of ``evaluate_publication_gate``.
    output_dir : str
        Directory to write outputs.
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
        json.dump(result, f, indent=2)

    # Markdown
    md_path = os.path.join(output_dir, f"{name}_report.md")
    lines: List[str] = [
        f"# Publication Readiness Gate Report",
        f"",
        f"Generated: {result.get('generated_at', 'unknown')}",
        f"",
        f"## Overall Verdict",
        f"",
        f"**{result['verdict'].upper()}**",
        f"",
        f"_{result.get('readiness_description', '')}_",
        f"",
    ]
    if result["failing_required"]:
        lines += [
            f"## Failing Required Gates",
            f"",
        ]
        for g in result["failing_required"]:
            lines.append(f"- `{g}`")
        lines.append("")

    if result["failing_recommended"]:
        lines += [
            f"## Failing Recommended Gates",
            f"",
        ]
        for g in result["failing_recommended"]:
            lines.append(f"- `{g}`")
        lines.append("")

    lines += [
        f"## Gate Details",
        f"",
        f"| Gate | Severity | Passed | Detail |",
        f"|---|---|---|---|",
    ]
    for g in result["gates"]:
        icon = "YES" if g["passed"] else "NO"
        lines.append(f"| `{g['id']}` | {g['severity']} | {icon} | {g['detail']} |")

    if result["notes"]:
        lines += ["", "## Notes", ""]
        for n in result["notes"]:
            lines.append(f"- {n}")

    lines += [
        "",
        "---",
        "",
        "This is an internal pipeline readiness report.",
        "It is not a scientific claim and does not substitute for external review.",
    ]

    with open(md_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    return md_path
