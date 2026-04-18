"""
ablation_studies.py — Toggle one factor at a time to identify which audit
components actually drive metric changes.

Ablation factors
----------------
1. governance_on  vs  governance_off
   Structural bypass via GovernanceEngine.check_action monkeypatch.

2. probe_passive  vs  probe_inactive  vs  probe_active_measurement

3. baseline_agent (low cooperation, low trust) vs normal_agent

4. encoding_variant: BFS+MDS (default) vs pure-hop vs manual-topological
   (re-uses encoding_robustness module, not a runtime toggle)

5. observation_schedule: passive (all turns observed) vs active (every-other-turn)

6. bandwidth_constrained: audit_bandwidth via active_measurement observe_period=2
   vs unconstrained (passive / observe_period=None)

7. cooperation_level: cooperation_bias 0.1 vs 0.5 vs 0.9

For each ablation pair the function:
  - holds everything else fixed (same ExperimentConfig template, same seeds)
  - runs N_SEEDS paired runs (condition_A, condition_B)
  - computes, per metric, the mean delta and Cohen's d-equivalent (d = delta/pooled_std)
  - reports which metrics moved meaningfully (|delta| > DELTA_THRESH or |d| > D_THRESH)

Output
------
ablation_report.json   — per-ablation, per-metric rich report
ablation_summary.csv   — flat table
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
    _REPO_ROOT / "commons_sentience_sim" / "output" / "reality_audit" / "ablation_studies"
)

# ---------------------------------------------------------------------------
# Thresholds for "meaningful movement"
# ---------------------------------------------------------------------------
DELTA_THRESH: float = 0.05   # absolute mean delta
D_THRESH: float = 0.20       # Cohen's d threshold

# Default campaign parameters
ABLATION_TOTAL_TURNS: int = 25
ABLATION_N_SEEDS: int = 3

# Metrics extracted from summary.json
SUMMARY_METRICS = [
    "mean_position_error",
    "stability_score",
    "avg_control_effort",
    "path_smoothness",
    "observer_dependence_score",
    "audit_bandwidth",
]

# Base config for most ablations (normal agent, governance on, passive probe)
_BASE_PARAMS: Dict[str, Any] = {
    "_name": "abl_base",
    "governance_strictness": 1.0,
    "cooperation_bias": 0.5,
    "initial_agent_trust": 0.5,
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


def _extract_metrics(summary: Optional[Dict[str, Any]]) -> Dict[str, Optional[float]]:
    if summary is None:
        return {m: None for m in SUMMARY_METRICS}
    return {m: summary.get(m) for m in SUMMARY_METRICS}


# ---------------------------------------------------------------------------
# Single-run helper
# ---------------------------------------------------------------------------

def _run_one(
    params: Dict[str, Any],
    total_turns: int,
    seed: int,
    probe_mode: str,
    run_dir: Path,
    gov_off: bool = False,
    observe_period: Optional[int] = None,
) -> Dict[str, Optional[float]]:
    """Run one ablation arm and return extracted metrics."""
    random.seed(seed)
    run_dir.mkdir(parents=True, exist_ok=True)
    cfg = _make_config(params, total_turns)

    _DATA_DIR = _REPO_ROOT / "commons_sentience_sim" / "data"
    probe = SimProbe(
        rooms_json_path=_DATA_DIR / "rooms.json",
        output_dir=run_dir,
        probe_mode=probe_mode,
        observe_period=observe_period,
    )

    if gov_off:
        from commons_sentience_sim.core import governance as _gov_mod

        def _always_permit(self_or_action, action: str = "") -> Tuple[bool, str]:
            return (True, "ablation: governance disabled")

        with mock.patch.object(_gov_mod.GovernanceEngine, "check_action", _always_permit):
            _run_simulation_with_probe(cfg, probe, run_dir)
    else:
        _run_simulation_with_probe(cfg, probe, run_dir)

    audit_dir = probe.finalize()
    if probe_mode == PROBE_MODE_INACTIVE:
        return {m: None for m in SUMMARY_METRICS}
    summary = _load_summary(audit_dir)
    return _extract_metrics(summary)


# ---------------------------------------------------------------------------
# Compare two arms
# ---------------------------------------------------------------------------

def _compare_arms(
    label_a: str,
    label_b: str,
    results_a: List[Dict[str, Optional[float]]],
    results_b: List[Dict[str, Optional[float]]],
) -> Dict[str, Any]:
    """Compute per-metric delta, Cohen's d and movement verdict."""
    metric_comparisons: Dict[str, Any] = {}
    for m in SUMMARY_METRICS:
        vals_a = [r[m] for r in results_a if r.get(m) is not None]
        vals_b = [r[m] for r in results_b if r.get(m) is not None]
        if not vals_a or not vals_b:
            metric_comparisons[m] = {
                "mean_a": None, "mean_b": None, "delta": None,
                "cohens_d": None, "moved_meaningfully": False,
                "note": "insufficient data",
            }
            continue
        mean_a = _mean(vals_a)
        mean_b = _mean(vals_b)
        delta = mean_a - mean_b
        d = _cohens_d(vals_a, vals_b)
        moved = abs(delta) > DELTA_THRESH or (d is not None and abs(d) > D_THRESH)
        metric_comparisons[m] = {
            "mean_a": round(mean_a, 6),
            "mean_b": round(mean_b, 6),
            "delta": round(delta, 6),
            "cohens_d": round(d, 4) if d is not None else None,
            "moved_meaningfully": moved,
        }

    sensitive_metrics = [
        m for m, v in metric_comparisons.items() if v.get("moved_meaningfully")
    ]
    return {
        "label_a": label_a,
        "label_b": label_b,
        "sensitive_metrics": sensitive_metrics,
        "metrics": metric_comparisons,
    }


# ---------------------------------------------------------------------------
# Ablation runners
# ---------------------------------------------------------------------------

def run_ablation_governance(
    total_turns: int = ABLATION_TOTAL_TURNS,
    n_seeds: int = ABLATION_N_SEEDS,
    output_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Ablation 1: governance_on vs governance_off."""
    root = (output_root or _OUTPUT_ROOT) / "ablation_governance"
    results_on, results_off = [], []
    for seed in range(n_seeds):
        metrics_on = _run_one(
            _BASE_PARAMS, total_turns, seed, PROBE_MODE_PASSIVE,
            root / "gov_on" / f"seed_{seed:02d}", gov_off=False,
        )
        results_on.append(metrics_on)
        metrics_off = _run_one(
            _BASE_PARAMS, total_turns, seed, PROBE_MODE_PASSIVE,
            root / "gov_off" / f"seed_{seed:02d}", gov_off=True,
        )
        results_off.append(metrics_off)
    return _compare_arms("governance_on", "governance_off", results_on, results_off)


def run_ablation_probe_mode(
    total_turns: int = ABLATION_TOTAL_TURNS,
    n_seeds: int = ABLATION_N_SEEDS,
    output_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Ablation 2: passive vs active_measurement_model (inactive excluded as degenerate)."""
    root = (output_root or _OUTPUT_ROOT) / "ablation_probe_mode"
    results_passive, results_active = [], []
    for seed in range(n_seeds):
        m_pass = _run_one(
            _BASE_PARAMS, total_turns, seed, PROBE_MODE_PASSIVE,
            root / "passive" / f"seed_{seed:02d}",
        )
        results_passive.append(m_pass)
        m_act = _run_one(
            _BASE_PARAMS, total_turns, seed, PROBE_MODE_ACTIVE_MEASUREMENT,
            root / "active" / f"seed_{seed:02d}",
        )
        results_active.append(m_act)
    return _compare_arms("probe_passive", "probe_active_measurement", results_passive, results_active)


def run_ablation_agent_type(
    total_turns: int = ABLATION_TOTAL_TURNS,
    n_seeds: int = ABLATION_N_SEEDS,
    output_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Ablation 3: normal agent vs low-cooperation (baseline) agent."""
    root = (output_root or _OUTPUT_ROOT) / "ablation_agent_type"
    _baseline_params = {
        "_name": "abl_baseline_agent",
        "governance_strictness": 1.0,
        "cooperation_bias": 0.1,
        "initial_agent_trust": 0.2,
    }
    results_normal, results_baseline = [], []
    for seed in range(n_seeds):
        m_norm = _run_one(
            _BASE_PARAMS, total_turns, seed, PROBE_MODE_PASSIVE,
            root / "normal" / f"seed_{seed:02d}",
        )
        results_normal.append(m_norm)
        m_base = _run_one(
            _baseline_params, total_turns, seed, PROBE_MODE_PASSIVE,
            root / "baseline" / f"seed_{seed:02d}",
        )
        results_baseline.append(m_base)
    return _compare_arms("normal_agent", "baseline_agent", results_normal, results_baseline)


def run_ablation_bandwidth(
    total_turns: int = ABLATION_TOTAL_TURNS,
    n_seeds: int = ABLATION_N_SEEDS,
    output_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Ablation 4: bandwidth unconstrained (passive) vs constrained (active, period=2)."""
    root = (output_root or _OUTPUT_ROOT) / "ablation_bandwidth"
    results_unc, results_con = [], []
    for seed in range(n_seeds):
        m_unc = _run_one(
            _BASE_PARAMS, total_turns, seed, PROBE_MODE_PASSIVE,
            root / "unconstrained" / f"seed_{seed:02d}",
        )
        results_unc.append(m_unc)
        m_con = _run_one(
            _BASE_PARAMS, total_turns, seed, PROBE_MODE_ACTIVE_MEASUREMENT,
            root / "constrained" / f"seed_{seed:02d}",
            observe_period=2,
        )
        results_con.append(m_con)
    return _compare_arms("bandwidth_unconstrained", "bandwidth_constrained", results_unc, results_con)


def run_ablation_cooperation(
    total_turns: int = ABLATION_TOTAL_TURNS,
    n_seeds: int = ABLATION_N_SEEDS,
    output_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Ablation 5: high cooperation (0.9) vs low cooperation (0.1)."""
    root = (output_root or _OUTPUT_ROOT) / "ablation_cooperation"
    _high_coop = copy.deepcopy(_BASE_PARAMS)
    _high_coop["_name"] = "abl_high_coop"
    _high_coop["cooperation_bias"] = 0.9
    _low_coop = copy.deepcopy(_BASE_PARAMS)
    _low_coop["_name"] = "abl_low_coop"
    _low_coop["cooperation_bias"] = 0.1

    results_high, results_low = [], []
    for seed in range(n_seeds):
        m_high = _run_one(
            _high_coop, total_turns, seed, PROBE_MODE_PASSIVE,
            root / "high_coop" / f"seed_{seed:02d}",
        )
        results_high.append(m_high)
        m_low = _run_one(
            _low_coop, total_turns, seed, PROBE_MODE_PASSIVE,
            root / "low_coop" / f"seed_{seed:02d}",
        )
        results_low.append(m_low)
    return _compare_arms("cooperation_high", "cooperation_low", results_high, results_low)


# ---------------------------------------------------------------------------
# Master runner
# ---------------------------------------------------------------------------

def run_all_ablations(
    total_turns: int = ABLATION_TOTAL_TURNS,
    n_seeds: int = ABLATION_N_SEEDS,
    output_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Run all ablation studies and write combined report."""
    root = output_root or _OUTPUT_ROOT

    ablations = {}
    ablations["governance"] = run_ablation_governance(total_turns, n_seeds, root)
    ablations["probe_mode"] = run_ablation_probe_mode(total_turns, n_seeds, root)
    ablations["agent_type"] = run_ablation_agent_type(total_turns, n_seeds, root)
    ablations["bandwidth"] = run_ablation_bandwidth(total_turns, n_seeds, root)
    ablations["cooperation"] = run_ablation_cooperation(total_turns, n_seeds, root)

    # Note: encoding_variant ablation is handled by encoding_robustness.py
    # (it is a post-hoc re-encoding, not a runtime toggle)
    ablations["encoding_variant"] = {
        "label_a": "BFS+MDS",
        "label_b": "pure_hop / manual_topological",
        "note": "Handled by encoding_robustness.py — see encoding_robustness_report.json",
        "sensitive_metrics": [
            "mean_position_error", "stability_score", "anisotropy_score"
        ],
    }

    # Build CSV summary
    root.mkdir(parents=True, exist_ok=True)
    rows = []
    for abl_name, result in ablations.items():
        for m, info in result.get("metrics", {}).items():
            rows.append({
                "ablation": abl_name,
                "condition_a": result.get("label_a", ""),
                "condition_b": result.get("label_b", ""),
                "metric": m,
                "mean_a": info.get("mean_a"),
                "mean_b": info.get("mean_b"),
                "delta": info.get("delta"),
                "cohens_d": info.get("cohens_d"),
                "moved_meaningfully": info.get("moved_meaningfully", False),
            })

    csv_path = root / "ablation_summary.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=[
                "ablation", "condition_a", "condition_b", "metric",
                "mean_a", "mean_b", "delta", "cohens_d", "moved_meaningfully",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    report = {
        "stage": "Stage 5",
        "description": "Ablation studies — one factor toggled at a time.",
        "total_turns": total_turns,
        "n_seeds": n_seeds,
        "ablations": ablations,
    }
    report_path = root / "ablation_report.json"
    with open(report_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)

    return report


if __name__ == "__main__":
    result = run_all_ablations()
    print("Ablation report written.")
    for name, abl in result["ablations"].items():
        print(f"  {name}: sensitive_metrics = {abl.get('sensitive_metrics', [])}")
