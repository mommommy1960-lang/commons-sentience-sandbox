"""
stage6_probe_impact_test.py — Long-horizon sandbox-native probe-impact comparison.

Motivation
----------
The Stage 6 first observation-effect test (stage6_first_test.py) produced a null
result at 25 turns because:

  1. The inactive probe returns no audit metrics, making numeric probe-metric
     comparison impossible.
  2. The active-vs-passive comparison showed Cohen's d = 0.0 on probe metrics
     only, not on simulation-native behaviour signals.

This module provides a *sandbox-native* comparison by extracting behavioural
traces directly from the agents' ``state_history`` (populated by the
simulation itself, independent of probe mode) and from the probe's detailed
per-turn raw_log where available.

Comparison strategy
-------------------
For each (seed, horizon) cell, three parallel runs are performed:

  inactive  — no probe; agents' state_history is the ONLY record source
  passive   — read-only probe; state_history + full probe raw_log
  active    — active_measurement_model; state_history + probe raw_log

All three runs share the same Python random seed, so *if the probe is truly
read-only* the room-sequence and action-sequence extracted from state_history
must be byte-for-byte identical across conditions.  Any divergence in those
sequences is evidence of a probe behavioural effect.

Sandbox-native metrics extracted per run
-----------------------------------------
  room_sequence          list[str]   — rooms visited per turn (from state_history)
  action_sequence        list[str]   — actions chosen per turn
  final_room             str         — room at last turn
  room_distribution      dict        — fraction of turns spent in each room
  mean_contradiction     float       — mean contradiction_pressure over turns
  mean_trust             float       — mean trust_in_{other} over turns
  oversight_events       int         — len(agent.oversight_log)
  memory_count_final     int         — len(agent.episodic_memory) at end
  contradict_total       int         — total contradiction events (len agent.pending_contradictions)

Comparison metrics between two conditions (same seed, different probe)
----------------------------------------------------------------------
  room_seq_identical   bool   — True if sequences match character-by-character
  action_seq_identical bool   — True if action lists are identical
  final_room_match     bool   — True if final rooms match
  room_dist_l1         float  — L1 distance between room distributions
  contradiction_delta  float  — abs(mean_contradiction_A - mean_contradiction_B)
  trust_delta          float  — abs(mean_trust_A - mean_trust_B)
  oversight_delta      int    — abs(oversight_A - oversight_B)
  memory_delta         int    — abs(memory_count_A - memory_count_B)

Classification per comparison
------------------------------
  exact_match                   — all sequences identical, all deltas = 0
  near_match_acceptable         — sequences match; small numeric float differences
  unexpected_divergence         — sequences differ or delta > threshold
  incomparable_nondeterminism   — nondeterministic field prevents comparison

Output
------
commons_sentience_sim/output/reality_audit/stage6_probe_impact_report.json
commons_sentience_sim/output/reality_audit/stage6_probe_impact_summary.csv
"""

from __future__ import annotations

import csv
import json
import random
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from experiment_config import ExperimentConfig
from reality_audit.adapters.sim_probe import (
    SimProbe,
    PROBE_MODE_INACTIVE,
    PROBE_MODE_PASSIVE,
    PROBE_MODE_ACTIVE_MEASUREMENT,
)
from reality_audit.experiments.sandbox_campaigns import (
    _run_simulation_with_probe,
    _make_config,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_OUTPUT_ROOT = (
    _REPO_ROOT / "commons_sentience_sim" / "output" / "reality_audit"
)
_DATA_DIR = _REPO_ROOT / "commons_sentience_sim" / "data"
_ROOMS_JSON = _DATA_DIR / "rooms.json"

_BASE_PARAMS: Dict[str, Any] = {
    "_name": "pit_baseline",
    "governance_strictness": 1.0,
    "cooperation_bias": 0.5,
    "initial_agent_trust": 0.5,
}

# Threshold for "near match" — small floating-point differences are acceptable
_NUMERIC_NEAR_THRESH = 0.01

# Horizons and seeds for the full comparison
DEFAULT_HORIZONS: List[int] = [25, 50, 100]
DEFAULT_N_SEEDS: int = 3

_CONDITIONS: List[Tuple[str, str]] = [
    ("inactive", PROBE_MODE_INACTIVE),
    ("passive", PROBE_MODE_PASSIVE),
    ("active", PROBE_MODE_ACTIVE_MEASUREMENT),
]

# ---------------------------------------------------------------------------
# Sandbox-native feature extraction
# ---------------------------------------------------------------------------

def _extract_sandbox_features(
    agent: Any,
    agent_name: str,
    other_name: str,
) -> Dict[str, Any]:
    """Extract behavioural signals from an agent's state_history.

    Uses ONLY fields populated by the simulation itself — does NOT read from
    the probe.  Works correctly whether probe is inactive or not.
    """
    hist = agent.state_history  # list of per-turn snapshot dicts

    if not hist:
        return {
            "room_sequence": [],
            "action_sequence": [],
            "final_room": None,
            "room_distribution": {},
            "mean_contradiction": 0.0,
            "mean_trust": 0.0,
            "oversight_events": 0,
            "memory_count_final": 0,
            "turns_recorded": 0,
        }

    room_seq: List[str] = [h["room"] for h in hist]
    action_seq: List[Optional[str]] = [h.get("action") for h in hist]
    final_room: str = room_seq[-1]

    # Room distribution
    room_ctr = Counter(room_seq)
    total = len(room_seq)
    room_dist: Dict[str, float] = {r: c / total for r, c in room_ctr.items()}

    # Mean contradiction_pressure
    contradictions = [h.get("contradiction_pressure", 0.0) for h in hist]
    mean_contradiction = sum(contradictions) / len(contradictions)

    # Mean trust in other agent
    trust_key = f"trust_in_{other_name}"
    trusts = [h.get(trust_key, 0.5) for h in hist]
    mean_trust = sum(trusts) / len(trusts)

    # Oversight events (governance checks / blocks)
    try:
        oversight_events = len(agent.oversight_log)
    except AttributeError:
        oversight_events = 0

    # Final memory count
    try:
        memory_count_final = len(agent.episodic_memory)
    except AttributeError:
        memory_count_final = 0

    return {
        "room_sequence": room_seq,
        "action_sequence": [str(a) if a is not None else "None" for a in action_seq],
        "final_room": final_room,
        "room_distribution": room_dist,
        "mean_contradiction": round(mean_contradiction, 6),
        "mean_trust": round(mean_trust, 6),
        "oversight_events": oversight_events,
        "memory_count_final": memory_count_final,
        "turns_recorded": len(hist),
    }


# ---------------------------------------------------------------------------
# Single run
# ---------------------------------------------------------------------------

def _run_one(
    probe_mode: str,
    total_turns: int,
    seed: int,
    run_dir: Path,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Run one simulation cell; returns (sentinel_features, aster_features)."""
    random.seed(seed)

    cfg = _make_config(dict(_BASE_PARAMS), total_turns)
    probe = SimProbe(
        rooms_json_path=_ROOMS_JSON,
        output_dir=run_dir,
        probe_mode=probe_mode,
    )
    sentinel, aster = _run_simulation_with_probe(cfg, probe, run_dir)
    probe.finalize()

    s_feat = _extract_sandbox_features(sentinel, "Sentinel", "Aster")
    a_feat = _extract_sandbox_features(aster, "Aster", "Sentinel")

    # Attach some probe-mode metadata
    # (probe raw_log available for passive/active; empty for inactive)
    s_feat["probe_mode"] = probe_mode
    a_feat["probe_mode"] = probe_mode
    s_feat["seed"] = seed
    a_feat["seed"] = seed
    s_feat["total_turns"] = total_turns
    a_feat["total_turns"] = total_turns

    return s_feat, a_feat


# ---------------------------------------------------------------------------
# Comparison helpers
# ---------------------------------------------------------------------------

def _room_dist_l1(dist_a: Dict[str, float], dist_b: Dict[str, float]) -> float:
    """L1 distance between two room-distribution dicts."""
    all_rooms = set(dist_a) | set(dist_b)
    return sum(abs(dist_a.get(r, 0.0) - dist_b.get(r, 0.0)) for r in all_rooms)


def _classify_comparison(
    room_seq_identical: bool,
    action_seq_identical: bool,
    final_room_match: bool,
    room_dist_l1_val: float,
    contradiction_delta: float,
    trust_delta: float,
    oversight_delta: int,
) -> str:
    """Classify the outcome of comparing two same-seed runs under different probe modes."""
    if (
        room_seq_identical
        and action_seq_identical
        and final_room_match
        and room_dist_l1_val < _NUMERIC_NEAR_THRESH
        and contradiction_delta < _NUMERIC_NEAR_THRESH
        and trust_delta < _NUMERIC_NEAR_THRESH
        and oversight_delta == 0
    ):
        return "exact_match"

    # Sequences match but tiny float drift (acceptable for read-only claim)
    if room_seq_identical and action_seq_identical and final_room_match:
        return "near_match_acceptable"

    # Sequences diverge — this is the key signal
    if not room_seq_identical or not action_seq_identical or not final_room_match:
        return "unexpected_divergence"

    return "incomparable_nondeterminism"


def _compare_features(
    feat_a: Dict[str, Any],
    feat_b: Dict[str, Any],
    label_a: str,
    label_b: str,
) -> Dict[str, Any]:
    """Compare two same-seed sandbox-native feature dicts."""
    room_identical = feat_a["room_sequence"] == feat_b["room_sequence"]
    action_identical = feat_a["action_sequence"] == feat_b["action_sequence"]
    final_match = feat_a["final_room"] == feat_b["final_room"]
    dist_l1 = _room_dist_l1(feat_a["room_distribution"], feat_b["room_distribution"])
    contra_delta = abs(feat_a["mean_contradiction"] - feat_b["mean_contradiction"])
    trust_delta = abs(feat_a["mean_trust"] - feat_b["mean_trust"])
    oversight_delta = abs(feat_a["oversight_events"] - feat_b["oversight_events"])
    memory_delta = abs(feat_a["memory_count_final"] - feat_b["memory_count_final"])

    classification = _classify_comparison(
        room_identical,
        action_identical,
        final_match,
        dist_l1,
        contra_delta,
        trust_delta,
        oversight_delta,
    )

    return {
        "label_a": label_a,
        "label_b": label_b,
        "seed": feat_a["seed"],
        "total_turns": feat_a["total_turns"],
        "room_seq_identical": room_identical,
        "action_seq_identical": action_identical,
        "final_room_match": final_match,
        "final_room_a": feat_a["final_room"],
        "final_room_b": feat_b["final_room"],
        "room_dist_l1": round(dist_l1, 6),
        "contradiction_delta": round(contra_delta, 6),
        "trust_delta": round(trust_delta, 6),
        "oversight_delta": oversight_delta,
        "memory_delta": memory_delta,
        "classification": classification,
    }


# ---------------------------------------------------------------------------
# Core orchestration
# ---------------------------------------------------------------------------

def run_probe_impact_test(
    horizons: Optional[List[int]] = None,
    n_seeds: int = DEFAULT_N_SEEDS,
    output_root: Optional[Path] = None,
    include_active: bool = True,
) -> Dict[str, Any]:
    """Run the full probe-impact test across horizons and seeds.

    Parameters
    ----------
    horizons : list of int, optional
        Turn counts to run.  Defaults to [25, 50, 100].
    n_seeds : int
        Number of random seeds per (horizon, probe_mode) cell.
    output_root : Path, optional
        Override output root directory.
    include_active : bool
        Whether to include the active_measurement_model condition
        (experimental; slower).

    Returns
    -------
    dict
        Full results report, also written to
        ``output_root/stage6_probe_impact_report.json``.
    """
    horizons = horizons or DEFAULT_HORIZONS
    root = output_root or DEFAULT_OUTPUT_ROOT
    test_root = root / "stage6_probe_impact"
    test_root.mkdir(parents=True, exist_ok=True)

    conditions = [
        ("inactive", PROBE_MODE_INACTIVE),
        ("passive", PROBE_MODE_PASSIVE),
    ]
    if include_active:
        conditions.append(("active", PROBE_MODE_ACTIVE_MEASUREMENT))

    # ── Collect all per-cell results ─────────────────────────────────────
    # Structure: results[horizon][condition_label][seed] = (s_feat, a_feat)
    all_features: Dict[int, Dict[str, Dict[int, Tuple[Any, Any]]]] = {}

    for horizon in horizons:
        all_features[horizon] = {}
        for cond_label, probe_mode in conditions:
            all_features[horizon][cond_label] = {}
            for seed in range(n_seeds):
                run_dir = test_root / f"h{horizon}" / cond_label / f"seed_{seed:02d}"
                run_dir.mkdir(parents=True, exist_ok=True)
                print(
                    f"  [probe_impact] horizon={horizon} cond={cond_label} seed={seed}",
                    flush=True,
                )
                s_feat, a_feat = _run_one(probe_mode, horizon, seed, run_dir)
                all_features[horizon][cond_label][seed] = (s_feat, a_feat)

    # ── Build per-horizon comparison table ───────────────────────────────
    comparisons: List[Dict[str, Any]] = []
    horizon_summaries: Dict[int, Dict[str, Any]] = {}

    for horizon in horizons:
        horizon_comps: List[Dict[str, Any]] = []

        for seed in range(n_seeds):
            # Compare: passive vs inactive
            s_inactive, a_inactive = all_features[horizon]["inactive"][seed]
            s_passive, a_passive = all_features[horizon]["passive"][seed]

            for agent_label, feat_inactive, feat_passive in [
                ("Sentinel", s_inactive, s_passive),
                ("Aster", a_inactive, a_passive),
            ]:
                comp = _compare_features(
                    feat_inactive, feat_passive,
                    f"inactive_{agent_label}", f"passive_{agent_label}",
                )
                comp["agent"] = agent_label
                comp["comparison"] = "passive_vs_inactive"
                horizon_comps.append(comp)

            # Compare: active vs passive (if available)
            if include_active and "active" in all_features[horizon]:
                s_active, a_active = all_features[horizon]["active"][seed]
                for agent_label, feat_passive, feat_active in [
                    ("Sentinel", s_passive, s_active),
                    ("Aster", a_passive, a_active),
                ]:
                    comp = _compare_features(
                        feat_passive, feat_active,
                        f"passive_{agent_label}", f"active_{agent_label}",
                    )
                    comp["agent"] = agent_label
                    comp["comparison"] = "active_vs_passive"
                    horizon_comps.append(comp)

        comparisons.extend(horizon_comps)

        # Summarise this horizon
        pvi_comps = [c for c in horizon_comps if c["comparison"] == "passive_vs_inactive"]
        avp_comps = [c for c in horizon_comps if c["comparison"] == "active_vs_passive"]

        def _summarise(comps: List[Dict[str, Any]]) -> Dict[str, Any]:
            if not comps:
                return {"n": 0, "verdict": "not_run"}
            n = len(comps)
            n_exact = sum(1 for c in comps if c["classification"] == "exact_match")
            n_near = sum(1 for c in comps if c["classification"] == "near_match_acceptable")
            n_div = sum(1 for c in comps if c["classification"] == "unexpected_divergence")
            n_room_identical = sum(1 for c in comps if c["room_seq_identical"])
            n_action_identical = sum(1 for c in comps if c["action_seq_identical"])
            n_final_match = sum(1 for c in comps if c["final_room_match"])
            mean_dist_l1 = sum(c["room_dist_l1"] for c in comps) / n
            mean_contra_delta = sum(c["contradiction_delta"] for c in comps) / n

            if n_div > 0:
                verdict = "divergence_detected"
            elif n_exact + n_near == n:
                verdict = "read_only_confirmed_exact_match" if n_exact == n else "read_only_confirmed_near_match"
            else:
                verdict = "mixed_result"

            return {
                "n": n,
                "n_exact_match": n_exact,
                "n_near_match": n_near,
                "n_divergence": n_div,
                "room_seq_identical_fraction": round(n_room_identical / n, 4),
                "action_seq_identical_fraction": round(n_action_identical / n, 4),
                "final_room_match_fraction": round(n_final_match / n, 4),
                "mean_room_dist_l1": round(mean_dist_l1, 6),
                "mean_contradiction_delta": round(mean_contra_delta, 6),
                "verdict": verdict,
            }

        horizon_summaries[horizon] = {
            "horizon": horizon,
            "passive_vs_inactive": _summarise(pvi_comps),
            "active_vs_passive": _summarise(avp_comps),
        }

    # ── Determine overall verdicts ───────────────────────────────────────
    all_pvi = [c for c in comparisons if c["comparison"] == "passive_vs_inactive"]
    all_avp = [c for c in comparisons if c["comparison"] == "active_vs_passive"]

    def _overall_verdict(label: str, comps: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not comps:
            return {"label": label, "verdict": "not_run", "details": "condition not included"}
        n_div = sum(1 for c in comps if c["classification"] == "unexpected_divergence")
        n_exact = sum(1 for c in comps if c["classification"] == "exact_match")
        n_near = sum(1 for c in comps if c["classification"] == "near_match_acceptable")
        n = len(comps)
        room_id_frac = sum(1 for c in comps if c["room_seq_identical"]) / n
        first_divergence_horizon: Optional[int] = None
        for horizon in sorted(horizons):
            h_comps = [c for c in comps if c["total_turns"] == horizon]
            if any(c["classification"] == "unexpected_divergence" for c in h_comps):
                first_divergence_horizon = horizon
                break

        if n_div == 0 and room_id_frac == 1.0:
            verdict = "probe_is_behaviorally_read_only"
            interp = (
                f"All {n} comparisons for '{label}' returned identical room and action "
                f"sequences. Passive probe introduces no detectable change in sandbox "
                f"behaviour across all tested horizons and seeds."
            )
        elif n_div > 0:
            verdict = "divergence_detected"
            interp = (
                f"{n_div}/{n} comparisons showed sequence divergence for '{label}'. "
                f"First divergence at horizon {first_divergence_horizon}. "
                f"This warrants further investigation."
            )
        else:
            verdict = "near_match_read_only_probable"
            interp = (
                f"Sequences matched in {n_exact + n_near}/{n} comparisons for '{label}'. "
                f"Small numeric differences present but no sequence divergence."
            )

        return {
            "label": label,
            "n_comparisons": n,
            "n_exact": n_exact,
            "n_near": n_near,
            "n_divergence": n_div,
            "room_seq_identical_fraction": round(room_id_frac, 4),
            "first_divergence_horizon": first_divergence_horizon,
            "verdict": verdict,
            "interpretation": interp,
        }

    pvi_overall = _overall_verdict("passive_vs_inactive", all_pvi)
    avp_overall = _overall_verdict("active_vs_passive", all_avp)

    # ── Probe-layer metrics summary (passive and active only) ────────────
    # Also summarise probe-metric deltas by loading finalized summary.jsons
    # across passive / active comparisons for those who want both layers.
    probe_metric_note = (
        "Probe-metric layer is reported separately in stage6_first_test/observation_effect_report.json. "
        "This report focuses on sandbox-native behavioural signals only."
    )

    # ── Build report ─────────────────────────────────────────────────────
    report: Dict[str, Any] = {
        "report_type": "stage6_probe_impact_test",
        "horizons_tested": horizons,
        "n_seeds": n_seeds,
        "conditions": [c[0] for c in conditions],
        "include_active": include_active,
        "passive_vs_inactive_overall": pvi_overall,
        "active_vs_passive_overall": avp_overall,
        "horizon_summaries": {str(h): v for h, v in horizon_summaries.items()},
        "all_comparisons": comparisons,
        "sandbox_native_metrics_used": [
            "room_sequence",
            "action_sequence",
            "final_room",
            "room_distribution",
            "mean_contradiction_pressure",
            "mean_trust_in_other_agent",
            "oversight_event_count",
            "episodic_memory_count_final",
        ],
        "determinism_note": (
            "Runs use Python random.seed(seed) before each call. "
            "The simulation is deterministic with respect to this seed for room "
            "navigation and action selection.  LLM-driven fields (contradiction "
            "reasoning text) are not compared; only numeric/categorical state "
            "history is used."
        ),
        "probe_metric_note": probe_metric_note,
    }

    # Write main report
    report_path = root / "stage6_probe_impact_report.json"
    with open(report_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print(f"  [probe_impact] Report written to {report_path}", flush=True)

    # Write CSV summary
    csv_path = root / "stage6_probe_impact_summary.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        if comparisons:
            writer = csv.DictWriter(fh, fieldnames=list(comparisons[0].keys()))
            writer.writeheader()
            writer.writerows(comparisons)
    print(f"  [probe_impact] CSV summary written to {csv_path}", flush=True)

    return report


# ---------------------------------------------------------------------------
# Convenience sub-functions (tested individually)
# ---------------------------------------------------------------------------

def extract_sandbox_features(agent: Any, agent_name: str, other_name: str) -> Dict[str, Any]:
    """Public wrapper for ``_extract_sandbox_features``."""
    return _extract_sandbox_features(agent, agent_name, other_name)


def compare_features(
    feat_a: Dict[str, Any],
    feat_b: Dict[str, Any],
    label_a: str = "A",
    label_b: str = "B",
) -> Dict[str, Any]:
    """Public wrapper for ``_compare_features``."""
    return _compare_features(feat_a, feat_b, label_a, label_b)


def classify_comparison(
    room_seq_identical: bool,
    action_seq_identical: bool,
    final_room_match: bool,
    room_dist_l1: float,
    contradiction_delta: float,
    trust_delta: float,
    oversight_delta: int,
) -> str:
    """Public wrapper for ``_classify_comparison``."""
    return _classify_comparison(
        room_seq_identical,
        action_seq_identical,
        final_room_match,
        room_dist_l1,
        contradiction_delta,
        trust_delta,
        oversight_delta,
    )


if __name__ == "__main__":
    print("Running Stage 6 probe-impact test (25 turns, 3 seeds) ...")
    result = run_probe_impact_test(horizons=[25], n_seeds=3)
    print("\n=== PASSIVE vs INACTIVE ===")
    pvi = result["passive_vs_inactive_overall"]
    print(f"  verdict : {pvi['verdict']}")
    print(f"  interp  : {pvi['interpretation']}")
    print("\n=== ACTIVE vs PASSIVE ===")
    avp = result["active_vs_passive_overall"]
    print(f"  verdict : {avp['verdict']}")
    print(f"  interp  : {avp['interpretation']}")
