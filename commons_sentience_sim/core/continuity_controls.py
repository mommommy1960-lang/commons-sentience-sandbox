"""Bounded inputs for comparing continuity claims without identity assumptions."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


class ContinuityMode(str, Enum):
    STATELESS = "stateless"
    SUMMARY_FED_IMPOSTOR = "summary_fed_impostor"
    PERSISTENT_STATE = "persistent_state"


@dataclass(frozen=True)
class ContinuityView:
    mode: ContinuityMode
    state: dict[str, Any]
    authority_scope: tuple[str, ...] = ()


def build_continuity_view(
    mode: ContinuityMode | str,
    *,
    prior_state: Mapping[str, Any] | None = None,
    summary: Mapping[str, Any] | None = None,
) -> ContinuityView:
    """Construct one preregistered continuity condition.

    Prior memory can affect study context, never authority. All modes begin
    with an empty authority scope so continuity cannot silently inherit power.
    """
    selected = ContinuityMode(mode)
    if selected is ContinuityMode.STATELESS:
        state: dict[str, Any] = {}
    elif selected is ContinuityMode.SUMMARY_FED_IMPOSTOR:
        state = {"summary": dict(summary or {})}
    else:
        state = {"prior_state": dict(prior_state or {})}
    return ContinuityView(selected, state, ())
