"""
governance_campaigns.py — Deeper governance sensitivity analysis.

Compares reality-audit metrics under two governance states:

  governance_on   — standard rules.json (GovernanceEngine as built)
  governance_off  — GovernanceEngine.check_action monkeypatched to always
                    permit all actions (structural bypass, not config-only)

Also runs a paired comparison in the physics framework (WorldMode proxy)
to isolate governance effects from LLM stochasticity.

Parameters swept
----------------
  turn_counts  : [25, 50]
  n_seeds      : 5
  configs      : governance_on, governance_off

Output
------
governance_campaign_report.json
governance_campaign_summary.csv
"""
from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from unittest import mock

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from experiment_config import ExperimentConfig
from reality_audit.adapters.sim_probe import SimProbe, PROBE_MODE_PASSIVE
from reality_audit.experiments.sandbox_campaigns import _run_simulation_with_probe

_OUTPUT_ROOT = (
    _REPO_ROOT / "commons_sentience_sim" / "output" / "reality_audit" / "governance_campaigns"
)

# Governance campaign turn counts and seeds
GOV_TURN_COUNTS: List[int] = [25, 50]
GOV_N_SEEDS: int = 5

# Base config parameters (governance_strictness is metadata; actual bypass is structural)
_GOV_BASE_PARAMS: Dict[str, Any] = {
    "name": "gov_campaign",
    "governance_strictness": 1.0,
    "cooperation_bias": 0.5,
    "initial_agent_trust": 0.5,
}


def _always_permit(action: str) -> Tuple[bool, str]:
    """Replacement for GovernanceEngine.check_action that always permits."""
    return True, "governance disabled for campaign experiment"


def run_governance_campaign_single(
    governance_active: bool,
    total_turns: int,
    seed: int,
    output_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Run one governance campaign (on or off) with a given seed.

    Parameters
    ----------
    governance_active : bool
        If False, monkeypatch GovernanceEngine to always permit actions.
    total_turns : int
    seed : int
    output_root : Path, optional
    """
    import random as _rand
    _rand.seed(seed)

    root = output_root or _OUTPUT_ROOT
    gov_label = "gov_on" if governance_active else "gov_off"
    run_dir = root / gov_label / f"turns_{total_turns:03d}" / f"seed_{seed:02d}"
    run_dir.mkdir(parents=True, exist_ok=True)

    params = dict(_GOV_BASE_PARAMS)
    params["total_turns"] = total_turns
    cfg = ExperimentConfig(params)

    data_dir = _REPO_ROOT / "commons_sentience_sim" / "data"
    probe = SimProbe(
        rooms_json_path=data_dir / "rooms.json",
        output_dir=run_dir,
        probe_mode=PROBE_MODE_PASSIVE,
    )

    if governance_active:
        _run_simulation_with_probe(cfg, probe, run_dir)
    else:
        # Monkeypatch GovernanceEngine.check_action for this run only
        from commons_sentience_sim.core import governance as _gov_mod
        with mock.patch.object(
            _gov_mod.GovernanceEngine,
            "check_action",
            side_effect=_always_permit,
        ):
            _run_simulation_with_probe(cfg, probe, run_dir)

    audit_dir = probe.finalize()

    summary_path = audit_dir / "summary.json"
    probe_metrics: Dict[str, Any] = {}
    if summary_path.exists():
        with open(summary_path, encoding="utf-8") as fh:
            probe_metrics = json.load(fh)

    result: Dict[str, Any] = {
        "governance_active": governance_active,
        "governance_label": gov_label,
        "total_turns": total_turns,
        "seed": seed,
        "audit_dir": str(audit_dir),
        "probe_metrics": probe_metrics,
    }

    result_path = run_dir / "gov_campaign_result.json"
    with open(result_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)

    return result


def _metric_stats(
    results: List[Dict[str, Any]],
    metric: str,
) -> Dict[str, float]:
    """Compute mean/std for a metric across a list of per-seed results."""
    vals = [
        r["probe_metrics"].get(metric)
        for r in results
        if isinstance(r.get("probe_metrics", {}).get(metric), (int, float))
    ]
    n = len(vals)
    if n == 0:
        return {"mean": None, "std": None, "n": 0}
    mean = sum(vals) / n
    variance = sum((v - mean) ** 2 for v in vals) / n
    return {
        "mean": round(mean, 6),
        "std": round(math.sqrt(variance), 6),
        "n": n,
    }


def run_governance_campaigns(
    turn_counts: Optional[List[int]] = None,
    n_seeds: int = GOV_N_SEEDS,
    output_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Run full governance ON vs OFF campaign comparison.

    Returns
    -------
    dict with per-(turns, gov_state) stats and delta metrics.
    """
    turn_counts = turn_counts or GOV_TURN_COUNTS
    root = output_root or _OUTPUT_ROOT

    # Metrics to compare
    target_metrics = [
        "mean_position_error",
        "stability_score",
        "avg_control_effort",
        "path_smoothness",
        "observer_dependence_score",
        "audit_bandwidth",
    ]

    all_results: Dict[str, Any] = {}

    for tc in turn_counts:
        on_results = [
            run_governance_campaign_single(True, tc, seed, root)
            for seed in range(n_seeds)
        ]
        off_results = [
            run_governance_campaign_single(False, tc, seed, root)
            for seed in range(n_seeds)
        ]

        tc_analysis: Dict[str, Any] = {}
        for m in target_metrics:
            on_stats = _metric_stats(on_results, m)
            off_stats = _metric_stats(off_results, m)

            delta: Optional[float] = None
            if on_stats["mean"] is not None and off_stats["mean"] is not None:
                delta = round(off_stats["mean"] - on_stats["mean"], 6)

            tc_analysis[m] = {
                "gov_on": on_stats,
                "gov_off": off_stats,
                "delta_off_minus_on": delta,
            }

        all_results[tc] = tc_analysis

    # Identify governance-sensitive metrics (|delta| > 5% of gov_on mean)
    sensitive_metrics: List[str] = []
    if turn_counts:
        ref_tc = turn_counts[0]
        for m, mdata in all_results.get(ref_tc, {}).items():
            delta = mdata.get("delta_off_minus_on")
            on_mean = mdata.get("gov_on", {}).get("mean")
            if delta is not None and on_mean is not None and abs(on_mean) > 1e-9:
                if abs(delta / on_mean) > 0.05:
                    sensitive_metrics.append(m)

    report: Dict[str, Any] = {
        "governance_off_mechanism": "GovernanceEngine.check_action monkeypatched to always return True",
        "turn_counts": turn_counts,
        "n_seeds_per_condition": n_seeds,
        "per_turn_count_analysis": all_results,
        "governance_sensitive_metrics": sensitive_metrics,
    }

    root.mkdir(parents=True, exist_ok=True)
    json_path = root / "governance_campaign_report.json"
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)

    _write_governance_csv(all_results, root / "governance_campaign_summary.csv")

    print(f"[governance_campaigns] Report written to {json_path}")
    print(f"\n  Governance-sensitive metrics: {sensitive_metrics}")
    return report


def _write_governance_csv(
    all_results: Dict[int, Dict[str, Any]],
    path: Path,
) -> None:
    rows = []
    for tc, mdata in all_results.items():
        for m, comp in mdata.items():
            rows.append({
                "turns": tc,
                "metric": m,
                "gov_on_mean": comp.get("gov_on", {}).get("mean", ""),
                "gov_on_std":  comp.get("gov_on", {}).get("std", ""),
                "gov_off_mean": comp.get("gov_off", {}).get("mean", ""),
                "gov_off_std":  comp.get("gov_off", {}).get("std", ""),
                "delta": comp.get("delta_off_minus_on", ""),
            })
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    print("Running governance campaigns (25 turns, 3 seeds demo)...")
    run_governance_campaigns(turn_counts=[25], n_seeds=3)
