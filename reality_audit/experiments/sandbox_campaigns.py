"""
sandbox_campaigns.py — Real sandbox repeated campaigns for Stage 4.

Runs the commons_sentience_sim sandbox (Sentinel + Aster) with 6 config
variants across multiple seeds and turn counts, collecting full reality-audit
probe output for each run.

Configurations
--------------
A  baseline          — normal agents, passive probe, governance_strictness=1.0
B  strict_governance — governance_strictness=1.5 (metadata)
C  relaxed_governance— governance_strictness=0.5 (metadata)
D  probe_inactive    — probe mode = inactive (no audit data)
E  active_measurement— probe mode = active_measurement_model
F  low_cooperation   — cooperation_bias=0.1, reduced trust initial_agent_trust=0.3

Turn counts: 25, 50, 100  (use total_turns in config)
Seeds: 5 independent runs per (config, turns) combination
"""
from __future__ import annotations

import copy
import json
import random
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Path setup for running from repo root
# ---------------------------------------------------------------------------
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

# Output root
_OUTPUT_ROOT = _REPO_ROOT / "commons_sentience_sim" / "output" / "reality_audit" / "sandbox_campaigns"

# ---------------------------------------------------------------------------
# Configuration definitions
# ---------------------------------------------------------------------------

_CONFIG_A_PARAMS: Dict[str, Any] = {
    "_name": "sc_baseline",
    "governance_strictness": 1.0,
    "cooperation_bias": 0.5,
    "initial_agent_trust": 0.5,
}

_CONFIG_B_PARAMS: Dict[str, Any] = {
    "_name": "sc_strict_governance",
    "governance_strictness": 1.5,
    "cooperation_bias": 0.5,
    "initial_agent_trust": 0.5,
}

_CONFIG_C_PARAMS: Dict[str, Any] = {
    "_name": "sc_relaxed_governance",
    "governance_strictness": 0.5,
    "cooperation_bias": 0.5,
    "initial_agent_trust": 0.5,
}

_CONFIG_D_PARAMS: Dict[str, Any] = {
    "_name": "sc_probe_inactive",
    "governance_strictness": 1.0,
    "cooperation_bias": 0.5,
    "initial_agent_trust": 0.5,
}
_CONFIG_D_PROBE_MODE = PROBE_MODE_INACTIVE

_CONFIG_E_PARAMS: Dict[str, Any] = {
    "_name": "sc_active_measurement",
    "governance_strictness": 1.0,
    "cooperation_bias": 0.5,
    "initial_agent_trust": 0.5,
}
_CONFIG_E_PROBE_MODE = PROBE_MODE_ACTIVE_MEASUREMENT

_CONFIG_F_PARAMS: Dict[str, Any] = {
    "_name": "sc_low_cooperation",
    "governance_strictness": 1.0,
    "cooperation_bias": 0.1,
    "initial_agent_trust": 0.3,
}

# Campaign turn counts
CAMPAIGN_TURN_COUNTS = [25, 50, 100]

# Number of seeds per (config, turns) combination
N_SEEDS = 5


def _make_config(params: Dict[str, Any], total_turns: int) -> ExperimentConfig:
    """Build an ExperimentConfig from a parameter dict with a given turn count."""
    merged = copy.deepcopy(params)
    merged["total_turns"] = total_turns
    return ExperimentConfig(merged)


def run_single_campaign(
    config_params: Dict[str, Any],
    total_turns: int,
    seed: int,
    probe_mode: str = PROBE_MODE_PASSIVE,
    output_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Run one sandbox campaign with a given config, turns, seed and probe mode.

    Returns a summary dict with the probe metrics and metadata.

    Parameters
    ----------
    config_params : dict
        Parameter overrides for ExperimentConfig.
    total_turns : int
        Number of simulation turns to run.
    seed : int
        Random seed (used to set Python's random module before the run).
    probe_mode : str
        One of PROBE_MODE_PASSIVE / PROBE_MODE_INACTIVE / PROBE_MODE_ACTIVE_MEASUREMENT.
    output_root : Path, optional
        Override root directory for campaign outputs.
    """
    import random as _rand
    _rand.seed(seed)

    root = output_root or _OUTPUT_ROOT
    cfg_name = config_params.get("_name", config_params.get("name", "unnamed"))
    run_dir = root / cfg_name / f"turns_{total_turns:03d}" / f"seed_{seed:02d}"
    run_dir.mkdir(parents=True, exist_ok=True)

    cfg = _make_config(config_params, total_turns)

    # Build a standalone probe (not injected via run_simulation flag, to allow
    # probe_mode override).  We patch the probe into the simulation manually.
    from reality_audit.adapters.room_distance import RoomPositionEncoder
    _DATA_DIR = _REPO_ROOT / "commons_sentience_sim" / "data"
    rooms_json = _DATA_DIR / "rooms.json"
    probe = SimProbe(
        rooms_json_path=rooms_json,
        output_dir=run_dir,
        probe_mode=probe_mode,
    )

    # Run the sandbox simulation — we call the low-level loop so we can
    # supply our own probe instance rather than relying on the flag.
    sentinel, aster = _run_simulation_with_probe(cfg, probe, run_dir)

    # Finalise probe; returns audit_dir
    audit_dir = probe.finalize()

    # Load the summary that was written by finalize()
    # ExperimentLogger writes "summary.json" (not "audit_summary.json")
    summary_path = audit_dir / "summary.json"
    if probe_mode == PROBE_MODE_INACTIVE or not summary_path.exists():
        probe_metrics: Dict[str, Any] = {
            "probe_mode": probe_mode,
            "note": "probe inactive — no audit metrics collected",
        }
    else:
        with open(summary_path, encoding="utf-8") as fh:
            probe_metrics = json.load(fh)

    result: Dict[str, Any] = {
        "config_name": cfg_name,
        "probe_mode": probe_mode,
        "total_turns": total_turns,
        "seed": seed,
        "governance_strictness": cfg.governance_strictness,
        "cooperation_bias": cfg.cooperation_bias,
        "initial_agent_trust": cfg.initial_agent_trust,
        "audit_dir": str(audit_dir),
        "probe_metrics": probe_metrics,
    }

    # Write per-run result summary
    result_path = run_dir / "campaign_result.json"
    with open(result_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)

    return result


def _run_simulation_with_probe(
    cfg: "ExperimentConfig",
    probe: "SimProbe",
    run_dir: Path,
) -> tuple:
    """Run the commons_sentience_sim simulation with an injected probe.

    Calls run_simulation() from run_sim.py, but monkeypatches the SimProbe
    constructor so that our pre-built *probe* instance is used instead of
    the default passive probe.  This allows probe_mode and output_dir to be
    specified by the caller.

    Parameters
    ----------
    cfg : ExperimentConfig
        Experiment configuration (governs agent behaviour, total_turns, etc.)
    probe : SimProbe
        Pre-built probe instance with the desired mode and output directory.
    run_dir : Path
        Run-specific directory (used for session naming).

    Returns
    -------
    (sentinel, aster) — the two agents after the run.
    """
    import run_sim as _run_sim_mod
    from unittest import mock

    # Monkeypatch the _SimProbe name inside run_sim module so that
    # run_simulation() uses *our* pre-built probe instance.
    # Using side_effect avoids __init__ being called on the returned instance.
    _probe_factory = mock.MagicMock(return_value=probe)

    with mock.patch.object(_run_sim_mod, "_SimProbe", _probe_factory):
        session_label = run_dir.name
        sentinel, aster = _run_sim_mod.run_simulation(
            session_name=session_label,
            experiment_config=cfg,
            enable_reality_audit=True,
        )

    return sentinel, aster


def run_config_a(total_turns: int = 25, n_seeds: int = 3,
                 output_root: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Config A: baseline (passive probe, default governance)."""
    return [
        run_single_campaign(_CONFIG_A_PARAMS, total_turns, seed,
                            PROBE_MODE_PASSIVE, output_root)
        for seed in range(n_seeds)
    ]


def run_config_b(total_turns: int = 25, n_seeds: int = 3,
                 output_root: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Config B: strict governance metadata."""
    return [
        run_single_campaign(_CONFIG_B_PARAMS, total_turns, seed,
                            PROBE_MODE_PASSIVE, output_root)
        for seed in range(n_seeds)
    ]


def run_config_c(total_turns: int = 25, n_seeds: int = 3,
                 output_root: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Config C: relaxed governance metadata."""
    return [
        run_single_campaign(_CONFIG_C_PARAMS, total_turns, seed,
                            PROBE_MODE_PASSIVE, output_root)
        for seed in range(n_seeds)
    ]


def run_config_d(total_turns: int = 25, n_seeds: int = 3,
                 output_root: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Config D: probe inactive."""
    return [
        run_single_campaign(_CONFIG_D_PARAMS, total_turns, seed,
                            PROBE_MODE_INACTIVE, output_root)
        for seed in range(n_seeds)
    ]


def run_config_e(total_turns: int = 25, n_seeds: int = 3,
                 output_root: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Config E: active measurement model (sparse audit sampling)."""
    return [
        run_single_campaign(_CONFIG_E_PARAMS, total_turns, seed,
                            PROBE_MODE_ACTIVE_MEASUREMENT, output_root)
        for seed in range(n_seeds)
    ]


def run_config_f(total_turns: int = 25, n_seeds: int = 3,
                 output_root: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Config F: low cooperation bias + low initial trust."""
    return [
        run_single_campaign(_CONFIG_F_PARAMS, total_turns, seed,
                            PROBE_MODE_PASSIVE, output_root)
        for seed in range(n_seeds)
    ]


def run_all_campaigns(
    turn_counts: Optional[List[int]] = None,
    n_seeds: int = N_SEEDS,
    output_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Run all 6 configurations across all turn counts and seeds.

    Parameters
    ----------
    turn_counts : list of int, optional
        Turn counts to run. Defaults to [25, 50, 100].
    n_seeds : int
        Number of independent seeds per (config, turns) combination.
    output_root : Path, optional
        Override root output directory.

    Returns
    -------
    dict
        Nested dict: config_name → turn_count → list of per-seed results.
    """
    turn_counts = turn_counts or CAMPAIGN_TURN_COUNTS
    root = output_root or _OUTPUT_ROOT

    all_results: Dict[str, Any] = {}

    configs = [
        ("sc_baseline",          _CONFIG_A_PARAMS, PROBE_MODE_PASSIVE),
        ("sc_strict_governance",  _CONFIG_B_PARAMS, PROBE_MODE_PASSIVE),
        ("sc_relaxed_governance", _CONFIG_C_PARAMS, PROBE_MODE_PASSIVE),
        ("sc_probe_inactive",     _CONFIG_D_PARAMS, PROBE_MODE_INACTIVE),
        ("sc_active_measurement", _CONFIG_E_PARAMS, PROBE_MODE_ACTIVE_MEASUREMENT),
        ("sc_low_cooperation",    _CONFIG_F_PARAMS, PROBE_MODE_PASSIVE),
    ]
    for cfg_name, params, probe_mode in configs:
        all_results[cfg_name] = {}
        for tc in turn_counts:
            runs = [
                run_single_campaign(params, tc, seed, probe_mode, root)
                for seed in range(n_seeds)
            ]
            all_results[cfg_name][tc] = runs

    # Write aggregate report
    report_path = root / "sandbox_campaigns_report.json"
    root.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as fh:
        json.dump(all_results, fh, indent=2)

    print(f"[sandbox_campaigns] Report written to {report_path}")
    return all_results


if __name__ == "__main__":
    # Demo: run Config A, 3 seeds, 5 turns for quick validation
    print("Running sandbox campaigns demo (Config A, 5 turns, 3 seeds)...")
    results = run_config_a(total_turns=5, n_seeds=3)
    for r in results:
        pm = r["probe_metrics"]
        print(
            f"  seed={r['seed']}  "
            f"mean_pos_error={pm.get('mean_position_error', 'N/A')}  "
            f"stability={pm.get('stability_score', 'N/A')}  "
            f"path_smoothness={pm.get('path_smoothness', 'N/A')}"
        )
