"""
update_metric_trust.py — Stage 6 Part 6

Revise metric trust classifications using Stage 5 + Stage 6 outputs.

For each metric, integrates evidence from:
  - metric_calibration_report.json     (Stage 5 baseline trust)
  - encoding_invariant_report.json     (Stage 5 encoding sensitivity)
  - encoding_horizon_report.json       (Stage 6 encoding × horizon)
  - governance_interpretation_report.json  (Stage 5 governance sensitivity)
  - governance_horizon_report.json     (Stage 6 governance × horizon)
  - horizon_scaling_report.json        (Stage 6 horizon scaling)
  - ablation_studies/ablation_report.json  (Stage 5 ablation results)

Trust levels (updated):
  trusted_absolute      — absolute values meaningful; minimal confounds; horizon-stable
  trusted_comparative   — reliable for comparisons; not raw absolute; comparative only
  trusted_long_horizon  — unreliable at short horizons but meaningful at ≥50 turns
  conditionally_trusted — usable with documented controls (encoding/governance/horizon)
  unstable_confounded   — known confounds; use with caution; do not interpret naively
  experimental          — exploratory only; interpretation unclear

For each metric, the updated record includes:
  - trust_level (updated)
  - previous_trust_level (Stage 5)
  - trust_change: upgraded / downgraded / unchanged
  - comparative_only: bool
  - horizon_validity: short / long / all
  - governance_confound: none / weak / strong / unknown
  - encoding_confound: none / weak / strong / unknown
  - horizon_sensitivity: horizon_stable / horizon_sensitive / meaningful_at_longer / insufficient_data
  - notes

Output
------
commons_sentience_sim/output/reality_audit/
  metric_trust_update_report.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_OUTPUT_ROOT = _REPO_ROOT / "commons_sentience_sim" / "output" / "reality_audit"

# Trust level constants (ordered from strongest to weakest)
TL_ABSOLUTE           = "trusted_absolute"
TL_COMPARATIVE        = "trusted_comparative"
TL_LONG_HORIZON       = "trusted_long_horizon"
TL_CONDITIONAL        = "conditionally_trusted"
TL_UNSTABLE           = "unstable_confounded"
TL_EXPERIMENTAL       = "experimental"

_TRUST_ORDER = [
    TL_ABSOLUTE, TL_COMPARATIVE, TL_LONG_HORIZON,
    TL_CONDITIONAL, TL_UNSTABLE, TL_EXPERIMENTAL,
]

# Horizon sensitivity labels (from horizon_scaling.py)
HS_STABLE            = "horizon_stable"
HS_SENSITIVE         = "horizon_sensitive"
HS_MEANINGFUL_LONGER = "meaningful_at_longer_horizons"
HS_UNSTABLE          = "unstable_across_horizon"
HS_INSUFFICIENT      = "insufficient_data"

# Encoding sensitivity
ENC_INVARIANT        = "invariant"
ENC_PARTIAL          = "partially_invariant"
ENC_SENSITIVE        = "encoding_sensitive"

# Governance classification
GOV_DOMINATED        = "governance_dominated"
GOV_MODULATED        = "governance_modulated"
GOV_NEUTRAL          = "governance_neutral"
GOV_INSUFFICIENT     = "data_insufficient"


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _load_json(path: Path) -> Optional[Dict[str, Any]]:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return None
    return None


def _trust_rank(level: str) -> int:
    try:
        return _TRUST_ORDER.index(level)
    except ValueError:
        return len(_TRUST_ORDER)


def _trust_change(prev: str, updated: str) -> str:
    pr = _trust_rank(prev)
    ur = _trust_rank(updated)
    if ur < pr:
        return "upgraded"
    if ur > pr:
        return "downgraded"
    return "unchanged"


# ---------------------------------------------------------------------------
# Load Stage 5 + Stage 6 evidence
# ---------------------------------------------------------------------------

def _load_evidence(output_root: Path) -> Dict[str, Dict[str, Any]]:
    """Load all available analysis reports and index by metric name."""
    evidence: Dict[str, Dict[str, Any]] = {}

    # Stage 5 calibration baseline
    cal = _load_json(output_root / "metric_calibration_report.json")
    if cal:
        for entry in cal.get("metrics", []):
            m = entry.get("metric")
            if m:
                evidence.setdefault(m, {})["calibration"] = entry

    # Stage 5 encoding invariance
    enc = _load_json(output_root / "encoding_invariant_report.json")
    if enc:
        for entry in enc.get("checks", []):
            m = entry.get("metric")
            if m:
                evidence.setdefault(m, {})["encoding_invariant"] = entry

    # Stage 5 governance interpretation
    gov = _load_json(output_root / "governance_interpretation_report.json")
    if gov:
        for entry in gov.get("metrics", []):
            m = entry.get("metric")
            if m:
                evidence.setdefault(m, {})["governance_interp"] = entry

    # Stage 6 horizon scaling
    hs_path = output_root / "stage6_long_horizon" / "horizon_scaling_report.json"
    hs = _load_json(hs_path)
    if hs:
        for entry in hs.get("metrics", []):
            m = entry.get("metric")
            if m:
                evidence.setdefault(m, {})["horizon_scaling"] = entry

    # Stage 6 governance horizon
    gh_path = output_root / "stage6_long_horizon" / "governance_horizon_report.json"
    gh = _load_json(gh_path)
    if gh:
        for entry in gh.get("metrics", []):
            m = entry.get("metric")
            if m:
                evidence.setdefault(m, {})["governance_horizon"] = entry

    # Stage 6 encoding horizon
    eh_path = output_root / "stage6_long_horizon" / "encoding_horizon_report.json"
    eh = _load_json(eh_path)
    if eh:
        for entry in eh.get("metrics", []):
            m = entry.get("metric")
            if m:
                evidence.setdefault(m, {})["encoding_horizon"] = entry

    # Stage 5 ablation results
    abl = (
        _load_json(output_root / "ablation_studies" / "ablation_report.json")
        or _load_json(output_root / "ablation_report.json")
    )
    if abl:
        for abl_name, abl_data in abl.get("ablations", {}).items():
            for m, abl_metric in abl_data.get("metrics", {}).items():
                evidence.setdefault(m, {}).setdefault("ablations", {})[abl_name] = abl_metric

    return evidence


# ---------------------------------------------------------------------------
# Classify governance confound for a metric
# ---------------------------------------------------------------------------

def _gov_confound(metric_evidence: Dict[str, Any]) -> str:
    # Check governance horizon (Stage 6) first
    gh = metric_evidence.get("governance_horizon", {})
    if gh:
        cl = gh.get("governance_classification", GOV_INSUFFICIENT)
        if cl == GOV_DOMINATED:
            return "strong"
        if cl == GOV_MODULATED:
            return "weak"
        if cl == GOV_NEUTRAL:
            return "none"
        return "unknown"

    # Fallback to Stage 5 governance interpretation
    gi = metric_evidence.get("governance_interp", {})
    if gi:
        cl = gi.get("governance_classification", GOV_INSUFFICIENT)
        if cl == GOV_DOMINATED:
            return "strong"
        if cl == GOV_MODULATED:
            return "weak"
        if cl == GOV_NEUTRAL:
            return "none"
        return "unknown"

    # Ablation fallback
    ablations = metric_evidence.get("ablations", {})
    gov_abl = ablations.get("governance", {})
    if gov_abl:
        moved = gov_abl.get("moved_meaningfully", False)
        return "weak" if moved else "none"

    return "unknown"


# ---------------------------------------------------------------------------
# Classify encoding confound for a metric
# ---------------------------------------------------------------------------

def _enc_confound(metric_evidence: Dict[str, Any]) -> str:
    # Check Stage 6 encoding horizon (most recent evidence)
    eh = metric_evidence.get("encoding_horizon", {})
    if eh:
        trend = eh.get("horizon_trend")
        if trend == "consistently_sensitive":
            return "strong"
        if trend == "consistently_invariant":
            return "none"
        if trend in ("worsening",):
            return "strong"
        if trend in ("stabilizing", "partially_invariant"):
            return "weak"

    # Stage 5 encoding invariant
    ei = metric_evidence.get("encoding_invariant", {})
    if ei:
        cl = ei.get("classification")
        if cl == ENC_SENSITIVE:
            return "strong"
        if cl == ENC_INVARIANT:
            return "none"
        if cl == ENC_PARTIAL:
            return "weak"

    # Fallback to calibration encoding_sensitive flag
    cal = metric_evidence.get("calibration", {})
    if cal:
        flag = cal.get("encoding_sensitive")
        if flag is True:
            return "strong"
        if flag is False:
            return "none"

    return "unknown"


# ---------------------------------------------------------------------------
# Horizon validity
# ---------------------------------------------------------------------------

def _horizon_validity(metric_evidence: Dict[str, Any]) -> str:
    hs = metric_evidence.get("horizon_scaling", {})
    if hs:
        cl = hs.get("classification")
        if cl == HS_MEANINGFUL_LONGER:
            return "long"
        if cl in (HS_STABLE,):
            return "all"
        if cl == HS_SENSITIVE:
            return "long"  # conservative: require longer horizon
        if cl == HS_UNSTABLE:
            return "none"
    return "all"  # default: no Stage 6 horizon data means we trust Stage 5 conclusions


# ---------------------------------------------------------------------------
# Determine updated trust level
# ---------------------------------------------------------------------------

def _compute_trust(
    prev_trust: str,
    enc_conf: str,
    gov_conf: str,
    horizon_val: str,
    is_comparative_only: bool,
) -> str:
    """Apply evidence-based rules to compute updated trust level."""

    # Hard downgrade rules
    if prev_trust == TL_UNSTABLE:
        return TL_UNSTABLE  # cannot upgrade from unstable without explicit new evidence

    if horizon_val == "none":
        return TL_UNSTABLE

    if enc_conf == "strong" and gov_conf == "strong":
        # Two strong confounds → unstable
        return TL_UNSTABLE

    if enc_conf == "strong":
        # Encoding sensitive: keep as comparative at best, or downgrade to conditional
        if prev_trust in (TL_ABSOLUTE,):
            return TL_CONDITIONAL
        if prev_trust == TL_COMPARATIVE:
            return TL_CONDITIONAL
        return prev_trust  # keep if already conditional/experimental

    if gov_conf == "strong":
        # Strong governance confound → conditional
        if prev_trust == TL_ABSOLUTE:
            return TL_CONDITIONAL
        return prev_trust

    if horizon_val == "long":
        # Only valid at long horizons
        if prev_trust in (TL_ABSOLUTE, TL_COMPARATIVE):
            return TL_LONG_HORIZON
        return prev_trust

    # Comparative-only flag keeps at comparative (cannot upgrade to absolute)
    if is_comparative_only and prev_trust == TL_ABSOLUTE:
        return TL_COMPARATIVE

    # No downgrade needed
    return prev_trust


# ---------------------------------------------------------------------------
# Build updated trust record for one metric
# ---------------------------------------------------------------------------

def _update_one_metric(
    metric: str,
    metric_evidence: Dict[str, Any],
) -> Dict[str, Any]:
    cal = metric_evidence.get("calibration", {})
    prev_trust = cal.get("status", TL_CONDITIONAL)
    comparative_only = cal.get("status") in (TL_COMPARATIVE,)

    enc_conf = _enc_confound(metric_evidence)
    gov_conf = _gov_confound(metric_evidence)
    horizon_val = _horizon_validity(metric_evidence)

    hs = metric_evidence.get("horizon_scaling", {})
    horizon_class = hs.get("classification", HS_INSUFFICIENT)

    updated_trust = _compute_trust(
        prev_trust, enc_conf, gov_conf, horizon_val, comparative_only
    )

    notes: List[str] = []
    if not metric_evidence.get("horizon_scaling"):
        notes.append("no Stage 6 horizon data; trust inherited from Stage 5")
    if enc_conf == "unknown":
        notes.append("encoding sensitivity unknown; use with caution")
    if gov_conf == "unknown":
        notes.append("governance confound unknown; use with caution")
    if updated_trust == TL_LONG_HORIZON:
        notes.append("only meaningful at ≥50 turns based on Stage 6 horizon analysis")

    change = _trust_change(prev_trust, updated_trust)

    return {
        "metric": metric,
        "trust_level": updated_trust,
        "previous_trust_level": prev_trust,
        "trust_change": change,
        "comparative_only": comparative_only or updated_trust == TL_COMPARATIVE,
        "horizon_validity": horizon_val,
        "horizon_sensitivity": horizon_class,
        "governance_confound": gov_conf,
        "encoding_confound": enc_conf,
        "notes": notes,
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_metric_trust_update(
    output_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Load all Stage 5/6 analysis outputs, compute updated trust for each metric,
    and write metric_trust_update_report.json.
    """
    root = output_root or _OUTPUT_ROOT
    evidence = _load_evidence(root)

    if not evidence:
        # Build minimal report from hardcoded Stage 5 baseline
        evidence = _build_fallback_evidence()

    metrics_out: List[Dict[str, Any]] = []
    for metric in sorted(evidence.keys()):
        entry = _update_one_metric(metric, evidence[metric])
        metrics_out.append(entry)

    summary = {
        "total_metrics": len(metrics_out),
        "trusted_absolute": sum(1 for m in metrics_out if m["trust_level"] == TL_ABSOLUTE),
        "trusted_comparative": sum(1 for m in metrics_out if m["trust_level"] == TL_COMPARATIVE),
        "trusted_long_horizon": sum(1 for m in metrics_out if m["trust_level"] == TL_LONG_HORIZON),
        "conditionally_trusted": sum(1 for m in metrics_out if m["trust_level"] == TL_CONDITIONAL),
        "unstable_confounded": sum(1 for m in metrics_out if m["trust_level"] == TL_UNSTABLE),
        "experimental": sum(1 for m in metrics_out if m["trust_level"] == TL_EXPERIMENTAL),
        "upgraded": sum(1 for m in metrics_out if m["trust_change"] == "upgraded"),
        "downgraded": sum(1 for m in metrics_out if m["trust_change"] == "downgraded"),
        "unchanged": sum(1 for m in metrics_out if m["trust_change"] == "unchanged"),
    }

    report: Dict[str, Any] = {
        "report_type": "metric_trust_update",
        "stage": 6,
        "description": (
            "Updated metric trust classifications incorporating Stage 5 calibration, "
            "encoding invariance, governance interpretation, and Stage 6 horizon analysis."
        ),
        "trust_level_legend": {
            TL_ABSOLUTE:    "absolute values meaningful; minimal confounds; horizon-stable",
            TL_COMPARATIVE: "reliable for comparisons; not raw absolute",
            TL_LONG_HORIZON:"only meaningful at ≥50 turns",
            TL_CONDITIONAL: "usable with documented controls",
            TL_UNSTABLE:    "known confounds; interpret with caution",
            TL_EXPERIMENTAL:"exploratory only; interpretation unclear",
        },
        "metrics": metrics_out,
        "summary": summary,
    }

    out_path = root / "metric_trust_update_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2))
    print(f"[metric_trust_update] written → {out_path}", file=sys.stderr)
    return report


# ---------------------------------------------------------------------------
# Fallback evidence (Stage 5 known values)
# ---------------------------------------------------------------------------

def _build_fallback_evidence() -> Dict[str, Dict[str, Any]]:
    """Minimal hard-coded evidence from Stage 5 for when no reports are available."""
    fallback = {
        "path_smoothness": {
            "calibration": {"metric": "path_smoothness", "status": TL_ABSOLUTE,
                            "encoding_sensitive": False, "governance_sensitive": False},
            "encoding_invariant": {"metric": "path_smoothness", "classification": ENC_INVARIANT},
        },
        "avg_control_effort": {
            "calibration": {"metric": "avg_control_effort", "status": TL_ABSOLUTE,
                            "encoding_sensitive": False, "governance_sensitive": False},
        },
        "audit_bandwidth": {
            "calibration": {"metric": "audit_bandwidth", "status": TL_ABSOLUTE,
                            "encoding_sensitive": False, "governance_sensitive": False},
        },
        "mean_position_error": {
            "calibration": {"metric": "mean_position_error", "status": TL_COMPARATIVE,
                            "encoding_sensitive": True, "governance_sensitive": False},
            "encoding_invariant": {"metric": "mean_position_error", "classification": ENC_SENSITIVE},
        },
        "stability_score": {
            "calibration": {"metric": "stability_score", "status": TL_COMPARATIVE,
                            "encoding_sensitive": True, "governance_sensitive": False},
            "encoding_invariant": {"metric": "stability_score", "classification": ENC_SENSITIVE},
        },
        "anisotropy_score": {
            "calibration": {"metric": "anisotropy_score", "status": TL_COMPARATIVE,
                            "encoding_sensitive": True, "governance_sensitive": False},
            "encoding_invariant": {"metric": "anisotropy_score", "classification": ENC_SENSITIVE},
        },
        "observer_dependence_score": {
            "calibration": {"metric": "observer_dependence_score", "status": TL_COMPARATIVE,
                            "encoding_sensitive": False, "governance_sensitive": False},
        },
        "bandwidth_bottleneck_score": {
            "calibration": {"metric": "bandwidth_bottleneck_score", "status": TL_COMPARATIVE,
                            "encoding_sensitive": False, "governance_sensitive": False},
        },
        "trajectory_entropy": {
            "calibration": {"metric": "trajectory_entropy", "status": TL_COMPARATIVE,
                            "encoding_sensitive": True, "governance_sensitive": False},
        },
        "constraint_violation_rate": {
            "calibration": {"metric": "constraint_violation_rate", "status": TL_COMPARATIVE,
                            "encoding_sensitive": False, "governance_sensitive": True},
        },
        "goal_proximity_score": {
            "calibration": {"metric": "goal_proximity_score", "status": TL_UNSTABLE,
                            "encoding_sensitive": True, "governance_sensitive": True},
        },
        "dimensionality_estimate": {
            "calibration": {"metric": "dimensionality_estimate", "status": TL_EXPERIMENTAL,
                            "encoding_sensitive": True, "governance_sensitive": False},
        },
    }
    return fallback


if __name__ == "__main__":
    r = run_metric_trust_update()
    print(json.dumps(r["summary"], indent=2))
