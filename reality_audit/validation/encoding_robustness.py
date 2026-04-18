"""
encoding_robustness.py — Compare reality-audit metric sensitivity across
three position-encoding strategies for the room-based coordinate system.

Encodings
---------
1. BFS+MDS (current default)
   Uses breadth-first-search hop distances and multidimensional scaling to
   place rooms in 2-D.  Preserves topology; coordinates are normalised to
   roughly [-1, 1].

2. Pure hop-distance linear (PHD)
   Assigns each room a 1-D position (x = normalised BFS hop count from a
   fixed root room, y = 0).  Degenerate — all rooms on the x-axis — but
   tests whether metric conclusions change when topological embedding is
   flattened.

3. Manual topological (MT)
   Hard-codes (x, y) based on room names / known graph structure.  Serves
   as a "ground truth anchor" for whether BFS+MDS captures human intuition
   about room layout.

For each encoding, every ``audit_raw_log.json`` record is re-encoded and
the core metrics recomputed, then compared to the original BFS+MDS result.

Output
------
encoding_robustness_report.json — per-metric, per-encoding comparison table
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

from reality_audit.adapters.room_distance import RoomPositionEncoder

# ---------------------------------------------------------------------------
# Manual topological coordinates
# (Social Hall = community centre; Governance Vault = formal authority;
#  Operations Desk = work hub; Quiet Lab = reflection space;
#  Memory Archive = history/storage)
# ---------------------------------------------------------------------------
_MANUAL_COORDS: Dict[str, Tuple[float, float]] = {
    "Social Hall":       (0.0,  0.5),
    "Governance Vault":  (0.0, -0.5),
    "Operations Desk":   (0.5,  0.0),
    "Quiet Lab":         (-0.5, 0.2),
    "Memory Archive":    (-0.5, -0.2),
}

# Root room for pure hop-distance encoding
_PHD_ROOT_ROOM = "Social Hall"


# ---------------------------------------------------------------------------
# Encoding builders
# ---------------------------------------------------------------------------

class PureHopDistanceEncoder:
    """Normalise BFS hop counts from a fixed root room to [0, 1] on the x-axis.

    y = 0 for all rooms (degenerate 1-D encoding in a 2-D coordinate space).
    """

    def __init__(self, rooms_json_path: Path, root_room: str = _PHD_ROOT_ROOM) -> None:
        self._base = RoomPositionEncoder(rooms_json_path)
        self._root = root_room
        rooms = self._base.rooms

        # Get row index for root room
        try:
            root_idx = rooms.index(root_room)
        except ValueError:
            root_idx = 0

        # BFS hop distances from root
        raw_dist = [self._base._dist_matrix[root_idx][j] for j in range(len(rooms))]
        max_dist = max(raw_dist) if max(raw_dist) > 0 else 1.0

        self.coordinates: Dict[str, Tuple[float, float]] = {}
        for i, room in enumerate(rooms):
            x = raw_dist[i] / max_dist  # normalised to [0, 1]
            self.coordinates[room] = (x, 0.0)

    def encode(self, room_name: str) -> Tuple[float, float]:
        return self.coordinates.get(room_name, (0.5, 0.0))


class ManualTopologicalEncoder:
    """Use hand-crafted (x, y) coordinates based on room semantics."""

    def __init__(self, coords: Optional[Dict[str, Tuple[float, float]]] = None) -> None:
        self.coordinates = coords or _MANUAL_COORDS

    def encode(self, room_name: str) -> Tuple[float, float]:
        return self.coordinates.get(room_name, (0.0, 0.0))


# ---------------------------------------------------------------------------
# Metric recomputation from raw log
# ---------------------------------------------------------------------------

def _recompute_metrics(
    raw_log: List[Dict[str, Any]],
    encoder: Any,
    goal_room: str,
) -> Dict[str, float]:
    """Re-encode positions and recompute core metrics from scratch."""
    goal_pos = encoder.encode(goal_room)

    re_records: List[Dict[str, Any]] = []
    for r in raw_log:
        actual_room = r.get("actual_room", "")
        pos = list(encoder.encode(actual_room))
        error = math.sqrt(
            (pos[0] - goal_pos[0]) ** 2 + (pos[1] - goal_pos[1]) ** 2
        )
        re_records.append({
            **r,
            "position": pos,
            "measured_position": pos,
            "position_error": error,
        })

    n = len(re_records)
    if n == 0:
        return {}

    errors = [r["position_error"] for r in re_records]
    mean_err = sum(errors) / n
    variance_err = sum((e - mean_err) ** 2 for e in errors) / n
    stability = 1.0 / (1.0 + variance_err)

    # Path smoothness: fraction of turns where room changed
    room_changes = 0
    prev_rooms: Dict[str, str] = {}
    for r in re_records:
        name = r.get("agent_name", "")
        room = r.get("actual_room", "")
        if name in prev_rooms and prev_rooms[name] != room:
            room_changes += 1
        prev_rooms[name] = room
    path_smoothness = room_changes / n

    # Anisotropy: |x_sum - y_sum| / max(...)
    x_vals = [r["position"][0] for r in re_records]
    y_vals = [r["position"][1] for r in re_records]
    x_sum = abs(sum(x_vals))
    y_sum = abs(sum(y_vals))
    denom = max(x_sum, y_sum)
    anisotropy = abs(x_sum - y_sum) / denom if denom > 1e-9 else 0.0

    return {
        "mean_position_error": round(mean_err, 6),
        "stability_score": round(stability, 6),
        "path_smoothness": round(path_smoothness, 6),
        "anisotropy_score": round(anisotropy, 6),
    }


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def run_encoding_robustness(
    audit_dir: Path,
    rooms_json_path: Optional[Path] = None,
    goal_room: str = "Social Hall",
    output_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Compare metrics across three encodings for a given audit directory.

    Parameters
    ----------
    audit_dir : Path
        Path to a reality-audit output directory (must contain raw_log.json).
    rooms_json_path : Path, optional
        Path to rooms.json. Defaults to commons_sentience_sim/data/rooms.json.
    goal_room : str
        Room treated as the goal for position-error calculation.
    output_path : Path, optional
        Where to write encoding_robustness_report.json.
        Defaults to audit_dir / "encoding_robustness_report.json".

    Returns
    -------
    dict with results for all three encodings.
    """
    rooms_json = rooms_json_path or (
        _REPO_ROOT / "commons_sentience_sim" / "data" / "rooms.json"
    )
    raw_log_path = audit_dir / "raw_log.json"
    if not raw_log_path.exists():
        raise FileNotFoundError(f"raw_log.json not found in {audit_dir}")

    with open(raw_log_path, encoding="utf-8") as fh:
        raw_log: List[Dict[str, Any]] = json.load(fh)

    # Build encoders
    bfs_mds_encoder = RoomPositionEncoder(rooms_json)
    phd_encoder = PureHopDistanceEncoder(rooms_json)
    mt_encoder = ManualTopologicalEncoder()

    encoders = {
        "bfs_mds": bfs_mds_encoder,
        "pure_hop_distance": phd_encoder,
        "manual_topological": mt_encoder,
    }

    results: Dict[str, Any] = {}
    for enc_name, enc in encoders.items():
        try:
            metrics = _recompute_metrics(raw_log, enc, goal_room)
        except Exception as exc:
            metrics = {"error": str(exc)}
        results[enc_name] = metrics

    # Compute deltas relative to BFS+MDS baseline
    baseline = results.get("bfs_mds", {})
    comparison: Dict[str, Any] = {}
    for enc_name, metrics in results.items():
        if enc_name == "bfs_mds":
            continue
        deltas: Dict[str, Optional[float]] = {}
        for m, v in metrics.items():
            if m == "error":
                deltas[m] = v
                continue
            b = baseline.get(m)
            if isinstance(b, (int, float)) and isinstance(v, (int, float)):
                deltas[m] = round(v - b, 6)
            else:
                deltas[m] = None
        comparison[f"{enc_name}_vs_bfs_mds"] = deltas

    # Robustness assessment: are the ordinal rankings stable?
    robustness_notes: List[str] = []
    for m in ("mean_position_error", "stability_score", "path_smoothness", "anisotropy_score"):
        vals = {enc: results.get(enc, {}).get(m) for enc in encoders}
        valid = {k: v for k, v in vals.items() if isinstance(v, (int, float))}
        if len(valid) >= 2:
            range_pct = (max(valid.values()) - min(valid.values())) / (
                abs(max(valid.values())) + 1e-9
            )
            if range_pct < 0.05:
                note = f"{m}: ROBUST across encodings (spread < 5%)"
            elif range_pct < 0.20:
                note = f"{m}: MODERATELY ROBUST (spread {range_pct:.1%})"
            else:
                note = f"{m}: ENCODING-SENSITIVE (spread {range_pct:.1%})"
            robustness_notes.append(note)

    output: Dict[str, Any] = {
        "audit_dir": str(audit_dir),
        "goal_room": goal_room,
        "n_records": len(raw_log),
        "encodings": results,
        "deltas_vs_bfs_mds": comparison,
        "robustness_notes": robustness_notes,
    }

    # Write report
    out_path = output_path or (audit_dir / "encoding_robustness_report.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(output, fh, indent=2)

    print(f"[encoding_robustness] Report written to {out_path}")
    print("\n  Robustness notes:")
    for n in robustness_notes:
        print(f"    {n}")

    return output


if __name__ == "__main__":
    # Quick test against any existing audit directory
    _DEFAULT_AUDIT = (
        _REPO_ROOT / "commons_sentience_sim" / "output" / "reality_audit"
    )
    candidates = list(_DEFAULT_AUDIT.glob("**/raw_log.json"))
    if not candidates:
        print("No raw_log.json found. Run a sandbox campaign first.")
    else:
        audit_dir = candidates[0].parent
        print(f"Using audit_dir: {audit_dir}")
        run_encoding_robustness(audit_dir)
