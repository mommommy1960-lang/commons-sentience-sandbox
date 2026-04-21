"""
catalog_comparison.py
=====================
Cross-catalog comparison utilities for the Reality Audit public anisotropy pipeline.

This module provides tools to compare results from two independent real catalogs
run through the same Stage 8/9 pipeline and to generate a concise comparison memo.

Motivation
----------
A single-catalog anisotropy result is hypothesis-generating at best.  A genuine
sky-position signal should persist across independent instruments and source
populations.  If a pattern appears in Fermi GBM GRBs but not in Swift BAT GRBs,
the most parsimonious explanation is instrument acceptance geometry, not a
physical sky asymmetry.

Usage
-----
::

    from reality_audit.data_analysis.catalog_comparison import (
        load_stage_results,
        compare_catalog_results,
        write_catalog_comparison_memo,
    )

    result_a = load_stage_results("outputs/stage9_first_results/fermi/fermi_summary.json")
    result_b = load_stage_results("outputs/stage10_first_results/swift/swift_summary.json")
    comparison = compare_catalog_results(result_a, result_b)
    write_catalog_comparison_memo(comparison, "outputs/stage10_first_results/comparison")

Author: commons-sentience-sandbox
"""

from __future__ import annotations

import datetime
import json
import os
import sys
from typing import Any, Dict, List, Optional

_HERE      = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


# ===========================================================================
# 1. Load a Stage 7/8/9 summary JSON
# ===========================================================================

def load_stage_results(summary_json_path: str) -> Dict[str, Any]:
    """Load a Stage 7/8/9 summary JSON file into a normalised dict.

    The summary JSON is written by ``write_public_study_artifacts`` and contains
    top-level keys: experiment, catalog, written_at, results, coverage, config.

    Parameters
    ----------
    summary_json_path : path to a ``*_summary.json`` artifact.

    Returns
    -------
    Dict with keys:
        path             – absolute file path loaded
        catalog          – catalog name string
        event_count      – int
        events_with_position – int
        null_mode        – str
        hemi_score       – float | None
        hemi_percentile  – float | None
        axis_score       – float | None
        axis_percentile  – float | None
        tier             – str
        max_percentile   – float | None
        run_metadata     – dict (from results["run_metadata"])
        _raw             – full raw dict for custom access
    """
    path = os.path.abspath(summary_json_path)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Summary JSON not found: {path}")

    with open(path) as f:
        raw = json.load(f)

    results = raw.get("results", {})
    nc      = results.get("null_comparison", {})
    sig     = results.get("signal_evaluation", {})
    ani     = results.get("anisotropy", {})
    pa      = results.get("preferred_axis", {})
    rm      = results.get("run_metadata", {})

    return {
        "path":                path,
        "catalog":             raw.get("catalog", os.path.basename(path)),
        "event_count":         results.get("event_count", 0),
        "events_with_position": results.get("events_with_position", 0),
        "null_mode":           nc.get("null_mode", rm.get("null_mode", "unknown")),
        "hemi_score":          ani.get("hemisphere_imbalance"),
        "hemi_percentile":     nc.get("hemi_percentile"),
        "axis_score":          pa.get("score"),
        "axis_percentile":     nc.get("axis_percentile"),
        "tier":                sig.get("tier", "unknown"),
        "max_percentile":      sig.get("max_percentile"),
        "run_metadata":        rm,
        "_raw":                raw,
    }


# ===========================================================================
# 2. Compare two catalog results
# ===========================================================================

def compare_catalog_results(
    result_a: Dict[str, Any],
    result_b: Dict[str, Any],
) -> Dict[str, Any]:
    """Compare anisotropy results from two independent catalogs.

    Parameters
    ----------
    result_a, result_b : dicts produced by ``load_stage_results``.

    Returns
    -------
    Dict with keys:
        catalog_a / catalog_b   – catalog name strings
        event_count_a / b       – int
        null_mode_a / b         – str
        hemi_percentile_a / b   – float | None
        axis_percentile_a / b   – float | None
        tier_a / tier_b         – str
        tiers_agree             – bool (same tier)
        both_anomaly            – bool (both ≥ "weak_anomaly")
        neither_anomaly         – bool (both = "no_anomaly")
        max_percentile_delta    – float | None (|a - b|)
        consistency_verdict     – "consistent_null" | "partial_agreement" | "inconsistent"
        interpretation          – str (human-readable paragraph)
        caveats                 – list[str]
        timestamp               – ISO-8601 string
    """
    def _pct(r, key):
        v = r.get(key)
        if v is None:
            return None
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    _tier_rank = {
        "no_anomaly_detected":         0,
        "no_anomaly":                  0,
        "weak_anomaly_like_deviation": 1,
        "weak_anomaly":                1,
        "moderate_anomaly_like_deviation": 2,
        "moderate_anomaly":            2,
        "strong_anomaly_like_deviation": 3,
        "strong_anomaly":              3,
        "unknown":                     -1,
    }

    tier_a = result_a.get("tier", "unknown")
    tier_b = result_b.get("tier", "unknown")
    rank_a = _tier_rank.get(tier_a, -1)
    rank_b = _tier_rank.get(tier_b, -1)

    tiers_agree    = (tier_a == tier_b)
    both_anomaly   = (rank_a >= 1 and rank_b >= 1)
    neither_anomaly = (rank_a == 0 and rank_b == 0)

    hemi_a = _pct(result_a, "hemi_percentile")
    hemi_b = _pct(result_b, "hemi_percentile")
    axis_a = _pct(result_a, "axis_percentile")
    axis_b = _pct(result_b, "axis_percentile")
    max_a  = _pct(result_a, "max_percentile")
    max_b  = _pct(result_b, "max_percentile")

    if max_a is not None and max_b is not None:
        delta = abs(max_a - max_b)
    else:
        delta = None

    # Consistency verdict
    if neither_anomaly:
        verdict = "consistent_null"
    elif both_anomaly:
        verdict = "partial_agreement"  # both show something, but tier may differ
    else:
        verdict = "inconsistent"  # one shows anomaly, one does not

    # Human-readable interpretation
    cat_a = result_a.get("catalog", "Catalog A")
    cat_b = result_b.get("catalog", "Catalog B")

    if verdict == "consistent_null":
        interpretation = (
            f"Both {cat_a} (tier: {tier_a}) and {cat_b} (tier: {tier_b}) "
            f"show no anomaly-like deviation under their respective null models. "
            f"This is the expected result for two well-understood wide-field detectors "
            f"when the correct acceptance-corrected null is used. "
            f"There is no evidence in either catalog for a catalog-independent "
            f"sky-position anisotropy."
        )
    elif verdict == "partial_agreement":
        interpretation = (
            f"Both catalogs show some anomaly-like deviation: "
            f"{cat_a} at tier={tier_a} (max percentile={max_a}), "
            f"{cat_b} at tier={tier_b} (max percentile={max_b}). "
            f"However, a shared pattern in two independently-observed catalogs warrants "
            f"deeper investigation into common systematics (e.g., galactic plane avoidance, "
            f"shared redshift selection, detector sensitivity boundaries) before "
            f"any physical interpretation is possible."
        )
    else:
        # One anomaly, one not — most likely systematic
        if rank_a > rank_b:
            anomaly_cat, null_cat = cat_a, cat_b
            anomaly_tier, null_tier = tier_a, tier_b
        else:
            anomaly_cat, null_cat = cat_b, cat_a
            anomaly_tier, null_tier = tier_b, tier_a
        interpretation = (
            f"{anomaly_cat} shows {anomaly_tier} while "
            f"{null_cat} shows {null_tier}. "
            f"Cross-catalog disagreement typically indicates an instrument-specific "
            f"systematic rather than a genuine sky-position signal. "
            f"The anomaly in {anomaly_cat} most likely reflects residual acceptance "
            f"geometry not fully corrected by the empirical null, "
            f"or a selection bias particular to that instrument. "
            f"This result does NOT support a catalog-independent anisotropy claim."
        )

    caveats = [
        "Both runs use empirical exposure-proxy nulls built from the data under test: "
        "any real signal is partially absorbed, making these tests conservative.",
        "Different catalogs have different source populations, redshift distributions, "
        "energy ranges, and trigger thresholds. Non-detection in Swift BAT does not rule "
        "out a GRB-population-wide effect undetectable by BAT.",
        "The preferred-axis scan uses 48 trial axes without a trial-factor correction; "
        "a metric significant at 90th percentile is consistent with a fluctuation.",
        "No pre-registration was filed before these runs. These are exploratory "
        "first-results packages, not confirmatory tests.",
        "N_Fermi=3000 vs N_Swift=872: unequal statistical power. The Fermi result is "
        "not directly comparable in absolute significance.",
    ]

    return {
        "catalog_a":             result_a.get("catalog"),
        "catalog_b":             result_b.get("catalog"),
        "event_count_a":         result_a.get("event_count"),
        "event_count_b":         result_b.get("event_count"),
        "events_with_pos_a":     result_a.get("events_with_position"),
        "events_with_pos_b":     result_b.get("events_with_position"),
        "null_mode_a":           result_a.get("null_mode"),
        "null_mode_b":           result_b.get("null_mode"),
        "hemi_percentile_a":     hemi_a,
        "hemi_percentile_b":     hemi_b,
        "axis_percentile_a":     axis_a,
        "axis_percentile_b":     axis_b,
        "tier_a":                tier_a,
        "tier_b":                tier_b,
        "max_percentile_a":      max_a,
        "max_percentile_b":      max_b,
        "tiers_agree":           tiers_agree,
        "both_anomaly":          both_anomaly,
        "neither_anomaly":       neither_anomaly,
        "max_percentile_delta":  delta,
        "consistency_verdict":   verdict,
        "interpretation":        interpretation,
        "caveats":               caveats,
        "timestamp":             datetime.datetime.utcnow().isoformat() + "Z",
    }


# ===========================================================================
# 3. Write comparison memo
# ===========================================================================

def write_catalog_comparison_memo(
    comparison: Dict[str, Any],
    output_dir: str,
    name: str = "stage10_catalog_comparison",
) -> str:
    """Write a Markdown comparison memo and JSON to ``output_dir``.

    Parameters
    ----------
    comparison : dict from ``compare_catalog_results``.
    output_dir : directory for output files.
    name       : base filename (without extension).

    Returns
    -------
    Path to the Markdown memo file.
    """
    os.makedirs(output_dir, exist_ok=True)
    memo_path = os.path.join(output_dir, f"{name}_memo.md")
    json_path = os.path.join(output_dir, f"{name}.json")

    # Write JSON
    with open(json_path, "w") as f:
        json.dump(comparison, f, indent=2, default=str)

    # Helpers
    def _fmt(v, digits=4):
        if v is None:
            return "N/A"
        return f"{float(v):.{digits}f}"

    cat_a   = comparison.get("catalog_a", "Catalog A")
    cat_b   = comparison.get("catalog_b", "Catalog B")
    tier_a  = comparison.get("tier_a", "unknown")
    tier_b  = comparison.get("tier_b", "unknown")
    verdict = comparison.get("consistency_verdict", "unknown")
    ts      = comparison.get("timestamp", "")

    # Verdict label
    verdict_labels = {
        "consistent_null":    "CONSISTENT — Both catalogs: No anomaly",
        "partial_agreement":  "PARTIAL AGREEMENT — Both catalogs show some deviation",
        "inconsistent":       "INCONSISTENT — Catalogs disagree",
    }
    verdict_label = verdict_labels.get(verdict, verdict.upper())

    caveats_md = "\n".join(f"- {c}" for c in comparison.get("caveats", []))

    memo = f"""# Stage 10: Cross-Catalog Comparison Memo

**Internal first-results artifact — not a scientific publication.**
*Generated: {ts}*

---

## Verdict: {verdict_label}

---

## Catalog Comparison Table

| Field | {cat_a} | {cat_b} |
|-------|---------|---------|
| Event count | {comparison.get("event_count_a")} | {comparison.get("event_count_b")} |
| Events with position | {comparison.get("events_with_pos_a")} | {comparison.get("events_with_pos_b")} |
| Null model | {comparison.get("null_mode_a")} | {comparison.get("null_mode_b")} |
| Hemisphere imbalance (pct) | {_fmt(comparison.get("hemi_percentile_a"))} | {_fmt(comparison.get("hemi_percentile_b"))} |
| Preferred-axis score (pct) | {_fmt(comparison.get("axis_percentile_a"))} | {_fmt(comparison.get("axis_percentile_b"))} |
| Max percentile | {_fmt(comparison.get("max_percentile_a"))} | {_fmt(comparison.get("max_percentile_b"))} |
| Interpretation tier | `{tier_a}` | `{tier_b}` |

---

## Interpretation

{comparison.get("interpretation", "")}

---

## Does this support a catalog-independent anisotropy claim?

{"**No.** The catalogs disagree in interpretation tier. Cross-catalog disagreement is the expected signature of instrument-specific systematics, not a genuine sky signal." if verdict == "inconsistent" else ""}
{"**No.** Neither catalog shows an anomaly under the corrected null. The Fermi GBM Stage 8 strong anomaly (isotropic null) was confirmed as an acceptance artefact." if verdict == "consistent_null" else ""}
{"**Not yet.** Both catalogs show some deviation, but the nature of the shared pattern must be investigated for common systematics before any physical claim." if verdict == "partial_agreement" else ""}

**Current status:** These are internal first-results packages. No pre-registration has been filed. The results are **hypothesis-generating only** — they do not constitute evidence for or against any physical or metaphysical claim.

---

## Caveats

{caveats_md}

---

## Next Steps

1. Obtain a proper instrument-response exposure map (e.g. Fermi GBM FSSC FITS file) for a
   model-based null rather than the empirical self-contaminating proxy.
2. Run IceCube HESE for a third independent test (different source class, neutrinos vs. gamma-rays).
3. Pre-register a specific, testable hypothesis with a defined axis and significance threshold
   before any unblinded confirmatory run.
4. Apply trial-factor correction (Bonferroni or simulation-based) across the four tested metrics.
5. Investigate galactic-plane avoidance and redshift-distribution differences between catalogs.

---

*This memo is part of the commons-sentience-sandbox Stage 10 artifact layer.
Internal guide only — not a scientific claim.*
"""

    with open(memo_path, "w") as f:
        f.write(memo)

    return memo_path
