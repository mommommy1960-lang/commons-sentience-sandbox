"""
stage8_first_results.py
=======================
Stage 8 orchestration module: "First Real-Catalog Results Package".

This module provides a thin orchestration layer on top of the Stage 7
public anisotropy study pipeline.  Its purpose is to:

1. Detect a manually placed real public catalog from ``data/real/``.
2. Run the full Stage 7 anisotropy study pipeline on it.
3. Build a compact result bundle.
4. Write a concise internal first-results memo in Markdown.
5. Write a Stage 8 artifact manifest.

Important disclaimers
---------------------
- Results are hypothesis-generating outputs, not proof of any physical or
  metaphysical claim.
- A single catalog run without exposure-map correction or trial-factor
  adjustment is insufficient for a publishable scientific result.
- See ``docs/REALITY_AUDIT_STAGE8_STATUS.md`` for what would be required
  before a first-results note could be published.

Author: commons-sentience-sandbox
"""

from __future__ import annotations

import csv
import datetime
import json
import os
import sys
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Ensure repo root on path when executed directly
# ---------------------------------------------------------------------------
_HERE      = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from reality_audit.data_analysis.public_event_catalogs import (
    load_public_catalog,
    describe_catalog_coverage,
    default_null_mode_for_catalog,
)
from reality_audit.data_analysis.public_anisotropy_study import (
    run_public_anisotropy_study,
    write_public_study_artifacts,
)


def _build_preregistration_metadata(
    plan: Optional[Dict[str, Any]],
    plan_path: Optional[str],
) -> Optional[Dict[str, Any]]:
    """Build a compact preregistration summary for embedding in run metadata.

    Returns None if no plan was provided (exploratory run)."""
    if plan is None:
        return None
    try:
        from reality_audit.data_analysis.preregistration import plan_summary_for_metadata
        return plan_summary_for_metadata(plan, plan_path=plan_path)
    except Exception:
        return {"error": "preregistration module unavailable", "plan_path": plan_path}

# ---------------------------------------------------------------------------
# Known real catalog filenames (in priority order)
# ---------------------------------------------------------------------------
_KNOWN_CATALOG_FILES: List[Dict[str, str]] = [
    {
        "filename": "fermi_lat_grb_catalog.csv",
        "label":    "fermi_lat_grb",
        "description": "Fermi-LAT GRB catalog (HEASARC)",
    },
    {
        "filename": "swift_bat3_grb_catalog.csv",
        "label":    "swift_bat3_grb",
        "description": "Swift BAT3 GRB catalog",
    },
    {
        "filename": "icecube_hese_events.csv",
        "label":    "icecube_hese",
        "description": "IceCube HESE neutrino events",
    },
]

_SUPPORTED_EXTENSIONS = (".csv", ".tsv")


# ===========================================================================
# 1. Auto-discovery
# ===========================================================================

def discover_real_catalog(data_dir: str = "data/real") -> Dict[str, Any]:
    """Detect candidate real catalog files placed in ``data_dir``.

    Priority order:
      1. Known catalog filenames (fermi_lat_grb, swift_bat3_grb, icecube_hese).
      2. Any other CSV/TSV file that is not the example/synthetic catalog.

    Returns
    -------
    Dict with keys:
      detected_path         – absolute path string or None
      detected_catalog_label – short label string or None
      detection_method      – "known_filename" | "fallback_csv" | "not_found"
      usable                – bool (True if a non-empty file was found)
      candidates            – list of all .csv/.tsv files found (for diagnostics)
      message               – human-readable description
    """
    # Resolve relative to repo root when running from any cwd
    if not os.path.isabs(data_dir):
        data_dir = os.path.join(_REPO_ROOT, data_dir)

    result: Dict[str, Any] = {
        "detected_path":          None,
        "detected_catalog_label": None,
        "detection_method":       "not_found",
        "usable":                 False,
        "candidates":             [],
        "message":                "",
    }

    if not os.path.isdir(data_dir):
        result["message"] = (
            f"Directory {data_dir!r} does not exist. "
            "Create it and place a supported catalog file there."
        )
        return result

    # Collect all CSV/TSV files
    all_files = [
        f for f in os.listdir(data_dir)
        if os.path.splitext(f)[1].lower() in _SUPPORTED_EXTENSIONS
    ]
    result["candidates"] = sorted(all_files)

    # Skip purely synthetic/example files that are part of the repo or pipeline output
    _SKIP_FILES = {"example_event_catalog.csv"}

    # Pass 1: look for known catalog filenames
    for known in _KNOWN_CATALOG_FILES:
        fpath = os.path.join(data_dir, known["filename"])
        if os.path.isfile(fpath) and known["filename"] not in _SKIP_FILES:
            size = os.path.getsize(fpath)
            if size > 0:
                result.update({
                    "detected_path":          fpath,
                    "detected_catalog_label": known["label"],
                    "detection_method":       "known_filename",
                    "usable":                 True,
                    "message":                (
                        f"Found known catalog: {known['filename']} "
                        f"({size} bytes) at {fpath}"
                    ),
                })
                return result

    # Pass 2: first non-skipped CSV/TSV (excluding synthetic pipeline outputs)
    for fname in sorted(all_files):
        if fname in _SKIP_FILES:
            continue
        # Skip pipeline-generated synthetic files
        if fname.startswith("_synthetic_") or fname.startswith("synthetic_"):
            continue
        fpath = os.path.join(data_dir, fname)
        size  = os.path.getsize(fpath)
        if size > 0:
            label = os.path.splitext(fname)[0]
            result.update({
                "detected_path":          fpath,
                "detected_catalog_label": label,
                "detection_method":       "fallback_csv",
                "usable":                 True,
                "message":                (
                    f"Found CSV catalog via fallback: {fname} "
                    f"({size} bytes) at {fpath}"
                ),
            })
            return result

    # Nothing found
    supported = ", ".join(k["filename"] for k in _KNOWN_CATALOG_FILES)
    result["message"] = (
        f"No usable real catalog found in {data_dir!r}. "
        f"Place one of the following files there: {supported}. "
        "See data/real/README_public_catalog_ingest.md for download instructions."
    )
    return result


# ===========================================================================
# 2. Stage 8 orchestration
# ===========================================================================

def run_stage8_first_results(
    input_path: str,
    output_dir: str,
    name: str = "stage8_first_results",
    null_repeats: int = 100,
    axis_count: int = 48,
    seed: int = 42,
    plots: bool = True,
    save_normalized: bool = True,
    null_mode: Optional[str] = None,
    preregistration_plan: Optional[Dict[str, Any]] = None,
    preregistration_plan_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Run the complete Stage 8 first-results workflow on a real catalog.

    Steps:
      1. Load and normalise the catalog via ``load_public_catalog``.
      2. Describe catalog coverage.
      3. Optionally save a normalised event CSV.
      4. Run ``run_public_anisotropy_study``.
      5. Write Stage 7 study artifacts via ``write_public_study_artifacts``.
      6. Write the Stage 8 memo and manifest.

    Parameters
    ----------
    input_path     : Path to the raw catalog file.
    output_dir     : Directory for all output artifacts.
    name           : Run name used in filenames and report headers.
    null_repeats   : Null ensemble size.
    axis_count     : Trial axis count (default 48).
    seed           : RNG seed.
    plots          : Whether to generate PNG plots.
    save_normalized: Whether to save the normalised event CSV.
    null_mode      : "isotropic", "exposure_corrected", or None (auto per catalog).
                     When None, the recommended default for the detected catalog is used.
    preregistration_plan : optional loaded plan dict (from preregistration.load_preregistration_plan).
                           When provided, a compact plan summary is recorded in run_metadata.
    preregistration_plan_path : optional path string for traceability (stored in metadata).

    Returns
    -------
    A compact result bundle dict.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Derive a catalog label from the file basename
    catalog_label = os.path.splitext(os.path.basename(input_path))[0]

    # Auto-select null model if not explicitly specified
    if null_mode is None:
        null_mode = default_null_mode_for_catalog(catalog_label)

    # --- Load and normalise ---
    events = load_public_catalog(input_path)

    # Add _b_proxy and _parse_warnings fields expected by downstream helpers
    import math as _math
    for e in events:
        if e.get("dec") is not None and "_b_proxy" not in e:
            e["_b_proxy"] = abs(float(e["dec"]))
        if "_parse_warnings" not in e:
            e["_parse_warnings"] = []

    # --- Coverage description ---
    coverage = describe_catalog_coverage(events)

    # --- Optional: save normalised CSV ---
    normalised_path: Optional[str] = None
    if save_normalized:
        normalised_path = os.path.join(output_dir, f"{name}_normalized_events.csv")
        schema_fields = [
            "event_id", "energy", "arrival_time", "ra", "dec", "instrument", "epoch"
        ]
        with open(normalised_path, "w", newline="") as f:
            writer = csv.DictWriter(
                f, fieldnames=schema_fields, extrasaction="ignore"
            )
            writer.writeheader()
            writer.writerows(events)

    # --- Run Stage 7 study pipeline ---
    run_config = {
        "null_repeats": null_repeats,
        "num_axes":     axis_count,
        "seed":         seed,
        "null_mode":    null_mode,
    }
    study_results = run_public_anisotropy_study(
        events,
        null_repeats=null_repeats,
        seed=seed,
        config=run_config,
        num_axes=axis_count,
        null_mode=null_mode,
    )

    # --- Write Stage 7 study artifacts ---
    study_manifest = write_public_study_artifacts(
        results=study_results,
        events=events,
        null_events_example=None,
        output_dir=output_dir,
        name=name,
        plots_enabled=plots,
        config=run_config,
        catalog_name=catalog_label,
        coverage=coverage,
    )

    # --- Stage 8 memo ---
    result_bundle: Dict[str, Any] = {
        "run_name":      name,
        "input_path":    input_path,
        "output_dir":    output_dir,
        "catalog_label": catalog_label,
        "event_count":   study_results.get("event_count", 0),
        "coverage":      coverage,
        "study_results": study_results,
        "manifest":      study_manifest,
        "normalised_path": normalised_path,
        "run_metadata": {
            "null_repeats": null_repeats,
            "axis_count":   axis_count,
            "seed":         seed,
            "plots":        plots,
            "save_normalized": save_normalized,
            "null_mode":    null_mode,
            "timestamp":    datetime.datetime.utcnow().isoformat() + "Z",
            "stage":        "stage8_first_results",
            "preregistration": _build_preregistration_metadata(
                preregistration_plan, preregistration_plan_path
            ),
        },
    }

    memo_path = write_stage8_first_results_memo(result_bundle, output_dir)
    result_bundle["memo_path"] = memo_path

    stage8_manifest_path = write_stage8_manifest(result_bundle, output_dir, name)
    result_bundle["stage8_manifest_path"] = stage8_manifest_path

    return result_bundle


# ===========================================================================
# 3. Status summary builder
# ===========================================================================

def build_stage8_status_summary(result_bundle: Dict[str, Any]) -> Dict[str, Any]:
    """Extract a compact status summary from a Stage 8 result bundle.

    Returns a flat dict with the most important metrics and recommended actions.
    """
    sr  = result_bundle.get("study_results", {})
    nc  = sr.get("null_comparison", {})
    sig = sr.get("signal_evaluation", {})
    pa  = sr.get("preferred_axis", {})
    ani = sr.get("anisotropy", {})
    cov = result_bundle.get("coverage", {})

    hemi_score  = ani.get("hemisphere_imbalance", None)
    axis_score  = pa.get("score", None)
    axis_pct    = nc.get("axis_percentile", None)
    hemi_pct    = nc.get("hemi_percentile", None)
    tier        = sig.get("tier", "unknown")
    max_pct     = sig.get("max_percentile", None)

    # Human-readable interpretation
    if tier == "strong_anomaly_like_deviation":
        interp = (
            "Strong anomaly-like deviation detected. "
            "Top 3% vs isotropic null. "
            "Requires systematic-effects investigation before any scientific claim."
        )
    elif tier == "moderate_anomaly_like_deviation":
        interp = (
            "Moderate anomaly-like deviation detected. "
            "Top 10% vs isotropic null. "
            "Warrants follow-up; consistent with a statistical fluctuation."
        )
    elif tier == "weak_anomaly_like_deviation":
        interp = (
            "Weak anomaly-like deviation detected. "
            "Top 25% vs isotropic null. "
            "Consistent with statistical fluctuation."
        )
    else:
        interp = (
            "No significant anomaly detected. "
            "All metrics within the bulk of the isotropic null distribution."
        )

    caveats = [
        "Single-catalog analysis with a simple isotropic null; no exposure-map correction.",
        "No trial-factor adjustment across the four tested metrics.",
        "Selection biases and instrument systematics not characterised.",
        "This run is an internal first-results package, not a publishable result.",
    ]

    next_actions = [
        "Add exposure-map / acceptance-weighted null model (Stage 9 priority).",
        "HEALPix-based axis scan (NSIDE ≥ 8) for finer preferred-axis sensitivity.",
        "Multi-catalog cross-matching for cross-instrument consistency check.",
        "Blinded pre-registration before any significance claim.",
        "Trial-factor correction across simultaneously tested metrics.",
    ]

    return {
        "catalog_label":            result_bundle.get("catalog_label"),
        "event_count":              result_bundle.get("event_count"),
        "events_with_position":     cov.get("ra_dec_coverage", {}).get("n_with_position"),
        "time_span_mjd":            cov.get("time_span_mjd"),
        "anisotropy_score":         hemi_score,
        "hemisphere_percentile":    hemi_pct,
        "preferred_axis_score":     axis_score,
        "preferred_axis_percentile": axis_pct,
        "max_percentile":           max_pct,
        "interpretation_label":     tier,
        "interpretation_text":      interp,
        "caveats":                  caveats,
        "next_recommended_actions": next_actions,
    }


# ===========================================================================
# 4. Memo writer
# ===========================================================================

def write_stage8_first_results_memo(
    result_bundle: Dict[str, Any],
    output_dir: str,
) -> str:
    """Write a polished internal Markdown memo summarising the Stage 8 run.

    Returns the path to the memo file.
    """
    status = build_stage8_status_summary(result_bundle)
    sr     = result_bundle.get("study_results", {})
    nc     = sr.get("null_comparison", {})
    sig    = sr.get("signal_evaluation", {})
    rm     = result_bundle.get("run_metadata", {})
    cov    = result_bundle.get("coverage", {})
    ts     = rm.get("timestamp", datetime.datetime.utcnow().isoformat() + "Z")

    name          = result_bundle.get("run_name", "stage8_first_results")
    catalog_label = result_bundle.get("catalog_label", "unknown")
    input_path    = result_bundle.get("input_path", "unknown")
    event_count   = result_bundle.get("event_count", 0)
    tier          = status.get("interpretation_label", "unknown")
    null_mode     = rm.get("null_mode", "isotropic")
    null_label    = "exposure-corrected empirical sky-acceptance proxy" if null_mode == "exposure_corrected" else "uniform isotropic sphere"
    null_why      = (
        "The empirical exposure-corrected null was selected to account for "
        "the non-uniform sky coverage of the Fermi GBM detector. "
        "The null is built by histogramming the observed events and re-sampling "
        "from the resulting distribution; see docs/REALITY_AUDIT_STAGE9_STATUS.md."
        if null_mode == "exposure_corrected"
        else
        "A uniform isotropic null was used (events placed uniformly on the sphere). "
        "This does not account for instrument sky-coverage biases."
    )

    def _fmt(v: Any, digits: int = 4) -> str:
        if v is None:
            return "N/A"
        if isinstance(v, float):
            return f"{v:.{digits}f}"
        return str(v)

    pa_score  = sr.get("preferred_axis", {}).get("score")
    hemi_imb  = sr.get("anisotropy", {}).get("hemisphere_imbalance")
    et_r      = sr.get("energy_time_correlation", {}).get("pearson_r")
    clust_val = sr.get("cluster_score", {}).get("value")
    seed      = rm.get("seed")
    null_rep  = rm.get("null_repeats")
    axis_cnt  = rm.get("axis_count")

    instruments = cov.get("instrument_labels", [])
    instr_str   = ", ".join(str(x) for x in instruments[:8]) if instruments else "N/A"
    n_pos       = cov.get("ra_dec_coverage", {}).get("n_with_position", "N/A")
    time_span   = cov.get("time_span_mjd", {})
    if isinstance(time_span, dict):
        t_str = (
            f"MJD {time_span.get('min', '?'):.1f} – {time_span.get('max', '?'):.1f}"
            if time_span.get("min") is not None else "N/A"
        )
    else:
        t_str = "N/A"

    sig_summary = sig.get("summary", "")
    sig_caveat  = sig.get("caveat", "")

    lines: List[str] = []
    lines.append(f"# Stage 8 First-Results Internal Memo")
    lines.append(f"")
    lines.append(f"**Run name:** `{name}`  ")
    lines.append(f"**Generated:** {ts}  ")
    lines.append(f"**Catalog:** `{catalog_label}` (`{input_path}`)  ")
    lines.append(f"**Stage:** Stage 8 — First Real-Catalog Results Package  ")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")
    lines.append(f"## 1. What Was Run")
    lines.append(f"")
    lines.append(
        f"The Stage 7 public-data anisotropy study was run on the catalog "
        f"`{catalog_label}` ({event_count} events after normalisation). "
        f"The pipeline tested four primary metrics against an isotropic null "
        f"ensemble of {null_rep} synthetic draws:"
    )
    lines.append(f"")
    lines.append(f"- Hemisphere imbalance (north–south event fraction difference)")
    lines.append(f"- Preferred-axis score (max |mean cos-projection| over {axis_cnt} trial axes)")
    lines.append(f"- Energy–time Pearson correlation")
    lines.append(f"- Temporal clustering score")
    lines.append(f"")
    lines.append(f"Seed: `{seed}`. Null model: **{null_label}**.")
    lines.append(f"")
    lines.append(f"**Why this null model:** {null_why}")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")
    lines.append(f"## 2. Catalog Coverage")
    lines.append(f"")
    lines.append(f"| Field               | Value                |")
    lines.append(f"|---------------------|----------------------|")
    lines.append(f"| Events (total)      | {event_count}        |")
    lines.append(f"| Events with position| {n_pos}              |")
    lines.append(f"| Instruments         | {instr_str}          |")
    lines.append(f"| Time span           | {t_str}              |")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")
    lines.append(f"## 3. Key Metrics")
    lines.append(f"")
    lines.append(f"| Metric                    | Observed value | Percentile vs null |")
    lines.append(f"|---------------------------|----------------|--------------------|")
    lines.append(
        f"| Hemisphere imbalance      | {_fmt(hemi_imb)} | "
        f"{_fmt(nc.get('hemi_percentile'))} |"
    )
    lines.append(
        f"| Preferred-axis score      | {_fmt(pa_score)} | "
        f"{_fmt(nc.get('axis_percentile'))} |"
    )
    lines.append(
        f"| Energy–time Pearson r     | {_fmt(et_r)} | "
        f"{_fmt(nc.get('et_r_percentile'))} |"
    )
    lines.append(
        f"| Temporal clustering score | {_fmt(clust_val)} | "
        f"{_fmt(nc.get('clust_percentile'))} |"
    )
    lines.append(f"")
    lines.append(f"**Signal tier:** `{tier}`  ")
    lines.append(f"**Maximum percentile:** {_fmt(sig.get('max_percentile'))}")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")
    lines.append(f"## 4. Interpretation")
    lines.append(f"")
    lines.append(sig_summary)
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")
    lines.append(f"## 5. What This Result Does NOT Prove")
    lines.append(f"")
    lines.append(
        "A deviation from an isotropic null model — even a statistically "
        "significant one — does **not** establish any of the following:"
    )
    lines.append(f"")
    lines.append(
        "- That the universe or physical reality is a simulation."
    )
    lines.append(
        "- That the signal is cosmological rather than instrumental."
    )
    lines.append(
        "- That any specific physical model is correct."
    )
    lines.append(
        "- That the result would survive a pre-registered replication with "
        "trial-factor correction."
    )
    lines.append(f"")
    lines.append(sig_caveat)
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")
    lines.append(f"## 6. Current Limitations")
    lines.append(f"")
    for c in status.get("caveats", []):
        lines.append(f"- {c}")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")
    lines.append(f"## 7. Recommended Next Upgrades")
    lines.append(f"")
    for a in status.get("next_recommended_actions", []):
        lines.append(f"- {a}")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")
    lines.append(
        f"*This memo is an internal first-results artifact produced by the "
        f"commons-sentience-sandbox Stage 8 pipeline. "
        f"It is not a scientific publication or preprint.*"
    )
    lines.append(f"")

    os.makedirs(output_dir, exist_ok=True)
    memo_path = os.path.join(output_dir, f"{name}_memo.md")
    with open(memo_path, "w") as f:
        f.write("\n".join(lines))

    return memo_path


# ===========================================================================
# 5. Manifest writer
# ===========================================================================

def write_stage8_manifest(
    result_bundle: Dict[str, Any],
    output_dir: str,
    name: str,
) -> str:
    """Write a Stage 8 artifacts manifest JSON file.

    Returns the path to the manifest file.
    """
    ts = datetime.datetime.utcnow().isoformat() + "Z"

    manifest_payload: Dict[str, Any] = {
        "stage":        "stage8_first_results",
        "run_name":     name,
        "written_at":   ts,
        "input_path":   result_bundle.get("input_path"),
        "output_dir":   output_dir,
        "catalog_label": result_bundle.get("catalog_label"),
        "event_count":  result_bundle.get("event_count"),
        "run_metadata": result_bundle.get("run_metadata", {}),
        "artifacts": {},
    }

    # Collect all artifact paths from study manifest
    for k, v in result_bundle.get("manifest", {}).items():
        manifest_payload["artifacts"][k] = v

    # Add Stage 8-specific artifacts
    if result_bundle.get("normalised_path"):
        manifest_payload["artifacts"]["normalized_events_csv"] = (
            result_bundle["normalised_path"]
        )
    if result_bundle.get("memo_path"):
        manifest_payload["artifacts"]["stage8_memo"] = result_bundle["memo_path"]

    # Summary status
    sig = result_bundle.get("study_results", {}).get("signal_evaluation", {})
    manifest_payload["signal_tier"]    = sig.get("tier", "unknown")
    manifest_payload["max_percentile"] = sig.get("max_percentile")

    os.makedirs(output_dir, exist_ok=True)
    manifest_path = os.path.join(output_dir, f"{name}_stage8_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest_payload, f, indent=2)

    return manifest_path
