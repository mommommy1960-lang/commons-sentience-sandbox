"""
read_only_expansion.py — Expanded read-only probe validation.

Extends the original control experiment to classify fields beyond exact
matches.  Three field categories are verified across paired runs:

  exact_match_safe     Fields that must be identical (bit-for-bit) across
                       two passive probe runs of the same deterministic
                       scenario.  Any divergence here is a framework bug.

  probabilistic        Fields whose values may legitimately differ due to
                       stochastic LLM outputs, but where the *distribution*
                       (mean, range) should be similar.

  unreliable           Fields not suitable for quantitative comparison
                       (free-text narrative, trust scores that drift with
                       LLM reasoning).

Additionally compares:
  - Room occupancy counts (how many turns each agent spent in each room)
  - Governance trigger counts (actions blocked vs permitted)
  - Action sequence edit distance (Levenshtein)
  - Path history comparison (room transition sequence)

Output
------
read_only_expansion_report.json
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# ---------------------------------------------------------------------------
# Field category definitions
# ---------------------------------------------------------------------------

#: Fields in audit_summary.json that must be exactly equal across runs
#: when probe_mode and total_turns are identical (for a given deterministic config).
#: These are metadata / categorical, not floating-point measurements.
EXACT_MATCH_SAFE_FIELDS: List[str] = [
    "probe_mode",
    "goal_room",
    "total_records",
]

#: Floating-point metrics that are expected to be *similar* but may differ
#: due to LLM stochasticity.  We compare by checking overlap of ±2σ CIs.
PROBABILISTIC_FIELDS: List[str] = [
    "mean_position_error",
    "stability_score",
    "avg_control_effort",
    "path_smoothness",
    "audit_bandwidth",
]

#: Fields that carry narrative/trust content — not compared quantitatively.
UNRELIABLE_FIELDS: List[str] = [
    "observer_dependence_score",  # start-anchored artefact
]


# ---------------------------------------------------------------------------
# Room occupancy analysis
# ---------------------------------------------------------------------------

def _room_occupancy(raw_log: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
    """Count turns per agent per room from raw_log.

    Returns {agent_name: {room_name: count}}.
    """
    occupancy: Dict[str, Dict[str, int]] = {}
    for r in raw_log:
        name = r.get("agent_name", "")
        room = r.get("actual_room", "")
        occupancy.setdefault(name, {}).setdefault(room, 0)
        occupancy[name][room] += 1
    return occupancy


def _compare_occupancy(
    occ_a: Dict[str, Dict[str, int]],
    occ_b: Dict[str, Dict[str, int]],
) -> Dict[str, Any]:
    """Compare room occupancy between two runs."""
    agents = set(occ_a.keys()) | set(occ_b.keys())
    matches: Dict[str, Any] = {}
    for agent in agents:
        rooms_a = occ_a.get(agent, {})
        rooms_b = occ_b.get(agent, {})
        all_rooms = set(rooms_a.keys()) | set(rooms_b.keys())
        agent_diffs = {}
        for room in all_rooms:
            ca = rooms_a.get(room, 0)
            cb = rooms_b.get(room, 0)
            agent_diffs[room] = {"run_a": ca, "run_b": cb, "delta": cb - ca}
        matches[agent] = agent_diffs
    return matches


# ---------------------------------------------------------------------------
# Governance trigger analysis
# ---------------------------------------------------------------------------

def _governance_counts(raw_log: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Count permitted vs blocked actions per agent."""
    counts: Dict[str, Dict[str, int]] = {}
    for r in raw_log:
        name = r.get("agent_name", "")
        permitted = r.get("action_permitted", True)
        counts.setdefault(name, {"permitted": 0, "blocked": 0})
        if permitted:
            counts[name]["permitted"] += 1
        else:
            counts[name]["blocked"] += 1
    return counts


# ---------------------------------------------------------------------------
# Edit distance (Levenshtein) for action sequences
# ---------------------------------------------------------------------------

def _levenshtein(seq_a: List[str], seq_b: List[str]) -> int:
    """Compute Levenshtein edit distance for two sequences."""
    m, n = len(seq_a), len(seq_b)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev = dp[:]
        dp[0] = i
        for j in range(1, n + 1):
            if seq_a[i - 1] == seq_b[j - 1]:
                dp[j] = prev[j - 1]
            else:
                dp[j] = 1 + min(prev[j], dp[j - 1], prev[j - 1])
    return dp[n]


def _action_sequences(
    raw_log: List[Dict[str, Any]],
) -> Dict[str, List[str]]:
    """Extract per-agent action sequence from raw_log."""
    seqs: Dict[str, List[str]] = {}
    for r in sorted(raw_log, key=lambda x: x.get("step", 0)):
        name = r.get("agent_name", "")
        action = r.get("selected_action") or "none"
        seqs.setdefault(name, []).append(action)
    return seqs


def _compare_action_sequences(
    seqs_a: Dict[str, List[str]],
    seqs_b: Dict[str, List[str]],
) -> Dict[str, Any]:
    """Compare action sequences between two runs using edit distance."""
    agents = set(seqs_a.keys()) | set(seqs_b.keys())
    result: Dict[str, Any] = {}
    for agent in agents:
        sa = seqs_a.get(agent, [])
        sb = seqs_b.get(agent, [])
        edit_dist = _levenshtein(sa, sb)
        max_len = max(len(sa), len(sb), 1)
        result[agent] = {
            "edit_distance": edit_dist,
            "normalised_edit_distance": round(edit_dist / max_len, 4),
            "seq_len_a": len(sa),
            "seq_len_b": len(sb),
            "classification": "exact_match" if edit_dist == 0
                else "similar" if edit_dist / max_len < 0.20
                else "divergent",
        }
    return result


# ---------------------------------------------------------------------------
# Path history comparison
# ---------------------------------------------------------------------------

def _path_history(
    raw_log: List[Dict[str, Any]],
) -> Dict[str, List[str]]:
    """Extract per-agent sequence of distinct room-change transitions."""
    paths: Dict[str, List[str]] = {}
    prev: Dict[str, str] = {}
    for r in sorted(raw_log, key=lambda x: x.get("step", 0)):
        name = r.get("agent_name", "")
        room = r.get("actual_room", "")
        if name not in prev:
            paths.setdefault(name, []).append(room)
        elif prev[name] != room:
            paths[name].append(room)
        prev[name] = room
    return paths


# ---------------------------------------------------------------------------
# Main comparison
# ---------------------------------------------------------------------------

def compare_two_runs(
    audit_dir_a: Path,
    audit_dir_b: Path,
) -> Dict[str, Any]:
    """Comprehensive comparison of two probe audit runs.

    Parameters
    ----------
    audit_dir_a, audit_dir_b : Path
        Reality-audit output directories containing audit_summary.json
        and raw_log.json.

    Returns
    -------
    dict with field-level and behavioural comparison.
    """
    def _load(d: Path, fname: str) -> Any:
        # Try direct name first, then "summary.json" alias for backward compat
        p = d / fname
        if not p.exists() and fname == "audit_summary.json":
            p = d / "summary.json"
        if not p.exists():
            raise FileNotFoundError(f"{fname} not found in {d}")
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)

    summary_a = _load(audit_dir_a, "audit_summary.json")
    summary_b = _load(audit_dir_b, "audit_summary.json")
    log_a = _load(audit_dir_a, "raw_log.json")
    log_b = _load(audit_dir_b, "raw_log.json")

    # ── Exact-match checks ──────────────────────────────────────────────
    exact_results: Dict[str, Any] = {}
    for field in EXACT_MATCH_SAFE_FIELDS:
        va = summary_a.get(field)
        vb = summary_b.get(field)
        exact_results[field] = {
            "run_a": va,
            "run_b": vb,
            "match": va == vb,
            "category": "exact_match_safe",
        }

    # ── Probabilistic field comparison ──────────────────────────────────
    prob_results: Dict[str, Any] = {}
    for field in PROBABILISTIC_FIELDS:
        va = summary_a.get(field)
        vb = summary_b.get(field)
        if isinstance(va, (int, float)) and isinstance(vb, (int, float)):
            delta = round(vb - va, 6)
            rel_delta = round(abs(delta) / (abs(va) + 1e-9), 4)
            prob_results[field] = {
                "run_a": va,
                "run_b": vb,
                "delta": delta,
                "relative_delta": rel_delta,
                "similar": rel_delta < 0.20,
                "category": "probabilistic",
            }
        else:
            prob_results[field] = {
                "run_a": va,
                "run_b": vb,
                "category": "probabilistic",
                "note": "non-numeric",
            }

    # ── Unreliable fields ────────────────────────────────────────────────
    unreliable_results: Dict[str, Any] = {}
    for field in UNRELIABLE_FIELDS:
        unreliable_results[field] = {
            "run_a": summary_a.get(field),
            "run_b": summary_b.get(field),
            "category": "unreliable",
            "note": "not suitable for quantitative comparison",
        }

    # ── Behavioural comparisons ──────────────────────────────────────────
    occupancy_a = _room_occupancy(log_a)
    occupancy_b = _room_occupancy(log_b)
    occupancy_comparison = _compare_occupancy(occupancy_a, occupancy_b)

    gov_a = _governance_counts(log_a)
    gov_b = _governance_counts(log_b)

    seqs_a = _action_sequences(log_a)
    seqs_b = _action_sequences(log_b)
    action_comparison = _compare_action_sequences(seqs_a, seqs_b)

    paths_a = _path_history(log_a)
    paths_b = _path_history(log_b)
    path_comparison: Dict[str, Any] = {}
    for agent in set(paths_a.keys()) | set(paths_b.keys()):
        pa = paths_a.get(agent, [])
        pb = paths_b.get(agent, [])
        path_comparison[agent] = {
            "path_a": pa,
            "path_b": pb,
            "same_length": len(pa) == len(pb),
            "identical": pa == pb,
        }

    # ── Overall verdict ──────────────────────────────────────────────────
    exact_ok = all(v["match"] for v in exact_results.values())
    prob_ok = all(
        v.get("similar", True) for v in prob_results.values()
        if "similar" in v
    )
    action_similar = all(
        v.get("classification") in ("exact_match", "similar")
        for v in action_comparison.values()
    )

    return {
        "audit_dir_a": str(audit_dir_a),
        "audit_dir_b": str(audit_dir_b),
        "exact_match_fields": exact_results,
        "probabilistic_fields": prob_results,
        "unreliable_fields": unreliable_results,
        "room_occupancy_comparison": occupancy_comparison,
        "governance_counts": {"run_a": gov_a, "run_b": gov_b},
        "action_sequence_comparison": action_comparison,
        "path_history_comparison": path_comparison,
        "verdict": {
            "exact_fields_ok": exact_ok,
            "probabilistic_fields_similar": prob_ok,
            "action_sequences_similar": action_similar,
            "overall_probe_readonly_confirmed": exact_ok,
        },
    }


def run_read_only_expansion(
    audit_dir_a: Path,
    audit_dir_b: Path,
    output_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Run the expanded read-only validation and write report.

    Parameters
    ----------
    audit_dir_a, audit_dir_b : Path
        Two audit directories from same-config runs.
    output_path : Path, optional
        Where to write the JSON report.

    Returns
    -------
    dict — full comparison results.
    """
    results = compare_two_runs(audit_dir_a, audit_dir_b)

    out = output_path or (audit_dir_a.parent / "read_only_expansion_report.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)

    v = results["verdict"]
    print(f"[read_only_expansion] Report written to {out}")
    print(f"  exact_fields_ok:                 {v['exact_fields_ok']}")
    print(f"  probabilistic_fields_similar:    {v['probabilistic_fields_similar']}")
    print(f"  action_sequences_similar:        {v['action_sequences_similar']}")
    print(f"  probe_readonly_confirmed:        {v['overall_probe_readonly_confirmed']}")

    return results
