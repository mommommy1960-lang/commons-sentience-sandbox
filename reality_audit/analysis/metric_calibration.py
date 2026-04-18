"""
metric_calibration.py — Assign calibration status to each reality-audit metric
based on cumulative evidence from Stages 1–4.

Calibration statuses
--------------------
A  trusted_absolute     — valid for absolute interpretation (no baseline needed)
B  trusted_comparative  — valid when comparing two runs of the same configuration
C  unstable_confounded  — known confounds that prevent safe interpretation
D  experimental         — not yet validated; for hypothesis generation only

Evidence sources used
---------------------
- Stage 2 validation scenarios (physics framework, 6 world modes)
- Stage 3 false-positive tests
- Stage 4 sandbox campaigns
- Stage 4 encoding robustness (BFS+MDS vs pure-hop vs manual topological)
- Stage 4 governance sensitivity (governance on vs off)
- Stage 4 read-only expansion (expanded probe validation)
- Stage 4 sandbox variability (CV-based stability classification)

Output
------
metric_calibration_report.json  — one entry per metric
metric_calibration_summary.csv  — flat table
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_OUTPUT_ROOT = _REPO_ROOT / "commons_sentience_sim" / "output" / "reality_audit"

# ---------------------------------------------------------------------------
# Status constants
# ---------------------------------------------------------------------------

STATUS_TRUSTED_ABSOLUTE    = "trusted_absolute"
STATUS_TRUSTED_COMPARATIVE = "trusted_comparative"
STATUS_UNSTABLE_CONFOUNDED = "unstable_confounded"
STATUS_EXPERIMENTAL        = "experimental"


# ---------------------------------------------------------------------------
# Static evidence catalogue
#
# Each entry encodes what we know from Stages 1–4.  Fields:
#   metric           — canonical metric name
#   status           — one of the four constants above
#   meaning          — plain-English measurement intent
#   evidence         — list of (stage, finding) pairs
#   confounds        — list of known confound descriptions
#   caveats          — usage caveats
#   encoding_sensitive — bool from Stage 4 encoding robustness
#   governance_sensitive — bool from Stage 4 governance campaigns
#   fp_threshold     — false-positive threshold from Stage 3 (if any)
# ---------------------------------------------------------------------------

_METRIC_CATALOGUE: List[Dict[str, Any]] = [
    {
        "metric": "path_smoothness",
        "status": STATUS_TRUSTED_ABSOLUTE,
        "meaning": (
            "Fraction of turns where the agent changed room; measures room-transition rate. "
            "0 = never moved; 1 = moved every turn."
        ),
        "evidence": [
            ("Stage 2", "Validated across all 6 physics world-modes; correctly distinguishes "
             "random-walk (high) from goal-seeking (moderate) agents."),
            ("Stage 3", "Consistent across 50-turn sandbox runs; no false positives."),
            ("Stage 4 encoding", "Classified ROBUST — spread < 5% across three encodings."),
            ("Stage 4 variability", "Classified deterministic_stable (CV < 0.01)."),
        ],
        "confounds": [
            "Categorical world: metric is 0/1 per turn (agent moves or does not), "
            "so values cluster at discrete fractions rather than a continuous range.",
        ],
        "caveats": [
            "Compare across configs to detect movement-pattern shifts.",
            "Not a measure of goal-seeking quality — high path_smoothness can also "
            "result from aimless movement.",
        ],
        "encoding_sensitive": False,
        "governance_sensitive": False,
        "fp_threshold": None,
    },
    {
        "metric": "avg_control_effort",
        "status": STATUS_TRUSTED_ABSOLUTE,
        "meaning": (
            "Fraction of agent actions blocked by GovernanceEngine.check_action; "
            "direct proxy for governance adherence / conflict rate."
        ),
        "evidence": [
            ("Stage 2", "Verified to move under structured governance conditions."),
            ("Stage 3", "Governance campaigns confirmed real action blocking effect."),
            ("Stage 4 variability", "Classified deterministic_stable."),
        ],
        "confounds": [
            "Agents rarely choose blockable actions in low-conflict scenarios; "
            "score anchors near 0 in baseline runs.",
        ],
        "caveats": [
            "Near-0 baseline is expected — do not interpret as a malfunction.",
            "Values > 0.3 are strongly meaningful.",
        ],
        "encoding_sensitive": False,
        "governance_sensitive": True,
        "fp_threshold": 0.95,
    },
    {
        "metric": "audit_bandwidth",
        "status": STATUS_TRUSTED_ABSOLUTE,
        "meaning": (
            "Fraction of turns where the audit sensor observed; reflects probe schedule, "
            "not agent behaviour. Passive mode always = 1.0."
        ),
        "evidence": [
            ("Stage 2", "Passive always 1.0 by construction; active_measurement < 1.0 confirms "
             "schedule sampling."),
            ("Stage 4 read-only", "Confirmed exact_match across paired passive runs."),
        ],
        "confounds": [],
        "caveats": [
            "In passive mode this is a probe-configuration readout, not a behaviour measure.",
            "Do not compare passive vs active values as behaviour differences.",
        ],
        "encoding_sensitive": False,
        "governance_sensitive": False,
        "fp_threshold": None,
    },
    {
        "metric": "stability_score",
        "status": STATUS_TRUSTED_COMPARATIVE,
        "meaning": (
            "Inverse variance of position-error across the run; "
            "high stability = consistent agent-to-goal relationship."
        ),
        "evidence": [
            ("Stage 2", "Full validation in physics framework; distinguishes structured from "
             "random agents."),
            ("Stage 3", "Stage 3 long-horizon runs confirmed directional consistency."),
            ("Stage 4 encoding", "Classified ENCODING-SENSITIVE — 49.8% spread "
             "across three encodings."),
            ("Stage 4 variability", "Classified deterministic_stable within single encoding."),
        ],
        "confounds": [
            "MDS coordinate scale varies across runs (not globally fixed); "
            "absolute value is not comparable across different coordinate instances.",
            "Values depend on which rooms the agent visited and the specific MDS layout.",
        ],
        "caveats": [
            "Compare only within the same coordinate encoding and room graph.",
            "Values > 0.3 suggest stable goal relationship.",
        ],
        "encoding_sensitive": True,
        "governance_sensitive": False,
        "fp_threshold": 0.05,
    },
    {
        "metric": "mean_position_error",
        "status": STATUS_TRUSTED_COMPARATIVE,
        "meaning": (
            "Mean Euclidean distance from measured agent position to goal room position "
            "in the MDS 2-D embedding."
        ),
        "evidence": [
            ("Stage 2", "Correctly orders random-walk >> structured >> goal-seeking agents."),
            ("Stage 3", "50-turn sandbox runs consistent within encoding."),
            ("Stage 4 encoding", "Classified ENCODING-SENSITIVE — 37.3% spread."),
            ("Stage 4 variability", "Classified deterministic_stable within encoding."),
        ],
        "confounds": [
            "Units depend on MDS coordinate scale (~[-1,1] normalised); not inherently "
            "meaningful in absolute terms.",
            "~0.97 typical for structured runs; ~11.6+ for random walk — gap is "
            "real but not calibrated in real-world units.",
        ],
        "caveats": [
            "Use for ordinal comparison only (ranking agents by goal-seeking quality).",
            "Never report as an absolute distance claim.",
        ],
        "encoding_sensitive": True,
        "governance_sensitive": False,
        "fp_threshold": 6.0,
    },
    {
        "metric": "convergence_turn",
        "status": STATUS_TRUSTED_COMPARATIVE,
        "meaning": (
            "First turn where position_error drops below 0.05; proxy for "
            "goal-approach speed."
        ),
        "evidence": [
            ("Stage 2", "Verified in physics framework continuous runs; goal-seeking agents "
             "converge reliably."),
            ("Stage 3", "Rarely achieves threshold in discrete room sandbox."),
        ],
        "confounds": [
            "In the categorical room sandbox, positions are room-level discrete; "
            "exact MDS-coordinate threshold is rarely triggered.",
            "Returns null in most sandbox runs — misleadingly absent.",
        ],
        "caveats": [
            "Report as null in sandbox contexts and note this is physics-framework-specific.",
            "Use room-occupancy of goal room as the sandbox-appropriate proxy instead.",
        ],
        "encoding_sensitive": False,
        "governance_sensitive": False,
        "fp_threshold": None,
    },
    {
        "metric": "quantization_artifact_score",
        "status": STATUS_TRUSTED_COMPARATIVE,
        "meaning": (
            "Variance in measured-vs-true position gaps; detects systematic "
            "measurement artefacts from sensor quantization."
        ),
        "evidence": [
            ("Stage 2", "validated in NOISY_QUANTIZED physics mode; correctly detects "
             "systematic shifts."),
            ("Stage 4 variability", "Always 0 in passive sandbox mode (by construction)."),
        ],
        "confounds": [
            "Always 0 in passive probe mode — passive probe has no quantization.",
            "Only meaningful in active_measurement_model mode.",
        ],
        "caveats": [
            "Use exclusively in active_measurement_model mode to detect sensor staleness.",
            "Do not report in passive-mode analyses without noting it is structurally zero.",
        ],
        "encoding_sensitive": False,
        "governance_sensitive": False,
        "fp_threshold": None,
    },
    {
        "metric": "observer_dependence_score",
        "status": STATUS_UNSTABLE_CONFOUNDED,
        "meaning": (
            "Mean L2 gap between hidden-state position and measured position; "
            "intended to detect agent epistemic opacity."
        ),
        "evidence": [
            ("Stage 2", "Physics framework: non-zero in observer-triggered modes."),
            ("Stage 3", "Calibrated threshold=15.0 to avoid false positives."),
            ("Stage 4", "In passive sandbox probe always 0 (no hidden-state divergence)."),
        ],
        "confounds": [
            "Start-anchored artefact: in non-OBSERVER_TRIGGERED physics modes, "
            "hidden_state.position in raw_log equals the true current position — "
            "there is no independent hidden-state estimate.",
            "In passive sandbox probe this score is always 0 by construction.",
            "In active_measurement_model it measures sensor staleness, not agent "
            "epistemic opacity.",
        ],
        "caveats": [
            "Do NOT interpret as a measure of agent self-awareness or opacity.",
            "Use hidden_measured_gap_path_normalised (observer_metrics) instead.",
        ],
        "encoding_sensitive": False,
        "governance_sensitive": False,
        "fp_threshold": 15.0,
    },
    {
        "metric": "anisotropy_score",
        "status": STATUS_TRUSTED_COMPARATIVE,
        "meaning": (
            "|x_sum − y_sum| / max across all positions; measures directional "
            "movement bias in the 2-D MDS space."
        ),
        "evidence": [
            ("Stage 2", "Near-0 for symmetric random walk; ~450 for x-directed structured runs."),
            ("Stage 4 encoding", "Classified ENCODING-SENSITIVE — 100% spread across encodings."),
        ],
        "confounds": [
            "Accumulates unboundedly over turns — longer runs always produce "
            "higher raw scores.",
            "Sensitive to MDS axis alignment which may vary across runs.",
            "Not comparable across different turn counts.",
        ],
        "caveats": [
            "Compare only within the same turn count and encoding.",
            "Large values (> 100) indicate strong directional structure; near-0 is isotropic.",
            "Never compare absolute values across different run lengths.",
        ],
        "encoding_sensitive": True,
        "governance_sensitive": False,
        "fp_threshold": None,
    },
    {
        "metric": "hidden_measured_gap_raw",
        "status": STATUS_TRUSTED_COMPARATIVE,
        "meaning": (
            "Mean L2 gap between true and audit-measured positions; richer "
            "version of observer_dependence_score adding std and max."
        ),
        "evidence": [
            ("Stage 4", "Observer metrics module; stage-4 comparative design validated."),
        ],
        "confounds": [
            "Always 0 in passive mode — same start-anchoring confound as "
            "observer_dependence_score.",
            "Compare passive vs active runs to isolate sensor staleness effect.",
        ],
        "caveats": [
            "Only meaningful as a passive-vs-active comparison, not as a standalone signal.",
        ],
        "encoding_sensitive": False,
        "governance_sensitive": False,
        "fp_threshold": None,
    },
    {
        "metric": "hidden_measured_gap_path_normalised",
        "status": STATUS_TRUSTED_COMPARATIVE,
        "meaning": (
            "Gap normalised by agent total path length; corrects for run length "
            "and movement magnitude."
        ),
        "evidence": [
            ("Stage 4", "Preferred replacement for observer_dependence_score in "
             "cross-run-length comparisons."),
        ],
        "confounds": [
            "Returns None if agent barely moved (path_length ≈ 0).",
        ],
        "caveats": [
            "Requires path_length > 0 to produce a value.",
            "Meaningful only when comparing runs of different lengths or movement patterns.",
        ],
        "encoding_sensitive": False,
        "governance_sensitive": False,
        "fp_threshold": None,
    },
    {
        "metric": "observation_schedule_sensitivity",
        "status": STATUS_EXPERIMENTAL,
        "meaning": (
            "Ratio of active-measurement gap to passive gap; quantifies how much "
            "the audit schedule inflates apparent opacity."
        ),
        "evidence": [
            ("Stage 4", "Design validated; requires paired runs (same config, different probe)."),
        ],
        "confounds": [
            "Requires two paired runs (passive + active_measurement_model) of identical config.",
            "Ratio undefined if passive gap ≈ 0.",
        ],
        "caveats": [
            "Use when deciding whether to deploy active_measurement vs passive mode.",
            "Ratio > 5 means active mode is highly misleading.",
            "Not yet validated in multi-seed sandbox campaigns.",
        ],
        "encoding_sensitive": False,
        "governance_sensitive": False,
        "fp_threshold": None,
    },
]


# ---------------------------------------------------------------------------
# Calibration engine
# ---------------------------------------------------------------------------

def build_calibration_report(
    output_root: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """Build the calibration report entries from the static catalogue.

    Parameters
    ----------
    output_root : Path, optional
        Override for output directory (defaults to _OUTPUT_ROOT).

    Returns
    -------
    list of dicts, one per metric.
    """
    root = output_root or _OUTPUT_ROOT

    # Optionally enrich with live sandbox variability data
    variability_path = root / "sandbox_variability_report.json"
    variability_index: Dict[str, str] = {}
    if variability_path.exists():
        try:
            with open(variability_path, encoding="utf-8") as fh:
                var_data = json.load(fh)
            # Aggregate across all (config, turns) combinations
            for entry in var_data.get("variability", []):
                for m, cls in entry.get("metrics", {}).items():
                    # Keep most conservative classification seen
                    _order = {
                        "deterministic_stable": 0,
                        "stochastic_but_usable": 1,
                        "too_unstable": 2,
                    }
                    prev = variability_index.get(m, "deterministic_stable")
                    if _order.get(cls, 0) > _order.get(prev, 0):
                        variability_index[m] = cls
        except (json.JSONDecodeError, KeyError):
            pass

    # Optionally enrich with encoding robustness data
    enc_path = root / "encoding_robustness_report.json"
    enc_sensitive: Dict[str, bool] = {}
    if enc_path.exists():
        try:
            with open(enc_path, encoding="utf-8") as fh:
                enc_data = json.load(fh)
            for m, info in enc_data.get("metrics", {}).items():
                enc_sensitive[m] = info.get("verdict", "") == "ENCODING-SENSITIVE"
        except (json.JSONDecodeError, KeyError):
            pass

    records = []
    for entry in _METRIC_CATALOGUE:
        rec = dict(entry)
        # Overwrite encoding_sensitive from live data if available
        metric_key = entry["metric"]
        if metric_key in enc_sensitive:
            rec["encoding_sensitive"] = enc_sensitive[metric_key]
        # Add sandbox variability classification
        rec["sandbox_variability"] = variability_index.get(metric_key, "unknown")
        records.append(rec)

    return records


def write_calibration_report(
    records: List[Dict[str, Any]],
    output_root: Optional[Path] = None,
) -> Path:
    """Write metric_calibration_report.json and metric_calibration_summary.csv."""
    root = output_root or _OUTPUT_ROOT
    root.mkdir(parents=True, exist_ok=True)

    report = {
        "stage": "Stage 5",
        "description": "Metric calibration status based on cumulative Stages 1–4 evidence.",
        "status_legend": {
            STATUS_TRUSTED_ABSOLUTE:    "Valid for absolute interpretation; no baseline needed.",
            STATUS_TRUSTED_COMPARATIVE: "Valid only when comparing two runs of same config.",
            STATUS_UNSTABLE_CONFOUNDED: "Known confounds prevent safe standalone interpretation.",
            STATUS_EXPERIMENTAL:        "Not yet validated; for hypothesis generation only.",
        },
        "metrics": records,
    }

    json_path = root / "metric_calibration_report.json"
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)

    # CSV summary
    csv_path = root / "metric_calibration_summary.csv"
    fieldnames = [
        "metric", "status", "encoding_sensitive", "governance_sensitive",
        "sandbox_variability", "fp_threshold",
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in records:
            writer.writerow(r)

    return json_path


def run_metric_calibration(output_root: Optional[Path] = None) -> Dict[str, Any]:
    """Run full metric calibration pipeline.

    Returns
    -------
    dict with keys:
      ``records``     — list of calibration records
      ``report_path`` — path to written JSON report
      ``counts``      — {status: count} summary
    """
    records = build_calibration_report(output_root=output_root)
    report_path = write_calibration_report(records, output_root=output_root)

    counts: Dict[str, int] = {}
    for r in records:
        counts[r["status"]] = counts.get(r["status"], 0) + 1

    return {
        "records": records,
        "report_path": str(report_path),
        "counts": counts,
    }


if __name__ == "__main__":
    result = run_metric_calibration()
    print(f"Calibration report written to: {result['report_path']}")
    print("Status counts:", result["counts"])
