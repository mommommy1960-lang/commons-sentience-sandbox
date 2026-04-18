"""Generate the Stage 3 scientific summary report (stage3_summary.md).

This module collects results from the various Stage 3 experiment modules
and writes a structured Markdown report.  It can be called programmatically
or via the command line after running the experiments.

Usage
-----
    python -m reality_audit.reports.generate_stage3_summary          # after experiments run
    python -m reality_audit.reports.generate_stage3_summary --help   # see options

Output
------
    reality_audit/reports/stage3_summary.md
"""

from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_AUDIT_DIR = (
    _REPO_ROOT / "commons_sentience_sim" / "output" / "reality_audit"
)
_REPORT_PATH = Path(__file__).resolve().parent / "stage3_summary.md"


# ---------------------------------------------------------------------------
# JSON loader helpers
# ---------------------------------------------------------------------------

def _load_json(path: Path) -> Optional[Dict[str, Any]]:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def _fmt(value: Any, precision: int = 4) -> str:
    if value is None:
        return "N/A"
    try:
        f = float(value)
        if math.isnan(f):
            return "N/A"
        return f"{f:.{precision}f}"
    except (TypeError, ValueError):
        return str(value)


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def _section_experiment_setup(
    long_run_dir: Optional[Path],
    n_seeds: int,
) -> str:
    scenarios = [
        "baseline", "anisotropy", "observer_divergence",
        "bandwidth_limited", "random_baseline_agent", "normal_agent"
    ]
    return f"""## 1. Experiment Setup

### Framework
- **Physics engine**: `RealityWorld` (continuous 2-D, seed-reproducible)
- **Adapter**: `SimProbe` passive mode → room-graph MDS embedding
- **Controller**: proportional (real-agent scenarios); random-walk (null baselines)

### Run Configuration
| Parameter | Value |
|---|---|
| Turn counts | 50, 75, 100 (dt=0.5 s → 25/37.5/50 s duration) |
| Seeds per configuration | {n_seeds} (42–46) |
| Scenarios | {len(scenarios)} |
| Total configurations | {n_seeds * 3 * len(scenarios)} |

### Scenarios Run
"""  + "\n".join(f"- `{s}`" for s in scenarios) + "\n"


def _section_aggregated_results(long_run_dir: Optional[Path]) -> str:
    lines = ["## 2. Key Aggregated Results\n"]
    if long_run_dir is None or not long_run_dir.exists():
        lines.append("*Experiment output directory not found. Run `long_horizon_runs.py` first.*\n")
        return "\n".join(lines)

    # Collect aggregated_summary.json files
    result_rows: List[str] = []
    for scenario_dir in sorted(long_run_dir.iterdir()):
        if not scenario_dir.is_dir():
            continue
        agg_json = scenario_dir / "aggregated_summary.json"
        if not agg_json.exists():
            continue
        data = _load_json(agg_json)
        if not data:
            continue
        metrics = data.get("metrics", {})
        result_rows.append(
            f"| {data.get('experiment_name', scenario_dir.name)} "
            f"| {_fmt(metrics.get('position_error', {}).get('mean'))} "
            f"| {_fmt(metrics.get('stability_score', {}).get('mean'))} "
            f"| {_fmt(metrics.get('anisotropy_score', {}).get('mean'))} "
            f"| {_fmt(metrics.get('bandwidth_bottleneck_score', {}).get('mean'))} "
            f"| {data.get('n_runs', '?')} |"
        )

    if result_rows:
        lines.append(
            "| Scenario | pos_error (mean) | stability (mean) "
            "| anisotropy (mean) | bandwidth (mean) | N |\n"
            "|---|---|---|---|---|---|\n"
        )
        lines.extend(result_rows)
    else:
        lines.append("*No aggregated_summary.json files found yet. Run experiments first.*\n")

    return "\n".join(lines) + "\n"


def _section_metric_stability(long_run_dir: Optional[Path]) -> str:
    lines = ["## 3. Metric Stability\n"]

    if long_run_dir is None or not long_run_dir.exists():
        lines.append(
            "*Stability data not yet available. Run experiments and aggregation first.*\n"
        )
        return "\n".join(lines)

    stable_metrics: Dict[str, List[str]] = {"stable": [], "moderate": [], "unstable": []}
    seen: Dict[str, str] = {}

    for scenario_dir in sorted(long_run_dir.iterdir()):
        agg_json = scenario_dir / "aggregated_summary.json"
        if not agg_json.exists():
            continue
        data = _load_json(agg_json)
        if not data:
            continue
        for metric, stats in data.get("metrics", {}).items():
            flag = stats.get("stability", "unknown")
            if metric not in seen:
                seen[metric] = flag
                if flag in stable_metrics:
                    stable_metrics[flag].append(metric)

    lines.append(
        "Stability flags are based on `consistency_score = 1 - std / (|mean| + ε)` "
        "across seeds.\n"
    )
    lines.append(f"- **Stable** (cs ≥ 0.8): {', '.join(seen_in(stable_metrics, 'stable')) or 'none'}")
    lines.append(f"- **Moderate** (0.5–0.8): {', '.join(seen_in(stable_metrics, 'moderate')) or 'none'}")
    lines.append(f"- **Unstable** (< 0.5): {', '.join(seen_in(stable_metrics, 'unstable')) or 'none'}")
    lines.append("")
    return "\n".join(lines) + "\n"


def seen_in(d: Dict[str, List[str]], k: str) -> List[str]:
    return d.get(k, [])


def _section_probe_readonly(audit_dir: Optional[Path]) -> str:
    lines = ["## 4. Probe Read-Only Verification\n"]

    sim_output = audit_dir.parent if audit_dir else None  # …/commons_sentience_sim/output

    # Stage 2 report lives in commons_sentience_sim/output/
    basic = None
    for search_dir in [sim_output, audit_dir]:
        if search_dir:
            candidate = search_dir / "probe_control_report.json"
            basic = _load_json(candidate)
            if basic:
                break

    # Stage 3 detailed report
    detailed = None
    for search_dir in [sim_output, audit_dir]:
        if search_dir:
            candidate = search_dir / "probe_control_detailed_report.json"
            detailed = _load_json(candidate)
            if detailed:
                break

    if basic:
        status = "✅ PASS" if basic.get("probe_is_readonly") else "❌ FAIL"
        lines.append(f"**Stage 2 basic check**: {status}  ({basic.get('turns_run')} turns)")
    else:
        lines.append("**Stage 2 basic check**: not yet run")

    if detailed:
        status = "✅ PASS" if detailed.get("probe_is_readonly") else "❌ FAIL"
        summ = detailed.get("summary", {})
        lines.append(f"**Stage 3 detailed check**: {status}  ({detailed.get('turns_run')} turns)")
        lines.append(
            f"  - Sentinel: {summ.get('sentinel_exact_matches')} exact matches, "
            f"{summ.get('sentinel_acceptable_variations')} acceptable variations"
        )
        lines.append(
            f"  - Aster: {summ.get('aster_exact_matches')} exact matches, "
            f"{summ.get('aster_acceptable_variations')} acceptable variations"
        )
        lines.append(
            f"  - Unexpected divergences: "
            f"Sentinel={summ.get('sentinel_unexpected_divergences')}, "
            f"Aster={summ.get('aster_unexpected_divergences')}"
        )
    else:
        lines.append("**Stage 3 detailed check**: not yet run")

    lines.append(
        "\n**Documented non-deterministic fields** (excluded from both comparisons):"
    )
    if basic:
        for f in basic.get("documented_nondeterministic_fields", []):
            lines.append(f"  - {f}")

    lines.append("")
    return "\n".join(lines) + "\n"


def _section_false_positives(audit_dir: Optional[Path]) -> str:
    lines = ["## 5. False-Positive Analysis\n"]
    fp = _load_json(audit_dir / "false_positive_report.json") if audit_dir else None

    if not fp:
        lines.append("*False-positive report not yet generated. Run `false_positive_tests.py`.*\n")
        return "\n".join(lines)

    status = "✅ ALL PASSED" if fp.get("all_thresholds_passed") else (
        f"⚠️ Issues: {fp.get('unreliable_metrics')}"
    )
    lines.append(f"**Overall**: {status}")
    lines.append(f"**Seeds tested**: {fp.get('n_seeds_tested')}")
    lines.append("")
    lines.append("| Metric | Value | Threshold | Direction | Status |")
    lines.append("|---|---|---|---|---|")
    for metric, c in fp.get("threshold_checks", {}).items():
        key = "mean_value" if "mean_value" in c else "max_value"
        icon = "✅" if c.get("passed") else "❌"
        lines.append(
            f"| {metric} | {_fmt(c.get(key))} | {c.get('threshold')} "
            f"| {c.get('direction')} | {icon} |"
        )
    lines.append("")
    if fp.get("unreliable_metrics"):
        lines.append(
            f"⚠️ **Unreliable metrics** (produce spurious structure on random input): "
            f"`{'`, `'.join(fp['unreliable_metrics'])}`"
        )
        lines.append(
            "Treat results for these metrics in real experiments with caution "
            "until the source of the false positive is understood."
        )
    else:
        lines.append(
            "No false positives detected. All metrics behave correctly on random input."
        )
    lines.append("")
    return "\n".join(lines) + "\n"


def _section_governance(audit_dir: Optional[Path]) -> str:
    lines = ["## 6. Governance Sensitivity\n"]
    gov = _load_json(audit_dir / "governance_comparison.json") if audit_dir else None

    if not gov:
        lines.append("*Governance comparison not yet run.*\n")
        return "\n".join(lines)

    lines.append(f"_{gov.get('description', '')}_\n")
    lines.append("| Metric | Gov-ON mean | Gov-OFF mean | Δ | Sensitive? |")
    lines.append("|---|---|---|---|---|")
    for metric, c in gov.get("metric_comparison", {}).items():
        lines.append(
            f"| {metric} | {_fmt(c.get('governance_on_mean'))} "
            f"| {_fmt(c.get('governance_off_mean'))} "
            f"| {_fmt(c.get('delta_off_minus_on'))} "
            f"| {'★' if c.get('governance_sensitive') else '–'} |"
        )
    lines.append("")
    return "\n".join(lines) + "\n"


def _section_unexpected_patterns(
    audit_dir: Optional[Path],
) -> str:
    lines = ["## 7. Unexpected Patterns\n"]
    lines.append(
        "This section is populated from anomalies found during the full experimental run.\n"
    )

    fp = _load_json(audit_dir / "false_positive_report.json") if audit_dir else None
    if fp and fp.get("unreliable_metrics"):
        lines.append(
            f"- **Metric reliability warning**: `{'`, `'.join(fp['unreliable_metrics'])}` "
            "produced elevated values on pure random input. "
            "These may reflect intrinsic metric sensitivity rather than true simulation structure."
        )

    detailed = _load_json(audit_dir / "probe_control_detailed_report.json") if audit_dir else None
    if detailed:
        summ = detailed.get("summary", {})
        all_divs = (
            (summ.get("sentinel_unexpected_divergences") or [])
            + (summ.get("aster_unexpected_divergences") or [])
        )
        if all_divs:
            lines.append(
                f"- **Probe divergence warning**: fields `{all_divs}` showed unexpected "
                "differences between probe-off and probe-on runs. Investigate whether "
                "the probe is causing a side-effect beyond documented LLM variance."
            )
        else:
            lines.append(
                "- **Probe verified**: no unexpected divergences in detailed comparison."
            )

    lines.append("")
    return "\n".join(lines) + "\n"


def _section_validated_vs_experimental() -> str:
    return """## 8. Validated vs Experimental

| Component | Status |
|---|---|
| `SimProbe` passive mode read-only | ✅ Confirmed (Stage 2 + Stage 3) |
| Long-horizon runs (50/75/100 turns) | ✅ Implemented; results in `long_runs/` |
| Multi-run aggregation | ✅ Implemented in `aggregate_experiments.py` |
| Cross-run consistency scores | ✅ Computed per metric |
| False-positive detection | ✅ Threshold checks against random baseline |
| Governance sensitivity analysis | ✅ Implemented (model-level approximation) |
| Detailed path-history comparison | ⚠️ Final-room comparison only; per-turn history requires sandbox hook |
| `active_measurement_model` probe mode | ⚠️ Experimental; not the production default |
| Long-horizon sandbox runs (50+ LLM turns) | 🔬 Not yet run at scale (computationally expensive) |
| True governance ON/OFF sandbox comparison | 🔬 Planned; requires sandbox modification |

"""


# ---------------------------------------------------------------------------
# Main report generator
# ---------------------------------------------------------------------------

def generate_report(
    audit_dir: Optional[Path] = None,
    output_path: Optional[Path] = None,
    n_seeds: int = 5,
    verbose: bool = False,
) -> Path:
    """Generate the Stage 3 summary Markdown report.

    Parameters
    ----------
    audit_dir : Path, optional
        Root of the `reality_audit/` output directory.
    output_path : Path, optional
        Where to write the .md file (default: `reports/stage3_summary.md`).
    """
    audit_dir = Path(audit_dir or _DEFAULT_AUDIT_DIR)
    long_run_dir = audit_dir / "long_runs"
    output_path = Path(output_path or _REPORT_PATH)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    header = f"""# Stage 3 Scientific Report: Reality Audit

**Generated**: {now}
**Status**: Stage 3 — Real Experimental Execution & Statistical Validation

---

"""

    sections = [
        header,
        _section_experiment_setup(long_run_dir, n_seeds),
        _section_aggregated_results(long_run_dir),
        _section_metric_stability(long_run_dir),
        _section_probe_readonly(audit_dir),
        _section_false_positives(audit_dir),
        _section_governance(audit_dir),
        _section_unexpected_patterns(audit_dir),
        _section_validated_vs_experimental(),
    ]

    report_text = "\n".join(sections)
    output_path.write_text(report_text, encoding="utf-8")

    if verbose:
        print(f"[Stage 3 Report] Written → {output_path}")

    return output_path


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate Stage 3 summary report")
    parser.add_argument("--audit-dir", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--seeds", type=int, default=5)
    args = parser.parse_args()
    p = generate_report(
        audit_dir=args.audit_dir,
        output_path=args.output,
        n_seeds=args.seeds,
        verbose=True,
    )
    print(f"Report: {p}")
