"""
observer_metrics.py — Three observer-dependence measures for the
reality-audit framework, replacing the ambiguous single
``observer_dependence_score`` in audit_summary.json.

Background
----------
The original ``observer_dependence_score`` computes the mean L2 distance
between the hidden-state position and the measured position.  In passive
probe mode the two are always equal (score ≡ 0).  In active_measurement
mode the hidden state always equals the true current position while the
measured position is the last-cached audit snapshot.  The result is
**start-anchored in non-observer-triggered physics modes** because the
*hidden_state* field in raw_log.json is always the true current position
(not an independent hidden-state propagator), making comparative
interpretations across runs misleading.

This module defines three cleaner measures:

1. hidden_measured_gap_raw
   Same formula as the original score, but with explicit documentation that
   its non-zero value in active_measurement mode reflects audit staleness,
   not agent epistemic opacity.

2. hidden_measured_gap_path_normalised
   The raw gap divided by the total path length of the agent (sum of L2
   distances between consecutive true positions).  This corrects for runs
   of different length and prevents long runs from appearing more opaque.
   Returns None if path length ≈ 0.

3. observation_schedule_sensitivity
   Ratio (active_measurement gap) / (passive gap + ε).  Requires two audit
   raw_log files for the SAME run config: one in passive mode, one in
   active_measurement mode.  A ratio near 1.0 means the audit schedule does
   not affect apparent opacity; a high ratio means the audit is highly
   sensitive to observation frequency.  This is a comparative metric only.

Usage
-----
    from reality_audit.metrics.observer_metrics import (
        hidden_measured_gap_raw,
        hidden_measured_gap_path_normalised,
        observation_schedule_sensitivity,
        compute_all_observer_metrics,
    )
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def _l2(a: List[float], b: List[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def _load_raw_log(audit_dir: Path) -> List[Dict[str, Any]]:
    """Load raw_log.json from an audit directory."""
    path = audit_dir / "raw_log.json"
    if not path.exists():
        raise FileNotFoundError(f"raw_log.json not found in {audit_dir}")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _gap_values(raw_log: List[Dict[str, Any]]) -> List[float]:
    """Per-record L2 distance between hidden_state.position and measured_position."""
    gaps = []
    for r in raw_log:
        hidden = r.get("hidden_state", {}).get("position")
        measured = r.get("measured_position")
        if hidden is not None and measured is not None:
            gaps.append(_l2(hidden, measured))
    return gaps


def _total_path_length(raw_log: List[Dict[str, Any]], agent_name: str) -> float:
    """Sum of L2 distances between consecutive true positions for one agent."""
    positions = [
        r["position"] for r in raw_log
        if r.get("agent_name") == agent_name and r.get("position") is not None
    ]
    if len(positions) < 2:
        return 0.0
    return sum(_l2(positions[i], positions[i + 1]) for i in range(len(positions) - 1))


# ---------------------------------------------------------------------------
# Metric 1: hidden_measured_gap_raw
# ---------------------------------------------------------------------------

def hidden_measured_gap_raw(
    raw_log: List[Dict[str, Any]],
) -> Dict[str, float]:
    """Mean (and std) L2 gap between hidden-state and measured position.

    Parameters
    ----------
    raw_log : list of dicts
        Contents of audit raw_log.json.

    Returns
    -------
    dict with keys: mean_gap, std_gap, max_gap, n_records
    """
    gaps = _gap_values(raw_log)
    n = len(gaps)
    if n == 0:
        return {"mean_gap": 0.0, "std_gap": 0.0, "max_gap": 0.0, "n_records": 0}

    mean = sum(gaps) / n
    variance = sum((g - mean) ** 2 for g in gaps) / n
    return {
        "mean_gap": round(mean, 6),
        "std_gap": round(math.sqrt(variance), 6),
        "max_gap": round(max(gaps), 6),
        "n_records": n,
    }


# ---------------------------------------------------------------------------
# Metric 2: hidden_measured_gap_path_normalised
# ---------------------------------------------------------------------------

def hidden_measured_gap_path_normalised(
    raw_log: List[Dict[str, Any]],
    agent_name: str = "Sentinel",
) -> Dict[str, Optional[float]]:
    """Gap normalised by agent total path length.

    A value of 0 means the measured position always matches the true position.
    A value of 1 means the cumulative gap equals the total path length —
    indicating severe audit staleness relative to actual motion.

    Parameters
    ----------
    raw_log : list of dicts
    agent_name : str
        Agent to compute path length for. Defaults to "Sentinel".

    Returns
    -------
    dict with keys: normalised_gap, raw_mean_gap, path_length, agent_name
      normalised_gap is None if path_length ≈ 0.
    """
    # Filter to agent records
    agent_log = [r for r in raw_log if r.get("agent_name") == agent_name]
    if not agent_log:
        return {
            "normalised_gap": None,
            "raw_mean_gap": None,
            "path_length": None,
            "agent_name": agent_name,
            "note": "no records for agent",
        }

    gaps = _gap_values(agent_log)
    mean_gap = sum(gaps) / len(gaps) if gaps else 0.0
    path_len = _total_path_length(agent_log, agent_name)

    if path_len < 1e-9:
        return {
            "normalised_gap": None,
            "raw_mean_gap": round(mean_gap, 6),
            "path_length": 0.0,
            "agent_name": agent_name,
            "note": "path_length ≈ 0; normalisation undefined",
        }

    return {
        "normalised_gap": round(mean_gap / path_len, 6),
        "raw_mean_gap": round(mean_gap, 6),
        "path_length": round(path_len, 6),
        "agent_name": agent_name,
    }


# ---------------------------------------------------------------------------
# Metric 3: observation_schedule_sensitivity
# ---------------------------------------------------------------------------

def observation_schedule_sensitivity(
    passive_raw_log: List[Dict[str, Any]],
    active_raw_log: List[Dict[str, Any]],
    epsilon: float = 1e-6,
) -> Dict[str, Any]:
    """Ratio of active-measurement gap to passive gap.

    Passive gap is ideally 0 (both positions identical in passive mode).
    Active gap is non-zero when the audit sensor is stale.  The ratio
    quantifies how much the observation *schedule* inflates apparent opacity.

    A ratio > 1 means active mode appears more opaque than passive.
    A ratio of 1.0 means the schedule makes no difference.

    Parameters
    ----------
    passive_raw_log : list of dicts — from a passive probe run
    active_raw_log  : list of dicts — from an active_measurement run
                      of the same scenario
    epsilon : float — denominator floor to avoid division by zero

    Returns
    -------
    dict with keys: sensitivity_ratio, passive_mean_gap, active_mean_gap,
                    interpretation
    """
    passive_gaps = _gap_values(passive_raw_log)
    active_gaps = _gap_values(active_raw_log)

    passive_mean = sum(passive_gaps) / len(passive_gaps) if passive_gaps else 0.0
    active_mean = sum(active_gaps) / len(active_gaps) if active_gaps else 0.0

    ratio = active_mean / (passive_mean + epsilon)

    if ratio < 1.1:
        interpretation = "schedule_insensitive"
    elif ratio < 5.0:
        interpretation = "moderately_schedule_sensitive"
    else:
        interpretation = "highly_schedule_sensitive"

    return {
        "sensitivity_ratio": round(ratio, 4),
        "passive_mean_gap": round(passive_mean, 6),
        "active_mean_gap": round(active_mean, 6),
        "interpretation": interpretation,
    }


# ---------------------------------------------------------------------------
# Composite helper
# ---------------------------------------------------------------------------

def compute_all_observer_metrics(
    audit_dir: Path,
    passive_audit_dir: Optional[Path] = None,
    agent_name: str = "Sentinel",
) -> Dict[str, Any]:
    """Compute all three observer metrics for an audit directory.

    Parameters
    ----------
    audit_dir : Path
        Path to an audit output directory (contains raw_log.json).
    passive_audit_dir : Path, optional
        Passive-mode audit directory for schedule-sensitivity comparison.
        If None, the sensitivity ratio is omitted.
    agent_name : str
        Agent name for path-normalisation metric.

    Returns
    -------
    dict with all computed observer metrics and their interpretations.
    """
    raw_log = _load_raw_log(audit_dir)

    result: Dict[str, Any] = {
        "audit_dir": str(audit_dir),
        "agent_name": agent_name,
        "hidden_measured_gap_raw": hidden_measured_gap_raw(raw_log),
        "hidden_measured_gap_path_normalised": hidden_measured_gap_path_normalised(
            raw_log, agent_name
        ),
    }

    if passive_audit_dir is not None and passive_audit_dir.exists():
        passive_log = _load_raw_log(passive_audit_dir)
        result["observation_schedule_sensitivity"] = observation_schedule_sensitivity(
            passive_log, raw_log
        )
    else:
        result["observation_schedule_sensitivity"] = {
            "note": "passive_audit_dir not provided; comparative metric unavailable"
        }

    return result
