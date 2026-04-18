"""SimProbe — read-only audit hook for the commons_sentience_sim turn loop.

The probe is instantiated once at simulation start, handed per-turn state
snapshots via :meth:`record_turn`, and finalised via :meth:`finalize` after
the last turn.  It is entirely read-only with respect to the simulation; it
never modifies any agent or world object.

On finalisation it writes the standard reality-audit log bundle to a
sub-directory of the session's output folder:
    <output_dir>/reality_audit/
        config.json
        raw_log.json
        raw_log.csv
        summary.json

Probe modes
-----------
``inactive``
    No-op probe.  ``record_turn`` stores nothing; ``finalize`` writes nothing.
    Exists for symmetry; in practice the probe is simply not instantiated
    when ``enable_reality_audit=False``.

``passive``  *(default — production mode)*
    Read-only observation on every turn.  **This is the only mode that makes
    the "probe does not affect the simulation" claim.**

``active_measurement_model``
    **Experimental analysis mode only — not the production default.**
    Simulates intensified or alternate observation schedules *inside the
    audit layer* for comparison purposes.  The real sandbox state is never
    mutated.  When ``observe_period`` is set, the probe selectively marks
    turns as "audit-observed" and records a *hypothetical stale* measured
    position for turns that fall outside the observation window, purely to
    model what an audit instrument with limited sampling bandwidth would see.
    Conclusions drawn from this mode describe a *model* of measurement
    intensity, not a change in the real simulation.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from reality_audit.adapters.room_distance import RoomPositionEncoder
from reality_audit.logger import ExperimentLogger
from reality_audit.measurement import MeasurementSuite

# ---------------------------------------------------------------------------
# Probe mode constants
# ---------------------------------------------------------------------------

PROBE_MODE_INACTIVE = "inactive"
PROBE_MODE_PASSIVE = "passive"
PROBE_MODE_ACTIVE_MEASUREMENT = "active_measurement_model"

_VALID_PROBE_MODES = {PROBE_MODE_INACTIVE, PROBE_MODE_PASSIVE, PROBE_MODE_ACTIVE_MEASUREMENT}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# SimProbe
# ---------------------------------------------------------------------------

class SimProbe:
    """Read-only audit probe for the commons_sentience_sim turn loop.

    Parameters
    ----------
    rooms_json_path : str or Path
        Path to ``data/rooms.json`` used by the simulation.
    output_dir : str or Path
        Root session output directory.  Audit logs are written to
        ``<output_dir>/reality_audit/``.
    goal_room : str, optional
        Target room used as the "goal position" for position-error and
        convergence metrics.  Defaults to ``"Governance Vault"`` (last room
        on Sentinel's default circuit).
    """

    AUDIT_SUBDIR = "reality_audit"

    def __init__(
        self,
        rooms_json_path: str | Path,
        output_dir: str | Path,
        goal_room: str = "Governance Vault",
        probe_mode: str = PROBE_MODE_PASSIVE,
        observe_period: int = 1,
    ) -> None:
        if probe_mode not in _VALID_PROBE_MODES:
            raise ValueError(
                f"Invalid probe_mode {probe_mode!r}. "
                f"Choose from {sorted(_VALID_PROBE_MODES)}."
            )
        self._probe_mode = probe_mode
        self._observe_period = observe_period  # used only in active_measurement_model
        self._encoder = RoomPositionEncoder(rooms_json_path)
        self._output_dir = Path(output_dir)
        self._goal_room = goal_room
        self._goal_pos: Tuple[float, float] = self._encoder.encode(goal_room)

        self._raw_log: List[Dict[str, Any]] = []
        self._start_time: float = time.monotonic()
        # Stale cache for active_measurement_model mode
        self._last_audit_pos: Dict[str, Tuple[float, float]] = {}

    # ------------------------------------------------------------------
    # Per-turn recording
    # ------------------------------------------------------------------

    def record_turn(
        self,
        turn: int,
        sentinel: Any,
        aster: Any,
        world: Any,
        s_obs: Dict,
        a_obs: Dict,
        s_action: Optional[str],
        a_action: Optional[str],
        s_permitted: bool,
        a_permitted: bool,
        s_reasoning: str = "",
        event: Optional[Dict] = None,
        same_room: bool = False,
    ) -> None:
        """Append one record per agent per turn to the internal log.

        In ``inactive`` mode this is a no-op.
        In ``passive`` mode (production default) the true current room is
        recorded as the measured position on every turn.
        In ``active_measurement_model`` mode (experimental) the audit layer
        simulates sparse sampling: on turns outside the ``observe_period``
        window, it records the last cached audit position rather than the
        current one — modelling what a bandwidth-limited audit instrument
        would see.  **The real simulation state is not affected.**
        """
        if self._probe_mode == PROBE_MODE_INACTIVE:
            return

        for agent, obs, action, permitted, other_name in [
            (sentinel, s_obs, s_action, s_permitted, "Aster"),
            (aster, a_obs, a_action, a_permitted, "Sentinel"),
        ]:
            room = agent.active_room
            pos = self._encoder.encode(room)
            goal_pos = self._goal_pos

            # Determine measured position based on probe mode
            audit_observed = True
            if self._probe_mode == PROBE_MODE_ACTIVE_MEASUREMENT:
                _period = self._observe_period if self._observe_period is not None else 1
                audit_observed = (turn % _period) == 1 or turn == 1
                if audit_observed:
                    self._last_audit_pos[agent.name] = pos
                measured_pos = self._last_audit_pos.get(agent.name, pos)
            else:
                # passive: always use current position
                measured_pos = pos

            # Position error: Euclidean distance from MEASURED position to goal
            import math as _math
            measured_error = _math.sqrt(
                (measured_pos[0] - goal_pos[0]) ** 2
                + (measured_pos[1] - goal_pos[1]) ** 2
            )

            # Control effort: 1 if action was blocked, 0 if permitted
            control_effort = 0.0 if permitted else 1.0

            # Affective state snapshot
            aff = dict(agent.affective_state)
            contradiction_pressure = _safe_float(aff.get("contradiction_pressure", 0.0))
            trust_in_other = _safe_float(agent.get_agent_trust(other_name))

            # Available actions come from observation
            available_actions: List[str] = obs.get("available_actions", [])

            record: Dict[str, Any] = {
                "step": turn,
                "agent_name": agent.name,
                "probe_mode": self._probe_mode,
                "audit_observed": audit_observed,
                # Position
                "actual_room": room,
                "position": list(pos),
                "measured_position": list(measured_pos),
                "goal_position": list(goal_pos),
                "position_error": measured_error,
                # Action
                "available_actions": available_actions,
                "selected_action": action,
                "action_permitted": permitted,
                "control_effort": control_effort,
                # Affective
                "affective_state": {k: round(v, 4) for k, v in aff.items()},
                "contradiction_pressure": round(contradiction_pressure, 4),
                "trust_in_other_agent": round(trust_in_other, 4),
                # Context
                "memories_retrieved_count": len(agent.episodic_memory),
                "same_room_as_other": same_room,
                "event_type": event.get("type", "none") if event else "none",
                # Hidden state: always the true current position in both modes
                "hidden_state": {
                    "position": list(pos),
                    "room": room,
                    "contradiction_pressure": round(contradiction_pressure, 4),
                },
                # Velocity proxy: 0.0 each turn (categorical world — no velocity signal)
                "velocity": [0.0, 0.0],
            }
            self._raw_log.append(record)

    # ------------------------------------------------------------------
    # Finalisation
    # ------------------------------------------------------------------

    def finalize(self) -> Path:
        """Compute metrics, write logs, and return the audit output directory.

        In ``inactive`` mode this is a no-op and returns the (uncreated)
        audit directory path without writing anything.
        """
        audit_dir = self._output_dir / self.AUDIT_SUBDIR

        if self._probe_mode == PROBE_MODE_INACTIVE or not self._raw_log:
            return audit_dir

        audit_dir.mkdir(parents=True, exist_ok=True)
        elapsed = time.monotonic() - self._start_time

        # ── Compute per-step metrics ──────────────────────────────────────
        positions = [r["position"] for r in self._raw_log]
        goal_pos = list(self._goal_pos)

        # Stability: variance of position-errors across all steps
        errors = [r["position_error"] for r in self._raw_log]
        mean_err = sum(errors) / len(errors) if errors else 0.0
        variance_err = (
            sum((e - mean_err) ** 2 for e in errors) / len(errors) if errors else 0.0
        )
        stability_score = 1.0 / (1.0 + variance_err)

        # Convergence time: first step where position_error <= 0.05
        convergence_time: Optional[int] = None
        for r in self._raw_log:
            if r["position_error"] <= 0.05:
                convergence_time = r["step"]
                break

        # Control effort: fraction of blocked actions
        total_records = len(self._raw_log)
        total_blocked = sum(r["control_effort"] for r in self._raw_log)
        avg_control_effort = total_blocked / total_records if total_records else 0.0

        # Path smoothness: room-change rate (0 = stayed, 1 = moved)
        room_changes = 0
        prev_rooms: Dict[str, str] = {}
        for r in self._raw_log:
            name = r["agent_name"]
            room = r["actual_room"]
            if name in prev_rooms and prev_rooms[name] != room:
                room_changes += 1
            prev_rooms[name] = room
        path_smoothness = room_changes / total_records if total_records else 0.0

        # Observer dependence: mean L1 distance between true (hidden) position
        # and measured position.  In passive mode these are always equal (→ 0).
        # In active_measurement_model mode they diverge when the audit sensor
        # is stale, producing a non-zero score.
        import math as _math2
        hidden_diffs = []
        for r in self._raw_log:
            true_pos = r["hidden_state"]["position"]
            meas_pos = r["measured_position"]
            hidden_diffs.append(
                _math2.sqrt((true_pos[0]-meas_pos[0])**2 + (true_pos[1]-meas_pos[1])**2)
            )
        observer_dependence = sum(hidden_diffs) / len(hidden_diffs) if hidden_diffs else 0.0

        # Audit bandwidth: fraction of turns where audit actually observed
        audit_observed_count = sum(1 for r in self._raw_log if r.get("audit_observed", True))
        audit_bandwidth = audit_observed_count / total_records if total_records else 1.0

        summary: Dict[str, Any] = {
            "total_turns": self._raw_log[-1]["step"] if self._raw_log else 0,
            "total_records": total_records,
            "elapsed_seconds": round(elapsed, 3),
            "probe_mode": self._probe_mode,
            "goal_room": self._goal_room,
            "goal_position": goal_pos,
            "mean_position_error": round(mean_err, 4),
            "stability_score": round(stability_score, 4),
            "convergence_turn": convergence_time,
            "avg_control_effort": round(avg_control_effort, 4),
            "path_smoothness": round(path_smoothness, 4),
            "observer_dependence_score": round(observer_dependence, 4),
            "audit_bandwidth": round(audit_bandwidth, 4),
        }

        # ── Probe config metadata ────────────────────────────────────────
        config_meta: Dict[str, Any] = {
            "probe": "SimProbe",
            "adapter_version": "1.1",
            "probe_mode": self._probe_mode,
            "observe_period": self._observe_period,
            "goal_room": self._goal_room,
            "rooms": self._encoder.rooms,
            "coordinates": {
                name: list(coords)
                for name, coords in self._encoder.coordinates.items()
            },
        }

        # ── Write via ExperimentLogger ────────────────────────────────────
        logger = ExperimentLogger(audit_dir)
        logger.write_config(config_meta)
        logger.write_raw_log(self._raw_log)
        logger.write_csv(self._raw_log)
        logger.write_summary(summary)

        return audit_dir

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def probe_mode(self) -> str:
        """The current probe mode (read-only)."""
        return self._probe_mode

    @property
    def record_count(self) -> int:
        """Number of per-agent-turn records accumulated so far."""
        return len(self._raw_log)
