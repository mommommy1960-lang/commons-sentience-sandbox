"""Room position encoder for the commons_sentience_sim sandbox.

Since the sandbox has no 2D geometry, this module provides:
- BFS shortest-path hop distances between rooms.
- A stable (x, y) coordinate embedding derived from the distance matrix
  via classical multidimensional scaling (MDS).  The coordinates are
  normalised to [-1, 1] so they slot naturally into reality-audit metrics
  that expect continuous positions.
"""

from __future__ import annotations

import json
import math
from collections import deque
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Graph utilities
# ---------------------------------------------------------------------------

def _build_adjacency(rooms_json: Dict) -> Dict[str, List[str]]:
    """Return {room_name: [neighbours]} from the rooms.json dict."""
    return {
        name: data.get("connected_rooms", [])
        for name, data in rooms_json.items()
    }


def _bfs_distances(adjacency: Dict[str, List[str]], source: str) -> Dict[str, int]:
    """Return BFS distances from *source* to every reachable room."""
    dist: Dict[str, int] = {source: 0}
    queue: deque[str] = deque([source])
    while queue:
        node = queue.popleft()
        for neighbour in adjacency.get(node, []):
            if neighbour not in dist:
                dist[neighbour] = dist[node] + 1
                queue.append(neighbour)
    return dist


def _full_distance_matrix(
    rooms: List[str],
    adjacency: Dict[str, List[str]],
) -> List[List[float]]:
    """Return |rooms| × |rooms| matrix of BFS hop distances."""
    n = len(rooms)
    matrix: List[List[float]] = [[0.0] * n for _ in range(n)]
    for i, room in enumerate(rooms):
        bfs = _bfs_distances(adjacency, room)
        for j, target in enumerate(rooms):
            matrix[i][j] = float(bfs.get(target, n))  # n = max penalty if unreachable
    return matrix


# ---------------------------------------------------------------------------
# Classical MDS  (2-D embedding from distance matrix)
# ---------------------------------------------------------------------------

def _mds_2d(dist_matrix: List[List[float]]) -> List[Tuple[float, float]]:
    """Classical MDS: return 2-D coordinates for each item.

    Uses the double-centring trick on squared distances, then takes the two
    largest eigenvector directions via power iteration.
    """
    n = len(dist_matrix)
    # Squared distance matrix
    d2 = [[dist_matrix[i][j] ** 2 for j in range(n)] for i in range(n)]

    row_mean = [sum(d2[i]) / n for i in range(n)]
    col_mean = [sum(d2[i][j] for i in range(n)) / n for j in range(n)]
    grand_mean = sum(row_mean) / n

    # B = -0.5 * (d2[i][j] - row_mean[i] - col_mean[j] + grand_mean)
    B = [
        [-0.5 * (d2[i][j] - row_mean[i] - col_mean[j] + grand_mean) for j in range(n)]
        for i in range(n)
    ]

    def _mat_vec(mat: List[List[float]], v: List[float]) -> List[float]:
        return [sum(mat[i][j] * v[j] for j in range(n)) for i in range(n)]

    def _norm(v: List[float]) -> float:
        return math.sqrt(sum(x * x for x in v))

    def _power_iter(mat: List[List[float]], deflate: Optional[List[float]] = None) -> Tuple[float, List[float]]:
        v = [1.0 / math.sqrt(n)] * n
        for _ in range(200):
            v = _mat_vec(mat, v)
            if deflate is not None:
                dot = sum(v[i] * deflate[i] for i in range(n))
                v = [v[i] - dot * deflate[i] for i in range(n)]
            nrm = _norm(v)
            if nrm < 1e-12:
                break
            v = [x / nrm for x in v]
        ev = sum(v[i] * _mat_vec(mat, v)[i] for i in range(n))
        return ev, v

    ev1, vec1 = _power_iter(B)
    ev2, vec2 = _power_iter(B, deflate=vec1)

    scale1 = math.sqrt(max(ev1, 0.0))
    scale2 = math.sqrt(max(ev2, 0.0))

    coords = [(vec1[i] * scale1, vec2[i] * scale2) for i in range(n)]

    # Normalise each axis to [-1, 1]
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    x_range = max(xs) - min(xs) or 1.0
    y_range = max(ys) - min(ys) or 1.0
    x_mid = (max(xs) + min(xs)) / 2.0
    y_mid = (max(ys) + min(ys)) / 2.0

    return [
        (2.0 * (x - x_mid) / x_range, 2.0 * (y - y_mid) / y_range)
        for x, y in coords
    ]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class RoomPositionEncoder:
    """Encode discrete room names as continuous (x, y) coordinates.

    Parameters
    ----------
    rooms_json_path : str or Path
        Path to the rooms.json file used by the simulation.

    Attributes
    ----------
    rooms : list[str]
        Ordered list of room names.
    coordinates : dict[str, tuple[float, float]]
        Stable MDS embedding; positions are in [-1, 1]².
    """

    def __init__(self, rooms_json_path: str | Path) -> None:
        path = Path(rooms_json_path)
        rooms_data: Dict = json.loads(path.read_text(encoding="utf-8"))

        self.rooms: List[str] = list(rooms_data.keys())
        adjacency = _build_adjacency(rooms_data)
        dist_matrix = _full_distance_matrix(self.rooms, adjacency)
        self._dist_matrix = dist_matrix  # stored for hop-distance lookups

        coords_list = _mds_2d(dist_matrix)
        self.coordinates: Dict[str, Tuple[float, float]] = {
            name: coords_list[i] for i, name in enumerate(self.rooms)
        }

    # ------------------------------------------------------------------

    def encode(self, room_name: str) -> Tuple[float, float]:
        """Return the (x, y) embedding for *room_name*.

        Falls back to (0.0, 0.0) for unknown rooms (e.g. None / 'unknown').
        """
        return self.coordinates.get(room_name, (0.0, 0.0))

    def hop_distance(self, room_a: str, room_b: str) -> float:
        """Return the BFS hop distance between two rooms.

        Returns ``len(rooms)`` as a penalty for unknown / disconnected rooms.
        """
        try:
            i = self.rooms.index(room_a)
            j = self.rooms.index(room_b)
            return self._dist_matrix[i][j]
        except ValueError:
            return float(len(self.rooms))

    def euclidean_distance(self, room_a: str, room_b: str) -> float:
        """Return Euclidean distance in the MDS embedding space."""
        ax, ay = self.encode(room_a)
        bx, by = self.encode(room_b)
        return math.sqrt((ax - bx) ** 2 + (ay - by) ** 2)
