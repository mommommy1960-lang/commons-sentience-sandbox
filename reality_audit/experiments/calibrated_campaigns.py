"""
calibrated_campaigns.py — Standardized campaign matrix using only the most
defensible (Stage 4 validated) metrics.

Campaign matrix
---------------
A  normal_agent   + passive probe + governance on
B  normal_agent   + passive probe + governance off (structural bypass)
C  baseline_agent (low-cooperation) + passive probe + governance on
D  passive probe  vs inactive probe side-by-side (same agent, same turns)
E  passive probe  vs active_measurement probe (experimental — marked as such)

Each campaign is run with:
  - 25, 50, and 100 turn counts
  - CAMPAIGN_N_SEEDS independent seeds

Output
------
commons_sentience_sim/output/reality_audit/calibrated_campaigns/
  <campaign_id>/<turn_count>/<seed>/campaign_result.json
  <campaign_id>/aggregated_summary.json

campaign_comparison_report.json   — paired effect-size comparisons
"""
from __future__ import annotations

import copy
import csv
import json
import math
import random
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from unittest import mock

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from experiment_config import ExperimentConfig
from reality_audit.adapters.sim_probe import (
    SimProbe,
    PROBE_MODE_PASSIVE,
    PROBE_MODE_INACTIVE,
    PROBE_MODE_ACTIVE_MEASUREMENT,
)
from reality_audit.experiments.sandbox_campaigns import (
    _run_simulation_with_probe,
    _make_config,
)

_OUTPUT_ROOT = (
    _REPO_ROOT / "commons_sentience_sim" / "output" / "reality_audit" / "calibrated_campaigns"
)

# Campaign parameters
CAMPAIGN_TURN_COUNTS: List[int] = [25, 50, 100]
CAMPAIGN_N_SEEDS: int = 3

# Only metrics that survived Stage 4 scrutiny
TRUSTED_METRICS: List[str] = [
    "path_smoothness",
    "avg_control_effort",
    "audit_bandwidth",
    "stability_score",
    "mean_position_error",
]
COMPARATIVE_METRICS: List[str] = [
    "anisotropy_score",
    "stability_score",
    "mean_position_error",
]
EXPERIMENTAL_METRICS: List[str] = [
    "observer_dependence_score",
]

# Effect-size threshold for "meaningful" difference
EFFECT_THRESH: float = 0.20  # Cohen's d threshold

# ---------------------------------------------------------------------------
# Campaign config definitions
# ---------------------------------------------------------------------------

_CAMPAIGN_DEFS: Dict[str, Dict[str, Any]] = {
    "campaign_A": {
        "label": "normal_agent_passive_gov_on",
        "description": "Normal agent, passive probe, governance on (standard baseline)",
        "probe_mode": PROBE_MODE_PASSIVE,
        "gov_off": False,
        "params": {
            "_name": "cal_A",
            "governance_strictness": 1.0,
            "cooperation_bias": 0.5,
            "initial_agent_trust": 0.5,
        },
    },
    "campaign_B": {
        "label": "normal_agent_passive_gov_off",
        "description": "Normal agent, passive probe, governance structurally disabled",
        "probe_mode": PROBE_MODE_PASSIVE,
        "gov_off": True,
        "params": {
            "_name": "cal_B",
            "governance_strictness": 1.0,
            "cooperation_bias": 0.5,
            "initial_agent_trust": 0.5,
        },
    },
    "campaign_C": {
        "label": "baseline_agent_passive",
        "description": "Low-cooperation / low-trust agent, passive probe, governance on",
        "probe_mode": PROBE_MODE_PASSIVE,
        "gov_off": False,
        "params": {
            "_name": "cal_C",
            "governance_strictness": 1.0,
            "cooperation_bias": 0.1,
            "initial_agent_trust": 0.2,
        },
    },
    "campaign_D_passive": {
        "label": "campaign_D_passive",
        "description": "Passive probe arm of probe_mode comparison",
        "probe_mode": PROBE_MODE_PASSIVE,
        "gov_off": False,
        "params": {
            "_name": "cal_D_passive",
            "governance_strictness": 1.0,
            "cooperation_bias": 0.5,
            "initial_agent_trust": 0.5,
        },
    },
    "campaign_D_inactive": {
        "label": "campaign_D_inactive",
        "description": "Inactive probe arm — no audit collected",
        "probe_mode": PROBE_MODE_INACTIVE,
        "gov_off": False,
        "params": {
            "_name": "cal_D_inactive",
            "governance_strictness": 1.0,
            "cooperation_bias": 0.5,
            "initial_agent_trust": 0.5,
        },
    },
    "campaign_E_passive": {
        "label": "campaign_E_passive",
        "description": "Passive arm for observation-schedule comparison (experimental)",
        "probe_mode": PROBE_MODE_PASSIVE,
        "gov_off": False,
        "experimental": True,
        "params": {
            "_name": "cal_E_passive",
            "governance_strictness": 1.0,
            "cooperation_bias": 0.5,
            "initial_agent_trust": 0.5,
        },
    },
    "campaign_E_active": {
        "label": "campaign_E_active",
        "description": "Active-measurement arm (experimental — marked, not main finding)",
        "probe_mode": PROBE_MODE_ACTIVE_MEASUREMENT,
        "gov_off": False,
        "experimental": True,
        "params": {
            "_name": "cal_E_active",
            "governance_strictness": 1.0,
            "cooperation_bias": 0.5,
            "initial_agent_trust": 0.5,
        },
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mean(vals: List[float]) -> float:
    return sum(vals) / len(vals) if vals else 0.0


def _std(vals: List[float]) -> float:
    if len(vals) < 2:
        return 0.0
    m = _mean(vals)
    return math.sqrt(sum((v - m) ** 2 for v in vals) / (len(vals) - 1))


def _cohens_d(a: List[float], b: List[float]) -> Optional[float]:
    if not a or not b:
        return None
    sa, sb = _std(a), _std(b)
    pooled = math.sqrt((sa ** 2 + sb ** 2) / 2.0)
    if pooled < 1e-12:
        return 0.0
    return (_mean(a) - _mean(b)) / pooled


def _load_summary(audit_dir: Path) -> Optional[Dict[str, Any]]:
    for name in ("summary.json", "audit_summary.json"):
        p = audit_dir / name
        if p.exists():
            try:
                with open(p, encoding="utf-8") as fh:
                    return json.load(fh)
            except (json.JSONDecodeError, OSError):
                pass
    return None


# ---------------------------------------------------------------------------
# Single run
# ---------------------------------------------------------------------------

def run_campaign_single(
    campaign_id: str,
    total_turns: int,
    seed: int,
    output_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Run one cell of the campaign matrix."""
    defn = _CAMPAIGN_DEFS[campaign_id]
    root = (output_root or _OUTPUT_ROOT) / campaign_id / f"turns_{total_turns:03d}" / f"seed_{seed:02d}"
    root.mkdir(parents=True, exist_ok=True)

    random.seed(seed)
    cfg = _make_config(defn["params"], total_turns)
    probe_mode: str = defn["probe_mode"]
    gov_off: bool = defn.get("gov_off", False)

    _DATA_DIR = _REPO_ROOT / "commons_sentience_sim" / "data"
    probe = SimProbe(
        rooms_json_path=_DATA_DIR / "rooms.json",
        output_dir=root,
        probe_mode=probe_mode,
    )

    if gov_off:
        from commons_sentience_sim.core import governance as _gov_mod

        def _always_permit(self_or_action, action: str = "") -> Tuple[bool, str]:
            return (True, "calibrated campaign: governance disabled")

        with mock.patch.object(_gov_mod.GovernanceEngine, "check_action", _always_permit):
            _run_simulation_with_probe(cfg, probe, root)
    else:
        _run_simulation_with_probe(cfg, probe, root)

    audit_dir = probe.finalize()
    probe_metrics: Dict[str, Any] = {}
    if probe_mode != PROBE_MODE_INACTIVE:
        summary = _load_summary(audit_dir)
        if summary:
            probe_metrics = {m: summary.get(m) for m in TRUSTED_METRICS + EXPERIMENTAL_METRICS}

    result = {
        "campaign_id": campaign_id,
        "label": defn["label"],
        "total_turns": total_turns,
        "seed": seed,
        "probe_mode": probe_mode,
        "gov_off": gov_off,
        "experimental": defn.get("experimental", False),
        "probe_metrics": probe_metrics,
    }
    with open(root / "campaign_result.json", "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)
    return result


# ---------------------------------------------------------------------------
# Aggregate campaign
# ---------------------------------------------------------------------------

def aggregate_campaign(
    campaign_id: str,
    turn_counts: List[int],
    n_seeds: int,
    output_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Run all seeds/turns for one campaign and return aggregated summary."""
    runs = []
    for turns in turn_counts:
        for seed in range(n_seeds):
            r = run_campaign_single(campaign_id, turns, seed, output_root=output_root)
            runs.append(r)

    # Aggregate per (turns, metric)
    agg_by_turns: Dict[int, Dict[str, Any]] = {}
    for turns in turn_counts:
        turn_runs = [r for r in runs if r["total_turns"] == turns]
        agg_metrics: Dict[str, Any] = {}
        for m in TRUSTED_METRICS + EXPERIMENTAL_METRICS:
            vals = [r["probe_metrics"][m] for r in turn_runs if r["probe_metrics"].get(m) is not None]
            agg_metrics[m] = {
                "mean": round(_mean(vals), 6) if vals else None,
                "std": round(_std(vals), 6) if len(vals) >= 2 else None,
                "n": len(vals),
            }
        agg_by_turns[turns] = agg_metrics

    defn = _CAMPAIGN_DEFS[campaign_id]
    summary = {
        "campaign_id": campaign_id,
        "label": defn["label"],
        "description": defn["description"],
        "probe_mode": defn["probe_mode"],
        "gov_off": defn.get("gov_off", False),
        "experimental": defn.get("experimental", False),
        "turn_counts": turn_counts,
        "n_seeds": n_seeds,
        "aggregated": agg_by_turns,
    }

    # Write aggregated_summary.json
    camp_dir = (output_root or _OUTPUT_ROOT) / campaign_id
    camp_dir.mkdir(parents=True, exist_ok=True)
    with open(camp_dir / "aggregated_summary.json", "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)

    return summary


# ---------------------------------------------------------------------------
# Comparison report
# ---------------------------------------------------------------------------

def _compare_campaigns(
    summary_a: Dict[str, Any],
    summary_b: Dict[str, Any],
    output_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Compute effect sizes between two campaign summaries for each metric+turns."""
    pairs = {}
    for turns in summary_a.get("turn_counts", []):
        agg_a = summary_a["aggregated"].get(turns, {})
        agg_b = summary_b["aggregated"].get(turns, {})
        pairs[turns] = {}
        for m in TRUSTED_METRICS:
            ma = agg_a.get(m, {}).get("mean")
            mb = agg_b.get(m, {}).get("mean")
            sa = agg_a.get(m, {}).get("std")
            sb = agg_b.get(m, {}).get("std")
            if ma is None or mb is None:
                pairs[turns][m] = {"delta": None, "meaningful": False, "note": "missing data"}
                continue
            delta = ma - mb
            pooled = math.sqrt(((sa or 0.0) ** 2 + (sb or 0.0) ** 2) / 2.0)
            d = delta / pooled if pooled >= 1e-12 else 0.0
            pairs[turns][m] = {
                "mean_a": ma, "mean_b": mb, "delta": round(delta, 6),
                "cohens_d": round(d, 4), "meaningful": abs(d) >= EFFECT_THRESH,
            }
    return pairs


def build_campaign_comparison_report(
    summaries: Dict[str, Dict[str, Any]],
    output_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Compare selected campaign pairs and write campaign_comparison_report.json."""
    comparisons = {}

    # Predefined comparison pairs
    pairs = [
        ("campaign_A", "campaign_B", "A_vs_B__gov_on_vs_gov_off"),
        ("campaign_A", "campaign_C", "A_vs_C__normal_vs_baseline_agent"),
        ("campaign_D_passive", "campaign_D_inactive", "D__passive_vs_inactive_probe"),
        ("campaign_E_passive", "campaign_E_active", "E__passive_vs_active_probe (experimental)"),
    ]
    for id_a, id_b, label in pairs:
        if id_a in summaries and id_b in summaries:
            comparisons[label] = _compare_campaigns(summaries[id_a], summaries[id_b])

    report = {
        "stage": "Stage 5",
        "description": "Effect-size comparisons between calibrated campaign pairs.",
        "effect_threshold": EFFECT_THRESH,
        "note_experimental": "campaign_E comparisons are experimental — do not overclaim.",
        "comparisons": comparisons,
    }

    root = output_root or _OUTPUT_ROOT
    root.mkdir(parents=True, exist_ok=True)
    path = root / "campaign_comparison_report.json"
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    return report


# ---------------------------------------------------------------------------
# Master runner
# ---------------------------------------------------------------------------

def run_calibrated_campaigns(
    turn_counts: Optional[List[int]] = None,
    n_seeds: int = CAMPAIGN_N_SEEDS,
    output_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Run all campaigns and build the comparison report."""
    turns = turn_counts or CAMPAIGN_TURN_COUNTS
    root = output_root or _OUTPUT_ROOT

    summaries = {}
    for cid in _CAMPAIGN_DEFS:
        summaries[cid] = aggregate_campaign(cid, turns, n_seeds, output_root=root)

    comparison_report = build_campaign_comparison_report(summaries, output_root=root)

    # Write CSV of aggregated means
    csv_rows = []
    for cid, summary in summaries.items():
        for t, metrics in summary["aggregated"].items():
            for m, stats in metrics.items():
                csv_rows.append({
                    "campaign_id": cid,
                    "label": summary["label"],
                    "total_turns": t,
                    "metric": m,
                    "mean": stats.get("mean"),
                    "std": stats.get("std"),
                    "n": stats.get("n"),
                    "experimental": summary.get("experimental", False),
                })
    csv_path = root / "calibrated_campaigns_summary.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["campaign_id", "label", "total_turns", "metric", "mean", "std", "n", "experimental"],
        )
        writer.writeheader()
        writer.writerows(csv_rows)

    return {
        "summaries": summaries,
        "comparison_report": comparison_report,
        "csv_path": str(csv_path),
    }


if __name__ == "__main__":
    result = run_calibrated_campaigns()
    print("Calibrated campaigns complete.")
    print("Comparison report written.")
