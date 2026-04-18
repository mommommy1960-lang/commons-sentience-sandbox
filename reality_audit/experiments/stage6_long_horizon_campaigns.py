"""
stage6_long_horizon_campaigns.py — Long-horizon real sandbox campaigns for Stage 6.

Extends Stage 5 calibrated_campaigns.py to meaningful horizon lengths (25, 50, 100 turns)
to determine which Stage 5 "neutral" results were artefacts of short runs.

Campaign matrix
---------------
A  governance ON  + passive probe  + normal agent  (baseline)
B  governance OFF + passive probe  + normal agent  (governance sensitivity test)
C  passive probe  vs inactive probe (read-only verification against longer horizon)
D  passive probe  vs active_measurement probe (experimental — labelled as such)
E  baseline agent (low-cooperation) vs normal agent (agent sensitivity)
F  bandwidth-constrained (observe_period=2) vs unconstrained passive

Output
------
commons_sentience_sim/output/reality_audit/stage6_long_horizon/
  <campaign_id>/<turns>/<seed>/
    raw_summary.json       — per-run reality_audit summary.json
    run_metadata.json      — seed, turns, params
  <campaign_id>/aggregated_summary.json
campaign_comparison_report.json
horizon_comparison_report.json  — grouped by horizon length
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
    _REPO_ROOT / "commons_sentience_sim" / "output" / "reality_audit" / "stage6_long_horizon"
)
_DATA_DIR = _REPO_ROOT / "commons_sentience_sim" / "data"

# ---------------------------------------------------------------------------
# Campaign parameters
# ---------------------------------------------------------------------------

STAGE6_TURN_COUNTS: List[int] = [25, 50, 100]
STAGE6_N_SEEDS: int = 3
EFFECT_THRESH: float = 0.20  # Cohen's d threshold for "meaningful"

# Metrics to track
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
    "observer_dependence_score",
]
ALL_TRACKED_METRICS: List[str] = list(
    dict.fromkeys(TRUSTED_METRICS + COMPARATIVE_METRICS)
)

# ---------------------------------------------------------------------------
# Campaign definitions
# ---------------------------------------------------------------------------

_CAMPAIGN_DEFS: Dict[str, Dict[str, Any]] = {
    # -- A: standard baseline -------------------------------------------------
    "lh_A": {
        "label": "gov_on_passive",
        "description": "Governance ON, passive probe, normal agent — long-horizon baseline",
        "probe_mode": PROBE_MODE_PASSIVE,
        "gov_off": False,
        "experimental": False,
        "params": {
            "_name": "lh_A",
            "governance_strictness": 1.0,
            "cooperation_bias": 0.5,
            "initial_agent_trust": 0.5,
        },
    },
    # -- B: governance off test -----------------------------------------------
    "lh_B": {
        "label": "gov_off_passive",
        "description": "Governance structurally disabled, passive probe — tests governance sensitivity at horizon",
        "probe_mode": PROBE_MODE_PASSIVE,
        "gov_off": True,
        "experimental": False,
        "params": {
            "_name": "lh_B",
            "governance_strictness": 1.0,
            "cooperation_bias": 0.5,
            "initial_agent_trust": 0.5,
        },
    },
    # -- C: probe mode comparison (passive) -----------------------------------
    "lh_C_passive": {
        "label": "probe_passive_arm",
        "description": "Passive probe arm for long-horizon read-only verification",
        "probe_mode": PROBE_MODE_PASSIVE,
        "gov_off": False,
        "experimental": False,
        "params": {
            "_name": "lh_C_passive",
            "governance_strictness": 1.0,
            "cooperation_bias": 0.5,
            "initial_agent_trust": 0.5,
        },
    },
    # -- C: probe mode comparison (inactive) ----------------------------------
    "lh_C_inactive": {
        "label": "probe_inactive_arm",
        "description": "Inactive probe arm — verifies probe does not affect outcomes at longer horizons",
        "probe_mode": PROBE_MODE_INACTIVE,
        "gov_off": False,
        "experimental": False,
        "params": {
            "_name": "lh_C_inactive",
            "governance_strictness": 1.0,
            "cooperation_bias": 0.5,
            "initial_agent_trust": 0.5,
        },
    },
    # -- D: experimental observation-schedule comparison ----------------------
    "lh_D_passive": {
        "label": "obs_schedule_passive",
        "description": "Passive arm for observation-schedule comparison (experimental)",
        "probe_mode": PROBE_MODE_PASSIVE,
        "gov_off": False,
        "experimental": True,
        "params": {
            "_name": "lh_D_passive",
            "governance_strictness": 1.0,
            "cooperation_bias": 0.5,
            "initial_agent_trust": 0.5,
        },
    },
    "lh_D_active": {
        "label": "obs_schedule_active",
        "description": "Active-measurement arm — labelled experimental; not a main finding",
        "probe_mode": PROBE_MODE_ACTIVE_MEASUREMENT,
        "gov_off": False,
        "experimental": True,
        "observe_period": 2,
        "params": {
            "_name": "lh_D_active",
            "governance_strictness": 1.0,
            "cooperation_bias": 0.5,
            "initial_agent_trust": 0.5,
        },
    },
    # -- E: agent type comparison ---------------------------------------------
    "lh_E_normal": {
        "label": "agent_normal",
        "description": "Normal agent — agent type comparison arm",
        "probe_mode": PROBE_MODE_PASSIVE,
        "gov_off": False,
        "experimental": False,
        "params": {
            "_name": "lh_E_normal",
            "governance_strictness": 1.0,
            "cooperation_bias": 0.5,
            "initial_agent_trust": 0.5,
        },
    },
    "lh_E_baseline": {
        "label": "agent_baseline",
        "description": "Low-cooperation / low-trust baseline agent — agent type comparison arm",
        "probe_mode": PROBE_MODE_PASSIVE,
        "gov_off": False,
        "experimental": False,
        "params": {
            "_name": "lh_E_baseline",
            "governance_strictness": 1.0,
            "cooperation_bias": 0.1,
            "initial_agent_trust": 0.2,
        },
    },
    # -- F: bandwidth constrained vs unconstrained ----------------------------
    "lh_F_unconstrained": {
        "label": "bandwidth_unconstrained",
        "description": "Passive probe (full bandwidth) — bandwidth comparison baseline",
        "probe_mode": PROBE_MODE_PASSIVE,
        "gov_off": False,
        "experimental": False,
        "params": {
            "_name": "lh_F_unconstrained",
            "governance_strictness": 1.0,
            "cooperation_bias": 0.5,
            "initial_agent_trust": 0.5,
        },
    },
    "lh_F_constrained": {
        "label": "bandwidth_constrained",
        "description": "Active-measurement with observe_period=2 (bandwidth-constrained)",
        "probe_mode": PROBE_MODE_ACTIVE_MEASUREMENT,
        "gov_off": False,
        "experimental": True,
        "observe_period": 2,
        "params": {
            "_name": "lh_F_constrained",
            "governance_strictness": 1.0,
            "cooperation_bias": 0.5,
            "initial_agent_trust": 0.5,
        },
    },
}

# ---------------------------------------------------------------------------
# Comparison pairs
# ---------------------------------------------------------------------------

_COMPARISON_PAIRS: List[Tuple[str, str, str]] = [
    ("lh_A_vs_lh_B__gov_sensitivity",       "lh_A",              "lh_B"),
    ("lh_C__probe_passive_vs_inactive",      "lh_C_passive",      "lh_C_inactive"),
    ("lh_D__passive_vs_active (experimental)","lh_D_passive",     "lh_D_active"),
    ("lh_E__normal_vs_baseline_agent",       "lh_E_normal",       "lh_E_baseline"),
    ("lh_F__bandwidth_unconstrained_vs_constrained", "lh_F_unconstrained", "lh_F_constrained"),
]

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
                return None
    return None


def _extract_metrics(summary: Optional[Dict[str, Any]]) -> Dict[str, Optional[float]]:
    if not summary:
        return {m: None for m in ALL_TRACKED_METRICS}
    return {m: summary.get(m) for m in ALL_TRACKED_METRICS}


# ---------------------------------------------------------------------------
# Single run
# ---------------------------------------------------------------------------

def run_single(
    campaign_id: str,
    total_turns: int,
    seed: int,
    output_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Execute one run of a named campaign at a given horizon and seed.

    Returns a dict with extracted metrics and run metadata.
    """
    defn = _CAMPAIGN_DEFS[campaign_id]
    root = (output_root or _OUTPUT_ROOT) / campaign_id / f"turns_{total_turns}" / f"seed_{seed:02d}"
    root.mkdir(parents=True, exist_ok=True)

    random.seed(seed)
    cfg = _make_config(defn["params"], total_turns)

    probe_mode = defn["probe_mode"]
    observe_period: Optional[int] = defn.get("observe_period")

    probe = SimProbe(
        rooms_json_path=_DATA_DIR / "rooms.json",
        output_dir=root,
        probe_mode=probe_mode,
        observe_period=observe_period,
    )

    gov_off: bool = defn.get("gov_off", False)
    if gov_off:
        from commons_sentience_sim.core import governance as _gov_mod

        def _always_permit(self_or_action, action: str = "") -> Tuple[bool, str]:
            return (True, "stage6: governance disabled")

        with mock.patch.object(_gov_mod.GovernanceEngine, "check_action", _always_permit):
            _run_simulation_with_probe(cfg, probe, root)
    else:
        _run_simulation_with_probe(cfg, probe, root)

    audit_dir = probe.finalize()

    metrics: Dict[str, Optional[float]] = {}
    if probe_mode != PROBE_MODE_INACTIVE:
        summary = _load_summary(audit_dir)
        metrics = _extract_metrics(summary)
    else:
        metrics = {m: None for m in ALL_TRACKED_METRICS}

    run_meta = {
        "campaign_id": campaign_id,
        "label": defn["label"],
        "total_turns": total_turns,
        "seed": seed,
        "probe_mode": probe_mode,
        "gov_off": gov_off,
        "experimental": defn.get("experimental", False),
        "metrics": metrics,
    }
    (root / "run_metadata.json").write_text(json.dumps(run_meta, indent=2))
    return run_meta


# ---------------------------------------------------------------------------
# Aggregate across seeds for one (campaign_id, turns) cell
# ---------------------------------------------------------------------------

def aggregate_campaign_horizon(
    campaign_id: str,
    total_turns: int,
    n_seeds: int = STAGE6_N_SEEDS,
    output_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Run all seeds for one (campaign, turns) cell; write aggregated_summary.json."""
    results = [
        run_single(campaign_id, total_turns, s, output_root)
        for s in range(n_seeds)
    ]
    agg: Dict[str, Any] = {}
    for metric in ALL_TRACKED_METRICS:
        vals = [r["metrics"].get(metric) for r in results if r["metrics"].get(metric) is not None]
        agg[metric] = {
            "mean": _mean(vals) if vals else None,
            "std": _std(vals) if len(vals) > 1 else None,
            "n": len(vals),
            "values": vals,
        }

    summary = {
        "campaign_id": campaign_id,
        "total_turns": total_turns,
        "n_seeds": n_seeds,
        "per_run": results,
        "aggregated_metrics": agg,
    }

    out_dir = (output_root or _OUTPUT_ROOT) / campaign_id
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = f"turns_{total_turns}"
    (out_dir / f"aggregated_{suffix}.json").write_text(json.dumps(summary, indent=2))
    return summary


# ---------------------------------------------------------------------------
# Compare two campaigns at a single horizon
# ---------------------------------------------------------------------------

def compare_campaigns_at_horizon(
    label: str,
    campaign_a_id: str,
    campaign_b_id: str,
    summaries: Dict[Tuple[str, int], Dict[str, Any]],
    total_turns: int,
) -> Dict[str, Any]:
    """Build pairwise metric comparison between two campaigns at one horizon."""
    sum_a = summaries.get((campaign_a_id, total_turns))
    sum_b = summaries.get((campaign_b_id, total_turns))
    metric_comps: Dict[str, Any] = {}
    for m in ALL_TRACKED_METRICS:
        agg_a = (sum_a or {}).get("aggregated_metrics", {}).get(m, {})
        agg_b = (sum_b or {}).get("aggregated_metrics", {}).get(m, {})
        vals_a: List[float] = agg_a.get("values", [])
        vals_b: List[float] = agg_b.get("values", [])
        if not vals_a or not vals_b:
            metric_comps[m] = {
                "mean_a": agg_a.get("mean"),
                "mean_b": agg_b.get("mean"),
                "delta": None,
                "cohens_d": None,
                "moved_meaningfully": False,
            }
            continue
        d = _cohens_d(vals_a, vals_b)
        delta = _mean(vals_a) - _mean(vals_b)
        metric_comps[m] = {
            "mean_a": _mean(vals_a),
            "mean_b": _mean(vals_b),
            "delta": round(delta, 6),
            "cohens_d": round(d, 4) if d is not None else None,
            "moved_meaningfully": bool(d is not None and abs(d) >= EFFECT_THRESH),
        }
    sensitive = [m for m, v in metric_comps.items() if v.get("moved_meaningfully")]
    return {
        "label": label,
        "campaign_a": campaign_a_id,
        "campaign_b": campaign_b_id,
        "total_turns": total_turns,
        "sensitive_metrics": sensitive,
        "n_sensitive": len(sensitive),
        "metrics": metric_comps,
    }


# ---------------------------------------------------------------------------
# Build horizon-comparison report — how does each metric change across turns?
# ---------------------------------------------------------------------------

def build_horizon_comparison_report(
    summaries: Dict[Tuple[str, int], Dict[str, Any]],
    turn_counts: List[int],
    campaign_id: str = "lh_A",
) -> Dict[str, Any]:
    """For each metric in campaign_id, show how mean/std evolves across turn counts."""
    metric_horizon: Dict[str, Any] = {}
    for m in ALL_TRACKED_METRICS:
        series = {}
        for t in turn_counts:
            s = summaries.get((campaign_id, t))
            if s:
                agg = s.get("aggregated_metrics", {}).get(m, {})
                series[str(t)] = {
                    "mean": agg.get("mean"),
                    "std": agg.get("std"),
                    "n": agg.get("n"),
                }
        metric_horizon[m] = series
    return {
        "campaign_id": campaign_id,
        "turn_counts": turn_counts,
        "metrics": metric_horizon,
    }


# ---------------------------------------------------------------------------
# Master run function
# ---------------------------------------------------------------------------

def run_stage6_long_horizon_campaigns(
    turn_counts: Optional[List[int]] = None,
    n_seeds: int = STAGE6_N_SEEDS,
    output_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Run all Stage 6 long-horizon campaigns.

    Returns dict with all summaries, comparison report, and horizon report.
    """
    root = output_root or _OUTPUT_ROOT
    root.mkdir(parents=True, exist_ok=True)

    tc = turn_counts if turn_counts is not None else STAGE6_TURN_COUNTS

    # 1. Run all (campaign, turns) cells
    summaries: Dict[Tuple[str, int], Dict[str, Any]] = {}
    for campaign_id in _CAMPAIGN_DEFS:
        for turns in tc:
            s = aggregate_campaign_horizon(campaign_id, turns, n_seeds, root)
            summaries[(campaign_id, turns)] = s

    # 2. Build comparison report per turns
    comparison_by_horizon: Dict[str, List[Dict[str, Any]]] = {str(t): [] for t in tc}
    for turns in tc:
        for pair_label, cid_a, cid_b in _COMPARISON_PAIRS:
            comp = compare_campaigns_at_horizon(pair_label, cid_a, cid_b, summaries, turns)
            comparison_by_horizon[str(turns)].append(comp)

    comparison_report = {
        "turn_counts": tc,
        "comparisons_by_horizon": comparison_by_horizon,
        "n_seeds": n_seeds,
    }
    (root / "campaign_comparison_report.json").write_text(
        json.dumps(comparison_report, indent=2)
    )

    # 3. Build horizon report (how baseline metrics evolve across turns)
    horizon_report = build_horizon_comparison_report(summaries, tc, campaign_id="lh_A")
    (root / "horizon_comparison_report.json").write_text(
        json.dumps(horizon_report, indent=2)
    )

    # 4. Summary CSV
    csv_rows: List[Dict[str, Any]] = []
    for (cid, turns), s in summaries.items():
        for m, agg in s.get("aggregated_metrics", {}).items():
            csv_rows.append({
                "campaign_id": cid,
                "turns": turns,
                "metric": m,
                "mean": agg.get("mean"),
                "std": agg.get("std"),
                "n": agg.get("n"),
            })
    if csv_rows:
        csv_path = root / "stage6_campaigns_summary.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(csv_rows[0].keys()))
            writer.writeheader()
            writer.writerows(csv_rows)

    print(
        f"Stage 6 long-horizon campaigns complete.\n"
        f"  Campaigns: {len(_CAMPAIGN_DEFS)} × {len(tc)} horizons × {n_seeds} seeds\n"
        f"  Output: {root}\n"
        f"  campaign_comparison_report.json written\n"
        f"  horizon_comparison_report.json written"
    )

    return {
        "summaries": summaries,
        "comparison_report": comparison_report,
        "horizon_report": horizon_report,
    }


if __name__ == "__main__":
    run_stage6_long_horizon_campaigns()
