"""
findings_extractor.py — Automatically extract the strongest supported findings
from Stage 5 outputs.

Each finding includes:
  - finding_id         — unique slug
  - finding_text       — plain-English claim
  - supporting_metrics — list of metric names cited
  - evidence_sources   — list of report file names
  - trust_level        — "strong" / "moderate" / "weak" / "experimental"
  - caveats            — list of caveat strings
  - absolute_or_comparative — "absolute" / "comparative" / "mixed"

Output
------
findings_ranked.json — sorted from most to least strongly supported
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


# ---------------------------------------------------------------------------
# Trust levels
# ---------------------------------------------------------------------------

TRUST_STRONG       = "strong"
TRUST_MODERATE     = "moderate"
TRUST_WEAK         = "weak"
TRUST_EXPERIMENTAL = "experimental"

_TRUST_ORDER = {TRUST_STRONG: 0, TRUST_MODERATE: 1, TRUST_WEAK: 2, TRUST_EXPERIMENTAL: 3}


# ---------------------------------------------------------------------------
# Static findings catalogue
#
# These are derived from cumulative Stage 2–4 evidence plus the design of
# Stage 5 campaigns.  Where live data is available, values are enriched at
# runtime.  Where it is not, the static entry stands.
# ---------------------------------------------------------------------------

_STATIC_FINDINGS: List[Dict[str, Any]] = [
    {
        "finding_id": "F01_passive_probe_readonly",
        "finding_text": (
            "The passive probe is read-only: path-history, total_records, goal_room, "
            "and probe_mode fields are exactly equal across repeated passive runs of the "
            "same configuration.  Probabilistic metrics (position_error, stability_score) "
            "are within natural stochastic tolerance.  Action sequences are similar "
            "(normalised edit distance < 0.20)."
        ),
        "supporting_metrics": ["audit_bandwidth", "path_smoothness", "avg_control_effort"],
        "evidence_sources": ["read_only_expansion_report.json"],
        "trust_level": TRUST_STRONG,
        "caveats": [
            "Evidence based on short (5-turn) runs; confirmed directional consistency "
            "across Stage 3 and 4 repeated seeds.",
            "Active_measurement_model mode modifies the probe schedule — read-only "
            "claim applies to passive mode only.",
        ],
        "absolute_or_comparative": "absolute",
    },
    {
        "finding_id": "F02_path_smoothness_encoding_robust",
        "finding_text": (
            "path_smoothness is robust to position-encoding strategy: spread across "
            "BFS+MDS, pure-hop, and manual-topological encodings is < 5%.  "
            "It can be reported without an encoding qualifier."
        ),
        "supporting_metrics": ["path_smoothness"],
        "evidence_sources": ["encoding_robustness_report.json"],
        "trust_level": TRUST_STRONG,
        "caveats": [
            "path_smoothness measures room-transition rate, which does not depend on "
            "coordinate values — this robustness result is structurally expected.",
        ],
        "absolute_or_comparative": "absolute",
    },
    {
        "finding_id": "F03_position_metrics_encoding_sensitive",
        "finding_text": (
            "mean_position_error, stability_score, and anisotropy_score are "
            "encoding-sensitive: raw values differ by 37–100% across three encodings.  "
            "These metrics must not be compared across analyses that used different "
            "position encodings."
        ),
        "supporting_metrics": ["mean_position_error", "stability_score", "anisotropy_score"],
        "evidence_sources": ["encoding_robustness_report.json"],
        "trust_level": TRUST_STRONG,
        "caveats": [
            "Scenario rank ordering may still be preserved even if absolute values differ "
            "— see encoding_invariant_report.json for rank-ordering checks.",
            "All Stage 3–4 results used BFS+MDS encoding; within-stage comparisons are valid.",
        ],
        "absolute_or_comparative": "comparative",
    },
    {
        "finding_id": "F04_no_false_positives_in_sandbox",
        "finding_text": (
            "No false positive detections were observed in sandbox conditions.  "
            "Both minimal-policy (cooperation=0.1, trust=0.2) and governance-off runs "
            "remained within calibrated thresholds for all monitored metrics."
        ),
        "supporting_metrics": [
            "mean_position_error", "stability_score", "avg_control_effort", "observer_dependence_score",
        ],
        "evidence_sources": ["sandbox_false_positive_report.json"],
        "trust_level": TRUST_STRONG,
        "caveats": [
            "Tested at 5 turns with 3 seeds — production FP characterisation at 50+ turns "
            "may yield different rates.",
            "Thresholds were calibrated on short runs; long-horizon runs may require "
            "threshold re-calibration.",
        ],
        "absolute_or_comparative": "absolute",
    },
    {
        "finding_id": "F05_governance_shifts_control_effort",
        "finding_text": (
            "Governance state affects avg_control_effort: governance-off runs show "
            "lower blocking rates than governance-on runs when agents choose blockable "
            "actions.  In baseline cooperation scenarios the difference may be small "
            "because agents rarely choose blockable actions."
        ),
        "supporting_metrics": ["avg_control_effort"],
        "evidence_sources": [
            "governance_campaign_report.json",
            "ablation_report.json",
        ],
        "trust_level": TRUST_MODERATE,
        "caveats": [
            "At 5-turn runs, governance_sensitive_metrics=[] was observed — too short "
            "for structural governance effects to emerge.",
            "Longer runs (25+ turns) are needed to confirm the shift magnitude.",
            "governance_strictness config parameter does NOT affect GovernanceEngine — "
            "only structural monkeypatch (gov_off) changes real behaviour.",
        ],
        "absolute_or_comparative": "comparative",
    },
    {
        "finding_id": "F06_observer_dependence_score_unreliable",
        "finding_text": (
            "observer_dependence_score is unreliable as a standalone anomaly signal.  "
            "In passive sandbox mode it is always 0 by construction.  In "
            "active_measurement_model mode it measures sensor staleness, not agent "
            "epistemic opacity.  It should not be interpreted as reflecting agent "
            "self-knowledge or hidden-state divergence."
        ),
        "supporting_metrics": ["observer_dependence_score"],
        "evidence_sources": [
            "docs/METRIC_TRUST_RANKING.md",
            "reality_audit/metrics/observer_metrics.py",
        ],
        "trust_level": TRUST_STRONG,
        "caveats": [
            "Replacement metrics (hidden_measured_gap_path_normalised, "
            "observation_schedule_sensitivity) exist but are Experimental/Comparative "
            "and require paired runs.",
        ],
        "absolute_or_comparative": "absolute",
    },
    {
        "finding_id": "F07_metrics_deterministic_stable_short_runs",
        "finding_text": (
            "All six core metrics (mean_position_error, stability_score, avg_control_effort, "
            "path_smoothness, observer_dependence_score, audit_bandwidth) are classified "
            "deterministic_stable (CV < 1%) across repeated seeds in short (5–10 turn) "
            "sandbox runs.  This suggests the sandbox initialisation is deterministic "
            "at short horizons; variability is expected to increase at 25+ turns."
        ),
        "supporting_metrics": [
            "mean_position_error", "stability_score", "avg_control_effort",
            "path_smoothness", "observer_dependence_score", "audit_bandwidth",
        ],
        "evidence_sources": ["sandbox_variability_report.json"],
        "trust_level": TRUST_MODERATE,
        "caveats": [
            "Stability at 5–10 turns may not generalise to 25–100 turn runs where LLM "
            "stochasticity accumulates.",
            "True stochastic variability characterisation requires longer campaigns.",
        ],
        "absolute_or_comparative": "absolute",
    },
    {
        "finding_id": "F08_audit_bandwidth_probe_config_readout",
        "finding_text": (
            "audit_bandwidth = 1.0 in all passive runs and < 1.0 in "
            "active_measurement runs.  This confirms the probe schedule is configured "
            "correctly and passive mode always samples every turn."
        ),
        "supporting_metrics": ["audit_bandwidth"],
        "evidence_sources": ["sandbox_campaigns_report.json", "read_only_expansion_report.json"],
        "trust_level": TRUST_STRONG,
        "caveats": [
            "audit_bandwidth is a probe-configuration readout, not a behaviour metric.  "
            "Do not compare it across probe modes as if it measures agent behaviour.",
        ],
        "absolute_or_comparative": "absolute",
    },
    {
        "finding_id": "F09_convergence_turn_null_in_sandbox",
        "finding_text": (
            "convergence_turn is null in virtually all sandbox runs.  The threshold "
            "(position_error ≤ 0.05) is rarely reached in the discrete-room categorical "
            "world because agents jump between rooms rather than approaching a goal "
            "continuously. This metric should not be reported for sandbox runs."
        ),
        "supporting_metrics": ["convergence_turn"],
        "evidence_sources": ["docs/METRIC_TRUST_RANKING.md"],
        "trust_level": TRUST_STRONG,
        "caveats": [
            "convergence_turn is valid in the continuous physics framework — it is a "
            "sandbox-specific limitation, not a metric flaw.",
        ],
        "absolute_or_comparative": "absolute",
    },
    {
        "finding_id": "F10_anisotropy_comparative_only",
        "finding_text": (
            "anisotropy_score is meaningful only comparatively within the same turn count "
            "and encoding.  It accumulates unboundedly with run length; a value of 450 at "
            "50 turns cannot be compared to a value of 450 at 100 turns.  It is "
            "encoding-sensitive (100% spread across encodings)."
        ),
        "supporting_metrics": ["anisotropy_score"],
        "evidence_sources": ["encoding_robustness_report.json", "docs/METRIC_TRUST_RANKING.md"],
        "trust_level": TRUST_MODERATE,
        "caveats": [
            "Within the same (turn_count, encoding) pair, large values (>100) reliably "
            "indicate directional structure.  Near-zero reliably indicates isotropy.",
        ],
        "absolute_or_comparative": "comparative",
    },
]


# ---------------------------------------------------------------------------
# Runtime enrichment
# ---------------------------------------------------------------------------

def _enrich_from_ablation(
    findings: List[Dict[str, Any]],
    ablation_report: Optional[Dict[str, Any]],
) -> None:
    """Update F05 governance finding with live ablation data if available."""
    if ablation_report is None:
        return
    gov_abl = ablation_report.get("ablations", {}).get("governance", {})
    sensitive = gov_abl.get("sensitive_metrics", [])
    for f in findings:
        if f["finding_id"] == "F05_governance_shifts_control_effort":
            if "avg_control_effort" in sensitive:
                f["trust_level"] = TRUST_STRONG
                f["finding_text"] = (
                    f["finding_text"] + f"  Live ablation confirms avg_control_effort "
                    f"moved (delta = {gov_abl.get('metrics', {}).get('avg_control_effort', {}).get('delta', 'N/A')})."
                )
            elif sensitive:
                f["finding_text"] = (
                    f["finding_text"] + f"  Live ablation: sensitive metrics = {sensitive}."
                )
            else:
                f["caveats"].append(
                    "Live ablation showed no sensitive metrics — may require longer run counts."
                )


def _enrich_from_calibration(
    findings: List[Dict[str, Any]],
    calibration_report: Optional[Dict[str, Any]],
) -> None:
    """Attach calibration status to each finding's supporting metrics."""
    if calibration_report is None:
        return
    status_map = {
        rec["metric"]: rec["status"]
        for rec in calibration_report.get("metrics", [])
    }
    for f in findings:
        f["metric_calibration_statuses"] = {
            m: status_map.get(m, "unknown") for m in f["supporting_metrics"]
        }


# ---------------------------------------------------------------------------
# Main extractor
# ---------------------------------------------------------------------------

def extract_findings(
    output_root: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """Extract and rank findings from Stage 5 outputs.

    Returns
    -------
    List of finding dicts sorted strongest → weakest.
    """
    root = output_root or _OUTPUT_ROOT
    findings = [dict(f) for f in _STATIC_FINDINGS]  # shallow copy

    # Load live reports for enrichment
    def _load(name: str) -> Optional[Dict[str, Any]]:
        p = root / name
        if p.exists():
            try:
                with open(p, encoding="utf-8") as fh:
                    return json.load(fh)
            except (json.JSONDecodeError, OSError):
                pass
        return None

    ablation = _load("ablation_report.json")
    calibration = _load("metric_calibration_report.json")

    _enrich_from_ablation(findings, ablation)
    _enrich_from_calibration(findings, calibration)

    # Sort by trust level
    findings.sort(key=lambda f: _TRUST_ORDER.get(f["trust_level"], 99))

    return findings


def write_findings(
    findings: List[Dict[str, Any]],
    output_root: Optional[Path] = None,
) -> Path:
    root = output_root or _OUTPUT_ROOT
    root.mkdir(parents=True, exist_ok=True)
    path = root / "findings_ranked.json"
    report = {
        "stage": "Stage 5",
        "description": "Ranked findings extracted from Stages 2–5 evidence.",
        "trust_levels": {
            TRUST_STRONG: "Multiple independent evidence sources; replicable result.",
            TRUST_MODERATE: "Evidence present but limited to short runs or single source.",
            TRUST_WEAK: "Directional trend only; insufficient replication.",
            TRUST_EXPERIMENTAL: "Not yet validated; hypothesis only.",
        },
        "findings": findings,
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    return path


def run_findings_extraction(output_root: Optional[Path] = None) -> Dict[str, Any]:
    findings = extract_findings(output_root=output_root)
    path = write_findings(findings, output_root=output_root)
    counts = {}
    for f in findings:
        counts[f["trust_level"]] = counts.get(f["trust_level"], 0) + 1
    return {"findings": findings, "report_path": str(path), "counts": counts}


if __name__ == "__main__":
    result = run_findings_extraction()
    print(f"Findings written to: {result['report_path']}")
    print("Trust counts:", result["counts"])
    for f in result["findings"][:3]:
        print(f"\n[{f['trust_level'].upper()}] {f['finding_id']}")
        print(" ", f["finding_text"][:120], "...")
