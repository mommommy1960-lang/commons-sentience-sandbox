"""
preregistration.py
==================
Helpers for loading, validating, and recording preregistered analysis plans.

A preregistered analysis plan is a JSON file (see configs/preregistered_anisotropy_plan.json)
that locks the key analysis choices — statistics, null model, axis count, thresholds,
and multiple-testing correction — BEFORE any confirmatory run.

Goals
-----
- Machine-readable plan files prevent post-hoc specification
- Run metadata records which plan (if any) was active at execution time
- A plan hash (SHA-256) detects unregistered modifications
- This module is intentionally lightweight; it does NOT enforce workflow
  restrictions — that is a social/institutional responsibility

Usage
-----
::

    from reality_audit.data_analysis.preregistration import (
        load_preregistration_plan,
        validate_preregistration_plan,
        plan_summary_for_metadata,
        compute_plan_hash,
    )

    plan = load_preregistration_plan("configs/preregistered_anisotropy_plan.json")
    issues = validate_preregistration_plan(plan)
    meta   = plan_summary_for_metadata(plan)

Author: commons-sentience-sandbox
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from typing import Any, Dict, List, Optional

_HERE      = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))

# ---------------------------------------------------------------------------
# Default plan path
# ---------------------------------------------------------------------------
DEFAULT_PLAN_PATH = os.path.join(_REPO_ROOT, "configs", "preregistered_anisotropy_plan.json")


# ===========================================================================
# 1. Load
# ===========================================================================

def load_preregistration_plan(path: Optional[str] = None) -> Dict[str, Any]:
    """Load a preregistration plan JSON file.

    Parameters
    ----------
    path : path to the JSON file.  Defaults to DEFAULT_PLAN_PATH.

    Returns
    -------
    dict parsed from JSON.

    Raises
    ------
    FileNotFoundError if the file does not exist.
    ValueError if the file is not valid JSON.
    """
    if path is None:
        path = DEFAULT_PLAN_PATH

    path = os.path.abspath(path)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Preregistration plan not found: {path}")

    with open(path) as f:
        raw = f.read()

    try:
        plan = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Preregistration plan is not valid JSON ({path}): {exc}") from exc

    return plan


# ===========================================================================
# 2. Validate
# ===========================================================================

_REQUIRED_TOP_KEYS = [
    "hypothesis",
    "target_catalogs",
    "primary_statistics",
    "null_model",
    "axis_scan",
    "thresholds",
    "multiple_testing_correction",
    "discovery_criteria",
    "interpretation_guardrails",
    "preregistration_metadata",
]


def validate_preregistration_plan(plan: Dict[str, Any]) -> List[str]:
    """Validate a loaded preregistration plan for required fields.

    Parameters
    ----------
    plan : dict from load_preregistration_plan

    Returns
    -------
    List of issue strings.  Empty list means the plan is structurally valid.
    """
    issues: List[str] = []

    if not isinstance(plan, dict):
        issues.append("Plan must be a JSON object (dict)")
        return issues

    for key in _REQUIRED_TOP_KEYS:
        if key not in plan:
            issues.append(f"Missing required top-level key: '{key}'")

    # Hypothesis checks
    hyp = plan.get("hypothesis", {})
    if not isinstance(hyp, dict):
        issues.append("'hypothesis' must be a dict")
    else:
        if not hyp.get("name"):
            issues.append("hypothesis.name is missing or empty")
        if not hyp.get("null_hypothesis"):
            issues.append("hypothesis.null_hypothesis is missing or empty")

    # Catalog checks
    cats = plan.get("target_catalogs", [])
    if not isinstance(cats, list) or len(cats) == 0:
        issues.append("target_catalogs must be a non-empty list")
    else:
        for i, c in enumerate(cats):
            if not isinstance(c, dict):
                issues.append(f"target_catalogs[{i}] must be a dict")
                continue
            for f in ("label", "null_mode", "role"):
                if not c.get(f):
                    issues.append(f"target_catalogs[{i}] missing field '{f}'")

    # Statistics checks
    ps = plan.get("primary_statistics", [])
    if not isinstance(ps, list) or len(ps) == 0:
        issues.append("primary_statistics must be a non-empty list")

    # Null model checks
    nm = plan.get("null_model", {})
    if isinstance(nm, dict):
        if not nm.get("primary"):
            issues.append("null_model.primary is missing")
        try:
            reps = int(nm.get("null_repeats", 0))
            if reps < 100:
                issues.append(f"null_model.null_repeats ({reps}) is below recommended minimum of 100")
        except (TypeError, ValueError):
            issues.append("null_model.null_repeats must be an integer")

    # Thresholds checks
    thr = plan.get("thresholds", {})
    if isinstance(thr, dict):
        for k in ("exclusion_percentile", "discovery_percentile"):
            v = thr.get(k)
            try:
                fv = float(v)
                if not (0.0 < fv < 1.0):
                    issues.append(f"thresholds.{k} ({v}) must be between 0 and 1")
            except (TypeError, ValueError):
                issues.append(f"thresholds.{k} must be a float between 0 and 1")

    # Multiple testing checks
    mtc = plan.get("multiple_testing_correction", {})
    if isinstance(mtc, dict):
        method = mtc.get("method", "")
        if method not in ("bonferroni", "holm", "none", ""):
            issues.append(f"multiple_testing_correction.method '{method}' not in (bonferroni, holm, none)")

    # Guardrails
    grails = plan.get("interpretation_guardrails", [])
    if not isinstance(grails, list) or len(grails) == 0:
        issues.append("interpretation_guardrails must be a non-empty list")

    return issues


# ===========================================================================
# 3. Hash
# ===========================================================================

def compute_plan_hash(plan: Dict[str, Any]) -> str:
    """Compute a SHA-256 hash of the canonical JSON form of a plan.

    The hash is deterministic: keys are sorted, separators are compact.
    It can be used to detect post-registration modifications to the plan file.

    Parameters
    ----------
    plan : dict (preregistration plan)

    Returns
    -------
    hex string (64 chars)
    """
    canonical = json.dumps(plan, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ===========================================================================
# 4. Metadata summary for run records
# ===========================================================================

def plan_summary_for_metadata(
    plan: Dict[str, Any],
    plan_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Return a compact summary of the plan suitable for inclusion in run metadata.

    Parameters
    ----------
    plan      : loaded preregistration plan dict
    plan_path : optional path to the plan file (stored for traceability)

    Returns
    -------
    Dict with keys:
        plan_path          – str or None
        hypothesis_name    – str
        primary_statistics – list
        null_model         – str
        null_repeats       – int
        axis_count         – int
        n_target_catalogs  – int
        mtc_method         – str
        discovery_pct      – float or None
        plan_hash_sha256   – str (64-char hex)
        locked             – bool
    """
    hyp_name = plan.get("hypothesis", {}).get("name", "unknown")
    ps       = plan.get("primary_statistics", [])
    nm       = plan.get("null_model", {})
    ax       = plan.get("axis_scan", {})
    thr      = plan.get("thresholds", {})
    mtc      = plan.get("multiple_testing_correction", {})
    cats     = plan.get("target_catalogs", [])
    locked   = bool(plan.get("_locked", False))

    try:
        disc_pct = float(thr.get("discovery_percentile"))
    except (TypeError, ValueError):
        disc_pct = None

    return {
        "plan_path":          plan_path,
        "hypothesis_name":    hyp_name,
        "primary_statistics": list(ps),
        "null_model":         nm.get("primary", "isotropic"),
        "null_repeats":       nm.get("null_repeats", 0),
        "axis_count":         ax.get("axis_count", 48),
        "n_target_catalogs":  len(cats),
        "mtc_method":         mtc.get("method", "none"),
        "discovery_pct":      disc_pct,
        "plan_hash_sha256":   compute_plan_hash(plan),
        "locked":             locked,
    }
