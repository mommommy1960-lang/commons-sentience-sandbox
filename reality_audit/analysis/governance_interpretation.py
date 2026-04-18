"""
governance_interpretation.py — Classify governance-induced metric shifts and
explain which metrics must not be interpreted as deep agent structure without
governance controls.

For each governance-sensitive metric:
  1. Compare shift magnitude to sandbox variability (CV from Stage 4)
  2. Compare shift magnitude to false-positive baseline behaviour (Stage 3 thresholds)
  3. Classify whether the metric is "governance-sensitive first" or
     "substrate-sensitive first"

Classification schema
---------------------
G1  governance_dominated   — shift > FP_threshold AND > sandbox_variability_range
G2  governance_modulated   — shift detectable but within FP_threshold margin
G3  governance_neutral     — no detectable shift under governance toggle
G4  data_insufficient      — run counts / turns too short to determine

Output
------
governance_interpretation_report.json
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_OUTPUT_ROOT = _REPO_ROOT / "commons_sentience_sim" / "output" / "reality_audit"

# Classification constants
G1_GOVERNANCE_DOMINATED   = "governance_dominated"
G2_GOVERNANCE_MODULATED   = "governance_modulated"
G3_GOVERNANCE_NEUTRAL     = "governance_neutral"
G4_DATA_INSUFFICIENT      = "data_insufficient"

# False-positive thresholds from Stage 3 calibration
FP_THRESHOLDS: Dict[str, Optional[float]] = {
    "mean_position_error":        6.0,
    "stability_score":            0.05,   # lower bound FP
    "avg_control_effort":         0.95,
    "path_smoothness":            None,
    "observer_dependence_score":  15.0,
    "audit_bandwidth":            None,
    "anisotropy_score":           None,
}

# Known governance sensitivity from Stage 4 (as prior)
_STAGE4_KNOWN_NEUTRAL = {
    "mean_position_error", "stability_score", "path_smoothness",
    "audit_bandwidth", "observer_dependence_score", "anisotropy_score",
}
_STAGE4_KNOWN_SENSITIVE = {"avg_control_effort"}


def _load_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        return None


def _classify_metric_shift(
    metric: str,
    delta: Optional[float],
    sandbox_cv: Optional[float],
    fp_threshold: Optional[float],
) -> str:
    """Classify how governance-induced shift compares to variability and FP threshold."""
    if delta is None:
        return G4_DATA_INSUFFICIENT

    abs_delta = abs(delta)

    # Check against FP threshold
    fp_exceeded = fp_threshold is not None and abs_delta > fp_threshold

    # Check against sandbox variability estimate
    # If CV is known and the shift is > 2x the expected variability range, flag as dominated
    # We approximate "variability range" as CV * typical_mean (0–1 scale → CV itself)
    variability_significant = sandbox_cv is not None and abs_delta > 2.0 * sandbox_cv

    if abs_delta < 0.01:
        return G3_GOVERNANCE_NEUTRAL
    if fp_exceeded or variability_significant:
        return G1_GOVERNANCE_DOMINATED
    # Some detectable shift but within tolerance
    return G2_GOVERNANCE_MODULATED


def interpret_governance_sensitivity(
    output_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Build governance interpretation report.

    Loads (if available):
      - governance_campaign_report.json — for delta estimates per metric
      - sandbox_variability_report.json — for CV estimates per metric
      - ablation_report.json            — for ablation governance data

    Falls back to Stage 4 known results if live data is unavailable.
    """
    root = output_root or _OUTPUT_ROOT

    gov_report = _load_json(root / "governance_campaigns" / "governance_campaign_report.json")
    var_report = _load_json(root / "sandbox_variability_report.json")
    abl_report = _load_json(root / "ablation_studies" / "ablation_report.json") or _load_json(root / "ablation_report.json")

    # Build CV index from variability report
    cv_index: Dict[str, Optional[float]] = {}
    if var_report:
        for entry in var_report.get("variability", []):
            for metric, cls in entry.get("metrics", {}).items():
                # Approximate CV from classification
                cv_approx = {
                    "deterministic_stable": 0.005,
                    "stochastic_but_usable": 0.15,
                    "too_unstable": 0.50,
                }.get(cls)
                # Keep most conservative
                if metric not in cv_index or (
                    cv_approx is not None and (cv_index[metric] is None or cv_approx > cv_index[metric])
                ):
                    cv_index[metric] = cv_approx

    # Build delta index — prefer ablation, fall back to governance campaign
    delta_index: Dict[str, Optional[float]] = {}
    if abl_report:
        gov_abl = abl_report.get("ablations", {}).get("governance", {})
        for metric, info in gov_abl.get("metrics", {}).items():
            delta_index[metric] = info.get("delta")
    if gov_report:
        for metric, info in gov_report.get("metrics", {}).items():
            if metric not in delta_index:
                delta_index[metric] = info.get("delta")

    # Determine which metrics to include
    all_metrics = set(FP_THRESHOLDS.keys())
    if delta_index:
        all_metrics |= set(delta_index.keys())

    interpretation_entries: List[Dict[str, Any]] = []
    for metric in sorted(all_metrics):
        delta = delta_index.get(metric)
        cv = cv_index.get(metric)
        fp_thresh = FP_THRESHOLDS.get(metric)

        classification = _classify_metric_shift(metric, delta, cv, fp_thresh)

        # Determine causal attribution
        if metric in _STAGE4_KNOWN_SENSITIVE:
            primary_interpretation = "governance_sensitive_first"
        elif delta is None:
            primary_interpretation = "unknown"
        elif classification == G3_GOVERNANCE_NEUTRAL:
            primary_interpretation = "substrate_sensitive_first"
        else:
            primary_interpretation = "governance_sensitive_first"

        entry: Dict[str, Any] = {
            "metric": metric,
            "governance_classification": classification,
            "primary_interpretation": primary_interpretation,
            "estimated_delta": delta,
            "sandbox_cv": cv,
            "fp_threshold": fp_thresh,
            "must_control_for_governance": classification in (G1_GOVERNANCE_DOMINATED, G2_GOVERNANCE_MODULATED),
        }

        # Explicit warnings for commonly misused metrics
        if metric == "avg_control_effort":
            entry["warning"] = (
                "This metric measures the governance blocking rate directly.  "
                "Always interpret as governance load first — it is not a measure "
                "of agent intrinsic behaviour."
            )
        elif metric == "observer_dependence_score":
            entry["warning"] = (
                "In passive sandbox mode this is always 0 (no hidden-state divergence).  "
                "Any non-zero values in active_measurement mode reflect sensor staleness, "
                "not governance effects."
            )
        elif classification == G3_GOVERNANCE_NEUTRAL and delta is not None:
            entry["note"] = (
                "Governance toggle does not appear to affect this metric in current run lengths.  "
                "Still report within-encoding only."
            )

        interpretation_entries.append(entry)

    report = {
        "stage": "Stage 5",
        "description": (
            "Classification of governance-induced metric shifts relative to variability "
            "and false-positive baselines."
        ),
        "classification_schema": {
            G1_GOVERNANCE_DOMINATED: (
                "Shift > FP threshold or > 2× sandbox variability; "
                "metric reflects governance state primarily."
            ),
            G2_GOVERNANCE_MODULATED: (
                "Detectable shift but within FP margin; "
                "governance contributes but substrate also plays a role."
            ),
            G3_GOVERNANCE_NEUTRAL: (
                "No detectable shift under governance toggle; "
                "metric reflects substrate-level agent structure."
            ),
            G4_DATA_INSUFFICIENT: (
                "Insufficient run counts / turn lengths to determine.  "
                "Increase turn_counts and n_seeds."
            ),
        },
        "key_constraint": (
            "Metrics classified G1 or G2 must NEVER be interpreted as reflecting "
            "'deep agent structure' without explicitly controlling for governance state.  "
            "Run both governance_on and governance_off conditions."
        ),
        "metrics": interpretation_entries,
    }

    root.mkdir(parents=True, exist_ok=True)
    path = root / "governance_interpretation_report.json"
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)

    return report


if __name__ == "__main__":
    result = interpret_governance_sensitivity()
    print("Governance interpretation report written.")
    for entry in result["metrics"]:
        print(
            f"  {entry['metric']}: {entry['governance_classification']} "
            f"(must_control={entry['must_control_for_governance']})"
        )
