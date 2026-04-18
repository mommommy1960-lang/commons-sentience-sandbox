"""
generate_stage5_summary.py — Compile Stage 5 experimental results into a
structured Markdown report.

Answers Stage 5 questions:
  Q1. Which metrics are trustworthy for absolute interpretation?
  Q2. Which metrics are comparative only?
  Q3. What remains confounded or encoding-sensitive?
  Q4. What do governance conditions do to metric interpretation?
  Q5. What does the passive probe evidence support?
  Q6. What conclusions are currently justified / not justified?
  Q7. What did ablation studies reveal?
  Q8. How do calibrated campaigns compare across conditions?

Also includes a replication checklist and Stage 6 roadmap.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_OUTPUT_ROOT = _REPO_ROOT / "commons_sentience_sim" / "output" / "reality_audit"
_REPORTS_DIR = Path(__file__).parent


def _load_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        return None


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def _section_metric_trust(cal: Optional[Dict[str, Any]]) -> str:
    lines = ["## Q1 — Metric Trust: Absolute vs Comparative vs Confounded\n"]
    if cal is None:
        lines.append("> _metric_calibration_report.json not found — run metric_calibration first._\n")
        return "\n".join(lines)

    by_status: Dict[str, List[str]] = {}
    for rec in cal.get("metrics", []):
        s = rec["status"]
        by_status.setdefault(s, []).append(rec["metric"])

    status_labels = {
        "trusted_absolute":    "**Trusted — Absolute Interpretation**",
        "trusted_comparative": "**Trusted — Comparative Interpretation Only**",
        "unstable_confounded": "**Unstable / Confounded**",
        "experimental":        "**Experimental**",
    }
    for status, label in status_labels.items():
        metrics = by_status.get(status, [])
        lines.append(f"### {label}\n")
        if metrics:
            for m in metrics:
                lines.append(f"- `{m}`")
        else:
            lines.append("_(none)_")
        lines.append("")
    return "\n".join(lines)


def _section_encoding_invariance(enc_inv: Optional[Dict[str, Any]]) -> str:
    lines = ["## Q3 (Part A) — Encoding Invariance\n"]
    if enc_inv is None:
        lines.append("> _encoding_invariant_report.json not found._\n")
        return "\n".join(lines)
    summary = enc_inv.get("invariance_summary", {})
    lines.append("| Metric | Ordering Invariance |\n|---|---|")
    for m, verdict in summary.items():
        lines.append(f"| `{m}` | {verdict} |")
    lines.append("")
    lines.append(f"> Source: {enc_inv.get('source', 'unknown')}\n")
    return "\n".join(lines)


def _section_governance(gov_interp: Optional[Dict[str, Any]]) -> str:
    lines = ["## Q4 — Governance Interpretation\n"]
    if gov_interp is None:
        lines.append("> _governance_interpretation_report.json not found._\n")
        return "\n".join(lines)
    lines.append(
        "| Metric | Gov Classification | Primary Interpretation | Must Control? |\n"
        "|---|---|---|---|"
    )
    for rec in gov_interp.get("metrics", []):
        lines.append(
            f"| `{rec['metric']}` | {rec['governance_classification']} "
            f"| {rec['primary_interpretation']} | {rec['must_control_for_governance']} |"
        )
    lines.append("")
    constraint = gov_interp.get("key_constraint", "")
    if constraint:
        lines.append(f"> **Key constraint:** {constraint}\n")
    return "\n".join(lines)


def _section_ablations(abl: Optional[Dict[str, Any]]) -> str:
    lines = ["## Q7 — Ablation Studies\n"]
    if abl is None:
        lines.append("> _ablation_report.json not found — run ablation_studies first._\n")
        return "\n".join(lines)
    lines.append(f"Turn count: {abl.get('total_turns', '?')}  Seeds: {abl.get('n_seeds', '?')}\n")
    for abl_name, result in abl.get("ablations", {}).items():
        sensitive = result.get("sensitive_metrics", [])
        la = result.get("label_a", "?")
        lb = result.get("label_b", "?")
        lines.append(f"**{abl_name}** (`{la}` vs `{lb}`)")
        if result.get("note"):
            lines.append(f"  - _{result['note']}_")
        elif sensitive:
            lines.append(f"  - Sensitive metrics: {', '.join(f'`{m}`' for m in sensitive)}")
        else:
            lines.append("  - No metrics moved meaningfully (may need more turns)")
        lines.append("")
    return "\n".join(lines)


def _section_campaigns(comp: Optional[Dict[str, Any]]) -> str:
    lines = ["## Q8 — Calibrated Campaign Comparison\n"]
    if comp is None:
        lines.append("> _campaign_comparison_report.json not found._\n")
        return "\n".join(lines)
    note_exp = comp.get("note_experimental", "")
    if note_exp:
        lines.append(f"> _{note_exp}_\n")
    for pair_label, by_turns in comp.get("comparisons", {}).items():
        lines.append(f"**{pair_label}**")
        if isinstance(by_turns, dict):
            for turns, m_data in sorted(by_turns.items()):
                if isinstance(m_data, dict):
                    meaningful = [m for m, v in m_data.items() if v.get("meaningful")]
                    if meaningful:
                        lines.append(f"  - turns={turns}: meaningful shift in {', '.join(f'`{m}`' for m in meaningful)}")
                    else:
                        lines.append(f"  - turns={turns}: no meaningful differences detected")
        lines.append("")
    return "\n".join(lines)


def _section_findings(findings_data: Optional[Dict[str, Any]]) -> str:
    lines = ["## Ranked Findings\n"]
    if findings_data is None:
        lines.append("> _findings_ranked.json not found._\n")
        return "\n".join(lines)
    for f in findings_data.get("findings", []):
        tid = f.get("finding_id", "?")
        trust = f.get("trust_level", "?")
        ac = f.get("absolute_or_comparative", "?")
        text = f.get("finding_text", "")[:300]
        lines.append(f"### [{trust.upper()}] {tid}  _{ac}_\n")
        lines.append(text)
        caveats = f.get("caveats", [])
        if caveats:
            lines.append("\n**Caveats:**")
            for c in caveats[:2]:
                lines.append(f"- {c}")
        lines.append("")
    return "\n".join(lines)


def _section_stage6_roadmap() -> str:
    return """## Stage 6 Roadmap

Based on Stage 5 outcomes, the following priorities are recommended for Stage 6:

1. **Long-horizon variability campaigns** — Run 50–100 turn campaigns with 5+ seeds
   to characterise true metric variance under LLM stochasticity.

2. **Governance re-analysis at 25+ turns** — Determine at what turn count structural
   governance effects become detectable in spatial metrics.

3. **Cross-encoding validation** — Re-run all Stage 3–4 campaigns under
   PureHop and ManualTopological encodings to confirm ordinal ranking invariance.

4. **Observer metric validation** — Design paired passive/active_measurement
   multi-seed campaign to validate `observation_schedule_sensitivity`.

5. **Threshold re-calibration** — Re-calibrate false-positive thresholds for 50+
   turn campaigns (current thresholds calibrated at 5 turns).

6. **Retire observer_dependence_score** — Replace with
   `hidden_measured_gap_path_normalised` in all future report templates.
"""


# ---------------------------------------------------------------------------
# Master report generator
# ---------------------------------------------------------------------------

def generate_report(output_root: Optional[Path] = None) -> Path:
    root = output_root or _OUTPUT_ROOT
    reports_dir = _REPORTS_DIR

    # Load available reports
    cal         = _load_json(root / "metric_calibration_report.json")
    enc_inv     = _load_json(root / "encoding_invariant_report.json")
    gov_interp  = _load_json(root / "governance_interpretation_report.json")
    abl         = _load_json(root / "ablation_report.json")
    findings_data = _load_json(root / "findings_ranked.json")
    comp_report = _load_json(root / "calibrated_campaigns" / "campaign_comparison_report.json")

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    lines = [
        "# Stage 5 Summary Report",
        "",
        f"**Generated:** {ts}",
        "",
        "**Purpose:** Publication-grade synthesis of Stage 5 calibrated campaigns, "
        "ablation studies, and encoding/governance analyses.",
        "",
        "> This report is conservative.  Findings supported by only short runs or "
        "a single evidence source are labelled **moderate** and caveated.",
        "",
        "---",
        "",
    ]

    lines.append(_section_metric_trust(cal))
    lines.append("")
    lines.append(_section_encoding_invariance(enc_inv))
    lines.append("")
    lines.append(_section_governance(gov_interp))
    lines.append("")
    lines.append(_section_ablations(abl))
    lines.append("")
    lines.append(_section_campaigns(comp_report))
    lines.append("")
    lines.append(_section_findings(findings_data))
    lines.append("")
    lines.append(_section_stage6_roadmap())

    content = "\n".join(lines)
    out_path = reports_dir / "stage5_summary.md"
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(content)

    print(f"stage5_summary.md written to {out_path}")
    return out_path


if __name__ == "__main__":
    generate_report()
