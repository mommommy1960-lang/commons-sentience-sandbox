"""
plot_stage6.py — Stage 6 figures and publication-ready tables.

Figures generated
-----------------
1. horizon_scaling.png              — line plot: metric mean ± std across horizons
2. governance_vs_horizon.png        — grouped bars: governance delta per horizon
3. encoding_sensitivity_vs_horizon.png — heatmap: encoding sensitivity by metric × horizon
4. metric_trust_changes.png         — comparison table: Stage 5 vs Stage 6 trust
5. long_horizon_read_only.png       — bar chart: read-only classification per horizon
6. observation_effect_comparison.png — effect-size plot for probe inactive/passive/active
7. horizon_summary_table.csv / .md  — CSV + markdown export

Output directory
----------------
commons_sentience_sim/output/reality_audit/figures_stage6/
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

_OUTPUT_ROOT = _REPO_ROOT / "commons_sentience_sim" / "output" / "reality_audit"
_STAGE6_OUT  = _OUTPUT_ROOT / "stage6_long_horizon"
_FIGS_DIR    = _OUTPUT_ROOT / "figures_stage6"

# Color palette
_COLORS = {
    "trusted_absolute":    "#2ecc71",
    "trusted_comparative": "#3498db",
    "trusted_long_horizon":"#1abc9c",
    "conditionally_trusted":"#f39c12",
    "unstable_confounded": "#e74c3c",
    "experimental":        "#9b59b6",
    "horizon_stable":               "#2ecc71",
    "horizon_sensitive":            "#f39c12",
    "meaningful_at_longer_horizons":"#3498db",
    "unstable_across_horizon":      "#e74c3c",
    "insufficient_data":            "#95a5a6",
}

_HORIZONS = [5, 25, 50, 100]
_PRIMARY_METRICS = [
    "path_smoothness", "avg_control_effort", "audit_bandwidth",
    "stability_score", "observer_dependence_score",
]


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


def _save(fig: plt.Figure, name: str) -> Path:
    _FIGS_DIR.mkdir(parents=True, exist_ok=True)
    out = _FIGS_DIR / name
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  [plot_stage6] saved → {out}", file=sys.stderr)
    return out


# ---------------------------------------------------------------------------
# Figure 1 — Horizon Scaling
# ---------------------------------------------------------------------------

def plot_horizon_scaling(hs_report: Optional[Dict[str, Any]] = None) -> Path:
    if hs_report is None:
        hs_report = _load_json(_STAGE6_OUT / "horizon_scaling_report.json")

    metrics = _PRIMARY_METRICS
    horizons = [25, 50, 100]

    # Build synthetic data if no live report
    if hs_report is None or not hs_report.get("metrics"):
        # Synthetic: flat lines with noise
        rng = np.random.default_rng(42)
        data = {m: [0.5 + rng.normal(0, 0.03, 1)[0] for _ in horizons] for m in metrics}
        stds = {m: [0.05] * len(horizons) for m in metrics}
        note = " (synthetic)"
    else:
        metric_map = {e["metric"]: e for e in hs_report.get("metrics", [])}
        data = {}
        stds = {}
        for m in metrics:
            entry = metric_map.get(m, {})
            vals = entry.get("means_by_horizon", {})
            std_vals = entry.get("stds_by_horizon", {})
            data[m] = [vals.get(str(h), float("nan")) for h in horizons]
            stds[m] = [std_vals.get(str(h), 0.0) for h in horizons]
        note = ""

    fig, ax = plt.subplots(figsize=(9, 5))
    for i, m in enumerate(metrics):
        y = data[m]
        err = stds[m]
        ax.errorbar(horizons, y, yerr=err, marker="o", label=m, capsize=4)

    ax.set_xlabel("Horizon (turns)")
    ax.set_ylabel("Metric mean")
    ax.set_title(f"Horizon Scaling — Primary Metrics{note}")
    ax.set_xticks(horizons)
    ax.legend(fontsize=7, loc="upper left")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return _save(fig, "horizon_scaling.png")


# ---------------------------------------------------------------------------
# Figure 2 — Governance vs Horizon
# ---------------------------------------------------------------------------

def plot_governance_vs_horizon(gh_report: Optional[Dict[str, Any]] = None) -> Path:
    if gh_report is None:
        gh_report = _load_json(_STAGE6_OUT / "governance_horizon_report.json")

    horizons = [25, 50, 100]
    metrics = ["path_smoothness", "avg_control_effort", "stability_score"]

    if gh_report is None or not gh_report.get("metrics"):
        rng = np.random.default_rng(7)
        deltas = {m: [rng.normal(0, 0.02) for _ in horizons] for m in metrics}
        note = " (synthetic)"
    else:
        metric_map = {e["metric"]: e for e in gh_report.get("metrics", [])}
        deltas = {}
        for m in metrics:
            entry = metric_map.get(m, {})
            by_h = entry.get("delta_by_horizon", {})
            deltas[m] = [by_h.get(str(h), 0.0) for h in horizons]
        note = ""

    x = np.arange(len(horizons))
    width = 0.25
    fig, ax = plt.subplots(figsize=(8, 4))
    for i, m in enumerate(metrics):
        ax.bar(x + i * width, deltas[m], width, label=m)

    ax.axhline(0, color="black", linewidth=0.7, linestyle="--")
    ax.set_xlabel("Horizon (turns)")
    ax.set_ylabel("Governance delta (off − on)")
    ax.set_title(f"Governance Effect vs Horizon{note}")
    ax.set_xticks(x + width)
    ax.set_xticklabels([str(h) for h in horizons])
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()
    return _save(fig, "governance_vs_horizon.png")


# ---------------------------------------------------------------------------
# Figure 3 — Encoding Sensitivity vs Horizon
# ---------------------------------------------------------------------------

def plot_encoding_sensitivity_vs_horizon(eh_report: Optional[Dict[str, Any]] = None) -> Path:
    if eh_report is None:
        eh_report = _load_json(_STAGE6_OUT / "encoding_horizon_report.json")

    metrics = [
        "path_smoothness", "mean_position_error", "stability_score",
        "anisotropy_score", "avg_control_effort",
    ]
    horizons = [5, 25, 50, 100]
    labels = {
        "invariant": 0, "partially_invariant": 1, "encoding_sensitive": 2, "insufficient_data": 3
    }
    cmap_colors = ["#2ecc71", "#f39c12", "#e74c3c", "#95a5a6"]

    if eh_report is None or not eh_report.get("metrics"):
        # Synthetic fallback
        stage5 = {"path_smoothness": 0, "mean_position_error": 2,
                  "stability_score": 2, "anisotropy_score": 2, "avg_control_effort": 0}
        matrix = np.array([[stage5.get(m, 3)] + [stage5.get(m, 3)] * 3 for m in metrics],
                          dtype=float)
        note = " (synthetic)"
    else:
        metric_map = {e["metric"]: e for e in eh_report.get("metrics", [])}
        matrix = []
        for m in metrics:
            row = []
            entry = metric_map.get(m, {})
            # Stage 5 baseline
            s5 = entry.get("stage5_baseline_classification", "insufficient_data")
            row.append(labels.get(s5, 3))
            for h in horizons[1:]:
                hcl = (entry.get("horizon_classifications", {}) or {}).get(str(h), "insufficient_data")
                row.append(labels.get(hcl, 3))
            matrix.append(row)
        matrix = np.array(matrix, dtype=float)
        note = ""

    from matplotlib.colors import ListedColormap
    fig, ax = plt.subplots(figsize=(8, 4))
    cmap = ListedColormap(cmap_colors)
    im = ax.imshow(matrix, aspect="auto", cmap=cmap, vmin=0, vmax=3)

    ax.set_xticks(range(len(horizons)))
    ax.set_xticklabels([f"{h}t" for h in horizons])
    ax.set_yticks(range(len(metrics)))
    ax.set_yticklabels(metrics, fontsize=8)
    ax.set_title(f"Encoding Sensitivity vs Horizon{note}")

    legend_patches = [
        mpatches.Patch(color=cmap_colors[0], label="invariant"),
        mpatches.Patch(color=cmap_colors[1], label="partially_invariant"),
        mpatches.Patch(color=cmap_colors[2], label="encoding_sensitive"),
        mpatches.Patch(color=cmap_colors[3], label="insufficient_data"),
    ]
    ax.legend(handles=legend_patches, loc="lower right", fontsize=7)
    fig.tight_layout()
    return _save(fig, "encoding_sensitivity_vs_horizon.png")


# ---------------------------------------------------------------------------
# Figure 4 — Metric Trust Changes: Stage 5 → Stage 6
# ---------------------------------------------------------------------------

def plot_metric_trust_changes(
    trust_report: Optional[Dict[str, Any]] = None,
) -> Path:
    if trust_report is None:
        trust_report = _load_json(_OUTPUT_ROOT / "metric_trust_update_report.json")

    trust_order = [
        "trusted_absolute", "trusted_comparative", "trusted_long_horizon",
        "conditionally_trusted", "unstable_confounded", "experimental",
    ]
    short_labels = {
        "trusted_absolute": "absolute", "trusted_comparative": "comparative",
        "trusted_long_horizon": "long_horizon", "conditionally_trusted": "conditional",
        "unstable_confounded": "unstable", "experimental": "experimental",
    }

    if trust_report is None or not trust_report.get("metrics"):
        # Hardcoded synthetic
        entries = [
            {"metric": "path_smoothness", "previous_trust_level": "trusted_absolute",
             "trust_level": "trusted_absolute", "trust_change": "unchanged"},
            {"metric": "stability_score", "previous_trust_level": "trusted_comparative",
             "trust_level": "conditionally_trusted", "trust_change": "downgraded"},
            {"metric": "avg_control_effort", "previous_trust_level": "trusted_absolute",
             "trust_level": "trusted_absolute", "trust_change": "unchanged"},
            {"metric": "anisotropy_score", "previous_trust_level": "trusted_comparative",
             "trust_level": "conditionally_trusted", "trust_change": "downgraded"},
        ]
        note = " (synthetic)"
    else:
        entries = trust_report["metrics"]
        note = ""

    x_labels = [e["metric"] for e in entries]
    y_prev = [trust_order.index(e.get("previous_trust_level", "experimental"))
              if e.get("previous_trust_level") in trust_order else 5 for e in entries]
    y_curr = [trust_order.index(e.get("trust_level", "experimental"))
              if e.get("trust_level") in trust_order else 5 for e in entries]

    fig, ax = plt.subplots(figsize=(max(8, len(entries) * 0.9), 5))
    x = np.arange(len(x_labels))
    ax.bar(x - 0.2, y_prev, 0.35, label="Stage 5", color="#3498db", alpha=0.7)
    ax.bar(x + 0.2, y_curr, 0.35, label="Stage 6", color="#e74c3c", alpha=0.7)

    ax.set_xticks(x)
    ax.set_xticklabels(x_labels, rotation=35, ha="right", fontsize=8)
    ax.set_yticks(range(len(trust_order)))
    ax.set_yticklabels([short_labels[t] for t in trust_order], fontsize=8)
    ax.set_ylabel("Trust level (lower = stronger)")
    ax.set_title(f"Metric Trust: Stage 5 vs Stage 6{note}")
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")
    ax.invert_yaxis()
    fig.tight_layout()
    return _save(fig, "metric_trust_changes.png")


# ---------------------------------------------------------------------------
# Figure 5 — Long-Horizon Read-Only Classification
# ---------------------------------------------------------------------------

def plot_long_horizon_read_only(ro_report: Optional[Dict[str, Any]] = None) -> Path:
    if ro_report is None:
        ro_report = _load_json(_STAGE6_OUT / "long_horizon_read_only_report.json")

    horizons = [25, 50, 100]
    class_labels = [
        "still_read_only_supported",
        "no_evidence_of_influence",
        "inconclusive_due_to_stochasticity",
        "possible_divergence_requires_review",
    ]
    class_colors = ["#2ecc71", "#3498db", "#f39c12", "#e74c3c"]
    short_labels = ["read-only OK", "no evidence", "inconclusive", "possible divergence"]

    if ro_report is None or not ro_report.get("horizons"):
        # Synthetic: all read-only supported
        counts_by_h = {h: {"still_read_only_supported": 3, "no_evidence_of_influence": 0,
                           "inconclusive_due_to_stochasticity": 0} for h in horizons}
        note = " (synthetic)"
    else:
        counts_by_h = {}
        for h_entry in ro_report.get("horizons", []):
            h = h_entry.get("total_turns")
            if h is None:
                continue
            cl = h_entry.get("overall_classification", "insufficient_data")
            counts_by_h.setdefault(h, {}).setdefault(cl, 0)
            counts_by_h[h][cl] = counts_by_h[h].get(cl, 0) + 1
        note = ""

    x = np.arange(len(horizons))
    width = 0.18
    fig, ax = plt.subplots(figsize=(8, 4))
    for i, (cl, color, short) in enumerate(zip(class_labels, class_colors, short_labels)):
        vals = [counts_by_h.get(h, {}).get(cl, 0) for h in horizons]
        ax.bar(x + (i - 1.5) * width, vals, width, color=color, alpha=0.85, label=short)

    ax.set_xticks(x)
    ax.set_xticklabels([f"{h} turns" for h in horizons])
    ax.set_ylabel("Number of checks")
    ax.set_title(f"Long-Horizon Read-Only Validation{note}")
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()
    return _save(fig, "long_horizon_read_only.png")


# ---------------------------------------------------------------------------
# Figure 6 — Observation Effect Comparison (first real test)
# ---------------------------------------------------------------------------

def plot_observation_effect_comparison(
    first_test_report: Optional[Dict[str, Any]] = None,
) -> Path:
    report_path = _OUTPUT_ROOT / "stage6_first_test" / "observation_effect_report.json"
    if first_test_report is None:
        first_test_report = _load_json(report_path)

    horizons = [25, 50, 100]
    conditions = ["lh_C_inactive", "lh_A", "lh_D_active"]
    condition_labels = ["Inactive probe", "Passive probe", "Active measurement"]
    metrics = ["observer_dependence_score", "stability_score", "path_smoothness"]

    if first_test_report is None or not first_test_report.get("comparisons"):
        rng = np.random.default_rng(123)
        data = {c: {m: rng.normal(0.5, 0.1) for m in metrics} for c in conditions}
        note = " (synthetic)"
    else:
        comps = first_test_report.get("comparisons", {})
        # Flatten by condition across last available horizon
        data = {c: {m: 0.0 for m in metrics} for c in conditions}
        for comp_key, comp_val in comps.items():
            for m in metrics:
                m_info = comp_val.get(m, {})
                mean_a = m_info.get("mean_a")
                mean_b = m_info.get("mean_b")
                if mean_a is not None:
                    data[conditions[0]][m] = mean_a
                if mean_b is not None:
                    data[conditions[1]][m] = mean_b
        note = ""

    x = np.arange(len(metrics))
    width = 0.25
    fig, ax = plt.subplots(figsize=(9, 5))
    for i, (c, label) in enumerate(zip(conditions, condition_labels)):
        vals = [data[c].get(m, 0.0) for m in metrics]
        ax.bar(x + (i - 1) * width, vals, width, label=label, alpha=0.82)

    ax.set_xticks(x)
    ax.set_xticklabels(metrics, rotation=20, ha="right", fontsize=8)
    ax.set_ylabel("Metric value")
    ax.set_title(f"Observation Effect: Inactive / Passive / Active{note}")
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()
    return _save(fig, "observation_effect_comparison.png")


# ---------------------------------------------------------------------------
# Table 7 — Horizon Summary Table
# ---------------------------------------------------------------------------

def write_horizon_summary_table(
    trust_report: Optional[Dict[str, Any]] = None,
    hs_report: Optional[Dict[str, Any]] = None,
) -> Tuple[Path, Path]:
    if trust_report is None:
        trust_report = _load_json(_OUTPUT_ROOT / "metric_trust_update_report.json")
    if hs_report is None:
        hs_report = _load_json(_STAGE6_OUT / "horizon_scaling_report.json")

    hs_map = {}
    if hs_report:
        for entry in hs_report.get("metrics", []):
            hs_map[entry.get("metric")] = entry.get("classification", "insufficient_data")

    metrics_rows: List[List[str]] = []
    header = ["metric", "trust_level_s5", "trust_level_s6", "trust_change",
              "horizon_sensitivity", "encoding_confound", "governance_confound", "comparative_only"]

    if trust_report:
        for entry in trust_report.get("metrics", []):
            m = entry.get("metric", "")
            metrics_rows.append([
                m,
                entry.get("previous_trust_level", ""),
                entry.get("trust_level", ""),
                entry.get("trust_change", ""),
                hs_map.get(m, entry.get("horizon_sensitivity", "")),
                entry.get("encoding_confound", ""),
                entry.get("governance_confound", ""),
                str(entry.get("comparative_only", "")),
            ])
    else:
        # Synthetic
        for m in _PRIMARY_METRICS:
            metrics_rows.append([m, "trusted_comparative", "trusted_comparative",
                                  "unchanged", "insufficient_data", "unknown", "unknown", "True"])

    _FIGS_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = _FIGS_DIR / "horizon_summary_table.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(metrics_rows)

    md_path = _FIGS_DIR / "horizon_summary_table.md"
    lines = ["| " + " | ".join(header) + " |",
             "| " + " | ".join(["---"] * len(header)) + " |"]
    for row in metrics_rows:
        lines.append("| " + " | ".join(row) + " |")
    md_path.write_text("\n".join(lines) + "\n")

    print(f"  [plot_stage6] saved → {csv_path}", file=sys.stderr)
    print(f"  [plot_stage6] saved → {md_path}", file=sys.stderr)
    return csv_path, md_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def generate_all_stage6_figures() -> List[Path]:
    """Generate all Stage 6 figures and tables. Returns list of output paths."""
    outputs: List[Path] = []
    outputs.append(plot_horizon_scaling())
    outputs.append(plot_governance_vs_horizon())
    outputs.append(plot_encoding_sensitivity_vs_horizon())
    outputs.append(plot_metric_trust_changes())
    outputs.append(plot_long_horizon_read_only())
    outputs.append(plot_observation_effect_comparison())
    csv_p, md_p = write_horizon_summary_table()
    outputs.extend([csv_p, md_p])
    print(f"[plot_stage6] All {len(outputs)} outputs generated.", file=sys.stderr)
    return outputs


if __name__ == "__main__":
    paths = generate_all_stage6_figures()
    for p in paths:
        print(p)
