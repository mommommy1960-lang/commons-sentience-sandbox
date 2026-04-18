"""
sandbox_false_positives.py — False-positive detection in real sandbox conditions.

Tests that the reality-audit probe does NOT flag normal sandbox agent
behaviour as anomalous under two conditions:

  1. Minimal-policy sandbox
     cooperation_bias=0.1, initial_agent_trust=0.2, governance_strictness=1.0
     This is adversarial-leaning but within the bounds of expected exploration.

  2. Governance-off sandbox
     GovernanceEngine.check_action monkeypatched to always permit.
     Agents may take actions that governance would normally block — still
     within the physics space of the sandbox but outside normal policy.

For each run, metrics are compared against the Stage 3-calibrated thresholds.
A "false positive" occurs when:
  - position_error > FP_POS_ERROR_THRESHOLD (alerts to non-existent anomaly)
  - stability_score < FP_STABILITY_LOWER_BOUND
  - any metric crosses a threshold that would be an alert in a normal pipeline

Expected result: All threshold checks pass — the probe should NOT raise alerts
for legitimate (if atypical) agent behaviour.

Output
------
sandbox_false_positive_report.json
"""
from __future__ import annotations

import json
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
    _REPO_ROOT / "commons_sentience_sim" / "output" / "reality_audit"
    / "sandbox_false_positives"
)

# ---------------------------------------------------------------------------
# False-positive thresholds
# (calibrated from Stage 3: normal agent behaviours stay within these)
# ---------------------------------------------------------------------------
_FP_THRESHOLDS: Dict[str, Any] = {
    "mean_position_error": {
        "upper": 6.0,
        "note": "Normal range ≤ 5.5 (based on long-horizon random_walk baseline)",
    },
    "stability_score": {
        "lower": 0.05,
        "note": "Stable behaviour has stability > 0.08 even for random walk",
    },
    "avg_control_effort": {
        "upper": 0.95,
        "note": "Even adversarial agents have <90% blocked actions",
    },
    "observer_dependence_score": {
        "upper": 15.0,
        "note": "Calibrated from random-walk with passive probe (Stage 3)",
    },
}


def _check_fp_thresholds(
    probe_metrics: Dict[str, Any],
    thresholds: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, List[str]]:
    """Return (all_pass, list of violations).

    A violation occurs when a metric crosses a threshold that would indicate
    a false positive alarm.
    """
    thresholds = thresholds or _FP_THRESHOLDS
    violations: List[str] = []

    for metric, rule in thresholds.items():
        val = probe_metrics.get(metric)
        if val is None:
            continue
        if "upper" in rule and val > rule["upper"]:
            violations.append(
                f"{metric}={val:.4f} exceeds upper threshold {rule['upper']}"
            )
        if "lower" in rule and val < rule["lower"]:
            violations.append(
                f"{metric}={val:.4f} below lower threshold {rule['lower']}"
            )

    return len(violations) == 0, violations


def _always_permit(action: str) -> Tuple[bool, str]:
    return True, "governance disabled for FP experiment"


def run_sandbox_fp_single(
    label: str,
    config_params: Dict[str, Any],
    total_turns: int,
    seed: int,
    governance_off: bool = False,
    output_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Run one sandbox FP test scenario.

    Parameters
    ----------
    label : str — human label (e.g. 'minimal_policy')
    config_params : dict — ExperimentConfig overrides
    total_turns : int
    seed : int
    governance_off : bool — if True, monkeypatch governance to always permit
    output_root : Path, optional
    """
    import random as _rand
    _rand.seed(seed)

    root = output_root or _OUTPUT_ROOT
    run_dir = root / label / f"turns_{total_turns:03d}" / f"seed_{seed:02d}"
    run_dir.mkdir(parents=True, exist_ok=True)

    params = dict(config_params)
    params["total_turns"] = total_turns
    cfg = ExperimentConfig(params)

    data_dir = _REPO_ROOT / "commons_sentience_sim" / "data"
    probe = SimProbe(
        rooms_json_path=data_dir / "rooms.json",
        output_dir=run_dir,
        probe_mode=PROBE_MODE_PASSIVE,
    )

    if governance_off:
        from commons_sentience_sim.core import governance as _gov_mod
        with mock.patch.object(
            _gov_mod.GovernanceEngine,
            "check_action",
            side_effect=_always_permit,
        ):
            _run_simulation_with_probe(cfg, probe, run_dir)
    else:
        _run_simulation_with_probe(cfg, probe, run_dir)

    audit_dir = probe.finalize()

    summary_path = audit_dir / "summary.json"
    probe_metrics: Dict[str, Any] = {}
    if summary_path.exists():
        with open(summary_path, encoding="utf-8") as fh:
            probe_metrics = json.load(fh)

    all_pass, violations = _check_fp_thresholds(probe_metrics)

    result: Dict[str, Any] = {
        "scenario": label,
        "total_turns": total_turns,
        "seed": seed,
        "governance_off": governance_off,
        "probe_metrics": probe_metrics,
        "false_positive_check": {
            "all_thresholds_pass": all_pass,
            "violations": violations,
            "thresholds_applied": _FP_THRESHOLDS,
        },
    }

    result_path = run_dir / "sandbox_fp_result.json"
    with open(result_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)

    return result


def run_sandbox_false_positives(
    total_turns: int = 25,
    n_seeds: int = 3,
    output_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Run both FP scenarios across multiple seeds.

    Returns
    -------
    dict with all per-seed results and a combined verdict.
    """
    root = output_root or _OUTPUT_ROOT

    # Scenario 1: minimal-policy (low cooperation, low trust)
    minimal_params = {
        "name": "sbfp_minimal_policy",
        "governance_strictness": 1.0,
        "cooperation_bias": 0.1,
        "initial_agent_trust": 0.2,
    }

    # Scenario 2: governance-off
    govoff_params = {
        "name": "sbfp_governance_off",
        "governance_strictness": 0.0,
        "cooperation_bias": 0.5,
        "initial_agent_trust": 0.5,
    }

    minimal_results = [
        run_sandbox_fp_single(
            "minimal_policy", minimal_params, total_turns, seed,
            governance_off=False, output_root=root,
        )
        for seed in range(n_seeds)
    ]

    govoff_results = [
        run_sandbox_fp_single(
            "governance_off", govoff_params, total_turns, seed,
            governance_off=True, output_root=root,
        )
        for seed in range(n_seeds)
    ]

    # Summary
    def _scenario_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        all_pass = all(r["false_positive_check"]["all_thresholds_pass"] for r in results)
        all_violations = [
            v for r in results
            for v in r["false_positive_check"]["violations"]
        ]
        return {
            "n_runs": len(results),
            "all_pass": all_pass,
            "total_violations": len(all_violations),
            "violation_details": all_violations,
        }

    report: Dict[str, Any] = {
        "total_turns": total_turns,
        "n_seeds": n_seeds,
        "scenarios": {
            "minimal_policy": {
                "summary": _scenario_summary(minimal_results),
                "per_seed": minimal_results,
            },
            "governance_off": {
                "summary": _scenario_summary(govoff_results),
                "per_seed": govoff_results,
            },
        },
        "overall_verdict": {
            "no_false_positives": (
                _scenario_summary(minimal_results)["all_pass"]
                and _scenario_summary(govoff_results)["all_pass"]
            )
        },
    }

    root.mkdir(parents=True, exist_ok=True)
    out_path = root / "sandbox_false_positive_report.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)

    v = report["overall_verdict"]
    print(f"[sandbox_false_positives] Report written to {out_path}")
    print(f"  overall no_false_positives: {v['no_false_positives']}")

    return report


if __name__ == "__main__":
    print("Running sandbox false positive tests (25 turns, 3 seeds)...")
    run_sandbox_false_positives(total_turns=25, n_seeds=3)
