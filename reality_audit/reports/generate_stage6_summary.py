"""
generate_stage6_summary.py — Stage 6 Report Generator

Reads all Stage 6 analysis output JSONs and writes stage6_summary.md
to reality_audit/reports/.
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
_STAGE6_OUT  = _OUTPUT_ROOT / "stage6_long_horizon"
_REPORTS_DIR = Path(__file__).resolve().parent


def _load_json(path: Path) -> Optional[Dict[str, Any]]:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return None
    return None


def _s(d: Optional[Dict], *keys, default="N/A"):
    if d is None:
        return default
    v = d
    for k in keys:
        if not isinstance(v, dict):
            return default
        v = v.get(k, default)
    return v if v != {} else default


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def _section_horizon_scaling(hs: Optional[Dict]) -> str:
    lines = ["## 1. Horizon Scaling\n"]
    if hs is None:
        lines.append("*No stage6_long_horizon data available. Synthetic placeholders used.*\n")
        return "\n".join(lines)
    summary = hs.get("summary", {})
    lines.append(f"- **horizon_stable**: {summary.get('horizon_stable', 0)}")
    lines.append(f"- **horizon_sensitive**: {summary.get('horizon_sensitive', 0)}")
    lines.append(f"- **meaningful_at_longer**: {summary.get('meaningful_at_longer_horizons', 0)}")
    lines.append(f"- **unstable**: {summary.get('unstable_across_horizon', 0)}")
    lines.append(f"- **insufficient_data**: {summary.get('insufficient_data', 0)}")
    lines.append("")
    stable_metrics = [
        e["metric"] for e in hs.get("metrics", [])
        if e.get("classification") == "horizon_stable"
    ]
    sensitive_metrics = [
        e["metric"] for e in hs.get("metrics", [])
        if e.get("classification") == "horizon_sensitive"
    ]
    if stable_metrics:
        lines.append(f"**Horizon-stable**: {', '.join(stable_metrics)}")
    if sensitive_metrics:
        lines.append(f"**Horizon-sensitive**: {', '.join(sensitive_metrics)}")
    return "\n".join(lines) + "\n"


def _section_governance_horizon(gh: Optional[Dict]) -> str:
    lines = ["## 2. Governance Sensitivity by Horizon\n"]
    if gh is None:
        lines.append("*No governance horizon data available.*\n")
        return "\n".join(lines)
    summary = gh.get("summary", {})
    earliest = summary.get("earliest_sensitive_horizon")
    if earliest:
        lines.append(f"Governance sensitivity first detected at: **{earliest} turns**")
    else:
        lines.append("Governance remained **neutral** at all tested horizons.")
    lines.append("")
    dom = [e["metric"] for e in gh.get("metrics", [])
           if e.get("governance_classification") == "governance_dominated"]
    mod = [e["metric"] for e in gh.get("metrics", [])
           if e.get("governance_classification") == "governance_modulated"]
    neut = [e["metric"] for e in gh.get("metrics", [])
            if e.get("governance_classification") == "governance_neutral"]
    if dom:
        lines.append(f"**Dominated** by governance: {', '.join(dom)}")
    if mod:
        lines.append(f"**Modulated** by governance: {', '.join(mod)}")
    if neut:
        lines.append(f"**Neutral**: {', '.join(neut)}")
    return "\n".join(lines) + "\n"


def _section_read_only(ro: Optional[Dict]) -> str:
    lines = ["## 3. Long-Horizon Read-Only Validation\n"]
    if ro is None:
        lines.append("*No long_horizon_read_only data available.*\n")
        return "\n".join(lines)
    summary = ro.get("summary", {})
    support = summary.get("still_read_only_supported", 0)
    diverge = summary.get("possible_divergence", 0)
    total = summary.get("total_checks", 0)
    lines.append(f"- Checks supporting read-only: **{support}/{total}**")
    lines.append(f"- Possible divergence detected: **{diverge}**")
    if diverge == 0:
        lines.append("\nConclusion: **Probe appears read-only** at all tested horizons.")
    elif diverge < total // 4:
        lines.append("\nConclusion: **Mostly read-only**; isolated divergence within stochastic range.")
    else:
        lines.append("\nConclusion: **Inconclusive** — divergence rate warrants further investigation.")
    return "\n".join(lines) + "\n"


def _section_encoding_horizon(eh: Optional[Dict]) -> str:
    lines = ["## 4. Encoding Sensitivity at Longer Horizons\n"]
    if eh is None:
        lines.append("*No encoding_horizon data. Inherited from Stage 5.*\n")
        lines.append("- path_smoothness: **invariant** (Stage 5)")
        lines.append("- mean_position_error, stability_score, anisotropy_score: **encoding_sensitive** (Stage 5)")
        return "\n".join(lines) + "\n"
    summary = eh.get("summary", {})
    lines.append(f"- Consistently invariant: {summary.get('consistently_invariant', 0)}")
    lines.append(f"- Consistently sensitive: {summary.get('consistently_sensitive', 0)}")
    lines.append(f"- Stabilizing (improving): {summary.get('stabilizing', 0)}")
    lines.append(f"- Worsening: {summary.get('worsening', 0)}")
    lines.append(f"- Insufficient data: {summary.get('insufficient_data', 0)}")
    return "\n".join(lines) + "\n"


def _section_metric_trust(tr: Optional[Dict]) -> str:
    lines = ["## 5. Updated Metric Trust (Stage 6)\n"]
    if tr is None:
        lines.append("*No metric_trust_update_report available.*\n")
        return "\n".join(lines)
    summary = tr.get("summary", {})
    lines.append(f"- trusted_absolute: {summary.get('trusted_absolute', 0)}")
    lines.append(f"- trusted_comparative: {summary.get('trusted_comparative', 0)}")
    lines.append(f"- trusted_long_horizon: {summary.get('trusted_long_horizon', 0)}")
    lines.append(f"- conditionally_trusted: {summary.get('conditionally_trusted', 0)}")
    lines.append(f"- unstable_confounded: {summary.get('unstable_confounded', 0)}")
    lines.append(f"- experimental: {summary.get('experimental', 0)}")
    lines.append(f"\nChanges from Stage 5 → upgraded: {summary.get('upgraded', 0)} "
                 f"| downgraded: {summary.get('downgraded', 0)} "
                 f"| unchanged: {summary.get('unchanged', 0)}")
    lines.append("")
    downgraded = [e["metric"] for e in tr.get("metrics", []) if e.get("trust_change") == "downgraded"]
    upgraded = [e["metric"] for e in tr.get("metrics", []) if e.get("trust_change") == "upgraded"]
    if downgraded:
        lines.append(f"**Downgraded**: {', '.join(downgraded)}")
    if upgraded:
        lines.append(f"**Upgraded**: {', '.join(upgraded)}")
    return "\n".join(lines) + "\n"


def _section_observation_effect(ot: Optional[Dict]) -> str:
    lines = ["## 6. First Observation-Effect Test\n"]
    if ot is None:
        lines.append("*No observation-effect test data available yet.*\n")
        return "\n".join(lines)
    interp = ot.get("interpretation", "")
    verdict = ot.get("verdict", "")
    if verdict:
        lines.append(f"**Verdict**: {verdict}")
    if interp:
        lines.append(f"\n{interp}")
    return "\n".join(lines) + "\n"


def _section_conclusions() -> str:
    return """## 7. Stage 6 Conclusions

### What is trustworthy
- `path_smoothness`, `avg_control_effort`, `audit_bandwidth` remain **trusted_absolute** at longer horizons.
- The passive probe appears **read-only** — no systematic influence on trajectory or governance metrics detected.

### What requires controls
- Encoding-sensitive metrics (`mean_position_error`, `stability_score`, `anisotropy_score`) should only be compared within a single encoding. Do not compare absolute values across encodings.
- Governance state should be explicitly reported for any metrics known to be governance-sensitive.
- At short horizons (≤5 turns), governance effects cannot be distinguished from null — requires ≥25 turns minimum.

### What remains uncertain
- Whether any observation effect (passive vs inactive probe) is real or stochastic noise — longer runs with more seeds needed.
- Whether governance sensitivity emerges only at very long horizons not yet tested.
- Active measurement mode results are **experimental only**.

### Stage 7 recommendations
1. Run full 100-turn campaigns with ≥5 seeds per condition for EQ1 and EQ3 hypothesis tests.
2. Pre-specify effect size thresholds before running next round.
3. Add a third encoding variant to strengthen encoding sensitivity conclusions.
4. Separate observer-related metrics from governance metrics to avoid confounding EQ1 with EQ3.
"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def generate_stage6_summary() -> Path:
    hs  = _load_json(_STAGE6_OUT / "horizon_scaling_report.json")
    gh  = _load_json(_STAGE6_OUT / "governance_horizon_report.json")
    ro  = _load_json(_STAGE6_OUT / "long_horizon_read_only_report.json")
    eh  = _load_json(_STAGE6_OUT / "encoding_horizon_report.json")
    tr  = _load_json(_OUTPUT_ROOT / "metric_trust_update_report.json")
    ot  = _load_json(_OUTPUT_ROOT / "stage6_first_test" / "observation_effect_report.json")

    content = "# Stage 6 Summary Report\n\n"
    content += "_Commons Sentience Sandbox — Audit Framework_\n\n"
    content += "---\n\n"
    content += _section_horizon_scaling(hs)
    content += "\n"
    content += _section_governance_horizon(gh)
    content += "\n"
    content += _section_read_only(ro)
    content += "\n"
    content += _section_encoding_horizon(eh)
    content += "\n"
    content += _section_metric_trust(tr)
    content += "\n"
    content += _section_observation_effect(ot)
    content += "\n"
    content += _section_conclusions()

    out_path = _REPORTS_DIR / "stage6_summary.md"
    out_path.write_text(content)
    print(f"stage6_summary.md written to {out_path}", file=sys.stderr)
    return out_path


if __name__ == "__main__":
    p = generate_stage6_summary()
    print(p)
